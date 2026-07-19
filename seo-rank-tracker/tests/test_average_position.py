import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pytest
from src.models import Result

def test_average_position_not_exact_position():
    row = Result(source="google_search_console", average_position="4.2").to_row()
    assert row["exact_organic_position"] == ""
    with pytest.raises(ValueError):
        Result(average_position="4.2", exact_organic_position="4")

def test_dry_run_status_required():
    with pytest.raises(ValueError):
        Result(status="ok", error="dry-run: no")
