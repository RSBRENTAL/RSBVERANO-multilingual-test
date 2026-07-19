from ..config import env
from ..models import Result

BASE_URL = "https://ssl.bing.com/webmaster/api.svc/json"
METHODS = ["GetQueryStats", "GetPageStats", "GetRankAndTrafficStats", "GetQueryPageStats"]

def _get(method):
    import requests
    response = requests.get(f"{BASE_URL}/{method}", params={"siteUrl": env("BING_SITE_URL"), "apikey": env("BING_WEBMASTER_API_KEY")}, timeout=30)
    response.raise_for_status()
    return response.json()

def _items(payload):
    data = payload.get("d", payload)
    if isinstance(data, dict):
        return data.get("results", data.get("Results", [])) or [data]
    if isinstance(data, list):
        return data
    return []

def _result_from_item(method, item):
    avg = item.get("AvgImpressionPosition", item.get("AveragePosition", item.get("Position", "")))
    return Result(date=str(item.get("Date", "")), source="bing_webmaster", engine="bing", surface="bing_webmaster", query=item.get("Query", ""), url=item.get("Page", item.get("Url", "")), clicks=item.get("Clicks", ""), impressions=item.get("Impressions", ""), ctr=item.get("Ctr", item.get("CTR", "")), average_position=avg, status="ok", error=f"method={method}; country/device not available from this endpoint").to_row()

def dry_run_rows():
    missing = [name for name in ["BING_WEBMASTER_API_KEY", "BING_SITE_URL"] if not env(name)]
    return [Result(source="bing_webmaster", engine="bing", surface="bing_webmaster", status="dry_run", error=f"dry_run: would try endpoints {','.join(METHODS)}; missing_credentials={','.join(missing) or 'none'}").to_row()]

def run(dry_run=False):
    if dry_run:
        return dry_run_rows()
    if not env("BING_WEBMASTER_API_KEY") or not env("BING_SITE_URL"):
        return [Result(source="bing_webmaster", engine="bing", surface="bing_webmaster", status="error", error="No disponible: missing Bing Webmaster credentials").to_row()]
    rows=[]; errors=[]
    for method in METHODS:
        try:
            payload = _get(method)
            rows.extend(_result_from_item(method, item) for item in _items(payload))
        except Exception as exc:
            response = getattr(exc, "response", None)
            if response is not None and hasattr(response, "status_code"):
                errors.append(f"{method}: HTTP {response.status_code}")
            elif exc.__class__.__name__ in {"RequestException", "ConnectionError", "Timeout"}:
                errors.append(f"{method}: network error {exc}")
            else:
                errors.append(f"{method}: unavailable or unsupported: {exc}")
    if rows:
        return rows
    return [Result(source="bing_webmaster", engine="bing", surface="bing_webmaster", status="error", error="No disponible: " + "; ".join(errors)).to_row()]
