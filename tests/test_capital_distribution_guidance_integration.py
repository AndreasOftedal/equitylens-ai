from decimal import Decimal

import pytest

from equitylens.capital_distribution_guidance import (
    extract_equinor_share_buyback_guidance,
)
from equitylens.documents import (
    EQUINOR_Q1_2026,
    EQUINOR_Q2_2026,
)
from equitylens.guidance import compare_guidance
from equitylens.parser import parse_pdf

pytestmark = pytest.mark.integration


@pytest.fixture(scope="module")
def q1_buyback_guidance():
    pages = parse_pdf(
        document_id=EQUINOR_Q1_2026.document_id,
        pdf_path=EQUINOR_Q1_2026.local_path,
    )

    return (
        extract_equinor_share_buyback_guidance(
            document_id=EQUINOR_Q1_2026.document_id,
            pages=pages,
        )
    )


@pytest.fixture(scope="module")
def q2_buyback_guidance():
    pages = parse_pdf(
        document_id=EQUINOR_Q2_2026.document_id,
        pdf_path=EQUINOR_Q2_2026.local_path,
    )

    return (
        extract_equinor_share_buyback_guidance(
            document_id=EQUINOR_Q2_2026.document_id,
            pages=pages,
        )
    )


def test_q1_extracts_annual_share_buyback_guidance(
    q1_buyback_guidance,
):
    assert (
        q1_buyback_guidance.numeric_value
        == Decimal("1.5")
    )

    assert (
        q1_buyback_guidance.target_period
        == "FY 2026"
    )

    assert (
        q1_buyback_guidance.qualifier
        == "up to"
    )

    assert (
        q1_buyback_guidance.category
        == "capital_distribution"
    )


def test_q2_extracts_annual_share_buyback_guidance(
    q2_buyback_guidance,
):
    assert (
        q2_buyback_guidance.numeric_value
        == Decimal(3)
    )

    assert (
        q2_buyback_guidance.target_period
        == "FY 2026"
    )

    assert (
        q2_buyback_guidance.qualifier
        == "up to"
    )


def test_q2_does_not_extract_third_tranche_as_annual_guidance(
    q2_buyback_guidance,
):
    assert (
        q2_buyback_guidance.numeric_value
        != Decimal("1.125")
    )

    assert (
        "1,125"
        not in q2_buyback_guidance.statement
    )


def test_q1_to_q2_share_buyback_guidance_increased(
    q1_buyback_guidance,
    q2_buyback_guidance,
):
    change = compare_guidance(
        q1_buyback_guidance,
        q2_buyback_guidance,
    )

    assert (
        change.change_type
        == "increased"
    )

    assert (
        change.qualifier_changed
        is False
    )

    assert (
        change.category_changed
        is False
    )


def test_share_buyback_guidance_preserves_provenance(
    q1_buyback_guidance,
    q2_buyback_guidance,
):
    assert (
        q1_buyback_guidance.document_id
        == EQUINOR_Q1_2026.document_id
    )

    assert (
        q2_buyback_guidance.document_id
        == EQUINOR_Q2_2026.document_id
    )

    assert (
        q1_buyback_guidance.page_number
        >= 1
    )

    assert (
        q2_buyback_guidance.page_number
        >= 1
    )

    assert (
        q1_buyback_guidance.statement
    )

    assert (
        q2_buyback_guidance.statement
    )