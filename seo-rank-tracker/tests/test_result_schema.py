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
    for column in ["date", "query_id", "category", "configured_query", "language_source", "expected_language_path", "period", "previous_average_position", "position_change"]:
        assert column in row
    assert validate_result_schema([row])


def test_report_generation_and_html_filters():
    row = Result(source="google_search_console", language="en", category="scooter", status="dry_run").to_row()
    csv_path = export_csv([row], "data/results/test-report.csv")
    html_path = export_html([row], "data/results/test-report.html")
    html = html_path.read_text(encoding="utf-8")
    assert csv_path.exists()
    assert "function filterRows" in html
    assert "data-filter='status'" in html
    assert "dry-run" in html
    csv_path.unlink(); html_path.unlink()


def test_generated_reports_are_ignored_by_git():
    ignored = subprocess.run(["git", "check-ignore", "seo-rank-tracker/reports/latest-report.csv"], cwd=Path(__file__).resolve().parents[2], text=True, capture_output=True)
    assert ignored.returncode == 0
