from dataclasses import dataclass

from equitylens.financial_extractor import (
    extract_registered_financial_fact,
)
from equitylens.metrics import get_metric_definition
from equitylens.models import FinancialFact, ParsedTable


@dataclass(frozen=True)
class FinancialFactSet:
    document_id: str
    period: str
    facts: tuple[FinancialFact, ...]

    def get(self, metric_id: str) -> FinancialFact:
        metric_definition = get_metric_definition(metric_id)

        matches = [
            fact
            for fact in self.facts
            if fact.metric == metric_definition.canonical_name
        ]

        if len(matches) != 1:
            raise ValueError(
                f"Expected exactly one fact for metric_id "
                f"'{metric_id}', found {len(matches)}."
            )

        return matches[0]


def extract_registered_fact_set(
    table: ParsedTable,
    metric_ids: tuple[str, ...],
    period: str,
) -> FinancialFactSet:
    """
    Extract multiple registered metrics for one reporting period.

    Each resulting FinancialFact retains its own source-level evidence.
    """

    if not metric_ids:
        raise ValueError("metric_ids cannot be empty.")

    if len(metric_ids) != len(set(metric_ids)):
        raise ValueError("metric_ids must be unique.")

    facts = tuple(
        extract_registered_financial_fact(
            table=table,
            metric_id=metric_id,
            period=period,
        )
        for metric_id in metric_ids
    )

    return FinancialFactSet(
        document_id=table.document_id,
        period=period,
        facts=facts,
    )