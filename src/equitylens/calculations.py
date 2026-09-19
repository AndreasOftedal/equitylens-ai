from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal

from equitylens.models import FinancialFact
from equitylens.periods import ComparisonType, classify_period_labels


@dataclass(frozen=True)
class FinancialChange:
    metric: str
    from_period: str
    to_period: str
    from_value: Decimal
    to_value: Decimal
    absolute_change: Decimal
    percentage_change: Decimal
    unit: str
    source_fact_ids: tuple[str, str]
    comparison_type: ComparisonType = "other"


def calculate_percentage_change(
    current: FinancialFact,
    comparison: FinancialFact,
) -> FinancialChange:
    """
    Calculate a deterministic change between two financial facts.

    The result retains lineage to both source facts and classifies the
    temporal relationship between the reporting periods.
    """

    if current.metric != comparison.metric:
        raise ValueError(
            "Cannot compare facts with different metrics: "
            f"'{current.metric}' and '{comparison.metric}'."
        )

    if current.unit != comparison.unit:
        raise ValueError(
            "Cannot compare facts with different units: "
            f"'{current.unit}' and '{comparison.unit}'."
        )

    if comparison.value == 0:
        raise ValueError(
            "Percentage change cannot be calculated from a zero comparison value."
        )

    absolute_change = current.value - comparison.value

    percentage_change = (
        absolute_change / abs(comparison.value) * Decimal(100)
    ).quantize(
        Decimal("0.1"),
        rounding=ROUND_HALF_UP,
    )

    return FinancialChange(
        metric=current.metric,
        from_period=comparison.period,
        to_period=current.period,
        from_value=comparison.value,
        to_value=current.value,
        absolute_change=absolute_change,
        percentage_change=percentage_change,
        unit=current.unit,
        source_fact_ids=(
            comparison.fact_id,
            current.fact_id,
        ),
        comparison_type=classify_period_labels(
            from_period=comparison.period,
            to_period=current.period,
        ),
    )