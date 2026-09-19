from collections.abc import Iterable
from dataclasses import dataclass

from equitylens.guidance import (
    GuidanceChange,
    GuidanceItem,
    compare_guidance,
)

GuidanceKey = tuple[str, str]


@dataclass(frozen=True)
class GuidanceReport:
    previous_document_id: str
    current_document_id: str
    changes: tuple[GuidanceChange, ...]
    introduced: tuple[GuidanceItem, ...]
    withdrawn: tuple[GuidanceItem, ...]

    @property
    def unchanged(
        self,
    ) -> tuple[GuidanceChange, ...]:
        return tuple(
            change
            for change in self.changes
            if change.change_type
            == "unchanged"
        )

    @property
    def changed(
        self,
    ) -> tuple[GuidanceChange, ...]:
        return tuple(
            change
            for change in self.changes
            if change.change_type
            != "unchanged"
        )


def _guidance_key(
    item: GuidanceItem,
) -> GuidanceKey:
    return (
        item.metric_id,
        item.target_period,
    )


def _index_guidance(
    items: Iterable[GuidanceItem],
    expected_document_id: str,
) -> dict[
    GuidanceKey,
    GuidanceItem,
]:
    indexed: dict[
        GuidanceKey,
        GuidanceItem,
    ] = {}

    for item in items:
        if (
            item.document_id
            != expected_document_id
        ):
            raise ValueError(
                "Guidance item document_id does not "
                "match the expected document."
            )

        key = _guidance_key(
            item
        )

        if key in indexed:
            raise ValueError(
                "Duplicate guidance item detected "
                f"for {key[0]} / {key[1]}."
            )

        indexed[key] = item

    return indexed


def build_guidance_report(
    previous_document_id: str,
    current_document_id: str,
    previous_items: Iterable[
        GuidanceItem
    ],
    current_items: Iterable[
        GuidanceItem
    ],
) -> GuidanceReport:
    if not previous_document_id.strip():
        raise ValueError(
            "previous_document_id cannot be empty."
        )

    if not current_document_id.strip():
        raise ValueError(
            "current_document_id cannot be empty."
        )

    if (
        previous_document_id
        == current_document_id
    ):
        raise ValueError(
            "Guidance report requires two "
            "different documents."
        )

    previous = _index_guidance(
        previous_items,
        previous_document_id,
    )

    current = _index_guidance(
        current_items,
        current_document_id,
    )

    previous_keys = set(
        previous
    )

    current_keys = set(
        current
    )

    shared_keys = sorted(
        previous_keys
        & current_keys
    )

    introduced_keys = sorted(
        current_keys
        - previous_keys
    )

    withdrawn_keys = sorted(
        previous_keys
        - current_keys
    )

    changes = tuple(
        compare_guidance(
            previous[key],
            current[key],
        )
        for key in shared_keys
    )

    introduced = tuple(
        current[key]
        for key in introduced_keys
    )

    withdrawn = tuple(
        previous[key]
        for key in withdrawn_keys
    )

    return GuidanceReport(
        previous_document_id=(
            previous_document_id
        ),
        current_document_id=(
            current_document_id
        ),
        changes=changes,
        introduced=introduced,
        withdrawn=withdrawn,
    )