import math
import re
from collections import Counter
from dataclasses import dataclass

from equitylens.text_chunks import TextChunk

_TOKEN_PATTERN = re.compile(
    r"[A-Za-z0-9]+(?:['’-][A-Za-z0-9]+)*"
)


@dataclass(frozen=True)
class RetrievalResult:
    chunk: TextChunk
    score: float
    rank: int


def tokenize(text: str) -> tuple[str, ...]:
    """
    Convert text into deterministic lowercase lexical tokens.
    """

    return tuple(
        match.group(0).lower()
        for match in _TOKEN_PATTERN.finditer(text)
    )


class BM25Retriever:
    """
    Small deterministic BM25 retriever for narrative evidence candidates.

    This is intentionally lexical and transparent. It acts as the first
    candidate-generation layer before later reranking or hybrid retrieval.
    """

    def __init__(
        self,
        chunks: tuple[TextChunk, ...],
        k1: float = 1.5,
        b: float = 0.75,
    ) -> None:
        if not chunks:
            raise ValueError("chunks cannot be empty.")

        if k1 <= 0:
            raise ValueError("k1 must be greater than zero.")

        if not 0 <= b <= 1:
            raise ValueError("b must be between 0 and 1.")

        self._chunks = chunks
        self._k1 = k1
        self._b = b

        self._tokenized_chunks = tuple(
            tokenize(chunk.text)
            for chunk in chunks
        )

        self._term_frequencies = tuple(
            Counter(tokens)
            for tokens in self._tokenized_chunks
        )

        self._document_lengths = tuple(
            len(tokens)
            for tokens in self._tokenized_chunks
        )

        self._average_document_length = (
            sum(self._document_lengths)
            / len(self._document_lengths)
        )

        self._document_frequencies = self._build_document_frequencies()

    def _build_document_frequencies(
        self,
    ) -> Counter[str]:
        document_frequencies: Counter[str] = Counter()

        for tokens in self._tokenized_chunks:
            document_frequencies.update(
                set(tokens)
            )

        return document_frequencies

    def _inverse_document_frequency(
        self,
        term: str,
    ) -> float:
        document_count = len(self._chunks)
        matching_documents = self._document_frequencies.get(
            term,
            0,
        )

        return math.log(
            1
            + (
                document_count
                - matching_documents
                + 0.5
            )
            / (
                matching_documents
                + 0.5
            )
        )

    def _score_chunk(
        self,
        query_tokens: tuple[str, ...],
        chunk_index: int,
    ) -> float:
        term_frequencies = self._term_frequencies[
            chunk_index
        ]

        document_length = self._document_lengths[
            chunk_index
        ]

        score = 0.0

        for term in set(query_tokens):
            term_frequency = term_frequencies.get(
                term,
                0,
            )

            if term_frequency == 0:
                continue

            inverse_document_frequency = (
                self._inverse_document_frequency(
                    term
                )
            )

            denominator = (
                term_frequency
                + self._k1
                * (
                    1
                    - self._b
                    + self._b
                    * (
                        document_length
                        / self._average_document_length
                    )
                )
            )

            score += (
                inverse_document_frequency
                * (
                    term_frequency
                    * (
                        self._k1
                        + 1
                    )
                )
                / denominator
            )

        return score

    def search(
        self,
        query: str,
        top_k: int = 5,
    ) -> tuple[RetrievalResult, ...]:
        if not query.strip():
            raise ValueError("query cannot be empty.")

        if top_k < 1:
            raise ValueError(
                "top_k must be greater than zero."
            )

        query_tokens = tokenize(query)

        scored_chunks = [
            (
                chunk,
                self._score_chunk(
                    query_tokens=query_tokens,
                    chunk_index=index,
                ),
            )
            for index, chunk in enumerate(
                self._chunks
            )
        ]

        ranked_chunks = sorted(
            (
                item
                for item in scored_chunks
                if item[1] > 0
            ),
            key=lambda item: (
                -item[1],
                item[0].document_id,
                item[0].page_number,
                item[0].chunk_index,
            ),
        )

        return tuple(
            RetrievalResult(
                chunk=chunk,
                score=score,
                rank=rank,
            )
            for rank, (
                chunk,
                score,
            ) in enumerate(
                ranked_chunks[:top_k],
                start=1,
            )
        )