import json
import subprocess
import sys
import tempfile
from pathlib import Path

from equitylens.models import ParsedTable


def parse_tables(
    document_id: str,
    pdf_path: Path,
    page_number: int,
) -> list[ParsedTable]:
    """Extract structured tables from one PDF page in an isolated process."""

    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    if page_number < 1:
        raise ValueError("page_number must be 1 or greater")

    with tempfile.TemporaryDirectory() as temp_directory:
        output_path = Path(temp_directory) / "tables.json"

        command = [
            sys.executable,
            "-m",
            "equitylens.docling_worker",
            "--document-id",
            document_id,
            "--pdf-path",
            str(pdf_path.resolve()),
            "--page-number",
            str(page_number),
            "--output-path",
            str(output_path),
        ]

        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )

        if result.returncode != 0:
            error_output = result.stderr.strip() or result.stdout.strip()

            raise RuntimeError(
                "Docling table extraction failed in worker process.\n"
                f"{error_output}"
            )

        if not output_path.exists():
            raise RuntimeError(
                "Docling worker completed without producing table output."
            )

        payload = json.loads(
            output_path.read_text(encoding="utf-8")
        )

    return [
        ParsedTable(
            document_id=table["document_id"],
            page_number=table["page_number"],
            table_number=table["table_number"],
            columns=tuple(table["columns"]),
            rows=tuple(
                tuple(row)
                for row in table["rows"]
            ),
        )
        for table in payload
    ]