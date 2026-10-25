"""Advertisement-level counts and explicit calendar coverage for longitudinal comparisons."""

import re
from collections import defaultdict
from datetime import date

from .advertisements import is_hiring_ad, is_job_seeker
from .classify import ROLE_FAMILIES, classify
from .collect import months_between


def classify_records(records: list[dict]) -> list[dict]:
    seen_text: set[tuple[str, str]] = set()
    results = []
    for record in sorted(records, key=lambda row: (row["month"], row["comment_id"])):
        text_key = (record["month"], re.sub(r"\s+", " ", record["text"]).strip().casefold())
        classification = classify(record["text"])
        conventional_ad = is_hiring_ad(record["text"])
        reason = ""
        if not record["text"]:
            reason = "empty"
        elif record["comment_created_at"][:7] != record["month"]:
            reason = "outside_thread_month"
        elif is_job_seeker(record["text"]) or not (conventional_ad or classification["role_families"]):
            reason = "not_identified_as_hiring"
        elif text_key in seen_text:
            reason = "same_month_exact_text_duplicate"
        else:
            seen_text.add(text_key)
        result = {
            **record,
            **classification,
            "included": not reason,
            "exclusion_reason": reason,
            "identification_method": "hiring_text"
            if conventional_ad
            else "advertised_role"
            if classification["role_families"]
            else "",
        }
        results.append(result)
    return results


def metric_definitions() -> list[str]:
    return [f"role:{family}" for family in ROLE_FAMILIES]


def has_metric(record: dict, metric: str) -> bool:
    return metric.removeprefix("role:") in record["role_families"]


def period_key(month: str, granularity: str) -> str:
    if granularity == "monthly":
        return month
    if granularity == "quarterly":
        return f"{month[:4]}-Q{(int(month[5:]) - 1) // 3 + 1}"
    if granularity == "annual":
        return month[:4]
    raise ValueError(f"Unknown granularity: {granularity}")


def calendar_months(period: str, granularity: str) -> list[str]:
    year = int(period[:4])
    if granularity == "monthly":
        return [period]
    if granularity == "annual":
        return [f"{year}-{month:02}" for month in range(1, 13)]
    quarter = int(period[-1])
    return [f"{year}-{month:02}" for month in range((quarter - 1) * 3 + 1, quarter * 3 + 1)]


def aggregate(
    records: list[dict], coverage: list[dict], start: date, end: date, granularity: str
) -> list[dict]:
    expected = months_between(start, end)
    available = {row["month"] for row in coverage}
    by_period: dict[str, list[dict]] = defaultdict(list)
    for record in records:
        if record["included"]:
            by_period[period_key(record["month"], granularity)].append(record)
    rows = []
    for period in sorted({period_key(month, granularity) for month in expected}):
        calendar = calendar_months(period, granularity)
        observed = [month for month in calendar if month in available and month in expected]
        ads = by_period[period]
        for metric in metric_definitions():
            count = sum(has_metric(record, metric) for record in ads)
            rows.append(
                {
                    "period": period,
                    "granularity": granularity,
                    "months_observed": len(observed),
                    "calendar_months": len(calendar),
                    "complete_period": observed == calendar,
                    "observed_months": ";".join(observed),
                    "advertisements": len(ads),
                    "metric": metric,
                    "count": count,
                    "denominator_name": "advertisements",
                    "denominator": len(ads),
                    "share": count / len(ads) if ads else None,
                }
            )
    return rows


def annual_advertisement_totals(annual_rows: list[dict]) -> list[dict]:
    years = {row["period"]: row for row in annual_rows}
    return [
        {
            "year": year,
            "total_hiring_advertisements": row["advertisements"],
            "months_observed": row["months_observed"],
            "observed_months": row["observed_months"],
            "complete_year": row["complete_period"],
        }
        for year, row in sorted(years.items())
    ]


def comparable_years(records: list[dict], coverage: list[dict], end: date) -> tuple[list[dict], list[int]]:
    """Use identical available calendar months in every compared year, not full-year/YTD mixes."""
    by_year: dict[str, set[int]] = defaultdict(set)
    for row in coverage:
        by_year[row["month"][:4]].add(int(row["month"][5:]))
    latest = str(end.year)
    latest_months = sorted(by_year.get(latest, set()))
    if not latest_months:
        return [], []
    eligible_years = [year for year, months in sorted(by_year.items()) if set(latest_months) <= months]
    selected_records = [
        row
        for row in records
        if row["month"][:4] in eligible_years and int(row["month"][5:]) in latest_months
    ]
    selected_coverage = [
        row
        for row in coverage
        if row["month"][:4] in eligible_years and int(row["month"][5:]) in latest_months
    ]
    rows = aggregate(selected_records, selected_coverage, date(int(eligible_years[0]), 1, 1), end, "annual")
    rows = [row for row in rows if row["period"] in eligible_years]
    for row in rows:
        row["comparison_months"] = ";".join(f"{month:02}" for month in latest_months)
        row["complete_comparison_window"] = row["months_observed"] == len(latest_months)
    return rows, latest_months


def least_squares_slope(points: list[tuple[float, float]]) -> float | None:
    if len(points) < 2:
        return None
    mean_x = sum(x for x, _ in points) / len(points)
    mean_y = sum(y for _, y in points) / len(points)
    denominator = sum((x - mean_x) ** 2 for x, _ in points)
    if not denominator:
        return None
    return sum((x - mean_x) * (y - mean_y) for x, y in points) / denominator


def descriptive_trends(quarterly: list[dict]) -> list[dict]:
    """Separate descriptive fits; these are not a causal model or significance test."""
    rows = []
    for metric in metric_definitions():
        observations = [
            row
            for row in quarterly
            if row["metric"] == metric and row["complete_period"] and row["share"] is not None
        ]
        pre, post = [], []
        for observation in observations:
            year = int(observation["period"][:4])
            quarter = int(observation["period"][-1])
            point = (year + (quarter - 0.5) / 4, 100 * observation["share"])
            (pre if year < 2023 else post).append(point)
        before = least_squares_slope(pre)
        after = least_squares_slope(post)
        rows.append(
            {
                "metric": metric,
                "pre_2023_complete_quarters": len(pre),
                "post_2023_complete_quarters": len(post),
                "pre_2023_percentage_points_per_year": before,
                "post_2023_percentage_points_per_year": after,
                "slope_change_percentage_points_per_year": after - before
                if before is not None and after is not None
                else None,
            }
        )
    return rows


def review_sample(records: list[dict], per_era: int = 12) -> list[dict]:
    """Era samples, concrete role examples, and unmatched product-role candidates for manual audit."""
    import hashlib

    included = [record for record in records if record["included"]]
    eras = ((2011, 2015), (2016, 2019), (2020, 2022), (2023, 9999))
    selected = []
    for first, last in eras:
        candidates = [record for record in included if first <= int(record["month"][:4]) <= last]
        candidates.sort(key=lambda record: hashlib.sha256(str(record["comment_id"]).encode()).hexdigest())
        selected.extend(
            {**record, "selection": f"era_sample_{first}_{last}"} for record in candidates[:per_era]
        )
        for family in ROLE_FAMILIES:
            match = next((record for record in candidates if family in record["role_families"]), None)
            if match:
                selected.append({**match, "selection": f"role_example_{first}_{last}_{family}"})
        missed_candidates = [
            record
            for record in candidates
            if record["candidate_evidence"] and "product" not in record["role_families"]
        ]
        selected.extend(
            {**record, "selection": f"product_candidate_{first}_{last}"} for record in missed_candidates[:4]
        )
    excluded = [record for record in records if not record["included"] and record["text"]]
    excluded.sort(key=lambda record: hashlib.sha256(str(record["comment_id"]).encode()).hexdigest())
    selected.extend({**record, "selection": "excluded_comment_sample"} for record in excluded[:per_era])
    return selected
