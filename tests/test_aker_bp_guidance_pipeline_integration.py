from decimal import Decimal

from equitylens.documents import (
    AKER_BP_Q1_2026,
    AKER_BP_Q2_2026,
)
from equitylens.guidance_pipeline import (
    build_aker_bp_guidance_report,
)
from equitylens.parser import parse_pdf


def _parse(document):
    return parse_pdf(
        document_id=document.document_id,
        pdf_path=document.local_path,
    )


def test_real_aker_bp_guidance_pipeline_builds_expected_report():
    report = build_aker_bp_guidance_report(
        previous_document_id=(
            AKER_BP_Q1_2026.document_id
        ),
        previous_pages=_parse(
            AKER_BP_Q1_2026
        ),
        current_document_id=(
            AKER_BP_Q2_2026.document_id
        ),
        current_pages=_parse(
            AKER_BP_Q2_2026
        ),
    )

    assert len(report.changes) == 6
    assert len(report.changed) == 2
    assert len(report.unchanged) == 4
    assert report.introduced == ()
    assert report.withdrawn == ()


def test_real_aker_bp_pipeline_detects_production_and_capex_increases():
    report = build_aker_bp_guidance_report(
        previous_document_id=(
            AKER_BP_Q1_2026.document_id
        ),
        previous_pages=_parse(
            AKER_BP_Q1_2026
        ),
        current_document_id=(
            AKER_BP_Q2_2026.document_id
        ),
        current_pages=_parse(
            AKER_BP_Q2_2026
        ),
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


def test_real_aker_bp_pipeline_preserves_guidance_provenance():
    report = build_aker_bp_guidance_report(
        previous_document_id=(
            AKER_BP_Q1_2026.document_id
        ),
        previous_pages=_parse(
            AKER_BP_Q1_2026
        ),
        current_document_id=(
            AKER_BP_Q2_2026.document_id
        ),
        current_pages=_parse(
            AKER_BP_Q2_2026
        ),
    )

    for change in report.changes:
        assert (
            change.previous.document_id
            == AKER_BP_Q1_2026.document_id
        )

        assert (
            change.current.document_id
            == AKER_BP_Q2_2026.document_id
        )

        assert (
            change.previous.page_number
            == 13
        )

        assert (
            change.current.page_number
            == 16
        )

        assert (
            change.target_period
            == "FY 2026"
        )