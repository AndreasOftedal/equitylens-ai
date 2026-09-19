from decimal import Decimal

import pytest

from equitylens.analysis_pipeline import (
    PeriodSource,
    build_multi_period_financial_dataset,
)
from equitylens.analyst_report import build_analyst_report
from equitylens.documents import EQUINOR_Q1_2026, EQUINOR_Q2_2026

pytestmark = pytest.mark.integration


METRIC_IDS = (
    "net_operating_income",
    "net_income",
    "basic_earnings_per_share",
    "adjusted_operating_income",
    "adjusted_net_income",
    "adjusted_earnings_per_share",
    "operating_cash_flow",
    "operating_cash_flow_after_tax",
    "net_cash_flow_before_capital_distribution",
    "group_average_liquids_price",
    "total_equity_production",
    "total_power_generation",
    "renewable_power_generation",
)


def _build_report():
    dataset = build_multi_period_financial_dataset(
        sources=(
            PeriodSource(
                document=EQUINOR_Q1_2026,
                page_number=4,
            ),
            PeriodSource(
                document=EQUINOR_Q2_2026,
                page_number=4,
            ),
        ),
        metric_ids=METRIC_IDS,
    )

    return build_analyst_report(
        dataset=dataset,
        company="Equinor ASA",
        ticker="EQNR",
        metric_ids=METRIC_IDS,
        from_period="Q1 2026",
        to_period="Q2 2026",
    )


def test_real_equnor_report_contains_all_metric_results():
    report = _build_report()

    assert report.company == "Equinor ASA"
    assert report.ticker == "EQNR"
    assert report.from_period == "Q1 2026"
    assert report.to_period == "Q2 2026"

    assert len(report.metric_results) == 13

    assert {
        result.metric_id
        for result in report.metric_results
    } == set(METRIC_IDS)


def test_real_report_contains_expected_auditable_claims():
    report = _build_report()

    results = {
        result.metric_id: result
        for result in report.metric_results
    }

    assert (
        results["net_income"].audit_trail.claim
        == "Net income increased 55.7% from Q1 2026 to Q2 2026."
    )

    assert (
        results["adjusted_net_income"].audit_trail.claim
        == "Adjusted net income decreased 12.7% from Q1 2026 to Q2 2026."
    )

    assert (
        results["total_equity_production"].audit_trail.claim
        == (
            "Total equity liquids and gas production decreased 6.4% "
            "from Q1 2026 to Q2 2026."
        )
    )


def test_real_report_preserves_deterministic_calculations():
    report = _build_report()

    results = {
        result.metric_id: result
        for result in report.metric_results
    }

    net_income = results["net_income"].change

    assert net_income.absolute_change == Decimal(1731)
    assert net_income.percentage_change == Decimal("55.7")
    assert net_income.comparison_type == "qoq"

    operating_cash_flow = results[
        "operating_cash_flow"
    ].change

    assert operating_cash_flow.absolute_change == Decimal(4257)
    assert operating_cash_flow.percentage_change == Decimal("81.7")
    assert operating_cash_flow.comparison_type == "qoq"


def test_real_report_preserves_exact_source_lineage():
    report = _build_report()

    for result in report.metric_results:
        audit = result.audit_trail

        comparison_fact, current_fact = audit.source_facts

        assert comparison_fact.evidence.document_id == (
            EQUINOR_Q1_2026.document_id
        )

        assert current_fact.evidence.document_id == (
            EQUINOR_Q2_2026.document_id
        )

        assert comparison_fact.evidence.page_number == 4
        assert current_fact.evidence.page_number == 4

        assert comparison_fact.evidence.table_number is not None
        assert current_fact.evidence.table_number is not None

        assert comparison_fact.evidence.row_label is not None
        assert current_fact.evidence.row_label is not None

        assert audit.calculation.source_fact_ids == (
            comparison_fact.fact_id,
            current_fact.fact_id,
        )


def test_real_report_contains_both_increases_and_decreases():
    report = _build_report()

    directions = {
        result.audit_trail.direction
        for result in report.metric_results
    }

    assert "increase" in directions
    assert "decrease" in directions