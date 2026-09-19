from decimal import Decimal

import pytest

from equitylens.documents import (
    EQUINOR_Q1_2026,
    EQUINOR_Q2_2026,
)
from equitylens.guidance_pipeline import (
    build_equinor_guidance_report,
)
from equitylens.parser import parse_pdf

pytestmark = pytest.mark.integration


@pytest.fixture(scope="module")
def guidance_report():
    q1_pages = parse_pdf(
        document_id=EQUINOR_Q1_2026.document_id,
        pdf_path=EQUINOR_Q1_2026.local_path,
    )

    q2_pages = parse_pdf(
        document_id=EQUINOR_Q2_2026.document_id,
        pdf_path=EQUINOR_Q2_2026.local_path,
    )

    return build_equinor_guidance_report(
        previous_document_id=(
            EQUINOR_Q1_2026.document_id
        ),
        previous_pages=q1_pages,
        current_document_id=(
            EQUINOR_Q2_2026.document_id
        ),
        current_pages=q2_pages,
    )


def test_real_pipeline_compares_five_guidance_items(
    guidance_report,
):
    assert len(
        guidance_report.changes
    ) == 5

    assert (
        guidance_report.introduced
        == ()
    )

    assert (
        guidance_report.withdrawn
        == ()
    )


def test_real_pipeline_finds_four_unchanged_items(
    guidance_report,
):
    assert len(
        guidance_report.unchanged
    ) == 4

    unchanged_metrics = {
        change.metric_id
        for change
        in guidance_report.unchanged
    }

    assert unchanged_metrics == {
        "organic_capex",
        "oil_gas_production_growth",
        "unit_production_cost_position",
        "maintenance_production_impact",
    }


def test_real_pipeline_finds_share_buyback_increase(
    guidance_report,
):
    assert len(
        guidance_report.changed
    ) == 1

    change = (
        guidance_report.changed[0]
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


def test_real_pipeline_uses_annual_buyback_programmes(
    guidance_report,
):
    change = (
        guidance_report.changed[0]
    )

    assert (
        change.previous.target_period
        == "FY 2026"
    )

    assert (
        change.current.target_period
        == "FY 2026"
    )

    assert (
        change.previous.qualifier
        == "up to"
    )

    assert (
        change.current.qualifier
        == "up to"
    )

    assert (
        "1,125"
        not in change.current.statement
    )


def test_real_pipeline_preserves_source_provenance(
    guidance_report,
):
    for change in (
        guidance_report.changes
    ):
        assert (
            change.previous.document_id
            == EQUINOR_Q1_2026.document_id
        )

        assert (
            change.current.document_id
            == EQUINOR_Q2_2026.document_id
        )

        assert (
            change.previous.page_number
            >= 1
        )

        assert (
            change.current.page_number
            >= 1
        )

        assert (
            change.previous.statement
        )

        assert (
            change.current.statement
        )


def test_real_formal_outlook_items_come_from_page_10(
    guidance_report,
):
    formal_metrics = {
        "organic_capex",
        "oil_gas_production_growth",
        "unit_production_cost_position",
        "maintenance_production_impact",
    }

    for change in (
        guidance_report.changes
    ):
        if (
            change.metric_id
            not in formal_metrics
        ):
            continue

        assert (
            change.previous.page_number
            == 10
        )

        assert (
            change.current.page_number
            == 10
        )

        assert (
            change.previous.section
            == "Outlook"
        )

        assert (
            change.current.section
            == "Outlook"
        )