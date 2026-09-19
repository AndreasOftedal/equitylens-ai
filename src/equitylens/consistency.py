from dataclasses import dataclass
from typing import Literal

from equitylens.evidence_assessment import (
    EvidenceAssessment,
)
from equitylens.narrative_direction import (
    NarrativeDirection,
    detect_narrative_direction,
)
from equitylens.periods import ComparisonType

ConsistencyStatus = Literal[
    "consistent",
    "potential_tension",
    "insufficient_evidence",
    "not_comparable",
]


FinancialDirection = Literal[
    "increase",
    "decrease",
    "unchanged",
]


@dataclass(frozen=True)
class ConsistencyAssessment:
    metric_id: str
    status: ConsistencyStatus
    financial_direction: FinancialDirection
    comparison_type: ComparisonType
    narrative_directions: tuple[
        NarrativeDirection,
        ...
    ]
    reason: str


def _classify_financial_direction(
    absolute_change,
) -> FinancialDirection:
    if absolute_change > 0:
        return "increase"

    if absolute_change < 0:
        return "decrease"

    return "unchanged"


def _direct_narrative_directions(
    assessment: EvidenceAssessment,
) -> tuple[NarrativeDirection, ...]:
    return tuple(
        detect_narrative_direction(
            evidence.sentence.text
        )
        for evidence
        in assessment.direct_explanations
    )


def assess_consistency(
    metric_id: str,
    absolute_change,
    comparison_type: ComparisonType,
    evidence_assessment: (
        EvidenceAssessment | None
    ),
) -> ConsistencyAssessment:
    """
    Compare deterministic financial direction with
    validated direct management narrative evidence.

    Aligned context is deliberately insufficient for
    a consistency conclusion because it does not
    represent a validated explanation of the metric.
    """

    if not metric_id.strip():
        raise ValueError(
            "metric_id cannot be empty."
        )

    financial_direction = (
        _classify_financial_direction(
            absolute_change
        )
    )

    if comparison_type not in {
        "qoq",
        "yoy",
    }:
        return ConsistencyAssessment(
            metric_id=metric_id,
            status="not_comparable",
            financial_direction=(
                financial_direction
            ),
            comparison_type=comparison_type,
            narrative_directions=(),
            reason=(
                "Consistency assessment is only "
                "supported for QoQ and YoY "
                "comparisons."
            ),
        )

    if evidence_assessment is None:
        return ConsistencyAssessment(
            metric_id=metric_id,
            status="insufficient_evidence",
            financial_direction=(
                financial_direction
            ),
            comparison_type=comparison_type,
            narrative_directions=(),
            reason=(
                "No validated narrative evidence "
                "assessment is available."
            ),
        )

    if (
        evidence_assessment
        .expected_comparison_type
        != comparison_type
    ):
        return ConsistencyAssessment(
            metric_id=metric_id,
            status="not_comparable",
            financial_direction=(
                financial_direction
            ),
            comparison_type=comparison_type,
            narrative_directions=(),
            reason=(
                "Narrative evidence uses a "
                "different comparison basis."
            ),
        )

    if (
        evidence_assessment.availability
        != "direct_explanation"
    ):
        return ConsistencyAssessment(
            metric_id=metric_id,
            status="insufficient_evidence",
            financial_direction=(
                financial_direction
            ),
            comparison_type=comparison_type,
            narrative_directions=(),
            reason=(
                "No validated direct management "
                "explanation is available."
            ),
        )

    narrative_directions = (
        _direct_narrative_directions(
            evidence_assessment
        )
    )

    usable_directions = {
        direction
        for direction
        in narrative_directions
        if direction
        in {
            "increase",
            "decrease",
            "unchanged",
        }
    }

    if not usable_directions:
        return ConsistencyAssessment(
            metric_id=metric_id,
            status="insufficient_evidence",
            financial_direction=(
                financial_direction
            ),
            comparison_type=comparison_type,
            narrative_directions=(
                narrative_directions
            ),
            reason=(
                "Direct evidence does not contain "
                "an unambiguous outcome direction."
            ),
        )

    if len(
        usable_directions
    ) > 1:
        return ConsistencyAssessment(
            metric_id=metric_id,
            status="insufficient_evidence",
            financial_direction=(
                financial_direction
            ),
            comparison_type=comparison_type,
            narrative_directions=(
                narrative_directions
            ),
            reason=(
                "Direct management evidence contains "
                "conflicting outcome directions."
            ),
        )

    narrative_direction = next(
        iter(
            usable_directions
        )
    )

    if (
        narrative_direction
        == financial_direction
    ):
        return ConsistencyAssessment(
            metric_id=metric_id,
            status="consistent",
            financial_direction=(
                financial_direction
            ),
            comparison_type=comparison_type,
            narrative_directions=(
                narrative_directions
            ),
            reason=(
                "Direct management narrative and "
                "the deterministic financial change "
                "have the same direction."
            ),
        )

    return ConsistencyAssessment(
        metric_id=metric_id,
        status="potential_tension",
        financial_direction=(
            financial_direction
        ),
        comparison_type=comparison_type,
        narrative_directions=(
            narrative_directions
        ),
        reason=(
            "Direct management narrative and the "
            "deterministic financial change have "
            "opposing directions."
        ),
    )