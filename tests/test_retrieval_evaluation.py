import pytest

from equitylens.narrative_reranker import RerankedResult
from equitylens.retrieval_evaluation import (
    RetrievalEvaluationCase,
    evaluate_retrieval_case,
    summarize_retrieval_evaluation,
)
from equitylens.text_chunks import TextChunk


def _result(
    chunk_id: str,
    rank: int,
) -> RerankedResult:
    text = f"Narrative evidence {chunk_id}."

    chunk = TextChunk(
        chunk_id=chunk_id,
        document_id="report",
        page_number=rank,
        chunk_index=0,
        text=text,
        start_char=0,
        end_char=len(text),
    )

    return RerankedResult(
        chunk=chunk,
        retrieval_score=5.0,
        narrative_score=2.0,
        final_score=7.0,
        rank=rank,
    )


def test_evaluation_detects_rank_one_hit():
    case = RetrievalEvaluationCase(
        query="What drove production?",
        relevant_chunk_ids=frozenset(
            {"relevant"}
        ),
    )

    result = evaluate_retrieval_case(
        case=case,
        results=(
            _result("relevant", 1),
            _result("other", 2),
        ),
    )

    assert result.first_relevant_rank == 1
    assert result.hit_at_1 is True
    assert result.hit_at_3 is True
    assert result.reciprocal_rank == 1.0


def test_evaluation_detects_rank_three_hit():
    case = RetrievalEvaluationCase(
        query="What drove cash flow?",
        relevant_chunk_ids=frozenset(
            {"relevant"}
        ),
    )

    result = evaluate_retrieval_case(
        case=case,
        results=(
            _result("other-1", 1),
            _result("other-2", 2),
            _result("relevant", 3),
        ),
    )

    assert result.first_relevant_rank == 3
    assert result.hit_at_1 is False
    assert result.hit_at_3 is True
    assert result.reciprocal_rank == pytest.approx(
        1 / 3
    )


def test_evaluation_handles_missing_relevant_result():
    case = RetrievalEvaluationCase(
        query="What drove renewable generation?",
        relevant_chunk_ids=frozenset(
            {"missing"}
        ),
    )

    result = evaluate_retrieval_case(
        case=case,
        results=(
            _result("other", 1),
        ),
    )

    assert result.first_relevant_rank is None
    assert result.hit_at_1 is False
    assert result.hit_at_3 is False
    assert result.reciprocal_rank == 0.0


def test_summary_calculates_metrics():
    cases = (
        evaluate_retrieval_case(
            RetrievalEvaluationCase(
                query="query-1",
                relevant_chunk_ids=frozenset(
                    {"a"}
                ),
            ),
            (
                _result("a", 1),
            ),
        ),
        evaluate_retrieval_case(
            RetrievalEvaluationCase(
                query="query-2",
                relevant_chunk_ids=frozenset(
                    {"b"}
                ),
            ),
            (
                _result("other", 1),
                _result("b", 2),
            ),
        ),
        evaluate_retrieval_case(
            RetrievalEvaluationCase(
                query="query-3",
                relevant_chunk_ids=frozenset(
                    {"c"}
                ),
            ),
            (
                _result("other", 1),
            ),
        ),
    )

    summary = summarize_retrieval_evaluation(
        cases
    )

    assert summary.hit_at_1 == pytest.approx(
        1 / 3
    )

    assert summary.hit_at_3 == pytest.approx(
        2 / 3
    )

    assert summary.mean_reciprocal_rank == pytest.approx(
        0.5
    )


def test_empty_query_is_rejected():
    with pytest.raises(
        ValueError,
        match="query cannot be empty",
    ):
        evaluate_retrieval_case(
            RetrievalEvaluationCase(
                query=" ",
                relevant_chunk_ids=frozenset(
                    {"chunk"}
                ),
            ),
            (),
        )


def test_empty_relevant_set_is_rejected():
    with pytest.raises(
        ValueError,
        match="relevant_chunk_ids cannot be empty",
    ):
        evaluate_retrieval_case(
            RetrievalEvaluationCase(
                query="production",
                relevant_chunk_ids=frozenset(),
            ),
            (),
        )


def test_empty_summary_is_rejected():
    with pytest.raises(
        ValueError,
        match="case_results cannot be empty",
    ):
        summarize_retrieval_evaluation(())