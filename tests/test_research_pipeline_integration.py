from decimal import Decimal

import pytest

from equitylens.analysis_pipeline import (
    PeriodSource,
)
from equitylens.documents import (
    EQUINOR_Q1_2026,
    EQUINOR_Q2_2026,
)
from equitylens.research_pipeline import (
    build_equinor_research_result,
)

pytestmark = pytest.mark.integration


METRIC_IDS = (
    "net_operating_income",
    "net_income",
    "adjusted_operating_income",
    "adjusted_net_income",
)


@pytest.fixture(scope="module")
def research_result():
    return build_equinor_research_result(
        previous_source=PeriodSource(
            document=EQUINOR_Q1_2026,
            page_number=4,
        ),
        current_source=PeriodSource(
            document=EQUINOR_Q2_2026,
            page_number=4,
        ),
        company="Equinor ASA",
        ticker="EQNR",
        metric_ids=METRIC_IDS,
    )


def _metric_results_by_id(
    research_result,
):
    return {
        result.metric_id: result
        for result
        in research_result.analyst_report.metric_results
    }


def test_real_unified_pipeline_builds_analyst_report(
    research_result,
):
    report = (
        research_result.analyst_report
    )

    assert report.company == "Equinor ASA"
    assert report.ticker == "EQNR"
    assert report.from_period == "Q1 2026"
    assert report.to_period == "Q2 2026"

    assert len(
        report.metric_results
    ) == 4


def test_real_unified_pipeline_preserves_financial_changes(
    research_result,
):
    results = _metric_results_by_id(
        research_result
    )

    assert (
        results[
            "net_operating_income"
        ].change.absolute_change
        == Decimal(4209)
    )

    assert (
        results[
            "adjusted_operating_income"
        ].change.absolute_change
        == Decimal(1712)
    )

    assert (
        results[
            "net_income"
        ].change.absolute_change
        == Decimal(1731)
    )

    assert (
        results[
            "adjusted_net_income"
        ].change.absolute_change
        == Decimal(-470)
    )


def test_real_unified_pipeline_attaches_validated_evidence_only(
    research_result,
):
    results = _metric_results_by_id(
        research_result
    )

    net_operating_income = results[
        "net_operating_income"
    ]

    adjusted_operating_income = results[
        "adjusted_operating_income"
    ]

    assert (
        net_operating_income
        .evidence_assessment
        is not None
    )

    assert (
        adjusted_operating_income
        .evidence_assessment
        is not None
    )

    assert (
        results[
            "net_income"
        ].evidence_assessment
        is None
    )

    assert (
        results[
            "adjusted_net_income"
        ].evidence_assessment
        is None
    )


def test_real_unified_pipeline_respects_conservative_evidence_gate(
    research_result,
):
    results = _metric_results_by_id(
        research_result
    )

    net_operating_income = (
        results[
            "net_operating_income"
        ].evidence_assessment
    )

    adjusted_operating_income = (
        results[
            "adjusted_operating_income"
        ].evidence_assessment
    )

    assert (
        net_operating_income
        is not None
    )

    assert (
        adjusted_operating_income
        is not None
    )

    assert (
        net_operating_income.availability
        == "unavailable"
    )

    assert (
        adjusted_operating_income.availability
        == "aligned_context_only"
    )

    assert (
        net_operating_income
        .expected_comparison_type
        == "qoq"
    )

    assert (
        adjusted_operating_income
        .expected_comparison_type
        == "qoq"
    )


def test_real_unified_pipeline_builds_guidance_report(
    research_result,
):
    report = (
        research_result.guidance_report
    )

    assert len(
        report.changes
    ) == 5

    assert len(
        report.unchanged
    ) == 4

    assert len(
        report.changed
    ) == 1

    assert report.introduced == ()
    assert report.withdrawn == ()


def test_real_unified_pipeline_detects_buyback_increase(
    research_result,
):
    change = (
        research_result
        .guidance_report
        .changed[0]
    )

    assert (
        change.metric_id
        == "share_buyback"
    )

    assert (
        change.change_type
        == "increased"
    )

    assert (
        change.previous.numeric_value
        == Decimal("1.5")
    )

    assert (
        change.current.numeric_value
        == Decimal(3)
    )


def test_real_unified_pipeline_keeps_financial_and_guidance_analysis_separate(
    research_result,
):
    financial_metric_ids = {
        result.metric_id
        for result
        in research_result.analyst_report.metric_results
    }

    guidance_metric_ids = {
        change.metric_id
        for change
        in research_result.guidance_report.changes
    }

    assert (
        "share_buyback"
        not in financial_metric_ids
    )

    assert (
        "share_buyback"
        in guidance_metric_ids
    )