from decimal import Decimal

from equitylens.guidance_pipeline import (
    build_aker_bp_guidance_report,
    extract_aker_bp_guidance,
)
from equitylens.parser import ParsedPage

Q1_DOCUMENT = "aker-bp-q1-2026-report"
Q2_DOCUMENT = "aker-bp-q2-2026-report"


def _q1_pages():
    return (
        ParsedPage(
            document_id=Q1_DOCUMENT,
            page_number=13,
            text=(
                "OUTLOOK "
                "Guidance for 2026 "
                "Aker BP provides financial guidance. "
                "Production: 370–400 mboepd "
                "Production cost: USD ~8 per boe "
                "Capex: USD 6.2-6.7 billion "
                "Exploration spend: USD ~400 million "
                "Abandonment spend: USD ~100 million "
                "Dividend: USD 0.6615 per share per quarter, "
                "annualised at USD 2.646 per share"
            ),
        ),
    )


def _q2_pages():
    return (
        ParsedPage(
            document_id=Q2_DOCUMENT,
            page_number=16,
            text=(
                "OUTLOOK "
                "Guidance for 2026 "
                "Aker BP provides the following financial "
                "guidance for 2026 "
                "(previous guidance in brackets): "
                "Production: 380-400 mboepd "
                "(370-400 mboepd) "
                "Production cost: USD ~8 per boe "
                "(no change) "
                "Capex: USD 6.8-7.2 billion "
                "(6.2-6.7 billion) "
                "Exploration spend: USD ~400 million "
                "(no change) "
                "Abandonment spend: USD ~100 million "
                "(no change) "
                "Dividend: USD 0.6615 per share per quarter, "
                "annualised at USD 2.646 per share "
                "(no change)"
            ),
        ),
    )


def test_extracts_six_supported_aker_bp_guidance_items():
    items = extract_aker_bp_guidance(
        document_id=Q1_DOCUMENT,
        pages=_q1_pages(),
    )

    assert len(items) == 6

    assert {
        item.metric_id
        for item in items
    } == {
        "production_guidance",
        "production_cost_guidance",
        "capex_guidance",
        "exploration_spend_guidance",
        "abandonment_spend_guidance",
        "dividend_guidance",
    }


def test_aker_bp_pipeline_accepts_single_use_page_iterable():
    pages = (
        page
        for page in _q1_pages()
    )

    items = extract_aker_bp_guidance(
        document_id=Q1_DOCUMENT,
        pages=pages,
    )

    assert len(items) == 6


def test_builds_aker_bp_guidance_report():
    report = build_aker_bp_guidance_report(
        previous_document_id=Q1_DOCUMENT,
        previous_pages=_q1_pages(),
        current_document_id=Q2_DOCUMENT,
        current_pages=_q2_pages(),
    )

    assert len(report.changes) == 6
    assert len(report.unchanged) == 4
    assert len(report.changed) == 2
    assert report.introduced == ()
    assert report.withdrawn == ()


def test_production_and_capex_are_changed_guidance():
    report = build_aker_bp_guidance_report(
        previous_document_id=Q1_DOCUMENT,
        previous_pages=_q1_pages(),
        current_document_id=Q2_DOCUMENT,
        current_pages=_q2_pages(),
    )

    changed_by_metric = {
        change.metric_id: change
        for change in report.changed
    }

    assert set(changed_by_metric) == {
        "production_guidance",
        "capex_guidance",
    }

    production = changed_by_metric[
        "production_guidance"
    ]

    assert production.change_type == "increased"

    assert (
        production.previous.numeric_lower_bound
        == Decimal(370)
    )

    assert (
        production.previous.numeric_upper_bound
        == Decimal(400)
    )

    assert (
        production.current.numeric_lower_bound
        == Decimal(380)
    )

    assert (
        production.current.numeric_upper_bound
        == Decimal(400)
    )

    capex = changed_by_metric[
        "capex_guidance"
    ]

    assert capex.change_type == "increased"

    assert (
        capex.previous.numeric_lower_bound
        == Decimal("6.2")
    )

    assert (
        capex.previous.numeric_upper_bound
        == Decimal("6.7")
    )

    assert (
        capex.current.numeric_lower_bound
        == Decimal("6.8")
    )

    assert (
        capex.current.numeric_upper_bound
        == Decimal("7.2")
    )


def test_remaining_aker_bp_guidance_is_unchanged():
    report = build_aker_bp_guidance_report(
        previous_document_id=Q1_DOCUMENT,
        previous_pages=_q1_pages(),
        current_document_id=Q2_DOCUMENT,
        current_pages=_q2_pages(),
    )

    unchanged_metric_ids = {
        change.metric_id
        for change in report.unchanged
    }

    assert unchanged_metric_ids == {
        "production_cost_guidance",
        "exploration_spend_guidance",
        "abandonment_spend_guidance",
        "dividend_guidance",
    }