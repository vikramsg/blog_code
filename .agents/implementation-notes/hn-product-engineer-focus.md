## Decisions

- Narrow the project to one hiring measurement
    - Decision: Remove other job-category, technical-breadth, product-responsibility, ownership, and AI measurements from the analysis and result bundle.
    - Why: The user wants product-engineer hiring only, with better detection rather than more output categories. Tidy, First removes the unused classification/presentation paths before improving the focused detector.
    - Where: `hn_hiring_trends/src/hn_hiring_trends/`; `hn_hiring_trends/results/`
    - Source: user
    - Origin: User asked to retain only product engineer and inspect more heuristics for fuller capture.

- Use all retained hiring advertisements as the denominator
    - Decision: Report product-engineer ad counts and their share of all retained hiring ads, labeling this denominator explicitly.
    - Why: The previous engineering-only share requires retaining a separate, imperfect engineering classifier that the focused project otherwise no longer needs. Counts remain visible, and the new percentage must not be compared directly with the old denominator.
    - Where: `hn_hiring_trends/src/hn_hiring_trends/analyze.py`; `hn_hiring_trends/README.md`
    - Source: agent

- Retain four concrete role categories rather than product alone
    - Decision: Keep frontend, backend, full-stack, and product engineer as the four reported categories; remove the previous indirect measurements. The product-only plan remains unchanged as an earlier scope record; the corrected implementation plan is `hn-four-engineering-roles.md`.
    - Why: The user clarified that frontend/backend/full-stack should remain and objected to vague measurements, not those job categories.
    - Where: `hn_hiring_trends/src/hn_hiring_trends/`; `hn_hiring_trends/results/`
    - Source: user
    - Origin: User clarified the desired categories during implementation.

- Commit chart images only as WebP
    - Decision: Render charts directly to lossless WebP and replace the PNG charts in the existing PR. Do not create committed PNG/JPEG chart intermediates.
    - Why: The user explicitly requested WebP-only committed images.
    - Where: `hn_hiring_trends/src/hn_hiring_trends/present.py`; `hn_hiring_trends/results/`
    - Source: user
    - Origin: User asked to commit images only as WebP, not PNG or JPG.

- Separate advertisement identification from role measurements
    - Decision: Extract the previous hiring-ad selector into `advertisements.py`, preserving its behavior while removing unrelated measurements from the focused detector. Clear newly recognized advertised roles can identify otherwise missed hiring ads; preserve an `identification_method` field and counts for that route.
    - Why: Advertisement membership is a separate concern from which of the four roles is advertised. The original selector loses some clear product-role ads, so the improvement must apply before those records are discarded. A manual replay of 94,946 eligible legacy records found no differences in the extracted conventional selector.
    - Where: `hn_hiring_trends/src/hn_hiring_trends/advertisements.py`; `analyze.py::classify_records`; `cli.py::run_pipeline`
    - Source: agent

- Keep product matches and unmatched candidates inspectable
    - Decision: Export every counted product-role ad and broad unmatched/excluded product-role candidates with source links, exact evidence, detection reasons, and identification method. Keep representative era samples separate from selected candidates.
    - Why: Fuller candidate capture needs inspection of both hits and misses. Candidate counts and selected examples are not a representative accuracy benchmark.
    - Where: `hn_hiring_trends/src/hn_hiring_trends/output.py`; `analyze.py::review_sample`
    - Source: agent

- Retain calendar/accounting contracts and verify the WebP output format
    - Decision: Update existing tests to the four-role schema and shared all-ad denominator; exercise product counts through the existing CLI fixture. Verify generated images are decodable WebP, without adding screenshot tests or a wording/alias catalog.
    - Why: These protect observable output behavior and the user's format requirement, not a coverage number or unvalidated language-classification score.
    - Where: `hn_hiring_trends/tests/test_analyze.py`; `test_classify.py`; `test_end_to_end.py`
    - Source: agent

- Mine real historical wording before broadening product-role heuristics
    - Decision: Audit the legacy corpus using broad candidate classes and retain selected source-linked positive/negative cases locally. Cover qualified/reversed/abbreviated titles, role descriptions, product-team recruitment, vacancy-link wording, and actual missed hiring ads.
    - Why: The audit found real misses such as `Software Engineer - Product`, `Product / Frontend Engineer`, `SWE, Product`, qualified developer titles, and explicit role definitions. Customer, manager, physical-engineering, qualification, testimonial, and optional-quality references require separate treatment. Selected cases and candidate frequencies are not accuracy or complete-recall estimates.
    - Where: `hn_hiring_trends/data/product_engineer_audit/`; `hn_hiring_trends/src/hn_hiring_trends/classify.py`
    - Source: agent

- Require engineering evidence for combined-role descriptions
    - Decision: A combined product-definition/management description requires an active engineering opening or an explicit engineering noun inside the combined-role description. Company-wide engineer identities require an actual engineering opening somewhere in the ad, rather than an unknown role state; another nonengineering opening does not cancel that identity.
    - Why: Product-definition work alone must not turn an unrecognized nonengineering vacancy into a product-engineer role. Conversely, a manager/designer listed elsewhere must not veto an explicitly described engineer opening.
    - Where: `hn_hiring_trends/src/hn_hiring_trends/classify.py::classify`
    - Source: agent

- Do not freeze report-disclaimer wording in the end-to-end test
    - Decision: Remove the literal disclaimer-sentence assertion while retaining counts, exclusions, denominators, cache replay, and decodable WebP checks. Inspect report wording manually.
    - Why: The report retained its warning but rephrased it; the literal assertion was a change-detection check, not a useful behavior contract.
    - Where: `hn_hiring_trends/tests/test_end_to_end.py`
    - Source: agent

- Keep complete product source indexes concise
    - Decision: Include every matched/candidate record in the respective CSV indexes, but show only a short header and bounded evidence excerpts. Preserve complete text and evidence in local classified JSONL.
    - Why: The broad candidate set contains over ten thousand ads. Complete source IDs and URLs are useful for coverage inspection, but duplicating entire ad bodies in Git would create an unnecessarily large result bundle.
    - Where: `hn_hiring_trends/src/hn_hiring_trends/output.py::_product_index`; `hn_hiring_trends/README.md`
    - Source: agent

- Use a small set of general product-role evidence routes
    - Decision: Detect advertised qualified/reversed/abbreviated titles, explicit product-focused recruitment or engineer-role definitions, recruitment into product-engineering teams, and vacancy-link slugs attached to the ad. Preserve each route as a match reason.
    - Why: The real-corpus audit showed misses across all these forms. These are general context rules, not employer-specific exceptions or a general-purpose language parser; generic product work and optional product intuition remain insufficient.
    - Where: `hn_hiring_trends/src/hn_hiring_trends/classify.py`
    - Source: agent

- Keep manager and nonsoftware exclusions local to the referenced role
    - Decision: Reject manager-only, prior-experience, testimonial, customer/support references, and explicitly physical product-engineering role evidence without globally vetoing separate engineer openings in the same ad. Keep unsupported hacker/builder or optional role directions as candidates unless explicit combined engineering/product work establishes the role.
    - Why: A manager mentioned elsewhere must not hide real engineer hiring, while mentioning an engineer in a customer's workflow or earlier career must not create a vacancy. Broad optional language does not establish an assigned role.
    - Where: `hn_hiring_trends/src/hn_hiring_trends/classify.py::_reference`, `_product_title`, `classify`
    - Source: agent

- Preserve source positions while matching punctuation variants
    - Decision: Translate Unicode dash/space variants character-for-character for matching and slice evidence from the original source segment.
    - Why: Qualified titles use inconsistent punctuation, but matched evidence must still be locatable verbatim in the collected ad.
    - Where: `hn_hiring_trends/src/hn_hiring_trends/classify.py::_PUNCTUATION`, `_excerpt`
    - Source: agent

- Let Matplotlib establish the upper axis bounds before fixing the zero baseline
    - Decision: Apply the zero lower bound after plotting the role series, not before.
    - Why: Manual WebP inspection showed that setting the limits on empty axes disabled autoscaling and clipped all values above the initial upper bound. This corrects the chart behavior without adding automated visual/screenshot tests.
    - Where: `hn_hiring_trends/src/hn_hiring_trends/present.py::_role_trends`
    - Source: agent

## Review focus

- Inspect real missed candidate titles and the boundaries between product-engineer roles, product-focused role descriptions, and company/team/product names.
- Verify all percentages clearly use retained hiring advertisements, not the prior engineering-only denominator or estimated vacancies.
- Reviewer-driven changes: none
- Audit qualified/reversed/abbreviated and role-description matches against the source, including attached vacancy links and mixed-role posts.
- Inspect unmatched product-hacker, conditional, and company-wide product-first candidates; the additional heuristics do not establish complete recall.
