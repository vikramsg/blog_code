"""Export four role measurements and source-linked product-role audit material."""

import csv
import hashlib
import json
from pathlib import Path

from .analyze import descriptive_trends, review_sample
from .present import ROLES, render_charts


def write_csv(path: Path, rows: list[dict]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        if rows:
            writer = csv.DictWriter(handle, fieldnames=list(rows[0]), lineterminator="\n")
            writer.writeheader()
            writer.writerows(rows)


def write_jsonl(path: Path, rows: list[dict]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def _example(record: dict) -> dict:
    return {
        "selection": record.get("selection", ""),
        "month": record["month"],
        "comment_id": record["comment_id"],
        "source_url": record["source_url"],
        "included": record["included"],
        "exclusion_reason": record["exclusion_reason"],
        "identification_method": record["identification_method"],
        "role_families": ";".join(record["role_families"]),
        "match_reasons": json.dumps(record["match_reasons"], ensure_ascii=False),
        "evidence": json.dumps(record["evidence"], ensure_ascii=False),
        "candidate_evidence": json.dumps(record["candidate_evidence"], ensure_ascii=False),
        "text_excerpt": record["text"][:1800],
    }


def _product_index(record: dict) -> dict:
    return {
        "month": record["month"],
        "comment_id": record["comment_id"],
        "source_url": record["source_url"],
        "included": record["included"],
        "exclusion_reason": record["exclusion_reason"],
        "identification_method": record["identification_method"],
        "role_families": ";".join(record["role_families"]),
        "product_match_reasons": ";".join(record["match_reasons"].get("product", [])),
        "header": record["text"].splitlines()[0][:300] if record["text"] else "",
        "product_evidence": json.dumps(record["evidence"].get("product", [])[:3], ensure_ascii=False),
        "candidate_evidence": json.dumps(record["candidate_evidence"][:2], ensure_ascii=False),
    }


def _share_with_count(row: dict) -> str:
    return "—" if row["share"] is None else f"{100 * row['share']:.1f}% ({row['count']}/{row['denominator']})"


def summary_markdown(manifest: dict, tables: dict, charts: list[str]) -> str:
    latest = manifest["requested_end"][:4]
    comparison = tables["comparable_years"]
    baselines = sorted({row["period"] for row in comparison if int(row["period"]) < 2023})
    baseline = baselines[-1] if baselines else None
    lines = [
        "# Frontend, backend, full-stack, and product-engineer hiring",
        "",
        f"Window: **{manifest['requested_start']}–{manifest['requested_end']}**. "
        "Measurements describe detected role advertisements in HN's hiring community, not vacancies or the wider labor market.",
        "",
        "**This is an unvalidated heuristic baseline. Better candidate capture does not establish complete recall or classification accuracy.**",
        "",
        "## Sample and denominator",
        "",
        f"- Canonical monthly threads: **{manifest['threads']} / {manifest['expected_months']}**; missing months: **{', '.join(manifest['missing_months']) or 'none'}**.",
        f"- Indexed top-level comments: **{manifest['indexed_listed_comments']:,} / {manifest['hn_listed_comments']:,}** HN-listed IDs; **{manifest['unindexed_listed_comments']:,}** are absent from the index.",
        f"- Retained hiring advertisements: **{manifest['advertisements']:,}**; detected product-engineer ads: **{manifest['product_engineer_advertisements']:,}**.",
        f"- Ads identified by an explicit advertised role rather than conventional hiring text: **{manifest['advertisements_identified_by_role']:,}**.",
        f"- Excluded comments: **{manifest['excluded_comments']:,}**, including **{manifest['duplicate_comments']:,}** exact same-month duplicates and **{manifest['outside_thread_month_comments']:,}** outside-month comments.",
        "",
        "Every percentage uses **all retained hiring advertisements** as its denominator, not just engineering ads. "
        "An ad can list more than one of the four roles; categories overlap and must not be stacked or added together.",
        "",
        "## Equivalent-month comparison",
        "",
        f"Every eligible year uses the same calendar months: **{', '.join(f'{month:02}' for month in manifest['comparison_months']) or 'none'}**. "
        "Years missing any comparison month are excluded.",
        "",
    ]
    lookup = {(row["period"], row["metric"]): row for row in comparison}
    if baseline and latest != baseline and (latest, "role:product") in lookup:
        lines += [f"| Advertised role | {baseline} | {latest} |", "|---|---:|---:|"]
        for role, label, _ in ROLES:
            before, after = lookup[(baseline, f"role:{role}")], lookup[(latest, f"role:{role}")]
            lines.append(f"| {label} | {_share_with_count(before)} | {_share_with_count(after)} |")
    else:
        lines.append(
            "This window does not contain both a pre-2023 year and a later equivalent-month comparison year."
        )
    lines += ["", "## Charts", ""]
    for chart in charts:
        lines += [f"![{chart.removesuffix('.webp').replace('_', ' ')}]({chart})", ""]
    lines += [
        "## Inspect product-engineer capture",
        "",
        "`product_engineer_matches.csv` includes every detected product-role ad with its source, matched evidence, and heuristic reasons. "
        "`product_engineer_candidates.csv` includes broad product/engineering candidates not counted as product roles, including excluded comments, so missed or ambiguous cases remain inspectable. "
        "`review_examples.csv` adds deterministic era samples and selected role/candidate examples; it is not an accuracy benchmark.",
        "",
        "## Interpretation limits",
        "",
        "- HN disproportionately represents technology companies and startups. Ads are not vacancies, hires, layoffs, or unique employers.",
        "- Product-focused role descriptions and qualified/reversed titles can qualify, but merely building a product, working with product managers, or serving product engineers does not.",
        "- English title/role heuristics can miss uncommon wording or confuse the subject of a description. Source-locatable evidence is not proof of correct attribution.",
        "- A representative, independently labeled cross-era benchmark is required before claims of complete capture, precision/recall, or strong substantive conclusions.",
        "- Vocabulary, ad length, repeated advertisers, employer mix, and changing indexed coverage can affect trends. Unindexed comments are not assumed to be live, deleted, or representative.",
        "- Only exact-text duplicates within a month are removed. Repeated advertisements in different months remain observations of advertised demand.",
        "- Complete-quarter/year charts exclude incomplete periods; equivalent-year charts use identical calendar months. Missing periods are gaps, not zero demand.",
        "- Any pre/post-2023 slopes in `descriptive_trends.csv` are unweighted descriptive fits to complete-quarter shares, not causal models or significance tests.",
        "- This dataset cannot explain layoffs, establish AI causality, or validate a future employment forecast.",
        "",
        "## Reproducibility",
        "",
        f"Classified-data SHA-256: `{manifest['classified_sha256']}`. Original JSON source responses and retrieval timestamps are cached locally. "
        "Exact replay requires those original caches; a fresh collection of the same months can differ.",
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
    write_csv(output_dir / "review_examples.csv", [_example(row) for row in examples])
    write_csv(
        output_dir / "product_engineer_matches.csv",
        [_product_index(row) for row in records if row["included"] and "product" in row["role_families"]],
    )
    write_csv(
        output_dir / "product_engineer_candidates.csv",
        [
            _product_index(row)
            for row in records
            if row["candidate_evidence"] and not (row["included"] and "product" in row["role_families"])
        ],
    )
    charts = render_charts(tables, output_dir)
    manifest["charts"] = charts
    (output_dir / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    (output_dir / "summary.md").write_text(summary_markdown(manifest, tables, charts), encoding="utf-8")
    return manifest
