from __future__ import annotations

import os
from pathlib import Path
from typing import Dict, List

from src.mock_responses import generate_mock_answer
from src.prompts import build_grounded_prompt, get_refusal_text, normalize_response_language


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def load_environment() -> None:
    try:
        from dotenv import load_dotenv

        load_dotenv(PROJECT_ROOT / ".env")
    except Exception:
        return


def gemini_configured() -> bool:
    load_environment()
    return bool(os.getenv("GEMINI_API_KEY"))


def generate_with_gemini(
    question: str,
    chunks: List[Dict[str, object]],
    response_language: str | None = "auto",
) -> Dict[str, object]:
    language = normalize_response_language(response_language, question)
    refusal_text = get_refusal_text(language)
    api_key = os.getenv("GEMINI_API_KEY")
    model_name = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
    if not api_key:
        return generate_mock_answer(question, chunks, response_language=language)

    try:
        from google import genai

        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model=model_name,
            contents=build_grounded_prompt(question, chunks, response_language=language),
        )
        text = (getattr(response, "text", "") or "").strip()
    except Exception as exc:
        fallback = generate_mock_answer(question, chunks, response_language=language)
        fallback["provider"] = "mock-fallback"
        fallback["error"] = str(exc)
        return fallback

    if not text:
        text = refusal_text

    return {
        "answer": text,
        "provider": "gemini",
        "model": model_name,
        "language": language,
        "used_chunk_ids": [
            str(chunk.get("metadata", {}).get("chunk_id") or chunk.get("id"))
            for chunk in chunks
            if isinstance(chunk.get("metadata", {}), dict)
        ],
        "is_refusal": text.strip() == refusal_text,
    }


def generate_answer(
    question: str,
    chunks: List[Dict[str, object]],
    provider_choice: str = "auto",
    response_language: str | None = "auto",
) -> Dict[str, object]:
    load_environment()
    provider_choice = provider_choice.lower()
    language = normalize_response_language(response_language, question)
    refusal_text = get_refusal_text(language)

    if not chunks:
        return {
            "answer": refusal_text,
            "provider": "mock",
            "language": language,
            "used_chunk_ids": [],
            "is_refusal": True,
        }

    if provider_choice == "mock":
        return generate_mock_answer(question, chunks, response_language=language)

    if provider_choice == "gemini":
        if gemini_configured():
            return generate_with_gemini(question, chunks, response_language=language)
        fallback = generate_mock_answer(question, chunks, response_language=language)
        fallback["provider"] = "mock-no-api-key"
        return fallback

    if gemini_configured():
        return generate_with_gemini(question, chunks, response_language=language)

    return generate_mock_answer(question, chunks, response_language=language)

