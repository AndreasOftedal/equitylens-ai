from decimal import Decimal

import streamlit as st

from equitylens.analysis_pipeline import PeriodSource
from equitylens.documents import (
    AKER_BP_Q1_2026,
    AKER_BP_Q2_2026,
    EQUINOR_Q1_2026,
    EQUINOR_Q2_2026,
)
from equitylens.research_pipeline import (
    build_aker_bp_research_result,
    build_equinor_research_result,
)

COMPANY_CONFIGS = {
    "Aker BP ASA · AKRBP": {
        "company": "Aker BP ASA",
        "ticker": "AKRBP",
        "previous_document": AKER_BP_Q1_2026,
        "current_document": AKER_BP_Q2_2026,
        "financial_page": 3,
        "metric_ids": (
            "net_income",
            "basic_earnings_per_share",
            "operating_cash_flow",
            "total_equity_production",
        ),
        "metric_labels": {
            "net_income": "Net income",
            "basic_earnings_per_share": "Basic EPS",
            "operating_cash_flow": "Operating cash flow",
            "total_equity_production": "Equity production",
        },
        "metric_kinds": {
            "net_income": "usd_million",
            "basic_earnings_per_share": "usd_per_share",
            "operating_cash_flow": "usd_million",
            "total_equity_production": "production",
        },
        "builder": build_aker_bp_research_result,
    },
    "Equinor ASA · EQNR": {
        "company": "Equinor ASA",
        "ticker": "EQNR",
        "previous_document": EQUINOR_Q1_2026,
        "current_document": EQUINOR_Q2_2026,
        "financial_page": 4,
        "metric_ids": (
            "net_operating_income",
            "net_income",
            "adjusted_operating_income",
            "adjusted_net_income",
        ),
        "metric_labels": {
            "net_operating_income": "Net operating income",
            "net_income": "Net income",
            "adjusted_operating_income": "Adjusted operating income",
            "adjusted_net_income": "Adjusted net income",
        },
        "metric_kinds": {
            "net_operating_income": "usd_million",
            "net_income": "usd_million",
            "adjusted_operating_income": "usd_million",
            "adjusted_net_income": "usd_million",
        },
        "builder": build_equinor_research_result,
    },
}


GUIDANCE_LABELS = {
    "production_guidance": "Production",
    "production_cost_guidance": "Production cost",
    "capex_guidance": "Capex",
    "exploration_spend_guidance": "Exploration spend",
    "abandonment_spend_guidance": "Abandonment spend",
    "dividend_guidance": "Dividend",
    "oil_and_gas_production_growth": "Oil & gas production growth",
    "renewable_power_generation_growth": "Renewable power generation growth",
    "organic_capex": "Organic capex",
    "share_buyback": "Share buyback",
}


st.set_page_config(
    page_title="EquityLens AI",
    page_icon="◈",
    layout="wide",
    initial_sidebar_state="expanded",
)


st.markdown(
    """
    <style>
    :root {
        --bg: #071018;
        --panel: #0d1822;
        --panel-soft: #101e29;
        --border: #1f3544;
        --text: #edf4f8;
        --muted: #8fa6b5;
        --accent: #50d6b0;
        --blue: #67aef5;
    }

    .stApp {
        background:
            radial-gradient(
                circle at 15% 0%,
                rgba(80, 214, 176, 0.07),
                transparent 28%
            ),
            var(--bg);
        color: var(--text);
    }

    [data-testid="stSidebar"] {
        background: #08131c;
        border-right: 1px solid var(--border);
    }

    [data-testid="stSidebar"] [data-testid="stWidgetLabel"] p {
        color: #9fb4c1 !important;
    }

    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p {
        color: #9fb4c1;
    }

    [data-testid="stSidebar"] h3 {
        color: var(--text);
    }

    [data-testid="stHeader"] {
        background: rgba(7, 16, 24, 0.75);
    }

    .block-container {
        padding-top: 2rem;
        padding-bottom: 4rem;
        max-width: 1450px;
    }

    .eyebrow {
        color: var(--accent);
        font-size: 0.74rem;
        font-weight: 700;
        letter-spacing: 0.16em;
        text-transform: uppercase;
        margin-bottom: 0.5rem;
    }

    .hero-title {
        font-size: 2.7rem;
        font-weight: 720;
        letter-spacing: -0.04em;
        line-height: 1.05;
        margin: 0;
        color: var(--text);
    }

    .hero-subtitle {
        color: #89b8d6;
        font-size: 1rem;
        margin-top: 0.7rem;
        margin-bottom: 1.8rem;
    }

    .status-row {
        display: flex;
        flex-wrap: wrap;
        gap: 0.55rem;
        margin: 0.8rem 0 1.7rem 0;
    }

    .pill {
        border: 1px solid var(--border);
        background: var(--panel);
        color: #bfd0da;
        padding: 0.32rem 0.62rem;
        border-radius: 999px;
        font-size: 0.76rem;
    }

    .pill-good {
        border-color: rgba(80, 214, 176, 0.38);
        color: #75e2c2;
    }

    .section-label {
        color: #7eb8dc;
        font-size: 0.72rem;
        font-weight: 700;
        letter-spacing: 0.13em;
        text-transform: uppercase;
        margin-bottom: 0.28rem;
    }

    .section-title {
        color: var(--text);
        font-size: 1.48rem;
        font-weight: 680;
        margin-bottom: 0.8rem;
    }

    .summary-card {
        background: linear-gradient(
            135deg,
            rgba(16, 30, 41, 0.95),
            rgba(10, 23, 32, 0.95)
        );
        border: 1px solid var(--border);
        border-radius: 14px;
        padding: 1.2rem 1.3rem;
        min-height: 160px;
    }

    .summary-card p {
        color: #cbd9e1;
        line-height: 1.55;
        margin: 0.4rem 0;
    }

    [data-testid="stMetric"] {
        background: var(--panel);
        border: 1px solid var(--border);
        border-radius: 12px;
        padding: 1rem 1rem 0.8rem 1rem;
    }

    [data-testid="stMetricLabel"] {
        color: #86b5d1;
    }

    [data-testid="stMetricValue"] {
        color: var(--text);
    }

    div[data-testid="stExpander"] {
        border: 1px solid var(--border);
        border-radius: 10px;
        background: rgba(13, 24, 34, 0.45);
    }

    .source-box {
        border-left: 2px solid var(--blue);
        padding: 0.25rem 0 0.25rem 0.8rem;
        margin-bottom: 0.9rem;
    }

    .source-title {
        color: #dce8ee;
        font-weight: 600;
    }

    .source-meta {
        color: var(--muted);
        font-size: 0.8rem;
        margin-top: 0.2rem;
    }

    .evidence-state {
        color: #8fa6b5;
        font-size: 0.82rem;
        margin-bottom: 0.35rem;
    }

    hr {
        border-color: var(--border) !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


def _format_decimal(
    value: Decimal,
    *,
    decimals: int | None = None,
) -> str:
    numeric = float(value)

    if decimals is not None:
        return f"{numeric:,.{decimals}f}"

    if numeric == int(numeric):
        return f"{numeric:,.0f}"

    return f"{numeric:,.2f}".rstrip("0").rstrip(".")


def _format_percentage(
    value: Decimal,
) -> str:
    return f"{float(value):+.1f}%"


def _format_metric_value(
    metric_id: str,
    value: Decimal,
    metric_kinds: dict[str, str],
) -> str:
    kind = metric_kinds[
        metric_id
    ]

    if kind == "usd_million":
        return (
            f"${_format_decimal(value, decimals=0)}m"
        )

    if kind == "usd_per_share":
        return (
            f"${_format_decimal(value, decimals=2)}"
        )

    if kind == "production":
        return _format_decimal(
            value,
            decimals=1,
        )

    return _format_decimal(
        value
    )


def _format_absolute_change(
    metric_id: str,
    value: Decimal,
    metric_kinds: dict[str, str],
) -> str:
    kind = metric_kinds[
        metric_id
    ]

    if kind == "usd_million":
        sign = "+" if value > 0 else ""

        return (
            f"{sign}${_format_decimal(value, decimals=0)}m"
        )

    if kind == "usd_per_share":
        sign = "+" if value > 0 else ""

        return (
            f"{sign}${_format_decimal(value, decimals=2)}"
        )

    sign = "+" if value > 0 else ""

    return (
        f"{sign}{_format_decimal(value)}"
    )


def _guidance_label(
    metric_id: str,
) -> str:
    if metric_id in GUIDANCE_LABELS:
        return GUIDANCE_LABELS[
            metric_id
        ]

    return (
        metric_id
        .replace("_guidance", "")
        .replace("_", " ")
        .title()
    )


def _format_guidance_number(
    value: Decimal,
) -> str:
    return _format_decimal(
        value
    )


def _format_guidance_item(
    item,
) -> str:
    lower = getattr(
        item,
        "numeric_lower_bound",
        None,
    )

    upper = getattr(
        item,
        "numeric_upper_bound",
        None,
    )

    if (
        lower is not None
        and upper is not None
    ):
        value = (
            f"{_format_guidance_number(lower)}–"
            f"{_format_guidance_number(upper)}"
        )

    elif item.numeric_value is not None:
        value = (
            _format_guidance_number(
                item.numeric_value
            )
        )

        if item.qualifier == "approximately":
            value = f"~{value}"

    elif item.qualitative_value is not None:
        return item.qualitative_value

    else:
        return "—"

    if item.unit:
        return (
            f"{value} {item.unit}"
        )

    return value


def _direction_text(
    value: Decimal,
) -> str:
    if value > 0:
        return "increased"

    if value < 0:
        return "decreased"

    return "was unchanged"


def _build_financial_summary(
    metric_ids: tuple[str, ...],
    metric_results: dict,
    metric_labels: dict[str, str],
    metric_kinds: dict[str, str],
) -> str:
    paragraphs = []

    for metric_id in metric_ids:
        change = (
            metric_results[
                metric_id
            ].change
        )

        label = (
            metric_labels[
                metric_id
            ]
        )

        direction = (
            _direction_text(
                change.absolute_change
            )
        )

        paragraphs.append(
            "<p>"
            f"<strong>{label}:</strong> "
            f"{direction} from "
            f"{_format_metric_value(metric_id, change.from_value, metric_kinds)} "
            f"to "
            f"{_format_metric_value(metric_id, change.to_value, metric_kinds)} "
            f"({_format_percentage(change.percentage_change)})."
            "</p>"
        )

    return "".join(
        paragraphs
    )


def _build_guidance_summary(
    guidance_report,
) -> str:
    changed = (
        guidance_report.changed
    )

    unchanged = (
        guidance_report.unchanged
    )

    if changed:
        changed_names = ", ".join(
            _guidance_label(
                change.metric_id
            )
            for change in changed
        )

        changed_text = (
            f"<p><strong>{len(changed)} guidance "
            f"{'item' if len(changed) == 1 else 'items'} changed.</strong> "
            f"{changed_names}.</p>"
        )
    else:
        changed_text = (
            "<p><strong>No comparable guidance "
            "items changed.</strong></p>"
        )

    unchanged_text = (
        f"<p><strong>{len(unchanged)} "
        f"{'item was' if len(unchanged) == 1 else 'items were'} unchanged.</strong> "
        "Forward-looking guidance is kept separate "
        "from historical financial performance.</p>"
    )

    introduced_text = ""

    if guidance_report.introduced:
        introduced_text = (
            f"<p>{len(guidance_report.introduced)} "
            "guidance item(s) were newly introduced.</p>"
        )

    withdrawn_text = ""

    if guidance_report.withdrawn:
        withdrawn_text = (
            f"<p>{len(guidance_report.withdrawn)} "
            "guidance item(s) were withdrawn.</p>"
        )

    return (
        changed_text
        + unchanged_text
        + introduced_text
        + withdrawn_text
    )


@st.cache_resource(
    show_spinner=False,
)
def _load_research_result(
    company_key: str,
):
    config = (
        COMPANY_CONFIGS[
            company_key
        ]
    )

    builder = (
        config[
            "builder"
        ]
    )

    return builder(
        previous_source=PeriodSource(
            document=config[
                "previous_document"
            ],
            page_number=config[
                "financial_page"
            ],
        ),
        current_source=PeriodSource(
            document=config[
                "current_document"
            ],
            page_number=config[
                "financial_page"
            ],
        ),
        company=config[
            "company"
        ],
        ticker=config[
            "ticker"
        ],
        metric_ids=config[
            "metric_ids"
        ],
    )


with st.sidebar:
    st.markdown(
        "### ◈ EquityLens AI"
    )

    st.caption(
        "Evidence-grounded equity research"
    )

    st.divider()

    selected_company = (
        st.selectbox(
            "Company",
            options=tuple(
                COMPANY_CONFIGS
            ),
            index=0,
        )
    )

    config = (
        COMPANY_CONFIGS[
            selected_company
        ]
    )

    comparison_label = (
        f"{config['previous_document'].reporting_period} "
        f"→ {config['current_document'].reporting_period}"
    )

    st.selectbox(
        "Comparison",
        options=[
            comparison_label,
        ],
        index=0,
    )

    st.divider()

    st.markdown(
        "**Research controls**"
    )

    st.caption(
        "✓ Deterministic financial calculations"
    )

    st.caption(
        "✓ Source-level provenance"
    )

    st.caption(
        "✓ Evidence-gated narrative"
    )

    st.caption(
        "✓ Guarded AI synthesis"
    )

    st.caption(
        "✓ Forward guidance kept separate"
    )


with st.spinner(
    "Building validated research view..."
):
    research_result = (
        _load_research_result(
            selected_company
        )
    )


report = (
    research_result.analyst_report
)

guidance_report = (
    research_result.guidance_report
)

metric_ids = (
    config[
        "metric_ids"
    ]
)

metric_labels = (
    config[
        "metric_labels"
    ]
)

metric_kinds = (
    config[
        "metric_kinds"
    ]
)

metric_results = {
    result.metric_id: result
    for result
    in report.metric_results
}


st.markdown(
    '<div class="eyebrow">'
    "EquityLens AI · Validated research"
    "</div>",
    unsafe_allow_html=True,
)

st.markdown(
    f'<div class="hero-title">'
    f"{report.company}"
    f"</div>",
    unsafe_allow_html=True,
)

st.markdown(
    f'<div class="hero-subtitle">'
    f"{report.ticker} · "
    f"{report.from_period} → "
    f"{report.to_period} · "
    "Research built from company-reported source documents"
    "</div>",
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="status-row">
        <span class="pill pill-good">Validated pipeline</span>
        <span class="pill">Deterministic finance</span>
        <span class="pill">Evidence grounded</span>
        <span class="pill">Auditable provenance</span>
        <span class="pill">Guidance tracked separately</span>
    </div>
    """,
    unsafe_allow_html=True,
)


st.markdown(
    '<div class="section-label">'
    "Executive view"
    "</div>",
    unsafe_allow_html=True,
)

st.markdown(
    '<div class="section-title">'
    "Research snapshot"
    "</div>",
    unsafe_allow_html=True,
)

summary_left, summary_right = (
    st.columns(
        [1.55, 1],
        gap="medium",
    )
)

with summary_left:
    financial_summary = (
        _build_financial_summary(
            metric_ids=metric_ids,
            metric_results=metric_results,
            metric_labels=metric_labels,
            metric_kinds=metric_kinds,
        )
    )

    st.markdown(
        f"""
        <div class="summary-card">
            {financial_summary}
        </div>
        """,
        unsafe_allow_html=True,
    )

with summary_right:
    guidance_summary = (
        _build_guidance_summary(
            guidance_report
        )
    )

    st.markdown(
        f"""
        <div class="summary-card">
            {guidance_summary}
        </div>
        """,
        unsafe_allow_html=True,
    )


st.write("")

st.markdown(
    '<div class="section-label">'
    "Financial performance"
    "</div>",
    unsafe_allow_html=True,
)

st.markdown(
    '<div class="section-title">'
    "Quarter-on-quarter fundamentals"
    "</div>",
    unsafe_allow_html=True,
)

metric_columns = (
    st.columns(
        len(metric_ids),
        gap="small",
    )
)

for column, metric_id in zip(
    metric_columns,
    metric_ids,
    strict=True,
):
    result = (
        metric_results[
            metric_id
        ]
    )

    change = (
        result.change
    )

    with column:
        st.metric(
            label=(
                metric_labels[
                    metric_id
                ]
            ),
            value=(
                _format_metric_value(
                    metric_id,
                    change.to_value,
                    metric_kinds,
                )
            ),
            delta=(
                _format_percentage(
                    change.percentage_change
                )
            ),
            help=(
                f"{report.from_period}: "
                f"{_format_metric_value(metric_id, change.from_value, metric_kinds)}"
            ),
        )


st.write("")

financial_rows = []

for metric_id in metric_ids:
    result = (
        metric_results[
            metric_id
        ]
    )

    change = (
        result.change
    )

    financial_rows.append(
        {
            "Metric": (
                metric_labels[
                    metric_id
                ]
            ),
            report.from_period: (
                _format_metric_value(
                    metric_id,
                    change.from_value,
                    metric_kinds,
                )
            ),
            report.to_period: (
                _format_metric_value(
                    metric_id,
                    change.to_value,
                    metric_kinds,
                )
            ),
            "Absolute change": (
                _format_absolute_change(
                    metric_id,
                    change.absolute_change,
                    metric_kinds,
                )
            ),
            "Change": (
                _format_percentage(
                    change.percentage_change
                )
            ),
            "Comparison": (
                change.comparison_type.upper()
            ),
        }
    )

st.dataframe(
    financial_rows,
    width="stretch",
    hide_index=True,
)


st.write("")

st.markdown(
    '<div class="section-label">'
    "Forward outlook"
    "</div>",
    unsafe_allow_html=True,
)

st.markdown(
    '<div class="section-title">'
    "Guidance tracker"
    "</div>",
    unsafe_allow_html=True,
)

guidance_rows = []

for change in (
    guidance_report.changes
):
    guidance_rows.append(
        {
            "Metric": (
                _guidance_label(
                    change.metric_id
                )
            ),
            "Target": (
                change.target_period
            ),
            "Previous": (
                _format_guidance_item(
                    change.previous
                )
            ),
            "Current": (
                _format_guidance_item(
                    change.current
                )
            ),
            "Status": (
                change.change_type
                .replace("_", " ")
                .title()
            ),
            "Current source": (
                f"p. "
                f"{change.current.page_number}"
            ),
        }
    )

for item in (
    guidance_report.introduced
):
    guidance_rows.append(
        {
            "Metric": (
                _guidance_label(
                    item.metric_id
                )
            ),
            "Target": (
                item.target_period
            ),
            "Previous": "—",
            "Current": (
                _format_guidance_item(
                    item
                )
            ),
            "Status": "Introduced",
            "Current source": (
                f"p. {item.page_number}"
            ),
        }
    )

for item in (
    guidance_report.withdrawn
):
    guidance_rows.append(
        {
            "Metric": (
                _guidance_label(
                    item.metric_id
                )
            ),
            "Target": (
                item.target_period
            ),
            "Previous": (
                _format_guidance_item(
                    item
                )
            ),
            "Current": "—",
            "Status": "Withdrawn",
            "Current source": "—",
        }
    )

if guidance_rows:
    st.dataframe(
        guidance_rows,
        width="stretch",
        hide_index=True,
    )
else:
    st.info(
        "No comparable formal guidance items "
        "were extracted for this period pair."
    )


st.write("")

st.markdown(
    '<div class="section-label">'
    "Evidence controls"
    "</div>",
    unsafe_allow_html=True,
)

st.markdown(
    '<div class="section-title">'
    "Management evidence"
    "</div>",
    unsafe_allow_html=True,
)

evidence_columns = (
    st.columns(
        len(metric_ids),
        gap="small",
    )
)

for column, metric_id in zip(
    evidence_columns,
    metric_ids,
    strict=True,
):
    result = (
        metric_results[
            metric_id
        ]
    )

    assessment = (
        result.evidence_assessment
    )

    if assessment is None:
        availability = (
            "Not evaluated"
        )

        explanation = (
            "No validated narrative "
            "evidence query is registered "
            "for this metric."
        )

    else:
        availability = (
            assessment.availability
            .replace("_", " ")
            .title()
        )

        if (
            assessment.availability
            == "direct_explanation"
        ):
            explanation = (
                "Validated direct management "
                "explanation is available."
            )

        elif (
            assessment.availability
            == "aligned_context_only"
        ):
            explanation = (
                "Related context exists, but it "
                "cannot support a direct claim."
            )

        else:
            explanation = (
                "No validated direct explanation "
                "supports this comparison."
            )

    with column:
        st.markdown(
            f"**{metric_labels[metric_id]}**"
        )

        st.markdown(
            f'<div class="evidence-state">'
            f"{availability}"
            f"</div>",
            unsafe_allow_html=True,
        )

        st.write(
            explanation
        )


st.write("")

st.markdown(
    '<div class="section-label">'
    "Auditability"
    "</div>",
    unsafe_allow_html=True,
)

st.markdown(
    '<div class="section-title">'
    "Source provenance"
    "</div>",
    unsafe_allow_html=True,
)

st.caption(
    "Every financial observation can be traced "
    "back to the exact source document and page."
)

for metric_id in metric_ids:
    result = (
        metric_results[
            metric_id
        ]
    )

    with st.expander(
        metric_labels[
            metric_id
        ]
    ):
        for fact in (
            result.audit_trail.source_facts
        ):
            evidence = (
                fact.evidence
            )

            table_text = (
                f" · table "
                f"{evidence.table_number}"
                if evidence.table_number
                is not None
                else ""
            )

            row_text = (
                f" · {evidence.row_label}"
                if evidence.row_label
                else ""
            )

            column_text = (
                f" · {evidence.column_label}"
                if evidence.column_label
                else ""
            )

            st.markdown(
                f"""
                <div class="source-box">
                    <div class="source-title">
                        {fact.period} ·
                        {_format_decimal(fact.value)}
                        {fact.unit}
                    </div>
                    <div class="source-meta">
                        {evidence.document_id} ·
                        page {evidence.page_number}
                        {table_text}
                        {row_text}
                        {column_text}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )


st.divider()

st.caption(
    "EquityLens separates deterministic financial calculations, "
    "validated narrative evidence and forward-looking guidance. "
    "The language model is not the calculation engine."
)