import re
from dataclasses import dataclass
from typing import Literal

from equitylens.evidence_alignment import detect_evidence_comparison_types
from equitylens.evidence_sentences import EvidenceSentence
from equitylens.periods import ComparisonType

EvidenceGateStatus = Literal[
    "direct_explanation",
    "aligned_context",
    "query_mismatch",
    "period_mismatch",
    "period_ambiguous",
    "period_unknown",
    "non_narrative",
    "unsupported_comparison",
]


_OUTCOME_FIRST_CAUSAL_PHRASES = (
    "driven by",
    "primarily driven by",
    "mainly driven by",
    "supported by",
    "due to",
    "mainly due to",
    "primarily due to",
    "because of",
    "attributable to",
    "reflecting",
    "offset by",
    "partially offset",
    "caused by",
)

_CAUSE_FIRST_CAUSAL_PHRASES = (
    "led to",
    "resulted in",
    "generated",
    "contributed to",
    "contributed positively",
)

_CAUSAL_PHRASES = (
    *_OUTCOME_FIRST_CAUSAL_PHRASES,
    *_CAUSE_FIRST_CAUSAL_PHRASES,
)

_QUERY_PATTERN = re.compile(
    r"^\s*what\s+drove\s+(.+?)\??\s*$",
    re.IGNORECASE,
)

_NORMALIZE_PATTERN = re.compile(
    r"[^a-z0-9]+"
)


@dataclass(frozen=True)
class EvidenceGateResult:
    sentence_id: str
    status: EvidenceGateStatus
    query_subject: str
    detected_comparison_types: frozenset[ComparisonType]
    metric_match: bool
    causal_signal: bool
    usable_as_direct_explanation: bool
    reason: str


def _normalize_text(
    text: str,
) -> str:
    normalized = _NORMALIZE_PATTERN.sub(
        " ",
        text.lower(),
    )

    return " ".join(
        normalized.split()
    )


def extract_query_subject(
    query: str,
) -> str:
    if not query.strip():
        raise ValueError(
            "query cannot be empty."
        )

    match = _QUERY_PATTERN.match(
        query
    )

    subject = (
        match.group(1)
        if match
        else query
    )

    normalized_subject = _normalize_text(
        subject
    )

    if not normalized_subject:
        raise ValueError(
            "query subject cannot be empty."
        )

    return normalized_subject


def _subject_positions(
    query_subject: str,
    normalized_sentence: str,
) -> tuple[tuple[int, int], ...]:
    pattern = re.compile(
        rf"\b{re.escape(query_subject)}\b"
    )

    return tuple(
        (
            match.start(),
            match.end(),
        )
        for match in pattern.finditer(
            normalized_sentence
        )
    )


def _phrase_positions(
    phrase: str,
    normalized_sentence: str,
) -> tuple[int, ...]:
    normalized_phrase = _normalize_text(
        phrase
    )

    return tuple(
        match.start()
        for match in re.finditer(
            re.escape(normalized_phrase),
            normalized_sentence,
        )
    )


def _metric_is_explained_outcome(
    query_subject: str,
    sentence: EvidenceSentence,
    causal_signal: bool,
) -> bool:
    """
    Determine whether the queried metric is the outcome being discussed,
    rather than merely appearing inside the explanation of another metric.

    Examples:

    "Production increased ... due to new fields."
        -> production is the outcome.

    "Higher prices generated cash flow ..."
        -> cash flow is the outcome.

    "Gas sales decreased ... due to higher production."
        -> production is a driver, not the outcome.
    """

    normalized_sentence = _normalize_text(
        sentence.text
    )

    subject_positions = _subject_positions(
        query_subject=query_subject,
        normalized_sentence=normalized_sentence,
    )

    if not subject_positions:
        return False

    if not causal_signal:
        return True

    outcome_first_positions = tuple(
        position
        for phrase in _OUTCOME_FIRST_CAUSAL_PHRASES
        for position in _phrase_positions(
            phrase=phrase,
            normalized_sentence=normalized_sentence,
        )
    )

    cause_first_positions = tuple(
        position
        for phrase in _CAUSE_FIRST_CAUSAL_PHRASES
        for position in _phrase_positions(
            phrase=phrase,
            normalized_sentence=normalized_sentence,
        )
    )

    for subject_start, subject_end in subject_positions:
        if any(
            position >= subject_end
            for position in outcome_first_positions
        ):
            return True

        if any(
            position < subject_start
            for position in cause_first_positions
        ):
            return True

    raw_lower = sentence.text.lower()

    for phrase in _OUTCOME_FIRST_CAUSAL_PHRASES:
        phrase_position = raw_lower.find(
            phrase
        )

        if not (
            0
            <= phrase_position
            <= 20
        ):
            continue

        comma_position = raw_lower.find(
            ",",
            phrase_position,
        )

        if comma_position == -1:
            continue

        after_prefix = _normalize_text(
            sentence.text[
                comma_position + 1:
            ]
        )

        if _subject_positions(
            query_subject=query_subject,
            normalized_sentence=after_prefix,
        ):
            return True

    return False


def _contains_causal_signal(
    sentence: EvidenceSentence,
) -> bool:
    normalized_sentence = sentence.text.lower()

    return any(
        phrase in normalized_sentence
        for phrase in _CAUSAL_PHRASES
    )


def _numeric_token_ratio(
    text: str,
) -> float:
    tokens = text.split()

    if not tokens:
        return 0.0

    numeric_tokens = sum(
        any(
            character.isdigit()
            for character in token
        )
        for token in tokens
    )

    return numeric_tokens / len(tokens)


def _looks_non_narrative(
    sentence: EvidenceSentence,
) -> bool:
    numeric_ratio = _numeric_token_ratio(
        sentence.text
    )

    return (
        numeric_ratio >= 0.30
        or (
            len(sentence.text) >= 500
            and numeric_ratio >= 0.12
        )
    )


def assess_sentence_evidence(
    query: str,
    expected_comparison_type: ComparisonType,
    sentence: EvidenceSentence,
) -> EvidenceGateResult:
    """
    Determine whether a sentence can support a direct explanation
    of a specific financial change.

    Direct explanatory evidence must:
    1. discuss the queried metric as the outcome being explained,
    2. use the same comparison basis as the financial calculation,
    3. contain explanatory or causal language,
    4. resemble narrative rather than table content.
    """

    query_subject = extract_query_subject(
        query
    )

    detected = detect_evidence_comparison_types(
        sentence.text
    )

    causal_signal = _contains_causal_signal(
        sentence
    )

    metric_match = _metric_is_explained_outcome(
        query_subject=query_subject,
        sentence=sentence,
        causal_signal=causal_signal,
    )

    if expected_comparison_type == "other":
        return EvidenceGateResult(
            sentence_id=sentence.sentence_id,
            status="unsupported_comparison",
            query_subject=query_subject,
            detected_comparison_types=detected,
            metric_match=metric_match,
            causal_signal=causal_signal,
            usable_as_direct_explanation=False,
            reason=(
                "The financial comparison is not "
                "classified as QoQ or YoY."
            ),
        )

    if not metric_match:
        return EvidenceGateResult(
            sentence_id=sentence.sentence_id,
            status="query_mismatch",
            query_subject=query_subject,
            detected_comparison_types=detected,
            metric_match=False,
            causal_signal=causal_signal,
            usable_as_direct_explanation=False,
            reason=(
                "The queried metric is not the "
                "outcome being explained."
            ),
        )

    if _looks_non_narrative(
        sentence
    ):
        return EvidenceGateResult(
            sentence_id=sentence.sentence_id,
            status="non_narrative",
            query_subject=query_subject,
            detected_comparison_types=detected,
            metric_match=True,
            causal_signal=causal_signal,
            usable_as_direct_explanation=False,
            reason=(
                "The sentence appears to contain "
                "table-like rather than narrative evidence."
            ),
        )

    if not detected:
        return EvidenceGateResult(
            sentence_id=sentence.sentence_id,
            status="period_unknown",
            query_subject=query_subject,
            detected_comparison_types=detected,
            metric_match=True,
            causal_signal=causal_signal,
            usable_as_direct_explanation=False,
            reason=(
                "No explicit QoQ or YoY comparison "
                "basis was detected."
            ),
        )

    if len(detected) > 1:
        return EvidenceGateResult(
            sentence_id=sentence.sentence_id,
            status="period_ambiguous",
            query_subject=query_subject,
            detected_comparison_types=detected,
            metric_match=True,
            causal_signal=causal_signal,
            usable_as_direct_explanation=False,
            reason=(
                "The sentence contains multiple "
                "comparison bases."
            ),
        )

    detected_type = next(
        iter(detected)
    )

    if (
        detected_type
        != expected_comparison_type
    ):
        return EvidenceGateResult(
            sentence_id=sentence.sentence_id,
            status="period_mismatch",
            query_subject=query_subject,
            detected_comparison_types=detected,
            metric_match=True,
            causal_signal=causal_signal,
            usable_as_direct_explanation=False,
            reason=(
                "The sentence comparison basis does "
                "not match the financial comparison."
            ),
        )

    if not causal_signal:
        return EvidenceGateResult(
            sentence_id=sentence.sentence_id,
            status="aligned_context",
            query_subject=query_subject,
            detected_comparison_types=detected,
            metric_match=True,
            causal_signal=False,
            usable_as_direct_explanation=False,
            reason=(
                "The sentence matches the metric and "
                "comparison basis but does not contain "
                "an explanatory causal signal."
            ),
        )

    return EvidenceGateResult(
        sentence_id=sentence.sentence_id,
        status="direct_explanation",
        query_subject=query_subject,
        detected_comparison_types=detected,
        metric_match=True,
        causal_signal=True,
        usable_as_direct_explanation=True,
        reason=(
            "The queried metric is the explained outcome, "
            "the comparison basis matches and the sentence "
            "contains causal language."
        ),
    )