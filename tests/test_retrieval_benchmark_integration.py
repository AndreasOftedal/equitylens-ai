import pytest

from equitylens.documents import EQUINOR_Q2_2026
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


def test_equinor_q2_retrieval_benchmark():
    pages = parse_pdf(
        document_id=EQUINOR_Q2_2026.document_id,
        pdf_path=EQUINOR_Q2_2026.local_path,
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
                        9,
                        2,
                    ),
                    _find_chunk_id(
                        chunks,
                        9,
                        3,
                    ),
                    _find_chunk_id(
                        chunks,
                        9,
                        4,
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
                        5,
                        0,
                    ),
                    _find_chunk_id(
                        chunks,
                        8,
                        0,
                    ),
                    _find_chunk_id(
                        chunks,
                        13,
                        0,
                    ),
                    _find_chunk_id(
                        chunks,
                        14,
                        0,
                    ),
                    _find_chunk_id(
                        chunks,
                        15,
                        0,
                    ),
                }
            ),
        ),
        RetrievalEvaluationCase(
            query=(
                "What drove renewable "
                "power generation?"
            ),
            relevant_chunk_ids=frozenset(
                {
                    _find_chunk_id(
                        chunks,
                        5,
                        0,
                    ),
                    _find_chunk_id(
                        chunks,
                        5,
                        1,
                    ),
                    _find_chunk_id(
                        chunks,
                        8,
                        1,
                    ),
                    _find_chunk_id(
                        chunks,
                        17,
                        0,
                    ),
                }
            ),
        ),
        RetrievalEvaluationCase(
            query=(
                "What drove adjusted "
                "operating income?"
            ),
            relevant_chunk_ids=frozenset(
                {
                    _find_chunk_id(
                        chunks,
                        5,
                        1,
                    ),
                }
            ),
        ),
        RetrievalEvaluationCase(
            query=(
                "What drove net "
                "operating income?"
            ),
            relevant_chunk_ids=frozenset(
                {
                    _find_chunk_id(
                        chunks,
                        5,
                        1,
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
                top_k=8,
            ),
        )
        for case in cases
    )

    summary = summarize_retrieval_evaluation(
        case_results
    )

    assert summary.hit_at_1 >= 0.40
    assert summary.hit_at_3 == 1.00
    assert (
        summary.mean_reciprocal_rank
        >= 0.65
    )