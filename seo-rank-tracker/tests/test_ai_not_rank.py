import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pytest
from src.models import Result
from src.connectors.google_search_console import period_range, previous_period

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

from src.connectors.google_search_console import run as run_gsc
from src.connectors.bing_webmaster import run as run_bing
from src.connectors.google_ai_import import run as run_ai_import


def test_missing_credentials_and_empty_import(monkeypatch):
    for key in ["GSC_PROPERTY", "GOOGLE_CLIENT_SECRET_FILE", "GOOGLE_TOKEN_FILE", "BING_WEBMASTER_API_KEY", "BING_SITE_URL"]:
        monkeypatch.delenv(key, raising=False)
    assert run_gsc()[0]["status"] == "error"
    assert run_bing()[0]["status"] == "error"
    assert run_ai_import()[0]["status"] in {"no_data", "ok"}
