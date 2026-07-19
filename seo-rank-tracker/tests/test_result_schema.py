import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.models import Result, RESULT_COLUMNS
from src.validators import validate_result_schema

def test_result_schema_empty_response():
    row = Result(status="no_data", error="No disponible").to_row()
    assert set(RESULT_COLUMNS) == set(row)
    assert validate_result_schema([row])

from src.reports.export_csv import export as export_csv
from src.reports.export_html import export as export_html


def test_report_generation(tmp_path):
    row = Result(source="google_search_console", average_position="2.5").to_row()
    csv_path = export_csv([row], "data/results/test-report.csv")
    html_path = export_html([row], "data/results/test-report.html")
    assert csv_path.exists()
    assert html_path.exists()
