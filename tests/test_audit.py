from decimal import Decimal

import pytest

from equitylens.audit import build_change_audit_trail
from equitylens.calculations import calculate_percentage_change
from equitylens.models import EvidenceRef, FinancialFact


def _build_q1_fact() -> FinancialFact:
    return FinancialFact(
        fact_id="equinor-adjusted-operating-income-q1-2026",
        metric="Adjusted operating income*",
        period="Q1 2026",
        value=Decimal(9770),
        unit="USD million",
        evidence=EvidenceRef(
            document_id="equinor-q1-2026-financial-statements-and-review",
            page_number=4,
            table_number=1,
            row_label="Adjusted operating income*",
            column_label="Quarters.Q1 2026",
        ),
    )


def _build_q2_fact() -> FinancialFact:
    return FinancialFact(
        fact_id="equinor-adjusted-operating-income-q2-2026",
        metric="Adjusted operating income*",
        period="Q2 2026",
        value=Decimal(11482),
        unit="USD million",
        evidence=EvidenceRef(
            document_id="equinor-q2-2026-financial-statements-and-review",
            page_number=4,
            table_number=1,
            row_label="Adjusted operating income*",
            column_label="Q2 2026",
        ),
    )


def test_build_change_audit_trail_preserves_complete_lineage():
    q1_fact = _build_q1_fact()
    q2_fact = _build_q2_fact()

    change = calculate_percentage_change(
        current=q2_fact,
        comparison=q1_fact,
    )

    audit_trail = build_change_audit_trail(
        change=change,
        source_facts=(
            q1_fact,
            q2_fact,
        ),
    )

    assert audit_trail.claim == (
        "Adjusted operating income increased 17.5% "
        "from Q1 2026 to Q2 2026."
    )

    assert audit_trail.direction == "increase"

    assert audit_trail.calculation.absolute_change == Decimal(1712)
    assert audit_trail.calculation.percentage_change == Decimal("17.5")

    assert audit_trail.source_facts[0].fact_id == q1_fact.fact_id
    assert audit_trail.source_facts[1].fact_id == q2_fact.fact_id

    assert (
        audit_trail.source_facts[0].evidence.document_id
        == "equinor-q1-2026-financial-statements-and-review"
    )

    assert (
        audit_trail.source_facts[1].evidence.document_id
        == "equinor-q2-2026-financial-statements-and-review"
    )

    assert audit_trail.source_facts[0].evidence.page_number == 4
    assert audit_trail.source_facts[1].evidence.page_number == 4


def test_build_change_audit_trail_rejects_wrong_lineage():
    q1_fact = _build_q1_fact()
    q2_fact = _build_q2_fact()

    change = calculate_percentage_change(
        current=q2_fact,
        comparison=q1_fact,
    )

    with pytest.raises(
        ValueError,
        match="Source facts do not match the calculation lineage",
    ):
        build_change_audit_trail(
            change=change,
            source_facts=(
                q2_fact,
                q1_fact,
            ),
        )