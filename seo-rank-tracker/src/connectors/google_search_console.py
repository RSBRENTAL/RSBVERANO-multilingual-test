from collections import defaultdict
from datetime import date, timedelta
from pathlib import Path
from urllib.error import URLError
from urllib.parse import urlparse
from ..config import env, query_lookup, normalize_query, language_paths, load_queries
from ..models import Result

READONLY_SCOPE = "https://www.googleapis.com/auth/webmasters.readonly"
PERIOD_DAYS = {"7d": 7, "28d": 28, "3m": 90}
QUERY_DIMENSIONS = ["date", "query", "page", "country", "device"]
DATE_DIMENSIONS = ["date"]
SEARCH_TYPE = "web"
LANG_HINTS = {
    "es": ["alquiler", "patines", "bicicletas"], "fr": ["barcelone", "vélo", "rollers"],
    "it": ["noleggio", "barcellona", "pattini", "spiaggia"], "de": ["mieten", "fahrrad", "motorrad", "motorroller"],
    "nl": ["huren", "fiets", "skeelers"], "pt": ["aluguel", "patins", "bicicleta", "praia"],
    "ca": ["lloguer", "bicicletes", "platja"], "sv": ["hyra", "cykeluthyrning", "motorcykel"],
    "pl": ["wynajem", "skutera", "motocykla", "rolek", "roweru", "plaża"],
}

def previous_period(start, end):
    s = date.fromisoformat(start); e = date.fromisoformat(end)
    days = (e - s).days + 1
    pe = s - timedelta(days=1)
    ps = pe - timedelta(days=days - 1)
    return ps.isoformat(), pe.isoformat()

def discover_latest_date(service, site_url):
    end = date.today().isoformat(); start = (date.today() - timedelta(days=10)).isoformat()
    body = {"startDate": start, "endDate": end, "dimensions": DATE_DIMENSIONS, "type": SEARCH_TYPE, "dataState": "final", "rowLimit": 25000}
    rows = service.searchanalytics().query(siteUrl=site_url, body=body).execute().get("rows", [])
    dates = [r.get("keys", [""])[0] for r in rows if r.get("keys")]
    return max(dates) if dates else ""

def period_range(period="7d", start_date=None, end_date=None, latest_date=None):
    if end_date:
        end = date.fromisoformat(end_date)
    elif latest_date:
        end = date.fromisoformat(latest_date)
    else:
        end = date.today() - timedelta(days=1)
    if period == "custom" and start_date:
        start = date.fromisoformat(start_date)
    elif start_date and end_date:
        start = date.fromisoformat(start_date)
    else:
        days = PERIOD_DAYS.get(period, 7)
        start = end - timedelta(days=days - 1)
    return start.isoformat(), end.isoformat()

def each_day(start, end):
    cur = date.fromisoformat(start); last = date.fromisoformat(end)
    while cur <= last:
        yield cur.isoformat()
        cur += timedelta(days=1)

def detect_query_language(query):
    q = normalize_query(query)
    for lang, hints in LANG_HINTS.items():
        if any(h in q for h in hints):
            return lang, "query_detection"
    return "unknown", "unknown"

def language_from_page(url):
    parsed = urlparse(url or "")
    parts = [p for p in parsed.path.split("/") if p]
    first = f"/{parts[0]}/" if parts else "/"
    for code, path in language_paths().items():
        if path == "/" and not parts:
            return code, "landing_page_path"
        if path != "/" and first == path:
            return code, "landing_page_path"
    return "unknown", "unknown"

def enrich_daily(item, configured, period):
    keys = item.get("keys", ["", "", "", "", ""])
    row_date, query, page, country, device = (keys + [""] * 5)[:5]
    config = configured.get((normalize_query(query), device.casefold(), "google", "search_console"))
    language = "unknown"; language_source = "unknown"; query_id = category = expected_path = ""; configured_query = "false"
    if config:
        language = config.get("language", "unknown"); language_source = "configured_query"; query_id = config.get("query_id", "")
        category = config.get("category", ""); expected_path = config.get("expected_language_path", ""); configured_query = "true"
    else:
        language, language_source = language_from_page(page)
        if language_source == "unknown":
            language, language_source = detect_query_language(query)
        expected_path = language_paths().get(language, "")
    return Result(date=row_date, row_type="daily", source="google_search_console", engine="google", surface="search_console",
        language=language, language_source=language_source, query_id=query_id, category=category, configured_query=configured_query,
        query=query, expected_language_path=expected_path, country=country, country_format="iso_3166_1_alpha_3" if country else "",
        device=device, period=period, average_position=item.get("position", ""), url=page, clicks=item.get("clicks", ""),
        impressions=item.get("impressions", ""), ctr=item.get("ctr", ""), status="ok").to_row()

def aggregate_period(rows, period, previous_rows=None, current_limit_reached=False, previous_limit_reached=False, current_limit_days=None, previous_limit_days=None):
    def grouped(source_rows):
        groups = defaultdict(lambda: {"clicks":0.0,"impressions":0.0,"weighted":0.0,"sample":None})
        for r in source_rows:
            key = (r.get("query",""), r.get("url",""), r.get("country",""), r.get("device",""))
            clicks = float(r.get("clicks") or 0); impressions = float(r.get("impressions") or 0); pos = float(r.get("average_position") or 0)
            g = groups[key]; g["clicks"] += clicks; g["impressions"] += impressions; g["weighted"] += pos * impressions; g["sample"] = r
        return groups
    current = grouped(rows); previous = grouped(previous_rows or [])
    current_limit_days = current_limit_days or []
    previous_limit_days = previous_limit_days or []
    any_limit = bool(current_limit_reached or previous_limit_reached)
    out=[]
    for key, g in current.items():
        sample = g["sample"]; impressions = g["impressions"]; clicks = g["clicks"]
        avg = (g["weighted"] / impressions) if impressions else ""; ctr = (clicks / impressions) if impressions else ""
        pg = previous.get(key); prev_avg = change = ""
        if pg and pg["impressions"]:
            prev_avg = pg["weighted"] / pg["impressions"]
            if avg != "": change = avg - prev_avg
        row = dict(sample); row.update({"row_type":"period_summary", "date":"", "period":period, "clicks":str(round(clicks,4)),
            "impressions":str(round(impressions,4)), "ctr":str(round(ctr,6)) if ctr != "" else "",
            "average_position":str(round(avg,4)) if avg != "" else "", "previous_average_position":str(round(prev_avg,4)) if prev_avg != "" else "",
            "position_change": "" if any_limit else (str(round(change,4)) if change != "" else ""), "comparison_reliable": "false" if any_limit else ("true" if change != "" else ""), "data_limit_reached": "true" if any_limit else "", "current_period_data_limit_reached": "true" if current_limit_reached else "", "previous_period_data_limit_reached": "true" if previous_limit_reached else "", "current_period_limit_days": ",".join(current_limit_days), "previous_period_limit_days": ",".join(previous_limit_days)})
        out.append(row)
    return out

def authorize():
    secret = env("GOOGLE_CLIENT_SECRET_FILE"); token_file = env("GOOGLE_TOKEN_FILE")
    if not secret or not Path(secret).exists(): raise FileNotFoundError("client secret inexistente")
    try:
        from google.auth.transport.requests import Request
        from google.oauth2.credentials import Credentials
        from google_auth_oauthlib.flow import InstalledAppFlow
    except ImportError as exc:
        raise RuntimeError(f"dependencia OAuth no disponible: {exc}") from exc
    creds = None
    if token_file and Path(token_file).exists():
        try: creds = Credentials.from_authorized_user_file(token_file, [READONLY_SCOPE])
        except Exception as exc: raise ValueError(f"token inválido: {exc}") from exc
    if creds and creds.expired and creds.refresh_token: creds.refresh(Request())
    if not creds or not creds.valid:
        creds = InstalledAppFlow.from_client_secrets_file(secret, [READONLY_SCOPE]).run_local_server(port=0)
    if not token_file: raise ValueError("GOOGLE_TOKEN_FILE no configurado")
    Path(token_file).parent.mkdir(parents=True, exist_ok=True); Path(token_file).write_text(creds.to_json(), encoding="utf-8")
    return creds

def fetch_day(service, site_url, day):
    rows=[]; start_row=0; row_limit=25000; daily_exposure_limit=50000
    while True:
        body={"startDate":day,"endDate":day,"dimensions":QUERY_DIMENSIONS,"type":SEARCH_TYPE,"dataState":"final","rowLimit":row_limit,"startRow":start_row}
        batch=service.searchanalytics().query(siteUrl=site_url, body=body).execute().get("rows", [])
        if not batch:
            break
        rows.extend(batch)
        if len(batch) < row_limit:
            break
        start_row += row_limit
        if len(rows) >= daily_exposure_limit:
            break
    return rows, len(rows) >= daily_exposure_limit

def fetch_daily(service, site_url, start, end):
    rows=[]; limit_days=[]; counts={}
    for day in each_day(start, end):
        day_rows, limit_reached = fetch_day(service, site_url, day)
        counts[day] = len(day_rows)
        if limit_reached:
            limit_days.append(day)
        rows.extend(day_rows)
    return rows, limit_days, counts

def dry_run_rows(period, start, end):
    active = load_queries(include_inactive=False)
    missing = [name for name in ["GSC_PROPERTY", "GOOGLE_CLIENT_SECRET_FILE", "GOOGLE_TOKEN_FILE"] if not env(name)]
    return [Result(row_type="period_summary", source="google_search_console", engine="google", surface="search_console", period=period,
                   status="dry_run", error=f"dry_run: would discover latest date then query daily type=web dataState=final dimensions={QUERY_DIMENSIONS} from {start} to {end}; active_queries={len(active)}; missing_credentials={','.join(missing) or 'none'}").to_row()]

def run(dry_run=False, period="7d", start_date=None, end_date=None):
    if dry_run:
        start, end = period_range(period, start_date, end_date)
        return dry_run_rows(period, start, end)
    if not env("GSC_PROPERTY") or not env("GOOGLE_CLIENT_SECRET_FILE") or not env("GOOGLE_TOKEN_FILE"):
        return [Result(source="google_search_console", engine="google", surface="search_console", status="error", error="No disponible: missing Google Search Console credentials").to_row()]
    try:
        from googleapiclient.discovery import build
        from googleapiclient.errors import HttpError
        service = build("searchconsole", "v1", credentials=authorize())
        latest = end_date or discover_latest_date(service, env("GSC_PROPERTY"))
        if not latest:
            return [Result(source="google_search_console", engine="google", surface="search_console", status="no_data", error="No disponible: no final dates available").to_row()]
        start, end = period_range(period, start_date, end_date, latest)
        ps, pe = previous_period(start, end)
        configured = query_lookup(include_inactive=False)
        current_raw, limit_days, _counts = fetch_daily(service, env("GSC_PROPERTY"), start, end)
        previous_raw, previous_limit_days, _previous_counts = fetch_daily(service, env("GSC_PROPERTY"), ps, pe)
        daily = [enrich_daily(item, configured, period) for item in current_raw]
        prev_daily = [enrich_daily(item, configured, period) for item in previous_raw]
        summaries = aggregate_period(daily, period, prev_daily, current_limit_reached=bool(limit_days), previous_limit_reached=bool(previous_limit_days), current_limit_days=limit_days, previous_limit_days=previous_limit_days)
        warnings = []
        if limit_days:
            warnings.append(Result(row_type="period_summary", source="google_search_console", engine="google", surface="search_console", period=period, data_limit_reached="true", current_period_data_limit_reached="true", current_period_limit_days=",".join(limit_days), limit_period="current", comparison_reliable="false", status="warning", error="Current Search Console period reached the daily exposure limit; comparison may be incomplete").to_row())
        if previous_limit_days:
            warnings.append(Result(row_type="period_summary", source="google_search_console", engine="google", surface="search_console", period=period, data_limit_reached="true", previous_period_data_limit_reached="true", previous_period_limit_days=",".join(previous_limit_days), limit_period="previous", comparison_reliable="false", status="warning", error="Previous Search Console period reached the daily exposure limit; comparison may be incomplete").to_row())
        return daily + summaries + warnings or [Result(source="google_search_console", engine="google", surface="search_console", status="no_data", error="No disponible").to_row()]
    except HttpError as exc:
        text = str(exc); msg = "No disponible: cuota agotada" if "quota" in text.lower() else ("No disponible: propiedad sin permisos" if "403" in text else f"No disponible: error Google API: {exc}")
        return [Result(source="google_search_console", engine="google", surface="search_console", status="error", error=msg).to_row()]
    except (ConnectionError, TimeoutError, URLError) as exc:
        return [Result(source="google_search_console", engine="google", surface="search_console", status="error", error=f"No disponible: error de red: {exc}").to_row()]
    except Exception as exc:
        return [Result(source="google_search_console", engine="google", surface="search_console", status="error", error=f"No disponible: {exc}").to_row()]
