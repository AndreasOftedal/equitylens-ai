from decimal import Decimal

import pytest

from equitylens.aker_bp_guidance_extractor import (
    extract_aker_bp_formal_outlook_guidance,
)
from equitylens.documents import (
    AKER_BP_Q1_2026,
    AKER_BP_Q2_2026,
)
from equitylens.guidance import compare_guidance
from equitylens.parser import parse_pdf

pytestmark = pytest.mark.integration


def _extract(document):
    pages = parse_pdf(
        document_id=document.document_id,
        pdf_path=document.local_path,
    )

    return {
        item.metric_id: item
        for item in (
            extract_aker_bp_formal_outlook_guidance(
                document_id=document.document_id,
                pages=pages,
            )
        )
    }


def test_real_aker_bp_reports_extract_all_guidance():
    q1 = _extract(
        AKER_BP_Q1_2026
    )

    q2 = _extract(
        AKER_BP_Q2_2026
    )

    expected_metric_ids = {
        "production_guidance",
        "production_cost_guidance",
        "capex_guidance",
        "exploration_spend_guidance",
        "abandonment_spend_guidance",
        "dividend_guidance",
    }

    assert set(q1) == expected_metric_ids
    assert set(q2) == expected_metric_ids


def test_real_aker_bp_production_guidance_is_extracted():
    q1 = _extract(
        AKER_BP_Q1_2026
    )

    q2 = _extract(
        AKER_BP_Q2_2026
    )

    q1_production = q1[
        "production_guidance"
    ]

    q2_production = q2[
        "production_guidance"
    ]

    assert (
        q1_production.numeric_lower_bound
        == Decimal(370)
    )

    assert (
        q1_production.numeric_upper_bound
        == Decimal(400)
    )

    assert (
        q2_production.numeric_lower_bound
        == Decimal(380)
    )

    assert (
        q2_production.numeric_upper_bound
        == Decimal(400)
    )

    assert q1_production.page_number == 13
    assert q2_production.page_number == 16

    assert (
        compare_guidance(
            q1_production,
            q2_production,
        ).change_type
        == "increased"
    )


def test_real_aker_bp_capex_guidance_increased():
    q1 = _extract(
        AKER_BP_Q1_2026
    )

    q2 = _extract(
        AKER_BP_Q2_2026
    )

    q1_capex = q1[
        "capex_guidance"
    ]

    q2_capex = q2[
        "capex_guidance"
    ]

    assert (
        q1_capex.numeric_lower_bound
        == Decimal("6.2")
    )

    assert (
        q1_capex.numeric_upper_bound
        == Decimal("6.7")
    )

    assert (
        q2_capex.numeric_lower_bound
        == Decimal("6.8")
    )

    assert (
        q2_capex.numeric_upper_bound
        == Decimal("7.2")
    )

    assert (
        compare_guidance(
            q1_capex,
            q2_capex,
        ).change_type
        == "increased"
    )


def test_real_aker_bp_unchanged_scalar_guidance():
    q1 = _extract(
        AKER_BP_Q1_2026
    )

    q2 = _extract(
        AKER_BP_Q2_2026
    )

    expected_values = {
        "production_cost_guidance": (
            Decimal(8),
            "USD per boe",
        ),
        "exploration_spend_guidance": (
            Decimal(400),
            "USD million",
        ),
        "abandonment_spend_guidance": (
            Decimal(100),
            "USD million",
        ),
        "dividend_guidance": (
            Decimal("0.6615"),
            "USD per share per quarter",
        ),
    }

    for metric_id, (
        expected_value,
        expected_unit,
    ) in expected_values.items():
        assert (
            q1[metric_id].numeric_value
            == expected_value
        )

        assert (
            q2[metric_id].numeric_value
            == expected_value
        )

        assert (
            q1[metric_id].unit
            == expected_unit
        )

        assert (
            q2[metric_id].unit
            == expected_unit
        )

        assert (
            compare_guidance(
                q1[metric_id],
                q2[metric_id],
            ).change_type
            == "unchanged"
        )


def test_real_aker_bp_guidance_preserves_document_provenance():
    q1 = _extract(
        AKER_BP_Q1_2026
    )

    q2 = _extract(
        AKER_BP_Q2_2026
    )

    assert all(
        item.document_id
        == AKER_BP_Q1_2026.document_id
        for item in q1.values()
    )

    assert all(
        item.document_id
        == AKER_BP_Q2_2026.document_id
        for item in q2.values()
    )

    assert all(
        item.page_number == 13
        for item in q1.values()
    )

    assert all(
        item.page_number == 16
        for item in q2.values()
    )

    assert all(
        item.target_period == "FY 2026"
        for item in (
            *q1.values(),
            *q2.values(),
        )
    )