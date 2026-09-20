from decimal import Decimal

from equitylens.aker_bp_guidance_extractor import (
    extract_aker_bp_formal_outlook_guidance,
)
from equitylens.parser import ParsedPage

Q1_DOCUMENT_ID = "aker-bp-q1-2026-report"
Q2_DOCUMENT_ID = "aker-bp-q2-2026-report"


Q1_TEXT = """
OUTLOOK
Guidance for 2026
In connection with Aker BP’s reporting for the full year 2025,
the company provided the following financial guidance for 2026,
which remains unchanged:
Production: 370–400 mboepd
Production cost: USD ~8 per boe
Capex: USD 6.2-6.7 billion
Exploration spend: USD ~400 million
Abandonment spend: USD ~100 million
Dividend: USD 0.6615 per share per quarter,
annualised at USD 2.646 per share
"""


Q2_TEXT = """
OUTLOOK
Guidance for 2026
Aker BP provides the following financial guidance for 2026
(previous guidance in brackets):
Production: 380-400 mboepd (370-400 mboepd)
Production cost: USD ~8 per boe (no change)
Capex: USD 6.8-7.2 billion (6.2-6.7 billion)
Exploration spend: USD ~400 million (no change)
Abandonment spend: USD ~100 million (no change)
Dividend: USD 0.6615 per share per quarter,
annualised at USD 2.646 per share (no change)
"""


def _page(
    *,
    document_id: str,
    page_number: int,
    text: str,
) -> ParsedPage:
    return ParsedPage(
        document_id=document_id,
        page_number=page_number,
        text=text,
    )


def _items_by_metric(
    items,
):
    return {
        item.metric_id: item
        for item in items
    }


def test_q1_extracts_expected_guidance_metrics():
    items = extract_aker_bp_formal_outlook_guidance(
        document_id=Q1_DOCUMENT_ID,
        pages=(
            _page(
                document_id=Q1_DOCUMENT_ID,
                page_number=13,
                text=Q1_TEXT,
            ),
        ),
    )

    assert tuple(
        item.metric_id
        for item in items
    ) == (
        "production_guidance",
        "production_cost_guidance",
        "capex_guidance",
        "exploration_spend_guidance",
        "abandonment_spend_guidance",
        "dividend_guidance",
    )


def test_q1_production_range_is_extracted():
    items = _items_by_metric(
        extract_aker_bp_formal_outlook_guidance(
            document_id=Q1_DOCUMENT_ID,
            pages=(
                _page(
                    document_id=Q1_DOCUMENT_ID,
                    page_number=13,
                    text=Q1_TEXT,
                ),
            ),
        )
    )

    production = items[
        "production_guidance"
    ]

    assert (
        production.numeric_lower_bound
        == Decimal(370)
    )

    assert (
        production.numeric_upper_bound
        == Decimal(400)
    )

    assert production.numeric_value is None
    assert production.unit == "mboepd"
    assert production.target_period == "FY 2026"
    assert production.page_number == 13


def test_q2_production_uses_current_range_not_bracketed_previous_range():
    items = _items_by_metric(
        extract_aker_bp_formal_outlook_guidance(
            document_id=Q2_DOCUMENT_ID,
            pages=(
                _page(
                    document_id=Q2_DOCUMENT_ID,
                    page_number=16,
                    text=Q2_TEXT,
                ),
            ),
        )
    )

    production = items[
        "production_guidance"
    ]

    assert (
        production.numeric_lower_bound
        == Decimal(380)
    )

    assert (
        production.numeric_upper_bound
        == Decimal(400)
    )

    assert production.unit == "mboepd"
    assert production.page_number == 16


def test_production_cost_is_extracted_as_scalar_guidance():
    for document_id, page_number, text in (
        (
            Q1_DOCUMENT_ID,
            13,
            Q1_TEXT,
        ),
        (
            Q2_DOCUMENT_ID,
            16,
            Q2_TEXT,
        ),
    ):
        items = _items_by_metric(
            extract_aker_bp_formal_outlook_guidance(
                document_id=document_id,
                pages=(
                    _page(
                        document_id=document_id,
                        page_number=page_number,
                        text=text,
                    ),
                ),
            )
        )

        cost = items[
            "production_cost_guidance"
        ]

        assert (
            cost.numeric_value
            == Decimal(8)
        )

        assert (
            cost.unit
            == "USD per boe"
        )

        assert (
            cost.qualifier
            == "approximately"
        )


def test_capex_ranges_are_extracted():
    q1 = _items_by_metric(
        extract_aker_bp_formal_outlook_guidance(
            document_id=Q1_DOCUMENT_ID,
            pages=(
                _page(
                    document_id=Q1_DOCUMENT_ID,
                    page_number=13,
                    text=Q1_TEXT,
                ),
            ),
        )
    )

    q2 = _items_by_metric(
        extract_aker_bp_formal_outlook_guidance(
            document_id=Q2_DOCUMENT_ID,
            pages=(
                _page(
                    document_id=Q2_DOCUMENT_ID,
                    page_number=16,
                    text=Q2_TEXT,
                ),
            ),
        )
    )

    assert (
        q1["capex_guidance"]
        .numeric_lower_bound
        == Decimal("6.2")
    )

    assert (
        q1["capex_guidance"]
        .numeric_upper_bound
        == Decimal("6.7")
    )

    assert (
        q2["capex_guidance"]
        .numeric_lower_bound
        == Decimal("6.8")
    )

    assert (
        q2["capex_guidance"]
        .numeric_upper_bound
        == Decimal("7.2")
    )

    assert (
        q1["capex_guidance"].unit
        == "USD billion"
    )

    assert (
        q2["capex_guidance"].unit
        == "USD billion"
    )


def test_spend_guidance_is_extracted():
    items = _items_by_metric(
        extract_aker_bp_formal_outlook_guidance(
            document_id=Q2_DOCUMENT_ID,
            pages=(
                _page(
                    document_id=Q2_DOCUMENT_ID,
                    page_number=16,
                    text=Q2_TEXT,
                ),
            ),
        )
    )

    exploration = items[
        "exploration_spend_guidance"
    ]

    abandonment = items[
        "abandonment_spend_guidance"
    ]

    assert (
        exploration.numeric_value
        == Decimal(400)
    )

    assert (
        exploration.unit
        == "USD million"
    )

    assert (
        exploration.qualifier
        == "approximately"
    )

    assert (
        abandonment.numeric_value
        == Decimal(100)
    )

    assert (
        abandonment.unit
        == "USD million"
    )

    assert (
        abandonment.qualifier
        == "approximately"
    )


def test_dividend_guidance_uses_quarterly_value():
    items = _items_by_metric(
        extract_aker_bp_formal_outlook_guidance(
            document_id=Q2_DOCUMENT_ID,
            pages=(
                _page(
                    document_id=Q2_DOCUMENT_ID,
                    page_number=16,
                    text=Q2_TEXT,
                ),
            ),
        )
    )

    dividend = items[
        "dividend_guidance"
    ]

    assert (
        dividend.numeric_value
        == Decimal("0.6615")
    )

    assert (
        dividend.unit
        == "USD per share per quarter"
    )

    assert dividend.target_period == "FY 2026"


def test_all_items_preserve_outlook_provenance():
    items = extract_aker_bp_formal_outlook_guidance(
        document_id=Q2_DOCUMENT_ID,
        pages=(
            _page(
                document_id=Q2_DOCUMENT_ID,
                page_number=16,
                text=Q2_TEXT,
            ),
        ),
    )

    assert all(
        item.document_id
        == Q2_DOCUMENT_ID
        for item in items
    )

    assert all(
        item.page_number == 16
        for item in items
    )

    assert all(
        item.section == "Outlook"
        for item in items
    )

    assert all(
        item.target_period == "FY 2026"
        for item in items
    )


def test_non_outlook_page_is_ignored():
    items = extract_aker_bp_formal_outlook_guidance(
        document_id=Q2_DOCUMENT_ID,
        pages=(
            _page(
                document_id=Q2_DOCUMENT_ID,
                page_number=7,
                text=(
                    "Production was 383.6 mboepd "
                    "during the second quarter."
                ),
            ),
        ),
        require_complete=False,
    )

    assert items == ()