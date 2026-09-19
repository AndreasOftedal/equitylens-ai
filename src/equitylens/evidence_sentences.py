import re
from dataclasses import dataclass
from itertools import pairwise

from equitylens.text_chunks import TextChunk

_SENTENCE_BOUNDARY = re.compile(
    r"(?<=[.!?])\s+(?=[A-Z0-9“\"'])"
)


@dataclass(frozen=True)
class EvidenceSentence:
    sentence_id: str
    chunk_id: str
    document_id: str
    page_number: int
    sentence_index: int
    text: str
    chunk_start_char: int
    chunk_end_char: int
    page_start_char: int
    page_end_char: int
    section_context: str


def _build_sentence_id(
    chunk: TextChunk,
    sentence_index: int,
    start_char: int,
    end_char: int,
) -> str:
    return (
        f"{chunk.chunk_id}:"
        f"s{sentence_index}:"
        f"{start_char}-{end_char}"
    )


def split_chunk_into_sentences(
    chunk: TextChunk,
) -> tuple[EvidenceSentence, ...]:
    """
    Split a retrieved chunk into sentence-level evidence while preserving
    exact chunk- and page-level provenance.

    Sentence splitting is intentionally deterministic and lightweight.
    """

    if not chunk.text.strip():
        return ()

    boundaries = [
        0,
        *(
            match.end()
            for match in _SENTENCE_BOUNDARY.finditer(
                chunk.text
            )
        ),
        len(chunk.text),
    ]

    sentences: list[EvidenceSentence] = []

    for start, end in pairwise(
        boundaries
    ):
        raw_text = chunk.text[start:end]

        leading_whitespace = (
            len(raw_text)
            - len(raw_text.lstrip())
        )

        trailing_whitespace = (
            len(raw_text)
            - len(raw_text.rstrip())
        )

        actual_start = start + leading_whitespace
        actual_end = end - trailing_whitespace

        text = chunk.text[
            actual_start:actual_end
        ]

        if not text:
            continue

        sentence_index = len(sentences)

        sentences.append(
            EvidenceSentence(
                sentence_id=_build_sentence_id(
                    chunk=chunk,
                    sentence_index=sentence_index,
                    start_char=actual_start,
                    end_char=actual_end,
                ),
                chunk_id=chunk.chunk_id,
                document_id=chunk.document_id,
                page_number=chunk.page_number,
                sentence_index=sentence_index,
                text=text,
                chunk_start_char=actual_start,
                chunk_end_char=actual_end,
                page_start_char=(
                    chunk.start_char
                    + actual_start
                ),
                page_end_char=(
                    chunk.start_char
                    + actual_end
                ),
                section_context=(
                    chunk.section_context
                ),
            )
        )

    return tuple(sentences)