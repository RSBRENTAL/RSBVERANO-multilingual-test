from dataclasses import dataclass, asdict
from datetime import datetime, timezone

RESULT_COLUMNS = [
    "timestamp", "date", "row_type", "source", "engine", "surface", "endpoint", "scenario", "language", "language_source",
    "query_id", "category", "configured_query", "query", "requested_query", "returned_query_value", "expected_language_path", "country", "country_format", "city", "device",
    "period", "average_position", "previous_average_position", "position_change", "exact_organic_position",
    "url", "title", "clicks", "impressions", "ctr", "ai_feature_present", "brand_mentioned",
    "domain_cited", "citation_url", "data_limit_reached", "current_period_data_limit_reached", "previous_period_data_limit_reached", "current_period_limit_days", "previous_period_limit_days", "limit_period", "comparison_reliable", "status", "error",
]
QUERY_COLUMNS = ["query_id","category","language","scenario","search_country","search_city","latitude","longitude","device","engine","surface","query","expected_language_path","active"]
ROW_TYPES = {"", "daily", "period_summary"}

@dataclass
class Result:
    timestamp: str = ""
    date: str = ""
    row_type: str = ""
    source: str = ""
    engine: str = ""
    surface: str = ""
    endpoint: str = ""
    scenario: str = ""
    language: str = ""
    language_source: str = ""
    query_id: str = ""
    category: str = ""
    configured_query: str = ""
    query: str = ""
    requested_query: str = ""
    returned_query_value: str = ""
    expected_language_path: str = ""
    country: str = ""
    country_format: str = ""
    city: str = ""
    device: str = ""
    period: str = ""
    average_position: str = ""
    previous_average_position: str = ""
    position_change: str = ""
    exact_organic_position: str = ""
    url: str = ""
    title: str = ""
    clicks: str = ""
    impressions: str = ""
    ctr: str = ""
    ai_feature_present: str = ""
    brand_mentioned: str = ""
    domain_cited: str = ""
    citation_url: str = ""
    data_limit_reached: str = ""
    current_period_data_limit_reached: str = ""
    previous_period_data_limit_reached: str = ""
    current_period_limit_days: str = ""
    previous_period_limit_days: str = ""
    limit_period: str = ""
    comparison_reliable: str = ""
    status: str = "ok"
    error: str = ""

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now(timezone.utc).isoformat()
        if self.row_type not in ROW_TYPES:
            raise ValueError("invalid row_type")
        if self.average_position and self.exact_organic_position:
            raise ValueError("average_position must not be copied into exact_organic_position")
        if self.surface in {"google_generative_ai", "ai_answer"} and self.exact_organic_position:
            raise ValueError("AI mentions or imports must never be stored as organic positions")
        if self.limit_period not in {"", "current", "previous"}:
            raise ValueError("invalid limit_period")
        if self.comparison_reliable not in {"", "true", "false"}:
            raise ValueError("invalid comparison_reliable")
        if self.status == "ok" and self.error.startswith("dry-run"):
            raise ValueError("dry-run rows must use status=dry_run")

    def to_row(self):
        row = asdict(self)
        return {column: str(row.get(column, "") or "") for column in RESULT_COLUMNS}
