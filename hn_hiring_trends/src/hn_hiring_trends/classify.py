"""Conservative, inspectable language rules for advertisement-level labels.

Labels describe what an ad explicitly says, not duties assigned to each role in
a multi-role ad. Missing labels mean missing evidence, not absence of a duty.
"""

import re

ROLE_FAMILIES: tuple[str, ...] = (
    "frontend",
    "backend",
    "full_stack",
    "mobile",
    "infrastructure",
    "data",
    "ml_ai",
    "security",
    "embedded_hardware",
    "qa",
    "engineering_unspecified",
    "product_management",
    "design",
    "sales_marketing",
    "support_operations",
)
SIGNALS: tuple[str, ...] = (
    "technical_breadth",
    "product_responsibility",
    "customer_contact",
    "product_decisions",
    "experimentation",
    "outcome_ownership",
    "end_to_end_ownership",
    "founding_engineer",
    "product_engineer_title",
    "ai_product_work",
    "ai_tool_use",
)

_ENGINEERING_FAMILIES = set(ROLE_FAMILIES[:11])
_ENGINEER = r"(?:engineers?|developers?|devs?)"
_TITLE_MODIFIER = (
    r"(?:senior(?:\s+(?:I{1,3}|IV|[1-4]))?|junior|staff|lead|principal|founding|full[ -]time|part[ -]time)"
)
_ROLE_PATTERNS = {
    "frontend": rf"\b(?:front[ -]?end|client[ -]side|UI)\s+(?:software\s+)?{_ENGINEER}\b",
    "backend": rf"\b(?:back[ -]?end|server[ -]side)\s+(?:software\s+)?{_ENGINEER}\b",
    "full_stack": rf"\bfull[ -]?stack\s+(?:(?:software|product)\s+)?{_ENGINEER}\b",
    "mobile": rf"\b(?:mobile|iOS|Android)\s+(?:software\s+)?{_ENGINEER}\b",
    "infrastructure": rf"\b(?:(?:infrastructure|platform|DevOps|site reliability|cloud)\s+{_ENGINEER}|SREs?)\b",
    "data": r"\bdata\s+(?:engineers?|scientists?|analysts?)\b",
    "ml_ai": rf"\b(?:AI|ML|machine learning|deep learning)\s+(?:research\s+)?(?:{_ENGINEER}|scientists?|researchers?)\b",
    "security": rf"\b(?:security|cybersecurity|application security)\s+{_ENGINEER}\b",
    "embedded_hardware": rf"\b(?:embedded|firmware|hardware|electrical|mechanical|robotics)\s+(?:software\s+)?{_ENGINEER}\b",
    "qa": rf"\b(?:(?:QA|quality assurance|test|testing)\s+{_ENGINEER}|SDETs?)\b",
    "engineering_unspecified": rf"\b(?:(?:software|founding|product|web)\s+)?{_ENGINEER}\b",
    "product_management": r"\bproduct\s+(?:managers?|owners?)\b",
    "design": r"\b(?:(?:product|UX\s*/\s*UI|UI\s*/\s*UX|UX|UI|visual|graphic)\s+)?designers?\b",
    "sales_marketing": r"\b(?:sales\s+(?:engineers?|representatives?|managers?)|account executives?|marketing\s+(?:managers?|specialists?)|marketers?)\b",
    "support_operations": r"\b(?:(?:customer|technical)\s+support\s+(?:engineers?|specialists?|representatives?)|customer success\s+(?:managers?|engineers?)|operations\s+(?:managers?|specialists?))\b",
}
_ROLES = {name: re.compile(pattern, re.I) for name, pattern in _ROLE_PATTERNS.items()}
_ANY_ROLE = re.compile("|".join(f"(?:{pattern})" for pattern in _ROLE_PATTERNS.values()), re.I)
_TITLE_LIST = re.compile(
    rf"[\s,/&+\-*#•]*(?:(?:and|or|a|an|{_TITLE_MODIFIER})\b[\s,/&+\-*#•]*)*",
    re.I,
)
_HIRING = re.compile(
    r"\b(?:we(?:['’]re| are)?\s+(?:hiring|recruiting|seeking)|(?:is|are) hiring|"
    r"hiring|recruiting|seeking|looking for|we (?:need|want)|open (?:roles?|positions?)|job openings?|"
    r"join (?:us|our team)(?: as)?)\b|\b(?:roles?|positions?)\s*:",
    re.I,
)
_NEGATIVE = re.compile(r"\b(?:not(?! (?:only|just)\b)|never|no|without|don't|doesn't|won't|will not)\b", re.I)
_APPLICANT_CONTEXT = re.compile(
    r"\b(?:you(?:'ll| will)?|your|candidate|responsibilities|"
    r"duties|the role|this role|we expect|we need|looking for|hiring)\b",
    re.I,
)
_ROLE_DUTY_SUBJECT = re.compile(
    rf"^[\s*\-•]*(?:(?:the|this|a|an)\s+)?(?:{_ANY_ROLE.pattern})\s+"
    r"(?:will|must|is expected to|are expected to|is responsible for|are responsible for)\b",
    re.I,
)
_COMPANY_CONTEXT = re.compile(
    r"\b(?:our (?:[\w-]+\s+){0,4}(?:company|product|platform|tool|service|engineers|developers|team)|customers are|users are|"
    r"used by|tools? for|platform for|(?:helps?|enables?|allows?) (?:companies|customers|users|developers|engineers|scientists))\b",
    re.I,
)


def _segments(text: str) -> list[str]:
    return [part.strip() for part in re.split(r"\n+|(?<=[.!?])\s+", text) if part.strip()]


def _negated(segment: str, start: int, end: int) -> bool:
    # Negation is local to a clause; a visa restriction must not cancel a role.
    prefix = re.split(r"[;:|,.]", segment[:start])[-1][-70:]
    return bool(_NEGATIVE.search(prefix + segment[start:end]))


def _role_context(segment: str, match: re.Match[str]) -> bool:
    if _inside_url(segment, match.start()) or _negated(segment, match.start(), match.end()):
        return False
    prefix = segment[: match.start()]
    if "|" in prefix and _TITLE_LIST.fullmatch(_ANY_ROLE.sub("", prefix.rsplit("|", 1)[1])):
        return True
    hiring = [match for match in _HIRING.finditer(prefix) if _recruitment_statement(segment, match)]
    if hiring and not _COMPANY_CONTEXT.search(prefix[hiring[-1].end() :]):
        previous_roles = [
            other for pattern in _ROLES.values() for other in pattern.finditer(prefix, hiring[-1].end())
        ]
        if previous_roles:
            gap = prefix[max(other.end() for other in previous_roles) :]
            if not _TITLE_LIST.fullmatch(gap):
                return False
        return True
    if re.search(r"\b(?:as (?:a|an)|role of|position of)\s*$", prefix, re.I):
        return True
    title_prefix = re.fullmatch(rf"[\s*#\-•]*(?:(?:{_TITLE_MODIFIER}|a|an)\s+)*", prefix, re.I)
    return bool(title_prefix and re.match(r"\s*(?:$|[|:(\-–—]|at\b)", segment[match.end() :], re.I))


def _excerpt(segment: str, start: int, end: int) -> str:
    # Slices, rather than rewritten snippets, can be found verbatim in the source.
    left = max(0, start - 45)
    right = min(len(segment), max(end, start + 130))
    return segment[left:right].strip()


def _inside_url(segment: str, position: int) -> bool:
    return any(match.start() <= position < match.end() for match in re.finditer(r"https?://\S+", segment))


def _recruitment_statement(segment: str, match: re.Match[str]) -> bool:
    return not (
        _inside_url(segment, match.start())
        or _negated(segment, match.start(), match.end())
        or segment.endswith("?")
        or re.search(
            r"\b(?:why|who|wish|wonder|question|discussion|if|stop|advice|feedback)\b",
            segment[: match.start()],
            re.I,
        )
        or re.match(r"\s+(?:advice|feedback|information|tips|is|seems)\b", segment[match.end() :], re.I)
    )


def is_hiring_ad(text: str) -> bool:
    """Retain explicit recruitment and conventional headers, not job seekers/replies."""
    segments = _segments(text)
    if not segments:
        return False
    beginning = " ".join(segments[:2])
    if re.search(
        r"\b(?:seeking work|looking for (?:a (?:new )?job|work|employment)|"
        r"(?:I am|I'm) (?:a |an )?(?:\w+\s+){0,3}(?:engineer|developer).*looking|"
        r"available for (?:hire|work))\b",
        beginning,
        re.I,
    ):
        return False
    for segment in segments:
        for match in _HIRING.finditer(segment):
            if _recruitment_statement(segment, match):
                if re.search(r"\bhiring|recruiting|open|join\b", match.group(), re.I) or any(
                    pattern.search(segment[match.end() :]) for pattern in _ROLES.values()
                ):
                    return True
                if re.search(
                    r"\b(?:someone|people|generalists?|architects?|head of|technologists?|interns?|specialists?|managers?)\b",
                    segment[match.end() :],
                    re.I,
                ):
                    return True
        if any(_role_context(segment, match) for match in _ANY_ROLE.finditer(segment)):
            return True
        if segment.count("|") >= 2 and re.search(
            r"\b(?:remote|onsite|on-site|hybrid|full[ -]time|part[ -]time|contract|engineers?|developers?)\b",
            segment.split("|", 1)[1],
            re.I,
        ):
            return True
        if re.search(
            r"\b(?:apply (?:at|via|here|now|to)|send (?:your |a )?(?:CV|resume)|careers\.)", segment, re.I
        ):
            return True
    return False


_FRONT = r"(?:front[ -]?end|client[ -]side)"
_BACK = r"(?:back[ -]?end|server[ -]side)"
_AI = r"(?:AI|ML|LLMs?|generative AI|machine learning|language models?)"
_AI_SYSTEM = (
    rf"(?:{_AI}(?:[-](?:powered|based|driven|infused|native))?\s+(?:[a-z][a-z-]*\s+){{0,2}}"
    r"(?:systems?|products?|applications?|apps?|models?|pipelines?|workflows?|agents?|tools?|platforms?|engines?|features?)|LLMs?|language models?)"
)
_BUILD = r"(?:build(?:ing)?|develop(?:ing)?|own(?:ing)?|work(?:ing)? on)"
_AI_TOOL_ACTION = (
    r"(?:us(?:e|ing)|leverag(?:e|ing)|adopt(?:ing)?|experience with|comfortable with|comfort with)"
)
_CODING_ASSISTANT = r"(?:GitHub Copilot|Copilot|Cursor|Claude Code|Codex|ChatGPT)"
_AI_SYSTEM_VERB = r"(?:build(?:ing)?|develop(?:ing)?|ship(?:ping)?|design(?:ing)?|implement(?:ing)?|integrat(?:e|ing)|train(?:ing)?|fine[ -]tun(?:e|ing)|evaluat(?:e|ing)|deploy(?:ing)?)"
_SIGNAL_PATTERNS = {
    "customer_contact": r"\b(?:talk(?:ing)?|speak(?:ing)?|interact(?:ing)?|meet(?:ing)?|engag(?:e|ing)|collaborat(?:e|ing)|work(?:ing)?)\s+(?:directly\s+|closely\s+|regularly\s+)?(?:to|with)\s+(?:our\s+|the\s+)?(?:customers|users)\b|\b(?:customer|user)\s+(?:interviews|research)\b",
    "product_decisions": r"\b(?:mak(?:e|ing)|shap(?:e|ing)|driv(?:e|ing)|defin(?:e|ing)|influenc(?:e|ing)|own(?:ing)?|decid(?:e|ing)|prioriti[sz](?:e|ing))\s+(?:our\s+|the\s+)?(?:product\s+(?:roadmap|direction|strategy|decisions|priorities|discovery)|what (?:we |to )?build)\b|\b(?:responsibilities|duties|role)\s+includes?\s+product discovery\b",
    "experimentation": r"\b(?:run(?:ning)?|design(?:ing)?|conduct(?:ing)?|own(?:ing)?|driv(?:e|ing))\s+(?:(?:product|growth|user|customer)\s+experiments|A/B tests|user tests)\b|\b(?:test(?:ing)?|validat(?:e|ing))\s+(?:product|customer|user|business|growth)\s+(?:hypotheses|assumptions)\b",
    "outcome_ownership": r"\b(?:own(?:ing)?|driv(?:e|ing)|responsible for|accountable for|measured (?:by|on)|take ownership of)\s+(?:product\s+|business\s+|customer\s+)?(?:outcomes|impact|metrics|retention|conversion|revenue|activation|engagement)\b",
    "end_to_end_ownership": r"\b(?:own|deliver|build|responsible for)(?:ing)?\b.{0,65}\bend[ -]to[ -]end\b|\bend[ -]to[ -]end\s+ownership\b|\b(?:own|take)\b.{0,35}\bfrom\s+(?:idea|concept|design)\b.{0,65}\b(?:production|deployment|launch)\b",
    "ai_product_work": rf"\b{_AI_SYSTEM_VERB}(?:\s*(?:,\s*(?:and\s+)?|and\s+){_AI_SYSTEM_VERB}){{0,3}}\s+(?:(?:a|an|the|our|new|production|scalable|automated|advanced|modern|large|self-service)\s+){{0,3}}{_AI_SYSTEM}\b",
    "ai_tool_use": (
        rf"\b{_AI_TOOL_ACTION}\s+(?:tools (?:like|such as)\s+|AI (?:coding )?(?:tools|assistants)\s*(?:(?:like|such as)\s+|\(\s*)|(?:an? |the )?){_CODING_ASSISTANT}\b|"
        rf"\b(?:{_AI_TOOL_ACTION}|with)\s+AI(?:[- ]assisted|[- ]powered)?\s+(?:coding|development|programming)(?:\s+(?:assistants?|tools))?\b|"
        rf"\b{_AI_TOOL_ACTION}\s+(?:(?:modern|generative)\s+)?AI\s+(?:tools|assistants)\s+(?:to|for)\s+(?:ship|develop|development|build|coding|programming|write code|code)\b|"
        r"\b(?:use|using|leverage)\s+(?:LLMs?|AI)\s+(?:to (?:write code|code|program)|for (?:coding|programming))\b|"
        r"\bAI-assisted\s+(?:coding|development|programming)\b(?=\s*(?:\(|is\b|has\b|will\b|[.,;:]|$))"
    ),
}
_SIGNAL_RULES = {name: re.compile(pattern, re.I) for name, pattern in _SIGNAL_PATTERNS.items()}
_FRONT_DUTY = rf"{_FRONT}(?!\s+(?:software\s+)?{_ENGINEER}\b)"
_BACK_DUTY = rf"{_BACK}(?!\s+(?:software\s+)?{_ENGINEER}\b)"
_BREADTH = re.compile(
    rf"\b{_BUILD}\b[^;|.]{{0,45}}\b(?:{_FRONT_DUTY}[^;|.]{{0,45}}{_BACK_DUTY}|"
    rf"{_BACK_DUTY}[^;|.]{{0,45}}{_FRONT_DUTY})\b|"
    rf"\b(?:across|spanning|from)\s+(?:the\s+)?(?:{_FRONT_DUTY}[^;|.]{{0,45}}{_BACK_DUTY}|"
    rf"{_BACK_DUTY}[^;|.]{{0,45}}{_FRONT_DUTY})\b",
    re.I,
)
_DUTY_ROLES = {
    "frontend": re.compile(rf"\b{_BUILD}\s+(?:our\s+|the\s+)?{_FRONT}\b", re.I),
    "backend": re.compile(rf"\b{_BUILD}\s+(?:our\s+|the\s+)?{_BACK}\b", re.I),
}


def _last_advertised_role(segment: str, start: int, end: int) -> re.Match[str] | None:
    roles = list(_ANY_ROLE.finditer(segment, start, end))
    return roles[-1] if roles and _role_context(segment, roles[-1]) else None


def _duty_context(segment: str, match: re.Match[str]) -> bool:
    if _inside_url(segment, match.start()) or _negated(segment, match.start(), match.end()):
        return False
    full_prefix = segment[: match.start()]
    clause_start = max(full_prefix.rfind("|"), full_prefix.rfind(";")) + 1
    relative_clauses = list(re.finditer(r"\b(?:who|that|which)\b", full_prefix[clause_start:], re.I))
    relative_duty = False
    if relative_clauses:
        relative = relative_clauses[-1]
        antecedent = _last_advertised_role(segment, clause_start, clause_start + relative.start())
        clause_start += relative.end()
        relative_duty = bool(
            antecedent
            and re.match(
                r"\s*(?:will|must|is expected to|are expected to)\b", full_prefix[clause_start:], re.I
            )
        )
        if not relative_duty and not _APPLICANT_CONTEXT.search(full_prefix[clause_start:]):
            return False
    prefix = full_prefix[clause_start:]
    # Headers and references to coworkers must not authorize a different
    # clause's work. Hypothetical explanations are not assigned duties.
    if re.match(r"\s*if\b", prefix, re.I) and not re.search(
        r"\byou(?:['’]ll| will)\b|\byour (?:role|responsibilities|duties)\b", prefix, re.I
    ):
        return False
    company = list(_COMPANY_CONTEXT.finditer(prefix))
    if company and not _APPLICANT_CONTEXT.search(prefix, company[-1].end()):
        return False
    role = _last_advertised_role(segment, clause_start, match.start())
    title_duty = bool(role and re.fullmatch(r"[\s:–—-]*", full_prefix[role.end() :]))
    return bool(
        relative_duty
        or _APPLICANT_CONTEXT.search(prefix)
        or _ROLE_DUTY_SUBJECT.search(prefix)
        or title_duty
        or re.fullmatch(r"[\s*\-•]*", prefix)
        or re.match(
            r"[\s*\-•]*(?:experience with|comfortable with|proficient in|proficiency in|must|ability to)\b",
            prefix,
            re.I,
        )
    )


def classify(text: str) -> dict:
    """Return overlapping families/signals with exact evidence for positive labels."""
    evidence: dict[str, list[str]] = {}

    def record(name: str, segment: str, match: re.Match[str]) -> None:
        excerpt = _excerpt(segment, match.start(), match.end())
        examples = evidence.setdefault(name, [])
        if excerpt not in examples and len(examples) < 3:
            examples.append(excerpt)

    segments = _segments(text)
    for segment in segments:
        specific_matches = [
            match
            for name, pattern in _ROLES.items()
            if name != "engineering_unspecified"
            for match in pattern.finditer(segment)
        ]
        for family, pattern in _ROLES.items():
            for match in pattern.finditer(segment):
                if family == "engineering_unspecified" and any(
                    other.start() <= match.start() < other.end() for other in specific_matches
                ):
                    continue
                if _role_context(segment, match):
                    record(family, segment, match)
                    if family == "full_stack":
                        record("technical_breadth", segment, match)
                    if (
                        family in _ENGINEERING_FAMILIES
                        and re.search(rf"\b{_ENGINEER}\b", match.group(), re.I)
                        and (
                            re.search(r"\bfounding engineers?\b", match.group(), re.I)
                            or re.search(r"\bfounding\s+$", segment[: match.start()], re.I)
                        )
                    ):
                        record("founding_engineer", segment, match)
                    if re.search(r"\bproduct engineers?\b", match.group(), re.I):
                        record("product_engineer_title", segment, match)
        for family, pattern in _DUTY_ROLES.items():
            for match in pattern.finditer(segment):
                if _duty_context(segment, match):
                    record(family, segment, match)
        for match in _BREADTH.finditer(segment):
            # Do not join the duties of separately named frontend/backend roles.
            separate_roles = _ROLES["frontend"].search(match.group()) or _ROLES["backend"].search(
                match.group()
            )
            if not separate_roles and _duty_context(segment, match):
                record("technical_breadth", segment, match)
                record("frontend", segment, match)
                record("backend", segment, match)
        for signal, pattern in _SIGNAL_RULES.items():
            for match in pattern.finditer(segment):
                if signal == "outcome_ownership" and re.search(
                    r"\b(?:that|which)\s*$", segment[: match.start()], re.I
                ):
                    continue
                if _duty_context(segment, match):
                    record(signal, segment, match)

    product_evidence = [
        excerpt
        for name in ("customer_contact", "product_decisions", "experimentation", "outcome_ownership")
        for excerpt in evidence.get(name, [])
    ]
    if product_evidence:
        evidence["product_responsibility"] = list(dict.fromkeys(product_evidence))[:3]
    families = [name for name in ROLE_FAMILIES if name in evidence]
    return {
        "role_families": families,
        "engineering_ad": bool(_ENGINEERING_FAMILIES.intersection(families)),
        "signals": {name: name in evidence for name in SIGNALS},
        "evidence": evidence,
    }
