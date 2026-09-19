import hashlib
from dataclasses import dataclass

from equitylens.parser import ParsedPage

DEFAULT_MAX_CHARS = 1200
DEFAULT_OVERLAP_CHARS = 200
DEFAULT_CONTEXT_CHARS = 250


@dataclass(frozen=True)
class TextChunk:
    chunk_id: str
    document_id: str
    page_number: int
    chunk_index: int
    text: str
    start_char: int
    end_char: int
    section_context: str = ""


def _build_chunk_id(
    document_id: str,
    page_number: int,
    chunk_index: int,
    start_char: int,
    end_char: int,
    text: str,
) -> str:
    content = (
        f"{document_id}|"
        f"{page_number}|"
        f"{chunk_index}|"
        f"{start_char}|"
        f"{end_char}|"
        f"{text}"
    )

    digest = hashlib.sha256(
        content.encode("utf-8")
    ).hexdigest()[:16]

    return (
        f"{document_id}:"
        f"p{page_number}:"
        f"c{chunk_index}:"
        f"{digest}"
    )


def _build_section_context(
    text: str,
    max_chars: int = DEFAULT_CONTEXT_CHARS,
) -> str:
    """
    Preserve a compact page-level structural prefix for every chunk.

    This does not attempt to interpret the section. It only retains
    deterministic context that can later be used for scope-aware retrieval.
    """

    if not text.strip():
        return ""

    normalized = " ".join(
        text[:max_chars].split()
    )

    return normalized


def _find_chunk_end(
    text: str,
    start: int,
    max_chars: int,
) -> int:
    hard_end = min(
        start + max_chars,
        len(text),
    )

    if hard_end == len(text):
        return hard_end

    minimum_boundary = start + (max_chars // 2)

    newline_boundary = text.rfind(
        "\n",
        minimum_boundary,
        hard_end,
    )

    space_boundary = text.rfind(
        " ",
        minimum_boundary,
        hard_end,
    )

    boundary = max(
        newline_boundary,
        space_boundary,
    )

    if boundary <= start:
        return hard_end

    return boundary


def _next_chunk_start(
    text: str,
    previous_end: int,
    overlap_chars: int,
) -> int:
    if overlap_chars == 0:
        return previous_end

    candidate = max(
        0,
        previous_end - overlap_chars,
    )

    if candidate == 0:
        return candidate

    while (
        candidate < previous_end
        and not text[candidate].isspace()
    ):
        candidate += 1

    while (
        candidate < previous_end
        and text[candidate].isspace()
    ):
        candidate += 1

    return candidate


def chunk_page(
    page: ParsedPage,
    max_chars: int = DEFAULT_MAX_CHARS,
    overlap_chars: int = DEFAULT_OVERLAP_CHARS,
) -> tuple[TextChunk, ...]:
    """
    Split one parsed PDF page into deterministic text chunks.

    Every chunk preserves document, page, character-level provenance
    and compact structural context from the source page.
    """

    if max_chars < 1:
        raise ValueError(
            "max_chars must be greater than zero."
        )

    if overlap_chars < 0:
        raise ValueError(
            "overlap_chars cannot be negative."
        )

    if overlap_chars >= max_chars:
        raise ValueError(
            "overlap_chars must be smaller than max_chars."
        )

    text = page.text

    if not text.strip():
        return ()

    section_context = _build_section_context(
        text
    )

    chunks: list[TextChunk] = []

    start = 0
    chunk_index = 0

    while start < len(text):
        end = _find_chunk_end(
            text=text,
            start=start,
            max_chars=max_chars,
        )

        raw_chunk = text[start:end]

        leading_whitespace = (
            len(raw_chunk)
            - len(raw_chunk.lstrip())
        )

        trailing_whitespace = (
            len(raw_chunk)
            - len(raw_chunk.rstrip())
        )

        actual_start = start + leading_whitespace
        actual_end = end - trailing_whitespace

        chunk_text = text[
            actual_start:actual_end
        ]

        if chunk_text:
            chunks.append(
                TextChunk(
                    chunk_id=_build_chunk_id(
                        document_id=page.document_id,
                        page_number=page.page_number,
                        chunk_index=chunk_index,
                        start_char=actual_start,
                        end_char=actual_end,
                        text=chunk_text,
                    ),
                    document_id=page.document_id,
                    page_number=page.page_number,
                    chunk_index=chunk_index,
                    text=chunk_text,
                    start_char=actual_start,
                    end_char=actual_end,
                    section_context=section_context,
                )
            )

            chunk_index += 1

        if end >= len(text):
            break

        next_start = _next_chunk_start(
            text=text,
            previous_end=end,
            overlap_chars=overlap_chars,
        )

        if next_start <= start:
            next_start = end

        start = next_start

    return tuple(chunks)


def chunk_pages(
    pages: list[ParsedPage],
    max_chars: int = DEFAULT_MAX_CHARS,
    overlap_chars: int = DEFAULT_OVERLAP_CHARS,
) -> tuple[TextChunk, ...]:
    """
    Chunk multiple parsed pages while preserving page boundaries.
    """

    return tuple(
        chunk
        for page in pages
        for chunk in chunk_page(
            page=page,
            max_chars=max_chars,
            overlap_chars=overlap_chars,
        )
    )