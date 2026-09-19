from dataclasses import dataclass

from equitylens.audit import (
    ResearchAuditTrail,
    build_change_audit_trail,
)
from equitylens.calculations import FinancialChange
from equitylens.financial_dataset import MultiPeriodFinancialDataset
from equitylens.metrics import get_metric_definition


@dataclass(frozen=True)
class MetricAnalysisResult:
    metric_id: str
    change: FinancialChange
    audit_trail: ResearchAuditTrail


@dataclass(frozen=True)
class AnalystReport:
    company: str
    ticker: str
    from_period: str
    to_period: str
    metric_results: tuple[MetricAnalysisResult, ...]


def build_analyst_report(
    dataset: MultiPeriodFinancialDataset,
    company: str,
    ticker: str,
    metric_ids: tuple[str, ...],
    from_period: str,
    to_period: str,
) -> AnalystReport:
    """
    Build a structured analyst report from deterministic financial data.

    The report performs no new financial calculations. Each metric result
    reuses the deterministic FinancialChange produced by the dataset and
    attaches the exact source facts through a ResearchAuditTrail.
    """

    if not company.strip():
        raise ValueError("company cannot be empty.")

    if not ticker.strip():
        raise ValueError("ticker cannot be empty.")

    if not metric_ids:
        raise ValueError("metric_ids cannot be empty.")

    if len(metric_ids) != len(set(metric_ids)):
        raise ValueError("metric_ids must be unique.")

    results = []

    for metric_id in metric_ids:
        get_metric_definition(metric_id)

        comparison_fact = dataset.get_fact(
            metric_id=metric_id,
            period=from_period,
        )

        current_fact = dataset.get_fact(
            metric_id=metric_id,
            period=to_period,
        )

        change = dataset.compare(
            metric_id=metric_id,
            from_period=from_period,
            to_period=to_period,
        )

        audit_trail = build_change_audit_trail(
            change=change,
            source_facts=(
                comparison_fact,
                current_fact,
            ),
        )

        results.append(
            MetricAnalysisResult(
                metric_id=metric_id,
                change=change,
                audit_trail=audit_trail,
            )
        )

    return AnalystReport(
        company=company.strip(),
        ticker=ticker.strip().upper(),
        from_period=from_period,
        to_period=to_period,
        metric_results=tuple(results),
    )