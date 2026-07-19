import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from collections import defaultdict
from src.config import load_queries, normalize_query
from src.validators import validate_query_schema

def test_queries_schema_devices_scenarios_and_categories():
    rows = load_queries()
    assert validate_query_schema(rows)
    assert {"TOURIST_IN_BARCELONA", "PRE_TRIP_ORIGIN"} <= {r["scenario"] for r in rows}
    assert any(r["active"] == "true" for r in rows)
    assert all(r["active"] == "false" for r in rows if r["scenario"] == "PRE_TRIP_ORIGIN")
    grouped = defaultdict(set)
    by_query = {}
    for r in rows:
        grouped[(r["language"], r["scenario"], r["query"])].add(r["device"])
        by_query[(normalize_query(r["query"]), r["language"])] = r["category"]
    assert all({"mobile", "desktop"} <= devices for devices in grouped.values())
    assert by_query[("motorbike rental barcelona", "en")] == "motorbike"
    assert by_query[("motorroller mieten barcelona", "de")] == "scooter"
    assert by_query[("hyra motorcykel barcelona", "sv")] == "motorbike"
