from decimal import Decimal

from equitylens.calculations import calculate_percentage_change
from equitylens.documents import EQUINOR_Q2_2026
from equitylens.financial_extractor import extract_financial_fact
from equitylens.table_parser import parse_tables


def test_real_pdf_to_adjusted_operating_income_yoy_change():
    tables = parse_tables(
        document_id=EQUINOR_Q2_2026.document_id,
        pdf_path=EQUINOR_Q2_2026.local_path,
        page_number=4,
    )

    assert len(tables) == 1

    table = tables[0]

    q2_2026 = extract_financial_fact(
        table=table,
        metric="Adjusted operating income*",
        period="Q2 2026",
        unit="USD million",
    )

    q2_2025 = extract_financial_fact(
        table=table,
        metric="Adjusted operating income*",
        period="Q2 2025",
        unit="USD million",
    )

    change = calculate_percentage_change(
        current=q2_2026,
        comparison=q2_2025,
    )

    assert q2_2026.value == Decimal(11482)
    assert q2_2025.value == Decimal(6535)

    assert change.absolute_change == Decimal(4947)
    assert change.percentage_change == Decimal("75.7")

    assert change.from_period == "Q2 2025"
    assert change.to_period == "Q2 2026"
    assert change.unit == "USD million"

    assert q2_2026.evidence.page_number == 4
    assert q2_2025.evidence.page_number == 4

    assert change.source_fact_ids == (
        q2_2025.fact_id,
        q2_2026.fact_id,
    )