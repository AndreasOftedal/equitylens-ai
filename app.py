import os
from decimal import Decimal

import streamlit as st
from dotenv import load_dotenv

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
from equitylens.synthesis_input import build_synthesis_input
from equitylens.synthesis_llm import OpenAISynthesisClient
from equitylens.synthesis_pipeline import run_synthesis

load_dotenv()


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
    "maintenance_production_impact": "Maintenance impact",
}


CLAIM_GROUPS = (
    (
        "financial_observation",
        "Financial observations",
        "Deterministic facts translated into analyst language.",
    ),
    (
        "guidance_update",
        "Guidance updates",
        "Forward-looking guidance kept separate from historical performance.",
    ),
    (
        "management_explanation",
        "Management explanations",
        "Only shown when direct narrative evidence passes validation.",
    ),
    (
        "consistency_observation",
        "Narrative consistency",
        "Only shown when the evidence boundary supports a conclusion.",
    ),
)


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

    .system-status-row {
        display: flex;
        flex-wrap: wrap;
        gap: 0.9rem;
        margin: 0.8rem 0 1.7rem 0;
        color: #9fb4c1;
        font-size: 0.76rem;
    }

    .system-tag {
        display: inline-flex;
        align-items: center;
        gap: 0.42rem;
        padding: 0.08rem 0;
        cursor: default;
        user-select: none;
    }

    .status-dot {
        width: 0.42rem;
        height: 0.42rem;
        border-radius: 50%;
        background: #547487;
        box-shadow: 0 0 0 3px rgba(84, 116, 135, 0.1);
    }

    .system-tag-good {
        color: #8ce7cc;
    }

    .system-tag-good .status-dot {
        background: var(--accent);
        box-shadow: 0 0 0 3px rgba(80, 214, 176, 0.1);
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

    .ai-intro {
        background: linear-gradient(
            135deg,
            rgba(80, 214, 176, 0.07),
            rgba(103, 174, 245, 0.04)
        );
        border: 1px solid rgba(80, 214, 176, 0.22);
        border-radius: 14px;
        padding: 1rem 1.15rem;
        margin-bottom: 1rem;
    }

    .ai-intro-title {
        color: #dff8f0;
        font-weight: 650;
        font-size: 1rem;
        margin-bottom: 0.3rem;
    }

    .ai-intro-text {
        color: #9eb4c1;
        font-size: 0.88rem;
        line-height: 1.5;
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
        padding: 0.15rem 0 0.15rem 0.8rem;
    }

    .source-title {
        color: #dce8ee;
        font-weight: 650;
    }

    .source-value {
        color: #f4f9fb;
        font-size: 1.08rem;
        font-weight: 650;
        margin-top: 0.25rem;
    }

    .source-meta {
        color: var(--muted);
        font-size: 0.8rem;
        line-height: 1.5;
        margin-top: 0.3rem;
    }

    .evidence-badge {
        display: inline-flex;
        align-items: center;
        gap: 0.38rem;
        width: fit-content;
        border-radius: 999px;
        padding: 0.2rem 0.5rem;
        margin: 0.15rem 0 0.65rem 0;
        font-size: 0.72rem;
        font-weight: 650;
        letter-spacing: 0.02em;
    }

    .evidence-direct {
        color: #85e7c9;
        background: rgba(80, 214, 176, 0.08);
        border: 1px solid rgba(80, 214, 176, 0.2);
    }

    .evidence-context {
        color: #9ecbf0;
        background: rgba(103, 174, 245, 0.08);
        border: 1px solid rgba(103, 174, 245, 0.2);
    }

    .evidence-muted {
        color: #9fb0ba;
        background: rgba(143, 166, 181, 0.06);
        border: 1px solid rgba(143, 166, 181, 0.16);
    }

    .evidence-control-note {
        background: rgba(103, 174, 245, 0.045);
        border: 1px solid rgba(103, 174, 245, 0.14);
        border-radius: 12px;
        color: #a9bfcc;
        font-size: 0.86rem;
        line-height: 1.55;
        margin-bottom: 0.9rem;
        padding: 0.85rem 1rem;
    }

    .evidence-row-title {
        color: #edf4f8;
        font-weight: 650;
        padding-top: 0.15rem;
    }

    .evidence-row-copy {
        color: #9fb4c1;
        font-size: 0.84rem;
        line-height: 1.5;
        padding-top: 0.08rem;
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
    kind = metric_kinds[metric_id]

    if kind == "usd_million":
        return f"${_format_decimal(value, decimals=0)}m"

    if kind == "usd_per_share":
        return f"${_format_decimal(value, decimals=2)}"

    if kind == "production":
        return (
            f"{_format_decimal(value, decimals=1)} "
            "mboe/day"
        )

    return _format_decimal(value)


def _format_metric_card_value(
    metric_id: str,
    value: Decimal,
    metric_kinds: dict[str, str],
) -> str:
    if metric_kinds[metric_id] == "production":
        return _format_decimal(
            value,
            decimals=1,
        )

    return _format_metric_value(
        metric_id,
        value,
        metric_kinds,
    )


def _metric_card_label(
    metric_id: str,
    metric_labels: dict[str, str],
    metric_kinds: dict[str, str],
) -> str:
    label = metric_labels[metric_id]

    if metric_kinds[metric_id] == "production":
        return f"{label} · mboe/day"

    return label


def _format_absolute_change(
    metric_id: str,
    value: Decimal,
    metric_kinds: dict[str, str],
) -> str:
    kind = metric_kinds[metric_id]
    sign = "+" if value > 0 else ""

    if kind == "usd_million":
        return f"{sign}${_format_decimal(value, decimals=0)}m"

    if kind == "usd_per_share":
        return f"{sign}${_format_decimal(value, decimals=2)}"

    if kind == "production":
        return (
            f"{sign}{_format_decimal(value, decimals=1)} "
            "mboe/day"
        )

    return f"{sign}{_format_decimal(value)}"


def _document_source_url(
    document_id: str,
    company_config: dict,
) -> str | None:
    for key in (
        "previous_document",
        "current_document",
    ):
        document = company_config[key]
        candidate_id = getattr(
            document,
            "document_id",
            None,
        )

        if candidate_id is None:
            candidate_id = getattr(
                document,
                "id",
                None,
            )

        if candidate_id != document_id:
            continue

        source_url = getattr(
            document,
            "source_url",
            None,
        )

        if source_url:
            return str(source_url)

    return None


def _guidance_label(
    metric_id: str,
) -> str:
    if metric_id in GUIDANCE_LABELS:
        return GUIDANCE_LABELS[metric_id]

    return (
        metric_id
        .replace("_guidance", "")
        .replace("_", " ")
        .title()
    )


def _metric_label(
    metric_id: str,
    metric_labels: dict[str, str],
) -> str:
    return metric_labels.get(
        metric_id,
        _guidance_label(metric_id),
    )


def _format_guidance_number(
    value: Decimal,
) -> str:
    text = format(value, "f")

    if "." in text:
        text = text.rstrip("0").rstrip(".")

    integer, separator, fraction = text.partition(".")
    integer_with_separators = f"{int(integer):,}"

    if not separator:
        return integer_with_separators

    return f"{integer_with_separators}.{fraction}"


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

    if lower is not None and upper is not None:
        value = (
            f"{_format_guidance_number(lower)}–"
            f"{_format_guidance_number(upper)}"
        )

    elif item.numeric_value is not None:
        value = _format_guidance_number(
            item.numeric_value
        )

        if item.qualifier == "approximately":
            value = f"~{value}"

    elif item.qualitative_value is not None:
        return item.qualitative_value

    else:
        return "—"

    if item.unit:
        return f"{value} {item.unit}"

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
        change = metric_results[metric_id].change
        label = metric_labels[metric_id]
        direction = _direction_text(
            change.absolute_change
        )

        paragraphs.append(
            "<p>"
            f"<strong>{label}:</strong> "
            f"{direction} from "
            f"{_format_metric_value(metric_id, change.from_value, metric_kinds)} "
            "to "
            f"{_format_metric_value(metric_id, change.to_value, metric_kinds)} "
            f"({_format_percentage(change.percentage_change)})."
            "</p>"
        )

    return "".join(paragraphs)


def _build_guidance_summary(
    guidance_report,
) -> str:
    changed = guidance_report.changed
    unchanged = guidance_report.unchanged

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
        f"{'item was' if len(unchanged) == 1 else 'items were'} unchanged."
        "</strong> Forward-looking guidance is kept separate "
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
    config = COMPANY_CONFIGS[company_key]
    builder = config["builder"]

    return builder(
        previous_source=PeriodSource(
            document=config["previous_document"],
            page_number=config["financial_page"],
        ),
        current_source=PeriodSource(
            document=config["current_document"],
            page_number=config["financial_page"],
        ),
        company=config["company"],
        ticker=config["ticker"],
        metric_ids=config["metric_ids"],
    )


def _configure_openai_api_key() -> bool:
    if os.getenv("OPENAI_API_KEY"):
        return True

    try:
        secret_key = st.secrets.get(
            "OPENAI_API_KEY"
        )
    except Exception:  # noqa: BLE001
        secret_key = None

    if not secret_key:
        return False

    os.environ["OPENAI_API_KEY"] = str(
        secret_key
    )

    return True


def _synthesis_session_key(
    report,
) -> str:
    return (
        "validated_synthesis::"
        f"{report.ticker}::"
        f"{report.from_period}::"
        f"{report.to_period}"
    )


def _synthesis_error_key(
    report,
) -> str:
    return (
        "synthesis_error::"
        f"{report.ticker}::"
        f"{report.from_period}::"
        f"{report.to_period}"
    )


def _claim_provenance(
    claim,
    synthesis_input,
) -> str:
    source_facts = {
        fact.fact_id: fact
        for metric in synthesis_input.metrics
        for fact in metric.source_facts
    }

    evidence_sentences = {
        evidence.sentence_id: evidence
        for metric in synthesis_input.metrics
        for evidence in (
            *metric.direct_explanations,
            *metric.aligned_context,
        )
    }

    references: list[str] = []

    for fact_id in claim.source_fact_ids:
        fact = source_facts.get(
            fact_id
        )

        if fact is None:
            continue

        references.append(
            f"{fact.period} · "
            f"{fact.source.document_id} · "
            f"p. {fact.source.page_number}"
        )

    for sentence_id in claim.evidence_sentence_ids:
        evidence = evidence_sentences.get(
            sentence_id
        )

        if evidence is None:
            continue

        references.append(
            f"{evidence.document_id} · "
            f"p. {evidence.page_number}"
        )

    if claim.claim_type == "guidance_update":
        guidance_sources = {}

        for change in synthesis_input.guidance_changes:
            guidance_sources[
                (
                    change.metric_id,
                    change.target_period,
                )
            ] = (
                change.current.document_id,
                change.current.page_number,
            )

        for item in synthesis_input.guidance_introduced:
            guidance_sources[
                (
                    item.metric_id,
                    item.target_period,
                )
            ] = (
                item.document_id,
                item.page_number,
            )

        for item in synthesis_input.guidance_withdrawn:
            guidance_sources[
                (
                    item.metric_id,
                    item.target_period,
                )
            ] = (
                item.document_id,
                item.page_number,
            )

        source = guidance_sources.get(
            (
                claim.metric_id,
                claim.target_period,
            )
        )

        if source is not None:
            references.append(
                f"{source[0]} · p. {source[1]}"
            )

    unique_references = list(
        dict.fromkeys(
            references
        )
    )

    return " · ".join(
        unique_references
    )


def _render_claim_group(
    title: str,
    description: str,
    claims: list,
    metric_labels: dict[str, str],
    synthesis_input,
) -> None:
    st.markdown(
        f"#### {title}"
    )

    st.caption(
        description
    )

    if not claims:
        st.caption(
            "No validated claims in this category."
        )
        return

    for claim in claims:
        with st.container(
            border=True
        ):
            label = _metric_label(
                claim.metric_id,
                metric_labels,
            )

            st.markdown(
                f"**{label}**"
            )

            st.write(
                claim.text
            )

            provenance = (
                _claim_provenance(
                    claim,
                    synthesis_input,
                )
            )

            if provenance:
                st.caption(
                    f"Source · {provenance}"
                )


def _render_synthesis(
    validated,
    synthesis_input,
    metric_labels: dict[str, str],
) -> None:
    draft = validated.draft

    st.success(
        "Validated by EquityLens guardrails. "
        "Only accepted claims are shown."
    )

    meta_columns = st.columns(
        3,
        gap="small",
    )

    with meta_columns[0]:
        st.metric(
            "Model",
            validated.model,
        )

    with meta_columns[1]:
        st.metric(
            "Synthesis attempts",
            validated.attempts,
        )

    with meta_columns[2]:
        st.metric(
            "Guardrail rejections",
            len(validated.failures),
        )

    st.markdown(
        f"### {draft.title}"
    )

    claims_by_type = {
        claim_type: [
            claim
            for claim in draft.claims
            if claim.claim_type
            == claim_type
        ]
        for claim_type, _, _
        in CLAIM_GROUPS
    }

    first_row = st.columns(
        2,
        gap="medium",
    )

    with first_row[0]:
        claim_type, title, description = (
            CLAIM_GROUPS[0]
        )

        _render_claim_group(
            title=title,
            description=description,
            claims=claims_by_type[
                claim_type
            ],
            metric_labels=metric_labels,
            synthesis_input=synthesis_input,
        )

    with first_row[1]:
        claim_type, title, description = (
            CLAIM_GROUPS[1]
        )

        _render_claim_group(
            title=title,
            description=description,
            claims=claims_by_type[
                claim_type
            ],
            metric_labels=metric_labels,
            synthesis_input=synthesis_input,
        )

    second_row_claims = (
        claims_by_type[
            "management_explanation"
        ]
        or claims_by_type[
            "consistency_observation"
        ]
    )

    if second_row_claims:
        second_row = st.columns(
            2,
            gap="medium",
        )

        with second_row[0]:
            claim_type, title, description = (
                CLAIM_GROUPS[2]
            )

            _render_claim_group(
                title=title,
                description=description,
                claims=claims_by_type[
                    claim_type
                ],
                metric_labels=metric_labels,
                synthesis_input=synthesis_input,
            )

        with second_row[1]:
            claim_type, title, description = (
                CLAIM_GROUPS[3]
            )

            _render_claim_group(
                title=title,
                description=description,
                claims=claims_by_type[
                    claim_type
                ],
                metric_labels=metric_labels,
                synthesis_input=synthesis_input,
            )

    if draft.limitations:
        with st.container(
            border=True
        ):
            st.markdown(
                "**Research limitations**"
            )

            for limitation in draft.limitations:
                st.markdown(
                    f"- {limitation}"
                )

    if validated.failures:
        with st.expander(
            "Guardrail retry details"
        ):
            st.caption(
                "Rejected attempts are never "
                "accepted as research output."
            )

            for failure in validated.failures:
                st.markdown(
                    f"**Attempt {failure.attempt} · "
                    f"{failure.error_type}**"
                )

                st.code(
                    failure.error_message
                )


def _render_ai_synthesis_section(
    research_result,
    report,
    metric_labels: dict[str, str],
) -> None:
    st.markdown(
        '<div class="section-label">'
        "Guarded AI layer"
        "</div>",
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="section-title">'
        "Validated AI synthesis"
        "</div>",
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="ai-intro">
            <div class="ai-intro-title">
                AI writes. EquityLens decides what is allowed through.
            </div>
            <div class="ai-intro-text">
                The model receives only structured research data.
                Financial calculations remain deterministic, unsupported
                management explanations are rejected, and raw model output
                is never shown as accepted research.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    synthesis_input = (
        build_synthesis_input(
            research_result
        )
    )

    synthesis_key = (
        _synthesis_session_key(
            report
        )
    )

    error_key = (
        _synthesis_error_key(
            report
        )
    )

    existing = st.session_state.get(
        synthesis_key
    )

    has_api_key = (
        _configure_openai_api_key()
    )

    control_left, control_right = (
        st.columns(
            [1, 2.4],
            gap="medium",
        )
    )

    with control_left:
        button_label = (
            "Regenerate validated synthesis"
            if existing is not None
            else "Generate validated AI synthesis"
        )

        generate_clicked = (
            st.button(
                button_label,
                type="primary",
                disabled=not has_api_key,
            )
        )

    with control_right:
        st.caption(
            "Runs only when you click the button. "
            "This uses the OpenAI API and may incur API usage. "
            "The accepted result is kept in this browser session."
        )

    if not has_api_key:
        st.info(
            "No OPENAI_API_KEY was detected. "
            "Add it to your local .env file or Streamlit secrets "
            "to enable live synthesis."
        )

    if generate_clicked:
        with st.spinner(
            "Generating and validating synthesis..."
        ):
            try:
                client = (
                    OpenAISynthesisClient()
                )

                validated = run_synthesis(
                    synthesis_input=(
                        synthesis_input
                    ),
                    generator=client,
                )

                st.session_state[
                    synthesis_key
                ] = validated

                st.session_state.pop(
                    error_key,
                    None,
                )

                existing = validated

            except Exception as exc:  # noqa: BLE001
                st.session_state[
                    error_key
                ] = (
                    f"{type(exc).__name__}: "
                    f"{exc}"
                )

                existing = None

    error_message = (
        st.session_state.get(
            error_key
        )
    )

    if error_message:
        st.error(
            "The synthesis was not accepted."
        )

        with st.expander(
            "Technical detail"
        ):
            st.code(
                error_message
            )

    if existing is not None:
        _render_synthesis(
            validated=existing,
            synthesis_input=(
                synthesis_input
            ),
            metric_labels=(
                metric_labels
            ),
        )

    else:
        st.caption(
            "No AI synthesis has been generated "
            "for this company in the current session."
        )


def _evidence_display_state(result):
    assessment = result.evidence_assessment

    if assessment is None:
        return (
            "Narrative not configured",
            "evidence-muted",
            (
                "This metric is included in the financial analysis, but "
                "narrative driver retrieval is not configured for it."
            ),
            (),
        )

    if assessment.availability == "direct_explanation":
        return (
            "Validated explanation",
            "evidence-direct",
            (
                "Direct management evidence passed period, comparison and "
                "scope validation and is eligible to support a claim."
            ),
            assessment.direct_explanations,
        )

    if assessment.availability == "aligned_context_only":
        return (
            "Context only",
            "evidence-context",
            (
                "Related management commentary was found, but it is not "
                "eligible to support a direct explanation of the measured move."
            ),
            assessment.aligned_context,
        )

    return (
        "No eligible explanation",
        "evidence-muted",
        (
            "Narrative evidence was evaluated, but no text met the period, "
            "comparison and scope requirements for a direct explanation."
        ),
        (),
    )


def _render_narrative_evidence_controls(
    metric_ids: tuple[str, ...],
    metric_results: dict,
    metric_labels: dict[str, str],
) -> None:
    st.markdown(
        '<div class="section-label">Evidence controls</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="section-title">Narrative evidence controls</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="evidence-control-note">
            This panel shows whether management commentary is <strong>eligible</strong>
            to explain the measured quarter-on-quarter move. A metric can be fully
            analyzed financially even when no narrative explanation is admitted.
            EquityLens prefers an explicit restriction over an unsupported causal claim.
        </div>
        """,
        unsafe_allow_html=True,
    )

    with st.container(border=True):
        for index, metric_id in enumerate(metric_ids):
            result = metric_results[metric_id]
            status, badge_class, explanation, evidence_items = (
                _evidence_display_state(result)
            )

            metric_col, status_col, explanation_col = st.columns(
                [1.15, 1.05, 2.8],
                gap="medium",
            )

            with metric_col:
                st.markdown(
                    f'<div class="evidence-row-title">'
                    f'{metric_labels[metric_id]}'
                    '</div>',
                    unsafe_allow_html=True,
                )

            with status_col:
                st.markdown(
                    f'<div class="evidence-badge {badge_class}">'
                    f'{status}'
                    '</div>',
                    unsafe_allow_html=True,
                )

            with explanation_col:
                st.markdown(
                    f'<div class="evidence-row-copy">'
                    f'{explanation}'
                    '</div>',
                    unsafe_allow_html=True,
                )

            if evidence_items:
                with st.expander(
                    f"Evidence detail · {metric_labels[metric_id]}"
                ):
                    for evidence_item in evidence_items[:3]:
                        sentence = getattr(
                            evidence_item,
                            "sentence",
                            None,
                        )

                        if sentence is None:
                            continue

                        st.write(sentence.text)
                        st.caption(
                            "Source · "
                            f"{sentence.document_id} · "
                            f"p. {sentence.page_number}"
                        )

                    if len(evidence_items) > 3:
                        st.caption(
                            f"+ {len(evidence_items) - 3} additional "
                            "validated evidence item(s)."
                        )

            if index < len(metric_ids) - 1:
                st.divider()

    st.caption(
        "Status describes evidence eligibility for this exact period "
        "comparison — not whether management discussed the topic elsewhere "
        "in the report."
    )


with st.sidebar:
    st.markdown(
        "### ◈ EquityLens AI"
    )

    st.caption(
        "Evidence-grounded equity research"
    )

    st.divider()

    selected_company = st.selectbox(
        "Company",
        options=tuple(
            COMPANY_CONFIGS
        ),
        index=0,
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

    st.text_input(
        "Comparison",
        value=comparison_label,
        disabled=True,
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
    <div class="system-status-row">
        <span class="system-tag system-tag-good">
            <span class="status-dot"></span>Validated pipeline
        </span>
        <span class="system-tag">
            <span class="status-dot"></span>Deterministic finance
        </span>
        <span class="system-tag">
            <span class="status-dot"></span>Evidence grounded
        </span>
        <span class="system-tag">
            <span class="status-dot"></span>Auditable provenance
        </span>
        <span class="system-tag">
            <span class="status-dot"></span>Guidance tracked separately
        </span>
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
                _metric_card_label(
                    metric_id,
                    metric_labels,
                    metric_kinds,
                )
            ),
            value=(
                _format_metric_card_value(
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

_render_ai_synthesis_section(
    research_result=research_result,
    report=report,
    metric_labels=metric_labels,
)

st.write("")

_render_narrative_evidence_controls(
    metric_ids=metric_ids,
    metric_results=metric_results,
    metric_labels=metric_labels,
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
    "Each metric expands into the deterministic source facts used in "
    "the comparison, including document, page and table coordinates "
    "when available."
)

for metric_id in metric_ids:
    result = metric_results[
        metric_id
    ]

    change = result.change

    expander_label = (
        f"{metric_labels[metric_id]} · "
        f"{report.from_period} → {report.to_period}"
    )

    with st.expander(
        expander_label
    ):
        comparison_columns = st.columns(
            3,
            gap="small",
        )

        with comparison_columns[0]:
            st.metric(
                report.from_period,
                _format_metric_value(
                    metric_id,
                    change.from_value,
                    metric_kinds,
                ),
            )

        with comparison_columns[1]:
            st.metric(
                report.to_period,
                _format_metric_value(
                    metric_id,
                    change.to_value,
                    metric_kinds,
                ),
            )

        with comparison_columns[2]:
            st.metric(
                "Change",
                _format_percentage(
                    change.percentage_change
                ),
            )

        st.caption(
            "Deterministic source facts"
        )

        for fact in (
            result.audit_trail.source_facts
        ):
            evidence = fact.evidence

            locator_parts = [
                f"page {evidence.page_number}"
            ]

            if (
                evidence.table_number
                is not None
            ):
                locator_parts.append(
                    f"table {evidence.table_number}"
                )

            if evidence.row_label:
                locator_parts.append(
                    f"row: {evidence.row_label}"
                )

            if evidence.column_label:
                locator_parts.append(
                    f"column: {evidence.column_label}"
                )

            source_url = (
                _document_source_url(
                    evidence.document_id,
                    config,
                )
            )

            with st.container(
                border=True
            ):
                source_left, source_right = (
                    st.columns(
                        [3.2, 1],
                        gap="medium",
                    )
                )

                with source_left:
                    locator_text = (
                        " · ".join(
                            locator_parts
                        )
                    )

                    st.markdown(
                        f"""
                        <div class="source-box">
                            <div class="source-title">
                                {fact.period}
                            </div>
                            <div class="source-value">
                                {_format_decimal(fact.value)} {fact.unit}
                            </div>
                            <div class="source-meta">
                                {evidence.document_id}<br>
                                {locator_text}<br>
                                Fact ID · {fact.fact_id}
                            </div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

                with source_right:
                    st.caption(
                        "Source document"
                    )

                    if source_url:
                        st.link_button(
                            "Open report ↗",
                            source_url,
                            width="stretch",
                        )
                    else:
                        st.caption(
                            "No external source URL "
                            "is registered."
                        )


st.divider()

st.caption(
    "EquityLens separates deterministic financial calculations, "
    "validated narrative evidence and forward-looking guidance. "
    "The language model is not the calculation engine."
)