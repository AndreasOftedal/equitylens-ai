from decimal import Decimal

from equitylens.documents import EQUINOR_Q2_2026
from equitylens.financial_extractor import extract_financial_fact
from equitylens.table_parser import parse_tables


def test_real_equinor_q2_2026_financial_kpis():
    tables = parse_tables(
        document_id=EQUINOR_Q2_2026.document_id,
        pdf_path=EQUINOR_Q2_2026.local_path,
        page_number=4,
    )

    assert len(tables) == 1

    table = tables[0]

    net_operating_income = extract_financial_fact(
        table=table,
        metric="Net operating income/(loss)",
        period="Q2 2026",
        unit="USD million",
    )

    net_income = extract_financial_fact(
        table=table,
        metric="Net income/(loss)",
        period="Q2 2026",
        unit="USD million",
    )

    adjusted_operating_income = extract_financial_fact(
        table=table,
        metric="Adjusted operating income*",
        period="Q2 2026",
        unit="USD million",
    )

    adjusted_net_income = extract_financial_fact(
        table=table,
        metric="Adjusted net income*",
        period="Q2 2026",
        unit="USD million",
    )

    assert net_operating_income.value == Decimal(12993)
    assert net_income.value == Decimal(4836)
    assert adjusted_operating_income.value == Decimal(11482)
    assert adjusted_net_income.value == Decimal(3225)

    facts = [
        net_operating_income,
        net_income,
        adjusted_operating_income,
        adjusted_net_income,
    ]

    for fact in facts:
        assert fact.period == "Q2 2026"
        assert fact.unit == "USD million"
        assert fact.evidence.document_id == EQUINOR_Q2_2026.document_id
        assert fact.evidence.page_number == 4
        assert fact.evidence.table_number == 1
        assert fact.evidence.column_label == "Q2 2026"