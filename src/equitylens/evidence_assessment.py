from collections import Counter
from dataclasses import dataclass
from typing import Literal

from equitylens.evidence_gate import (
    EvidenceGateResult,
    EvidenceGateStatus,
    assess_sentence_evidence,
)
from equitylens.evidence_sentences import (
    EvidenceSentence,
    split_chunk_into_sentences,
)
from equitylens.narrative_reranker import RerankedResult
from equitylens.periods import ComparisonType

EvidenceAvailability = Literal[
    "direct_explanation",
    "aligned_context_only",
    "unavailable",
]


@dataclass(frozen=True)
class AssessedEvidence:
    sentence: EvidenceSentence
    gate: EvidenceGateResult
    chunk_rank: int
    retrieval_score: float
    final_score: float


@dataclass(frozen=True)
class EvidenceAssessment:
    query: str
    expected_comparison_type: ComparisonType
    availability: EvidenceAvailability
    direct_explanations: tuple[AssessedEvidence, ...]
    aligned_context: tuple[AssessedEvidence, ...]
    rejection_counts: tuple[
        tuple[EvidenceGateStatus, int],
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


def assess_retrieved_evidence(
    query: str,
    expected_comparison_type: ComparisonType,
    results: tuple[RerankedResult, ...],
) -> EvidenceAssessment:
    """
    Assess retrieved narrative evidence at sentence level.

    Only sentences that pass metric-outcome, comparison-basis,
    causal-language and narrative-quality checks are treated as
    direct explanations.

    Overlapping retrieval chunks may contain the same sentence.
    Sentence-level provenance is therefore used to deduplicate
    evidence deterministically.
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
        EvidenceGateStatus
    ] = Counter()

    for result in results:
        sentences = split_chunk_into_sentences(
            result.chunk
        )

        for sentence in sentences:
            key = _sentence_key(
                sentence
            )

            if key in seen_sentences:
                continue

            seen_sentences.add(
                key
            )

            gate = assess_sentence_evidence(
                query=query,
                expected_comparison_type=(
                    expected_comparison_type
                ),
                sentence=sentence,
            )

            assessed = AssessedEvidence(
                sentence=sentence,
                gate=gate,
                chunk_rank=result.rank,
                retrieval_score=(
                    result.retrieval_score
                ),
                final_score=result.final_score,
            )

            if gate.status == "direct_explanation":
                direct_explanations.append(
                    assessed
                )

            elif gate.status == "aligned_context":
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