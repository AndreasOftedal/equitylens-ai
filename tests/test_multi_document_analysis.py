from decimal import Decimal

from equitylens.calculations import calculate_percentage_change
from equitylens.documents import EQUINOR_Q1_2026, EQUINOR_Q2_2026
from equitylens.financial_extractor import extract_financial_fact
from equitylens.models import ParsedTable
from equitylens.table_parser import parse_tables


def _find_table_for_metric_and_period(
    tables: list[ParsedTable],
    metric: str,
    period: str,
) -> ParsedTable:
    """Find the table that contains both the requested metric and period."""

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


def test_q1_to_q2_adjusted_operating_income_change_across_documents():
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
        metric="Adjusted operating income*",
        period="Q1 2026",
    )

    q2_table = _find_table_for_metric_and_period(
        tables=q2_tables,
        metric="Adjusted operating income*",
        period="Q2 2026",
    )

    q1_fact = extract_financial_fact(
        table=q1_table,
        metric="Adjusted operating income*",
        period="Q1 2026",
        unit="USD million",
    )

    q2_fact = extract_financial_fact(
        table=q2_table,
        metric="Adjusted operating income*",
        period="Q2 2026",
        unit="USD million",
    )

    change = calculate_percentage_change(
        current=q2_fact,
        comparison=q1_fact,
    )

    assert q1_fact.value == Decimal(9770)
    assert q2_fact.value == Decimal(11482)

    assert change.absolute_change == Decimal(1712)
    assert change.percentage_change == Decimal("17.5")

    assert change.from_period == "Q1 2026"
    assert change.to_period == "Q2 2026"

    assert q1_fact.evidence.document_id == EQUINOR_Q1_2026.document_id
    assert q2_fact.evidence.document_id == EQUINOR_Q2_2026.document_id

    assert q1_fact.evidence.page_number == 4
    assert q2_fact.evidence.page_number == 4

    assert change.source_fact_ids == (
        q1_fact.fact_id,
        q2_fact.fact_id,
    )