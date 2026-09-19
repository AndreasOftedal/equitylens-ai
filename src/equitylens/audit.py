from dataclasses import dataclass
from typing import Literal

from equitylens.calculations import FinancialChange
from equitylens.models import FinancialFact

ChangeDirection = Literal[
    "increase",
    "decrease",
    "unchanged",
]


@dataclass(frozen=True)
class ResearchAuditTrail:
    claim: str
    direction: ChangeDirection
    calculation: FinancialChange
    source_facts: tuple[FinancialFact, FinancialFact]


def _change_direction(change: FinancialChange) -> ChangeDirection:
    if change.absolute_change > 0:
        return "increase"

    if change.absolute_change < 0:
        return "decrease"

    return "unchanged"


def _build_change_claim(
    change: FinancialChange,
    direction: ChangeDirection,
) -> str:
    metric = change.metric.rstrip("*").strip()

    if direction == "increase":
        return (
            f"{metric} increased {abs(change.percentage_change)}% "
            f"from {change.from_period} to {change.to_period}."
        )

    if direction == "decrease":
        return (
            f"{metric} decreased {abs(change.percentage_change)}% "
            f"from {change.from_period} to {change.to_period}."
        )

    return (
        f"{metric} was unchanged from "
        f"{change.from_period} to {change.to_period}."
    )


def build_change_audit_trail(
    change: FinancialChange,
    source_facts: tuple[FinancialFact, FinancialFact],
) -> ResearchAuditTrail:
    """
    Build a deterministic audit trail for a financial change.

    The source facts must exactly match the fact IDs retained by the
    deterministic calculation. This prevents an analysis from being
    attached to unrelated evidence.
    """

    expected_fact_ids = change.source_fact_ids
    actual_fact_ids = tuple(
        fact.fact_id
        for fact in source_facts
    )

    if actual_fact_ids != expected_fact_ids:
        raise ValueError(
            "Source facts do not match the calculation lineage. "
            f"Expected {expected_fact_ids}, got {actual_fact_ids}."
        )

    comparison_fact, current_fact = source_facts

    if comparison_fact.metric != change.metric:
        raise ValueError(
            "Comparison fact metric does not match the calculation metric."
        )

    if current_fact.metric != change.metric:
        raise ValueError(
            "Current fact metric does not match the calculation metric."
        )

    if comparison_fact.period != change.from_period:
        raise ValueError(
            "Comparison fact period does not match the calculation from_period."
        )

    if current_fact.period != change.to_period:
        raise ValueError(
            "Current fact period does not match the calculation to_period."
        )

    if comparison_fact.unit != change.unit or current_fact.unit != change.unit:
        raise ValueError(
            "Source fact units do not match the calculation unit."
        )

    direction = _change_direction(change)

    return ResearchAuditTrail(
        claim=_build_change_claim(
            change=change,
            direction=direction,
        ),
        direction=direction,
        calculation=change,
        source_facts=source_facts,
    )