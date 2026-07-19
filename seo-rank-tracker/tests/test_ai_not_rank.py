import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import types
import pytest
from src.models import Result
from src.connectors.google_search_console import period_range, previous_period, enrich_daily, QUERY_DIMENSIONS, authorize, aggregate_period, fetch_daily, discover_latest_date, language_from_page
from src.connectors.google_search_console import run as run_gsc
from src.connectors.bing_webmaster import run as run_bing, bing_date_to_iso, parse_page_stats, parse_query_stats
from src.connectors.google_ai_import import run as run_ai_import, explicit_ai_present


def test_ai_mentions_never_rank():
    assert Result(surface="google_generative_ai", brand_mentioned="true").to_row()["exact_organic_position"] == ""
    with pytest.raises(ValueError): Result(surface="google_generative_ai", brand_mentioned="true", exact_organic_position="1")


def test_periods_and_previous_period():
    assert previous_period("2026-07-08", "2026-07-14") == ("2026-07-01", "2026-07-07")
    assert period_range("7d", latest_date="2026-07-18") == ("2026-07-12", "2026-07-18")


def test_missing_credentials_empty_import_and_dry_run(monkeypatch):
    for key in ["GSC_PROPERTY", "GOOGLE_CLIENT_SECRET_FILE", "GOOGLE_TOKEN_FILE", "BING_WEBMASTER_API_KEY", "BING_SITE_URL"]: monkeypatch.delenv(key, raising=False)
    assert run_gsc()[0]["status"] == "error"
    assert run_bing()[0]["status"] == "error"
    assert run_ai_import()[0]["status"] in {"no_data", "ok"}
    assert run_gsc(dry_run=True)[0]["status"] == "dry_run"
    assert run_bing(dry_run=True)[0]["status"] == "dry_run"
    assert run_ai_import(dry_run=True)[0]["status"] == "dry_run"


def test_gsc_daily_dimension_query_enrichment_no_scenario_city():
    assert QUERY_DIMENSIONS == ["date", "query", "page", "country", "device"]
    item = {"keys": ["2026-07-18", "Scooter Rental Barcelona", "https://rentalscooterbarcelona.com/", "esp", "mobile"], "position": 3.5, "clicks": 1, "impressions": 10, "ctr": 0.1}
    configured = {("scooter rental barcelona", "mobile", "google", "search_console"): {"query_id":"qid", "category":"scooter", "language":"en", "expected_language_path":"/"}}
    row = enrich_daily(item, configured, "7d")
    assert row["date"] == "2026-07-18" and row["row_type"] == "daily"
    assert row["configured_query"] == "true" and row["language_source"] == "configured_query"
    assert row["scenario"] == "" and row["city"] == ""
    assert row["country"] == "esp" and row["country_format"] == "iso_3166_1_alpha_3"


def test_unknown_query_unknown_language_and_safe_cat_path():
    item = {"keys": ["2026-07-18", "zzzz qqqq", "https://rentalscooterbarcelona.com/catalog/page/", "esp", "desktop"], "position": 8}
    row = enrich_daily(item, {}, "7d")
    assert row["configured_query"] == "false"
    assert row["language"] == "unknown" and row["language_source"] == "unknown"
    assert language_from_page("https://rentalscooterbarcelona.com/cat/page/") == ("ca", "landing_page_path")
    assert language_from_page("https://rentalscooterbarcelona.com/catalog/page/") == ("unknown", "unknown")


def test_weighted_period_summary_and_no_day_overwrite():
    current = [Result(row_type="daily", query="q", url="u", country="esp", device="mobile", clicks="1", impressions="10", average_position="2").to_row(), Result(row_type="daily", query="q", url="u", country="esp", device="mobile", clicks="3", impressions="30", average_position="4").to_row()]
    previous = [Result(row_type="daily", query="q", url="u", country="esp", device="mobile", clicks="1", impressions="20", average_position="5").to_row()]
    summary = aggregate_period(current, "7d", previous)[0]
    assert summary["row_type"] == "period_summary"
    assert summary["clicks"] == "4.0" and summary["impressions"] == "40.0"
    assert summary["average_position"] == "3.5"
    assert summary["previous_average_position"] == "5.0"
    assert summary["position_change"] == "-1.5"


def test_fetch_daily_paginates_each_day_and_latest_date():
    calls=[]
    class Q:
        def __init__(self, rows): self.rows=rows
        def execute(self): return {"rows": self.rows}
    class SA:
        def query(self, siteUrl, body):
            calls.append(body.copy())
            if body["dimensions"] == ["date"]: return Q([{"keys":["2026-07-15"]},{"keys":["2026-07-18"]}])
            if body["startRow"] == 0: return Q([{"keys":[body["startDate"],"q","u","esp","mobile"]}] * 25000)
            return Q([])
    class S: 
        def searchanalytics(self): return SA()
    assert discover_latest_date(S(), "site") == "2026-07-18"
    rows, limit_days, counts = fetch_daily(S(), "site", "2026-07-17", "2026-07-18")
    assert len(rows) == 50000 and limit_days == []
    assert counts == {"2026-07-17": 25000, "2026-07-18": 25000}
    assert {c["startDate"] for c in calls if c["dimensions"] != ["date"]} == {"2026-07-17", "2026-07-18"}


def test_first_oauth_without_token(monkeypatch, tmp_path):
    secret = tmp_path / "client_secret.json"; secret.write_text("{}")
    token = tmp_path / "token.json"; monkeypatch.setenv("GOOGLE_CLIENT_SECRET_FILE", str(secret)); monkeypatch.setenv("GOOGLE_TOKEN_FILE", str(token))
    class FakeCreds:
        valid=True; expired=False; refresh_token=None
        def to_json(self): return '{"token":"x"}'
    class FakeFlow:
        @classmethod
        def from_client_secrets_file(cls, filename, scopes): return cls()
        def run_local_server(self, port=0): return FakeCreds()
    sys.modules['google.auth.transport.requests'] = types.SimpleNamespace(Request=object)
    sys.modules['google.oauth2.credentials'] = types.SimpleNamespace(Credentials=types.SimpleNamespace(from_authorized_user_file=lambda *a, **k: None))
    sys.modules['google_auth_oauthlib.flow'] = types.SimpleNamespace(InstalledAppFlow=FakeFlow)
    assert authorize().valid and token.exists()


def test_refresh_and_invalid_token(monkeypatch, tmp_path):
    secret = tmp_path / "client_secret.json"; secret.write_text("{}")
    token = tmp_path / "token.json"; token.write_text("{}")
    monkeypatch.setenv("GOOGLE_CLIENT_SECRET_FILE", str(secret)); monkeypatch.setenv("GOOGLE_TOKEN_FILE", str(token))
    class FakeCreds:
        valid=False; expired=True; refresh_token="r"
        def refresh(self, request): self.valid=True; self.expired=False
        def to_json(self): return '{"token":"refreshed"}'
    sys.modules['google.auth.transport.requests'] = types.SimpleNamespace(Request=object)
    sys.modules['google.oauth2.credentials'] = types.SimpleNamespace(Credentials=types.SimpleNamespace(from_authorized_user_file=lambda *a, **k: FakeCreds()))
    sys.modules['google_auth_oauthlib.flow'] = types.SimpleNamespace(InstalledAppFlow=object)
    assert authorize().valid
    sys.modules['google.oauth2.credentials'] = types.SimpleNamespace(Credentials=types.SimpleNamespace(from_authorized_user_file=lambda *a, **k: (_ for _ in ()).throw(ValueError("bad"))))
    with pytest.raises(ValueError): authorize()


def test_bing_methods_dates_ctr_endpoint_and_query_param(monkeypatch):
    monkeypatch.setenv("BING_WEBMASTER_API_KEY", "k"); monkeypatch.setenv("BING_SITE_URL", "https://example.com/")
    assert bing_date_to_iso("/Date(1721260800000)/") == "2024-07-18"
    page = parse_page_stats({"Query":"https://example.com/p", "Clicks":2, "Impressions":4})
    assert page["url"] == "https://example.com/p" and page["query"] == "" and page["ctr"] == "0.5" and page["error"] == "" and page["endpoint"] == "GetPageStats"
    import src.connectors.bing_webmaster as bing
    seen=[]
    monkeypatch.setattr(bing, "active_unique_queries", lambda: ["q1", "q2"])
    monkeypatch.setattr(bing, "_get", lambda method, **params: seen.append((method, params)) or {"d": [{"Query":"q", "Clicks":1, "Impressions":2}]})
    rows = bing.run(bing_detailed=True)
    assert any(m == "GetQueryPageStats" and p.get("query") for m,p in seen)
    assert all(not (m == "GetQueryPageStats" and "query" not in p) for m,p in seen)
    assert rows[0]["status"] == "ok" and rows[0]["error"] == ""


def test_ai_feature_not_invented():
    assert explicit_ai_present({}) == ""
    assert explicit_ai_present({}) == ""
    assert explicit_ai_present({"ai_feature_present":"true"}) == "true"
    assert explicit_ai_present({"report_type":"ai_overview"}) == "true"


def test_gsc_25000_then_empty_no_warning_and_datastate_final():
    calls=[]
    class Q:
        def __init__(self, rows): self.rows=rows
        def execute(self): return {"rows": self.rows}
    class SA:
        def query(self, siteUrl, body):
            calls.append(body.copy())
            if body["startRow"] == 0: return Q([{"keys":[body["startDate"],"q","u","esp","mobile"]}] * 25000)
            return Q([])
    class S:
        def searchanalytics(self): return SA()
    rows, limit_days, counts = fetch_daily(S(), "site", "2026-07-18", "2026-07-18")
    assert len(rows) == 25000
    assert limit_days == []
    assert counts["2026-07-18"] == 25000
    assert all(c.get("dataState") == "final" for c in calls)


def test_gsc_two_25000_pages_sets_limit_reached():
    calls=[]
    class Q:
        def __init__(self, rows): self.rows=rows
        def execute(self): return {"rows": self.rows}
    class SA:
        def query(self, siteUrl, body):
            calls.append(body.copy())
            if body["startRow"] in {0, 25000}: return Q([{"keys":[body["startDate"],"q","u","esp","mobile"]}] * 25000)
            return Q([])
    class S:
        def searchanalytics(self): return SA()
    rows, limit_days, counts = fetch_daily(S(), "site", "2026-07-18", "2026-07-18")
    assert len(rows) == 50000
    assert limit_days == ["2026-07-18"]
    assert counts["2026-07-18"] == 50000
    assert all(c.get("dataState") == "final" for c in calls)


def test_bing_query_page_stats_does_not_invent_url():
    from src.connectors.bing_webmaster import parse_query_page_stats
    row = parse_query_page_stats({"Query":"returned", "Clicks":1, "Impressions":2}, "requested")
    assert row["endpoint"] == "GetQueryPageStats"
    assert row["requested_query"] == "requested"
    assert row["returned_query_value"] == "returned"
    assert row["url"] == ""


def test_discover_latest_date_uses_large_row_limit_for_11_ascending_dates():
    calls=[]
    class Q:
        def execute(self):
            return {"rows": [{"keys":[f"2026-07-{day:02d}"]} for day in range(9, 20)]}
    class SA:
        def query(self, siteUrl, body):
            calls.append(body.copy()); return Q()
    class S:
        def searchanalytics(self): return SA()
    assert discover_latest_date(S(), "site") == "2026-07-19"
    assert calls[0]["rowLimit"] == 25000
    assert calls[0]["dimensions"] == ["date"]
    assert calls[0]["type"] == "web"
    assert calls[0]["dataState"] == "final"


def test_current_previous_limit_warning_flags_and_comparison_reliability():
    current = [Result(row_type="daily", query="q", url="u", country="esp", device="mobile", clicks="1", impressions="10", average_position="2").to_row()]
    previous = [Result(row_type="daily", query="q", url="u", country="esp", device="mobile", clicks="1", impressions="10", average_position="5").to_row()]
    reliable = aggregate_period(current, "7d", previous, previous_limit_reached=False)[0]
    unreliable = aggregate_period(current, "7d", previous, previous_limit_reached=True)[0]
    assert reliable["position_change"] == "-3.0" and reliable["comparison_reliable"] == "true"
    assert unreliable["position_change"] == "" and unreliable["comparison_reliable"] == "false"
    current_warning = Result(row_type="period_summary", status="warning", data_limit_reached="true", current_period_data_limit_reached="true", error="Current Search Console period reached the daily exposure limit; additional rows may not be available: 2026-07-18").to_row()
    previous_warning = Result(row_type="period_summary", status="warning", data_limit_reached="true", previous_period_data_limit_reached="true", comparison_reliable="false", error="Previous Search Console period reached the daily exposure limit; comparison may be incomplete: 2026-07-11").to_row()
    both_warning = Result(row_type="period_summary", status="warning", data_limit_reached="true", current_period_data_limit_reached="true", previous_period_data_limit_reached="true", comparison_reliable="false").to_row()
    assert current_warning["current_period_data_limit_reached"] == "true" and current_warning["data_limit_reached"] == "true"
    assert previous_warning["previous_period_data_limit_reached"] == "true" and previous_warning["comparison_reliable"] == "false"
    assert both_warning["current_period_data_limit_reached"] == "true" and both_warning["previous_period_data_limit_reached"] == "true"


def _sample_raw(day, query="q"):
    return [{"keys":[day, query, "https://rentalscooterbarcelona.com/", "esp", "mobile"], "position": 2 if day >= "2026-07-12" else 5, "clicks": 1, "impressions": 10, "ctr": 0.1}]


def _run_with_limits(monkeypatch, current_limits, previous_limits):
    import sys, types
    import src.connectors.google_search_console as gsc
    monkeypatch.setenv("GSC_PROPERTY", "site")
    monkeypatch.setenv("GOOGLE_CLIENT_SECRET_FILE", "secret")
    monkeypatch.setenv("GOOGLE_TOKEN_FILE", "token")
    monkeypatch.setattr(gsc, "authorize", lambda: object())
    monkeypatch.setattr(gsc, "discover_latest_date", lambda service, site_url: "2026-07-18")
    monkeypatch.setattr(gsc, "query_lookup", lambda include_inactive=False: {})
    def fake_fetch_daily(service, site_url, start, end):
        previous = end < "2026-07-12"
        limits = previous_limits if previous else current_limits
        rows = _sample_raw(end)
        return rows, limits, {end: 50000 if limits else 1}
    monkeypatch.setattr(gsc, "fetch_daily", fake_fetch_daily)
    sys.modules['googleapiclient.discovery'] = types.SimpleNamespace(build=lambda *a, **k: object())
    sys.modules['googleapiclient.errors'] = types.SimpleNamespace(HttpError=Exception)
    return gsc.run(period="7d")


def _summaries(rows):
    return [r for r in rows if r["row_type"] == "period_summary" and r["status"] == "ok"]


def _warnings(rows):
    return [r for r in rows if r["status"] == "warning"]


def test_run_current_limit_only(monkeypatch):
    rows = _run_with_limits(monkeypatch, ["2026-07-18"], [])
    warnings = _warnings(rows); summary = _summaries(rows)[0]
    assert [w["limit_period"] for w in warnings] == ["current"]
    assert summary["current_period_data_limit_reached"] == "true"
    assert summary["previous_period_data_limit_reached"] == ""
    assert summary["current_period_limit_days"] == "2026-07-18"
    assert summary["comparison_reliable"] == "false"
    assert summary["position_change"] == ""


def test_run_previous_limit_only(monkeypatch):
    rows = _run_with_limits(monkeypatch, [], ["2026-07-11"])
    warnings = _warnings(rows); summary = _summaries(rows)[0]
    assert [w["limit_period"] for w in warnings] == ["previous"]
    assert summary["previous_period_data_limit_reached"] == "true"
    assert summary["current_period_data_limit_reached"] == ""
    assert summary["previous_period_limit_days"] == "2026-07-11"
    assert summary["comparison_reliable"] == "false"
    assert summary["position_change"] == ""


def test_run_both_limits(monkeypatch):
    rows = _run_with_limits(monkeypatch, ["2026-07-18"], ["2026-07-11"])
    warnings = _warnings(rows); summary = _summaries(rows)[0]
    assert len(warnings) == 2
    assert {w["limit_period"] for w in warnings} == {"current", "previous"}
    current = [w for w in warnings if w["limit_period"] == "current"][0]
    previous = [w for w in warnings if w["limit_period"] == "previous"][0]
    assert current != previous
    assert current["current_period_limit_days"] == "2026-07-18" and current["previous_period_limit_days"] == ""
    assert previous["previous_period_limit_days"] == "2026-07-11" and previous["current_period_limit_days"] == ""
    assert summary["current_period_data_limit_reached"] == "true" and summary["previous_period_data_limit_reached"] == "true"
    assert summary["comparison_reliable"] == "false" and summary["position_change"] == ""


def test_run_no_limits(monkeypatch):
    rows = _run_with_limits(monkeypatch, [], [])
    assert _warnings(rows) == []
    summary = _summaries(rows)[0]
    assert summary["comparison_reliable"] == "true"
    assert summary["position_change"] == "-3.0"


def test_ai_feature_explicit_values_only():
    assert explicit_ai_present({"ai_feature_present":"true"}) == "true"
    assert explicit_ai_present({"ai_feature_present":"1"}) == "true"
    assert explicit_ai_present({"ai_feature_present":"sí"}) == "true"
    assert explicit_ai_present({"ai_feature_present":"false"}) == "false"
    assert explicit_ai_present({"ai_feature_present":"0"}) == "false"
    assert explicit_ai_present({"ai_feature_present":"no"}) == "false"
    assert explicit_ai_present({"ai_feature_present":"maybe"}) == ""
    assert explicit_ai_present({"ai_feature_present":"enabled"}) == ""


def test_bing_items_empty_and_result_shapes():
    from src.connectors.bing_webmaster import _items
    assert _items({"d": {}}) == []
    assert _items({"d": []}) == []
    assert _items(None) == []
    assert _items({"d": {"Results": [{"Query": "q"}]}}) == [{"Query": "q"}]
    assert _items({"d": {"Query": "q", "Clicks": 1}}) == [{"Query": "q", "Clicks": 1}]


def test_bing_no_data_when_successful_empty(monkeypatch):
    import src.connectors.bing_webmaster as bing
    monkeypatch.setenv("BING_WEBMASTER_API_KEY", "k")
    monkeypatch.setenv("BING_SITE_URL", "site")
    monkeypatch.setattr(bing, "_get", lambda method, **params: {"d": []})
    rows = bing.run()
    assert len(rows) == 1
    assert rows[0]["status"] == "no_data"
    assert rows[0]["error"] == "No disponible: Bing Webmaster returned no statistics"


def test_bing_partial_success_adds_warning(monkeypatch):
    import src.connectors.bing_webmaster as bing
    monkeypatch.setenv("BING_WEBMASTER_API_KEY", "k")
    monkeypatch.setenv("BING_SITE_URL", "site")
    def fake_get(method, **params):
        if method == "GetPageStats":
            raise RuntimeError("not supported")
        return {"d": [{"Query": "q", "Clicks": 1, "Impressions": 2}]}
    monkeypatch.setattr(bing, "_get", fake_get)
    rows = bing.run()
    assert any(r["status"] == "ok" for r in rows)
    warning = [r for r in rows if r["status"] == "warning"][0]
    assert warning["endpoint"] == "GetPageStats"
    assert "GetPageStats unavailable or unsupported" in warning["error"]


def test_bing_total_failure_returns_error(monkeypatch):
    import src.connectors.bing_webmaster as bing
    monkeypatch.setenv("BING_WEBMASTER_API_KEY", "k")
    monkeypatch.setenv("BING_SITE_URL", "site")
    monkeypatch.setattr(bing, "_get", lambda method, **params: (_ for _ in ()).throw(RuntimeError(f"{method} boom")))
    rows = bing.run()
    assert len(rows) == 1
    assert rows[0]["status"] == "error"
    assert "GetQueryStats" in rows[0]["error"] and "GetPageStats" in rows[0]["error"] and "GetRankAndTrafficStats" in rows[0]["error"]


def test_bing_detailed_partial_success_adds_query_warning(monkeypatch):
    import src.connectors.bing_webmaster as bing
    monkeypatch.setenv("BING_WEBMASTER_API_KEY", "k")
    monkeypatch.setenv("BING_SITE_URL", "site")
    monkeypatch.setattr(bing, "active_unique_queries", lambda: ["ok query", "bad query"])
    def fake_get(method, **params):
        if method in bing.GENERAL_METHODS:
            return {"d": []}
        if params.get("query") == "bad query":
            raise RuntimeError("query failed")
        return {"d": [{"Query": "returned", "Clicks": 1, "Impressions": 2}]}
    monkeypatch.setattr(bing, "_get", fake_get)
    rows = bing.run(bing_detailed=True)
    ok = [r for r in rows if r["status"] == "ok"]
    warnings = [r for r in rows if r["status"] == "warning"]
    assert ok and ok[0]["requested_query"] == "ok query"
    assert len(warnings) == 1
    assert warnings[0]["endpoint"] == "GetQueryPageStats"
    assert warnings[0]["requested_query"] == "bad query"
    assert warnings[0]["url"] == "" and warnings[0]["clicks"] == "" and warnings[0]["impressions"] == ""


def test_bing_empty_responses_do_not_create_ok_rows_and_dry_run_no_connection(monkeypatch):
    import src.connectors.bing_webmaster as bing
    monkeypatch.setenv("BING_WEBMASTER_API_KEY", "k")
    monkeypatch.setenv("BING_SITE_URL", "site")
    called = {"value": False}
    def fake_get(method, **params):
        called["value"] = True
        return {"d": {}}
    monkeypatch.setattr(bing, "_get", fake_get)
    assert all(r["status"] != "ok" for r in bing.run())
    called["value"] = False
    assert bing.run(dry_run=True)[0]["status"] == "dry_run"
    assert called["value"] is False
