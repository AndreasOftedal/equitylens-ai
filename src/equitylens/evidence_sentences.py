import re
from dataclasses import dataclass
from itertools import pairwise

from equitylens.text_chunks import TextChunk

_SENTENCE_BOUNDARY = re.compile(
    r"(?<=[.!?])\s+(?=[A-Z0-9â€œ\"'])"
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


def _numeric_token_ratio(
    text: str,
) -> float:
    tokens = text.split()

    if not tokens:
        return 0.0

    numeric_tokens = sum(
        any(
            character.isdigit()
            for character in token
        )
        for token in tokens
    )

    return numeric_tokens / len(tokens)


def _looks_table_like_line(
    line: str,
) -> bool:
    stripped = line.strip()

    if not stripped:
        return False

    return (
        _numeric_token_ratio(stripped) >= 0.50
    )


def _looks_narrative_line(
    line: str,
) -> bool:
    stripped = line.strip()

    if not stripped:
        return False

    words = stripped.split()

    if len(words) < 5:
        return False

    if not stripped[0].isalpha():
        return False

    return any(
        character.islower()
        for character in stripped
    )


def _table_to_narrative_boundaries(
    text: str,
) -> tuple[int, ...]:
    """
    Detect transitions from table-like PDF text into narrative prose.

    PDF extraction may place a table and the following paragraph in the
    same text block without punctuation between them. In that case the
    normal sentence-boundary regex cannot separate the narrative from
    the table.

    A structural boundary is added only when a numeric-heavy line is
    immediately followed by a sentence-like narrative line.
    """

    boundaries: list[int] = []

    lines = text.splitlines(
        keepends=True
    )

    offset = 0

    for index, line in enumerate(
        lines[:-1]
    ):
        next_line = lines[index + 1]

        offset += len(line)

        if (
            _looks_table_like_line(line)
            and _looks_narrative_line(
                next_line
            )
        ):
            boundaries.append(
                offset
            )

    return tuple(boundaries)


def split_chunk_into_sentences(
    chunk: TextChunk,
) -> tuple[EvidenceSentence, ...]:
    """
    Split a retrieved chunk into sentence-level evidence while preserving
    exact chunk- and page-level provenance.

    Sentence splitting is intentionally deterministic and lightweight.
    In addition to punctuation boundaries, table-to-narrative transitions
    are detected so extracted PDF tables do not absorb the prose that
    follows them.
    """

    if not chunk.text.strip():
        return ()

    punctuation_boundaries = (
        match.end()
        for match in _SENTENCE_BOUNDARY.finditer(
            chunk.text
        )
    )

    structural_boundaries = (
        _table_to_narrative_boundaries(
            chunk.text
        )
    )

    boundaries = sorted(
        {
            0,
            *punctuation_boundaries,
            *structural_boundaries,
            len(chunk.text),
        }
    )

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

        actual_start = (
            start
            + leading_whitespace
        )
        actual_end = (
            end
            - trailing_whitespace
        )

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