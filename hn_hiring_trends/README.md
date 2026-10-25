# HN hiring trends

Analyze how explicit job titles and responsibilities change across Hacker News's monthly “Who is hiring?” advertisements. The analysis separates technical specialties, cross-stack breadth, product responsibilities, product-engineer titles, AI-product work, and AI-tool expectations.

This is evidence about **advertised language in HN's hiring community**, not a measure of vacancies, layoffs, actual skills, or the total labor market. It cannot establish AI causality or forecast future employment.

## Run with uv

Install [uv](https://docs.astral.sh/uv/getting-started/installation/), then run from this folder:

```sh
uv sync --locked
uv run hn-hiring
```

The default window starts in April 2011 and ends at the latest completed calendar month in UTC. The current month is excluded even if its thread already exists. Source responses are cached in `data/cache/`; outputs go to `data/results/`.

Choose a historical window and output directory:

```sh
uv run hn-hiring --start 2011-04 --end 2026-09 --output results
```

Reproduce the locally cached snapshot without network access:

```sh
uv run hn-hiring --start 2011-04 --end 2026-09 --output results --offline
```

Use `--refresh` to replace cached source responses with a new snapshot. A refresh can change historical results because source comments and index availability can change. `--offline` fails on missing responses rather than silently dropping data; it cannot be combined with `--refresh`. Downloads use four concurrent workers by default; set `--workers` to change this.

## Read the outputs

| Output | Purpose |
|---|---|
| `summary.md` | Coverage, equivalent-month comparisons, descriptive slopes, and charts |
| `monthly.csv`, `quarterly.csv`, `annual.csv` | Counts, denominators, shares, and calendar completeness for every metric |
| `comparable_years.csv` | Identical available calendar months in every eligible year, including the latest partial year |
| `descriptive_trends.csv` | Separate pre-2023 and post-2023 quarterly slopes, in percentage points per year |
| `source_coverage.csv` | Thread IDs, source links, indexed counts, and HN-listed comments missing from the index |
| `review_examples.csv` | Source-linked era samples and deliberately selected category-boundary examples |
| `manifest.json` | Requested window, missing months, totals, and classified-data SHA-256 |
| `advertisements.jsonl` | Local full-text classifications, matched evidence, and exclusion reasons |
| `review_sample.jsonl` | Local full text of the review examples |
| `*.png` | Six charts with explicit denominators and missing-period gaps |

The checked-in `results/` folder contains a historical run. Raw caches and full-text JSONL outputs are gitignored; the source-linked example excerpts, tables, manifest, and charts remain shareable. Exact snapshot reproduction requires the original local cache. Fresh downloads of the same dates are not guaranteed to reproduce a previous snapshot.

## Collection and counting

- Discovery uses [HN's Algolia search API](https://hn.algolia.com/api) for monthly hiring stories posted by `whoishiring`, beginning in April 2011. Four documented historical canonical threads have other authors: July 2011 ([2719028](https://news.ycombinator.com/item?id=2719028)), December 2011 ([3300290](https://news.ycombinator.com/item?id=3300290)), April 2015 ([9303396](https://news.ycombinator.com/item?id=9303396)), and May 2015 ([9471287](https://news.ycombinator.com/item?id=9471287)). The December official-account post explicitly redirects readers to its canonical thread. These IDs are curated source data, not inferred substitutes. Thread authors and selection sources appear in the coverage export. Job-seeker, freelance, and discussion threads are excluded; unresolved missing months are reported.
- Comment text comes from Algolia's thread tree. Only direct top-level comments whose IDs are still listed by the [official HN API](https://github.com/HackerNews/API) are eligible; replies are excluded.
- The official API supplies each thread's top-level comment IDs. The analysis reports how many are absent from the index. Those absences may include deleted, flagged, or unindexed comments; the code does not infer which. This is an indexed sample, not complete recovery of every historical comment.
- Plain text retains paragraph boundaries. Explicit hiring language and conventional company/role headers identify advertisements; ambiguous or unidentified comments remain available locally with exclusion reasons.
- A retained comment must have been posted during its thread's calendar month in UTC. Later comments remain inspectable but are excluded, so they cannot leak into completed-month or historical comparisons.
- Identical text, ignoring case and whitespace, counts once within a thread month. Repeated ads across different months remain observations of advertised demand. Different ads from the same employer are not merged.
- **One observation is one advertisement, not one job.** An ad mentioning frontend and backend openings can receive both role labels but is not automatically a full-stack job.

## Category interpretation

Role families describe explicit advertised specialties, not every technology mentioned in a company's description. They include frontend, backend, full-stack, mobile, infrastructure, data, ML/AI, security, embedded/hardware, QA, unspecified engineering, product management, design, sales/marketing, and support/operations. Labels can overlap and their percentages must not be stacked or added together.

| Signal | Interpretation |
|---|---|
| Technical breadth | Explicit full-stack or cross-frontend/backend responsibility language; separate specialist openings alone do not qualify |
| Product responsibility | Explicit customer contact, product decisions, experimentation, or outcome ownership, rather than the word “product” alone |
| Customer contact / product decisions / experimentation / outcome ownership | Individual components of product responsibility, with their matched language preserved |
| End-to-end ownership / founding engineer | Separate ownership language; these do not automatically establish product responsibility |
| Product-engineer title | An explicit role title, measured separately from responsibilities |
| AI-product work | Explicit advertised duties involving construction, integration, evaluation, or deployment of AI/ML systems; company descriptions alone do not qualify |
| AI-tool use | Explicit AI-assisted working practices or development-tool expectations |
| Breadth + product responsibility | Both signals in the same engineering advertisement; not proof that both duties belong to one particular position |

Rules and matched evidence are inspectable in `src/hn_hiring_trends/classify.py`. There is no model API key, paid inference, or claimed classification-accuracy score. Negative classifications mean “not detected by these rules,” not “this responsibility was absent.”

Experimentation requires product, user, customer, business, or growth context, or explicit A/B/user testing. Generic technical experiments do not establish product responsibility. A platform helping its users improve outcomes does not establish that the advertised engineer owns those outcomes.

“Product discovery” in merchandise search is not a product-decision responsibility. AI-product labels require a construction/integration action connected to an AI system or model, not nearby AI terminology. AI-tool labels require assistant-use expectations or an explicit AI-assisted development workflow; a vendor partnership or generic AI implementation skills do not qualify. Founding-engineer labels apply to engineering titles, not founding designers or product managers.

## Time comparisons and limitations

Role shares use **all retained advertisements** as their denominator. Responsibility, title, ownership, and AI-signal shares use **retained advertisements with explicit engineering-role language**. Every table includes the numerator and denominator. A zero denominator produces an unavailable share, not 0%.

Complete annual and quarterly charts exclude incomplete calendar periods; missing interior periods appear as gaps. The equivalent-year comparison uses the calendar months present in the requested final year and includes only years containing every one of those months. Thus a January–September window is never compared against another year's January–December total. The first partial year and years with missing months may be excluded.

The pre/post-2023 fits are descriptive, unweighted fits to complete-quarter shares. They are not significance tests or a causal model. The 2023 boundary is a convenient comparison around widespread generative-AI adoption, not a claim that all changes started then. Economic conditions, employer mix, recurring advertisers, ad length, terminology, and index coverage are not controlled for.

HN disproportionately represents startups and technology employers. Even a rise in product-responsibility language would not show that all engineers are becoming product managers, that AI caused layoffs, or that employment will recover within five years.

## Review classifications manually

Start with `review_examples.csv`, follow the HN source links, and use local `review_sample.jsonl` for full collected text. The sample has two different uses:

- Deterministic random-within-era advertisements expose ordinary cases from different periods.
- Deliberately chosen positive, negative, and excluded-comment examples expose category boundaries and extraction mistakes. These are **not** representative samples and cannot estimate error rates.

Before using these measurements as strong evidence in a post, create a separately labeled, representative benchmark across eras and assess precision and recall. Manual example inspection does not replace that benchmark. Inspect the charts directly for readability, missing-period gaps, and denominator labels; these visual checks are not automated screenshot tests.

One concrete subject-ambiguity case to include in that audit is [Wordware's May 2025 advertisement, comment 43866209](https://news.ycombinator.com/item?id=43866209). Its product description says it “lets you design, test, and deploy AI systems,” referring to product users rather than assigning that work to the applicant. The current rules detect AI-product work in this passage. Matched keywords and source-locatable evidence do not establish the action's subject; examine product-user descriptions separately from hiring requirements.

## Development checks

```sh
uv sync --locked
uv run ruff check .
uv run ruff format --check .
uv run pytest
```

Tests cover source selection, exclusions, overlapping classifications, counts and denominators, calendar comparability, cache behavior, and a fixture-driven collection-to-chart run. They do not assert internal code structure or compare screenshots.
