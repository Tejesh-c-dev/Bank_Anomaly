import json
import os

import streamlit as st

from services.explainer import GEMINI_MODEL, generate_explanation


st.set_page_config(
    page_title="Apex Financial | Risk Intelligence",
    page_icon="BANK",
    layout="wide",
)

st.markdown(
    """
    <style>
        :root {
            --ink: #16263d;
            --muted: #65748b;
            --line: #dce5ef;
            --surface: #ffffff;
            --canvas: #f4f7fb;
            --blue: #2563eb;
            --blue-soft: #eaf1ff;
            --red: #c2413b;
            --red-soft: #fff0ef;
            --green: #147d64;
            --green-soft: #e9f7f2;
            --amber: #a66a00;
            --amber-soft: #fff7e6;
        }
        .stApp { background: var(--canvas); color: var(--ink); }
        .block-container { max-width: 1440px; padding: 2.5rem 3rem 4rem; }
        [data-testid="stSidebar"] { background: #12233a; }
        [data-testid="stSidebar"] * { color: #eef4fb; }
        [data-testid="stSidebar"] .stSelectbox label { color: #aebed0; }
        h1, h2, h3, p { color: var(--ink); }
        h1 { letter-spacing: -0.02em; font-size: 2.15rem; margin-bottom: 0.35rem; }
        h2 { font-size: 1.25rem; margin-top: 1.8rem; }
        .eyebrow { color: var(--blue); font-size: 0.72rem; font-weight: 700; letter-spacing: 0.12em; text-transform: uppercase; margin-bottom: 0.3rem; }
        .subtitle { color: var(--muted); font-size: 0.98rem; margin-bottom: 1.7rem; }
        .card { background: var(--surface); border: 1px solid var(--line); border-radius: 10px; padding: 1.1rem 1.25rem; min-height: 100px; box-shadow: 0 3px 12px rgba(26, 46, 75, 0.04); }
        .card-label { color: var(--muted); font-size: 0.73rem; font-weight: 700; letter-spacing: 0.08em; text-transform: uppercase; }
        .card-value { color: var(--ink); font-size: 1.22rem; font-weight: 700; margin-top: 0.45rem; overflow-wrap: anywhere; }
        .card-meta { color: var(--muted); font-size: 0.78rem; margin-top: 0.3rem; }
        .status-card { border-left: 4px solid var(--red); background: var(--red-soft); }
        .status-card.safe { border-left-color: var(--green); background: var(--green-soft); }
        .status-card.review { border-left-color: var(--amber); background: var(--amber-soft); }
        .status-text { font-size: 1.05rem; font-weight: 750; margin-top: 0.5rem; }
        .risk-panel { background: var(--surface); border: 1px solid var(--line); border-radius: 10px; padding: 1.15rem 1.25rem; margin-top: 1rem; }
        .risk-row { display: flex; justify-content: space-between; align-items: baseline; gap: 1rem; }
        .risk-level { font-size: 1.1rem; font-weight: 750; }
        .risk-score { color: var(--muted); font-size: 0.9rem; }
        .section-caption { color: var(--muted); font-size: 0.88rem; margin-top: -0.5rem; }
        div[data-testid="stExpander"] { background: var(--surface); border: 1px solid var(--line); border-radius: 10px; }
        div[data-testid="stButton"] button { border-radius: 7px; font-weight: 700; }
        .stProgress > div > div > div > div { background-color: var(--blue); }
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_data
def load_transactions():
    data_path = os.path.join(os.path.dirname(__file__), "data", "transactions.json")
    with open(data_path, "r", encoding="utf-8") as transactions_file:
        return json.load(transactions_file)


transactions = load_transactions()
transaction_options = {
    transaction["transaction_id"]: transaction for transaction in transactions
}
if "explanation" not in st.session_state:
    st.session_state.explanation = None
if "positive_feedback" not in st.session_state:
    st.session_state.positive_feedback = 0
if "total_feedback" not in st.session_state:
    st.session_state.total_feedback = 0

total_feedback = st.session_state.total_feedback
clarity_score = (
    st.session_state.positive_feedback / total_feedback * 100
    if total_feedback
    else 0
)

st.markdown('<div class="eyebrow">Apex Financial · Risk Intelligence</div>', unsafe_allow_html=True)
st.title("Transaction monitoring dashboard")
st.markdown(
    "Review transaction signals and generate a customer-friendly explanation for the selected event.",
    unsafe_allow_html=True,
)

with st.sidebar:
    st.header("Transaction selector")
    selected_id = st.selectbox(
        "Select a transaction",
        options=list(transaction_options),
        format_func=lambda transaction_id: (
            f"{transaction_id} - "
            f"{transaction_options[transaction_id].get('customer_name', 'Unknown customer')}"
        ),
    )
    model_name = st.selectbox(
        "AI model",
        options=[GEMINI_MODEL],
    )

selected_transaction = transaction_options[selected_id]
currency = selected_transaction.get("currency", "USD")
amount = selected_transaction.get("amount", 0.0)
average_amount = selected_transaction.get(
    "historical_avg_amount",
    selected_transaction.get("average_transaction_amount", 0.0),
)
risk_score = selected_transaction.get(
    "risk_score", selected_transaction.get("anomaly_score", 0.0)
)
risk_score = max(0.0, min(float(risk_score), 1.0))

if risk_score >= 0.75:
    risk_level, risk_class = "High risk", "high"
elif risk_score >= 0.4:
    risk_level, risk_class = "Review", "review"
else:
    risk_level, risk_class = "Low risk", "safe"

is_anomaly = bool(
    selected_transaction.get("is_anomaly", selected_transaction.get("anomaly_flag", False))
)
status_label = "Anomaly detected" if is_anomaly else "No anomaly detected"
status_class = "status-card" if is_anomaly else "status-card safe"

st.subheader(f"Transaction {selected_transaction.get('transaction_id', '-')}")
st.markdown('<div class="section-caption">Selected event overview</div>', unsafe_allow_html=True)
metric_columns = st.columns(4)
cards = [
    ("Transaction amount", f"{currency} {amount:,.2f}", f"Historical average: {currency} {average_amount:,.2f}"),
    ("Customer", selected_transaction.get("customer_name", "Unknown customer"), selected_transaction.get("customer_id", "-")),
    ("Location", selected_transaction.get("location", "-"), f"Usual: {selected_transaction.get('usual_location', '-')}"),
    ("Event time", selected_transaction.get("timestamp", "-"), selected_transaction.get("merchant", "-")),
]
for column, (label, value, meta) in zip(metric_columns, cards):
    with column:
        st.markdown(
            f'<div class="card"><div class="card-label">{label}</div>'
            f'<div class="card-value">{value}</div><div class="card-meta">{meta}</div></div>',
            unsafe_allow_html=True,
        )

st.metric(
    "Clarity score",
    f"{clarity_score:.0f}%",
    f"{total_feedback} response{'s' if total_feedback != 1 else ''}",
)

status_columns = st.columns([1.1, 1.9])
with status_columns[0]:
    st.markdown(
        f'<div class="card {status_class}"><div class="card-label">Detection status</div>'
        f'<div class="status-text">{status_label}</div><div class="card-meta">{selected_transaction.get("status", "-")}</div></div>',
        unsafe_allow_html=True,
    )
with status_columns[1]:
    st.markdown(
        '<div class="risk-panel"><div class="risk-row"><span class="card-label">Risk assessment</span>'
        f'<span class="risk-score">{risk_score:.0%} score</span></div>'
        f'<div class="risk-level">{risk_level}</div>',
        unsafe_allow_html=True,
    )
    st.progress(risk_score)
    st.markdown('</div>', unsafe_allow_html=True)

with st.expander("View transaction details"):
    detail_columns = st.columns(4)
    detail_values = [
        ("Transaction ID", selected_transaction.get("transaction_id", "-")),
        ("Anomaly type", selected_transaction.get("anomaly_type", "-")),
        ("Category", selected_transaction.get("category", "-")),
        ("Device", selected_transaction.get("device_info", "-")),
        ("Usual device", selected_transaction.get("usual_device", "-")),
        ("Account age", f"{selected_transaction.get('account_age_days', '-')} days"),
        ("Beneficiary", "New" if selected_transaction.get("new_beneficiary") else "Existing"),
        ("Currency", currency),
    ]
    for index, (label, value) in enumerate(detail_values):
        with detail_columns[index % 4]:
            st.markdown(
                f'<div class="card"><div class="card-label">{label}</div><div class="card-value">{value}</div></div>',
                unsafe_allow_html=True,
            )

st.divider()
st.subheader("Why was this transaction flagged?")
st.markdown('<div class="section-caption">Signals contributing to the current assessment</div>', unsafe_allow_html=True)

reasons = selected_transaction.get("reasons") or selected_transaction.get("rule_flags")
if reasons:
    for reason in reasons:
        st.markdown(f"- {reason}")
else:
    st.info("No predefined reasons were recorded for this transaction.")

st.divider()
if st.button("Generate AI Explanation", type="primary"):
    with st.spinner("Generating explanation..."):
        st.session_state.explanation = generate_explanation(
            selected_transaction,
            model_name=model_name,
        )

if st.session_state.explanation:
    explanation = st.session_state.explanation
    with st.container():
        st.subheader("AI Explanation")
        st.markdown("#### AI Summary")
        st.write(explanation.get("summary", "No summary available."))

        with st.expander("Why It Was Flagged", expanded=True):
            explanation_reasons = explanation.get("reasons", [])
            if explanation_reasons:
                for reason in explanation_reasons:
                    st.markdown(f"- {reason}")
            else:
                st.info("No additional AI-generated reasons were returned.")

        with st.expander("Recommended Actions", expanded=True):
            actions = explanation.get("recommended_actions", [])
            if actions:
                for action in actions:
                    st.markdown(f"- {action}")
            else:
                st.info("No recommended actions were returned.")

        st.markdown("**Was this explanation clear?**")
        feedback_columns = st.columns(2)
        with feedback_columns[0]:
            if st.button("👍 Clear", key="clear_feedback"):
                st.session_state.positive_feedback += 1
                st.session_state.total_feedback += 1
                st.rerun()
        with feedback_columns[1]:
            if st.button("👎 Not Clear", key="not_clear_feedback"):
                st.session_state.total_feedback += 1
                st.rerun()
