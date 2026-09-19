import pytest

from equitylens.evidence_retrieval import (
    NarrativeEvidenceRetriever,
)
from equitylens.text_chunks import TextChunk


def _chunk(
    chunk_id: str,
    text: str,
    page_number: int,
) -> TextChunk:
    return TextChunk(
        chunk_id=chunk_id,
        document_id="report",
        page_number=page_number,
        chunk_index=0,
        text=text,
        start_char=0,
        end_char=len(text),
    )


def test_retrieval_pipeline_prefers_explanatory_narrative():
    chunks = (
        _chunk(
            chunk_id="table",
            page_number=4,
            text=(
                "Cash flow Q2 2026 Q1 2026 Q2 2025 "
                "9,470 5,213 2,477 100% 14,683 11,518."
            ),
        ),
        _chunk(
            chunk_id="narrative",
            page_number=9,
            text=(
                "Cash flow and net debt. High commodity prices, "
                "combined with strong production, generated strong "
                "cash flow from operating activities."
            ),
        ),
        _chunk(
            chunk_id="definition",
            page_number=41,
            text=(
                "Our definition of cash flow does not represent "
                "residual cash flows available for discretionary "
                "expenditures."
            ),
        ),
    )

    retriever = NarrativeEvidenceRetriever(
        chunks
    )

    results = retriever.retrieve(
        query="What drove cash flow?",
        top_k=3,
        candidate_k=3,
    )

    assert (
        results[0].chunk.chunk_id
        == "narrative"
    )

    assert results[0].rank == 1
    assert results[0].narrative_score > 0


def test_retrieval_pipeline_preserves_provenance():
    chunk = _chunk(
        chunk_id="production",
        page_number=8,
        text=(
            "Production increased, driven by the ramp-up "
            "of new fields and supported by new wells."
        ),
    )

    retriever = NarrativeEvidenceRetriever(
        (chunk,)
    )

    result = retriever.retrieve(
        query="What drove production?"
    )[0]

    assert result.chunk.chunk_id == "production"
    assert result.chunk.document_id == "report"
    assert result.chunk.page_number == 8
    assert result.chunk.start_char == 0
    assert result.chunk.end_char == len(
        chunk.text
    )


def test_retrieval_pipeline_returns_empty_when_no_candidate_matches():
    retriever = NarrativeEvidenceRetriever(
        (
            _chunk(
                chunk_id="dividend",
                page_number=3,
                text=(
                    "The company announced a quarterly dividend."
                ),
            ),
        )
    )

    results = retriever.retrieve(
        query="geothermal drilling"
    )

    assert results == ()


def test_retrieval_pipeline_respects_top_k():
    chunks = tuple(
        _chunk(
            chunk_id=f"production-{index}",
            page_number=index + 1,
            text=(
                "Production was driven by new fields "
                f"and operational improvement {index}."
            ),
        )
        for index in range(5)
    )

    retriever = NarrativeEvidenceRetriever(
        chunks
    )

    results = retriever.retrieve(
        query="What drove production?",
        top_k=2,
        candidate_k=5,
    )

    assert len(results) == 2

    assert tuple(
        result.rank
        for result in results
    ) == (
        1,
        2,
    )


def test_candidate_pool_cannot_be_smaller_than_final_result_set():
    retriever = NarrativeEvidenceRetriever(
        (
            _chunk(
                chunk_id="production",
                page_number=1,
                text="Production was driven by new fields.",
            ),
        )
    )

    with pytest.raises(
        ValueError,
        match=(
            "candidate_k must be greater than "
            "or equal to top_k"
        ),
    ):
        retriever.retrieve(
            query="production",
            top_k=5,
            candidate_k=3,
        )


def test_invalid_candidate_k_is_rejected():
    retriever = NarrativeEvidenceRetriever(
        (
            _chunk(
                chunk_id="production",
                page_number=1,
                text="Production was driven by new fields.",
            ),
        )
    )

    with pytest.raises(
        ValueError,
        match="candidate_k must be greater than zero",
    ):
        retriever.retrieve(
            query="production",
            candidate_k=0,
        )


def test_invalid_top_k_is_rejected():
    retriever = NarrativeEvidenceRetriever(
        (
            _chunk(
                chunk_id="production",
                page_number=1,
                text="Production was driven by new fields.",
            ),
        )
    )

    with pytest.raises(
        ValueError,
        match="top_k must be greater than zero",
    ):
        retriever.retrieve(
            query="production",
            top_k=0,
        )