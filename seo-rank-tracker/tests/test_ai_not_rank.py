import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import types
import pytest
from src.models import Result
from src.connectors.google_search_console import period_range, previous_period, enrich_row, QUERY_DIMENSIONS, authorize
from src.connectors.google_search_console import run as run_gsc
from src.connectors.bing_webmaster import run as run_bing
from src.connectors.google_ai_import import run as run_ai_import


def test_ai_mentions_never_rank():
    row = Result(surface="google_generative_ai", brand_mentioned="true").to_row()
    assert row["exact_organic_position"] == ""
    with pytest.raises(ValueError):
        Result(surface="google_generative_ai", brand_mentioned="true", exact_organic_position="1")


def test_periods_and_previous_period():
    start, end = period_range("7d")
    ps, pe = previous_period("2026-07-08", "2026-07-14")
    assert (ps, pe) == ("2026-07-01", "2026-07-07")
    assert start <= end


def test_missing_credentials_empty_import_and_dry_run(monkeypatch):
    for key in ["GSC_PROPERTY", "GOOGLE_CLIENT_SECRET_FILE", "GOOGLE_TOKEN_FILE", "BING_WEBMASTER_API_KEY", "BING_SITE_URL"]:
        monkeypatch.delenv(key, raising=False)
    assert run_gsc()[0]["status"] == "error"
    assert run_bing()[0]["status"] == "error"
    assert run_ai_import()[0]["status"] in {"no_data", "ok"}
    assert run_gsc(dry_run=True)[0]["status"] == "dry_run"
    assert run_bing(dry_run=True)[0]["status"] == "dry_run"
    assert run_ai_import(dry_run=True)[0]["status"] == "dry_run"


def test_gsc_date_dimension_and_query_enrichment():
    assert QUERY_DIMENSIONS == ["date", "query", "page", "country", "device"]
    item = {"keys": ["2026-07-18", "  Scooter Rental Barcelona ", "https://rentalscooterbarcelona.com/", "esp", "mobile"], "position": 3.5, "clicks": 1, "impressions": 10, "ctr": 0.1}
    prev = {("  Scooter Rental Barcelona ", "https://rentalscooterbarcelona.com/", "esp", "mobile"): 5.0}
    configured = {("scooter rental barcelona", "mobile"): {"query_id":"qid", "category":"scooter", "language":"en", "scenario":"TOURIST_IN_BARCELONA", "search_city":"Barcelona", "expected_language_path":"/"}}
    row = enrich_row(item, configured, "7d", prev)
    assert row["date"] == "2026-07-18"
    assert row["configured_query"] == "true"
    assert row["language_source"] == "configured_query"
    assert row["query_id"] == "qid"
    assert row["previous_average_position"] == "5.0"
    assert row["position_change"] == "-1.5"
    assert row["exact_organic_position"] == ""


def test_unconfigured_query_language_source():
    item = {"keys": ["2026-07-18", "consulta rara", "https://rentalscooterbarcelona.com/cat/page/", "esp", "desktop"], "position": 8}
    row = enrich_row(item, {}, "7d", {})
    assert row["configured_query"] == "false"
    assert row["language"] == "ca"
    assert row["language_source"] == "landing_page_path"


def test_first_oauth_without_token(monkeypatch, tmp_path):
    secret = tmp_path / "client_secret.json"; secret.write_text("{}")
    token = tmp_path / "token.json"
    monkeypatch.setenv("GOOGLE_CLIENT_SECRET_FILE", str(secret))
    monkeypatch.setenv("GOOGLE_TOKEN_FILE", str(token))
    class FakeCreds:
        valid = True; expired = False; refresh_token = None
        def to_json(self): return '{"token":"x"}'
    class FakeFlow:
        @classmethod
        def from_client_secrets_file(cls, filename, scopes): return cls()
        def run_local_server(self, port=0): return FakeCreds()
    sys.modules['google.auth.transport.requests'] = types.SimpleNamespace(Request=object)
    sys.modules['google.oauth2.credentials'] = types.SimpleNamespace(Credentials=types.SimpleNamespace(from_authorized_user_file=lambda *a, **k: None))
    sys.modules['google_auth_oauthlib.flow'] = types.SimpleNamespace(InstalledAppFlow=FakeFlow)
    assert authorize().valid
    assert token.exists()


def test_refresh_and_invalid_token(monkeypatch, tmp_path):
    secret = tmp_path / "client_secret.json"; secret.write_text("{}")
    token = tmp_path / "token.json"; token.write_text("{}")
    monkeypatch.setenv("GOOGLE_CLIENT_SECRET_FILE", str(secret))
    monkeypatch.setenv("GOOGLE_TOKEN_FILE", str(token))
    class FakeCreds:
        valid = False; expired = True; refresh_token = "r"
        def refresh(self, request): self.valid = True; self.expired = False
        def to_json(self): return '{"token":"refreshed"}'
    sys.modules['google.auth.transport.requests'] = types.SimpleNamespace(Request=object)
    sys.modules['google.oauth2.credentials'] = types.SimpleNamespace(Credentials=types.SimpleNamespace(from_authorized_user_file=lambda *a, **k: FakeCreds()))
    sys.modules['google_auth_oauthlib.flow'] = types.SimpleNamespace(InstalledAppFlow=object)
    assert authorize().valid
    sys.modules['google.oauth2.credentials'] = types.SimpleNamespace(Credentials=types.SimpleNamespace(from_authorized_user_file=lambda *a, **k: (_ for _ in ()).throw(ValueError("bad"))))
    with pytest.raises(ValueError):
        authorize()


def test_bing_simulated_response(monkeypatch):
    monkeypatch.setenv("BING_WEBMASTER_API_KEY", "k")
    monkeypatch.setenv("BING_SITE_URL", "https://example.com/")
    import src.connectors.bing_webmaster as bing
    monkeypatch.setattr(bing, "_get", lambda method: {"d": [{"Date":"2026-07-18", "Query":"q", "Page":"u", "Clicks":2, "Impressions":4, "AvgImpressionPosition":3.2}]})
    rows = run_bing()
    assert rows[0]["source"] == "bing_webmaster"
    assert rows[0]["average_position"] == "3.2"
