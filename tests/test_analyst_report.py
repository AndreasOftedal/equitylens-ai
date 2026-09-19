from decimal import Decimal

import pytest

from equitylens.analyst_report import build_analyst_report
from equitylens.fact_sets import FinancialFactSet
from equitylens.financial_dataset import MultiPeriodFinancialDataset
from equitylens.models import EvidenceRef, FinancialFact


def _fact(
    fact_id: str,
    metric: str,
    period: str,
    value: Decimal,
    document_id: str,
) -> FinancialFact:
    return FinancialFact(
        fact_id=fact_id,
        metric=metric,
        period=period,
        value=value,
        unit="USD million",
        evidence=EvidenceRef(
            document_id=document_id,
            page_number=4,
            table_number=1,
            row_label=metric,
            column_label=period,
        ),
    )


def _dataset() -> MultiPeriodFinancialDataset:
    q1_facts = (
        _fact(
            fact_id="net-income-q1",
            metric="Net income",
            period="Q1 2026",
            value=Decimal(3105),
            document_id="q1-report",
        ),
        _fact(
            fact_id="adjusted-net-income-q1",
            metric="Adjusted net income",
            period="Q1 2026",
            value=Decimal(3695),
            document_id="q1-report",
        ),
    )

    q2_facts = (
        _fact(
            fact_id="net-income-q2",
            metric="Net income",
            period="Q2 2026",
            value=Decimal(4836),
            document_id="q2-report",
        ),
        _fact(
            fact_id="adjusted-net-income-q2",
            metric="Adjusted net income",
            period="Q2 2026",
            value=Decimal(3225),
            document_id="q2-report",
        ),
    )

    return MultiPeriodFinancialDataset(
        fact_sets=(
            FinancialFactSet(
                document_id="q1-report",
                period="Q1 2026",
                facts=q1_facts,
            ),
            FinancialFactSet(
                document_id="q2-report",
                period="Q2 2026",
                facts=q2_facts,
            ),
        )
    )


def test_build_analyst_report_preserves_report_metadata():
    report = build_analyst_report(
        dataset=_dataset(),
        company="Equinor ASA",
        ticker="eqnr",
        metric_ids=(
            "net_income",
            "adjusted_net_income",
        ),
        from_period="Q1 2026",
        to_period="Q2 2026",
    )

    assert report.company == "Equinor ASA"
    assert report.ticker == "EQNR"
    assert report.from_period == "Q1 2026"
    assert report.to_period == "Q2 2026"
    assert len(report.metric_results) == 2


def test_report_contains_deterministic_financial_change():
    report = build_analyst_report(
        dataset=_dataset(),
        company="Equinor ASA",
        ticker="EQNR",
        metric_ids=("net_income",),
        from_period="Q1 2026",
        to_period="Q2 2026",
    )

    result = report.metric_results[0]

    assert result.metric_id == "net_income"
    assert result.change.metric == "Net income"
    assert result.change.absolute_change == Decimal(1731)
    assert result.change.percentage_change == Decimal("55.7")
    assert result.change.comparison_type == "qoq"


def test_report_builds_auditable_claim_with_exact_lineage():
    report = build_analyst_report(
        dataset=_dataset(),
        company="Equinor ASA",
        ticker="EQNR",
        metric_ids=("net_income",),
        from_period="Q1 2026",
        to_period="Q2 2026",
    )

    result = report.metric_results[0]
    audit = result.audit_trail

    assert audit.claim == (
        "Net income increased 55.7% "
        "from Q1 2026 to Q2 2026."
    )

    assert audit.direction == "increase"

    assert tuple(
        fact.fact_id
        for fact in audit.source_facts
    ) == (
        "net-income-q1",
        "net-income-q2",
    )

    assert audit.calculation.source_fact_ids == (
        "net-income-q1",
        "net-income-q2",
    )


def test_report_preserves_source_evidence():
    report = build_analyst_report(
        dataset=_dataset(),
        company="Equinor ASA",
        ticker="EQNR",
        metric_ids=("net_income",),
        from_period="Q1 2026",
        to_period="Q2 2026",
    )

    comparison_fact, current_fact = (
        report.metric_results[0].audit_trail.source_facts
    )

    assert comparison_fact.evidence.document_id == "q1-report"
    assert current_fact.evidence.document_id == "q2-report"

    assert comparison_fact.evidence.page_number == 4
    assert current_fact.evidence.page_number == 4

    assert comparison_fact.evidence.table_number == 1
    assert current_fact.evidence.table_number == 1


def test_report_supports_multiple_metric_results():
    report = build_analyst_report(
        dataset=_dataset(),
        company="Equinor ASA",
        ticker="EQNR",
        metric_ids=(
            "net_income",
            "adjusted_net_income",
        ),
        from_period="Q1 2026",
        to_period="Q2 2026",
    )

    results = {
        result.metric_id: result
        for result in report.metric_results
    }

    assert set(results) == {
        "net_income",
        "adjusted_net_income",
    }

    assert (
        results["adjusted_net_income"]
        .change.absolute_change
        == Decimal(-470)
    )

    assert (
        results["adjusted_net_income"]
        .audit_trail.direction
        == "decrease"
    )


def test_report_rejects_empty_metric_ids():
    with pytest.raises(
        ValueError,
        match="metric_ids cannot be empty",
    ):
        build_analyst_report(
            dataset=_dataset(),
            company="Equinor ASA",
            ticker="EQNR",
            metric_ids=(),
            from_period="Q1 2026",
            to_period="Q2 2026",
        )


def test_report_rejects_duplicate_metric_ids():
    with pytest.raises(
        ValueError,
        match="metric_ids must be unique",
    ):
        build_analyst_report(
            dataset=_dataset(),
            company="Equinor ASA",
            ticker="EQNR",
            metric_ids=(
                "net_income",
                "net_income",
            ),
            from_period="Q1 2026",
            to_period="Q2 2026",
        )


def test_report_rejects_empty_company_or_ticker():
    with pytest.raises(
        ValueError,
        match="company cannot be empty",
    ):
        build_analyst_report(
            dataset=_dataset(),
            company=" ",
            ticker="EQNR",
            metric_ids=("net_income",),
            from_period="Q1 2026",
            to_period="Q2 2026",
        )

    with pytest.raises(
        ValueError,
        match="ticker cannot be empty",
    ):
        build_analyst_report(
            dataset=_dataset(),
            company="Equinor ASA",
            ticker=" ",
            metric_ids=("net_income",),
            from_period="Q1 2026",
            to_period="Q2 2026",
        )