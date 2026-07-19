import csv, json, os, re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover - dependency absence is handled by env fallback
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

def load_queries(include_inactive=True):
    with (ROOT / "data/queries.csv").open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    if include_inactive:
        return rows
    return [row for row in rows if row.get("active", "").lower() == "true"]

def query_lookup(include_inactive=True):
    lookup = {}
    for row in load_queries(include_inactive=include_inactive):
        key = (normalize_query(row.get("query")), (row.get("device") or "").casefold())
        lookup.setdefault(key, row)
    return lookup

def env(name):
    return os.environ.get(name, "")
