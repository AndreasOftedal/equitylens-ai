import pytest

from equitylens.documents import EQUINOR_Q2_2026
from equitylens.parser import parse_pdf

pytestmark = pytest.mark.integration


def test_parse_equinor_report_returns_pages():
    pages = parse_pdf(
        document_id=EQUINOR_Q2_2026.document_id,
        pdf_path=EQUINOR_Q2_2026.local_path,
    )

    assert len(pages) > 0
    assert pages[0].page_number == 1
    assert pages[0].document_id == EQUINOR_Q2_2026.document_id


def test_parse_equinor_report_extracts_text():
    pages = parse_pdf(
        document_id=EQUINOR_Q2_2026.document_id,
        pdf_path=EQUINOR_Q2_2026.local_path,
    )

    total_text = " ".join(page.text for page in pages)

    assert len(total_text) > 1000
    assert "Equinor" in total_text