from decimal import Decimal

import pytest

from equitylens.analysis_pipeline import (
    PeriodSource,
)
from equitylens.documents import (
    AKER_BP_Q1_2026,
    AKER_BP_Q2_2026,
)
from equitylens.research_pipeline import (
    build_aker_bp_research_result,
)

pytestmark = pytest.mark.integration


METRIC_IDS = (
    "net_income",
    "basic_earnings_per_share",
    "operating_cash_flow",
    "total_equity_production",
)


@pytest.fixture(scope="module")
def research_result():
    return build_aker_bp_research_result(
        previous_source=PeriodSource(
            document=AKER_BP_Q1_2026,
            page_number=3,
        ),
        current_source=PeriodSource(
            document=AKER_BP_Q2_2026,
            page_number=3,
        ),
        company="Aker BP ASA",
        ticker="AKRBP",
        metric_ids=METRIC_IDS,
    )


def _metric_results_by_id(
    research_result,
):
    return {
        result.metric_id: result
        for result in (
            research_result
            .analyst_report
            .metric_results
        )
    }


def _consistency_by_metric_id(
    research_result,
):
    return {
        assessment.metric_id: assessment
        for assessment in (
            research_result
            .consistency_assessments
        )
    }


def test_real_aker_bp_unified_pipeline_builds_analyst_report(
    research_result,
):
    report = (
        research_result.analyst_report
    )

    assert report.company == "Aker BP ASA"
    assert report.ticker == "AKRBP"
    assert report.from_period == "Q1 2026"
    assert report.to_period == "Q2 2026"

    assert tuple(
        result.metric_id
        for result in report.metric_results
    ) == METRIC_IDS


def test_real_aker_bp_unified_pipeline_preserves_financial_changes(
    research_result,
):
    results = _metric_results_by_id(
        research_result
    )

    assert (
        results[
            "net_income"
        ].change.absolute_change
        == Decimal(-237)
    )

    assert (
        results[
            "basic_earnings_per_share"
        ].change.absolute_change
        == Decimal("-0.38")
    )

    assert (
        results[
            "operating_cash_flow"
        ].change.absolute_change
        == Decimal(1110)
    )

    assert (
        results[
            "total_equity_production"
        ].change.absolute_change
        == Decimal("-14.8")
    )


def test_real_aker_bp_unified_pipeline_uses_conservative_evidence(
    research_result,
):
    results = _metric_results_by_id(
        research_result
    )

    assert (
        results[
            "net_income"
        ].evidence_assessment
        is None
    )

    assert (
        results[
            "basic_earnings_per_share"
        ].evidence_assessment
        is None
    )

    cash_flow = results[
        "operating_cash_flow"
    ].evidence_assessment

    production = results[
        "total_equity_production"
    ].evidence_assessment

    assert cash_flow is not None
    assert production is not None

    assert (
        cash_flow.availability
        == "unavailable"
    )

    assert (
        production.availability
        == "unavailable"
    )

    assert (
        cash_flow.expected_comparison_type
        == "qoq"
    )

    assert (
        production.expected_comparison_type
        == "qoq"
    )


def test_real_aker_bp_unified_pipeline_builds_consistency_assessments(
    research_result,
):
    assessments = (
        research_result
        .consistency_assessments
    )

    by_metric = (
        _consistency_by_metric_id(
            research_result
        )
    )

    assert tuple(
        assessment.metric_id
        for assessment in assessments
    ) == METRIC_IDS

    assert all(
        assessment.comparison_type == "qoq"
        for assessment in assessments
    )

    assert all(
        assessment.status
        == "insufficient_evidence"
        for assessment in assessments
    )

    assert (
        by_metric[
            "net_income"
        ].financial_direction
        == "decrease"
    )

    assert (
        by_metric[
            "basic_earnings_per_share"
        ].financial_direction
        == "decrease"
    )

    assert (
        by_metric[
            "operating_cash_flow"
        ].financial_direction
        == "increase"
    )

    assert (
        by_metric[
            "total_equity_production"
        ].financial_direction
        == "decrease"
    )


def test_real_aker_bp_unified_pipeline_builds_guidance_report(
    research_result,
):
    report = (
        research_result.guidance_report
    )

    assert len(report.changes) == 6
    assert len(report.changed) == 2
    assert len(report.unchanged) == 4

    assert report.introduced == ()
    assert report.withdrawn == ()

    changed_by_metric = {
        change.metric_id: change
        for change in report.changed
    }

    assert set(changed_by_metric) == {
        "production_guidance",
        "capex_guidance",
    }

    assert (
        changed_by_metric[
            "production_guidance"
        ].change_type
        == "increased"
    )

    assert (
        changed_by_metric[
            "capex_guidance"
        ].change_type
        == "increased"
    )


def test_real_aker_bp_unified_pipeline_keeps_financial_and_guidance_analysis_separate(
    research_result,
):
    financial_metric_ids = {
        result.metric_id
        for result in (
            research_result
            .analyst_report
            .metric_results
        )
    }

    guidance_metric_ids = {
        change.metric_id
        for change in (
            research_result
            .guidance_report
            .changes
        )
    }

    assert (
        "total_equity_production"
        in financial_metric_ids
    )

    assert (
        "production_guidance"
        not in financial_metric_ids
    )

    assert (
        "production_guidance"
        in guidance_metric_ids
    )

    assert (
        "total_equity_production"
        not in guidance_metric_ids
    )