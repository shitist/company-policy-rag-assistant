from __future__ import annotations

import re
from typing import Dict, List


REFUSAL_TEXTS = {
    "en": "The current knowledge base does not contain enough evidence to answer this question.",
    "zh": "当前知识库没有足够依据回答这个问题。",
    "ja": "現在のナレッジベースには、この質問に回答するための十分な根拠がありません。",
}

LANGUAGE_NAMES = {
    "en": "English",
    "zh": "Simplified Chinese",
    "ja": "Japanese",
}

HIRAGANA_KATAKANA_RE = re.compile(r"[\u3040-\u30ff]")
CJK_RE = re.compile(r"[\u4e00-\u9fff]")


def detect_response_language(question: str) -> str:
    if HIRAGANA_KATAKANA_RE.search(question):
        return "ja"
    if CJK_RE.search(question):
        return "zh"
    return "en"


def normalize_response_language(response_language: str | None, question: str = "") -> str:
    value = (response_language or "auto").lower()
    aliases = {
        "auto": "auto",
        "english": "en",
        "en": "en",
        "simplified chinese": "zh",
        "chinese": "zh",
        "zh": "zh",
        "zh-cn": "zh",
        "简体中文": "zh",
        "japanese": "ja",
        "ja": "ja",
        "jp": "ja",
        "日本語": "ja",
    }
    normalized = aliases.get(value, value)
    if normalized == "auto":
        return detect_response_language(question)
    if normalized in REFUSAL_TEXTS:
        return normalized
    return "en"


def get_refusal_text(response_language: str | None = "en", question: str = "") -> str:
    language = normalize_response_language(response_language, question)
    return REFUSAL_TEXTS[language]


def format_context(chunks: List[Dict[str, object]]) -> str:
    blocks = []
    for chunk in chunks:
        metadata = chunk.get("metadata", {})
        if not isinstance(metadata, dict):
            metadata = {}
        chunk_id = metadata.get("chunk_id") or chunk.get("id")
        title = metadata.get("doc_title", "Unknown document")
        section = metadata.get("section_title", "Unknown section")
        text = chunk.get("text", "")
        blocks.append(f"[{chunk_id}] {title} > {section}\n{text}")
    return "\n\n---\n\n".join(blocks)


def build_grounded_prompt(
    question: str,
    chunks: List[Dict[str, object]],
    response_language: str | None = "auto",
) -> str:
    language = normalize_response_language(response_language, question)
    refusal_text = get_refusal_text(language)
    language_name = LANGUAGE_NAMES[language]

    return f"""You are a policy RAG assistant.

Important constraints:
- Use only the provided policy context.
- Do not use outside knowledge.
- Do not invent policy details.
- Answer in {language_name}.
- If the context is insufficient, answer exactly: {refusal_text}
- Include source chunk IDs in square brackets for every substantive claim.
- Keep the answer concise and practical.

User question:
{question}

Policy context:
{format_context(chunks)}
"""

