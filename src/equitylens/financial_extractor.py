from decimal import Decimal, InvalidOperation

from equitylens.models import EvidenceRef, FinancialFact, ParsedTable


def _find_period_column(
    columns: tuple[str, ...],
    period: str,
) -> tuple[int, str]:
    matches = [
        (index, column)
        for index, column in enumerate(columns)
        if column == period or column.endswith(f".{period}")
    ]

    if len(matches) != 1:
        raise ValueError(
            f"Expected exactly one column for period '{period}', "
            f"found {len(matches)}."
        )

    return matches[0]


def _parse_decimal(raw_value: str) -> Decimal:
    cleaned_value = raw_value.strip().replace(",", "")

    if not cleaned_value:
        raise ValueError("Cannot convert an empty value to Decimal.")

    if cleaned_value.startswith("(") and cleaned_value.endswith(")"):
        cleaned_value = f"-{cleaned_value[1:-1]}"

    try:
        return Decimal(cleaned_value)
    except InvalidOperation as exc:
        raise ValueError(
            f"Could not convert '{raw_value}' to Decimal."
        ) from exc


def extract_financial_fact(
    table: ParsedTable,
    metric: str,
    period: str,
    unit: str,
) -> FinancialFact:
    """
    Extract a financial KPI deterministically from a parsed table.

    Extraction is based on an exact metric row and a uniquely identified
    reporting-period column. Unrelated columns in the parsed table are ignored.
    """

    column_index, source_column_label = _find_period_column(
        table.columns,
        period,
    )

    matching_rows = [
        row
        for row in table.rows
        if row and row[0].strip() == metric
    ]

    if len(matching_rows) != 1:
        raise ValueError(
            f"Expected exactly one row for metric '{metric}', "
            f"found {len(matching_rows)}."
        )

    row = matching_rows[0]

    if column_index >= len(row):
        raise ValueError(
            f"Metric '{metric}' does not contain "
            f"column '{source_column_label}'."
        )

    raw_value = row[column_index]
    value = _parse_decimal(raw_value)

    fact_id = (
        f"{table.document_id}-"
        f"{metric.lower().replace('/', '-').replace(' ', '-')}-"
        f"{period.lower().replace(' ', '-')}"
    )

    return FinancialFact(
        fact_id=fact_id,
        metric=metric,
        period=period,
        value=value,
        unit=unit,
        evidence=EvidenceRef(
            document_id=table.document_id,
            page_number=table.page_number,
            table_number=table.table_number,
            row_label=metric,
            column_label=source_column_label,
        ),
    )


def extract_exchange_rate_fact(
    table: ParsedTable,
    currency_pair: str,
    measure: str,
    period: str,
) -> FinancialFact:
    """
    Extract one exchange-rate fact deterministically from a parsed table.
    """

    column_index, source_column_label = _find_period_column(
        table.columns,
        period,
    )

    active_currency_pair: str | None = None

    for row in table.rows:
        if not row:
            continue

        row_label = row[0].strip()

        if row_label in {"USD/NOK", "EUR/USD"}:
            active_currency_pair = row_label
            continue

        if active_currency_pair != currency_pair:
            continue

        if row_label != measure:
            continue

        if column_index >= len(row):
            raise ValueError(
                f"Row '{measure}' does not contain "
                f"column '{source_column_label}'."
            )

        value = _parse_decimal(row[column_index])

        fact_id = (
            f"{table.document_id}-"
            f"{currency_pair.lower().replace('/', '-')}-"
            f"{measure.lower().replace(' ', '-')}-"
            f"{period.lower().replace(' ', '-')}"
        )

        unit = (
            "NOK per USD"
            if currency_pair == "USD/NOK"
            else "USD per EUR"
        )

        return FinancialFact(
            fact_id=fact_id,
            metric=f"{currency_pair} {measure}",
            period=period,
            value=value,
            unit=unit,
            evidence=EvidenceRef(
                document_id=table.document_id,
                page_number=table.page_number,
                table_number=table.table_number,
                row_label=f"{currency_pair} / {measure}",
                column_label=source_column_label,
            ),
        )

    raise ValueError(
        f"Could not find {currency_pair} / {measure} / {period}."
    )