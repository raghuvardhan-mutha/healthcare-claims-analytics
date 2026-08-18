"""Interactive portfolio UI for the AI Claims Analytics Assistant."""

from __future__ import annotations

import pandas as pd
import streamlit as st
from dotenv import load_dotenv

from ai import ClaimsAssistant, MissingAPIKeyError
from ai.sql_guard import UnsafeQueryError


load_dotenv()
st.set_page_config(
    page_title="AI Claims Analytics Assistant",
    page_icon="🏥",
    layout="wide",
)

st.title("AI Healthcare Claims Analytics Assistant")
st.caption("Ask questions about synthetic claims, denials, providers, population health, and payment-integrity signals.")
st.info("Portfolio demo only: all records are synthetic, and risk signals are not confirmed fraud.")

assistant = ClaimsAssistant()

with st.sidebar:
    st.header("How it works")
    st.markdown(
        "1. AI translates a question into SQLite SQL.\n"
        "2. A guard allows only approved read-only queries.\n"
        "3. The app returns the result, chart, explanation, and SQL."
    )
    if assistant.api_key:
        st.success(f"OpenAI enabled · `{assistant.model}`")
    else:
        st.warning("No API key detected. Built-in questions still work; add `OPENAI_API_KEY` for free-form questions.")

selected = st.selectbox(
    "Start with a tested question",
    ["Write my own question"] + assistant.curated_questions,
)
default_question = "" if selected == "Write my own question" else selected
question = st.text_input(
    "Question",
    value=default_question,
    placeholder="Example: Compare denial rates by provider specialty",
)

if st.button("Analyze", type="primary", use_container_width=True):
    try:
        with st.spinner("Planning a safe query and analyzing the result..."):
            result = assistant.ask(question)

        st.subheader("Answer")
        st.write(result.answer)
        frame = pd.DataFrame(result.rows, columns=result.columns)

        if not frame.empty and result.chart_type != "none" and result.x_axis and result.y_axis:
            chart_frame = frame.set_index(result.x_axis)[[result.y_axis]]
            if result.chart_type == "line":
                st.line_chart(chart_frame)
            else:
                st.bar_chart(chart_frame)

        st.subheader("Result")
        st.dataframe(frame, use_container_width=True, hide_index=True)
        with st.expander("View approved SQL"):
            st.code(result.sql, language="sql")
        st.caption(f"Answer mode: {result.source} · Maximum 200 result rows")
    except MissingAPIKeyError as exc:
        st.error(str(exc))
    except (UnsafeQueryError, ValueError) as exc:
        st.error(f"The request could not be run safely: {exc}")
    except Exception:
        st.error("The analysis could not be completed. Check the API key and application logs, then try again.")
