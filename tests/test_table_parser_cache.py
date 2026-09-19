import json
from pathlib import Path

import pytest

from equitylens import table_parser


def _write_worker_output(
    output_path: Path,
    document_id: str,
    page_number: int,
) -> None:
    output_path.write_text(
        json.dumps(
            [
                {
                    "document_id": document_id,
                    "page_number": page_number,
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


def test_parse_tables_reuses_cache_without_running_worker_again(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    pdf_path = tmp_path / "report.pdf"
    pdf_path.write_bytes(b"stable-pdf-content")

    cache_dir = tmp_path / "cache"

    monkeypatch.setattr(
        table_parser,
        "TABLE_CACHE_DIR",
        cache_dir,
    )

    worker_calls = 0

    def fake_run_worker(command, output_path):
        nonlocal worker_calls
        worker_calls += 1

        _write_worker_output(
            output_path=output_path,
            document_id="test-document",
            page_number=4,
        )

    monkeypatch.setattr(
        table_parser,
        "_run_worker",
        fake_run_worker,
    )

    first_result = table_parser.parse_tables(
        document_id="test-document",
        pdf_path=pdf_path,
        page_number=4,
    )

    second_result = table_parser.parse_tables(
        document_id="test-document",
        pdf_path=pdf_path,
        page_number=4,
    )

    assert worker_calls == 1
    assert first_result == second_result
    assert len(list(cache_dir.glob("*.json"))) == 1


def test_cache_key_changes_when_pdf_content_changes(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    pdf_path = tmp_path / "report.pdf"
    pdf_path.write_bytes(b"version-one")

    cache_dir = tmp_path / "cache"

    monkeypatch.setattr(
        table_parser,
        "TABLE_CACHE_DIR",
        cache_dir,
    )

    worker_calls = 0

    def fake_run_worker(command, output_path):
        nonlocal worker_calls
        worker_calls += 1

        _write_worker_output(
            output_path=output_path,
            document_id="test-document",
            page_number=4,
        )

    monkeypatch.setattr(
        table_parser,
        "_run_worker",
        fake_run_worker,
    )

    table_parser.parse_tables(
        document_id="test-document",
        pdf_path=pdf_path,
        page_number=4,
    )

    pdf_path.write_bytes(b"version-two")

    table_parser.parse_tables(
        document_id="test-document",
        pdf_path=pdf_path,
        page_number=4,
    )

    assert worker_calls == 2
    assert len(list(cache_dir.glob("*.json"))) == 2


def test_corrupted_cache_is_discarded_and_rebuilt(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    pdf_path = tmp_path / "report.pdf"
    pdf_path.write_bytes(b"stable-pdf-content")

    cache_dir = tmp_path / "cache"

    monkeypatch.setattr(
        table_parser,
        "TABLE_CACHE_DIR",
        cache_dir,
    )

    cache_path = table_parser._build_cache_path(
        document_id="test-document",
        pdf_path=pdf_path,
        page_number=4,
    )

    cache_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    cache_path.write_text(
        "not-valid-json",
        encoding="utf-8",
    )

    worker_calls = 0

    def fake_run_worker(command, output_path):
        nonlocal worker_calls
        worker_calls += 1

        _write_worker_output(
            output_path=output_path,
            document_id="test-document",
            page_number=4,
        )

    monkeypatch.setattr(
        table_parser,
        "_run_worker",
        fake_run_worker,
    )

    tables = table_parser.parse_tables(
        document_id="test-document",
        pdf_path=pdf_path,
        page_number=4,
    )

    assert worker_calls == 1
    assert len(tables) == 1

    rebuilt_payload = json.loads(
        cache_path.read_text(encoding="utf-8")
    )

    assert rebuilt_payload[0]["document_id"] == "test-document"