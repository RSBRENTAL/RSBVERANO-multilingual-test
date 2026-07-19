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
