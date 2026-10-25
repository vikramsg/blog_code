from datetime import date

import pytest

from hn_hiring_trends.analyze import (
    aggregate,
    classify_records,
    comparable_years,
    descriptive_trends,
    least_squares_slope,
)


def ad(comment_id, month, families):
    return {
        "comment_id": comment_id,
        "month": month,
        "included": True,
        "role_families": families,
    }


def metric_row(rows, metric, period=None):
    return next(
        row for row in rows if row["metric"] == metric and (period is None or row["period"] == period)
    )


def test_overlapping_roles_count_advertisements_not_vacancies():
    records = [
        ad(1, "2022-01", ["frontend", "backend"]),
        ad(2, "2022-01", ["backend"]),
        ad(3, "2022-01", []),
    ]
    rows = aggregate(records, [{"month": "2022-01"}], date(2022, 1, 1), date(2022, 1, 1), "monthly")
    backend = metric_row(rows, "role:backend")
    frontend = metric_row(rows, "role:frontend")
    assert (backend["count"], backend["denominator"]) == (2, 3)
    assert backend["share"] == pytest.approx(2 / 3)
    assert (frontend["count"], frontend["denominator"]) == (1, 3)


def test_product_and_fullstack_mentions_have_the_same_denominator_without_requiring_each_other():
    records = [
        ad(1, "2022-01", ["full_stack"]),
        ad(2, "2022-01", ["product"]),
        ad(3, "2022-01", ["full_stack", "product"]),
    ]
    rows = aggregate(records, [{"month": "2022-01"}], date(2022, 1, 1), date(2022, 1, 1), "monthly")
    assert metric_row(rows, "role:product")["count"] == 2
    assert metric_row(rows, "role:full_stack")["count"] == 2
    assert metric_row(rows, "role:product")["denominator"] == 3
    assert metric_row(rows, "role:full_stack")["denominator"] == 3


def test_missing_month_is_not_interpreted_as_zero_demand_or_complete_quarter():
    rows = aggregate(
        [ad(1, "2022-01", ["backend"])],
        [{"month": "2022-01"}],
        date(2022, 1, 1),
        date(2022, 3, 1),
        "quarterly",
    )
    quarter = metric_row(rows, "role:backend")
    assert not quarter["complete_period"]
    assert (quarter["months_observed"], quarter["calendar_months"]) == (1, 3)
    monthly = aggregate([], [], date(2022, 2, 1), date(2022, 2, 1), "monthly")
    assert metric_row(monthly, "role:backend")["share"] is None


def test_partial_year_comparison_uses_identical_calendar_months():
    coverage = [
        {"month": month} for month in ("2021-01", "2021-02", "2021-03", "2022-01", "2023-01", "2023-02")
    ]
    records = [ad(index, row["month"], ["backend"]) for index, row in enumerate(coverage)]
    rows, months = comparable_years(records, coverage, date(2023, 2, 1))
    assert months == [1, 2]
    assert {row["period"] for row in rows} == {"2021", "2023"}
    assert metric_row(rows, "role:backend", "2021")["denominator"] == 2
    assert all(row["complete_comparison_window"] for row in rows)


def test_same_month_exact_duplicates_removed_but_repeated_monthly_demand_retained():
    text = "Acme | Backend Engineer | Remote | Full-time\nWe are hiring. Apply at jobs@example.com."
    records = [
        {"comment_id": index, "month": month, "text": body, "comment_created_at": month + "-02T00:00:00Z"}
        for index, month, body in (
            (1, "2022-01", text),
            (2, "2022-01", text.replace("\n", "  ")),
            (3, "2022-02", text),
        )
    ]
    classified = classify_records(records)
    january = [row for row in classified if row["month"] == "2022-01"]
    february = [row for row in classified if row["month"] == "2022-02"]
    assert sum(row["included"] for row in january) == 1
    assert all(row["included"] for row in february)
    assert all(
        row["exclusion_reason"] == "same_month_exact_text_duplicate" for row in january if not row["included"]
    )


def test_late_comments_do_not_leak_into_a_completed_thread_month():
    records = [
        {
            "comment_id": 1,
            "month": "2022-01",
            "comment_created_at": "2022-02-01T00:00:00Z",
            "text": "Acme | Backend Engineer | Remote",
        }
    ]
    classified = classify_records(records)
    assert not classified[0]["included"]
    assert classified[0]["exclusion_reason"] == "outside_thread_month"


def test_descriptive_trends_exclude_incomplete_quarters():
    quarters = [
        {"period": "2021-Q1", "metric": "role:product", "complete_period": True, "share": 0.1},
        {"period": "2022-Q1", "metric": "role:product", "complete_period": True, "share": 0.2},
        {"period": "2023-Q1", "metric": "role:product", "complete_period": True, "share": 0.2},
        {"period": "2024-Q1", "metric": "role:product", "complete_period": True, "share": 0.25},
        {"period": "2024-Q2", "metric": "role:product", "complete_period": False, "share": 0.99},
    ]
    row = next(row for row in descriptive_trends(quarters) if row["metric"] == "role:product")
    assert row["pre_2023_percentage_points_per_year"] == pytest.approx(10)
    assert row["post_2023_percentage_points_per_year"] == pytest.approx(5)
    assert row["slope_change_percentage_points_per_year"] == pytest.approx(-5)


def test_slope_is_unavailable_without_two_distinct_observation_times():
    assert least_squares_slope([(2022, 1)]) is None
    assert least_squares_slope([(2022, 1), (2022, 2)]) is None
