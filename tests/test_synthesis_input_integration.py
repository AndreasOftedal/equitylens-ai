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
from equitylens.synthesis_input import (
    build_synthesis_input,
)

pytestmark = pytest.mark.integration


METRIC_IDS = (
    "net_operating_income",
    "net_income",
    "adjusted_operating_income",
    "adjusted_net_income",
)


@pytest.fixture(scope="module")
def synthesis_input():
    research_result = (
        build_equinor_research_result(
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
    )

    return build_synthesis_input(
        research_result
    )


def _metrics_by_id(
    synthesis_input,
):
    return {
        metric.metric_id: metric
        for metric
        in synthesis_input.metrics
    }


def _guidance_by_id(
    synthesis_input,
):
    return {
        guidance.metric_id: guidance
        for guidance
        in synthesis_input.guidance_changes
    }


def test_real_synthesis_input_preserves_root_metadata(
    synthesis_input,
):
    assert (
        synthesis_input.schema_version
        == "1.0"
    )

    assert (
        synthesis_input.company
        == "Equinor ASA"
    )

    assert (
        synthesis_input.ticker
        == "EQNR"
    )

    assert (
        synthesis_input.from_period
        == "Q1 2026"
    )

    assert (
        synthesis_input.to_period
        == "Q2 2026"
    )

    assert (
        synthesis_input.previous_document_id
        == (
            "equinor-q1-2026-"
            "financial-statements-and-review"
        )
    )

    assert (
        synthesis_input.current_document_id
        == (
            "equinor-q2-2026-"
            "financial-statements-and-review"
        )
    )


def test_real_synthesis_input_preserves_exact_financial_values(
    synthesis_input,
):
    metrics = _metrics_by_id(
        synthesis_input
    )

    net_operating_income = metrics[
        "net_operating_income"
    ]

    assert (
        net_operating_income.from_value
        == "8784"
    )

    assert (
        net_operating_income.to_value
        == "12993"
    )

    assert (
        net_operating_income.absolute_change
        == "4209"
    )

    assert (
        Decimal(
            net_operating_income
            .percentage_change
        )
        == Decimal("47.9")
    )

    adjusted_net_income = metrics[
        "adjusted_net_income"
    ]

    assert (
        adjusted_net_income.absolute_change
        == "-470"
    )

    assert (
        adjusted_net_income
        .financial_direction
        == "decrease"
    )


def test_real_synthesis_input_preserves_financial_provenance(
    synthesis_input,
):
    metrics = _metrics_by_id(
        synthesis_input
    )

    metric = metrics[
        "net_operating_income"
    ]

    assert len(
        metric.source_facts
    ) == 2

    previous_fact, current_fact = (
        metric.source_facts
    )

    assert (
        previous_fact.period
        == "Q1 2026"
    )

    assert (
        current_fact.period
        == "Q2 2026"
    )

    assert (
        previous_fact.source.document_id
        == synthesis_input.previous_document_id
    )

    assert (
        current_fact.source.document_id
        == synthesis_input.current_document_id
    )

    assert (
        previous_fact.source.page_number
        >= 1
    )

    assert (
        current_fact.source.page_number
        >= 1
    )

    assert (
        previous_fact.source.row_label
        is not None
    )

    assert (
        current_fact.source.row_label
        is not None
    )


def test_real_synthesis_input_keeps_evidence_semantics_conservative(
    synthesis_input,
):
    metrics = _metrics_by_id(
        synthesis_input
    )

    net_operating_income = metrics[
        "net_operating_income"
    ]

    adjusted_operating_income = metrics[
        "adjusted_operating_income"
    ]

    net_income = metrics[
        "net_income"
    ]

    adjusted_net_income = metrics[
        "adjusted_net_income"
    ]

    assert (
        net_operating_income
        .evidence_availability
        == "unavailable"
    )

    assert (
        adjusted_operating_income
        .evidence_availability
        == "unavailable"
    )

    assert (
        net_income.evidence_availability
        == "not_evaluated"
    )

    assert (
        adjusted_net_income
        .evidence_availability
        == "not_evaluated"
    )

    assert (
        net_operating_income
        .direct_explanations
        == ()
    )

    assert (
        adjusted_operating_income
        .direct_explanations
        == ()
    )

    assert (
        adjusted_operating_income
        .aligned_context
        == ()
    )


def test_real_synthesis_input_preserves_consistency_guardrails(
    synthesis_input,
):
    assert all(
        metric.comparison_type
        == "qoq"
        for metric
        in synthesis_input.metrics
    )

    assert all(
        metric.consistency_status
        == "insufficient_evidence"
        for metric
        in synthesis_input.metrics
    )


def test_real_synthesis_input_preserves_guidance_changes(
    synthesis_input,
):
    guidance = _guidance_by_id(
        synthesis_input
    )

    assert len(
        synthesis_input.guidance_changes
    ) == 5

    share_buyback = guidance[
        "share_buyback"
    ]

    assert (
        share_buyback.change_type
        == "increased"
    )

    assert (
        share_buyback.previous.numeric_value
        == "1.5"
    )

    assert (
        share_buyback.current.numeric_value
        == "3"
    )

    assert (
        share_buyback.previous.unit
        == share_buyback.current.unit
    )

    assert (
        share_buyback.previous.document_id
        == synthesis_input.previous_document_id
    )

    assert (
        share_buyback.current.document_id
        == synthesis_input.current_document_id
    )


def test_real_synthesis_input_preserves_unchanged_guidance(
    synthesis_input,
):
    unchanged = tuple(
        guidance
        for guidance
        in synthesis_input.guidance_changes
        if guidance.change_type
        == "unchanged"
    )

    assert len(
        unchanged
    ) == 4

    assert (
        synthesis_input.guidance_introduced
        == ()
    )

    assert (
        synthesis_input.guidance_withdrawn
        == ()
    )


def test_real_synthesis_payload_is_json_ready(
    synthesis_input,
):
    payload = (
        synthesis_input.to_dict()
    )

    assert (
        payload["company"]
        == "Equinor ASA"
    )

    assert isinstance(
        payload["metrics"],
        tuple,
    )

    first_metric = (
        payload["metrics"][0]
    )

    assert isinstance(
        first_metric["from_value"],
        str,
    )

    assert isinstance(
        first_metric[
            "absolute_change"
        ],
        str,
    )