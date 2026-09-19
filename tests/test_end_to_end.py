from decimal import Decimal

import pytest

from equitylens.documents import EQUINOR_Q2_2026
from equitylens.financial_extractor import extract_exchange_rate_fact
from equitylens.table_parser import parse_tables

pytestmark = pytest.mark.integration


def test_real_equinor_pdf_to_auditable_financial_fact():
    tables = parse_tables(
        document_id=EQUINOR_Q2_2026.document_id,
        pdf_path=EQUINOR_Q2_2026.local_path,
        page_number=39,
    )

    assert len(tables) == 1

    fact = extract_exchange_rate_fact(
        table=tables[0],
        currency_pair="USD/NOK",
        measure="Average daily rate",
        period="Q2 2026",
    )

    assert fact.metric == "USD/NOK Average daily rate"
    assert fact.period == "Q2 2026"
    assert fact.value == Decimal("9.4240")
    assert fact.unit == "NOK per USD"

    assert fact.evidence.document_id == EQUINOR_Q2_2026.document_id
    assert fact.evidence.page_number == 39
    assert fact.evidence.table_number == 1
    assert fact.evidence.row_label == "USD/NOK / Average daily rate"
    assert fact.evidence.column_label == "Quarters.Q2 2026"