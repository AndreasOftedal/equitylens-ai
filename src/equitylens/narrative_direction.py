import re
from typing import Literal

NarrativeDirection = Literal[
    "increase",
    "decrease",
    "unchanged",
    "mixed",
    "unknown",
]


_OUTCOME_FIRST_CAUSAL_PATTERNS = (
    r"\bprimarily driven by\b",
    r"\bmainly driven by\b",
    r"\bdriven by\b",
    r"\bprimarily due to\b",
    r"\bmainly due to\b",
    r"\bdue to\b",
    r"\bbecause of\b",
    r"\battributable to\b",
    r"\breflecting\b",
    r"\bsupported by\b",
    r"\bpartially offset by\b",
    r"\boffset by\b",
)


_CAUSE_FIRST_CAUSAL_PATTERNS = (
    r"\bled to\b",
    r"\bresulted in\b",
    r"\bgenerated\b",
    r"\bcontributed to\b",
    r"\bcontributed positively to\b",
)


_UNCHANGED_PATTERNS = (
    r"\bremained broadly stable\b",
    r"\bremained stable\b",
    r"\bremained at a similar level\b",
    r"\bremained at similar levels\b",
    r"\bwas broadly stable\b",
    r"\bwere broadly stable\b",
    r"\bwas unchanged\b",
    r"\bwere unchanged\b",
    r"\bunchanged\b",
    r"\bbroadly flat\b",
)


_INCREASE_PATTERNS = (
    r"\bincreased\b",
    r"\bincrease\b",
    r"\bgrew\b",
    r"\bgrowth\b",
    r"\brose\b",
    r"\brisen\b",
    r"\bimproved\b",
    r"\bhigher\b",
)


_DECREASE_PATTERNS = (
    r"\bdecreased\b",
    r"\bdecrease\b",
    r"\bdeclined\b",
    r"\bdecline\b",
    r"\bfell\b",
    r"\bfallen\b",
    r"\breduced\b",
    r"\blower\b",
)


def _normalize_text(
    text: str,
) -> str:
    return " ".join(
        text.lower().split()
    )


def _find_first_pattern(
    text: str,
    patterns: tuple[str, ...],
) -> re.Match[str] | None:
    matches = tuple(
        match
        for pattern in patterns
        if (
            match := re.search(
                pattern,
                text,
                re.IGNORECASE,
            )
        )
    )

    if not matches:
        return None

    return min(
        matches,
        key=lambda match: match.start(),
    )


def _extract_outcome_clause(
    text: str,
) -> str:
    outcome_first = _find_first_pattern(
        text,
        _OUTCOME_FIRST_CAUSAL_PATTERNS,
    )

    cause_first = _find_first_pattern(
        text,
        _CAUSE_FIRST_CAUSAL_PATTERNS,
    )

    if (
        outcome_first is not None
        and (
            cause_first is None
            or outcome_first.start()
            < cause_first.start()
        )
    ):
        return text[
            :outcome_first.start()
        ].strip()

    if cause_first is not None:
        return text[
            cause_first.end():
        ].strip()

    return text


def _contains_any(
    text: str,
    patterns: tuple[str, ...],
) -> bool:
    return any(
        re.search(
            pattern,
            text,
            re.IGNORECASE,
        )
        is not None
        for pattern in patterns
    )


def detect_narrative_direction(
    text: str,
) -> NarrativeDirection:
    """
    Detect the direction of the explained outcome in
    a management narrative sentence.

    Driver direction is deliberately excluded where
    causal language separates the outcome from its
    explanation. For example, "cash flow decreased
    due to higher tax payments" is a decrease, not a
    mixed signal.
    """

    normalized = _normalize_text(
        text
    )

    if not normalized:
        return "unknown"

    outcome_clause = (
        _extract_outcome_clause(
            normalized
        )
    )

    has_unchanged = _contains_any(
        outcome_clause,
        _UNCHANGED_PATTERNS,
    )

    has_increase = _contains_any(
        outcome_clause,
        _INCREASE_PATTERNS,
    )

    has_decrease = _contains_any(
        outcome_clause,
        _DECREASE_PATTERNS,
    )

    directions_detected = sum(
        (
            has_unchanged,
            has_increase,
            has_decrease,
        )
    )

    if directions_detected == 0:
        return "unknown"

    if directions_detected > 1:
        return "mixed"

    if has_unchanged:
        return "unchanged"

    if has_increase:
        return "increase"

    return "decrease"