"""Identify four advertised engineering roles with inspectable source evidence.

Categories overlap: a full-stack product engineer can belong to both categories.
Unmatched product-role wording is retained for inspection, not treated as a label.
"""

import re

from .advertisements import (
    advertised_title,
    inside_url,
    is_hiring_ad,
    is_job_seeker,
    negated,
    recruitment_statement,
    segments,
)

ROLE_FAMILIES: tuple[str, ...] = ("frontend", "backend", "full_stack", "product")

# Translation preserves character positions so evidence still slices the original.
_PUNCTUATION = str.maketrans({char: "-" for char in "‐‑‒–—−"} | {"\u00a0": " ", "\u202f": " "})
_ENGINEER = r"(?:engineers?|developers?|devs?|engs?|SWEs?)"
_SENIORITY = r"(?:senior|Sr\.?|junior|Jr\.?|staff|principal|lead|founding|graduate|intern|mid(?:[ -]level)?)"
_FRONT = r"(?:front[ -]?end|client[ -]side|UI(?:\s*/\s*UX)?)"
_BACK = r"(?:back[ -]?end|server[ -]side)"
_FULL = r"full[ -]?stack"
_ORIENTATION = r"(?:minded|focused|oriented|driven|centric|first|leaning|sensitive)"
_TECHNOLOGY = r"(?:Python|Java(?:Script)?|TypeScript|Ruby(?: on Rails)?|Rails|Go|Rust|C\+\+|C\#|PHP|React|Node(?:\.js)?|Django|Kotlin|Elixir|Scala)"
_QUALIFIER = rf"(?:{_SENIORITY}|{_FRONT}|{_BACK}|{_FULL}|{_TECHNOLOGY}|software|web|mobile|iOS|Android|application|technical|design|UX|data|ad|advertising|product(?:[ -]{_ORIENTATION})?)"
_SEPARATOR = r"[ \t/(),:-]+"
_QUALIFIERS = rf"(?:{_QUALIFIER}{_SEPARATOR}){{0,4}}"
_LEADING_QUALIFIERS = rf"(?:{_QUALIFIER}[ \t/(-]+){{0,4}}"
_ENGINEERING_TITLE = re.compile(rf"\b{_LEADING_QUALIFIERS}{_ENGINEER}\b", re.I)
_OTHER_TITLE = re.compile(
    rf"\b(?:{_SENIORITY}\s+)*(?:(?:product|engineering|software|AI|data|sales|marketing|design|project|program|account|customer success)\s+)*(?:managers?|directors?|designers?|owners?|analysts?|scientists?|executives?)\b|\b(?:CTO|CEO|VP|head of)\b",
    re.I,
)
_LIST_TITLE = re.compile(
    rf"\b(?:(?:{_QUALIFIER}|infrastructure|platform|DevOps|cloud|security|streaming|NLP|API|test|QA|growth|research|systems|engineering)\s+)*"
    rf"(?:{_ENGINEER}|interns?|managers?|designers?|directors?|scientists?|analysts?|owners?|executives?)\b|\bSREs?\b",
    re.I,
)
_LIST_GAP = re.compile(r"[\s,/&+*#•§()\[\]-]*(?:(?:and|or|a|an)\b[\s,/&+*#•§()\[\]-]*)*", re.I)
_TITLE_FRAGMENT = re.compile(
    rf"\b(?:{_QUALIFIER}|engineering|growth|infrastructure|platform|DevOps|AI|great|strong|very)\b", re.I
)
_RECRUITMENT = re.compile(
    r"\b(?:hiring|recruiting|seek(?:ing)?|looking (?:for|to hire)|we (?:need|want)|(?:open|available) (?:roles?|positions?))\b|\b(?:roles?|positions?|hiring)\s*:",
    re.I,
)
_PAST_OR_OPTIONAL = re.compile(
    r"\b(?:experience (?:as|in|engineering|working)|years of experience|previously|formerly|used to|worked as|last (?:week|year)|years ago|"
    r"bonus|nice[ -]to[ -]have|optional|preference for|depending on|opportunity (?:for .*? )?to be)\b",
    re.I,
)
_HISTORICAL = re.compile(r"\b(?:previously|formerly|last (?:week|year)|years ago|used to)\b", re.I)
_REFERENCE_PREFIX = re.compile(
    r"\b(?:work(?:ing)? (?:closely |directly )?with|collaborat\w* with|support(?:ing)?|help(?:ing)?|tools? for|for (?:our|the) (?:customers|users)|"
    r"customers? (?:are|include)|users? (?:are|include)|used by|made up of|comprised of|team of|I am|I'm)\b",
    re.I,
)
_NON_PRODUCT_TITLE = re.compile(
    r"\b(?:managers?|management|director|VP|head|chief|designers?|owners?|analysts?|marketers?|marketing|evangelists?|research|adoption|"
    r"leaders?|leads?(?!\s+(?:software\s+)?(?:engineer|developer))|people|folks|security|support|reliability|embedded|mechanical|hardware|electrical|manufacturing|"
    r"solar|microgrid|supercharger|energy (?:products?|charging)|industrial storage|commercial solar)\b",
    re.I,
)
_ROLE_PATTERNS = {
    name: re.compile(
        rf"\b{_LEADING_QUALIFIERS}{stem}{_SEPARATOR}{_QUALIFIERS}{_ENGINEER}\b|"
        rf"\b{_LEADING_QUALIFIERS}(?:{_ENGINEER}|engineering)\s*\(\s*(?:{_QUALIFIER}{_SEPARATOR}){{0,2}}{stem}\b"
        rf"(?:{_SEPARATOR}{_QUALIFIERS}{_ENGINEER}\b)?|"
        rf"\b{_LEADING_QUALIFIERS}(?:{_ENGINEER}|engineering)\s*[,/:-]\s*(?:{_QUALIFIER}{_SEPARATOR}){{0,2}}{stem}\b"
        rf"(?!{_SEPARATOR}{_QUALIFIERS}{_ENGINEER}\b)",
        re.I,
    )
    for name, stem in (
        ("frontend", _FRONT),
        ("backend", _BACK),
        ("full_stack", _FULL),
        ("product", "product"),
    )
}
_PRODUCT_ORIENTED = re.compile(
    rf"\bproduct[ -]{_ORIENTATION}{_SEPARATOR}{_QUALIFIERS}{_ENGINEER}\b|"
    rf"\b{_QUALIFIERS}{_ENGINEER}(?:\s*[,(:/-]\s*|\s+(?:who are|that are|who have|with|have|are)\s+(?:(?:a|strong|huge|great|deep)\s+){{0,2}})"
    rf"(?:product[ -]{_ORIENTATION}|product (?:mindset|focus))\b",
    re.I,
)
_PRODUCT_IDENTITY = re.compile(
    rf"\b(?:we (?:view|see|consider|describe|treat) (?:each|every|our|all) {_ENGINEER}[^.!?;|]{{0,35}}\bas (?:a |an |true )*product {_ENGINEER}|"
    rf"(?:our|each|every|all) {_ENGINEER}[^.!?;|]{{0,35}}\b(?:are|is|act as) (?:true )?product {_ENGINEER})\b",
    re.I,
)
_PRODUCT_TEAM = re.compile(
    r"\bproduct[ /-]engineering\s+(?:teams?|group|org(?:anization)?|department)\b", re.I
)
_INTO_TEAM = re.compile(r"\b(?:join|joining|into|for|on|within)\b", re.I)
_PRODUCT_DEFINITION = re.compile(
    r"(?<![\w-])(?:defin(?:e|ing) (?:the |our )?product|own(?:ing)? product decisions|"
    r"(?:their|your|our) own product managers?|effectively product managers?|"
    r"(?:PM|product manager),?\s*(?:designer,?\s*)?and engineer in one person|"
    r"part engineer[^.!?;|]{0,40}product designer)\b",
    re.I,
)
_PRODUCT_SUBJECT = re.compile(
    r"\s*(?:\[\d+\])?\s+(?:will|are|build|create|develop|don't just|do not just)\b", re.I
)
_CANDIDATE = re.compile(
    rf"\bproduct\b[^.!?;|]{{0,100}}\b(?:{_ENGINEER}|engineering|development|builders?|hackers?)\b|"
    rf"\b(?:{_ENGINEER}|engineering|development)\b[^.!?;|]{{0,100}}\bproduct\b",
    re.I,
)
_VACANCY_SLUG = re.compile(
    rf"(?:product[-_/](?:(?:software|full[-_]?stack|frontend|backend|senior)[-_/])*{_ENGINEER}|"
    rf"{_ENGINEER}[-_/]product)(?![a-z])",
    re.I,
)


def _excerpt(source: str, start: int, end: int) -> str:
    return source[max(0, start - 45) : min(len(source), max(end, start + 165))].strip()


def _title_field(prefix: str) -> str:
    return re.split(r"[|;]", prefix)[-1]


def _recruitment_matches(segment: str, start: int = 0, end: int | None = None) -> list[re.Match[str]]:
    return [
        cue
        for cue in _RECRUITMENT.finditer(segment, start, len(segment) if end is None else end)
        if recruitment_statement(segment, cue)
        and not re.match(r"\s+manager\b", segment[cue.end() :], re.I)
        and not re.search(r"\b(?:was|were|previously|formerly|used to)\s*$", segment[: cue.start()], re.I)
    ]


def _reference(segment: str, match: re.Match[str]) -> bool:
    prefix = segment[: match.start()]
    field_start = max(prefix.rfind("|"), prefix.rfind(";")) + 1
    hiring = _recruitment_matches(segment, field_start, match.start())
    if hiring:
        prefix = segment[hiring[-1].end() : match.start()]
    else:
        prefix = prefix[field_start:]
    return bool(
        negated(segment, match.start(), match.end())
        or _PAST_OR_OPTIONAL.search(prefix + match.group())
        or _HISTORICAL.search(re.split(r"[,|;:]", segment[match.end() :])[0])
        or _REFERENCE_PREFIX.search(prefix)
    )


def _advertised_role(segment: str, match: re.Match[str]) -> bool:
    if inside_url(segment, match.start()) or _reference(segment, match):
        return False
    if advertised_title(segment, match):
        return True
    prefix = segment[: match.start()]
    field_start = max(prefix.rfind("|"), prefix.rfind(";")) + 1
    hiring = _recruitment_matches(segment, field_start, match.start())
    if hiring:
        prefix = segment[hiring[-1].end() : match.start()]
        if not (_ENGINEERING_TITLE.search(prefix) or _OTHER_TITLE.search(prefix)):
            return True
    else:
        prefix = re.split(r"\s+-\s+", prefix[field_start:])[-1]
    # Conventional headers and comma-separated vacancy lists also use abbreviated
    # titles that the general advertisement identifier need not recognize.
    remainder = _TITLE_FRAGMENT.sub("", _LIST_TITLE.sub("", prefix))
    if _LIST_GAP.fullmatch(remainder):
        return bool(
            hiring
            or re.match(r"\s*(?:$|[.,|:()\]/-]|at\b|wanted\b|job posting\b)", segment[match.end() :], re.I)
        )
    return False


def _product_title(segment: str, match: re.Match[str]) -> bool:
    if inside_url(segment, match.start()):
        url = next(
            url for url in re.finditer(r"https?://\S+", segment) if url.start() <= match.start() < url.end()
        )
        slug = url.group().split("/", 3)[-1].replace("-", " ").replace("_", " ")
        return not (
            _NON_PRODUCT_TITLE.search(_title_field(segment[: url.start()]))
            or _NON_PRODUCT_TITLE.search(slug)
            or re.search(r"/(?:blog|posts?|articles?|guides?)/", url.group(), re.I)
        )
    prefix = segment[: match.start()]
    hiring = _recruitment_matches(segment, end=match.start())
    if hiring:
        prefix = prefix[hiring[-1].end() :]
    prefix = re.split(r"[,|;:&]|\b(?:and|as well as)\b", prefix, flags=re.I)[-1]
    suffix = re.split(r"[,|;]", segment[match.end() :])[0]
    if re.search(r"\bengineering\s*[,/:-]", match.group(), re.I):
        return False
    if re.search(r"\bproduct$", match.group(), re.I):
        tail = segment[match.end() :]
        if re.match(r"\s*[,/&+]", tail) and not re.match(rf"\s*[/&+]\s*{_QUALIFIER}\b", tail, re.I):
            return False
    following = suffix.strip(" ()/-:")
    design_hybrid = re.search(
        rf"\bproduct{_SEPARATOR}{_QUALIFIERS}{_ENGINEER}\b", match.group(), re.I
    ) and re.match(r"\s*/\s*(?:product\s+)?designer\b", segment[match.end() :], re.I)
    return not (
        _NON_PRODUCT_TITLE.search(prefix)
        or (not design_hybrid and (_NON_PRODUCT_TITLE.match(following) or _OTHER_TITLE.match(following)))
    )


def classify(text: str) -> dict:
    """Return advertised roles, reasons, and broad product-role candidates."""
    evidence: dict[str, list[str]] = {}
    reasons: dict[str, list[str]] = {}
    candidates: list[str] = []

    def record(role: str, source: str, match: re.Match[str], reason: str) -> None:
        snippet = _excerpt(source, match.start(), match.end())
        if snippet not in evidence.setdefault(role, []):
            evidence[role].append(snippet)
        if reason not in reasons.setdefault(role, []):
            reasons[role].append(reason)
        if role == "product" and snippet not in candidates:
            candidates.append(snippet)

    source_segments = segments(text)
    translated = [source.translate(_PUNCTUATION) for source in source_segments]
    recruiting_engineering = any(
        _ENGINEERING_TITLE.search(segment, cue.end())
        for segment in translated
        for cue in _recruitment_matches(segment)
    )
    hiring_ad = (
        is_hiring_ad(text)
        or recruiting_engineering
        or bool(re.search(r"\b(?:positions?|roles?) available\b", text, re.I))
    )
    job_seeker = is_job_seeker(text)
    active_engineering: bool | None = None
    engineering_opening_seen = False
    for index, (source, segment) in enumerate(zip(source_segments, translated, strict=True)):
        for match in _CANDIDATE.finditer(segment):
            snippet = _excerpt(source, match.start(), match.end())
            if snippet not in candidates:
                candidates.append(snippet)
        for match in _VACANCY_SLUG.finditer(segment):
            snippet = _excerpt(source, match.start(), match.end())
            if snippet not in candidates:
                candidates.append(snippet)
        if job_seeker:
            continue

        opening_titles = [
            (match.start(), engineering)
            for pattern, engineering in ((_ENGINEERING_TITLE, True), (_OTHER_TITLE, False))
            for match in pattern.finditer(segment)
            if _advertised_role(segment, match)
        ]
        if opening_titles:
            active_engineering = sorted(opening_titles)[-1][1]
            engineering_opening_seen |= any(engineering for _, engineering in opening_titles)

        for role, pattern in _ROLE_PATTERNS.items():
            for match in pattern.finditer(segment):
                if role == "product" and not _product_title(segment, match):
                    continue
                if _advertised_role(segment, match):
                    record(role, source, match, "advertised_title")
                elif (
                    role == "product"
                    and hiring_ad
                    and active_engineering is not False
                    and not _reference(segment, match)
                    and _LIST_GAP.fullmatch(
                        segment[: match.start()].removeprefix("Our ").removeprefix("our ")
                    )
                    and _PRODUCT_SUBJECT.match(segment[match.end() :])
                ):
                    record(role, source, match, "product_engineer_description")

        for match in _PRODUCT_ORIENTED.finditer(segment):
            if _product_title(segment, match) and _advertised_role(segment, match):
                record("product", source, match, "product_focused_recruitment")

        if hiring_ad and engineering_opening_seen:
            for match in _PRODUCT_IDENTITY.finditer(segment):
                if not _reference(segment, match):
                    record("product", source, match, "product_engineer_description")
        if hiring_ad and active_engineering is not False:
            for match in _PRODUCT_TEAM.finditer(segment):
                before = segment[: match.start()]
                roles = [
                    role for role in _ENGINEERING_TITLE.finditer(before) if _advertised_role(segment, role)
                ]
                incoming = bool(roles and _INTO_TEAM.search(before[roles[-1].end() :]))
                assigned_team = active_engineering and re.search(
                    r"\byou(?:'ll| will)?[^.!?;|]{0,35}\bjoin\b", before, re.I
                )
                next_segment = translated[index + 1] if index + 1 < len(translated) else ""
                hiring_manager = re.search(r"\bhiring manager for (?:our|the)\s*$", before, re.I) and any(
                    _advertised_role(next_segment, role) for role in _ENGINEERING_TITLE.finditer(next_segment)
                )
                if (incoming or assigned_team or hiring_manager) and (
                    hiring_manager or (not _reference(segment, match) and _product_title(segment, match))
                ):
                    record("product", source, match, "product_engineering_team")

        for match in _PRODUCT_DEFINITION.finditer(segment):
            incoming = bool(_recruitment_matches(segment, end=match.start()))
            assigned = re.search(
                rf"\b(?:you|your|our {_ENGINEER}|each {_ENGINEER}|every {_ENGINEER}|each of us|we(?:'re| are)? (?:hiring|looking))\b",
                segment[: match.start()],
                re.I,
            )
            combined_role = incoming and "engineer in one person" in match.group().lower()
            explicit_engineering = active_engineering is True or bool(
                re.search(rf"\b{_ENGINEER}\b", match.group(), re.I)
            )
            engineering_duty = hiring_ad and explicit_engineering and assigned
            if (
                (combined_role or engineering_duty)
                and not re.search(r"\b(?:market|industry|category)\s+$", segment[: match.start()], re.I)
                and not _PAST_OR_OPTIONAL.search(segment)
                and not _reference(segment, match)
            ):
                record("product", source, match, "combined_product_engineering_role")

        for match in _VACANCY_SLUG.finditer(segment):
            if not inside_url(segment, match.start()) or not _product_title(segment, match):
                continue
            # Slugs count only when attached to this ad's vacancy/application,
            # rather than a company homepage, blog, or someone's past role.
            attached = re.search(
                r"\b(?:apply|job|jobs|careers|positions?|roles?|posting|opening)\b", segment, re.I
            )
            if hiring_ad and attached and not _PAST_OR_OPTIONAL.search(segment):
                record("product", source, match, "vacancy_link")

    return {
        "role_families": [role for role in ROLE_FAMILIES if role in evidence],
        "evidence": evidence,
        "match_reasons": reasons,
        "candidate_evidence": candidates,
    }
