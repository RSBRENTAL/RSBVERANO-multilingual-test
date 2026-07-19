import csv
from pathlib import Path
from ..models import Result

ROOT = Path(__file__).resolve().parents[2]
KNOWN = {"date","page","url","country","device","impressions","brand_mentioned","domain_cited","citation_url"}

def run(dry_run=False):
    folder = ROOT / "imports/google-ai"
    files = sorted(folder.glob("*.csv"))
    if dry_run:
        return [Result(source="google_search_console", engine="google", surface="google_generative_ai", status="dry_run", error=f"dry_run: {len(files)} import files found").to_row()]
    rows=[]
    for path in files:
        with path.open(newline="", encoding="utf-8") as handle:
            reader = csv.DictReader(handle)
            unknown = [c for c in (reader.fieldnames or []) if c not in KNOWN]
            for item in reader:
                rows.append(Result(date=item.get("date", ""), source="google_search_console", engine="google", surface="google_generative_ai", country=item.get("country", ""), device=item.get("device", ""), impressions=item.get("impressions", ""), url=item.get("page") or item.get("url", ""), ai_feature_present="true", brand_mentioned=item.get("brand_mentioned", ""), domain_cited=item.get("domain_cited", ""), citation_url=item.get("citation_url", ""), status="ok", error=("Unknown columns: " + ",".join(unknown)) if unknown else "").to_row())
    return rows or [Result(source="google_search_console", engine="google", surface="google_generative_ai", status="no_data", error="No disponible").to_row()]
