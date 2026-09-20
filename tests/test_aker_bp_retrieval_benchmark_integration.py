import pytest

from equitylens.documents import AKER_BP_Q2_2026
from equitylens.evidence_retrieval import NarrativeEvidenceRetriever
from equitylens.parser import parse_pdf
from equitylens.retrieval_evaluation import (
    RetrievalEvaluationCase,
    evaluate_retrieval_case,
    summarize_retrieval_evaluation,
)
from equitylens.text_chunks import (
    TextChunk,
    chunk_pages,
)

pytestmark = pytest.mark.integration


def _find_chunk_id(
    chunks: tuple[TextChunk, ...],
    page_number: int,
    chunk_index: int,
) -> str:
    matches = [
        chunk.chunk_id
        for chunk in chunks
        if (
            chunk.page_number == page_number
            and chunk.chunk_index == chunk_index
        )
    ]

    if len(matches) != 1:
        raise ValueError(
            "Expected exactly one chunk for "
            f"page {page_number}, chunk {chunk_index}; "
            f"found {len(matches)}."
        )

    return matches[0]


def test_aker_bp_q2_retrieval_benchmark():
    pages = parse_pdf(
        document_id=AKER_BP_Q2_2026.document_id,
        pdf_path=AKER_BP_Q2_2026.local_path,
    )

    chunks = chunk_pages(pages)

    retriever = NarrativeEvidenceRetriever(
        chunks
    )

    cases = (
        RetrievalEvaluationCase(
            query="What drove cash flow?",
            relevant_chunk_ids=frozenset(
                {
                    _find_chunk_id(
                        chunks,
                        2,
                        2,
                    ),
                    _find_chunk_id(
                        chunks,
                        6,
                        0,
                    ),
                }
            ),
        ),
        RetrievalEvaluationCase(
            query="What drove production?",
            relevant_chunk_ids=frozenset(
                {
                    _find_chunk_id(
                        chunks,
                        7,
                        0,
                    ),
                    _find_chunk_id(
                        chunks,
                        8,
                        0,
                    ),
                    _find_chunk_id(
                        chunks,
                        10,
                        0,
                    ),
                    _find_chunk_id(
                        chunks,
                        10,
                        2,
                    ),
                    _find_chunk_id(
                        chunks,
                        11,
                        0,
                    ),
                }
            ),
        ),
    )

    case_results = tuple(
        evaluate_retrieval_case(
            case=case,
            results=retriever.retrieve(
                query=case.query,
                top_k=12,
            ),
        )
        for case in cases
    )

    summary = summarize_retrieval_evaluation(
        case_results
    )

    assert summary.hit_at_1 == 1.00
    assert summary.hit_at_3 == 1.00
    assert (
        summary.mean_reciprocal_rank
        == 1.00
    )