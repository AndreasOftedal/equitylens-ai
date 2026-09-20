from equitylens.documents import (
    AKER_BP_Q2_2026,
    EQUINOR_Q2_2026,
)
from equitylens.evidence_scope import (
    assess_scope_compatibility,
    resolve_evidence_scope,
)


def test_aker_bp_alvheim_area_is_asset_scope():
    scope = resolve_evidence_scope(
        document_id=(
            AKER_BP_Q2_2026.document_id
        ),
        section_context=(
            "7 · Aker BP Quarterly Report · "
            "Q2 2026 OPERATIONAL REVIEW "
            "Alvheim area KEY FIGURES"
        ),
    )

    assert scope == "asset"


def test_aker_bp_eiga_area_is_asset_scope():
    scope = resolve_evidence_scope(
        document_id=(
            AKER_BP_Q2_2026.document_id
        ),
        section_context=(
            "8 · Aker BP Quarterly Report · "
            "Q2 2026 Eiga area KEY FIGURES"
        ),
    )

    assert scope == "asset"


def test_aker_bp_johan_sverdrup_is_asset_scope():
    scope = resolve_evidence_scope(
        document_id=(
            AKER_BP_Q2_2026.document_id
        ),
        section_context=(
            "9 · Aker BP Quarterly Report · "
            "Q2 2026 Johan Sverdrup KEY FIGURES"
        ),
    )

    assert scope == "asset"


def test_aker_bp_skarv_area_is_asset_scope():
    scope = resolve_evidence_scope(
        document_id=(
            AKER_BP_Q2_2026.document_id
        ),
        section_context=(
            "10 · Aker BP Quarterly Report · "
            "Q2 2026 Skarv area KEY FIGURES"
        ),
    )

    assert scope == "asset"


def test_aker_bp_ula_area_is_asset_scope():
    scope = resolve_evidence_scope(
        document_id=(
            AKER_BP_Q2_2026.document_id
        ),
        section_context=(
            "10 · Aker BP Quarterly Report · "
            "Q2 2026 Ula area KEY FIGURES"
        ),
    )

    assert scope == "asset"


def test_aker_bp_valhall_area_is_asset_scope():
    scope = resolve_evidence_scope(
        document_id=(
            AKER_BP_Q2_2026.document_id
        ),
        section_context=(
            "11 · Aker BP Quarterly Report · "
            "Q2 2026 Valhall area KEY FIGURES"
        ),
    )

    assert scope == "asset"


def test_aker_bp_group_results_are_group_scope():
    scope = resolve_evidence_scope(
        document_id=(
            AKER_BP_Q2_2026.document_id
        ),
        section_context=(
            "2 · Aker BP Quarterly Report · "
            "Q2 2026 SECOND QUARTER 2026 RESULTS"
        ),
    )

    assert scope == "group"


def test_aker_bp_cash_flow_is_group_scope():
    scope = resolve_evidence_scope(
        document_id=(
            AKER_BP_Q2_2026.document_id
        ),
        section_context=(
            "6 · Aker BP Quarterly Report · "
            "Q2 2026 Cash flow (USD MILLION)"
        ),
    )

    assert scope == "group"


def test_equinor_results_are_group_scope():
    scope = resolve_evidence_scope(
        document_id=(
            EQUINOR_Q2_2026.document_id
        ),
        section_context=(
            "Equinor second quarter 2026 results "
            "Equinor delivered an adjusted operating income "
            "of USD 11.48 billion."
        ),
    )

    assert scope == "group"


def test_equinor_group_review_is_group_scope():
    scope = resolve_evidence_scope(
        document_id=(
            EQUINOR_Q2_2026.document_id
        ),
        section_context=(
            "Group review Operations and financial results "
            "Equinor delivered strong production."
        ),
    )

    assert scope == "group"


def test_equinor_ep_norway_is_segment_scope():
    scope = resolve_evidence_scope(
        document_id=(
            EQUINOR_Q2_2026.document_id
        ),
        section_context=(
            "Exploration & Production Norway "
            "Production and revenues"
        ),
    )

    assert scope == "segment"


def test_equinor_ep_international_is_segment_scope():
    scope = resolve_evidence_scope(
        document_id=(
            EQUINOR_Q2_2026.document_id
        ),
        section_context=(
            "Exploration & Production International "
            "Production and revenues"
        ),
    )

    assert scope == "segment"


def test_equinor_ep_usa_is_segment_scope():
    scope = resolve_evidence_scope(
        document_id=(
            EQUINOR_Q2_2026.document_id
        ),
        section_context=(
            "Exploration & Production USA "
            "Production and revenues"
        ),
    )

    assert scope == "segment"


def test_equinor_mmp_is_segment_scope():
    scope = resolve_evidence_scope(
        document_id=(
            EQUINOR_Q2_2026.document_id
        ),
        section_context=(
            "Marketing, Midstream & Processing "
            "Volumes, pricing and revenues"
        ),
    )

    assert scope == "segment"


def test_equinor_power_is_segment_scope():
    scope = resolve_evidence_scope(
        document_id=(
            EQUINOR_Q2_2026.document_id
        ),
        section_context=(
            "Power Power generation "
            "The increase in renewable power generation"
        ),
    )

    assert scope == "segment"


def test_equinor_continuation_text_is_not_inferred_as_segment():
    scope = resolve_evidence_scope(
        document_id=(
            EQUINOR_Q2_2026.document_id
        ),
        section_context=(
            "than offset lower gas-to-power generation, "
            "resulting in higher total power generation. "
            "Marketing, Midstream and Processing delivered "
            "strong results."
        ),
    )

    assert scope == "unknown"


def test_unknown_document_context_is_unknown_scope():
    scope = resolve_evidence_scope(
        document_id="unknown-report",
        section_context="Operational review",
    )

    assert scope == "unknown"


def test_group_metric_accepts_group_evidence():
    result = assess_scope_compatibility(
        metric_scope="group",
        evidence_scope="group",
    )

    assert result == "compatible"


def test_group_metric_rejects_asset_evidence():
    result = assess_scope_compatibility(
        metric_scope="group",
        evidence_scope="asset",
    )

    assert result == "mismatched"


def test_group_metric_rejects_segment_evidence():
    result = assess_scope_compatibility(
        metric_scope="group",
        evidence_scope="segment",
    )

    assert result == "mismatched"


def test_unknown_evidence_scope_remains_unknown():
    result = assess_scope_compatibility(
        metric_scope="group",
        evidence_scope="unknown",
    )

    assert result == "unknown"


def test_non_group_same_type_is_not_assumed_compatible():
    result = assess_scope_compatibility(
        metric_scope="asset",
        evidence_scope="asset",
    )

    assert result == "unknown"