"""Interactive portfolio UI for the AI Claims Analytics Assistant."""

from __future__ import annotations

import pandas as pd
import streamlit as st
from dotenv import load_dotenv

from ai import ClaimsAssistant, MissingAPIKeyError
from ai.sql_guard import UnsafeQueryError


load_dotenv()
st.set_page_config(
    page_title="Claims Analytics AI",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
        .stApp {background: #f7f9fc;}
        .hero {
            padding: 2rem 2.25rem;
            border-radius: 18px;
            background: linear-gradient(120deg, #0b1f3a 0%, #0f5f6d 58%, #1aa6a6 100%);
            color: white;
            margin-bottom: 1.25rem;
            box-shadow: 0 10px 30px rgba(11, 31, 58, 0.16);
        }
        .hero h1 {margin: 0 0 .45rem 0; font-size: 2.35rem;}
        .hero p {margin: 0; opacity: .92; font-size: 1.05rem; max-width: 850px;}
        .eyebrow {font-size: .78rem; letter-spacing: .12em; text-transform: uppercase; font-weight: 700; opacity: .8;}
        div[data-testid="stMetric"] {
            background: white;
            border: 1px solid #e6ebf2;
            padding: 1rem;
            border-radius: 12px;
            box-shadow: 0 4px 14px rgba(11, 31, 58, 0.05);
        }
        .disclaimer {
            border-left: 4px solid #1aa6a6;
            background: #eaf8f8;
            color: #163942;
            padding: .85rem 1rem;
            border-radius: 8px;
            margin: .75rem 0 1.25rem 0;
        }
        .footer {color: #667085; font-size: .82rem; margin-top: 2rem;}
    </style>
    <div class="hero">
        <div class="eyebrow">Healthcare analytics portfolio</div>
        <h1>AI Claims Analytics Assistant</h1>
        <p>Explore synthetic claims, denials, reimbursement, provider performance, population health, and payment-integrity review signals using guarded natural-language-to-SQL analytics.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    '<div class="disclaimer"><strong>Responsible-use notice:</strong> All records are synthetic. '
    "Payment-integrity indicators are review signals—not confirmed fraud, medical advice, or reimbursement determinations.</div>",
    unsafe_allow_html=True,
)

metric_columns = st.columns(4)
metric_columns[0].metric("Synthetic claims", "40,514")
metric_columns[1].metric("Warehouse tables", "12")
metric_columns[2].metric("SQL analyses", "30+")
metric_columns[3].metric("Maximum result rows", "200")

assistant = ClaimsAssistant()

with st.sidebar:
    st.header("Project guide")
    st.markdown(
        "**How the assistant works**\n\n"
        "1. Plans one read-only SQLite query.\n"
        "2. Validates tables, columns, and SQL syntax.\n"
        "3. Runs against a read-only warehouse.\n"
        "4. Returns evidence, a visual, and visible SQL."
    )
    st.divider()
    st.subheader("AI status")
    if assistant.api_key:
        st.success(f"Free-form AI enabled · `{assistant.model}`")
    else:
        st.warning("Curated mode is active. Add `OPENAI_API_KEY` to enable free-form questions.")
    st.divider()
    st.subheader("Safety controls")
    st.markdown("- Approved semantic layer\n- SELECT-only SQL\n- Read-only database\n- Five-second timeout\n- 200-row limit")
    st.divider()
    st.caption("Do not enter PHI, real patient data, credentials, or confidential company information.")

st.subheader("Ask an analytics question")
choice_column, question_column = st.columns([1, 2])
with choice_column:
    selected = st.selectbox(
        "Tested starting point",
        ["Write my own question"] + assistant.curated_questions,
    )
with question_column:
    default_question = "" if selected == "Write my own question" else selected
    question = st.text_input(
        "Question",
        value=default_question,
        placeholder="Example: Compare denial rates by provider specialty",
    )

analyze = st.button("Analyze claims data", type="primary", use_container_width=True)

if analyze:
    try:
        with st.spinner("Planning a safe query and analyzing the synthetic warehouse..."):
            result = assistant.ask(question)

        frame = pd.DataFrame(result.rows, columns=result.columns)
        summary_tab, data_tab, sql_tab = st.tabs(["Executive answer", "Result table", "Approved SQL"])

        with summary_tab:
            st.success(result.answer)
            if not frame.empty and result.chart_type != "none" and result.x_axis and result.y_axis:
                chart_frame = frame.set_index(result.x_axis)[[result.y_axis]]
                st.subheader("Visual evidence")
                if result.chart_type == "line":
                    st.line_chart(chart_frame)
                else:
                    st.bar_chart(chart_frame)
            elif frame.empty:
                st.info("The approved query returned no matching rows.")

        with data_tab:
            st.dataframe(frame, use_container_width=True, hide_index=True)
            st.caption(f"{len(frame):,} rows displayed · Maximum 200 rows per query")

        with sql_tab:
            st.code(result.sql, language="sql")
            st.caption("This SQL passed the semantic allowlist and read-only query guard before execution.")

        st.caption(f"Answer mode: {result.source} · Synthetic-data portfolio demonstration")
    except MissingAPIKeyError as exc:
        st.error(str(exc))
    except (UnsafeQueryError, ValueError) as exc:
        st.error(f"The request could not be run safely: {exc}")
    except Exception:
        st.error("The analysis could not be completed. Check the API key, billing status, and application logs, then try again.")

st.markdown(
    '<div class="footer">Built with Python, SQLite, Streamlit, SQLGlot, and the OpenAI Responses API. '
    "Designed for operational and financial decision support—not clinical decision-making.</div>",
    unsafe_allow_html=True,
)
