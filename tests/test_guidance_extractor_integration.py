from decimal import Decimal

import pytest

from equitylens.documents import (
    EQUINOR_Q1_2026,
    EQUINOR_Q2_2026,
)
from equitylens.guidance import compare_guidance
from equitylens.guidance_extractor import (
    extract_equinor_formal_outlook_guidance,
)
from equitylens.parser import parse_pdf

pytestmark = pytest.mark.integration


@pytest.fixture(scope="module")
def q1_guidance():
    pages = parse_pdf(
        document_id=EQUINOR_Q1_2026.document_id,
        pdf_path=EQUINOR_Q1_2026.local_path,
    )

    return (
        extract_equinor_formal_outlook_guidance(
            document_id=EQUINOR_Q1_2026.document_id,
            pages=pages,
        )
    )


@pytest.fixture(scope="module")
def q2_guidance():
    pages = parse_pdf(
        document_id=EQUINOR_Q2_2026.document_id,
        pdf_path=EQUINOR_Q2_2026.local_path,
    )

    return (
        extract_equinor_formal_outlook_guidance(
            document_id=EQUINOR_Q2_2026.document_id,
            pages=pages,
        )
    )


def _by_metric(items):
    return {
        item.metric_id: item
        for item in items
    }


def test_q1_extracts_expected_formal_outlook_guidance(
    q1_guidance,
):
    items = _by_metric(
        q1_guidance
    )

    assert set(items) == {
        "organic_capex",
        "oil_gas_production_growth",
        "unit_production_cost_position",
        "maintenance_production_impact",
    }

    assert (
        items["organic_capex"].numeric_value
        == Decimal(13)
    )

    assert (
        items[
            "oil_gas_production_growth"
        ].numeric_value
        == Decimal(3)
    )

    assert (
        items[
            "maintenance_production_impact"
        ].numeric_value
        == Decimal(35)
    )

    assert (
        items[
            "unit_production_cost_position"
        ].qualitative_value
        == "top quartile of peer group"
    )


def test_q2_extracts_expected_formal_outlook_guidance(
    q2_guidance,
):
    items = _by_metric(
        q2_guidance
    )

    assert set(items) == {
        "organic_capex",
        "oil_gas_production_growth",
        "unit_production_cost_position",
        "maintenance_production_impact",
    }

    assert (
        items["organic_capex"].numeric_value
        == Decimal(13)
    )

    assert (
        items[
            "oil_gas_production_growth"
        ].numeric_value
        == Decimal(3)
    )

    assert (
        items[
            "maintenance_production_impact"
        ].numeric_value
        == Decimal(35)
    )

    assert (
        items[
            "unit_production_cost_position"
        ].qualitative_value
        == "top quartile of peer group"
    )


def test_real_guidance_preserves_outlook_provenance(
    q1_guidance,
    q2_guidance,
):
    for item in (
        *q1_guidance,
        *q2_guidance,
    ):
        assert item.page_number == 10
        assert item.section == "Outlook"
        assert item.statement


def test_q1_to_q2_formal_outlook_is_unchanged(
    q1_guidance,
    q2_guidance,
):
    q1 = _by_metric(
        q1_guidance
    )

    q2 = _by_metric(
        q2_guidance
    )

    changes = {
        metric_id: compare_guidance(
            q1[metric_id],
            q2[metric_id],
        )
        for metric_id in q1
    }

    assert all(
        change.change_type
        == "unchanged"
        for change in changes.values()
    )


def test_production_growth_guidance_is_not_historical_q2_growth(
    q2_guidance,
):
    item = _by_metric(
        q2_guidance
    )[
        "oil_gas_production_growth"
    ]

    assert (
        item.numeric_value
        == Decimal(3)
    )

    assert (
        "for 2026"
        in item.statement.lower()
    )

    assert (
        "compared to 2025"
        in item.statement.lower()
    )