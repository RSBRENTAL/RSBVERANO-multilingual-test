import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import subprocess
from src.models import Result, RESULT_COLUMNS
from src.validators import validate_result_schema
from src.reports.export_csv import export as export_csv
from src.reports.export_html import export as export_html


def test_result_schema_empty_response_and_new_columns():
    row = Result(status="no_data", error="No disponible").to_row()
    assert set(RESULT_COLUMNS) == set(row)
    for column in ["date", "row_type", "endpoint", "query_id", "category", "configured_query", "language_source", "expected_language_path", "country_format", "period", "previous_average_position", "position_change"]:
        assert column in row
    assert validate_result_schema([row])


def test_report_generation_html_filters_and_sections():
    rows = [Result(source="google_search_console", surface="search_console", row_type="period_summary", status="dry_run").to_row(), Result(source="google_search_console", surface="google_generative_ai", status="ok").to_row(), Result(source="bing_webmaster", surface="bing_webmaster", endpoint="GetQueryStats", status="ok").to_row()]
    csv_path = export_csv(rows, "data/results/test-report.csv")
    html_path = export_html(rows, "data/results/test-report.html")
    html = html_path.read_text(encoding="utf-8")
    assert csv_path.exists() and "function filterRows" in html
    assert "data-filter='row_type'" in html and "data-filter='endpoint'" in html
    assert html.count("Google generative AI importado") == 1
    assert "dry-run" in html
    csv_path.unlink(); html_path.unlink()


def test_generated_reports_are_ignored_by_git():
    ignored = subprocess.run(["git", "check-ignore", "seo-rank-tracker/reports/latest-report.csv"], cwd=Path(__file__).resolve().parents[2], text=True, capture_output=True)
    assert ignored.returncode == 0


def test_result_schema_new_limit_and_bing_fields():
    row = Result(requested_query="requested", returned_query_value="returned", data_limit_reached="true").to_row()
    assert row["requested_query"] == "requested"
    assert row["returned_query_value"] == "returned"
    assert row["data_limit_reached"] == "true"


def test_html_indicators_for_warning_and_unreliable_comparison():
    from src.reports.export_html import indicator
    assert indicator(Result(status="warning").to_row()) == "warning"
    assert indicator(Result(comparison_reliable="false").to_row()) == "comparación no fiable"


def test_html_new_limit_filters():
    html_path = export_html([Result(row_type="period_summary", current_period_limit_days="2026-07-18", previous_period_limit_days="2026-07-11", limit_period="current", comparison_reliable="false").to_row()], "data/results/test-limit-filter.html")
    html = html_path.read_text(encoding="utf-8")
    assert "data-filter='current_period_limit_days'" in html
    assert "data-filter='previous_period_limit_days'" in html
    assert "data-filter='limit_period'" in html
    html_path.unlink()


def test_limited_date_validators():
    assert validate_result_schema([Result(current_period_limit_days="2026-07-18,2026-07-19", limit_period="current", comparison_reliable="false").to_row()])
    import pytest
    with pytest.raises(ValueError):
        validate_result_schema([Result(current_period_limit_days="18-07-2026").to_row()])
    with pytest.raises(ValueError):
        validate_result_schema([Result(limit_period="both").to_row()])


def _cleanup_report_files():
    for name in ["google-search-console.csv", "bing-webmaster.csv", "google-generative-ai.csv", "latest-report.csv", "latest-report.html"]:
        (Path(__file__).resolve().parents[1] / "reports" / name).unlink(missing_ok=True)


def test_report_combines_three_existing_source_files():
    from src.main import run_report
    from src.storage import read_results
    _cleanup_report_files()
    g = Result(source="google_search_console", surface="search_console", status="ok", query="g").to_row()
    b = Result(source="bing_webmaster", surface="bing_webmaster", status="warning", query="b").to_row()
    ai = Result(source="google_search_console", surface="google_generative_ai", status="no_data", query="ai").to_row()
    export_csv([g], "reports/google-search-console.csv")
    export_csv([b], "reports/bing-webmaster.csv")
    export_csv([ai], "reports/google-generative-ai.csv")
    rows = run_report(rows=None)
    latest = read_results("reports/latest-report.csv")
    html = (Path(__file__).resolve().parents[1] / "reports/latest-report.html").read_text(encoding="utf-8")
    assert [r["query"] for r in rows] == ["g", "b", "ai"]
    assert [r["query"] for r in latest] == ["g", "b", "ai"]
    assert "Google Search Console" in html and "Bing Webmaster Tools" in html and "Google generative AI importado" in html
    _cleanup_report_files()


def test_report_combines_single_existing_file_and_ignores_missing():
    from src.main import run_report
    _cleanup_report_files()
    row = Result(source="bing_webmaster", surface="bing_webmaster", status="error", query="only").to_row()
    export_csv([row], "reports/bing-webmaster.csv")
    rows = run_report(rows=None)
    assert len(rows) == 1 and rows[0]["query"] == "only" and rows[0]["status"] == "error"
    _cleanup_report_files()


def test_report_no_source_files_generates_no_data():
    from src.main import run_report
    from src.storage import read_results
    _cleanup_report_files()
    rows = run_report(rows=None)
    assert rows[0]["source"] == "report"
    assert rows[0]["status"] == "no_data"
    assert rows[0]["error"] == "No disponible: no source report files found"
    assert read_results("reports/latest-report.csv")[0]["status"] == "no_data"
    _cleanup_report_files()


def test_report_explicit_rows_do_not_read_or_duplicate_local_files():
    from src.main import run_report
    _cleanup_report_files()
    local = Result(source="bing_webmaster", status="ok", query="local").to_row()
    explicit = Result(source="report", status="warning", query="explicit").to_row()
    export_csv([local], "reports/bing-webmaster.csv")
    rows = run_report(rows=[explicit])
    assert rows == [explicit]
    from src.storage import read_results
    latest = read_results("reports/latest-report.csv")
    assert len(latest) == 1 and latest[0]["query"] == "explicit"
    _cleanup_report_files()


def test_report_explicit_empty_list_does_not_read_sources():
    from src.main import run_report
    from src.storage import read_results
    _cleanup_report_files()
    export_csv([Result(source="bing_webmaster", status="ok", query="local").to_row()], "reports/bing-webmaster.csv")
    rows = run_report(rows=[])
    assert rows == []
    assert read_results("reports/latest-report.csv") == []
    _cleanup_report_files()


def test_report_dry_run_reads_metadata_without_writing_latest():
    from src.main import run_report
    _cleanup_report_files()
    export_csv([Result(source="bing_webmaster", status="ok", query="local").to_row()], "reports/bing-webmaster.csv")
    rows = run_report(rows=None, dry_run=True)
    root = Path(__file__).resolve().parents[1]
    assert rows[0]["status"] == "dry_run"
    assert "rows_available=1" in rows[0]["error"]
    assert not (root / "reports/latest-report.csv").exists()
    assert not (root / "reports/latest-report.html").exists()
    _cleanup_report_files()


def test_report_integrity_preserves_statuses_and_columns():
    from src.main import run_report
    _cleanup_report_files()
    rows = [Result(source="report", status=status, query=status).to_row() for status in ["ok", "warning", "error", "no_data"]]
    export_csv(rows, "reports/google-search-console.csv")
    combined = run_report(rows=None)
    assert [r["status"] for r in combined] == ["ok", "warning", "error", "no_data"]
    assert all(set(RESULT_COLUMNS) == set(row) for row in combined)
    _cleanup_report_files()
