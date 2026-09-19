from decimal import Decimal

import pytest

from equitylens.guidance_extractor import (
    extract_equinor_formal_outlook_guidance,
)
from equitylens.parser import ParsedPage

DOCUMENT_ID = "equinor-q1-2026"


def _outlook_page() -> ParsedPage:
    return ParsedPage(
        document_id=DOCUMENT_ID,
        page_number=10,
        text=(
            "Outlook\n"
            "Organic capital expenditures* are estimated "
            "at around USD 13 billion for 2026.\n"
            "Oil & gas production for 2026 is estimated "
            "to grow around 3% compared to 2025 level.\n"
            "Equinor’s ambition is to keep the unit of "
            "production cost in the top quartile of its "
            "peer group.\n"
            "Scheduled maintenance activity is estimated "
            "to reduce equity production by around "
            "35 mboe per day for the full year of 2026."
        ),
    )


def _historical_page() -> ParsedPage:
    return ParsedPage(
        document_id=DOCUMENT_ID,
        page_number=3,
        text=(
            "Strong financial results. "
            "Production growth of 9% from strong "
            "operational performance."
        ),
    )


def _items_by_metric():
    items = (
        extract_equinor_formal_outlook_guidance(
            document_id=DOCUMENT_ID,
            pages=(
                _historical_page(),
                _outlook_page(),
            ),
        )
    )

    return {
        item.metric_id: item
        for item in items
    }


def test_extracts_four_formal_outlook_items():
    items = _items_by_metric()

    assert set(items) == {
        "organic_capex",
        "oil_gas_production_growth",
        "unit_production_cost_position",
        "maintenance_production_impact",
    }


def test_extracts_capex_guidance():
    item = _items_by_metric()[
        "organic_capex"
    ]

    assert (
        item.numeric_value
        == Decimal(13)
    )
    assert item.unit == "USD billion"
    assert item.qualifier == "around"
    assert item.target_period == "FY 2026"


def test_extracts_production_growth_guidance():
    item = _items_by_metric()[
        "oil_gas_production_growth"
    ]

    assert (
        item.numeric_value
        == Decimal(3)
    )
    assert item.unit == "percent"
    assert item.qualifier == "around"
    assert item.target_period == "FY 2026"


def test_extracts_cost_position_as_ongoing_ambition():
    item = _items_by_metric()[
        "unit_production_cost_position"
    ]

    assert item.numeric_value is None

    assert (
        item.qualitative_value
        == "top quartile of peer group"
    )

    assert item.qualifier == "ambition"
    assert item.target_period == "ongoing"


def test_extracts_maintenance_guidance():
    item = _items_by_metric()[
        "maintenance_production_impact"
    ]

    assert (
        item.numeric_value
        == Decimal(35)
    )

    assert item.unit == "mboe per day"
    assert item.qualifier == "around"
    assert item.target_period == "FY 2026"


def test_preserves_guidance_provenance():
    items = _items_by_metric()

    for item in items.values():
        assert (
            item.document_id
            == DOCUMENT_ID
        )

        assert item.page_number == 10
        assert item.section == "Outlook"
        assert item.statement


def test_historical_growth_statement_is_not_extracted():
    items = _items_by_metric()

    production = items[
        "oil_gas_production_growth"
    ]

    assert (
        production.numeric_value
        == Decimal(3)
    )

    assert (
        "Production growth of 9%"
        not in production.statement
    )


def test_missing_formal_guidance_is_rejected():
    incomplete_page = ParsedPage(
        document_id=DOCUMENT_ID,
        page_number=10,
        text=(
            "Outlook "
            "Organic capital expenditures* are estimated "
            "at around USD 13 billion for 2026."
        ),
    )

    with pytest.raises(
        ValueError,
        match=(
            "Missing expected formal Outlook guidance"
        ),
    ):
        extract_equinor_formal_outlook_guidance(
            document_id=DOCUMENT_ID,
            pages=(
                incomplete_page,
            ),
        )


def test_mismatched_page_document_is_rejected():
    page = ParsedPage(
        document_id="different-document",
        page_number=10,
        text="Outlook",
    )

    with pytest.raises(
        ValueError,
        match=(
            "Parsed page document_id does not match"
        ),
    ):
        extract_equinor_formal_outlook_guidance(
            document_id=DOCUMENT_ID,
            pages=(page,),
        )