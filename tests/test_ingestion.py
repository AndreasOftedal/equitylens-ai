import hashlib
from io import BytesIO
from pathlib import Path

import pytest

from equitylens.ingestion import (
    SourceIntegrityError,
    calculate_sha256,
    download_source,
    verify_source_file,
)
from equitylens.source_manifest import DocumentSource


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def test_calculate_sha256(tmp_path: Path):
    file_path = tmp_path / "example.pdf"
    file_path.write_bytes(b"equitylens-test-data")

    assert calculate_sha256(file_path) == _sha256(
        b"equitylens-test-data"
    )


def test_verify_source_file_accepts_matching_file(tmp_path: Path):
    payload = b"verified-equitylens-source"

    local_path = tmp_path / "report.pdf"
    local_path.write_bytes(payload)

    source = DocumentSource(
        document_id="test-document",
        download_url="https://example.com/report.pdf",
        local_path=local_path,
        sha256=_sha256(payload),
    )

    assert verify_source_file(source) is True


def test_download_source_verifies_before_saving(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    payload = b"downloaded-equitylens-source"

    source = DocumentSource(
        document_id="test-document",
        download_url="https://example.com/report.pdf",
        local_path=tmp_path / "report.pdf",
        sha256=_sha256(payload),
    )

    monkeypatch.setattr(
        "equitylens.ingestion.urlopen",
        lambda request, timeout: BytesIO(payload),
    )

    downloaded_path = download_source(source)

    assert downloaded_path == source.local_path
    assert downloaded_path.read_bytes() == payload
    assert verify_source_file(source) is True


def test_download_source_rejects_hash_mismatch(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    source = DocumentSource(
        document_id="test-document",
        download_url="https://example.com/report.pdf",
        local_path=tmp_path / "report.pdf",
        sha256=_sha256(b"expected-content"),
    )

    monkeypatch.setattr(
        "equitylens.ingestion.urlopen",
        lambda request, timeout: BytesIO(b"wrong-content"),
    )

    with pytest.raises(SourceIntegrityError):
        download_source(source)

    assert not source.local_path.exists()