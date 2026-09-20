from dataclasses import dataclass
from typing import Literal

from equitylens.retrieval import RetrievalResult
from equitylens.text_chunks import TextChunk

ScopeType = Literal[
    "group",
    "ep_norway",
    "ep_international",
    "ep_usa",
    "mmp",
    "power",
    "unknown",
]


_CAUSAL_PHRASES = (
    "driven by",
    "supported by",
    "due to",
    "primarily",
    "attributable to",
    "impacted by",
    "partially offset",
    "offset by",
    "contributed to",
    "contributed positively",
    "benefitting from",
    "benefited from",
    "generated",
    "reflecting",
)

_NARRATIVE_SECTION_PHRASES = (
    "financial results",
    "operations and financial results",
    "production and revenues",
    "cash flow and net debt",
)

_DEFINITION_PHRASES = (
    "our definition of",
    "does not represent",
    "represents, and is used by management",
    "use and reconciliation of non-gaap",
    "reconciliation of adjusted",
)

_FORWARD_LOOKING_SECTION_PHRASES = (
    "outlook",
    "guidance",
)

_HISTORICAL_DRIVER_QUERY_PHRASES = (
    "what drove",
    "what caused",
    "why did",
)

_QUERY_SCOPE_ALIASES = {
    "ep_norway": (
        "e&p norway",
        "exploration & production norway",
        "exploration and production norway",
    ),
    "ep_international": (
        "e&p international",
        "exploration & production international",
        "exploration and production international",
    ),
    "ep_usa": (
        "e&p usa",
        "exploration & production usa",
        "exploration and production usa",
    ),
    "mmp": (
        "mmp",
        "marketing, midstream & processing",
        "marketing, midstream and processing",
    ),
    "power": (
        "power segment",
        "power business area",
        "business area power",
    ),
}


@dataclass(frozen=True)
class RerankedResult:
    chunk: TextChunk
    retrieval_score: float
    narrative_score: float
    final_score: float
    rank: int
    scope_score: float = 0.0
    temporal_score: float = 0.0


def _normalize_scope_text(
    text: str,
) -> str:
    return " ".join(
        text.lower()
        .replace("&", "and")
        .replace(",", " ")
        .split()
    )


def _detect_query_scope(
    query: str,
) -> ScopeType:
    normalized_query = _normalize_scope_text(
        query
    )

    for scope, aliases in _QUERY_SCOPE_ALIASES.items():
        for alias in aliases:
            normalized_alias = _normalize_scope_text(
                alias
            )

            if normalized_alias in normalized_query:
                return scope

    return "group"


def _detect_chunk_scope(
    chunk: TextChunk,
) -> ScopeType:
    context = _normalize_scope_text(
        chunk.section_context
    )

    if not context:
        return "unknown"

    if context.startswith("group review"):
        return "group"

    if context.startswith(
        "exploration and production norway"
    ):
        return "ep_norway"

    if context.startswith(
        "exploration and production international"
    ):
        return "ep_international"

    if context.startswith(
        "exploration and production usa"
    ):
        return "ep_usa"

    if context.startswith(
        "marketing midstream and processing"
    ):
        return "mmp"

    if context.startswith("power "):
        return "power"

    return "unknown"


def calculate_scope_score(
    query: str,
    chunk: TextChunk,
) -> float:
    """
    Score whether a chunk matches the analytical scope of the query.

    Queries default to group scope unless an explicit segment is named.
    General page-level narrative remains eligible, while clearly
    segment-specific evidence is penalised for group-level questions.
    """

    query_scope = _detect_query_scope(
        query
    )

    chunk_scope = _detect_chunk_scope(
        chunk
    )

    if query_scope == "group":
        if chunk_scope == "group":
            return 3.0

        if chunk_scope == "unknown":
            return 1.0

        return -3.0

    if chunk_scope == query_scope:
        return 4.0

    if chunk_scope == "group":
        return 0.5

    if chunk_scope == "unknown":
        return 0.0

    return -3.0


def calculate_temporal_score(
    query: str,
    chunk: TextChunk,
) -> float:
    """
    Score whether a chunk matches the temporal intent of the query.

    Historical driver questions should prefer explanatory narrative
    about realised performance over explicitly forward-looking
    outlook or guidance sections. Queries that explicitly ask about
    guidance or outlook remain unaffected.
    """

    normalized_query = _normalize_scope_text(
        query
    )

    if (
        "guidance" in normalized_query
        or "outlook" in normalized_query
    ):
        return 0.0

    is_historical_driver_query = any(
        phrase in normalized_query
        for phrase in _HISTORICAL_DRIVER_QUERY_PHRASES
    )

    if not is_historical_driver_query:
        return 0.0

    normalized_context = _normalize_scope_text(
        chunk.section_context
    )

    is_forward_looking_section = any(
        phrase in normalized_context
        for phrase in _FORWARD_LOOKING_SECTION_PHRASES
    )

    if is_forward_looking_section:
        return -2.0

    return 0.0


def _numeric_token_ratio(text: str) -> float:
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


def _short_line_ratio(text: str) -> float:
    lines = [
        line.strip()
        for line in text.splitlines()
        if line.strip()
    ]

    if not lines:
        return 0.0

    short_lines = sum(
        len(line) <= 20
        for line in lines
    )

    return short_lines / len(lines)


def calculate_narrative_score(
    chunk: TextChunk,
) -> float:
    """
    Score how likely a chunk is to contain explanatory narrative.

    Positive scores reward causal management language. Negative scores
    penalise table-heavy and definition-heavy content.
    """

    normalized_text = chunk.text.lower()

    score = 0.0

    causal_hits = sum(
        phrase in normalized_text
        for phrase in _CAUSAL_PHRASES
    )

    score += min(
        causal_hits,
        3,
    ) * 1.5

    narrative_section_hits = sum(
        phrase in normalized_text
        for phrase in _NARRATIVE_SECTION_PHRASES
    )

    score += min(
        narrative_section_hits,
        2,
    ) * 1.0

    definition_hits = sum(
        phrase in normalized_text
        for phrase in _DEFINITION_PHRASES
    )

    score -= definition_hits * 2.5

    numeric_ratio = _numeric_token_ratio(
        chunk.text
    )

    if numeric_ratio >= 0.30:
        score -= 3.0
    elif numeric_ratio >= 0.20:
        score -= 1.5

    short_line_ratio = _short_line_ratio(
        chunk.text
    )

    if short_line_ratio >= 0.60:
        score -= 2.0
    elif short_line_ratio >= 0.45:
        score -= 1.0

    return score


class NarrativeEvidenceReranker:
    """
    Deterministically rerank lexical retrieval candidates using
    narrative quality, analytical scope and temporal intent.
    """

    def rerank(
        self,
        results: tuple[RetrievalResult, ...],
        query: str,
        top_k: int | None = None,
    ) -> tuple[RerankedResult, ...]:
        if not results:
            raise ValueError(
                "results cannot be empty."
            )

        if not query.strip():
            raise ValueError(
                "query cannot be empty."
            )

        if top_k is not None and top_k < 1:
            raise ValueError(
                "top_k must be greater than zero."
            )

        scored_results = []

        for result in results:
            narrative_score = (
                calculate_narrative_score(
                    result.chunk
                )
            )

            scope_score = calculate_scope_score(
                query=query,
                chunk=result.chunk,
            )

            temporal_score = calculate_temporal_score(
                query=query,
                chunk=result.chunk,
            )

            final_score = (
                result.score
                + narrative_score
                + scope_score
                + temporal_score
            )

            scored_results.append(
                (
                    result,
                    narrative_score,
                    scope_score,
                    temporal_score,
                    final_score,
                )
            )

        ranked_results = sorted(
            scored_results,
            key=lambda item: (
                -item[4],
                item[0].rank,
                item[0].chunk.document_id,
                item[0].chunk.page_number,
                item[0].chunk.chunk_index,
            ),
        )

        if top_k is not None:
            ranked_results = ranked_results[
                :top_k
            ]

        return tuple(
            RerankedResult(
                chunk=result.chunk,
                retrieval_score=result.score,
                narrative_score=narrative_score,
                scope_score=scope_score,
                temporal_score=temporal_score,
                final_score=final_score,
                rank=rank,
            )
            for rank, (
                result,
                narrative_score,
                scope_score,
                temporal_score,
                final_score,
            ) in enumerate(
                ranked_results,
                start=1,
            )
        )