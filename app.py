from __future__ import annotations

import os
from pathlib import Path
from typing import Dict, List

import pandas as pd
import streamlit as st

from src.build_index import rebuild_index
from src.generate import gemini_configured, generate_answer
from src.retrieve import retrieve_chunks


CATEGORY_LABELS = {
    "ai_tool_policy": "AI Tool Usage Policy",
    "sns_guideline": "SNS Operations Guideline",
    "information_security": "Information Security Policy",
    "copyright_material": "Copyright Material Policy",
    "talent_privacy": "Talent Privacy Protection Policy",
    "fan_content": "Fan Content Usage Policy",
    "expense_policy": "Expense Policy",
    "incident_response": "Public Incident Response Manual",
}

ROLE_LABELS = {
    "all": "All roles / departments",
    "all_staff": "All staff",
    "sns_operator": "SNS operator",
    "content_editor": "Content editor",
    "risk_response": "Risk response",
    "finance_reviewer": "Finance reviewer",
    "security_reviewer": "Security reviewer",
    "talent_support": "Talent support",
}

ANSWER_LANGUAGE_LABELS = {
    "auto": "Auto-detect from question",
    "en": "English",
    "zh": "简体中文",
    "ja": "日本語",
}

SAMPLE_QUESTIONS = [
    "Can I use an AI tool to draft external social media copy?",
    "AIツールでSNS投稿文の下書きを作れますか？",
    "炎上時の初動対応は何ですか？",
    "可以复用粉丝投稿的插画做活动素材吗？",
    "What should an SNS operator check before posting sensitive content?",
    "Can we reuse fan-submitted artwork in a campaign?",
    "What should staff do if a rumor includes private talent information?",
    "What information is required for a reimbursement request?",
    "What is the first response step during a public incident?",
    "Can the company approve my personal vacation request?",
]


def provider_status(provider_choice: str) -> str:
    if provider_choice == "Mock":
        return "Mock mode"
    if gemini_configured() and provider_choice in {"Auto", "Gemini"}:
        return "Gemini configured"
    return "Mock mode"


def citation_rows(chunks: List[Dict[str, object]], used_chunk_ids: List[str]) -> List[Dict[str, object]]:
    used = set(used_chunk_ids)
    rows = []
    for chunk in chunks:
        metadata = chunk.get("metadata", {})
        if not isinstance(metadata, dict):
            continue
        chunk_id = str(metadata.get("chunk_id") or chunk.get("id"))
        if used and chunk_id not in used:
            continue
        rows.append(
            {
                "source": metadata.get("doc_title"),
                "section": metadata.get("section_title"),
                "chunk_id": chunk_id,
                "distance": round(float(chunk.get("distance", 0.0)), 4),
            }
        )
    return rows


def metadata_summary(metadata: Dict[str, object]) -> Dict[str, object]:
    keys = [
        "doc_id",
        "category",
        "section_id",
        "role_tags",
        "department_tags",
        "version",
        "effective_date",
        "confidentiality",
        "source_file",
    ]
    return {key: metadata.get(key) for key in keys}


st.set_page_config(
    page_title="Company Policy RAG Assistant",
    layout="wide",
)

st.title("Company Policy RAG Assistant")
st.caption("Policy search with retrieval, citations, and source inspection")

st.info(
    "The bundled sample documents are fictional and contain no real company data. "
    "Role filters demonstrate retrieval behavior and are not an access-control layer."
)

with st.sidebar:
    st.header("Retrieval Settings")
    selected_categories = st.multiselect(
        "Document category",
        options=list(CATEGORY_LABELS.keys()),
        format_func=lambda value: CATEGORY_LABELS.get(value, value),
    )
    selected_role = st.selectbox(
        "Department / role",
        options=list(ROLE_LABELS.keys()),
        format_func=lambda value: ROLE_LABELS.get(value, value),
    )
    top_k = st.slider("Top-k retrieval number", min_value=1, max_value=8, value=4)

    st.header("Generation")
    provider_choice = st.selectbox("Generation provider", options=["Auto", "Mock", "Gemini"])
    response_language = st.selectbox(
        "Answer language",
        options=list(ANSWER_LANGUAGE_LABELS.keys()),
        format_func=lambda value: ANSWER_LANGUAGE_LABELS[value],
    )
    status = provider_status(provider_choice)
    st.metric("Provider status", status)

    if provider_choice == "Gemini" and status != "Gemini configured":
        st.warning("No GEMINI_API_KEY found. The app will fall back to mock mode.")

    if st.button("Rebuild Chroma index"):
        with st.spinner("Rebuilding Chroma index..."):
            count = rebuild_index()
        st.success(f"Rebuilt index with {count} chunks.")

st.subheader("Ask a Policy Question")
sample_question = st.selectbox("Try a sample question", SAMPLE_QUESTIONS)

with st.form("question_form"):
    question = st.text_area(
        "Question",
        value=sample_question,
        height=100,
        help="Ask about the bundled policy set. Unsupported questions should refuse.",
    )
    submitted = st.form_submit_button("Ask")

if submitted:
    if not question.strip():
        st.warning("Please enter a question.")
        st.stop()

    persist_path = Path(os.getenv("CHROMA_DB_PATH", "chroma_db"))
    with st.spinner("Retrieving policy chunks..."):
        chunks = retrieve_chunks(
            question=question.strip(),
            categories=selected_categories,
            role_filter=selected_role,
            top_k=top_k,
            persist_path=persist_path,
        )
        result = generate_answer(
            question.strip(),
            chunks,
            provider_choice=provider_choice,
            response_language=response_language,
        )

    answer_col, meta_col = st.columns([2, 1])

    with answer_col:
        st.subheader("Generated Answer")
        if result.get("is_refusal"):
            st.warning(str(result.get("answer")))
        else:
            st.markdown(str(result.get("answer")))

    with meta_col:
        st.subheader("Run Metadata")
        st.json(
            {
                "provider": result.get("provider"),
                "model": result.get("model", "mock"),
                "answer_language": result.get("language"),
                "top_k": top_k,
                "categories": selected_categories or "all",
                "role_filter": selected_role,
                "retrieved_chunks": len(chunks),
            }
        )
        if result.get("error"):
            st.warning(f"Provider fallback reason: {result['error']}")

    st.subheader("Citation Sources")
    rows = citation_rows(chunks, list(result.get("used_chunk_ids", [])))
    if rows and not result.get("is_refusal"):
        st.dataframe(pd.DataFrame(rows), hide_index=True, use_container_width=True)
    elif result.get("is_refusal"):
        st.info("No citation is shown because the available evidence was insufficient for an answer.")
    else:
        st.info("No citation rows were selected by the generator.")

    st.subheader("Retrieved Source Chunks")
    if not chunks:
        st.info("No chunks were retrieved. Try removing filters or rebuilding the index.")
    for index, chunk in enumerate(chunks, start=1):
        metadata = chunk.get("metadata", {})
        if not isinstance(metadata, dict):
            metadata = {}
        title = metadata.get("doc_title", "Unknown document")
        section = metadata.get("section_title", "Unknown section")
        chunk_id = metadata.get("chunk_id", chunk.get("id"))
        with st.expander(f"{index}. {title} / {section} / {chunk_id}"):
            st.markdown(chunk.get("text", ""))
            st.markdown("**Metadata**")
            st.json(metadata_summary(metadata))
else:
    st.subheader("What This Demo Shows")
    st.markdown(
        """
- Fictional sample policy documents only.
- Sidebar metadata filters for category and role/department.
- Chroma-backed retrieval over local embeddings.
- Mock LLM mode for API-key-free portfolio demos.
- Optional Gemini provider when configured.
- Answer language selection with English, Simplified Chinese, and Japanese support.
- Citation sources, retrieved chunks, and metadata visibility.
- Refusal instead of hallucination when evidence is insufficient.
"""
    )
