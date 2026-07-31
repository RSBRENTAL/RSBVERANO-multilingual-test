from collections import Counter

from src.config import language_paths, load_queries, normalize_query, query_lookup


def test_priority_services_have_broad_multilingual_coverage():
    active = load_queries(include_inactive=False)
    counts = Counter((row["language"], row["category"]) for row in active)

    for language in language_paths():
        scooter_rows = counts[(language, "scooter")] + counts[(language, "motorbike")]
        rollerblades_rows = counts[(language, "rollerblades")]
        assert scooter_rows >= 20
        assert rollerblades_rows >= 20


def test_priority_queries_keep_language_paths_and_devices():
    active = load_queries(include_inactive=False)
    paths = language_paths()

    for row in active:
        assert row["expected_language_path"] == paths[row["language"]]

    grouped = Counter((row["language"], normalize_query(row["query"])) for row in active)
    for language in paths:
        language_queries = {
            normalize_query(row["query"])
            for row in active
            if row["language"] == language
        }
        assert any("50cc" in query for query in language_queries)
        assert any("125cc" in query for query in language_queries)

    for count in grouped.values():
        assert count == 2  # one mobile row and one desktop row


def test_priority_query_keys_are_unique():
    lookup = query_lookup(include_inactive=False)
    active = load_queries(include_inactive=False)
    assert len(lookup) == len(active)
