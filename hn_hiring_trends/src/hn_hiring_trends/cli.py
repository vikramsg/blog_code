"""Run historical collection through classification, tables, and charts."""

import argparse
import json
import sys
from collections import defaultdict
from datetime import UTC, date, datetime, timedelta
from pathlib import Path

from .analyze import (
    aggregate,
    annual_advertisement_totals,
    classify_records,
    comparable_years,
    monthly_advertisement_totals,
)
from .collect import JsonCache, SourceError, collect, months_between
from .output import write_outputs


def parse_month(value: str) -> date:
    try:
        month = date.fromisoformat(value + "-01")
    except ValueError as error:
        raise argparse.ArgumentTypeError("Use a calendar month in YYYY-MM format.") from error
    if month.isoformat()[:7] != value:
        raise argparse.ArgumentTypeError("Use a calendar month in YYYY-MM format.")
    return month


def latest_complete_month(today: date) -> date:
    previous = today.replace(day=1) - timedelta(days=1)
    return previous.replace(day=1)


def run_pipeline(cache: JsonCache, start: date, end: date, output_dir: Path, workers: int = 4) -> dict:
    records, coverage = collect(cache, start, end, workers)
    classified = classify_records(records)
    by_month = defaultdict(list)
    for row in classified:
        by_month[row["month"]].append(row)
    for row in coverage:
        month_records = by_month[row["month"]]
        month_ads = [record for record in month_records if record["included"]]
        row.update(
            {
                "included_advertisements": len(month_ads),
                "advertisements_with_selected_roles": sum(
                    bool(record["role_families"]) for record in month_ads
                ),
                "product_engineer_advertisements": sum(
                    "product" in record["role_families"] for record in month_ads
                ),
                "not_identified_as_hiring": sum(
                    record["exclusion_reason"] == "not_identified_as_hiring" for record in month_records
                ),
                "outside_thread_month": sum(
                    record["exclusion_reason"] == "outside_thread_month" for record in month_records
                ),
                "exact_text_duplicates": sum(
                    record["exclusion_reason"] == "same_month_exact_text_duplicate"
                    for record in month_records
                ),
            }
        )
    tables = {
        granularity: aggregate(classified, coverage, start, end, granularity)
        for granularity in ("monthly", "quarterly", "annual")
    }
    tables["comparable_years"], comparison_months = comparable_years(classified, coverage, end)
    tables["annual_totals"] = annual_advertisement_totals(tables["annual"])
    tables["monthly_totals"] = monthly_advertisement_totals(tables["monthly"])
    included = [row for row in classified if row["included"]]
    expected_months = months_between(start, end)
    found_months = {row["month"] for row in coverage}
    manifest = {
        "requested_start": start.isoformat()[:7],
        "requested_end": end.isoformat()[:7],
        "expected_months": len(expected_months),
        "threads": len(coverage),
        "missing_months": sorted(set(expected_months) - found_months),
        "hn_listed_comments": sum(row["hn_listed_comments"] for row in coverage),
        "indexed_listed_comments": sum(row["indexed_listed_comments"] for row in coverage),
        "unindexed_listed_comments": sum(row["unindexed_listed_comments"] for row in coverage),
        "advertisements": len(included),
        "advertisements_with_selected_roles": sum(bool(row["role_families"]) for row in included),
        "product_engineer_advertisements": sum("product" in row["role_families"] for row in included),
        "advertisements_identified_by_role": sum(
            row["identification_method"] == "advertised_role" for row in included
        ),
        "excluded_comments": len(classified) - len(included),
        "duplicate_comments": sum(
            row["exclusion_reason"] == "same_month_exact_text_duplicate" for row in classified
        ),
        "outside_thread_month_comments": sum(
            row["exclusion_reason"] == "outside_thread_month" for row in classified
        ),
        "comparison_months": comparison_months,
        "classification_method": "four advertised role categories with inspectable title/role-description heuristics",
        "share_denominator": "all retained hiring advertisements",
        "comment_source": "Algolia indexed top-level comments intersected with official HN comment IDs",
        "causal_inference": False,
    }
    return write_outputs(output_dir, classified, coverage, tables, manifest)


def main(argv: list[str] | None = None) -> int:
    today = datetime.now(UTC).date()
    parser = argparse.ArgumentParser(
        description="Analyze frontend, backend, full-stack, and product-engineer hiring advertisements."
    )
    parser.add_argument(
        "--start",
        type=parse_month,
        default=date(2011, 4, 1),
        help="First thread month, YYYY-MM (default: 2011-04).",
    )
    parser.add_argument(
        "--end",
        type=parse_month,
        default=latest_complete_month(today),
        help="Last thread month, YYYY-MM (default: latest complete month).",
    )
    parser.add_argument(
        "--cache", type=Path, default=Path("data/cache"), help="Source response cache directory."
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/results"),
        help="Tables, charts, classified records, and summary directory.",
    )
    parser.add_argument("--workers", type=int, default=4, help="Concurrent thread downloads (default: 4).")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--offline",
        action="store_true",
        help="Read only cached sources; fail if any required source is missing.",
    )
    mode.add_argument(
        "--refresh", action="store_true", help="Replace cached responses with fresh source snapshots."
    )
    args = parser.parse_args(argv)
    if args.start > args.end:
        parser.error("--start must not be after --end")
    if args.end >= today.replace(day=1):
        parser.error("--end must be a completed calendar month")
    if args.workers < 1:
        parser.error("--workers must be at least 1")
    try:
        with JsonCache(args.cache, offline=args.offline, refresh=args.refresh) as cache:
            manifest = run_pipeline(cache, args.start, args.end, args.output, args.workers)
    except (SourceError, OSError, ValueError) as error:
        print(f"Analysis failed: {error}", file=sys.stderr)
        return 1
    print(
        json.dumps(
            {
                "output": str(args.output),
                "threads": manifest["threads"],
                "advertisements": manifest["advertisements"],
                "missing_months": manifest["missing_months"],
            },
            indent=2,
        )
    )
    return 0
