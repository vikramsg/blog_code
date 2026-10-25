import json
from datetime import date

import httpx
import pytest

from hn_hiring_trends.collect import (
    ALGOLIA,
    JsonCache,
    SourceError,
    discover_threads,
    extract_thread,
    month_from_title,
    plain_text,
)


@pytest.mark.parametrize(
    "title",
    [
        "Ask HN: Who wants to be hired? (April 2011)",
        "Ask HN: Freelancer? Seeking freelancers? (April 2011)",
        "Ask HN: Should we agree that this account will submit all Who is Hiring posts?",
    ],
)
def test_only_monthly_employer_hiring_titles_are_selected(title):
    assert month_from_title(title) is None


def test_historical_title_capitalization_is_accepted():
    assert month_from_title("Ask HN: Who is Hiring? (April 2011)") == date(2011, 4, 1)


def test_plain_text_retains_job_header_and_paragraph_boundaries():
    assert (
        plain_text("Acme | Backend Engineer<p>R&amp;D<br>Apply <a href='https://example.com'>here</a>")
        == "Acme | Backend Engineer\nR&D\nApply here"
    )


def test_only_direct_indexed_comments_still_listed_by_hn_are_collected():
    thread = {"thread_id": 10, "month": "2022-01", "title": "Ask HN: Who is hiring? (January 2022)"}
    reply = {
        "id": 31,
        "parent_id": 20,
        "type": "comment",
        "text": "Interested!",
        "created_at": "2022-01-02T00:00:00Z",
    }
    direct = {
        "id": 20,
        "parent_id": 10,
        "type": "comment",
        "text": "Acme | Backend Engineer",
        "created_at": "2022-01-01T00:00:00Z",
        "children": [reply],
    }
    removed = {**direct, "id": 21}
    indexed = {"id": 10, "type": "story", "children": [direct, removed, reply]}
    official = {"id": 10, "by": "whoishiring", "title": thread["title"], "kids": [20, 22]}
    records, coverage = extract_thread(thread, indexed, official)
    assert [row["comment_id"] for row in records] == [20]
    assert records[0]["source_url"] == "https://news.ycombinator.com/item?id=20"
    assert coverage["unindexed_listed_comments"] == 1
    assert coverage["indexed_not_listed_comments"] == 1


def test_missing_official_metadata_fails_instead_of_dropping_a_month():
    with pytest.raises(SourceError, match="missing or mismatched"):
        extract_thread({"thread_id": 10}, {}, None)


def test_source_cache_supports_offline_reproduction_and_keeps_provenance(tmp_path):
    url = f"{ALGOLIA}/items/10"
    with JsonCache(tmp_path) as cache:
        cache.client.close()
        cache.client = httpx.Client(
            transport=httpx.MockTransport(lambda request: httpx.Response(200, json={"id": 10}))
        )
        assert cache.get(url) == {"id": 10}
    snapshot = json.loads(next(tmp_path.glob("*.json")).read_text())
    assert snapshot["url"] == url
    assert snapshot["fetched_at"]
    with JsonCache(tmp_path, offline=True) as cache:
        assert cache.get(url) == {"id": 10}
        with pytest.raises(SourceError, match="Missing cached source"):
            cache.get(f"{ALGOLIA}/items/11")


def test_failed_source_response_does_not_create_a_successful_cache_entry(tmp_path):
    with JsonCache(tmp_path) as cache:
        cache.client.close()
        cache.client = httpx.Client(transport=httpx.MockTransport(lambda request: httpx.Response(404)))
        with pytest.raises(SourceError, match="Source request failed"):
            cache.get(f"{ALGOLIA}/items/10")
    with JsonCache(tmp_path, offline=True) as cache:
        with pytest.raises(SourceError, match="Missing cached source"):
            cache.get(f"{ALGOLIA}/items/10")


def test_refresh_replaces_the_cached_source_snapshot(tmp_path):
    url = f"{ALGOLIA}/items/10"
    for version in (1, 2):
        with JsonCache(tmp_path, refresh=version == 2) as cache:
            cache.client.close()
            cache.client = httpx.Client(
                transport=httpx.MockTransport(
                    lambda request, version=version: httpx.Response(200, json={"version": version})
                )
            )
            assert cache.get(url) == {"version": version}
    with JsonCache(tmp_path, offline=True) as cache:
        assert cache.get(url) == {"version": 2}


def test_discovery_paginates_and_excludes_unrelated_threads():
    pages = [
        {
            "nbHits": 2,
            "nbPages": 2,
            "hits": [{"objectID": "10", "title": "Ask HN: Who wants to be hired? (January 2022)"}],
        },
        {
            "nbHits": 2,
            "nbPages": 2,
            "hits": [{"objectID": "11", "title": "Ask HN: Who is hiring? (January 2022)"}],
        },
    ]

    class Source:
        def get(self, url):
            return pages.pop(0)

    threads = discover_threads(Source(), date(2022, 1, 1), date(2022, 1, 1))
    assert [row["thread_id"] for row in threads] == [11]


def test_discovery_refuses_truncated_search():
    class Source:
        def get(self, url):
            return {"nbHits": 1001, "nbPages": 10, "hits": []}

    with pytest.raises(SourceError, match="1,000-result limit"):
        discover_threads(Source(), date(2011, 4, 1), date(2026, 9, 1))


def test_december_2011_uses_the_canonical_advertisement_thread_not_its_redirect():
    title = "Ask HN: Who is Hiring? (December 2011)"

    class Source:
        def get(self, url):
            if url.endswith("/items/3300290"):
                return {"id": 3300290, "type": "story", "title": title}
            return {"nbHits": 1, "nbPages": 1, "hits": [{"objectID": "3300371", "title": title}]}

    threads = discover_threads(Source(), date(2011, 12, 1), date(2011, 12, 1))
    assert [thread["thread_id"] for thread in threads] == [3300290]
    assert threads[0]["author"] == "lpolovets"


def test_curated_historical_month_is_found_even_without_an_official_account_post():
    title = "Ask HN: Who is Hiring? (July 2011)"

    class Source:
        def get(self, url):
            if url.endswith("/items/2719028"):
                return {"id": 2719028, "type": "story", "title": title}
            return {"nbHits": 0, "nbPages": 0, "hits": []}

    threads = discover_threads(Source(), date(2011, 7, 1), date(2011, 7, 1))
    assert [thread["thread_id"] for thread in threads] == [2719028]
