import csv, json, os, re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover
    load_dotenv = None


def _fallback_load_dotenv(path):
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


if load_dotenv:
    load_dotenv(ROOT / ".env", override=False)
else:
    _fallback_load_dotenv(ROOT / ".env")


def load_json(relative_path):
    with (ROOT / relative_path).open(encoding="utf-8") as handle:
        return json.load(handle)


def load_languages():
    return load_json("config/languages.json")["languages"]


def language_paths():
    return {item["code"]: item["path"] for item in load_languages()}


def normalize_query(value):
    return re.sub(r"\s+", " ", (value or "").strip().casefold())


def _load_query_csv_files():
    rows = []
    query_files = [ROOT / "data/queries.csv"]
    query_files.extend(sorted((ROOT / "data").glob("queries-priority-*.csv")))
    for path in query_files:
        if not path.exists():
            continue
        with path.open(newline="", encoding="utf-8") as handle:
            rows.extend(csv.DictReader(handle))
    return rows


def _load_generated_priority_queries():
    path = ROOT / "config/priority_queries.json"
    if not path.exists():
        return []
    payload = load_json("config/priority_queries.json")
    scenario = payload["scenario"]
    rows = []
    for language, language_config in payload["languages"].items():
        sequence = 200
        for category in ("scooter", "rollerblades"):
            for query in language_config.get(category, []):
                for device in ("mobile", "desktop"):
                    rows.append({
                        "query_id": f"{language}_tourist_in_barcelona_{device}_{sequence:03d}",
                        "category": category,
                        "language": language,
                        "scenario": scenario["id"],
                        "search_country": scenario["search_country"],
                        "search_city": scenario["search_city"],
                        "latitude": scenario["latitude"],
                        "longitude": scenario["longitude"],
                        "device": device,
                        "engine": "google",
                        "surface": "search_console",
                        "query": query,
                        "expected_language_path": language_config["path"],
                        "active": "true",
                    })
                sequence += 1
    return rows


def load_queries(include_inactive=True):
    rows = _load_query_csv_files() + _load_generated_priority_queries()
    if include_inactive:
        return rows
    return [row for row in rows if row.get("active", "").lower() == "true"]


def query_lookup(include_inactive=False, engine="google", surface="search_console"):
    lookup = {}
    duplicates = []
    for row in load_queries(include_inactive=include_inactive):
        if not include_inactive and row.get("active", "").lower() != "true":
            continue
        key = (
            normalize_query(row.get("query")),
            (row.get("device") or "").casefold(),
            (row.get("engine") or "").casefold(),
            (row.get("surface") or "").casefold(),
        )
        if engine and key[2] != engine:
            continue
        if surface and key[3] != surface:
            continue
        if key in lookup:
            duplicates.append(key)
        lookup[key] = row
    if duplicates:
        raise ValueError(f"Duplicate active query keys: {duplicates}")
    return lookup


def active_unique_queries(engine="google", surface="search_console"):
    seen = []
    keys = set()
    for row in load_queries(include_inactive=False):
        if row.get("engine") != engine or row.get("surface") != surface:
            continue
        key = normalize_query(row.get("query"))
        if key not in keys:
            keys.add(key)
            seen.append(row.get("query", ""))
    return seen


def env(name):
    return os.environ.get(name, "")
