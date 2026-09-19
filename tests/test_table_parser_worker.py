import json
import subprocess
from pathlib import Path

import pytest

from equitylens.table_parser import parse_tables


def test_parse_tables_retries_after_transient_worker_failure(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    pdf_path = tmp_path / "report.pdf"
    pdf_path.write_bytes(b"test-pdf")

    attempts = 0

    def fake_run(command, **kwargs):
        nonlocal attempts
        attempts += 1

        if attempts == 1:
            return subprocess.CompletedProcess(
                args=command,
                returncode=1,
                stdout="",
                stderr="transient worker failure",
            )

        output_path = Path(
            command[command.index("--output-path") + 1]
        )

        output_path.write_text(
            json.dumps(
                [
                    {
                        "document_id": "test-document",
                        "page_number": 4,
                        "table_number": 1,
                        "columns": [
                            "Metric",
                            "Q2 2026",
                        ],
                        "rows": [
                            [
                                "Adjusted operating income*",
                                "11,482",
                            ]
                        ],
                    }
                ]
            ),
            encoding="utf-8",
        )

        return subprocess.CompletedProcess(
            args=command,
            returncode=0,
            stdout="",
            stderr="",
        )

    monkeypatch.setattr(
        "equitylens.table_parser.subprocess.run",
        fake_run,
    )

    tables = parse_tables(
        document_id="test-document",
        pdf_path=pdf_path,
        page_number=4,
    )

    assert attempts == 2
    assert len(tables) == 1
    assert tables[0].document_id == "test-document"
    assert tables[0].page_number == 4
    assert tables[0].rows[0][1] == "11,482"


def test_parse_tables_raises_after_retry_is_exhausted(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    pdf_path = tmp_path / "report.pdf"
    pdf_path.write_bytes(b"test-pdf")

    def fake_run(command, **kwargs):
        return subprocess.CompletedProcess(
            args=command,
            returncode=1,
            stdout="",
            stderr="persistent worker failure",
        )

    monkeypatch.setattr(
        "equitylens.table_parser.subprocess.run",
        fake_run,
    )

    with pytest.raises(
        RuntimeError,
        match="failed after 2 attempts",
    ) as error:
        parse_tables(
            document_id="test-document",
            pdf_path=pdf_path,
            page_number=4,
        )

    message = str(error.value)

    assert "Attempt 1/2 failed" in message
    assert "Attempt 2/2 failed" in message
    assert "persistent worker failure" in message