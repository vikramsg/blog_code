# HN hiring trends

## Agreed objective

Analyze historical HN monthly hiring advertisements to investigate whether engineering expectations are broadening technically and toward product ownership, and whether the observed trend changed after generative AI became widely available. Do not assume the thesis is true or infer AI causality, layoffs, vacancy counts, or future employment from this sample.

## Deliverables

- A standalone `hn_hiring_trends/` Python project run, locked, and tested with uv.
- Cached source collection with original comment IDs, dates, source links, and visible coverage gaps.
- Separate, inspectable dimensions for role-family mentions, technical breadth, product responsibility, ownership language, AI-product work, and AI-tool expectations. Titles must remain separate from responsibilities.
- Quarterly and annual counts and shares, equivalent-month partial-year comparisons, charts, and source-linked examples.
- Operational documentation covering commands, category definitions, limitations, and reproducibility.
- Behavioral tests, a real historical-data end-to-end run, manual example/chart inspection, and an independent background review.
- A pushed branch and GitHub PR with a short feature summary following any repository template, without implementation or verification details.

## Approach

1. Inspect the repository and create a separate worktree from upstream main.
2. Tidy, First: establish small collection, classification, aggregation, and presentation modules with explicit data boundaries, using repository conventions where present. Avoid a framework, paid API dependency, and compatibility shims.
3. Discover the monthly historical hiring series, cache source snapshots, and retain top-level advertisements rather than conversation replies. Report missing months and unavailable source records.
4. Define transparent explicit-language categories using examples from different eras. Keep overlapping labels and ambiguous records inspectable. These are advertisement-level signals, not inferred vacancy counts or duties assigned to particular roles within a multi-role ad.
5. Produce quarterly/yearly aggregates, counts alongside percentages, combined breadth/product signals, and comparable partial-year windows. Show the pre/post-2023 trajectories descriptively, without causal claims.
6. Write behavioral tests for extraction, classification, denominators, time windows, caching, and fixture-based end-to-end output. Do not automate manual review or use change-detection tests.
7. Run the full available historical collection through charts, inspect coverage and examples across eras, then obtain independent background review. Accept correctness and simplification findings without silently expanding scope.
8. Rerun affected checks, commit, push, and create the PR.

## Plan immutability

Implementation starts after this file is created. Do not modify this plan during implementation. Record all implementation choices, deviations, and reviewer/user-driven changes in `.agents/implementation-notes/hn-hiring-trends.md`, including Tidy, First reasoning and review focus.
