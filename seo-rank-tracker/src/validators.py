from .models import QUERY_COLUMNS, RESULT_COLUMNS

OFFICIAL_LANGUAGES = {"en", "es", "fr", "it", "de", "nl", "pt", "ca", "sv", "pl"}
VALID_LANGUAGE_SOURCES = {"configured_query", "landing_page_path", "query_detection", "unknown", ""}

def validate_languages(paths):
    assert set(paths) == OFFICIAL_LANGUAGES
    assert paths["ca"] == "/cat/"
    return True

def validate_query_schema(rows):
    for row in rows:
        missing = [column for column in QUERY_COLUMNS if column not in row]
        if missing:
            raise ValueError(f"Missing query columns: {missing}")
    return True

def validate_result_schema(rows):
    for row in rows:
        missing = [column for column in RESULT_COLUMNS if column not in row]
        if missing:
            raise ValueError(f"Missing result columns: {missing}")
        if row.get("exact_organic_position") and row.get("average_position"):
            raise ValueError("Average position cannot be exact organic position")
        if row.get("surface") in {"google_generative_ai", "ai_answer"} and row.get("exact_organic_position"):
            raise ValueError("AI data cannot be organic position")
        if row.get("language_source") not in VALID_LANGUAGE_SOURCES:
            raise ValueError("Invalid language_source")
        if row.get("status") == "ok" and str(row.get("error", "")).startswith("dry-run"):
            raise ValueError("Dry-run rows cannot be status=ok")
    return True
