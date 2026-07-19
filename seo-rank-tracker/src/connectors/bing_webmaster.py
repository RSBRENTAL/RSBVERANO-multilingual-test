from ..config import env
from ..models import Result

def run(dry_run=False):
    if dry_run:
        return [Result(source="bing_webmaster", engine="bing", surface="bing_webmaster", status="ok", error="dry-run: no external connection").to_row()]
    if not env("BING_WEBMASTER_API_KEY") or not env("BING_SITE_URL"):
        return [Result(source="bing_webmaster", engine="bing", surface="bing_webmaster", status="error", error="No disponible: missing Bing Webmaster credentials").to_row()]
    try:
        import requests
        # Placeholder for read-only Bing Webmaster endpoint integration. Kept separate from exact SERP checks.
        return [Result(source="bing_webmaster", engine="bing", surface="bing_webmaster", status="no_data", error="No disponible: configure endpoint/method available for the verified site").to_row()]
    except Exception as exc:
        return [Result(source="bing_webmaster", engine="bing", surface="bing_webmaster", status="error", error=f"No disponible: {exc}").to_row()]
