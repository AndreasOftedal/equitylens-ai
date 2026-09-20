from pathlib import Path

from equitylens.source_manifest import (
    AKER_BP_SOURCES,
    ALL_SOURCES,
    EQUINOR_SOURCES,
)


def test_equinor_source_manifest_is_complete():
    assert len(EQUINOR_SOURCES) == 2

    document_ids = {
        source.document_id
        for source in EQUINOR_SOURCES
    }

    assert document_ids == {
        "equinor-q1-2026-financial-statements-and-review",
        "equinor-q2-2026-financial-statements-and-review",
    }


def test_aker_bp_source_manifest_is_complete():
    assert len(AKER_BP_SOURCES) == 2

    document_ids = {
        source.document_id
        for source in AKER_BP_SOURCES
    }

    assert document_ids == {
        "aker-bp-q1-2026-report",
        "aker-bp-q2-2026-report",
    }


def test_all_sources_contains_both_companies():
    assert len(ALL_SOURCES) == 4

    assert ALL_SOURCES == (
        *EQUINOR_SOURCES,
        *AKER_BP_SOURCES,
    )


def test_all_source_document_ids_are_unique():
    document_ids = tuple(
        source.document_id
        for source in ALL_SOURCES
    )

    assert len(document_ids) == len(
        set(document_ids)
    )


def test_all_sources_have_valid_sha256_fingerprints():
    for source in ALL_SOURCES:
        assert len(source.sha256) == 64

        assert all(
            character in "0123456789abcdef"
            for character in source.sha256
        )


def test_all_sources_have_expected_local_paths():
    local_paths = {
        source.local_path
        for source in ALL_SOURCES
    }

    assert local_paths == {
        Path(
            "data/raw/equinor/"
            "equinor_q1_2026_financial_statements_and_review.pdf"
        ),
        Path(
            "data/raw/equinor/"
            "equinor_q2_2026_financial_statements_and_review.pdf"
        ),
        Path(
            "data/raw/aker_bp/"
            "aker_bp_q1_2026_report.pdf"
        ),
        Path(
            "data/raw/aker_bp/"
            "aker_bp_q2_2026_report.pdf"
        ),
    }