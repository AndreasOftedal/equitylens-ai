import pytest

from equitylens.narrative_reranker import (
    NarrativeEvidenceReranker,
    calculate_narrative_score,
    calculate_scope_score,
    calculate_temporal_score,
)
from equitylens.retrieval import RetrievalResult
from equitylens.text_chunks import TextChunk


def _chunk(
    chunk_id: str,
    text: str,
    page_number: int,
    section_context: str = "",
) -> TextChunk:
    return TextChunk(
        chunk_id=chunk_id,
        document_id="report",
        page_number=page_number,
        chunk_index=0,
        text=text,
        start_char=0,
        end_char=len(text),
        section_context=section_context,
    )


def _result(
    chunk: TextChunk,
    score: float,
    rank: int,
) -> RetrievalResult:
    return RetrievalResult(
        chunk=chunk,
        score=score,
        rank=rank,
    )


def test_causal_narrative_receives_positive_score():
    chunk = _chunk(
        chunk_id="narrative",
        page_number=5,
        text=(
            "Financial results were primarily driven by "
            "higher liquids prices and supported by "
            "strong production."
        ),
    )

    assert calculate_narrative_score(
        chunk
    ) > 0


def test_numeric_table_like_chunk_is_penalised():
    chunk = _chunk(
        chunk_id="table",
        page_number=4,
        text=(
            "Q2 2026\n"
            "Q1 2026\n"
            "Q2 2025\n"
            "12,993\n"
            "8,784\n"
            "5,721\n"
            "49%\n"
            "21,776\n"
            "14,595\n"
        ),
    )

    assert calculate_narrative_score(
        chunk
    ) < 0


def test_definition_chunk_is_penalised():
    chunk = _chunk(
        chunk_id="definition",
        page_number=41,
        text=(
            "Our definition of cash flow does not represent "
            "residual cash flows available for discretionary "
            "expenditures."
        ),
    )

    assert calculate_narrative_score(
        chunk
    ) < 0


def test_group_query_rewards_group_context():
    chunk = _chunk(
        chunk_id="group",
        page_number=8,
        text="Group financial results.",
        section_context=(
            "Group review Operations and financial results"
        ),
    )

    assert calculate_scope_score(
        query="What drove net operating income?",
        chunk=chunk,
    ) == 3.0


def test_group_query_penalises_segment_context():
    chunk = _chunk(
        chunk_id="mmp",
        page_number=16,
        text="Segment financial results.",
        section_context=(
            "Marketing, Midstream & Processing "
            "Volumes, pricing and revenues"
        ),
    )

    assert calculate_scope_score(
        query="What drove adjusted operating income?",
        chunk=chunk,
    ) == -3.0


def test_general_power_metric_query_remains_group_scope():
    chunk = _chunk(
        chunk_id="power-segment",
        page_number=17,
        text="Power segment narrative.",
        section_context="Power Power generation",
    )

    assert calculate_scope_score(
        query="What drove renewable power generation?",
        chunk=chunk,
    ) == -3.0


def test_explicit_segment_query_rewards_matching_segment():
    chunk = _chunk(
        chunk_id="mmp",
        page_number=16,
        text="MMP financial results.",
        section_context=(
            "Marketing, Midstream & Processing "
            "Volumes, pricing and revenues"
        ),
    )

    assert calculate_scope_score(
        query="What drove MMP adjusted operating income?",
        chunk=chunk,
    ) == 4.0


def test_general_narrative_remains_eligible_for_group_query():
    chunk = _chunk(
        chunk_id="general",
        page_number=5,
        text="General company financial commentary.",
        section_context=(
            "More energy through strong production"
        ),
    )

    assert calculate_scope_score(
        query="What drove net operating income?",
        chunk=chunk,
    ) == 1.0


def test_historical_driver_query_penalises_forward_looking_section():
    chunk = _chunk(
        chunk_id="guidance",
        page_number=16,
        text=(
            "Production guidance for 2026 "
            "is 380-400 mboepd."
        ),
        section_context="OUTLOOK Guidance for 2026",
    )

    assert calculate_temporal_score(
        query="What drove production?",
        chunk=chunk,
    ) == -2.0


def test_guidance_query_does_not_penalise_forward_looking_section():
    chunk = _chunk(
        chunk_id="guidance",
        page_number=16,
        text=(
            "Production guidance for 2026 "
            "is 380-400 mboepd."
        ),
        section_context="OUTLOOK Guidance for 2026",
    )

    assert calculate_temporal_score(
        query="What is the production guidance?",
        chunk=chunk,
    ) == 0.0


def test_historical_driver_query_does_not_penalise_historical_section():
    chunk = _chunk(
        chunk_id="historical",
        page_number=8,
        text=(
            "Production decreased due to "
            "planned maintenance."
        ),
        section_context="Operational review",
    )

    assert calculate_temporal_score(
        query="What drove production?",
        chunk=chunk,
    ) == 0.0


def test_scope_aware_reranker_can_promote_group_evidence():
    segment_chunk = _chunk(
        chunk_id="segment",
        page_number=16,
        text=(
            "Results were primarily driven by strong "
            "trading and supported by higher margins."
        ),
        section_context=(
            "Marketing, Midstream & Processing "
            "Volumes, pricing and revenues"
        ),
    )

    group_chunk = _chunk(
        chunk_id="group",
        page_number=8,
        text=(
            "Operations and financial results were driven "
            "by strong production and higher prices."
        ),
        section_context=(
            "Group review Operations and financial results"
        ),
    )

    results = (
        _result(
            chunk=segment_chunk,
            score=8.0,
            rank=1,
        ),
        _result(
            chunk=group_chunk,
            score=6.0,
            rank=2,
        ),
    )

    reranked = NarrativeEvidenceReranker().rerank(
        results=results,
        query="What drove net operating income?",
    )

    assert reranked[0].chunk.chunk_id == "group"
    assert reranked[0].scope_score == 3.0
    assert reranked[1].scope_score == -3.0


def test_driver_query_prefers_historical_explanation_over_guidance():
    guidance_chunk = _chunk(
        chunk_id="guidance",
        page_number=16,
        text=(
            "Guidance for 2026. Production: "
            "380-400 mboepd."
        ),
        section_context="OUTLOOK Guidance for 2026",
    )

    historical_chunk = _chunk(
        chunk_id="historical-explanation",
        page_number=8,
        text=(
            "Production decreased due to "
            "planned maintenance during the quarter."
        ),
        section_context="Operational review",
    )

    results = (
        _result(
            chunk=guidance_chunk,
            score=8.0,
            rank=1,
        ),
        _result(
            chunk=historical_chunk,
            score=6.0,
            rank=2,
        ),
    )

    reranked = NarrativeEvidenceReranker().rerank(
        results=results,
        query="What drove production?",
    )

    assert (
        reranked[0].chunk.chunk_id
        == "historical-explanation"
    )

    assert reranked[1].temporal_score == -2.0


def test_reranker_preserves_source_provenance():
    chunk = _chunk(
        chunk_id="narrative",
        page_number=9,
        text=(
            "Cash flow was driven by higher "
            "commodity prices."
        ),
    )

    result = _result(
        chunk=chunk,
        score=5.0,
        rank=1,
    )

    reranked = NarrativeEvidenceReranker().rerank(
        results=(result,),
        query="What drove cash flow?",
    )[0]

    assert reranked.chunk.chunk_id == "narrative"
    assert reranked.chunk.document_id == "report"
    assert reranked.chunk.page_number == 9


def test_reranker_respects_top_k():
    results = tuple(
        _result(
            chunk=_chunk(
                chunk_id=f"chunk-{index}",
                page_number=index + 1,
                text=(
                    "Results were driven by "
                    f"factor {index}."
                ),
            ),
            score=float(10 - index),
            rank=index + 1,
        )
        for index in range(5)
    )

    reranked = NarrativeEvidenceReranker().rerank(
        results=results,
        query="What drove results?",
        top_k=2,
    )

    assert len(reranked) == 2

    assert tuple(
        result.rank
        for result in reranked
    ) == (
        1,
        2,
    )


def test_empty_result_collection_is_rejected():
    with pytest.raises(
        ValueError,
        match="results cannot be empty",
    ):
        NarrativeEvidenceReranker().rerank(
            results=(),
            query="What drove results?",
        )


def test_empty_query_is_rejected():
    chunk = _chunk(
        chunk_id="chunk",
        page_number=1,
        text="Results were driven by higher prices.",
    )

    with pytest.raises(
        ValueError,
        match="query cannot be empty",
    ):
        NarrativeEvidenceReranker().rerank(
            results=(
                _result(
                    chunk=chunk,
                    score=5.0,
                    rank=1,
                ),
            ),
            query=" ",
        )


def test_invalid_top_k_is_rejected():
    chunk = _chunk(
        chunk_id="chunk",
        page_number=1,
        text="Results were driven by higher prices.",
    )

    with pytest.raises(
        ValueError,
        match="top_k must be greater than zero",
    ):
        NarrativeEvidenceReranker().rerank(
            results=(
                _result(
                    chunk=chunk,
                    score=5.0,
                    rank=1,
                ),
            ),
            query="What drove results?",
            top_k=0,
        )