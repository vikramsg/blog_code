## Decisions

- Reuse the existing clone without altering its checkout
    - Decision: Create `feat/hn-hiring-trends` from freshly fetched `origin/main` in a separate worktree.
    - Why: The existing clone is on another branch; isolating this work preserves it and the blog draft. Tidy, First begins with a clean working boundary rather than changing unrelated projects.
    - Where: Git worktree `/Users/vikramsingh/Projects/Personal/worktrees/blog-code-hn-hiring-trends`
    - Source: agent

- Use explicit advertisement-level signals
    - Decision: Use transparent language rules without a paid model API, preserve matched evidence, and avoid attributing an advertisement's combined responsibilities to a particular advertised role.
    - Why: Multi-role ads cannot reliably establish role-level duties; an inspectable reproducible baseline is more defensible than opaque inference.
    - Where: `hn_hiring_trends/src/hn_hiring_trends/classify.py`
    - Source: agent

- Start discovery with the official-account indexed series
    - Decision: Discover monthly employer threads posted by `whoishiring`, collect Algolia's direct-comment text, and retain only comment IDs listed by the official HN API. The coverage audit subsequently added four explicit canonical historical IDs, as recorded below; unresolved missing months and unindexed IDs remain visible rather than inferred.
    - Why: This keeps a consistent, reproducible source cohort and avoids silent source substitutions. The index is not a complete archive; its changing coverage is a research limitation, not evidence of deleted or live comment status.
    - Where: `hn_hiring_trends/src/hn_hiring_trends/collect.py`; `results/source_coverage.csv`
    - Source: agent

- Preserve source snapshots and fail on incomplete retrieval
    - Decision: Cache JSON responses with source URLs and UTC retrieval timestamps, support offline replay and explicit refresh, retry transient HTTP failures three times, and stop on source errors or discovery truncation.
    - Why: Reproducibility requires the same inputs, and partial network failures must not silently become apparent hiring declines. HTTP retries do not change source selection or supply compatibility behavior.
    - Where: `hn_hiring_trends/src/hn_hiring_trends/collect.py::JsonCache`
    - Source: agent

- Count advertisements with overlapping labels
    - Decision: Use all retained advertisements for role-family shares and engineering advertisements for responsibility/title/AI shares. Preserve overlapping roles and both numerator and denominator. Remove case/whitespace-equivalent text only within the same month.
    - Why: Multi-role advertisements do not provide vacancy counts, and recurring monthly ads remain observations of advertised demand rather than unique employers.
    - Where: `hn_hiring_trends/src/hn_hiring_trends/analyze.py`
    - Source: agent

- Make exclusions inspectable over time
    - Decision: Retain excluded-comment reasons in local classified records and add per-month retained, engineering, unlabeled, unidentified-hiring, and duplicate counts to source coverage.
    - Why: Changes in ad identification or explicit role language can bias trends just as changing source coverage can.
    - Where: `hn_hiring_trends/src/hn_hiring_trends/cli.py::run_pipeline`
    - Source: agent

- Compare like calendar windows
    - Decision: Complete-year/quarter charts exclude incomplete calendar periods; comparable-year tables use the same observed months as the requested final year and exclude years missing any comparison month.
    - Why: Comparing partial-year counts to complete years creates artificial changes. Missing interior periods remain gaps, not zero demand.
    - Where: `hn_hiring_trends/src/hn_hiring_trends/analyze.py`; `hn_hiring_trends/src/hn_hiring_trends/present.py`
    - Source: agent

- Use descriptive trajectory comparisons rather than causal statistics
    - Decision: Fit separate equally weighted straight lines to complete-quarter shares before 2023 and from 2023 onward; report slopes in percentage points per year without p-values or causal claims.
    - Why: Repeated advertisers, vocabulary, employer mix, and economic changes are not controlled. These fits describe the selected sample and cannot explain layoffs or future employment.
    - Where: `hn_hiring_trends/src/hn_hiring_trends/analyze.py::descriptive_trends`; `results/descriptive_trends.csv`
    - Source: agent

- Separate a shareable result bundle from large local data
    - Decision: Commit tables, charts, summary, source-linked excerpts, and a classified-data hash; keep raw caches and full-text JSONL local and gitignored.
    - Why: The source snapshots are large. Links and evidence make results inspectable without placing the whole archive in Git, but exact replay on another machine requires those original caches.
    - Where: `hn_hiring_trends/.gitignore`; `hn_hiring_trends/src/hn_hiring_trends/output.py`
    - Source: agent

- Separate ordinary review samples from category-boundary examples
    - Decision: Select deterministic random-within-era ads using comment-ID hashes, and separately label deliberately chosen positive, negative, and excluded examples.
    - Why: Boundary examples help debug rules but are not representative and cannot establish classification accuracy. A separately labeled benchmark remains necessary for precision/recall claims.
    - Where: `hn_hiring_trends/src/hn_hiring_trends/analyze.py::review_sample`; `hn_hiring_trends/README.md`
    - Source: agent

- Keep the uv project isolated
    - Decision: Pin the Python minor version to 3.12, lock dependencies with uv, use HTTPX and Matplotlib plus pytest/Ruff, and avoid changes to existing projects or introducing repository-wide CI.
    - Why: A small standalone project fits the repository's collection-of-experiments structure. Tidy, First separates collection, classification, aggregation, output, and CLI without a shared framework.
    - Where: `hn_hiring_trends/pyproject.toml`; `hn_hiring_trends/uv.lock`; `hn_hiring_trends/.python-version`
    - Source: agent

- Correct canonical historical thread selection after auditing coverage
    - Decision: Curate July 2011 (2719028), December 2011 (3300290), April 2015 (9303396), and May 2015 (9471287), recording their authors and historical-canonical selection in the source export. Replace the December official post with the canonical thread it explicitly links to. Validate each selected title/month against both source providers.
    - Why: Author-only discovery falsely labeled three real monthly threads as absent and included a December redirect with almost no ads. These are fixed, documented source records, not guessed replacements or an automatic compatibility/fallback mechanism.
    - Where: `hn_hiring_trends/src/hn_hiring_trends/collect.py::HISTORICAL_CANONICAL_THREADS`; `hn_hiring_trends/README.md`
    - Source: agent

- Preserve real hiring advertisements without pipe-delimited headers
    - Decision: Reuse advertised-role context to retain explicit standalone role lines and recognize recruitment for someone or less-common titles. Distinguish personal employer voice from job-seeker requests. Share the recruitment-versus-discussion checks between role context and ad identification.
    - Why: Manual historical examples (5970371, 10157331, 7829708) showed valid older ads being excluded. Tidy, First extracts the shared recruitment check rather than introducing separate inconsistent acceptance paths. Existing discussion/job-seeker behavioral cases remain required.
    - Where: `hn_hiring_trends/src/hn_hiring_trends/classify.py`; `hn_hiring_trends/tests/test_classify.py`
    - Source: agent

- Refine explicit title and duty vocabulary from historical examples
    - Decision: Recognize full-stack product engineers, founding/full-time/senior-level qualifiers, frontend/backend shorthand, UI/UX variants, making product decisions, and explicit ML-product duties. Treat generic web developers as unspecified engineering rather than infer frontend specialization.
    - Why: Manual examples from 2014–2026 exposed clear missed language, including 10492711, 24975443, 7511134, 46468311, and 20593407. Titles must not establish duties, and generic web work is not a specialty. Conservative rules still miss uncommon or indirectly expressed roles.
    - Where: `hn_hiring_trends/src/hn_hiring_trends/classify.py`; `hn_hiring_trends/tests/test_classify.py`
    - Source: agent

- Do not derive job labels from URL slugs
    - Decision: Exclude URL-contained recruitment and role matches while preserving original text and exact evidence excerpts.
    - Why: Manual example 10155192 received its engineering label from a hiring URL rather than advertised title text. URL metadata is not explicit role evidence in the ad body.
    - Where: `hn_hiring_trends/src/hn_hiring_trends/classify.py::_inside_url`
    - Source: agent

- Exclude comments outside their thread's calendar month
    - Decision: Preserve but exclude comments whose UTC posting month differs from the selected thread month, and report their exclusion counts.
    - Why: Late comments otherwise leak into completed-month windows and historical comparisons. Source coverage still measures all indexed IDs, while analysis eligibility is a separate decision.
    - Where: `hn_hiring_trends/src/hn_hiring_trends/analyze.py::classify_records`; `hn_hiring_trends/src/hn_hiring_trends/cli.py`
    - Source: agent

- Make small role shares legible without changing their scale
    - Decision: Add one-decimal numeric values to valid annual heatmap cells, retaining a common 0–100% color scale and blank missing periods.
    - Why: Manual chart inspection showed most specialist rows were too pale to compare reliably. Numeric labels improve reading without using per-role scales that could exaggerate differences.
    - Where: `hn_hiring_trends/src/hn_hiring_trends/present.py::_role_heatmap`
    - Source: agent

- Narrow product outcomes and experimentation to advertised responsibilities
    - Decision: Treat company platforms helping developers/users as capability descriptions rather than applicant duties, exclude relative clauses describing behaviors that drive revenue, and require product/user/customer/business/growth context for experiments or assumptions (or explicit A/B/user testing).
    - Why: Manual boundary examples 3540450 and 20867460 showed company capability and analytical descriptions receiving outcome-ownership labels. Generic model-convergence experiments also do not demonstrate product discovery.
    - Where: `hn_hiring_trends/src/hn_hiring_trends/classify.py`; `hn_hiring_trends/tests/test_classify.py`; `hn_hiring_trends/README.md`
    - Source: agent

- Use LF line endings for the committed CSV exports
    - Decision: Set the CSV writer's line terminator to LF and regenerate CSV exports without changing their records.
    - Why: The default CSV dialect emitted CRLF, which Git's whitespace check flagged throughout the new result bundle. LF keeps the text exports clean in this repository without changing source text or numeric values.
    - Where: `hn_hiring_trends/src/hn_hiring_trends/output.py::write_csv`; `hn_hiring_trends/results/*.csv`
    - Source: agent

- Connect AI-product actions to AI-system objects and actual applicant subjects
    - Decision: Replace the loose construction-verb/nearby-AI window with direct AI-system/model object phrases. Replace arbitrary engineer mentions as duty context with advertised role titles, explicit role-duty subjects, or applicant/qualification language.
    - Why: The old rule counted API-design qualifications, tool-assisted shipping, and descriptions of customers building ML pipelines. Narrowing the grammar removes overbroad alternatives rather than adding company-specific exclusions.
    - Where: `hn_hiring_trends/src/hn_hiring_trends/classify.py::_AI_SYSTEM`, `_ROLE_DUTY_SUBJECT`, `_duty_context`; `hn_hiring_trends/tests/test_classify.py`
    - Source: reviewer
    - Origin: Reviewer reproduced false positives in 49200756, 17667107, 30880560, and 40849312 and recommended explicit action/object and applicant-subject checks.

- Require actual participation in product discovery
    - Decision: Remove the bare `product discovery` alternative; retain explicit ownership/decision verbs and stated role responsibilities that include discovery.
    - Why: Merchandise-search services are not product prioritization or discovery duties, and were inflating the combined breadth/product metric. No commerce-specific exception list was introduced.
    - Where: `hn_hiring_trends/src/hn_hiring_trends/classify.py::_SIGNAL_PATTERNS`; `hn_hiring_trends/tests/test_classify.py`
    - Source: reviewer
    - Origin: Reviewer identified Birchbox, Shopify, and Coveo merchandise-discovery descriptions (4597145, 28382369, 46616072, 46857798).

- Distinguish AI-assisted working practices from vendors and implementation skills
    - Decision: Remove standalone `with <brand>` as tool-use evidence, require coding/development context for generic AI tools, and recognize explicit assistant-use/proficiency and AI-tool shipping workflows.
    - Why: A Cursor partnership and prompting/vector-database skills do not establish AI-assisted development practices; actual tool-use expectations in 49200756 should be detected separately from AI-product duties.
    - Where: `hn_hiring_trends/src/hn_hiring_trends/classify.py::_AI_TOOL_ACTION`, `_CODING_ASSISTANT`, `_SIGNAL_PATTERNS`; `hn_hiring_trends/tests/test_classify.py`
    - Source: reviewer
    - Origin: Reviewer found material errors in the small AI-tool numerator, including 46858205 and 44441928.

- Attach founding-engineer labels only to engineering titles
    - Decision: Require both an engineering role family and an engineer/developer title noun before applying the founding modifier.
    - Why: Founding designers, product managers, and scientists are not founding-engineer titles merely because an advertisement also lists engineers.
    - Where: `hn_hiring_trends/src/hn_hiring_trends/classify.py::classify`; `hn_hiring_trends/tests/test_classify.py`
    - Source: reviewer
    - Origin: Reviewer reproduced founding-title contamination in 42103659, 43548733, and 49162833.

- Name the shared rule collection for all its signals
    - Decision: Rename private product-pattern/rule constants to `_SIGNAL_PATTERNS` and `_SIGNAL_RULES`.
    - Why: The collection also contains AI and ownership signals. This Tidy, First naming cleanup keeps the correction within the existing classifier rather than introducing another rule abstraction.
    - Where: `hn_hiring_trends/src/hn_hiring_trends/classify.py`
    - Source: reviewer
    - Origin: Reviewer suggested signal terminology as a concrete simplification/clarity improvement.

- Carry the benchmark prerequisite into the shareable summary
    - Decision: Include the need for a separately labeled, representative cross-era benchmark in generated `summary.md`, not only the operational README.
    - Why: The summary is likely to be read independently, and behavioral tests plus manual examples do not validate precision/recall or justify strong evidence claims.
    - Where: `hn_hiring_trends/src/hn_hiring_trends/output.py::summary_markdown`; `hn_hiring_trends/results/summary.md`
    - Source: reviewer
    - Origin: Reviewer recommended putting the README's explicit benchmark limitation into the primary shareable interpretation artifact.

- Recognize explicit AI-assisted workflows without restoring broad vendor matches
    - Decision: Recognize standalone AI-assisted coding/development practice statements and applicant-use statements naming coding assistants inside parentheses. Keep bare partnerships and generic AI implementation skills excluded.
    - Why: Clear daily-workflow expectations and `You use AI tools (Cursor/Copilot)` were missed after narrowing the earlier overbroad tool rule.
    - Where: `hn_hiring_trends/src/hn_hiring_trends/classify.py::_SIGNAL_PATTERNS`; `hn_hiring_trends/tests/test_classify.py`
    - Source: reviewer
    - Origin: Follow-up review identified missed explicit tool expectations in 49543040 and 46858502.

- Keep duty context within the action's clause
    - Decision: Bound context at pipe/semicolon and relative-clause boundaries; permit a hired role's explicit future relative-clause duties, but not coworkers' experience or hypothetical technical explanations. A role title authorizes a following imperative duty only when no other subject intervenes.
    - Why: Earlier header or applicant mentions were authorizing unrelated company/coworker model-training statements. The implementation reuses role-context validation and a small clause-prefix check rather than introducing a general parser or company-specific exceptions.
    - Where: `hn_hiring_trends/src/hn_hiring_trends/classify.py::_last_advertised_role`, `_duty_context`; `hn_hiring_trends/tests/test_classify.py`
    - Source: reviewer
    - Origin: Follow-up review reproduced subject leakage in 43864845, 43866206, and an inline company-description header.

- Allow coordinated AI-system actions to share their object
    - Decision: Factor AI-system action verbs into `_AI_SYSTEM_VERB` and permit a bounded list of coordinated actions before the same AI-system object, including evaluation/deployment duties.
    - Why: `build LLM-driven features` and `build, evaluate, and deploy LLM-driven features` describe the same relevant expectation and should not diverge merely because of coordination. The old arbitrary nearby-AI window remains removed.
    - Where: `hn_hiring_trends/src/hn_hiring_trends/classify.py::_AI_SYSTEM_VERB`, `_SIGNAL_PATTERNS`; `hn_hiring_trends/tests/test_classify.py`; `hn_hiring_trends/README.md`
    - Source: reviewer
    - Origin: Follow-up review identified coordinated-action false negatives in Starbridge ads 46468074 and 47221603 and suggested factoring the shared verb expression.

- Put classification uncertainty before the result tables
    - Decision: Add a prominent unvalidated-baseline warning at the beginning of the shareable summary, in addition to the detailed benchmark prerequisite in its interpretation limits.
    - Why: Rule refinements changing detected rates are evidence of measurement sensitivity, not validated improvements in accuracy. The headline numbers should not be mistaken for actual job prevalence or AI adoption.
    - Where: `hn_hiring_trends/src/hn_hiring_trends/output.py::summary_markdown`
    - Source: agent

- Replace the expanding synthetic phrase catalog with measurement contracts
    - Decision: Replace classifier wording/alias regressions with a small set of tests for background invariance, specialist-versus-full-stack breadth, title-versus-responsibility separation, independent AI dimensions, source-locatable evidence, and explicit negation. Do not assert incidental label ordering. Preserve collection, calendar/accounting, caching, and fixture end-to-end tests. Real-ad examples remain manual audit inputs, not an automated accuracy benchmark.
    - Why: The phrase catalog repeatedly tested strings the rules had just been written to recognize. That is weak evidence of research validity and was creating an example-by-example expansion loop. Tidy, First removes redundant checks and keeps the tests focused on the agreed measurements rather than regex vocabulary.
    - Where: `hn_hiring_trends/tests/test_classify.py`; collection and accounting behaviors remain covered separately
    - Source: user
    - Origin: User challenged the pasted classifier test catalog as coverage theater and clarified that the implementation task should continue.

- Exercise job-seeker exclusion through the complete pipeline
    - Decision: Add a job-seeker comment alongside real employer ads and discussion in the existing fixture-driven CLI test, and assert retained/excluded counts and unchanged category denominators.
    - Why: This checks the user-visible consequence of excluding non-employer comments, rather than rebuilding a unit-test catalog of job-seeker phrases.
    - Where: `hn_hiring_trends/tests/test_end_to_end.py`
    - Source: agent

- Remove incidental ordering/storage assertions from pipeline tests
    - Decision: Assert within-month deduplication and across-month retention by counts rather than returned row order. Check that a failed request cannot be replayed offline, rather than asserting a cache directory's file inventory.
    - Why: These tests should protect observable accounting and cache behavior while allowing harmless changes to record ordering or storage layout.
    - Where: `hn_hiring_trends/tests/test_analyze.py`; `hn_hiring_trends/tests/test_collect.py`
    - Source: agent

## Review focus

- Review classification boundaries and advertisement-level denominators, especially multi-role ads.
- Check historical source coverage, incomplete periods, and limitations on causal interpretation.
- Inspect ordinary and boundary examples across eras; this is not a validated classification-accuracy benchmark.
- Check that index-coverage and retained-advertisement changes do not get misrepresented as hiring changes.
- Assess whether the small modules and plotting helpers can be simplified without losing research safeguards.
- Verify the four curated historical canonical IDs and the exclusion of late comments.
- Review shared recruitment context and URL exclusion against both real ads and discussion negatives.
- Review AI action/object and applicant-subject grammar against both actual duties and company/customer descriptions.
- The results are a transparent rules-based baseline, not a validated benchmark; do not interpret the test count as classification accuracy.
- Review whether the remaining tests protect useful measurement/pipeline behavior, rather than exact wording, ordering, or code structure.
- Reviewer-driven changes:
    - Narrow AI-product action/object and applicant-subject matching.
    - Require explicit product-discovery participation.
    - Separate AI-assisted working practices from partnerships and implementation skills.
    - Restrict founding-engineer modifiers to engineering titles.
    - Rename the shared rule constants using signal terminology.
    - Add the benchmark prerequisite to the generated summary.
    - Recognize explicit AI-assisted and parenthesized-assistant workflows.
    - Bound duty context to the action's clause/subject.
    - Support coordinated AI-system action verbs.
