from pathlib import Path

from docling.backend.docling_parse_backend import DoclingParseDocumentBackend
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions, TableFormerMode
from docling.document_converter import DocumentConverter, PdfFormatOption

from equitylens.models import ParsedTable


def _create_converter() -> DocumentConverter:
    pipeline_options = PdfPipelineOptions(
        do_ocr=False,
        do_table_structure=True,
    )

    pipeline_options.table_structure_options.mode = TableFormerMode.ACCURATE

    return DocumentConverter(
        format_options={
            InputFormat.PDF: PdfFormatOption(
                pipeline_options=pipeline_options,
                backend=DoclingParseDocumentBackend,
            )
        }
    )


def parse_tables(
    document_id: str,
    pdf_path: Path,
    page_number: int,
) -> list[ParsedTable]:
    """Extract structured tables from one PDF page."""

    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    if page_number < 1:
        raise ValueError("page_number must be 1 or greater")

    converter = _create_converter()

    result = converter.convert(
        pdf_path,
        page_range=(page_number, page_number),
    )

    parsed_tables: list[ParsedTable] = []

    for table_number, table in enumerate(result.document.tables, start=1):
        dataframe = table.export_to_dataframe(doc=result.document)

        columns = tuple(str(column).strip() for column in dataframe.columns)

        rows = tuple(
            tuple(
                "" if value is None else str(value).strip()
                for value in row
            )
            for row in dataframe.itertuples(index=False, name=None)
        )

        parsed_tables.append(
            ParsedTable(
                document_id=document_id,
                page_number=page_number,
                table_number=table_number,
                columns=columns,
                rows=rows,
            )
        )

    return parsed_tables