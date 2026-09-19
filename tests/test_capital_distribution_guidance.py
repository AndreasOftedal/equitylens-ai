from decimal import Decimal

import pytest

from equitylens.capital_distribution_guidance import (
    extract_equinor_share_buyback_guidance,
)
from equitylens.parser import ParsedPage

DOCUMENT_ID = "equinor-report"


def _page(
    page_number: int,
    text: str,
) -> ParsedPage:
    return ParsedPage(
        document_id=DOCUMENT_ID,
        page_number=page_number,
        text=text,
    )


def test_extracts_q1_style_share_buyback_guidance():
    item = (
        extract_equinor_share_buyback_guidance(
            document_id=DOCUMENT_ID,
            pages=(
                _page(
                    6,
                    (
                        "Capital distribution. "
                        "The expected share buy-back "
                        "programme for 2026 is up to "
                        "USD 1.5 billion."
                    ),
                ),
            ),
        )
    )

    assert (
        item.numeric_value
        == Decimal("1.5")
    )

    assert item.target_period == "FY 2026"
    assert item.unit == "USD billion"
    assert item.qualifier == "up to"

    assert (
        item.category
        == "capital_distribution"
    )


def test_extracts_q2_style_share_buyback_guidance():
    item = (
        extract_equinor_share_buyback_guidance(
            document_id=DOCUMENT_ID,
            pages=(
                _page(
                    6,
                    (
                        "At the Capital Markets Day "
                        "Equinor announced an intention "
                        "to increase the programme. "
                        "This brings the total expected "
                        "programme for 2026 to up to "
                        "USD 3 billion."
                    ),
                ),
            ),
        )
    )

    assert (
        item.numeric_value
        == Decimal(3)
    )

    assert item.target_period == "FY 2026"
    assert item.qualifier == "up to"


def test_individual_tranche_is_not_mistaken_for_annual_guidance():
    item = (
        extract_equinor_share_buyback_guidance(
            document_id=DOCUMENT_ID,
            pages=(
                _page(
                    6,
                    (
                        "This brings the total expected "
                        "programme for 2026 to up to "
                        "USD 3 billion. "
                        "The board has decided to initiate "
                        "a third tranche of the share "
                        "buy-back programme for 2026 "
                        "of up to USD 1,125 million."
                    ),
                ),
            ),
        )
    )

    assert (
        item.numeric_value
        == Decimal(3)
    )

    assert (
        "1,125"
        not in item.statement
    )


def test_duplicate_same_guidance_uses_earliest_page():
    item = (
        extract_equinor_share_buyback_guidance(
            document_id=DOCUMENT_ID,
            pages=(
                _page(
                    9,
                    (
                        "The expected share buy-back "
                        "programme for 2026 is up to "
                        "USD 1.5 billion."
                    ),
                ),
                _page(
                    6,
                    (
                        "The expected share buy-back "
                        "programme for 2026 is up to "
                        "USD 1.5 billion."
                    ),
                ),
            ),
        )
    )

    assert item.page_number == 6


def test_conflicting_annual_guidance_is_rejected():
    with pytest.raises(
        ValueError,
        match=(
            "Conflicting full-year share buy-back "
            "guidance detected"
        ),
    ):
        extract_equinor_share_buyback_guidance(
            document_id=DOCUMENT_ID,
            pages=(
                _page(
                    6,
                    (
                        "The expected share buy-back "
                        "programme for 2026 is up to "
                        "USD 1.5 billion."
                    ),
                ),
                _page(
                    9,
                    (
                        "This brings the total expected "
                        "programme for 2026 to up to "
                        "USD 3 billion."
                    ),
                ),
            ),
        )


def test_missing_annual_guidance_is_rejected():
    with pytest.raises(
        ValueError,
        match=(
            "Expected full-year share buy-back "
            "guidance was not found"
        ),
    ):
        extract_equinor_share_buyback_guidance(
            document_id=DOCUMENT_ID,
            pages=(
                _page(
                    6,
                    (
                        "The third tranche of the "
                        "share buy-back programme is "
                        "up to USD 1,125 million."
                    ),
                ),
            ),
        )


def test_mismatched_document_is_rejected():
    page = ParsedPage(
        document_id="different-document",
        page_number=6,
        text="Capital distribution.",
    )

    with pytest.raises(
        ValueError,
        match=(
            "Parsed page document_id does not match"
        ),
    ):
        extract_equinor_share_buyback_guidance(
            document_id=DOCUMENT_ID,
            pages=(page,),
        )