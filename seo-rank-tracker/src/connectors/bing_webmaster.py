import re
from datetime import datetime, timezone
from ..config import env, active_unique_queries
from ..models import Result

BASE_URL = "https://ssl.bing.com/webmaster/api.svc/json"
GENERAL_METHODS = ["GetQueryStats", "GetPageStats", "GetRankAndTrafficStats"]
DETAILED_METHOD = "GetQueryPageStats"
STAT_FIELDS = {"Query", "Page", "Url", "Clicks", "Impressions", "Ctr", "CTR", "AvgImpressionPosition", "AveragePosition", "Position", "Date"}


def bing_date_to_iso(value):
    if not value: return ""
    m = re.search(r"/Date\((-?\d+)", str(value))
    if m:
        return datetime.fromtimestamp(int(m.group(1)) / 1000, tz=timezone.utc).date().isoformat()
    return str(value)[:10] if re.match(r"\d{4}-\d{2}-\d{2}", str(value)) else str(value)


def ctr(clicks, impressions, existing=""):
    if existing not in (None, ""): return existing
    try:
        c = float(clicks or 0); i = float(impressions or 0)
        return str(round(c / i, 6)) if i else ""
    except ValueError:
        return ""


def _get(method, **params):
    import requests
    merged = {"siteUrl": env("BING_SITE_URL"), "apikey": env("BING_WEBMASTER_API_KEY")}
    merged.update({k:v for k,v in params.items() if v not in (None, "")})
    response = requests.get(f"{BASE_URL}/{method}", params=merged, timeout=30)
    response.raise_for_status()
    return response.json()


def _items(payload):
    if not payload:
        return []
    data = payload.get("d", payload) if isinstance(payload, dict) else payload
    if data in (None, ""):
        return []
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        for key in ("results", "Results"):
            if key in data:
                value = data.get(key)
                return value if isinstance(value, list) else []
        return [data] if data and any(field in data for field in STAT_FIELDS) else []
    return []


def warning_row(endpoint, message, requested_query=""):
    return Result(source="bing_webmaster", engine="bing", surface="bing_webmaster", endpoint=endpoint, requested_query=requested_query, status="warning", error=message).to_row()


def error_row(message):
    return Result(source="bing_webmaster", engine="bing", surface="bing_webmaster", status="error", error=message).to_row()


def parse_query_stats(item):
    clicks = item.get("Clicks", ""); impressions = item.get("Impressions", "")
    return Result(date=bing_date_to_iso(item.get("Date", "")), source="bing_webmaster", engine="bing", surface="bing_webmaster", endpoint="GetQueryStats", query=item.get("Query", ""), clicks=clicks, impressions=impressions, ctr=ctr(clicks, impressions, item.get("Ctr", item.get("CTR", ""))), average_position=item.get("AvgImpressionPosition", item.get("AveragePosition", item.get("Position", ""))), status="ok").to_row()


def parse_page_stats(item):
    clicks = item.get("Clicks", ""); impressions = item.get("Impressions", "")
    return Result(date=bing_date_to_iso(item.get("Date", "")), source="bing_webmaster", engine="bing", surface="bing_webmaster", endpoint="GetPageStats", url=item.get("Page", item.get("Url", item.get("Query", ""))), clicks=clicks, impressions=impressions, ctr=ctr(clicks, impressions, item.get("Ctr", item.get("CTR", ""))), average_position=item.get("AvgImpressionPosition", item.get("AveragePosition", item.get("Position", ""))), status="ok").to_row()


def parse_rank_traffic(item):
    clicks = item.get("Clicks", ""); impressions = item.get("Impressions", "")
    return Result(date=bing_date_to_iso(item.get("Date", "")), source="bing_webmaster", engine="bing", surface="bing_webmaster", endpoint="GetRankAndTrafficStats", clicks=clicks, impressions=impressions, ctr=ctr(clicks, impressions, item.get("Ctr", item.get("CTR", ""))), average_position=item.get("AvgImpressionPosition", item.get("AveragePosition", item.get("Position", ""))), status="ok").to_row()


def parse_query_page_stats(item, requested_query):
    clicks = item.get("Clicks", ""); impressions = item.get("Impressions", "")
    return Result(date=bing_date_to_iso(item.get("Date", "")), source="bing_webmaster", engine="bing", surface="bing_webmaster", endpoint="GetQueryPageStats", query=requested_query, requested_query=requested_query, returned_query_value=item.get("Query", ""), url=item.get("Page", item.get("Url", "")), clicks=clicks, impressions=impressions, ctr=ctr(clicks, impressions, item.get("Ctr", item.get("CTR", ""))), average_position=item.get("AvgImpressionPosition", item.get("AveragePosition", item.get("Position", ""))), status="ok").to_row()


PARSERS = {"GetQueryStats": parse_query_stats, "GetPageStats": parse_page_stats, "GetRankAndTrafficStats": parse_rank_traffic}


def dry_run_rows(bing_detailed=False):
    missing = [name for name in ["BING_WEBMASTER_API_KEY", "BING_SITE_URL"] if not env(name)]
    endpoints = GENERAL_METHODS + ([DETAILED_METHOD] if bing_detailed else [])
    detail = len(active_unique_queries()) if bing_detailed else 0
    return [Result(source="bing_webmaster", engine="bing", surface="bing_webmaster", status="dry_run", error=f"dry_run: would try endpoints {','.join(endpoints)}; detailed_queries={detail}; missing_credentials={','.join(missing) or 'none'}").to_row()]


def _error_message(method, exc, requested_query=""):
    response = getattr(exc, "response", None)
    prefix = f"{method}({requested_query})" if requested_query else method
    if response is not None and hasattr(response, "status_code"):
        return f"{prefix} unavailable or unsupported: HTTP {response.status_code}"
    return f"{prefix} unavailable or unsupported: {exc}"


def run(dry_run=False, bing_detailed=False):
    if dry_run: return dry_run_rows(bing_detailed)
    if not env("BING_WEBMASTER_API_KEY") or not env("BING_SITE_URL"):
        return [error_row("No disponible: missing Bing Webmaster credentials")]
    rows=[]; warnings=[]; errors=[]
    for method in GENERAL_METHODS:
        try:
            items = _items(_get(method))
            rows.extend(PARSERS[method](item) for item in items)
        except Exception as exc:
            message = _error_message(method, exc)
            errors.append(message); warnings.append(warning_row(method, message))
    if bing_detailed:
        for query in active_unique_queries():
            try:
                items = _items(_get(DETAILED_METHOD, query=query))
                rows.extend(parse_query_page_stats(item, query) for item in items)
            except Exception as exc:
                message = _error_message(DETAILED_METHOD, exc, requested_query=query)
                errors.append(message); warnings.append(warning_row(DETAILED_METHOD, message, requested_query=query))
    if rows:
        return rows + warnings
    if errors:
        return [error_row("No disponible: " + "; ".join(errors))]
    return [Result(source="bing_webmaster", engine="bing", surface="bing_webmaster", status="no_data", error="No disponible: Bing Webmaster returned no statistics").to_row()]
