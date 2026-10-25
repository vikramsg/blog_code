"""Identify employer advertisements without assigning job-category measurements."""

import re

_ENGINEER = r"(?:engineers?|developers?|devs?)"
_TITLE_MODIFIER = (
    r"(?:senior(?:\s+(?:I{1,3}|IV|[1-4]))?|junior|staff|lead|principal|founding|full[ -]time|part[ -]time)"
)
_TITLE_PATTERNS = (
    rf"\b(?:front[ -]?end|client[ -]side|UI)\s+(?:software\s+)?{_ENGINEER}\b",
    rf"\b(?:back[ -]?end|server[ -]side)\s+(?:software\s+)?{_ENGINEER}\b",
    rf"\bfull[ -]?stack\s+(?:(?:software|product)\s+)?{_ENGINEER}\b",
    rf"\b(?:mobile|iOS|Android)\s+(?:software\s+)?{_ENGINEER}\b",
    rf"\b(?:(?:infrastructure|platform|DevOps|site reliability|cloud)\s+{_ENGINEER}|SREs?)\b",
    r"\bdata\s+(?:engineers?|scientists?|analysts?)\b",
    rf"\b(?:AI|ML|machine learning|deep learning)\s+(?:research\s+)?(?:{_ENGINEER}|scientists?|researchers?)\b",
    rf"\b(?:security|cybersecurity|application security)\s+{_ENGINEER}\b",
    rf"\b(?:embedded|firmware|hardware|electrical|mechanical|robotics)\s+(?:software\s+)?{_ENGINEER}\b",
    rf"\b(?:(?:QA|quality assurance|test|testing)\s+{_ENGINEER}|SDETs?)\b",
    rf"\b(?:(?:software|founding|product|web)\s+)?{_ENGINEER}\b",
    r"\bproduct\s+(?:managers?|owners?)\b",
    r"\b(?:(?:product|UX\s*/\s*UI|UI\s*/\s*UX|UX|UI|visual|graphic)\s+)?designers?\b",
    r"\b(?:sales\s+(?:engineers?|representatives?|managers?)|account executives?|marketing\s+(?:managers?|specialists?)|marketers?)\b",
    r"\b(?:(?:customer|technical)\s+support\s+(?:engineers?|specialists?|representatives?)|customer success\s+(?:managers?|engineers?)|operations\s+(?:managers?|specialists?))\b",
)
_TITLES = [re.compile(pattern, re.I) for pattern in _TITLE_PATTERNS]
_ANY_TITLE = re.compile("|".join(f"(?:{pattern})" for pattern in _TITLE_PATTERNS), re.I)
_TITLE_LIST = re.compile(rf"[\s,/&+\-*#•]*(?:(?:and|or|a|an|{_TITLE_MODIFIER})\b[\s,/&+\-*#•]*)*", re.I)
_HIRING = re.compile(
    r"\b(?:we(?:['’]re| are)?\s+(?:hiring|recruiting|seeking)|(?:is|are) hiring|"
    r"hiring|recruiting|seeking|looking for|we (?:need|want)|open (?:roles?|positions?)|job openings?|"
    r"join (?:us|our team)(?: as)?)\b|\b(?:roles?|positions?)\s*:",
    re.I,
)
_NEGATIVE = re.compile(r"\b(?:not(?! (?:only|just)\b)|never|no|without|don't|doesn't|won't|will not)\b", re.I)
_COMPANY_CONTEXT = re.compile(
    r"\b(?:our (?:[\w-]+\s+){0,4}(?:company|product|platform|tool|service|engineers|developers|team)|customers are|users are|"
    r"used by|tools? for|platform for|(?:helps?|enables?|allows?) (?:companies|customers|users|developers|engineers|scientists))\b",
    re.I,
)


def segments(text: str) -> list[str]:
    return [part.strip() for part in re.split(r"\n+|(?<=[.!?])\s+", text) if part.strip()]


def inside_url(segment: str, position: int) -> bool:
    return any(match.start() <= position < match.end() for match in re.finditer(r"https?://\S+", segment))


def negated(segment: str, start: int, end: int) -> bool:
    # A visa restriction in another clause must not cancel an advertised job.
    prefix = re.split(r"[;:|,.]", segment[:start])[-1][-70:]
    return bool(_NEGATIVE.search(prefix + segment[start:end]))


def recruitment_statement(segment: str, match: re.Match[str]) -> bool:
    return not (
        inside_url(segment, match.start())
        or negated(segment, match.start(), match.end())
        or segment.endswith("?")
        or re.search(
            r"\b(?:why|who|wish|wonder|question|discussion|if|stop|advice|feedback)\b",
            segment[: match.start()],
            re.I,
        )
        or re.match(r"\s+(?:advice|feedback|information|tips|is|seems)\b", segment[match.end() :], re.I)
    )


def advertised_title(segment: str, match: re.Match[str]) -> bool:
    if inside_url(segment, match.start()) or negated(segment, match.start(), match.end()):
        return False
    prefix = segment[: match.start()]
    if "|" in prefix and _TITLE_LIST.fullmatch(_ANY_TITLE.sub("", prefix.rsplit("|", 1)[1])):
        return True
    hiring = [match for match in _HIRING.finditer(prefix) if recruitment_statement(segment, match)]
    if hiring and not _COMPANY_CONTEXT.search(prefix[hiring[-1].end() :]):
        previous = [other for pattern in _TITLES for other in pattern.finditer(prefix, hiring[-1].end())]
        if previous and not _TITLE_LIST.fullmatch(prefix[max(other.end() for other in previous) :]):
            return False
        return True
    if re.search(r"\b(?:as (?:a|an)|role of|position of)\s*$", prefix, re.I):
        return True
    title_prefix = re.fullmatch(rf"[\s*#\-•]*(?:(?:{_TITLE_MODIFIER}|a|an)\s+)*", prefix, re.I)
    return bool(title_prefix and re.match(r"\s*(?:$|[|:(\-–—]|at\b)", segment[match.end() :], re.I))


def is_job_seeker(text: str) -> bool:
    beginning = " ".join(segments(text)[:2])
    return bool(
        re.search(
            r"\b(?:seeking work|looking for (?:a (?:new )?job|work|employment)|"
            r"(?:I am|I'm) (?:a |an )?(?:\w+\s+){0,3}(?:engineer|developer).*looking|"
            r"available for (?:hire|work))\b",
            beginning,
            re.I,
        )
    )


def is_hiring_ad(text: str) -> bool:
    if is_job_seeker(text):
        return False
    for segment in segments(text):
        for match in _HIRING.finditer(segment):
            if recruitment_statement(segment, match):
                if re.search(r"\bhiring|recruiting|open|join\b", match.group(), re.I) or any(
                    pattern.search(segment[match.end() :]) for pattern in _TITLES
                ):
                    return True
                if re.search(
                    r"\b(?:someone|people|generalists?|architects?|head of|technologists?|interns?|specialists?|managers?)\b",
                    segment[match.end() :],
                    re.I,
                ):
                    return True
        if any(advertised_title(segment, match) for match in _ANY_TITLE.finditer(segment)):
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
