"""Collect indexed hiring threads and compare their coverage with HN's comment lists."""

import hashlib
import json
import re
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, date, datetime
from html.parser import HTMLParser
from pathlib import Path
from typing import Any
from urllib.parse import urlencode

import httpx

ALGOLIA = "https://hn.algolia.com/api/v1"
HN_API = "https://hacker-news.firebaseio.com/v0"
MONTHS = {
    name: index
    for index, name in enumerate(
        (
            "january",
            "february",
            "march",
            "april",
            "may",
            "june",
            "july",
            "august",
            "september",
            "october",
            "november",
            "december",
        ),
        start=1,
    )
}
THREAD_TITLE = re.compile(r"^Ask HN:\s*Who is hiring\?\s*\(([A-Za-z]+)\s+(\d{4})\)$", re.I)
# These canonical monthly threads have different authors. The December official
# post (3300371) explicitly directs readers to 3300290 rather than hosting ads.
HISTORICAL_CANONICAL_THREADS = {
    "2011-07": (2719028, "Aloisius"),
    "2011-12": (3300290, "lpolovets"),
    "2015-04": (9303396, "_whoishiring"),
    "2015-05": (9471287, "_whoishiring"),
}


class SourceError(RuntimeError):
    """A source request failed or cannot provide the requested coverage."""


class JsonCache:
    def __init__(self, directory: Path, *, offline: bool = False, refresh: bool = False):
        if offline and refresh:
            raise ValueError("--offline and --refresh cannot be combined")
        self.directory = directory
        self.offline = offline
        self.refresh = refresh
        self.client = httpx.Client(
            timeout=60, headers={"User-Agent": "hn-hiring-trends/0.1 (historical research)"}
        )

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.client.close()

    def get(self, url: str) -> Any:
        filename = self.directory / f"{hashlib.sha256(url.encode()).hexdigest()}.json"
        if filename.exists() and not self.refresh:
            return json.loads(filename.read_text())["data"]
        if self.offline:
            raise SourceError(f"Missing cached source: {url}. Run without --offline first.")
        for attempt in range(3):
            try:
                response = self.client.get(url)
                response.raise_for_status()
                data = response.json()
                break
            except (httpx.TransportError, httpx.HTTPStatusError, ValueError) as error:
                if (
                    isinstance(error, httpx.HTTPStatusError)
                    and error.response.status_code < 500
                    and error.response.status_code != 429
                ):
                    raise SourceError(f"Source request failed: {url}: {error}") from error
                if attempt == 2:
                    raise SourceError(
                        f"Source request failed after three attempts: {url}: {error}"
                    ) from error
                time.sleep(2**attempt)
        self.directory.mkdir(parents=True, exist_ok=True)
        snapshot = {"url": url, "fetched_at": datetime.now(UTC).isoformat(), "data": data}
        temporary = filename.with_suffix(".pending")
        temporary.write_text(json.dumps(snapshot, ensure_ascii=False))
        temporary.replace(filename)
        return data


def month_from_title(title: str) -> date | None:
    match = THREAD_TITLE.fullmatch(title.strip())
    if not match or match[1].lower() not in MONTHS:
        return None
    return date(int(match[2]), MONTHS[match[1].lower()], 1)


def discover_threads(cache: JsonCache, start: date, end: date) -> list[dict]:
    threads = []
    page = 0
    seen_hits = 0
    while True:
        query = urlencode({"tags": "story,author_whoishiring", "hitsPerPage": 100, "page": page})
        result = cache.get(f"{ALGOLIA}/search_by_date?{query}")
        if result["nbHits"] > 1000:
            raise SourceError(
                "The discovery search exceeds Algolia's 1,000-result limit; narrow the discovery query before proceeding."
            )
        seen_hits += len(result["hits"])
        for hit in result["hits"]:
            month = month_from_title(hit.get("title") or "")
            if month and start <= month <= end:
                threads.append(
                    {
                        "thread_id": int(hit["objectID"]),
                        "month": month.isoformat()[:7],
                        "title": hit["title"],
                        "author": "whoishiring",
                        "selection_source": "official_account",
                    }
                )
        page += 1
        if page >= result["nbPages"]:
            if seen_hits != result["nbHits"]:
                raise SourceError(
                    "Incomplete discovery response; refusing to analyze a silently truncated series."
                )
            break
    for month, (thread_id, author) in HISTORICAL_CANONICAL_THREADS.items():
        if start <= date.fromisoformat(month + "-01") <= end:
            indexed = cache.get(f"{ALGOLIA}/items/{thread_id}")
            if indexed.get("type") != "story" or month_from_title(
                indexed.get("title") or ""
            ) != date.fromisoformat(month + "-01"):
                raise SourceError(f"Historical canonical thread does not match its month: {thread_id}")
            threads = [thread for thread in threads if thread["month"] != month]
            threads.append(
                {
                    "thread_id": thread_id,
                    "month": month,
                    "title": indexed["title"],
                    "author": author,
                    "selection_source": "historical_canonical",
                }
            )
    months = [thread["month"] for thread in threads]
    if len(set(months)) != len(months):
        raise SourceError(
            "Multiple official hiring threads in one month; resolve the source ambiguity before analysis."
        )
    return sorted(threads, key=lambda thread: thread["month"])


class PlainText(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []

    def handle_starttag(self, tag, attrs):
        if tag in {"p", "br", "li", "div"}:
            self.parts.append("\n")

    def handle_endtag(self, tag):
        if tag in {"p", "li", "div"}:
            self.parts.append("\n")

    def handle_data(self, data):
        self.parts.append(data)


def plain_text(html: str) -> str:
    parser = PlainText()
    parser.feed(html)
    return "\n".join(line.strip() for line in "".join(parser.parts).splitlines() if line.strip())


def extract_thread(thread: dict, indexed: dict, official: dict) -> tuple[list[dict], dict]:
    thread_id = thread["thread_id"]
    if (
        not official
        or official.get("id") != thread_id
        or official.get("by") != thread.get("author", "whoishiring")
    ):
        raise SourceError(f"Official HN thread metadata is missing or mismatched: {thread_id}")
    if indexed.get("id") != thread_id or indexed.get("type") != "story":
        raise SourceError(f"Indexed thread metadata is mismatched: {thread_id}")
    if month_from_title(official.get("title", "")) != date.fromisoformat(thread["month"] + "-01"):
        raise SourceError(f"Official thread title does not match its discovery month: {thread_id}")
    listed_ids = set(official.get("kids", []))
    comments = [
        child
        for child in indexed.get("children", [])
        if child.get("parent_id") == thread_id and child.get("type") == "comment"
    ]
    indexed_ids = {child["id"] for child in comments}
    if len(indexed_ids) != len(comments):
        raise SourceError(f"Duplicate indexed comment IDs in thread {thread_id}")
    records = []
    for child in comments:
        # HN's current listing governs membership; the index can retain removed comments.
        if child["id"] not in listed_ids:
            continue
        text = plain_text(child.get("text") or "")
        records.append(
            {
                "comment_id": child["id"],
                "thread_id": thread_id,
                "month": thread["month"],
                "comment_created_at": child["created_at"],
                "text": text,
                "source_url": f"https://news.ycombinator.com/item?id={child['id']}",
            }
        )
    coverage = {
        **thread,
        "thread_url": f"https://news.ycombinator.com/item?id={thread_id}",
        "indexed_source_url": f"{ALGOLIA}/items/{thread_id}",
        "official_source_url": f"{HN_API}/item/{thread_id}.json",
        "hn_listed_comments": len(listed_ids),
        "indexed_listed_comments": len(indexed_ids & listed_ids),
        "unindexed_listed_comments": len(listed_ids - indexed_ids),
        "indexed_not_listed_comments": len(indexed_ids - listed_ids),
        "empty_indexed_comments": sum(not record["text"] for record in records),
    }
    return records, coverage


def collect(cache: JsonCache, start: date, end: date, workers: int = 4) -> tuple[list[dict], list[dict]]:
    threads = discover_threads(cache, start, end)
    if not threads:
        raise SourceError("No official monthly hiring threads found in the requested window.")

    def fetch_thread(thread):
        thread_id = thread["thread_id"]
        indexed = cache.get(f"{ALGOLIA}/items/{thread_id}")
        official = cache.get(f"{HN_API}/item/{thread_id}.json")
        return extract_thread(thread, indexed, official)

    records, coverage = [], []
    with ThreadPoolExecutor(max_workers=workers) as pool:
        for thread_records, thread_coverage in pool.map(fetch_thread, threads):
            records.extend(thread_records)
            coverage.append(thread_coverage)
    return records, coverage


def months_between(start: date, end: date) -> list[str]:
    months = []
    month = start
    while month <= end:
        months.append(month.isoformat()[:7])
        month = date(month.year + (month.month == 12), month.month % 12 + 1, 1)
    return months
