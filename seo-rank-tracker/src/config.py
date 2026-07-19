import csv, json, os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def load_json(relative_path):
    with (ROOT / relative_path).open(encoding="utf-8") as handle:
        return json.load(handle)

def load_languages():
    return load_json("config/languages.json")["languages"]

def language_paths():
    return {item["code"]: item["path"] for item in load_languages()}

def load_queries(include_inactive=True):
    with (ROOT / "data/queries.csv").open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    if include_inactive:
        return rows
    return [row for row in rows if row.get("active", "").lower() == "true"]

def env(name):
    return os.environ.get(name, "")
