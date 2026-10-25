# HN engineering hiring trends

Compare advertised **frontend, backend, full-stack, and product-engineer** roles across Hacker News's monthly “Who is hiring?” threads. Role counts and clearly labeled percentages are accompanied by source-linked evidence and product-role candidates for inspecting missed or ambiguous cases.

The heuristics are an exploratory baseline, not a validated census of jobs or actual responsibilities. Complete capture, precision/recall, and strong labor-market claims require a representative, independently labeled benchmark.

## Run with uv

Install [uv](https://docs.astral.sh/uv/getting-started/installation/) and run from this folder:

```sh
uv sync --locked
uv run hn-hiring
```

The default window begins in April 2011 and ends at the latest completed calendar month in UTC. Responses are cached in `data/cache/`; output goes to `data/results/`.

Choose a fixed window and output location:

```sh
uv run hn-hiring --start 2011-04 --end 2026-09 --output results
```

Reproduce the locally cached snapshot without network requests:

```sh
uv run hn-hiring --start 2011-04 --end 2026-09 --output results --offline
```

`--offline` fails if any requested source is absent. `--refresh` replaces cached responses with a new snapshot; fresh collection can change historical results as comments and index availability change. These options cannot be combined. `--workers` controls concurrent downloads; the default is four.

## Measurements and interpretation

- One observation is one retained advertisement, not a vacancy or a unique employer.
- All four role shares use **all retained hiring advertisements** as the denominator, including advertisements for other roles. Do not compare these percentages directly with engineering-only percentages.
- Role mentions overlap. An ad can advertise frontend and backend specialists, or a full-stack product engineer. The four percentages must not be stacked or added together.
- Separate frontend/backend openings do not imply a full-stack position. A technology mentioned in a company's description does not establish a specialist vacancy.
- Product-engineer detection considers qualified, reversed, and abbreviated titles; explicit product-focused engineering role descriptions; and explicit recruitment into product-engineering teams. Evidence and detection reasons remain visible.
- Generic product work, working alongside product managers, customer references to engineers, optional product intuition, and manager-only hiring do not by themselves establish a product-engineer role.
- No technical-breadth, product-responsibility, AI, or ownership scores are reported.

Definitions and context heuristics are inspectable in `src/hn_hiring_trends/classify.py`. Negative labels mean “not detected by these rules,” not proof that a role is absent. A broad candidate match is an audit lead, not a counted product engineer.

## Outputs

| File | Use |
|---|---|
| `summary.md` | Four-role comparison, charts, sample coverage, and interpretation limits |
| `monthly.csv`, `quarterly.csv`, `annual.csv` | Counts, denominators, shares, and calendar completeness for the four roles |
| `annual_totals.csv` | Total hiring advertisements per calendar year, with observed months and partial-year flags |
| `comparable_years.csv` | Identical calendar-month windows in every eligible year, including the latest partial year |
| `descriptive_trends.csv` | Descriptive pre/post-2023 slopes for the four role shares |
| `product_engineer_matches.csv` | Every counted product-role ad, source links, evidence, and detection reasons |
| `product_engineer_candidates.csv` | Broad product/engineering candidates not counted, including excluded comments |
| `review_examples.csv` | Deterministic era samples plus selected role and unmatched-candidate examples |
| `source_coverage.csv` | Canonical thread IDs/authors, indexed coverage, and retention/exclusion counts |
| `manifest.json` | Requested window, totals, missing months, output chart names, and classified-data hash |
| `*.webp` | Lossless WebP charts; no PNG/JPEG chart intermediates are needed |
| `advertisements.jsonl`, `review_sample.jsonl` | Local full-text classifications and audit examples, gitignored |

The checked-in `results/` contains a historical run. Large source caches and full-text JSONL files remain local; exact replay requires those original caches. A fresh download of the same dates is not guaranteed to reproduce an earlier snapshot.

Chart filenames include an image-content hash. A changed rendering gets a new path in `manifest.json` and `summary.md`, preventing previews from reusing an older image under the same URL.

## Collection and calendar comparisons

Discovery uses [HN's Algolia API](https://hn.algolia.com/api) for monthly employer threads posted by `whoishiring`, plus four documented historical canonical IDs: July 2011 ([2719028](https://news.ycombinator.com/item?id=2719028)), December 2011 ([3300290](https://news.ycombinator.com/item?id=3300290)), April 2015 ([9303396](https://news.ycombinator.com/item?id=9303396)), and May 2015 ([9471287](https://news.ycombinator.com/item?id=9471287)). The December official-account post explicitly redirects to its canonical thread. Source authors and selection methods appear in the coverage export.

Only indexed direct comments still listed by the [official HN API](https://github.com/HackerNews/API) are eligible. Replies, job-seeker requests, and discussion are excluded. An explicit advertised role can establish a hiring ad even when a conventional hiring phrase is absent. A retained comment must have been posted during its thread's UTC calendar month; late comments remain inspectable but do not leak into completed-month comparisons.

Identical text, ignoring case and whitespace, counts once within a month. Repeated ads in different months remain observations of advertised demand. Missing canonical months and HN-listed comments absent from the index are reported rather than imputed; their deletion/visibility status is not inferred.

Complete-quarter/year charts exclude incomplete calendar periods. Equivalent-year comparisons use the months present in the requested final year and include only years with every one of those months. Thus January–September is never compared against a full January–December total. Missing periods appear as gaps, not zero demand.

Pre/post-2023 slopes are descriptive, equally weighted fits to complete-quarter shares. They provide neither a causal estimate nor a significance test. Economic conditions, employer mix, repeated advertisers, ad length, vocabulary, and changing source coverage are not controlled. This dataset cannot explain layoffs or validate a future employment forecast.

The annual total-volume table/chart count each retained ad once, regardless of how many categories it mentions. They do not estimate vacancies from role lists or unspecified headcount. Partial 2011 and latest-year windows are marked explicitly.

## Manual audit

Start with `product_engineer_matches.csv` and `product_engineer_candidates.csv`, follow the HN links, and inspect the full collected text in local `advertisements.jsonl`. Check who the role description refers to: incoming engineers, existing colleagues, product users, or a different advertised position.

These complete source indexes show a short header, up to three product-evidence excerpts, and up to two candidate excerpts per ad, rather than committing the entire corpus text. Additional evidence and full text remain in local `advertisements.jsonl`.

`review_examples.csv` separates deterministic random-within-era examples from deliberately selected role/candidate cases. The latter are not representative and cannot estimate accuracy. Broad candidate mining and manually selected misses can improve coverage, but a separate representative cross-era benchmark is needed to measure precision and recall, including roles that the candidate rules never find.

Inspect the WebP charts directly for legible labels, source gaps, and correct denominators. These visual checks are manual, not screenshot tests.

## Development checks

```sh
uv sync --locked
uv run ruff check .
uv run ruff format --check .
uv run pytest
```

Tests protect selected role-measurement contracts, source selection, exclusions, calendar/accounting behavior, cache replay, and a fixture-driven collection-to-WebP run. They do not freeze a vocabulary catalog, internal structure, record ordering, or screenshots, and they do not establish classification accuracy.
