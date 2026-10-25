import csv
import json
from urllib.parse import parse_qs

import httpx
import pytest

from hn_hiring_trends.cli import main
from hn_hiring_trends.collect import JsonCache


def test_cli_collects_classifies_exports_and_reproduces_cached_results(tmp_path, monkeypatch):
    months = ["2022-07", "2022-08", "2022-09", "2023-07", "2023-08", "2023-09"]
    month_names = ["July", "August", "September"] * 2
    hits, sources = [], {}
    for thread_id, (month, name) in enumerate(zip(months, month_names, strict=True), start=10):
        title = f"Ask HN: Who is hiring? ({name} {month[:4]})"
        hits.append({"objectID": str(thread_id), "title": title})
        comments = [
            {
                "id": thread_id * 100,
                "parent_id": thread_id,
                "type": "comment",
                "created_at": month + "-02T00:00:00Z",
                "text": "Acme | Backend Engineer | Full-time | Remote<p>We are hiring a backend engineer. Apply at jobs@example.com.",
            },
            {
                "id": thread_id * 100 + 1,
                "parent_id": thread_id,
                "type": "comment",
                "created_at": month + "-03T00:00:00Z",
                "text": "Beta | Full Stack Engineer | Remote<p>We are hiring. You will talk to customers and make product decisions. Apply at jobs@example.com.",
            },
            {
                "id": thread_id * 100 + 2,
                "parent_id": thread_id,
                "type": "comment",
                "created_at": month + "-03T00:00:00Z",
                "text": "Why do companies insist on office work?",
            },
            {
                "id": thread_id * 100 + 3,
                "parent_id": thread_id,
                "type": "comment",
                "created_at": month + "-03T00:00:00Z",
                "text": "I'm looking for a job as a backend engineer. Available for remote work.",
            },
        ]
        sources[f"/api/v1/items/{thread_id}"] = {"id": thread_id, "type": "story", "children": comments}
        sources[f"/v0/item/{thread_id}.json"] = {
            "id": thread_id,
            "by": "whoishiring",
            "title": title,
            "kids": [comment["id"] for comment in comments] + [thread_id * 100 + 4],
        }
    requests = []

    def respond(request):
        requests.append(str(request.url))
        if request.url.path.endswith("search_by_date"):
            assert parse_qs(request.url.query.decode())["page"] == ["0"]
            return httpx.Response(200, json={"hits": hits, "nbHits": len(hits), "nbPages": 1})
        return httpx.Response(200, json=sources[request.url.path])

    original_init = JsonCache.__init__

    def init_with_source(self, *args, **kwargs):
        original_init(self, *args, **kwargs)
        self.client.close()
        self.client = httpx.Client(transport=httpx.MockTransport(respond))

    monkeypatch.setattr(JsonCache, "__init__", init_with_source)
    output, cache = tmp_path / "results", tmp_path / "cache"
    args = ["--start", "2022-07", "--end", "2023-09", "--output", str(output), "--cache", str(cache)]
    assert main(args) == 0
    manifest = json.loads((output / "manifest.json").read_text())
    assert manifest["advertisements"] == 12
    assert manifest["engineering_advertisements"] == 12
    assert manifest["excluded_comments"] == 12
    assert manifest["unindexed_listed_comments"] == 6
    assert len(manifest["missing_months"]) == 9
    rows = list(csv.DictReader((output / "quarterly.csv").open()))
    backend = next(row for row in rows if row["period"] == "2022-Q3" and row["metric"] == "role:backend")
    assert (int(backend["count"]), int(backend["denominator"])) == (3, 6)
    assert float(backend["share"]) == pytest.approx(0.5)
    assert "not a labor-market census" in (output / "summary.md").read_text()
    assert all((output / chart).stat().st_size > 0 for chart in manifest["charts"])
    first_hash = manifest["classified_sha256"]
    request_count = len(requests)
    assert main([*args, "--offline"]) == 0
    assert len(requests) == request_count
    assert json.loads((output / "manifest.json").read_text())["classified_sha256"] == first_hash


def test_cli_rejects_current_or_future_month_without_network():
    with pytest.raises(SystemExit) as error:
        main(["--end", "9999-01"])
    assert error.value.code == 2


def test_cli_offline_failure_explains_missing_sources(tmp_path, capsys):
    assert main(["--start", "2022-01", "--end", "2022-01", "--cache", str(tmp_path), "--offline"]) == 1
    assert "Missing cached source" in capsys.readouterr().err
