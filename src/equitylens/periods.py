from dataclasses import dataclass
from typing import Literal

PeriodType = Literal[
    "quarter",
    "half_year",
    "full_year",
]

ComparisonType = Literal[
    "qoq",
    "yoy",
    "other",
]


@dataclass(frozen=True, order=True)
class ReportingPeriod:
    year: int
    period_type: PeriodType
    period_number: int | None = None

    @property
    def label(self) -> str:
        if self.period_type == "quarter":
            return f"Q{self.period_number} {self.year}"

        if self.period_type == "half_year":
            return f"H{self.period_number} {self.year}"

        return f"FY {self.year}"


def parse_reporting_period(label: str) -> ReportingPeriod:
    parts = label.strip().upper().split()

    if len(parts) != 2:
        raise ValueError(
            f"Unsupported reporting period: {label!r}."
        )

    period_token, year_token = parts

    try:
        year = int(year_token)
    except ValueError as exc:
        raise ValueError(
            f"Invalid reporting period year: {year_token!r}."
        ) from exc

    if period_token.startswith("Q"):
        try:
            quarter = int(period_token[1:])
        except ValueError as exc:
            raise ValueError(
                f"Invalid quarter: {period_token!r}."
            ) from exc

        if quarter not in {1, 2, 3, 4}:
            raise ValueError(
                f"Quarter must be between 1 and 4, got {quarter}."
            )

        return ReportingPeriod(
            year=year,
            period_type="quarter",
            period_number=quarter,
        )

    if period_token.startswith("H"):
        try:
            half_year = int(period_token[1:])
        except ValueError as exc:
            raise ValueError(
                f"Invalid half-year period: {period_token!r}."
            ) from exc

        if half_year not in {1, 2}:
            raise ValueError(
                f"Half-year period must be 1 or 2, got {half_year}."
            )

        return ReportingPeriod(
            year=year,
            period_type="half_year",
            period_number=half_year,
        )

    if period_token == "FY":
        return ReportingPeriod(
            year=year,
            period_type="full_year",
        )

    raise ValueError(
        f"Unsupported reporting period: {label!r}."
    )


def classify_period_comparison(
    from_period: ReportingPeriod,
    to_period: ReportingPeriod,
) -> ComparisonType:
    if (
        from_period.period_type == "quarter"
        and to_period.period_type == "quarter"
    ):
        if (
            from_period.year == to_period.year
            and from_period.period_number is not None
            and to_period.period_number == from_period.period_number + 1
        ):
            return "qoq"

        if (
            from_period.period_number == 4
            and to_period.period_number == 1
            and to_period.year == from_period.year + 1
        ):
            return "qoq"

        if (
            to_period.year == from_period.year + 1
            and to_period.period_number == from_period.period_number
        ):
            return "yoy"

    return "other"


def classify_period_labels(
    from_period: str,
    to_period: str,
) -> ComparisonType:
    """
    Classify two period labels without making financial calculations
    depend on every possible source-specific period format.
    """

    try:
        parsed_from_period = parse_reporting_period(from_period)
        parsed_to_period = parse_reporting_period(to_period)
    except ValueError:
        return "other"

    return classify_period_comparison(
        from_period=parsed_from_period,
        to_period=parsed_to_period,
    )