from dataclasses import dataclass

from equitylens.calculations import (
    FinancialChange,
    calculate_percentage_change,
)
from equitylens.fact_sets import FinancialFactSet
from equitylens.metrics import get_metric_definition
from equitylens.models import FinancialFact


@dataclass(frozen=True)
class MultiPeriodFinancialDataset:
    fact_sets: tuple[FinancialFactSet, ...]

    def get_fact(
        self,
        metric_id: str,
        period: str,
    ) -> FinancialFact:
        matching_sets = [
            fact_set
            for fact_set in self.fact_sets
            if fact_set.period == period
        ]

        if len(matching_sets) != 1:
            raise ValueError(
                f"Expected exactly one fact set for period "
                f"'{period}', found {len(matching_sets)}."
            )

        return matching_sets[0].get(metric_id)

    def compare(
        self,
        metric_id: str,
        from_period: str,
        to_period: str,
    ) -> FinancialChange:
        get_metric_definition(metric_id)

        comparison_fact = self.get_fact(
            metric_id=metric_id,
            period=from_period,
        )

        current_fact = self.get_fact(
            metric_id=metric_id,
            period=to_period,
        )

        return calculate_percentage_change(
            current=current_fact,
            comparison=comparison_fact,
        )

    def compare_metrics(
        self,
        metric_ids: tuple[str, ...],
        from_period: str,
        to_period: str,
    ) -> tuple[FinancialChange, ...]:
        if not metric_ids:
            raise ValueError("metric_ids cannot be empty.")

        if len(metric_ids) != len(set(metric_ids)):
            raise ValueError("metric_ids must be unique.")

        return tuple(
            self.compare(
                metric_id=metric_id,
                from_period=from_period,
                to_period=to_period,
            )
            for metric_id in metric_ids
        )