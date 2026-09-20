from dataclasses import asdict, dataclass
from typing import Literal

from equitylens.consistency import (
    ConsistencyStatus,
    FinancialDirection,
)
from equitylens.guidance import (
    GuidanceCategory,
    GuidanceChangeType,
)
from equitylens.periods import ComparisonType
from equitylens.research_pipeline import (
    UnifiedResearchResult,
)

SynthesisEvidenceAvailability = Literal[
    "not_evaluated",
    "direct_explanation",
    "aligned_context_only",
    "unavailable",
]


EvidenceRole = Literal[
    "direct_explanation",
    "aligned_context",
]


@dataclass(frozen=True)
class SynthesisSourceRef:
    document_id: str
    page_number: int
    table_number: int | None
    row_label: str | None
    column_label: str | None


@dataclass(frozen=True)
class SynthesisSourceFact:
    fact_id: str
    metric_id: str
    period: str
    value: str
    unit: str
    source: SynthesisSourceRef


@dataclass(frozen=True)
class SynthesisNarrativeEvidence:
    role: EvidenceRole
    sentence_id: str
    document_id: str
    page_number: int
    text: str
    page_start_char: int
    page_end_char: int
    section_context: str


@dataclass(frozen=True)
class SynthesisMetric:
    metric_id: str
    from_period: str
    to_period: str
    from_value: str
    to_value: str
    absolute_change: str
    percentage_change: str
    unit: str
    comparison_type: ComparisonType
    financial_direction: FinancialDirection
    consistency_status: ConsistencyStatus
    consistency_reason: str
    evidence_availability: SynthesisEvidenceAvailability
    source_facts: tuple[SynthesisSourceFact, ...]
    direct_explanations: tuple[
        SynthesisNarrativeEvidence,
        ...,
    ]
    aligned_context: tuple[
        SynthesisNarrativeEvidence,
        ...,
    ]


@dataclass(frozen=True)
class SynthesisGuidanceItem:
    metric_id: str
    target_period: str
    category: GuidanceCategory
    document_id: str
    page_number: int
    section: str
    statement: str
    numeric_value: str | None
    unit: str | None
    qualifier: str | None
    qualitative_value: str | None
    numeric_lower_bound: str | None = None
    numeric_upper_bound: str | None = None


@dataclass(frozen=True)
class SynthesisGuidanceChange:
    metric_id: str
    target_period: str
    change_type: GuidanceChangeType
    previous: SynthesisGuidanceItem
    current: SynthesisGuidanceItem
    qualifier_changed: bool
    category_changed: bool


@dataclass(frozen=True)
class SynthesisInput:
    schema_version: str
    company: str
    ticker: str
    from_period: str
    to_period: str
    previous_document_id: str
    current_document_id: str
    metrics: tuple[SynthesisMetric, ...]
    guidance_changes: tuple[
        SynthesisGuidanceChange,
        ...,
    ]
    guidance_introduced: tuple[
        SynthesisGuidanceItem,
        ...,
    ]
    guidance_withdrawn: tuple[
        SynthesisGuidanceItem,
        ...,
    ]

    def to_dict(
        self,
    ) -> dict[str, object]:
        return asdict(self)


def _build_source_ref(
    evidence,
) -> SynthesisSourceRef:
    return SynthesisSourceRef(
        document_id=evidence.document_id,
        page_number=evidence.page_number,
        table_number=evidence.table_number,
        row_label=evidence.row_label,
        column_label=evidence.column_label,
    )


def _build_source_fact(
    fact,
) -> SynthesisSourceFact:
    return SynthesisSourceFact(
        fact_id=fact.fact_id,
        metric_id=fact.metric,
        period=fact.period,
        value=str(fact.value),
        unit=fact.unit,
        source=_build_source_ref(
            fact.evidence
        ),
    )


def _build_narrative_evidence(
    assessed_evidence,
    role: EvidenceRole,
) -> SynthesisNarrativeEvidence:
    sentence = assessed_evidence.sentence

    return SynthesisNarrativeEvidence(
        role=role,
        sentence_id=sentence.sentence_id,
        document_id=sentence.document_id,
        page_number=sentence.page_number,
        text=sentence.text,
        page_start_char=(
            sentence.page_start_char
        ),
        page_end_char=(
            sentence.page_end_char
        ),
        section_context=(
            sentence.section_context
        ),
    )


def _build_metric(
    metric_result,
    consistency,
) -> SynthesisMetric:
    change = metric_result.change

    evidence_assessment = (
        metric_result.evidence_assessment
    )

    if evidence_assessment is None:
        evidence_availability: (
            SynthesisEvidenceAvailability
        ) = "not_evaluated"

        direct_explanations = ()
        aligned_context = ()

    else:
        evidence_availability = (
            evidence_assessment.availability
        )

        direct_explanations = tuple(
            _build_narrative_evidence(
                assessed_evidence=evidence,
                role="direct_explanation",
            )
            for evidence
            in evidence_assessment.direct_explanations
        )

        aligned_context = tuple(
            _build_narrative_evidence(
                assessed_evidence=evidence,
                role="aligned_context",
            )
            for evidence
            in evidence_assessment.aligned_context
        )

    source_facts = tuple(
        _build_source_fact(
            fact
        )
        for fact
        in metric_result.audit_trail.source_facts
    )

    return SynthesisMetric(
        metric_id=metric_result.metric_id,
        from_period=change.from_period,
        to_period=change.to_period,
        from_value=str(
            change.from_value
        ),
        to_value=str(
            change.to_value
        ),
        absolute_change=str(
            change.absolute_change
        ),
        percentage_change=str(
            change.percentage_change
        ),
        unit=change.unit,
        comparison_type=(
            change.comparison_type
        ),
        financial_direction=(
            consistency.financial_direction
        ),
        consistency_status=(
            consistency.status
        ),
        consistency_reason=(
            consistency.reason
        ),
        evidence_availability=(
            evidence_availability
        ),
        source_facts=source_facts,
        direct_explanations=(
            direct_explanations
        ),
        aligned_context=(
            aligned_context
        ),
    )


def _build_guidance_item(
    item,
) -> SynthesisGuidanceItem:
    numeric_lower_bound = getattr(
        item,
        "numeric_lower_bound",
        None,
    )

    numeric_upper_bound = getattr(
        item,
        "numeric_upper_bound",
        None,
    )

    return SynthesisGuidanceItem(
        metric_id=item.metric_id,
        target_period=item.target_period,
        category=item.category,
        document_id=item.document_id,
        page_number=item.page_number,
        section=item.section,
        statement=item.statement,
        numeric_value=(
            str(item.numeric_value)
            if item.numeric_value is not None
            else None
        ),
        unit=item.unit,
        qualifier=item.qualifier,
        qualitative_value=(
            item.qualitative_value
        ),
        numeric_lower_bound=(
            str(numeric_lower_bound)
            if numeric_lower_bound is not None
            else None
        ),
        numeric_upper_bound=(
            str(numeric_upper_bound)
            if numeric_upper_bound is not None
            else None
        ),
    )


def _build_guidance_change(
    change,
) -> SynthesisGuidanceChange:
    return SynthesisGuidanceChange(
        metric_id=change.metric_id,
        target_period=change.target_period,
        change_type=change.change_type,
        previous=_build_guidance_item(
            change.previous
        ),
        current=_build_guidance_item(
            change.current
        ),
        qualifier_changed=(
            change.qualifier_changed
        ),
        category_changed=(
            change.category_changed
        ),
    )


def build_synthesis_input(
    research_result: UnifiedResearchResult,
) -> SynthesisInput:
    analyst_report = (
        research_result.analyst_report
    )

    guidance_report = (
        research_result.guidance_report
    )

    metric_results = (
        analyst_report.metric_results
    )

    metric_ids = tuple(
        result.metric_id
        for result
        in metric_results
    )

    if len(metric_ids) != len(
        set(metric_ids)
    ):
        raise ValueError(
            "Analyst report contains duplicate "
            "metric_ids."
        )

    consistency_by_metric = {}

    for assessment in (
        research_result
        .consistency_assessments
    ):
        if (
            assessment.metric_id
            in consistency_by_metric
        ):
            raise ValueError(
                "Consistency assessments contain "
                "duplicate metric_ids."
            )

        consistency_by_metric[
            assessment.metric_id
        ] = assessment

    consistency_metric_ids = set(
        consistency_by_metric
    )

    expected_metric_ids = set(
        metric_ids
    )

    if (
        consistency_metric_ids
        != expected_metric_ids
    ):
        missing = sorted(
            expected_metric_ids
            - consistency_metric_ids
        )

        extra = sorted(
            consistency_metric_ids
            - expected_metric_ids
        )

        raise ValueError(
            "Consistency assessments must match "
            "analyst report metrics exactly. "
            f"Missing: {missing}. Extra: {extra}."
        )

    metrics = tuple(
        _build_metric(
            metric_result=result,
            consistency=(
                consistency_by_metric[
                    result.metric_id
                ]
            ),
        )
        for result
        in metric_results
    )

    guidance_changes = tuple(
        _build_guidance_change(
            change
        )
        for change
        in guidance_report.changes
    )

    guidance_introduced = tuple(
        _build_guidance_item(
            item
        )
        for item
        in guidance_report.introduced
    )

    guidance_withdrawn = tuple(
        _build_guidance_item(
            item
        )
        for item
        in guidance_report.withdrawn
    )

    return SynthesisInput(
        schema_version="1.0",
        company=analyst_report.company,
        ticker=analyst_report.ticker,
        from_period=(
            analyst_report.from_period
        ),
        to_period=(
            analyst_report.to_period
        ),
        previous_document_id=(
            guidance_report
            .previous_document_id
        ),
        current_document_id=(
            guidance_report
            .current_document_id
        ),
        metrics=metrics,
        guidance_changes=(
            guidance_changes
        ),
        guidance_introduced=(
            guidance_introduced
        ),
        guidance_withdrawn=(
            guidance_withdrawn
        ),
    )