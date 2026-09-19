import argparse
import json
from pathlib import Path

from docling.backend.docling_parse_backend import DoclingParseDocumentBackend
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions, TableFormerMode
from docling.document_converter import DocumentConverter, PdfFormatOption


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


def _extract_tables(
    document_id: str,
    pdf_path: Path,
    page_number: int,
) -> list[dict]:
    converter = _create_converter()

    result = converter.convert(
        pdf_path,
        page_range=(page_number, page_number),
    )

    tables = []

    for table_number, table in enumerate(result.document.tables, start=1):
        dataframe = table.export_to_dataframe(doc=result.document)

        columns = [
            str(column).strip()
            for column in dataframe.columns
        ]

        rows = [
            [
                "" if value is None else str(value).strip()
                for value in row
            ]
            for row in dataframe.itertuples(index=False, name=None)
        ]

        tables.append(
            {
                "document_id": document_id,
                "page_number": page_number,
                "table_number": table_number,
                "columns": columns,
                "rows": rows,
            }
        )

    return tables


def main() -> None:
    parser = argparse.ArgumentParser()

    parser.add_argument("--document-id", required=True)
    parser.add_argument("--pdf-path", required=True)
    parser.add_argument("--page-number", required=True, type=int)
    parser.add_argument("--output-path", required=True)

    args = parser.parse_args()

    tables = _extract_tables(
        document_id=args.document_id,
        pdf_path=Path(args.pdf_path),
        page_number=args.page_number,
    )

    output_path = Path(args.output_path)

    output_path.write_text(
        json.dumps(tables, ensure_ascii=False),
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()