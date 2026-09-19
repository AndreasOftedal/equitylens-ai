from types import SimpleNamespace

import pytest

from equitylens import research_pipeline
from equitylens.analysis_pipeline import (
    PeriodSource,
)


def _document(
    document_id: str,
    reporting_period: str,
):
    return SimpleNamespace(
        document_id=document_id,
        reporting_period=reporting_period,
        local_path=f"{document_id}.pdf",
    )


def _sources():
    return (
        PeriodSource(
            document=_document(
                "q1-document",
                "Q1 2026",
            ),
            page_number=4,
        ),
        PeriodSource(
            document=_document(
                "q2-document",
                "Q2 2026",
            ),
            page_number=4,
        ),
    )


def test_unified_pipeline_connects_existing_components(
    monkeypatch,
):
    previous_source, current_source = (
        _sources()
    )

    fake_dataset = object()
    fake_previous_pages = [
        SimpleNamespace(
            document_id="q1-document"
        )
    ]
    fake_current_pages = [
        SimpleNamespace(
            document_id="q2-document"
        )
    ]
    fake_evidence = {
        "net_operating_income": object()
    }
    fake_analyst_report = object()
    fake_guidance_report = object()

    dataset_calls = []
    parse_calls = []
    evidence_calls = []
    analyst_calls = []
    guidance_calls = []

    def fake_build_dataset(
        sources,
        metric_ids,
    ):
        dataset_calls.append(
            (
                sources,
                metric_ids,
            )
        )
        return fake_dataset

    def fake_parse_pdf(
        document_id,
        pdf_path,
    ):
        parse_calls.append(
            (
                document_id,
                pdf_path,
            )
        )

        if document_id == "q1-document":
            return fake_previous_pages

        return fake_current_pages

    def fake_build_evidence(
        **kwargs,
    ):
        evidence_calls.append(
            kwargs
        )
        return fake_evidence

    def fake_build_analyst(
        **kwargs,
    ):
        analyst_calls.append(
            kwargs
        )
        return fake_analyst_report

    def fake_build_guidance(
        **kwargs,
    ):
        guidance_calls.append(
            kwargs
        )
        return fake_guidance_report

    monkeypatch.setattr(
        research_pipeline,
        "build_multi_period_financial_dataset",
        fake_build_dataset,
    )

    monkeypatch.setattr(
        research_pipeline,
        "parse_pdf",
        fake_parse_pdf,
    )

    monkeypatch.setattr(
        research_pipeline,
        "build_evidence_assessments",
        fake_build_evidence,
    )

    monkeypatch.setattr(
        research_pipeline,
        "build_analyst_report",
        fake_build_analyst,
    )

    monkeypatch.setattr(
        research_pipeline,
        "build_equinor_guidance_report",
        fake_build_guidance,
    )

    result = (
        research_pipeline
        .build_equinor_research_result(
            previous_source=(
                previous_source
            ),
            current_source=(
                current_source
            ),
            company="Equinor ASA",
            ticker="EQNR",
            metric_ids=(
                "net_operating_income",
            ),
        )
    )

    assert (
        result.analyst_report
        is fake_analyst_report
    )

    assert (
        result.guidance_report
        is fake_guidance_report
    )

    assert len(dataset_calls) == 1

    assert (
        dataset_calls[0][1]
        == ("net_operating_income",)
    )

    assert parse_calls == [
        (
            "q1-document",
            "q1-document.pdf",
        ),
        (
            "q2-document",
            "q2-document.pdf",
        ),
    ]

    assert len(evidence_calls) == 1

    evidence_call = (
        evidence_calls[0]
    )

    assert (
        evidence_call["document_id"]
        == "q2-document"
    )

    assert (
        evidence_call["dataset"]
        is fake_dataset
    )

    assert (
        evidence_call["from_period"]
        == "Q1 2026"
    )

    assert (
        evidence_call["to_period"]
        == "Q2 2026"
    )

    assert len(analyst_calls) == 1

    analyst_call = analyst_calls[0]

    assert (
        analyst_call["dataset"]
        is fake_dataset
    )

    assert (
        analyst_call[
            "evidence_assessments"
        ]
        is fake_evidence
    )

    assert (
        analyst_call["company"]
        == "Equinor ASA"
    )

    assert (
        analyst_call["ticker"]
        == "EQNR"
    )

    assert len(guidance_calls) == 1

    guidance_call = (
        guidance_calls[0]
    )

    assert (
        guidance_call[
            "previous_document_id"
        ]
        == "q1-document"
    )

    assert (
        guidance_call[
            "current_document_id"
        ]
        == "q2-document"
    )


def test_current_document_drives_narrative_evidence(
    monkeypatch,
):
    previous_source, current_source = (
        _sources()
    )

    monkeypatch.setattr(
        research_pipeline,
        "build_multi_period_financial_dataset",
        lambda **kwargs: object(),
    )

    parsed_documents = []

    def fake_parse_pdf(
        document_id,
        pdf_path,
    ):
        page = SimpleNamespace(
            document_id=document_id
        )

        parsed_documents.append(
            document_id
        )

        return [page]

    monkeypatch.setattr(
        research_pipeline,
        "parse_pdf",
        fake_parse_pdf,
    )

    evidence_pages = []

    def fake_evidence(
        **kwargs,
    ):
        evidence_pages.extend(
            kwargs["pages"]
        )
        return {}

    monkeypatch.setattr(
        research_pipeline,
        "build_evidence_assessments",
        fake_evidence,
    )

    monkeypatch.setattr(
        research_pipeline,
        "build_analyst_report",
        lambda **kwargs: object(),
    )

    monkeypatch.setattr(
        research_pipeline,
        "build_equinor_guidance_report",
        lambda **kwargs: object(),
    )

    (
        research_pipeline
        .build_equinor_research_result(
            previous_source=(
                previous_source
            ),
            current_source=(
                current_source
            ),
            company="Equinor",
            ticker="EQNR",
            metric_ids=(
                "net_operating_income",
            ),
        )
    )

    assert parsed_documents == [
        "q1-document",
        "q2-document",
    ]

    assert all(
        page.document_id
        == "q2-document"
        for page in evidence_pages
    )


def test_reporting_periods_flow_from_documents(
    monkeypatch,
):
    previous_source, current_source = (
        _sources()
    )

    monkeypatch.setattr(
        research_pipeline,
        "build_multi_period_financial_dataset",
        lambda **kwargs: object(),
    )

    monkeypatch.setattr(
        research_pipeline,
        "parse_pdf",
        lambda **kwargs: [],
    )

    captured = {}

    def fake_evidence(
        **kwargs,
    ):
        captured.update(
            kwargs
        )
        return {}

    monkeypatch.setattr(
        research_pipeline,
        "build_evidence_assessments",
        fake_evidence,
    )

    monkeypatch.setattr(
        research_pipeline,
        "build_analyst_report",
        lambda **kwargs: object(),
    )

    monkeypatch.setattr(
        research_pipeline,
        "build_equinor_guidance_report",
        lambda **kwargs: object(),
    )

    (
        research_pipeline
        .build_equinor_research_result(
            previous_source=(
                previous_source
            ),
            current_source=(
                current_source
            ),
            company="Equinor",
            ticker="EQNR",
            metric_ids=(
                "net_operating_income",
            ),
        )
    )

    assert (
        captured["from_period"]
        == "Q1 2026"
    )

    assert (
        captured["to_period"]
        == "Q2 2026"
    )


def test_same_document_is_rejected():
    document = _document(
        "same-document",
        "Q1 2026",
    )

    previous_source = PeriodSource(
        document=document,
        page_number=4,
    )

    current_source = PeriodSource(
        document=document,
        page_number=4,
    )

    with pytest.raises(
        ValueError,
        match=(
            "requires two different documents"
        ),
    ):
        (
            research_pipeline
            .build_equinor_research_result(
                previous_source=(
                    previous_source
                ),
                current_source=(
                    current_source
                ),
                company="Equinor",
                ticker="EQNR",
                metric_ids=(
                    "net_operating_income",
                ),
            )
        )