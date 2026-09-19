from equitylens.narrative_reranker import (
    NarrativeEvidenceReranker,
    RerankedResult,
)
from equitylens.retrieval import BM25Retriever
from equitylens.text_chunks import TextChunk

DEFAULT_CANDIDATE_K = 60


class NarrativeEvidenceRetriever:
    """
    Retrieve explanatory narrative evidence from document chunks.

    Retrieval uses deterministic BM25 candidate generation followed by
    narrative-quality and scope-aware deterministic reranking.

    A deliberately broad candidate pool is used because explanatory
    narrative can have weaker lexical overlap than tables, definitions
    and segment-specific disclosures that mention the metric directly.
    """

    def __init__(
        self,
        chunks: tuple[TextChunk, ...],
    ) -> None:
        self._retriever = BM25Retriever(chunks)
        self._reranker = NarrativeEvidenceReranker()

    def retrieve(
        self,
        query: str,
        top_k: int = 5,
        candidate_k: int = DEFAULT_CANDIDATE_K,
    ) -> tuple[RerankedResult, ...]:
        if top_k < 1:
            raise ValueError(
                "top_k must be greater than zero."
            )

        if candidate_k < 1:
            raise ValueError(
                "candidate_k must be greater than zero."
            )

        if candidate_k < top_k:
            raise ValueError(
                "candidate_k must be greater than or equal to top_k."
            )

        candidates = self._retriever.search(
            query=query,
            top_k=candidate_k,
        )

        if not candidates:
            return ()

        return self._reranker.rerank(
            results=candidates,
            query=query,
            top_k=top_k,
        )