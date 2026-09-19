import pytest

from equitylens.retrieval import (
    BM25Retriever,
    tokenize,
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


def test_tokenize_normalizes_text():
    assert tokenize(
        "Higher Prices supported Cash Flow."
    ) == (
        "higher",
        "prices",
        "supported",
        "cash",
        "flow",
    )


def test_retriever_returns_relevant_chunk_first():
    chunks = (
        _chunk(
            chunk_id="production",
            page_number=5,
            text=(
                "Production increased due to new fields "
                "and higher output on the NCS."
            ),
        ),
        _chunk(
            chunk_id="cash-flow",
            page_number=6,
            text=(
                "Cash flow was supported by higher "
                "liquids and European gas prices."
            ),
        ),
        _chunk(
            chunk_id="unrelated",
            page_number=7,
            text=(
                "The company announced a dividend "
                "and share buy-back programme."
            ),
        ),
    )

    retriever = BM25Retriever(chunks)

    results = retriever.search(
        "cash flow higher prices",
        top_k=3,
    )

    assert results[0].chunk.chunk_id == "cash-flow"
    assert results[0].rank == 1
    assert results[0].score > 0


def test_retriever_preserves_chunk_provenance():
    chunks = (
        _chunk(
            chunk_id="production",
            page_number=5,
            text=(
                "Production growth was driven by "
                "new fields."
            ),
        ),
    )

    retriever = BM25Retriever(chunks)

    result = retriever.search(
        "production growth",
    )[0]

    assert result.chunk.document_id == "report"
    assert result.chunk.page_number == 5
    assert result.chunk.chunk_id == "production"


def test_search_respects_top_k():
    chunks = tuple(
        _chunk(
            chunk_id=f"chunk-{index}",
            page_number=index + 1,
            text=f"Production growth example {index}.",
        )
        for index in range(5)
    )

    retriever = BM25Retriever(chunks)

    results = retriever.search(
        "production growth",
        top_k=2,
    )

    assert len(results) == 2

    assert tuple(
        result.rank
        for result in results
    ) == (
        1,
        2,
    )


def test_search_returns_only_positive_matches():
    chunks = (
        _chunk(
            chunk_id="relevant",
            page_number=1,
            text="Higher liquids prices improved results.",
        ),
        _chunk(
            chunk_id="unrelated",
            page_number=2,
            text="Dividend information.",
        ),
    )

    retriever = BM25Retriever(chunks)

    results = retriever.search(
        "liquids prices",
    )

    assert len(results) == 1
    assert results[0].chunk.chunk_id == "relevant"


def test_empty_query_is_rejected():
    retriever = BM25Retriever(
        (
            _chunk(
                chunk_id="chunk",
                page_number=1,
                text="Some narrative text.",
            ),
        )
    )

    with pytest.raises(
        ValueError,
        match="query cannot be empty",
    ):
        retriever.search(" ")


def test_invalid_top_k_is_rejected():
    retriever = BM25Retriever(
        (
            _chunk(
                chunk_id="chunk",
                page_number=1,
                text="Some narrative text.",
            ),
        )
    )

    with pytest.raises(
        ValueError,
        match="top_k must be greater than zero",
    ):
        retriever.search(
            "narrative",
            top_k=0,
        )


def test_empty_chunk_collection_is_rejected():
    with pytest.raises(
        ValueError,
        match="chunks cannot be empty",
    ):
        BM25Retriever(())