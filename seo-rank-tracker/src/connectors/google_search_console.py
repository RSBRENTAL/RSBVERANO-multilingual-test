from datetime import date, timedelta
from pathlib import Path
from urllib.error import URLError
from ..config import env, query_lookup, normalize_query, language_paths, load_queries
from ..models import Result

READONLY_SCOPE = "https://www.googleapis.com/auth/webmasters.readonly"
PERIOD_DAYS = {"7d": 7, "28d": 28, "3m": 90}
QUERY_DIMENSIONS = ["date", "query", "page", "country", "device"]

LANG_HINTS = {
    "es": ["alquiler", "moto", "patines", "bicicletas", "playa"],
    "fr": ["location", "barcelone", "vélo", "rollers"],
    "it": ["noleggio", "barcellona", "pattini", "spiaggia"],
    "de": ["mieten", "fahrrad", "strand", "motorrad", "motorroller"],
    "nl": ["huren", "fiets", "strand", "skeelers"],
    "pt": ["aluguel", "patins", "bicicleta", "praia"],
    "ca": ["lloguer", "patins", "bicicletes", "platja"],
    "sv": ["hyra", "cykeluthyrning", "strand", "motorcykel"],
    "pl": ["wynajem", "skutera", "motocykla", "rolek", "roweru", "plaża"],
}

def period_range(period="7d", start_date=None, end_date=None):
    if period == "custom" and start_date and end_date:
        return start_date, end_date
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

def detect_query_language(query):
    q = normalize_query(query)
    for lang, hints in LANG_HINTS.items():
        if any(h in q for h in hints):
            return lang, "query_detection"
    if q:
        return "en", "query_detection"
    return "unknown", "unknown"

def language_from_page(url):
    for code, path in language_paths().items():
        if code == "en":
            continue
        if path and path in (url or ""):
            return code, "landing_page_path"
    if "rentalscooterbarcelona.com/" in (url or ""):
        return "en", "landing_page_path"
    return "unknown", "unknown"

def enrich_row(item, configured, period, previous_index=None):
    keys = item.get("keys", ["", "", "", "", ""])
    row_date, query, page, country, device = (keys + [""] * 5)[:5]
    query_key = (normalize_query(query), device.casefold())
    config = configured.get(query_key)
    language = "unknown"; language_source = "unknown"; query_id = category = expected_path = scenario = city = ""; configured_query = "false"
    if config:
        language = config.get("language", "unknown")
        language_source = "configured_query"
        query_id = config.get("query_id", "")
        category = config.get("category", "")
        expected_path = config.get("expected_language_path", "")
        scenario = config.get("scenario", "")
        city = config.get("search_city", "")
        configured_query = "true"
    else:
        language, language_source = language_from_page(page)
        if language_source == "unknown":
            language, language_source = detect_query_language(query)
        expected_path = language_paths().get(language, "")
    average = item.get("position", "")
    previous = ""; change = ""
    if previous_index is not None:
        prev = previous_index.get((query, page, country, device))
        if prev not in (None, "") and average not in (None, ""):
            previous = prev
            change = str(round(float(average) - float(prev), 4))
    return Result(
        date=row_date, source="google_search_console", engine="google", surface="search_console",
        scenario=scenario, language=language, language_source=language_source, query_id=query_id,
        category=category, configured_query=configured_query, query=query, expected_language_path=expected_path,
        country=country, city=city, device=device, period=period, average_position=average,
        previous_average_position=previous, position_change=change, url=page, clicks=item.get("clicks", ""),
        impressions=item.get("impressions", ""), ctr=item.get("ctr", ""), status="ok"
    ).to_row()

def authorize():
    secret = env("GOOGLE_CLIENT_SECRET_FILE")
    token_file = env("GOOGLE_TOKEN_FILE")
    if not secret or not Path(secret).exists():
        raise FileNotFoundError("client secret inexistente")
    try:
        from google.auth.transport.requests import Request
        from google.oauth2.credentials import Credentials
        from google_auth_oauthlib.flow import InstalledAppFlow
    except ImportError as exc:
        raise RuntimeError(f"dependencia OAuth no disponible: {exc}") from exc
    creds = None
    if token_file and Path(token_file).exists():
        try:
            creds = Credentials.from_authorized_user_file(token_file, [READONLY_SCOPE])
        except Exception as exc:
            raise ValueError(f"token inválido: {exc}") from exc
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
    if not creds or not creds.valid:
        flow = InstalledAppFlow.from_client_secrets_file(secret, [READONLY_SCOPE])
        creds = flow.run_local_server(port=0)
    if not token_file:
        raise ValueError("GOOGLE_TOKEN_FILE no configurado")
    Path(token_file).parent.mkdir(parents=True, exist_ok=True)
    Path(token_file).write_text(creds.to_json(), encoding="utf-8")
    return creds

def fetch(service, site_url, start, end):
    rows=[]; start_row=0; row_limit=25000
    while True:
        body={"startDate":start,"endDate":end,"dimensions":QUERY_DIMENSIONS,"rowLimit":row_limit,"startRow":start_row}
        response=service.searchanalytics().query(siteUrl=site_url, body=body).execute()
        batch=response.get("rows", [])
        if not batch:
            break
        rows.extend(batch)
        if len(batch) < row_limit:
            break
        start_row += row_limit
    return rows

def dry_run_rows(period, start, end):
    active = load_queries(include_inactive=False)
    missing = [name for name in ["GSC_PROPERTY", "GOOGLE_CLIENT_SECRET_FILE", "GOOGLE_TOKEN_FILE"] if not env(name)]
    return [Result(source="google_search_console", engine="google", surface="search_console", period=period,
                   status="dry_run", error=f"dry_run: would query {QUERY_DIMENSIONS} from {start} to {end}; active_queries={len(active)}; missing_credentials={','.join(missing) or 'none'}").to_row()]

def run(dry_run=False, period="7d", start_date=None, end_date=None):
    start, end = period_range(period, start_date, end_date)
    if dry_run:
        return dry_run_rows(period, start, end)
    if not env("GSC_PROPERTY") or not env("GOOGLE_CLIENT_SECRET_FILE") or not env("GOOGLE_TOKEN_FILE"):
        return [Result(source="google_search_console", engine="google", surface="search_console", status="error", error="No disponible: missing Google Search Console credentials").to_row()]
    try:
        from googleapiclient.discovery import build
        from googleapiclient.errors import HttpError
        creds = authorize()
        service = build("searchconsole", "v1", credentials=creds)
        current = fetch(service, env("GSC_PROPERTY"), start, end)
        ps, pe = previous_period(start, end)
        previous = fetch(service, env("GSC_PROPERTY"), ps, pe)
        prev_index = {(r.get("keys", ["", "", "", "", ""])[1], r.get("keys", ["", "", "", "", ""])[2], r.get("keys", ["", "", "", "", ""])[3], r.get("keys", ["", "", "", "", ""])[4]): r.get("position", "") for r in previous}
        configured = query_lookup(include_inactive=True)
        return [enrich_row(item, configured, period, prev_index) for item in current] or [Result(source="google_search_console", engine="google", surface="search_console", status="no_data", error="No disponible").to_row()]
    except HttpError as exc:
        text = str(exc)
        if "quota" in text.lower(): msg = "No disponible: cuota agotada"
        elif "403" in text: msg = "No disponible: propiedad sin permisos"
        else: msg = f"No disponible: error Google API: {exc}"
        return [Result(source="google_search_console", engine="google", surface="search_console", status="error", error=msg).to_row()]
    except (ConnectionError, TimeoutError, URLError) as exc:
        return [Result(source="google_search_console", engine="google", surface="search_console", status="error", error=f"No disponible: error de red: {exc}").to_row()]
    except Exception as exc:
        return [Result(source="google_search_console", engine="google", surface="search_console", status="error", error=f"No disponible: {exc}").to_row()]
