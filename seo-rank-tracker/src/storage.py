import csv
from pathlib import Path
from .models import RESULT_COLUMNS

ROOT = Path(__file__).resolve().parents[1]

def write_results(rows, relative_path):
    path = ROOT / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=RESULT_COLUMNS)
        writer.writeheader()
        for row in rows:
            writer.writerow({column: row.get(column, "") or "" for column in RESULT_COLUMNS})
    return path

def read_results(relative_path):
    path = ROOT / relative_path
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))
