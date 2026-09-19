from decimal import Decimal

from equitylens.guidance_pipeline import (
    build_equinor_guidance_report,
    extract_equinor_guidance,
)
from equitylens.parser import ParsedPage

Q1_DOCUMENT = "equinor-q1-2026"
Q2_DOCUMENT = "equinor-q2-2026"


def _q1_pages():
    return (
        ParsedPage(
            document_id=Q1_DOCUMENT,
            page_number=6,
            text=(
                "Capital distribution. "
                "The expected share buy-back programme "
                "for 2026 is up to USD 1.5 billion."
            ),
        ),
        ParsedPage(
            document_id=Q1_DOCUMENT,
            page_number=10,
            text=(
                "Outlook "
                "Organic capital expenditures* are "
                "estimated at around USD 13 billion "
                "for 2026. "
                "Oil & gas production for 2026 is "
                "estimated to grow around 3% compared "
                "to 2025 level. "
                "Equinor’s ambition is to keep the "
                "unit of production cost in the top "
                "quartile of its peer group. "
                "Scheduled maintenance activity is "
                "estimated to reduce equity production "
                "by around 35 mboe per day for the "
                "full year of 2026."
            ),
        ),
    )


def _q2_pages():
    return (
        ParsedPage(
            document_id=Q2_DOCUMENT,
            page_number=3,
            text=(
                "Production growth of 3%. "
                "Third tranche of the share buy-back "
                "of up to USD 1,125 million."
            ),
        ),
        ParsedPage(
            document_id=Q2_DOCUMENT,
            page_number=6,
            text=(
                "Capital distribution. "
                "At the Capital Markets Day Equinor "
                "announced an intention to increase "
                "the share buy-back programme. "
                "This brings the total expected "
                "programme for 2026 to up to "
                "USD 3 billion. "
                "The board has decided to initiate "
                "a third tranche of the share "
                "buy-back programme for 2026 of up "
                "to USD 1,125 million."
            ),
        ),
        ParsedPage(
            document_id=Q2_DOCUMENT,
            page_number=10,
            text=(
                "Outlook "
                "Organic capital expenditures* are "
                "estimated at around USD 13 billion "
                "for 2026. "
                "Oil & gas production for 2026 is "
                "estimated to grow around 3% compared "
                "to 2025 level. "
                "Equinor’s ambition is to keep the "
                "unit of production cost in the top "
                "quartile of its peer group. "
                "Scheduled maintenance activity is "
                "estimated to reduce equity production "
                "by around 35 mboe per day for the "
                "full year of 2026."
            ),
        ),
    )


def test_extracts_five_supported_guidance_items():
    items = extract_equinor_guidance(
        document_id=Q1_DOCUMENT,
        pages=_q1_pages(),
    )

    assert len(items) == 5

    assert {
        item.metric_id
        for item in items
    } == {
        "organic_capex",
        "oil_gas_production_growth",
        "unit_production_cost_position",
        "maintenance_production_impact",
        "share_buyback",
    }


def test_pipeline_accepts_single_use_page_iterable():
    pages = (
        page
        for page in _q1_pages()
    )

    items = extract_equinor_guidance(
        document_id=Q1_DOCUMENT,
        pages=pages,
    )

    assert len(items) == 5


def test_builds_combined_guidance_report():
    report = (
        build_equinor_guidance_report(
            previous_document_id=(
                Q1_DOCUMENT
            ),
            previous_pages=_q1_pages(),
            current_document_id=(
                Q2_DOCUMENT
            ),
            current_pages=_q2_pages(),
        )
    )

    assert len(report.changes) == 5
    assert len(report.unchanged) == 4
    assert len(report.changed) == 1
    assert report.introduced == ()
    assert report.withdrawn == ()


def test_share_buyback_is_only_changed_guidance():
    report = (
        build_equinor_guidance_report(
            previous_document_id=(
                Q1_DOCUMENT
            ),
            previous_pages=_q1_pages(),
            current_document_id=(
                Q2_DOCUMENT
            ),
            current_pages=_q2_pages(),
        )
    )

    change = report.changed[0]

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


def test_historical_growth_and_tranche_are_not_promoted():
    report = (
        build_equinor_guidance_report(
            previous_document_id=(
                Q1_DOCUMENT
            ),
            previous_pages=_q1_pages(),
            current_document_id=(
                Q2_DOCUMENT
            ),
            current_pages=_q2_pages(),
        )
    )

    current_by_metric = {
        change.metric_id: change.current
        for change in report.changes
    }

    production = current_by_metric[
        "oil_gas_production_growth"
    ]

    buyback = current_by_metric[
        "share_buyback"
    ]

    assert (
        "compared to 2025"
        in production.statement.lower()
    )

    assert (
        buyback.numeric_value
        == Decimal(3)
    )

    assert (
        "1,125"
        not in buyback.statement
    )