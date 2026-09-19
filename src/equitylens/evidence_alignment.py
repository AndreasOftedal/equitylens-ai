import re
from dataclasses import dataclass
from typing import Literal

from equitylens.periods import (
    ComparisonType,
    ReportingPeriod,
    classify_period_comparison,
)
from equitylens.text_chunks import TextChunk

EvidenceAlignmentStatus = Literal[
    "aligned",
    "mismatched",
    "ambiguous",
    "unknown",
]


_QOQ_PATTERNS = (
    re.compile(
        r"\bprevious quarter\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\bprior quarter\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\bpreceding quarter\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\bquarter[- ]on[- ]quarter\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\bqoq\b",
        re.IGNORECASE,
    ),
)

_YOY_PATTERNS = (
    re.compile(
        r"\bsame quarter last year\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\bsame period last year\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\bsame periods last year\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\bcorresponding quarter last year\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\bcorresponding period last year\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\bcorresponding periods last year\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\bcorresponding period(?:s)? in \d{4}\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\byear[- ]on[- ]year\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\byoy\b",
        re.IGNORECASE,
    ),
)

_QUARTER_LABEL_PATTERN = re.compile(
    r"\bQ([1-4])\s+(\d{4})\b",
    re.IGNORECASE,
)

_QUARTER_WORD_PATTERN = re.compile(
    (
        r"\b(first|second|third|fourth) "
        r"quarter(?: of)?\s+(\d{4})\b"
    ),
    re.IGNORECASE,
)

_QUARTER_WORD_TO_NUMBER = {
    "first": 1,
    "second": 2,
    "third": 3,
    "fourth": 4,
}


@dataclass(frozen=True)
class EvidencePeriodAlignment:
    chunk_id: str
    expected_comparison_type: ComparisonType
    detected_comparison_types: frozenset[ComparisonType]
    status: EvidenceAlignmentStatus
    reason: str


def _extract_quarter_periods(
    text: str,
) -> tuple[ReportingPeriod, ...]:
    periods: list[ReportingPeriod] = []

    for match in _QUARTER_LABEL_PATTERN.finditer(
        text
    ):
        periods.append(
            ReportingPeriod(
                year=int(match.group(2)),
                period_type="quarter",
                period_number=int(match.group(1)),
            )
        )

    for match in _QUARTER_WORD_PATTERN.finditer(
        text
    ):
        periods.append(
            ReportingPeriod(
                year=int(match.group(2)),
                period_type="quarter",
                period_number=(
                    _QUARTER_WORD_TO_NUMBER[
                        match.group(1).lower()
                    ]
                ),
            )
        )

    unique_periods: list[ReportingPeriod] = []

    for period in periods:
        if period not in unique_periods:
            unique_periods.append(period)

    return tuple(unique_periods)


def detect_evidence_comparison_types(
    text: str,
) -> frozenset[ComparisonType]:
    """
    Detect explicit QoQ and YoY comparison signals in narrative text.

    Both comparison types may be returned when a chunk discusses
    multiple comparison bases. No inference is made when the text
    does not contain sufficiently explicit evidence.
    """

    detected: set[ComparisonType] = set()

    if any(
        pattern.search(text)
        for pattern in _QOQ_PATTERNS
    ):
        detected.add("qoq")

    if any(
        pattern.search(text)
        for pattern in _YOY_PATTERNS
    ):
        detected.add("yoy")

    periods = _extract_quarter_periods(
        text
    )

    for index, first_period in enumerate(
        periods
    ):
        for second_period in periods[
            index + 1:
        ]:
            comparison_type = (
                classify_period_comparison(
                    first_period,
                    second_period,
                )
            )

            if comparison_type in {
                "qoq",
                "yoy",
            }:
                detected.add(
                    comparison_type
                )

            reverse_comparison_type = (
                classify_period_comparison(
                    second_period,
                    first_period,
                )
            )

            if reverse_comparison_type in {
                "qoq",
                "yoy",
            }:
                detected.add(
                    reverse_comparison_type
                )

    return frozenset(
        detected
    )


def assess_period_alignment(
    expected_comparison_type: ComparisonType,
    chunk: TextChunk,
) -> EvidencePeriodAlignment:
    """
    Compare the deterministic financial comparison basis with the
    comparison basis explicitly supported by narrative evidence.
    """

    detected = (
        detect_evidence_comparison_types(
            chunk.text
        )
    )

    if expected_comparison_type == "other":
        return EvidencePeriodAlignment(
            chunk_id=chunk.chunk_id,
            expected_comparison_type=(
                expected_comparison_type
            ),
            detected_comparison_types=detected,
            status="unknown",
            reason=(
                "The financial comparison is not "
                "classified as QoQ or YoY."
            ),
        )

    if not detected:
        return EvidencePeriodAlignment(
            chunk_id=chunk.chunk_id,
            expected_comparison_type=(
                expected_comparison_type
            ),
            detected_comparison_types=detected,
            status="unknown",
            reason=(
                "No explicit QoQ or YoY comparison "
                "signal was detected in the evidence."
            ),
        )

    if len(detected) > 1:
        return EvidencePeriodAlignment(
            chunk_id=chunk.chunk_id,
            expected_comparison_type=(
                expected_comparison_type
            ),
            detected_comparison_types=detected,
            status="ambiguous",
            reason=(
                "The evidence contains multiple "
                "comparison bases."
            ),
        )

    detected_type = next(
        iter(detected)
    )

    if detected_type == expected_comparison_type:
        return EvidencePeriodAlignment(
            chunk_id=chunk.chunk_id,
            expected_comparison_type=(
                expected_comparison_type
            ),
            detected_comparison_types=detected,
            status="aligned",
            reason=(
                "The evidence comparison basis "
                "matches the financial comparison."
            ),
        )

    return EvidencePeriodAlignment(
        chunk_id=chunk.chunk_id,
        expected_comparison_type=(
            expected_comparison_type
        ),
        detected_comparison_types=detected,
        status="mismatched",
        reason=(
            "The evidence comparison basis does "
            "not match the financial comparison."
        ),
    )