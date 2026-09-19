from decimal import Decimal

import pytest

from equitylens.analyst_report import (
    build_analyst_report,
)
from equitylens.evidence_assessment import (
    EvidenceAssessment,
)
from equitylens.fact_sets import FinancialFactSet
from equitylens.financial_dataset import (
    MultiPeriodFinancialDataset,
)
from equitylens.models import (
    EvidenceRef,
    FinancialFact,
)


def _fact(
    fact_id: str,
    period: str,
    value: Decimal,
    document_id: str,
) -> FinancialFact:
    return FinancialFact(
        fact_id=fact_id,
        metric="Net income",
        period=period,
        value=value,
        unit="USD million",
        evidence=EvidenceRef(
            document_id=document_id,
            page_number=4,
            table_number=1,
            row_label="Net income",
            column_label=period,
        ),
    )


def _dataset() -> MultiPeriodFinancialDataset:
    return MultiPeriodFinancialDataset(
        fact_sets=(
            FinancialFactSet(
                document_id="q1-report",
                period="Q1 2026",
                facts=(
                    _fact(
                        fact_id="net-income-q1",
                        period="Q1 2026",
                        value=Decimal(3105),
                        document_id="q1-report",
                    ),
                ),
            ),
            FinancialFactSet(
                document_id="q2-report",
                period="Q2 2026",
                facts=(
                    _fact(
                        fact_id="net-income-q2",
                        period="Q2 2026",
                        value=Decimal(4836),
                        document_id="q2-report",
                    ),
                ),
            ),
        )
    )


def _qoq_assessment() -> EvidenceAssessment:
    return EvidenceAssessment(
        query="What drove net income?",
        expected_comparison_type="qoq",
        availability="unavailable",
        direct_explanations=(),
        aligned_context=(),
        rejection_counts=(
            (
                "period_mismatch",
                2,
            ),
            (
                "period_unknown",
                1,
            ),
        ),
    )


def test_report_without_evidence_remains_supported():
    report = build_analyst_report(
        dataset=_dataset(),
        company="Equinor ASA",
        ticker="EQNR",
        metric_ids=("net_income",),
        from_period="Q1 2026",
        to_period="Q2 2026",
    )

    result = report.metric_results[0]

    assert (
        result.evidence_assessment
        is None
    )

    assert (
        result.change.absolute_change
        == Decimal(1731)
    )


def test_report_attaches_evidence_assessment():
    evidence = _qoq_assessment()

    report = build_analyst_report(
        dataset=_dataset(),
        company="Equinor ASA",
        ticker="EQNR",
        metric_ids=("net_income",),
        from_period="Q1 2026",
        to_period="Q2 2026",
        evidence_assessments={
            "net_income": evidence,
        },
    )

    result = report.metric_results[0]

    assert (
        result.evidence_assessment
        is evidence
    )

    assert (
        result.evidence_assessment.availability
        == "unavailable"
    )

    assert (
        dict(
            result.evidence_assessment.rejection_counts
        )["period_mismatch"]
        == 2
    )


def test_report_keeps_financial_and_narrative_evidence_separate():
    report = build_analyst_report(
        dataset=_dataset(),
        company="Equinor ASA",
        ticker="EQNR",
        metric_ids=("net_income",),
        from_period="Q1 2026",
        to_period="Q2 2026",
        evidence_assessments={
            "net_income": _qoq_assessment(),
        },
    )

    result = report.metric_results[0]

    assert (
        result.audit_trail.source_facts[
            0
        ].fact_id
        == "net-income-q1"
    )

    assert (
        result.audit_trail.source_facts[
            1
        ].fact_id
        == "net-income-q2"
    )

    assert (
        result.evidence_assessment.query
        == "What drove net income?"
    )


def test_report_rejects_evidence_with_wrong_comparison_basis():
    yoy_evidence = EvidenceAssessment(
        query="What drove net income?",
        expected_comparison_type="yoy",
        availability="unavailable",
        direct_explanations=(),
        aligned_context=(),
        rejection_counts=(),
    )

    with pytest.raises(
        ValueError,
        match=(
            "Evidence comparison type for "
            "net_income does not match "
            "the financial change"
        ),
    ):
        build_analyst_report(
            dataset=_dataset(),
            company="Equinor ASA",
            ticker="EQNR",
            metric_ids=("net_income",),
            from_period="Q1 2026",
            to_period="Q2 2026",
            evidence_assessments={
                "net_income": yoy_evidence,
            },
        )


def test_report_rejects_evidence_for_unrequested_metric():
    with pytest.raises(
        ValueError,
        match=(
            "evidence_assessments contains "
            "unrequested metric_ids"
        ),
    ):
        build_analyst_report(
            dataset=_dataset(),
            company="Equinor ASA",
            ticker="EQNR",
            metric_ids=("net_income",),
            from_period="Q1 2026",
            to_period="Q2 2026",
            evidence_assessments={
                "adjusted_net_income": (
                    _qoq_assessment()
                ),
            },
        )


def test_report_financial_change_is_unchanged_by_narrative_evidence():
    without_evidence = build_analyst_report(
        dataset=_dataset(),
        company="Equinor ASA",
        ticker="EQNR",
        metric_ids=("net_income",),
        from_period="Q1 2026",
        to_period="Q2 2026",
    )

    with_evidence = build_analyst_report(
        dataset=_dataset(),
        company="Equinor ASA",
        ticker="EQNR",
        metric_ids=("net_income",),
        from_period="Q1 2026",
        to_period="Q2 2026",
        evidence_assessments={
            "net_income": _qoq_assessment(),
        },
    )

    assert (
        with_evidence.metric_results[
            0
        ].change
        == without_evidence.metric_results[
            0
        ].change
    )

    assert (
        with_evidence.metric_results[
            0
        ].audit_trail
        == without_evidence.metric_results[
            0
        ].audit_trail
    )