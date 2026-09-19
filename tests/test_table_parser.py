from equitylens.documents import EQUINOR_Q2_2026
from equitylens.table_parser import parse_tables


def test_parse_exchange_rate_table():
    tables = parse_tables(
        document_id=EQUINOR_Q2_2026.document_id,
        pdf_path=EQUINOR_Q2_2026.local_path,
        page_number=39,
    )

    assert len(tables) == 1

    table = tables[0]

    assert table.document_id == EQUINOR_Q2_2026.document_id
    assert table.page_number == 39
    assert table.table_number == 1

    usd_nok_average_rate_row = next(
        row
        for row in table.rows
        if row[0] == "Average daily rate" and row[1] == "9.4240"
    )

    assert usd_nok_average_rate_row[1] == "9.4240"
    assert usd_nok_average_rate_row[2] == "9.7267"
    assert usd_nok_average_rate_row[3] == "10.2974"