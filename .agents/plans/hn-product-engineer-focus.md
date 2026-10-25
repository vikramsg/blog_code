# Product-engineer hiring focus

## Objective

Narrow the existing HN hiring analysis and PR to product-engineer hiring only. Improve detection by inspecting real advertisements across the historical series, not by expanding a synthetic phrase-test catalog. Do not promise exhaustive recall without a separately labeled benchmark.

## Deliverables and approach

- Reuse the existing canonical-thread collection, source caches, duplicate handling, completed-month windows, and source coverage checks.
- Tidy, First: remove unrelated role, breadth, responsibility, ownership, and AI measurements and their presentation machinery rather than retain unused classification complexity.
- Audit broad product/engineering candidates in real historical advertisements, including missed explicit titles, qualified titles, reversed title/department formats, and clear role descriptions. Preserve matched evidence and the detection heuristic for manual inspection.
- Distinguish advertised individual engineering roles from company names, customers, managers, and general descriptions of product development. Explicit product-focused role descriptions may support a product-engineer classification; generic product work alone does not.
- Report monthly/quarterly/annual product-engineer advertisement counts and shares, equivalent-month year comparisons, source coverage, and source-linked match/candidate examples. Use all retained hiring advertisements as the denominator, explicitly labeling the change from the previous engineering-only denominator.
- Keep a small set of behavioral measurement/pipeline contracts. Do not create a wording-by-wording test catalog or mistake selected tests/manual examples for classification-accuracy validation.
- Run checks and a full cached historical end-to-end analysis, manually inspect real matches and misses, obtain an advisory background review, then update the existing pushed branch and PR description to its narrowed features.

## Implementation notes and immutability

Do not modify this plan after implementation starts. Record choices and reviewer/user-driven changes in `.agents/implementation-notes/hn-product-engineer-focus.md`. The earlier broad-analysis plan remains unchanged.
