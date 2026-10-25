"""WebP charts of concrete advertised roles, with counts and comparable calendar windows."""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
from matplotlib.ticker import PercentFormatter

ROLES = (
    ("frontend", "Frontend", "#2166ac"),
    ("backend", "Backend", "#1b7837"),
    ("full_stack", "Full-stack", "#b35806"),
    ("product", "Product engineer", "#762a83"),
)


def _index(period: str, granularity: str) -> int:
    return int(period[:4]) * 4 + int(period[-1]) - 1 if granularity == "quarterly" else int(period)


def _label(index: int, granularity: str) -> str:
    return f"{index // 4}-Q{index % 4 + 1}" if granularity == "quarterly" else str(index)


def _save(figure, directory: Path, filename: str) -> str:
    try:
        figure.savefig(
            directory / filename, format="webp", dpi=150, facecolor="white", pil_kwargs={"lossless": True}
        )
    finally:
        plt.close(figure)
    return filename


def _role_trends(rows: list[dict], directory: Path, *, comparable: bool) -> str:
    granularity = "annual" if comparable else "quarterly"
    complete = "complete_comparison_window" if comparable else "complete_period"
    figure, axes = plt.subplots(2, 1, figsize=(12, 8), sharex=True)
    figure.subplots_adjust(left=0.09, right=0.97, top=0.83, bottom=0.23, hspace=0.13)
    title = (
        "Engineering roles in equivalent-month annual windows"
        if comparable
        else "Engineering role hiring on Hacker News"
    )
    figure.suptitle(title, x=0.09, y=0.96, ha="left", fontsize=17, fontweight="bold")
    subtitle = "Complete quarters only"
    if comparable and rows:
        subtitle = (
            f"Identical calendar months in each year: {rows[0]['comparison_months'].replace(';', ', ')}"
        )
    figure.text(
        0.09, 0.9, subtitle + " · an advertisement can list more than one role", fontsize=10, color="#555555"
    )
    eligible = [row for row in rows if row[complete]]
    periods = [_index(row["period"], granularity) for row in rows]
    grid = list(range(min(periods), max(periods) + 1)) if periods else []
    values = {(row["period"], row["metric"]): row for row in eligible}
    for axis in axes:
        axis.spines[["top", "right"]].set_visible(False)
        axis.grid(axis="y", color="#e5e5e5", linewidth=0.7)
        axis.set_axisbelow(True)
    if not grid or not eligible:
        for axis in axes:
            axis.text(
                0.5,
                0.5,
                "Insufficient complete periods for this comparison",
                ha="center",
                transform=axis.transAxes,
            )
            axis.set_xticks([])
            axis.set_yticks([])
    else:
        for role, label, color in ROLES:
            observations = [values.get((_label(index, granularity), f"role:{role}")) for index in grid]
            shares = [
                100 * row["share"] if row and row["share"] is not None else float("nan")
                for row in observations
            ]
            counts = [row["count"] if row else float("nan") for row in observations]
            axes[0].plot(grid, shares, color=color, label=label, linewidth=2, marker="o", markersize=3)
            axes[1].plot(grid, counts, color=color, linewidth=2, marker="o", markersize=3)
        step = max(1, (len(grid) + 9) // 10)
        ticks = grid[::step]
        if grid[-1] not in ticks:
            ticks.append(grid[-1])
        axes[1].set_xticks(ticks, [_label(index, granularity) for index in ticks], rotation=35, ha="right")
        axes[1].set_xlim(grid[0] - 0.4, grid[-1] + 0.4)
        boundary = _index("2023" if comparable else "2023-Q1", granularity)
        if grid[0] <= boundary <= grid[-1]:
            for axis in axes:
                axis.axvline(boundary, color="#777777", linewidth=1, linestyle="--")
            axes[0].text(
                boundary, 1.02, "2023", transform=axes[0].get_xaxis_transform(), ha="center", fontsize=9
            )
        handles, labels = axes[0].get_legend_handles_labels()
        figure.legend(handles, labels, loc="lower center", bbox_to_anchor=(0.53, 0.07), ncol=4, frameon=False)
    for axis in axes:
        axis.set_ylim(bottom=0)
    axes[0].set_ylabel("Share of all hiring ads")
    axes[0].yaxis.set_major_formatter(PercentFormatter(xmax=100))
    axes[1].set_ylabel("Ads mentioning the role")
    figure.text(
        0.09,
        0.015,
        "Counts are advertisements, not vacancies. Role categories overlap; gaps are incomplete/missing periods.\n2023 is a descriptive boundary, not evidence of AI causation. Classification is an unvalidated heuristic baseline.",
        fontsize=9,
        color="#555555",
    )
    filename = "comparable_year_roles.webp" if comparable else "quarterly_role_trends.webp"
    return _save(figure, directory, filename)


def _annual_heatmap(rows: list[dict], directory: Path) -> str:
    figure, axes = plt.subplots(figsize=(12, 4.5))
    figure.subplots_adjust(left=0.15, right=0.92, top=0.78, bottom=0.25)
    figure.suptitle(
        "Advertised engineering roles over time", x=0.15, y=0.96, ha="left", fontsize=17, fontweight="bold"
    )
    axes.set_title(
        "Complete years only · percentage of all retained hiring advertisements",
        loc="left",
        fontsize=10,
        pad=16,
    )
    eligible = [row for row in rows if row["complete_period"]]
    if not eligible:
        axes.text(0.5, 0.5, "Insufficient complete years", ha="center", transform=axes.transAxes)
        axes.set_xticks([])
        axes.set_yticks([])
    else:
        years = list(
            range(
                min(int(row["period"]) for row in eligible), max(int(row["period"]) for row in eligible) + 1
            )
        )
        values = {(int(row["period"]), row["metric"]): row["share"] for row in eligible}
        matrix = [
            [
                100 * value if (value := values.get((year, f"role:{role}"))) is not None else float("nan")
                for year in years
            ]
            for role, _, _ in ROLES
        ]
        colormap = plt.get_cmap("Blues").copy()
        colormap.set_bad("#eeeeee")
        image = axes.imshow(matrix, aspect="auto", cmap=colormap, vmin=0, vmax=100)
        for row_index, row in enumerate(matrix):
            for column_index, value in enumerate(row):
                if value == value:
                    axes.text(
                        column_index,
                        row_index,
                        f"{value:.1f}",
                        ha="center",
                        va="center",
                        fontsize=9,
                        color="white" if value >= 65 else "#333333",
                    )
        axes.set_yticks(range(len(ROLES)), [label for _, label, _ in ROLES])
        axes.set_xticks(range(len(years)), [str(year) for year in years], rotation=35, ha="right")
        figure.colorbar(image, ax=axes, pad=0.02, label="Share of all hiring ads (%)")
    figure.text(
        0.15,
        0.03,
        "Role mentions overlap; percentages must not be stacked or added. Blank cells are missing periods, not zero demand.\nProduct-engineer detection includes inspectable title and explicit role-description heuristics, not generic product work.",
        fontsize=9,
        color="#555555",
    )
    return _save(figure, directory, "annual_role_shares.webp")


def render_charts(tables: dict[str, list[dict]], output_dir: Path) -> list[str]:
    output_dir.mkdir(parents=True, exist_ok=True)
    with plt.rc_context({"font.family": "DejaVu Sans", "font.size": 10}):
        return [
            _annual_heatmap(tables["annual"], output_dir),
            _role_trends(tables["quarterly"], output_dir, comparable=False),
            _role_trends(tables["comparable_years"], output_dir, comparable=True),
        ]
