import re
from collections import Counter
from dataclasses import dataclass
from typing import Literal

from equitylens.evidence_gate import (
    EvidenceGateResult,
    EvidenceGateStatus,
    assess_sentence_evidence,
)
from equitylens.evidence_scope import (
    assess_scope_compatibility,
    resolve_evidence_scope,
)
from equitylens.evidence_sentences import (
    EvidenceSentence,
    split_chunk_into_sentences,
)
from equitylens.metrics import MetricScope
from equitylens.narrative_reranker import RerankedResult
from equitylens.periods import ComparisonType

EvidenceAvailability = Literal[
    "direct_explanation",
    "aligned_context_only",
    "unavailable",
]

EvidenceAssessmentRejectionStatus = (
    EvidenceGateStatus
    | Literal[
        "scope_mismatch",
        "scope_unknown",
    ]
)


_ANAPHORIC_OUTCOME_PATTERN = re.compile(
    (
        r"^\s*(?:the|this)\s+"
        r"(?:slight\s+)?"
        r"(?:increase|decrease|decline|reduction|improvement|change)\b"
    ),
    re.IGNORECASE,
)


@dataclass(frozen=True)
class AssessedEvidence:
    sentence: EvidenceSentence
    gate: EvidenceGateResult
    chunk_rank: int
    retrieval_score: float
    final_score: float
    context_sentences: tuple[
        EvidenceSentence,
        ...,
    ] = ()


@dataclass(frozen=True)
class EvidenceAssessment:
    query: str
    expected_comparison_type: ComparisonType
    availability: EvidenceAvailability
    direct_explanations: tuple[AssessedEvidence, ...]
    aligned_context: tuple[AssessedEvidence, ...]
    rejection_counts: tuple[
        tuple[
            EvidenceAssessmentRejectionStatus,
            int,
        ],
        ...,
    ]


def _sentence_key(
    sentence: EvidenceSentence,
) -> tuple[
    str,
    int,
    int,
    int,
    str,
]:
    return (
        sentence.document_id,
        sentence.page_number,
        sentence.page_start_char,
        sentence.page_end_char,
        sentence.text.strip(),
    )


def _is_adjacent_context_explanation(
    expected_comparison_type: ComparisonType,
    context_sentence: EvidenceSentence,
    context_gate: EvidenceGateResult,
    causal_sentence: EvidenceSentence,
    causal_gate: EvidenceGateResult,
) -> bool:
    """
    Determine whether two immediately adjacent sentences jointly form
    a direct explanation.

    The first sentence must independently establish the queried metric
    and the expected comparison basis. The following sentence must
    contain causal language and explicitly refer back to the preceding
    outcome through a directional anaphor such as "the decrease".

    Comparison context is never inherited from arbitrary chunk text.
    """

    if context_gate.status != "aligned_context":
        return False

    if (
        context_gate.detected_comparison_types
        != frozenset(
            {expected_comparison_type}
        )
    ):
        return False

    if not context_gate.metric_match:
        return False

    if causal_gate.detected_comparison_types:
        return False

    if not causal_gate.causal_signal:
        return False

    if (
        context_sentence.document_id
        != causal_sentence.document_id
    ):
        return False

    if (
        context_sentence.page_number
        != causal_sentence.page_number
    ):
        return False

    if (
        context_sentence.chunk_id
        != causal_sentence.chunk_id
    ):
        return False

    if (
        context_sentence.sentence_index + 1
        != causal_sentence.sentence_index
    ):
        return False

    return (
        _ANAPHORIC_OUTCOME_PATTERN.search(
            causal_sentence.text
        )
        is not None
    )


def _build_adjacent_direct_gate(
    context_gate: EvidenceGateResult,
    causal_sentence: EvidenceSentence,
) -> EvidenceGateResult:
    return EvidenceGateResult(
        sentence_id=causal_sentence.sentence_id,
        status="direct_explanation",
        query_subject=context_gate.query_subject,
        detected_comparison_types=(
            context_gate.detected_comparison_types
        ),
        metric_match=True,
        causal_signal=True,
        usable_as_direct_explanation=True,
        reason=(
            "The immediately preceding sentence establishes "
            "the queried metric and matching comparison basis, "
            "and this sentence explicitly refers back to that "
            "outcome using causal language."
        ),
    )


def _remove_aligned_context(
    aligned_context: list[AssessedEvidence],
    sentence: EvidenceSentence,
) -> None:
    key = _sentence_key(
        sentence
    )

    aligned_context[:] = [
        evidence
        for evidence in aligned_context
        if _sentence_key(
            evidence.sentence
        )
        != key
    ]


def _scope_rejection_status(
    metric_scope: MetricScope | None,
    result: RerankedResult,
) -> (
    Literal[
        "scope_mismatch",
        "scope_unknown",
    ]
    | None
):
    if metric_scope is None:
        return None

    evidence_scope = resolve_evidence_scope(
        document_id=result.chunk.document_id,
        section_context=(
            result.chunk.section_context
        ),
    )

    compatibility = assess_scope_compatibility(
        metric_scope=metric_scope,
        evidence_scope=evidence_scope,
    )

    if compatibility == "compatible":
        return None

    if compatibility == "mismatched":
        return "scope_mismatch"

    return "scope_unknown"


def assess_retrieved_evidence(
    query: str,
    expected_comparison_type: ComparisonType,
    results: tuple[RerankedResult, ...],
    metric_scope: MetricScope | None = None,
) -> EvidenceAssessment:
    """
    Assess retrieved narrative evidence at sentence level.

    Direct explanations may be supported either by one sentence that
    independently passes all evidence gates, or by a tightly controlled
    pair of adjacent sentences where:

    1. the first sentence establishes the queried metric and matching
       comparison basis, and
    2. the immediately following sentence explicitly refers back to the
       outcome and supplies the causal explanation.

    When metric_scope is provided, narrative evidence must also have
    compatible analytical scope. Mismatched or unresolved scope cannot
    be promoted to aligned context or direct explanation.

    Both sentences retain their original provenance.
    """

    if not query.strip():
        raise ValueError(
            "query cannot be empty."
        )

    seen_sentences: set[
        tuple[
            str,
            int,
            int,
            int,
            str,
        ]
    ] = set()

    direct_explanations: list[
        AssessedEvidence
    ] = []

    aligned_context: list[
        AssessedEvidence
    ] = []

    rejection_counter: Counter[
        EvidenceAssessmentRejectionStatus
    ] = Counter()

    for result in results:
        sentences = split_chunk_into_sentences(
            result.chunk
        )

        gates = tuple(
            assess_sentence_evidence(
                query=query,
                expected_comparison_type=(
                    expected_comparison_type
                ),
                sentence=sentence,
            )
            for sentence in sentences
        )

        scope_rejection = (
            _scope_rejection_status(
                metric_scope=metric_scope,
                result=result,
            )
        )

        for index, (
            sentence,
            gate,
        ) in enumerate(
            zip(
                sentences,
                gates,
                strict=True,
            )
        ):
            key = _sentence_key(
                sentence
            )

            if key in seen_sentences:
                continue

            seen_sentences.add(
                key
            )

            if (
                scope_rejection is not None
                and gate.status
                in {
                    "direct_explanation",
                    "aligned_context",
                }
            ):
                rejection_counter[
                    scope_rejection
                ] += 1

                continue

            adjacent_context: (
                EvidenceSentence | None
            ) = None

            adjacent_gate: (
                EvidenceGateResult | None
            ) = None

            if (
                scope_rejection is None
                and index > 0
            ):
                candidate_context = (
                    sentences[index - 1]
                )

                candidate_context_gate = (
                    gates[index - 1]
                )

                if _is_adjacent_context_explanation(
                    expected_comparison_type=(
                        expected_comparison_type
                    ),
                    context_sentence=(
                        candidate_context
                    ),
                    context_gate=(
                        candidate_context_gate
                    ),
                    causal_sentence=sentence,
                    causal_gate=gate,
                ):
                    adjacent_context = (
                        candidate_context
                    )

                    adjacent_gate = (
                        _build_adjacent_direct_gate(
                            context_gate=(
                                candidate_context_gate
                            ),
                            causal_sentence=sentence,
                        )
                    )

            if gate.status == "direct_explanation":
                direct_explanations.append(
                    AssessedEvidence(
                        sentence=sentence,
                        gate=gate,
                        chunk_rank=result.rank,
                        retrieval_score=(
                            result.retrieval_score
                        ),
                        final_score=(
                            result.final_score
                        ),
                    )
                )

                continue

            if (
                adjacent_context is not None
                and adjacent_gate is not None
            ):
                _remove_aligned_context(
                    aligned_context=aligned_context,
                    sentence=adjacent_context,
                )

                direct_explanations.append(
                    AssessedEvidence(
                        sentence=sentence,
                        gate=adjacent_gate,
                        chunk_rank=result.rank,
                        retrieval_score=(
                            result.retrieval_score
                        ),
                        final_score=(
                            result.final_score
                        ),
                        context_sentences=(
                            adjacent_context,
                        ),
                    )
                )

                continue

            assessed = AssessedEvidence(
                sentence=sentence,
                gate=gate,
                chunk_rank=result.rank,
                retrieval_score=(
                    result.retrieval_score
                ),
                final_score=result.final_score,
            )

            if gate.status == "aligned_context":
                aligned_context.append(
                    assessed
                )

            else:
                rejection_counter[
                    gate.status
                ] += 1

    if direct_explanations:
        availability: EvidenceAvailability = (
            "direct_explanation"
        )

    elif aligned_context:
        availability = (
            "aligned_context_only"
        )

    else:
        availability = "unavailable"

    return EvidenceAssessment(
        query=query,
        expected_comparison_type=(
            expected_comparison_type
        ),
        availability=availability,
        direct_explanations=tuple(
            direct_explanations
        ),
        aligned_context=tuple(
            aligned_context
        ),
        rejection_counts=tuple(
            sorted(
                rejection_counter.items()
            )
        ),
    )