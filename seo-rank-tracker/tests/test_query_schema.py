import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from collections import defaultdict
import pytest
from src.config import load_queries, normalize_query, query_lookup
from src.validators import validate_query_schema

def test_queries_schema_devices_scenarios_and_categories():
    rows = load_queries()
    assert validate_query_schema(rows)
    assert {"TOURIST_IN_BARCELONA", "PRE_TRIP_ORIGIN"} <= {r["scenario"] for r in rows}
    grouped = defaultdict(set); by_query = {}
    for r in rows:
        grouped[(r["language"], r["scenario"], r["query"])].add(r["device"])
        by_query[(normalize_query(r["query"]), r["language"])] = r["category"]
    assert all({"mobile", "desktop"} <= devices for devices in grouped.values())
    assert by_query[("motorbike rental barcelona", "en")] == "motorbike"
    assert by_query[("motorroller mieten barcelona", "de")] == "scooter"
    assert by_query[("hyra motorcykel barcelona", "sv")] == "motorbike"


def test_active_query_index_excludes_inactive_and_detects_duplicates(monkeypatch):
    rows = [{"query":"q", "device":"mobile", "engine":"google", "surface":"search_console", "active":"true"}, {"query":"q", "device":"mobile", "engine":"google", "surface":"search_console", "active":"false"}]
    import src.config as config
    monkeypatch.setattr(config, "load_queries", lambda include_inactive=True: rows)
    assert len(config.query_lookup(include_inactive=False)) == 1
    rows[1]["active"] = "true"
    with pytest.raises(ValueError): config.query_lookup(include_inactive=False)


def test_custom_period_validation_no_connection():
    from src.main import main
    with pytest.raises(SystemExit):
        main(["all", "--period", "custom", "--dry-run"])
    with pytest.raises(SystemExit):
        main(["all", "--period", "custom", "--start-date", "2026-07-20", "--end-date", "2026-07-19", "--dry-run"])
