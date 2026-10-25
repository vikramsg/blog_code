"""Blog charts with explicit denominators, calendar windows, and missing-period gaps."""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
from matplotlib.ticker import PercentFormatter

COLORS = ("#2166ac", "#b35806", "#1b7837", "#762a83", "#a63603", "#557b83")
BROADENING = (
    ("signal:technical_breadth", "Technical breadth"),
    ("signal:product_responsibility", "Product responsibility"),
    ("signal:product_engineer_title", "Product-engineer title"),
    ("signal:breadth_and_product", "Breadth + product responsibility"),
)
AI_SIGNALS = (
    ("signal:ai_product_work", "AI-product work"),
    ("signal:ai_tool_use", "AI-tool use"),
)
ROLE_LABELS = {"role:ml_ai": "ML / AI", "role:qa": "QA", "role:full_stack": "Full-stack"}


def _period_index(period: str, granularity: str) -> int:
    year = int(period[:4])
    if granularity == "quarterly":
        return year * 4 + int(period[-1]) - 1
    if granularity == "monthly":
        return year * 12 + int(period[5:]) - 1
    return year


def _period_label(index: int, granularity: str) -> str:
    if granularity == "quarterly":
        return f"{index // 4}-Q{index % 4 + 1}"
    if granularity == "monthly":
        return f"{index // 12}-{index % 12 + 1:02}"
    return str(index)


def _calendar_grid(rows: list[dict], granularity: str, period_field: str = "period") -> list[int]:
    indices = [_period_index(row[period_field], granularity) for row in rows]
    return list(range(min(indices), max(indices) + 1)) if indices else []


def _figure(title: str, subtitle: str, footer: str):
    figure, axes = plt.subplots(figsize=(12, 6))
    figure.subplots_adjust(left=0.09, right=0.97, top=0.82, bottom=0.35)
    figure.suptitle(title, x=0.09, y=0.96, ha="left", fontsize=17, fontweight="bold")
    axes.set_title(subtitle, loc="left", fontsize=10, color="#555555", pad=14)
    axes.spines[["top", "right"]].set_visible(False)
    axes.grid(axis="y", color="#e5e5e5", linewidth=0.7)
    axes.set_axisbelow(True)
    figure.text(0.09, 0.035, footer, fontsize=9, color="#555555", va="bottom")
    return figure, axes


def _empty(axes, message: str) -> None:
    axes.text(0.5, 0.5, message, ha="center", va="center", transform=axes.transAxes, color="#555555")
    axes.set_xticks([])
    axes.set_yticks([])


def _calendar_axis(axes, grid: list[int], granularity: str) -> None:
    step = max(1, (len(grid) + 9) // 10)
    ticks = grid[::step]
    if grid[-1] not in ticks:
        ticks.append(grid[-1])
    axes.set_xticks(ticks, [_period_label(index, granularity) for index in ticks], rotation=35, ha="right")
    axes.set_xlim(grid[0] - 0.4, grid[-1] + 0.4)


def _boundary(axes, grid: list[int], granularity: str) -> None:
    boundary = _period_index("2023-Q1" if granularity == "quarterly" else "2023", granularity)
    if grid[0] <= boundary <= grid[-1]:
        axes.axvline(boundary, color="#777777", linestyle="--", linewidth=1, zorder=1)
        axes.text(
            boundary,
            1.02,
            "2023",
            transform=axes.get_xaxis_transform(),
            ha="center",
            fontsize=9,
            color="#666666",
        )


def _save(figure, output_dir: Path, filename: str) -> str:
    try:
        figure.savefig(output_dir / filename, dpi=150, facecolor="white")
    finally:
        plt.close(figure)
    return filename


def _share_chart(
    rows: list[dict],
    metrics: tuple[tuple[str, str], ...],
    output_dir: Path,
    filename: str,
    title: str,
    subtitle: str,
    granularity: str = "quarterly",
    completeness_field: str = "complete_period",
) -> str:
    figure, axes = _figure(
        title,
        subtitle,
        "Signals overlap; shares use engineering advertisements, not vacancies. Gaps are missing/ineligible periods or zero denominators.\n"
        "2023 marks a descriptive boundary, not evidence of AI causation.",
    )
    grid = _calendar_grid(rows, granularity)
    eligible = [row for row in rows if row[completeness_field]]
    if not grid or not eligible:
        _empty(axes, "Insufficient complete periods for this comparison.")
        return _save(figure, output_dir, filename)
    values = {(row["period"], row["metric"]): row["share"] for row in eligible}
    finite_values = []
    for color, (metric, label) in zip(COLORS, metrics, strict=False):
        shares = [values.get((_period_label(index, granularity), metric)) for index in grid]
        percentages = [100 * value if value is not None else float("nan") for value in shares]
        finite_values.extend(value for value in percentages if value == value)
        axes.plot(grid, percentages, label=label, color=color, linewidth=2, marker="o", markersize=3)
    _calendar_axis(axes, grid, granularity)
    _boundary(axes, grid, granularity)
    axes.set_ylabel("Share of engineering advertisements")
    axes.yaxis.set_major_formatter(PercentFormatter(xmax=100))
    axes.set_ylim(0, min(100, max(5, max(finite_values, default=0) * 1.15)))
    if not finite_values:
        axes.text(
            0.5,
            0.5,
            "No engineering denominator in the eligible periods.",
            transform=axes.transAxes,
            ha="center",
            color="#555555",
        )
    figure.legend(loc="lower center", bbox_to_anchor=(0.53, 0.12), ncol=2, frameon=False, fontsize=9)
    return _save(figure, output_dir, filename)


def _role_heatmap(rows: list[dict], output_dir: Path) -> str:
    figure, axes = _figure(
        "Role-family mentions in hiring advertisements",
        "Complete calendar years only · percentage of all advertisements",
        "Role families overlap: an advertisement can mention several roles. Categories must not be added together.\n"
        "Blank cells indicate missing/incomplete years or a zero advertisement denominator; these are not zero shares.",
    )
    eligible = [row for row in rows if row["complete_period"] and row["metric"].startswith("role:")]
    if not eligible:
        _empty(axes, "Insufficient complete calendar years for the role comparison.")
        return _save(figure, output_dir, "annual_role_shares.png")
    grid = _calendar_grid(eligible, "annual")
    roles = sorted({row["metric"] for row in eligible})
    values = {(row["period"], row["metric"]): row["share"] for row in eligible}
    matrix = [
        [
            100 * values[(str(year), role)] if values.get((str(year), role)) is not None else float("nan")
            for year in grid
        ]
        for role in roles
    ]
    axes.grid(False)
    colormap = plt.get_cmap("Blues").copy()
    colormap.set_bad("#eeeeee")
    image = axes.imshow(matrix, aspect="auto", cmap=colormap, vmin=0, vmax=100, interpolation="nearest")
    for row_index, row in enumerate(matrix):
        for column_index, value in enumerate(row):
            if value == value:
                axes.text(
                    column_index,
                    row_index,
                    f"{value:.1f}",
                    ha="center",
                    va="center",
                    fontsize=7,
                    color="white" if value >= 65 else "#333333",
                )
    axes.set_yticks(
        range(len(roles)),
        [ROLE_LABELS.get(role, role.removeprefix("role:").replace("_", " ").capitalize()) for role in roles],
        fontsize=9,
    )
    step = max(1, (len(grid) + 13) // 14)
    axes.set_xticks(range(0, len(grid), step), [str(year) for year in grid[::step]], rotation=35, ha="right")
    figure.subplots_adjust(left=0.22, bottom=0.2)
    figure.colorbar(image, ax=axes, pad=0.025, label="Share of all advertisements (%)")
    return _save(figure, output_dir, "annual_role_shares.png")


def _advertisement_counts(rows: list[dict], output_dir: Path) -> str:
    figure, axes = _figure(
        "Quarterly hiring-advertisement counts",
        "Complete calendar quarters only · engineering advertisements are a subset of all advertisements",
        "Counts represent included advertisements, not vacancies or unique employers. Missing/incomplete quarters are gaps.\n"
        "2023 marks a descriptive boundary, not evidence of AI causation.",
    )
    grid = _calendar_grid(rows, "quarterly")
    eligible = {row["period"]: row for row in rows if row["complete_period"]}
    if not grid or not eligible:
        _empty(axes, "Insufficient complete calendar quarters for the count comparison.")
    else:
        for color, field, label in (
            (COLORS[0], "advertisements", "All advertisements"),
            (COLORS[1], "engineering_advertisements", "Engineering advertisements"),
        ):
            counts = [
                eligible.get(_period_label(index, "quarterly"), {}).get(field, float("nan")) for index in grid
            ]
            axes.plot(grid, counts, label=label, color=color, linewidth=2, marker="o", markersize=3)
        _calendar_axis(axes, grid, "quarterly")
        _boundary(axes, grid, "quarterly")
        axes.set_ylabel("Advertisements")
        axes.set_ylim(bottom=0)
        figure.legend(loc="lower center", bbox_to_anchor=(0.53, 0.12), ncol=2, frameon=False)
    return _save(figure, output_dir, "quarterly_advertisement_counts.png")


def _coverage_chart(coverage: list[dict], output_dir: Path) -> str:
    figure, axes = _figure(
        "Indexed coverage of HN-listed top-level comments",
        "Monthly indexed comments ÷ HN-listed comments · before hiring-advertisement classification",
        "Coverage measures source retrieval, not how representative HN is of the labor market.\n"
        "Missing months and months with no listed-comment denominator are gaps, not 0% coverage.",
    )
    grid = _calendar_grid(coverage, "monthly", "month")
    if not grid:
        _empty(axes, "No monthly source-coverage observations available.")
    else:
        by_month = {row["month"]: row for row in coverage}
        percentages = []
        for index in grid:
            row = by_month.get(_period_label(index, "monthly"), {})
            listed = row.get("hn_listed_comments", 0)
            percentages.append(100 * row["indexed_listed_comments"] / listed if listed else float("nan"))
        axes.plot(grid, percentages, color=COLORS[0], linewidth=1.8, marker="o", markersize=2.5)
        _calendar_axis(axes, grid, "monthly")
        axes.set_ylabel("Indexed share of listed comments")
        axes.yaxis.set_major_formatter(PercentFormatter(xmax=100))
        axes.set_ylim(0, 105)
        if not any(value == value for value in percentages):
            axes.text(
                0.5,
                0.5,
                "No listed-comment denominator available.",
                transform=axes.transAxes,
                ha="center",
                color="#555555",
            )
    return _save(figure, output_dir, "monthly_indexed_coverage.png")


def render_charts(tables: dict[str, list[dict]], coverage: list[dict], output_dir: Path) -> list[str]:
    """Write six PNG charts, including explicit empty states when calendar coverage is insufficient."""
    output_dir.mkdir(parents=True, exist_ok=True)
    quarterly = tables.get("quarterly", [])
    comparable = tables.get("comparable_years", [])
    windows = {row["comparison_months"] for row in comparable if row["complete_comparison_window"]}
    if len(windows) == 1:
        months = next(iter(windows)).split(";")
        month_names = ("Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec")
        window_label = ", ".join(month_names[int(month) - 1] for month in months)
        subtitle = f"Identical calendar months in every year: {window_label} · includes latest available year"
    else:
        # Different calendar-month windows cannot be interpreted as a single annual trajectory.
        comparable = []
        subtitle = "No single complete equivalent-calendar-month comparison window available"
    with plt.rc_context(
        {
            "font.family": "DejaVu Sans",
            "font.size": 10,
            "axes.labelcolor": "#333333",
            "xtick.color": "#555555",
            "ytick.color": "#555555",
        }
    ):
        return [
            _role_heatmap(tables.get("annual", []), output_dir),
            _share_chart(
                quarterly,
                BROADENING,
                output_dir,
                "quarterly_broadening_product.png",
                "Technical breadth and product expectations",
                "Complete calendar quarters only · explicit responsibility language is separate from titles",
            ),
            _share_chart(
                quarterly,
                AI_SIGNALS,
                output_dir,
                "quarterly_ai_signals.png",
                "AI-product work and AI-tool expectations",
                "Complete calendar quarters only · building AI products is distinct from using AI tools",
            ),
            _advertisement_counts(quarterly, output_dir),
            _share_chart(
                comparable,
                BROADENING + AI_SIGNALS,
                output_dir,
                "comparable_year_signals.png",
                "Engineering expectations in equivalent-month annual windows",
                subtitle,
                "annual",
                "complete_comparison_window",
            ),
            _coverage_chart(coverage, output_dir),
        ]
