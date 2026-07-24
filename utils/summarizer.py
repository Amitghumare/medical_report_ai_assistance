"""
Step 4: Generate AI Summary
Uses LangChain + OpenAI to turn extracted lab results into a plain-language
health summary, highlighting normal vs abnormal findings.
"""

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser


SYSTEM_PROMPT = """You are a careful, empathetic medical report assistant.
You explain lab results in plain, easy-to-understand language for a
non-medical audience. You are NOT a doctor and must not diagnose
conditions or prescribe treatment. Always:
- Summarize each test result in one short line, noting whether it is
  normal, high, or low.
- Use a checkmark-style tone for normal values and a warning tone for
  abnormal ones (but write in plain text, no diagnosis).
- End with a short, general "what this could mean" note and a reminder
  to consult a licensed physician for interpretation and next steps.
- Keep the entire summary concise (150-250 words).
"""

USER_PROMPT = """Patient info: {patient_info}

Lab results (test, value, unit, reference range, status):
{results_table}

Write the health summary now."""


def build_chain(api_key: str, model: str = "gpt-4o-mini", temperature: float = 0.3):
    llm = ChatOpenAI(model=model, temperature=temperature, api_key=api_key)
    prompt = ChatPromptTemplate.from_messages(
        [("system", SYSTEM_PROMPT), ("user", USER_PROMPT)]
    )
    return prompt | llm | StrOutputParser()


def format_results_table(results: list) -> str:
    if not results:
        return "No structured lab values were detected in this report."
    lines = []
    for r in results:
        lines.append(
            f"- {r['Test']}: {r['Value']} {r['Unit']} "
            f"(reference: {r['Reference Range']}) -> {r['Status']}"
        )
    return "\n".join(lines)


def _generate_summary_uncached(patient_info: dict, results: list, api_key: str) -> str:
    """Call the LLM chain and return the generated summary text."""
    chain = build_chain(api_key)
    results_table = format_results_table(results)
    patient_info_str = ", ".join(
        f"{k}: {v}" for k, v in patient_info.items() if v
    ) or "Not provided"

    summary = chain.invoke(
        {"patient_info": patient_info_str, "results_table": results_table}
    )
    return summary.strip()


try:
    import streamlit as st

    @st.cache_data(show_spinner=False)
    def generate_summary(patient_info: dict, results: list, api_key: str) -> str:
        return _generate_summary_uncached(patient_info, results, api_key)

except ImportError:  # allows running summarizer logic outside streamlit (tests)
    generate_summary = _generate_summary_uncached
