from dataclasses import dataclass

from equitylens.narrative_reranker import RerankedResult


@dataclass(frozen=True)
class RetrievalEvaluationCase:
    query: str
    relevant_chunk_ids: frozenset[str]


@dataclass(frozen=True)
class RetrievalCaseResult:
    query: str
    first_relevant_rank: int | None
    hit_at_1: bool
    hit_at_3: bool
    reciprocal_rank: float


@dataclass(frozen=True)
class RetrievalEvaluationSummary:
    case_results: tuple[RetrievalCaseResult, ...]
    hit_at_1: float
    hit_at_3: float
    mean_reciprocal_rank: float


def evaluate_retrieval_case(
    case: RetrievalEvaluationCase,
    results: tuple[RerankedResult, ...],
) -> RetrievalCaseResult:
    if not case.query.strip():
        raise ValueError("query cannot be empty.")

    if not case.relevant_chunk_ids:
        raise ValueError(
            "relevant_chunk_ids cannot be empty."
        )

    first_relevant_rank = next(
        (
            result.rank
            for result in results
            if result.chunk.chunk_id
            in case.relevant_chunk_ids
        ),
        None,
    )

    reciprocal_rank = (
        0.0
        if first_relevant_rank is None
        else 1.0 / first_relevant_rank
    )

    return RetrievalCaseResult(
        query=case.query,
        first_relevant_rank=first_relevant_rank,
        hit_at_1=first_relevant_rank == 1,
        hit_at_3=(
            first_relevant_rank is not None
            and first_relevant_rank <= 3
        ),
        reciprocal_rank=reciprocal_rank,
    )


def summarize_retrieval_evaluation(
    case_results: tuple[RetrievalCaseResult, ...],
) -> RetrievalEvaluationSummary:
    if not case_results:
        raise ValueError(
            "case_results cannot be empty."
        )

    case_count = len(case_results)

    hit_at_1 = (
        sum(
            result.hit_at_1
            for result in case_results
        )
        / case_count
    )

    hit_at_3 = (
        sum(
            result.hit_at_3
            for result in case_results
        )
        / case_count
    )

    mean_reciprocal_rank = (
        sum(
            result.reciprocal_rank
            for result in case_results
        )
        / case_count
    )

    return RetrievalEvaluationSummary(
        case_results=case_results,
        hit_at_1=hit_at_1,
        hit_at_3=hit_at_3,
        mean_reciprocal_rank=mean_reciprocal_rank,
    )