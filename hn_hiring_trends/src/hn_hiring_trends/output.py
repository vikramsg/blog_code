"""Export inspectable counts, source coverage, and a descriptive research summary."""

import csv
import hashlib
import json
from pathlib import Path

from .analyze import descriptive_trends, review_sample
from .present import render_charts


def write_csv(path: Path, rows: list[dict]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        if not rows:
            return
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def write_jsonl(path: Path, rows: list[dict]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def percentage(value: float | None) -> str:
    return "—" if value is None else f"{100 * value:.1f}%"


def summary_markdown(manifest: dict, tables: dict, trends: list[dict], charts: list[str]) -> str:
    latest = manifest["requested_end"][:4]
    comparable = tables["comparable_years"]
    baseline_years = sorted({row["period"] for row in comparable if int(row["period"]) < 2023})
    baseline = baseline_years[-1] if baseline_years else None
    metrics = (
        "role:frontend",
        "role:backend",
        "role:full_stack",
        "role:ml_ai",
        "signal:technical_breadth",
        "signal:product_responsibility",
        "signal:product_engineer_title",
        "signal:breadth_and_product",
        "signal:ai_product_work",
        "signal:ai_tool_use",
    )
    lines = [
        "# HN hiring advertisement trends",
        "",
        f"Requested window: **{manifest['requested_start']}–{manifest['requested_end']}**. "
        "This is a descriptive study of explicit language in indexed HN advertisements, not a labor-market census.",
        "",
        "**Classification is an unvalidated rules-based baseline. Detected signals are not estimates of actual job responsibilities or AI adoption.**",
        "",
        "## Sample and coverage",
        "",
        f"- Canonical monthly threads found: **{manifest['threads']} / {manifest['expected_months']}**.",
        f"- Missing monthly threads: **{', '.join(manifest['missing_months']) or 'none'}**.",
        f"- HN-listed top-level comments: **{manifest['hn_listed_comments']:,}**; "
        f"present in the index: **{manifest['indexed_listed_comments']:,}**.",
        f"- HN-listed comments absent from the index: **{manifest['unindexed_listed_comments']:,}**. "
        "Their visibility/deletion status is not inferred. Coverage changes can affect trends.",
        f"- Retained advertisements: **{manifest['advertisements']:,}**; "
        f"with explicit engineering-role language: **{manifest['engineering_advertisements']:,}**.",
        f"- Excluded indexed comments: **{manifest['excluded_comments']:,}**, including "
        f"**{manifest['duplicate_comments']:,}** same-month exact-text duplicates and "
        f"**{manifest['outside_thread_month_comments']:,}** comments posted outside their thread month.",
        "",
        "## Equivalent-month comparison",
        "",
        f"Calendar months used in every compared year: **{', '.join(f'{month:02}' for month in manifest['comparison_months']) or 'none'}**. "
        "Years missing any comparison month are excluded. Role shares use all retained advertisements; "
        "responsibility and AI-signal shares use retained engineering advertisements.",
        "",
    ]
    if baseline and latest != baseline and any(row["period"] == latest for row in comparable):
        lines += [f"| Explicit signal | {baseline} | {latest} |", "|---|---:|---:|"]
        lookup = {(row["period"], row["metric"]): row for row in comparable}
        for metric in metrics:
            before, after = lookup.get((baseline, metric)), lookup.get((latest, metric))
            if before and after:
                lines.append(
                    f"| {metric.split(':')[1].replace('_', ' ')} | {percentage(before['share'])} ({before['count']}/{before['denominator']}) | {percentage(after['share'])} ({after['count']}/{after['denominator']}) |"
                )
    else:
        lines.append(
            "The requested window does not provide both a pre-2023 comparison year and a later comparison year."
        )
    lines += [
        "",
        "## Descriptive change in trajectory",
        "",
        "Separate straight-line fits use complete quarters before 2023 and from 2023 onward, with each quarter weighted equally. "
        "Slopes are percentage points per year. A slope difference is not evidence that AI caused a change, "
        "and these fits do not provide uncertainty estimates or adjust for economic conditions or repeated advertisers.",
        "",
        "| Explicit signal | Before 2023 | From 2023 | Difference |",
        "|---|---:|---:|---:|",
    ]
    for row in trends:
        if row["metric"] not in metrics:
            continue
        values = [
            row[key]
            for key in (
                "pre_2023_percentage_points_per_year",
                "post_2023_percentage_points_per_year",
                "slope_change_percentage_points_per_year",
            )
        ]
        lines.append(
            f"| {row['metric'].split(':')[1].replace('_', ' ')} | "
            + " | ".join("—" if value is None else f"{value:+.2f}" for value in values)
            + " |"
        )
    lines += ["", "## Charts", ""]
    for filename in charts:
        lines += [f"![{filename.removesuffix('.png').replace('_', ' ')}]({filename})", ""]
    lines += [
        "## Interpretation limits",
        "",
        "- HN overrepresents technology companies and startups. Advertisements are not vacancies, hires, layoffs, or employment totals.",
        "- Labels overlap. A multi-role advertisement may mention several specialties and responsibilities; co-occurrence does not prove one engineer is expected to perform them all.",
        "- Technical breadth requires explicit full-stack or cross-stack responsibility language, not merely separate frontend and backend openings.",
        "- Product-engineer titles are separate from product responsibilities. Advertised AI-product duties are separate from expectations to use AI development tools; company descriptions alone do not establish either.",
        "- Rules detect explicit language, not actual skills or workplace behavior. Changing vocabulary, job-ad length, source availability, and classification errors can affect the result.",
        "- A separately labeled, representative benchmark across eras is required before using these measurements as strong evidence or claiming classification precision/recall. Manual example inspection and behavioral tests do not provide that validation.",
        "- Repeated advertisements across months remain observations of advertised demand; they are not independent employers. Only exact-text duplicates within a month are removed.",
        "- `review_examples.csv` contains deterministic era samples and deliberately selected positive/negative examples. The latter are not representative and must not be used to estimate accuracy. Full text is available locally in `review_sample.jsonl`.",
        "- This dataset cannot establish AI causality, explain layoffs, or validate a five-year employment forecast.",
        "",
        "## Reproducibility",
        "",
        f"The manifest identifies classified data with SHA-256 **`{manifest['classified_sha256']}`**. "
        "Original source responses and retrieval timestamps are cached locally. Use the cached offline rerun "
        "to reproduce this snapshot; a fresh collection can differ as comments and the index change.",
        "",
    ]
    return "\n".join(lines)


def write_outputs(
    output_dir: Path, records: list[dict], coverage: list[dict], tables: dict, manifest: dict
) -> dict:
    output_dir.mkdir(parents=True, exist_ok=True)
    write_jsonl(output_dir / "advertisements.jsonl", records)
    manifest["classified_sha256"] = hashlib.sha256(
        (output_dir / "advertisements.jsonl").read_bytes()
    ).hexdigest()
    write_csv(output_dir / "source_coverage.csv", coverage)
    for name, rows in tables.items():
        write_csv(output_dir / f"{name}.csv", rows)
    trends = descriptive_trends(tables["quarterly"])
    write_csv(output_dir / "descriptive_trends.csv", trends)
    examples = review_sample(records)
    write_jsonl(output_dir / "review_sample.jsonl", examples)
    write_csv(
        output_dir / "review_examples.csv",
        [
            {
                "selection": row["selection"],
                "month": row["month"],
                "comment_id": row["comment_id"],
                "source_url": row["source_url"],
                "included": row["included"],
                "exclusion_reason": row["exclusion_reason"],
                "role_families": ";".join(row.get("role_families", [])),
                "positive_signals": ";".join(
                    name for name, positive in row.get("signals", {}).items() if positive
                ),
                "evidence": json.dumps(row.get("evidence", {}), ensure_ascii=False),
                "text_excerpt": row["text"][:1600],
            }
            for row in examples
        ],
    )
    charts = render_charts(tables, coverage, output_dir)
    manifest["charts"] = charts
    (output_dir / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    (output_dir / "summary.md").write_text(
        summary_markdown(manifest, tables, trends, charts), encoding="utf-8"
    )
    return manifest
