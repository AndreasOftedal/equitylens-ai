import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

from equitylens.models import ParsedTable

MAX_WORKER_ATTEMPTS = 2

TABLE_CACHE_VERSION = "v1"
TABLE_CACHE_DIR = Path("data/cache/tables")


def _run_worker(
    command: list[str],
    output_path: Path,
) -> None:
    errors = []

    for attempt in range(1, MAX_WORKER_ATTEMPTS + 1):
        if output_path.exists():
            output_path.unlink()

        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )

        if result.returncode == 0 and output_path.exists():
            return

        error_output = result.stderr.strip() or result.stdout.strip()

        if not error_output:
            error_output = "Worker exited without diagnostic output."

        errors.append(
            f"Attempt {attempt}/{MAX_WORKER_ATTEMPTS} failed "
            f"with exit code {result.returncode}:\n"
            f"{error_output}"
        )

    raise RuntimeError(
        "Docling table extraction failed after "
        f"{MAX_WORKER_ATTEMPTS} attempts.\n\n"
        + "\n\n".join(errors)
    )


def _calculate_file_sha256(file_path: Path) -> str:
    digest = hashlib.sha256()

    with file_path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)

    return digest.hexdigest()


def _build_cache_path(
    document_id: str,
    pdf_path: Path,
    page_number: int,
) -> Path:
    pdf_sha256 = _calculate_file_sha256(pdf_path)

    cache_identity = (
        f"{TABLE_CACHE_VERSION}|"
        f"{document_id}|"
        f"{pdf_sha256}|"
        f"page={page_number}"
    )

    cache_key = hashlib.sha256(
        cache_identity.encode("utf-8")
    ).hexdigest()

    return TABLE_CACHE_DIR / f"{cache_key}.json"


def _load_cached_payload(
    cache_path: Path,
) -> list[dict[str, Any]] | None:
    if not cache_path.exists():
        return None

    try:
        payload = json.loads(
            cache_path.read_text(encoding="utf-8")
        )

        if not isinstance(payload, list):
            raise TypeError("Cached table payload must be a list.")

        for table in payload:
            if not isinstance(table, dict):
                raise TypeError("Cached table entry must be an object.")

            required_fields = {
                "document_id",
                "page_number",
                "table_number",
                "columns",
                "rows",
            }

            if not required_fields.issubset(table):
                raise ValueError(
                    "Cached table entry is missing required fields."
                )

        return payload

    except (
        json.JSONDecodeError,
        OSError,
        TypeError,
        ValueError,
    ):
        cache_path.unlink(missing_ok=True)
        return None


def _write_cached_payload(
    cache_path: Path,
    payload: list[dict[str, Any]],
) -> None:
    cache_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    temporary_path: Path | None = None

    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            suffix=".tmp",
            prefix="table-cache-",
            dir=cache_path.parent,
            delete=False,
        ) as temporary_file:
            temporary_path = Path(temporary_file.name)

            json.dump(
                payload,
                temporary_file,
                ensure_ascii=False,
            )

        temporary_path.replace(cache_path)

    finally:
        if temporary_path is not None and temporary_path.exists():
            temporary_path.unlink()


def _payload_to_tables(
    payload: list[dict[str, Any]],
) -> list[ParsedTable]:
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


def parse_tables(
    document_id: str,
    pdf_path: Path,
    page_number: int,
) -> list[ParsedTable]:
    """
    Extract structured tables from one PDF page.

    Results are cached using the source PDF hash, document identity,
    page number and parser-cache version. Docling runs in an isolated
    worker process only when a valid cache entry is unavailable.
    """

    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    if page_number < 1:
        raise ValueError("page_number must be 1 or greater")

    cache_path = _build_cache_path(
        document_id=document_id,
        pdf_path=pdf_path,
        page_number=page_number,
    )

    cached_payload = _load_cached_payload(cache_path)

    if cached_payload is not None:
        return _payload_to_tables(cached_payload)

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

        _run_worker(
            command=command,
            output_path=output_path,
        )

        payload = json.loads(
            output_path.read_text(encoding="utf-8")
        )

    _write_cached_payload(
        cache_path=cache_path,
        payload=payload,
    )

    return _payload_to_tables(payload)