from dataclasses import dataclass

from equitylens.fact_sets import (
    FinancialFactSet,
    extract_registered_fact_set,
)
from equitylens.financial_dataset import MultiPeriodFinancialDataset
from equitylens.metrics import get_metric_definition
from equitylens.models import Document, ParsedTable
from equitylens.table_parser import parse_tables


@dataclass(frozen=True)
class PeriodSource:
    document: Document
    page_number: int


def _find_registered_metric_table(
    tables: list[ParsedTable],
    metric_ids: tuple[str, ...],
    period: str,
) -> ParsedTable:
    metric_definitions = tuple(
        get_metric_definition(metric_id)
        for metric_id in metric_ids
    )

    matching_tables = []

    for table in tables:
        has_period = any(
            column == period or column.endswith(f".{period}")
            for column in table.columns
        )

        if not has_period:
            continue

        row_labels = {
            row[0].strip()
            for row in table.rows
            if row
        }

        contains_all_metrics = all(
            any(
                source_label in row_labels
                for source_label in metric_definition.source_labels
            )
            for metric_definition in metric_definitions
        )

        if contains_all_metrics:
            matching_tables.append(table)

    if len(matching_tables) != 1:
        raise ValueError(
            f"Expected exactly one table containing all registered metrics "
            f"for period '{period}', found {len(matching_tables)}."
        )

    return matching_tables[0]


def _extract_period_fact_set(
    source: PeriodSource,
    metric_ids: tuple[str, ...],
) -> FinancialFactSet:
    tables = parse_tables(
        document_id=source.document.document_id,
        pdf_path=source.document.local_path,
        page_number=source.page_number,
    )

    table = _find_registered_metric_table(
        tables=tables,
        metric_ids=metric_ids,
        period=source.document.reporting_period,
    )

    return extract_registered_fact_set(
        table=table,
        metric_ids=metric_ids,
        period=source.document.reporting_period,
    )


def build_multi_period_financial_dataset(
    sources: tuple[PeriodSource, ...],
    metric_ids: tuple[str, ...],
) -> MultiPeriodFinancialDataset:
    """
    Build a deterministic multi-period financial dataset from real documents.
    """

    if not sources:
        raise ValueError("sources cannot be empty.")

    if not metric_ids:
        raise ValueError("metric_ids cannot be empty.")

    periods = tuple(
        source.document.reporting_period
        for source in sources
    )

    if len(periods) != len(set(periods)):
        raise ValueError(
            "Each source must represent a unique reporting period."
        )

    fact_sets = tuple(
        _extract_period_fact_set(
            source=source,
            metric_ids=metric_ids,
        )
        for source in sources
    )

    return MultiPeriodFinancialDataset(
        fact_sets=fact_sets,
    )