from decimal import Decimal

import pytest

from equitylens.audit import build_change_audit_trail
from equitylens.calculations import calculate_percentage_change
from equitylens.documents import EQUINOR_Q1_2026, EQUINOR_Q2_2026
from equitylens.financial_extractor import extract_financial_fact
from equitylens.models import ParsedTable
from equitylens.table_parser import parse_tables

pytestmark = pytest.mark.integration


def _find_table_for_metric_and_period(
    tables: list[ParsedTable],
    metric: str,
    period: str,
) -> ParsedTable:
    """Find exactly one table containing the requested metric and period."""

    matching_tables = []

    for table in tables:
        has_metric = any(
            row and row[0] == metric
            for row in table.rows
        )

        has_period = any(
            column == period or column.endswith(f".{period}")
            for column in table.columns
        )

        if has_metric and has_period:
            matching_tables.append(table)

    if len(matching_tables) != 1:
        raise ValueError(
            f"Expected exactly one table containing metric={metric!r} "
            f"and period={period!r}, found {len(matching_tables)}."
        )

    return matching_tables[0]


def test_real_documents_produce_auditable_change_claim():
    metric = "Adjusted operating income*"

    q1_tables = parse_tables(
        document_id=EQUINOR_Q1_2026.document_id,
        pdf_path=EQUINOR_Q1_2026.local_path,
        page_number=4,
    )

    q2_tables = parse_tables(
        document_id=EQUINOR_Q2_2026.document_id,
        pdf_path=EQUINOR_Q2_2026.local_path,
        page_number=4,
    )

    q1_table = _find_table_for_metric_and_period(
        tables=q1_tables,
        metric=metric,
        period="Q1 2026",
    )

    q2_table = _find_table_for_metric_and_period(
        tables=q2_tables,
        metric=metric,
        period="Q2 2026",
    )

    q1_fact = extract_financial_fact(
        table=q1_table,
        metric=metric,
        period="Q1 2026",
        unit="USD million",
    )

    q2_fact = extract_financial_fact(
        table=q2_table,
        metric=metric,
        period="Q2 2026",
        unit="USD million",
    )

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

    assert audit_trail.calculation.from_value == Decimal(9770)
    assert audit_trail.calculation.to_value == Decimal(11482)
    assert audit_trail.calculation.absolute_change == Decimal(1712)
    assert audit_trail.calculation.percentage_change == Decimal("17.5")

    q1_evidence = audit_trail.source_facts[0].evidence
    q2_evidence = audit_trail.source_facts[1].evidence

    assert q1_evidence.document_id == EQUINOR_Q1_2026.document_id
    assert q2_evidence.document_id == EQUINOR_Q2_2026.document_id

    assert q1_evidence.page_number == 4
    assert q2_evidence.page_number == 4

    assert q1_evidence.table_number == 1
    assert q2_evidence.table_number == 1

    assert q1_evidence.row_label == metric
    assert q2_evidence.row_label == metric