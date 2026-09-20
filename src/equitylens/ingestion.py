import hashlib
import shutil
import tempfile
from pathlib import Path
from urllib.request import Request, urlopen

from equitylens.source_manifest import ALL_SOURCES, DocumentSource


class SourceIntegrityError(RuntimeError):
    """Raised when a downloaded or existing source fails integrity verification."""


def calculate_sha256(file_path: Path) -> str:
    """Calculate the SHA-256 fingerprint of a file."""

    digest = hashlib.sha256()

    with file_path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)

    return digest.hexdigest()


def verify_source_file(source: DocumentSource) -> bool:
    """Return True when the local source exists and matches its manifest hash."""

    if not source.local_path.exists():
        return False

    return calculate_sha256(source.local_path) == source.sha256


def download_source(
    source: DocumentSource,
    *,
    force: bool = False,
) -> Path:
    """Download and verify one source document."""

    if source.local_path.exists() and not force:
        if verify_source_file(source):
            return source.local_path

        raise SourceIntegrityError(
            f"Existing source failed SHA-256 verification: {source.local_path}"
        )

    source.local_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    request = Request(
        source.download_url,
        headers={
            "User-Agent": "EquityLens-AI/0.1",
        },
    )

    temporary_path: Path | None = None

    try:
        with tempfile.NamedTemporaryFile(
            mode="wb",
            suffix=".part",
            prefix=f"{source.document_id}-",
            dir=source.local_path.parent,
            delete=False,
        ) as temporary_file:
            temporary_path = Path(temporary_file.name)

            with urlopen(request, timeout=60) as response:
                shutil.copyfileobj(response, temporary_file)

        actual_sha256 = calculate_sha256(temporary_path)

        if actual_sha256 != source.sha256:
            raise SourceIntegrityError(
                f"SHA-256 mismatch for {source.document_id}. "
                f"Expected {source.sha256}, got {actual_sha256}."
            )

        temporary_path.replace(source.local_path)

        return source.local_path

    finally:
        if temporary_path is not None and temporary_path.exists():
            temporary_path.unlink()


def download_all_sources(
    *,
    force: bool = False,
) -> list[Path]:
    """Download and verify all registered source documents."""

    return [
        download_source(source, force=force)
        for source in ALL_SOURCES
    ]


def main() -> None:
    downloaded_paths = download_all_sources()

    for path in downloaded_paths:
        print(f"Verified: {path}")


if __name__ == "__main__":
    main()