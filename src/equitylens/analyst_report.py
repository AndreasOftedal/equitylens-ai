from collections.abc import Mapping
from dataclasses import dataclass

from equitylens.audit import (
    ResearchAuditTrail,
    build_change_audit_trail,
)
from equitylens.calculations import FinancialChange
from equitylens.evidence_assessment import EvidenceAssessment
from equitylens.financial_dataset import MultiPeriodFinancialDataset
from equitylens.metrics import get_metric_definition


@dataclass(frozen=True)
class MetricAnalysisResult:
    metric_id: str
    change: FinancialChange
    audit_trail: ResearchAuditTrail
    evidence_assessment: EvidenceAssessment | None = None


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
    evidence_assessments: Mapping[
        str,
        EvidenceAssessment,
    ]
    | None = None,
) -> AnalystReport:
    """
    Build a structured analyst report from deterministic financial data.

    The report performs no new financial calculations. Each metric result
    reuses the deterministic FinancialChange produced by the dataset and
    attaches the exact source facts through a ResearchAuditTrail.

    Optional narrative EvidenceAssessment objects may be attached to metric
    results. Their comparison basis must match the deterministic financial
    comparison before they can enter the report.
    """

    if not company.strip():
        raise ValueError(
            "company cannot be empty."
        )

    if not ticker.strip():
        raise ValueError(
            "ticker cannot be empty."
        )

    if not metric_ids:
        raise ValueError(
            "metric_ids cannot be empty."
        )

    if len(metric_ids) != len(
        set(metric_ids)
    ):
        raise ValueError(
            "metric_ids must be unique."
        )

    evidence_by_metric = (
        dict(evidence_assessments)
        if evidence_assessments is not None
        else {}
    )

    unknown_evidence_metrics = (
        set(evidence_by_metric)
        - set(metric_ids)
    )

    if unknown_evidence_metrics:
        unknown = ", ".join(
            sorted(
                unknown_evidence_metrics
            )
        )

        raise ValueError(
            "evidence_assessments contains "
            "unrequested metric_ids: "
            f"{unknown}"
        )

    results: list[
        MetricAnalysisResult
    ] = []

    for metric_id in metric_ids:
        get_metric_definition(
            metric_id
        )

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

        evidence_assessment = (
            evidence_by_metric.get(
                metric_id
            )
        )

        if (
            evidence_assessment is not None
            and evidence_assessment.expected_comparison_type
            != change.comparison_type
        ):
            raise ValueError(
                "Evidence comparison type for "
                f"{metric_id} does not match "
                "the financial change."
            )

        results.append(
            MetricAnalysisResult(
                metric_id=metric_id,
                change=change,
                audit_trail=audit_trail,
                evidence_assessment=(
                    evidence_assessment
                ),
            )
        )

    return AnalystReport(
        company=company.strip(),
        ticker=ticker.strip().upper(),
        from_period=from_period,
        to_period=to_period,
        metric_results=tuple(
            results
        ),
    )