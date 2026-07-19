from datetime import date, timedelta
from ..config import env, load_queries
from ..models import Result

READONLY_SCOPE = "https://www.googleapis.com/auth/webmasters.readonly"

PERIOD_DAYS = {"7d": 7, "28d": 28, "3m": 90}

def period_range(period="7d", start_date=None, end_date=None):
    if start_date and end_date:
        return start_date, end_date
    days = PERIOD_DAYS.get(period, 7)
    end = date.today() - timedelta(days=1)
    start = end - timedelta(days=days - 1)
    return start.isoformat(), end.isoformat()

def previous_period(start, end):
    s = date.fromisoformat(start); e = date.fromisoformat(end)
    days = (e - s).days + 1
    pe = s - timedelta(days=1)
    ps = pe - timedelta(days=days - 1)
    return ps.isoformat(), pe.isoformat()

def language_from_page(url, configured=""):
    if configured:
        return configured, "configured_query"
    paths = {"/es/":"es","/fr/":"fr","/it/":"it","/de/":"de","/nl/":"nl","/pt/":"pt","/cat/":"ca","/sv/":"sv","/pl/":"pl"}
    for path, code in paths.items():
        if path in url:
            return code, "landing_page_path"
    if "rentalscooterbarcelona.com/" in url:
        return "en", "landing_page_path"
    return "unknown", "unknown"

def run(dry_run=False, period="7d", start_date=None, end_date=None):
    start, end = period_range(period, start_date, end_date)
    if dry_run:
        return [Result(source="google_search_console", engine="google", surface="search_console", scenario="TOURIST_IN_BARCELONA", status="ok", error=f"dry-run: {start} to {end}").to_row()]
    if not env("GSC_PROPERTY") or not env("GOOGLE_CLIENT_SECRET_FILE") or not env("GOOGLE_TOKEN_FILE"):
        return [Result(source="google_search_console", engine="google", surface="search_console", status="error", error="No disponible: missing Google Search Console credentials").to_row()]
    try:
        from google_auth_oauthlib.flow import InstalledAppFlow
        from google.oauth2.credentials import Credentials
        from googleapiclient.discovery import build
        from googleapiclient.errors import HttpError
    except ImportError as exc:
        return [Result(source="google_search_console", engine="google", surface="search_console", status="error", error=f"No disponible: dependency missing: {exc}").to_row()]
    # Network/API execution is intentionally minimal and read-only; pagination supported via rowLimit/startRow.
    try:
        token_file = env("GOOGLE_TOKEN_FILE")
        creds = Credentials.from_authorized_user_file(token_file, [READONLY_SCOPE])
        service = build("searchconsole", "v1", credentials=creds)
        rows=[]; start_row=0; row_limit=25000
        while True:
            body={"startDate":start,"endDate":end,"dimensions":["query","page","country","device"],"rowLimit":row_limit,"startRow":start_row}
            response=service.searchanalytics().query(siteUrl=env("GSC_PROPERTY"), body=body).execute()
            batch=response.get("rows", [])
            if not batch: break
            for item in batch:
                keys=item.get("keys", ["", "", "", ""])
                lang, _src = language_from_page(keys[1], "")
                rows.append(Result(source="google_search_console", engine="google", surface="search_console", language=lang, query=keys[0], country=keys[2], device=keys[3], average_position=item.get("position", ""), url=keys[1], clicks=item.get("clicks", ""), impressions=item.get("impressions", ""), ctr=item.get("ctr", ""), status="ok").to_row())
            if len(batch) < row_limit: break
            start_row += row_limit
        return rows or [Result(source="google_search_console", engine="google", surface="search_console", status="no_data", error="No disponible").to_row()]
    except Exception as exc:
        return [Result(source="google_search_console", engine="google", surface="search_console", status="error", error=f"No disponible: {exc}").to_row()]
