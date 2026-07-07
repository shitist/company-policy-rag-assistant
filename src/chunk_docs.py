from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Dict, Iterable, List

from src.load_docs import PolicyDocument


HEADING_RE = re.compile(r"^##\s+(.+?)\s*$")
SLUG_RE = re.compile(r"[^a-z0-9]+")


@dataclass(frozen=True)
class MarkdownChunk:
    id: str
    text: str
    metadata: Dict[str, object]


def slugify(value: str) -> str:
    value = value.lower().strip()
    value = SLUG_RE.sub("-", value)
    return value.strip("-") or "section"


def split_sections(document: PolicyDocument) -> List[tuple[str, str]]:
    sections: List[tuple[str, List[str]]] = []
    current_title = "Overview"
    current_lines: List[str] = []

    for line in document.body.splitlines():
        match = HEADING_RE.match(line)
        if match:
            if current_lines:
                sections.append((current_title, current_lines))
            current_title = match.group(1).strip()
            current_lines = [line]
        else:
            current_lines.append(line)

    if current_lines:
        sections.append((current_title, current_lines))

    return [(title, "\n".join(lines).strip()) for title, lines in sections if "\n".join(lines).strip()]


def split_long_text(text: str, target_chars: int = 1800, overlap_chars: int = 180) -> List[str]:
    paragraphs = [paragraph.strip() for paragraph in re.split(r"\n\s*\n", text) if paragraph.strip()]
    chunks: List[str] = []
    current: List[str] = []
    current_length = 0

    for paragraph in paragraphs:
        paragraph_length = len(paragraph)
        if current and current_length + paragraph_length > target_chars:
            chunk = "\n\n".join(current).strip()
            chunks.append(chunk)
            overlap = chunk[-overlap_chars:] if overlap_chars > 0 else ""
            current = [overlap, paragraph] if overlap else [paragraph]
            current_length = len("\n\n".join(current))
        else:
            current.append(paragraph)
            current_length += paragraph_length + 2

    if current:
        chunks.append("\n\n".join(current).strip())

    return chunks


def chunk_documents(
    documents: Iterable[PolicyDocument],
    target_chars: int = 1800,
    overlap_chars: int = 180,
) -> List[MarkdownChunk]:
    chunks: List[MarkdownChunk] = []

    for document in documents:
        doc_id = str(document.metadata["doc_id"])
        doc_title = str(document.metadata["doc_title"])

        for section_title, section_text in split_sections(document):
            section_id = slugify(section_title)
            text_parts = split_long_text(section_text, target_chars=target_chars, overlap_chars=overlap_chars)

            for local_index, text_part in enumerate(text_parts, start=1):
                chunk_index = len([chunk for chunk in chunks if chunk.metadata.get("doc_id") == doc_id])
                chunk_id = f"{doc_id}::{section_id}::chunk_{local_index:03d}"
                chunk_text = f"# {doc_title}\n\n{text_part}".strip()
                metadata: Dict[str, object] = {
                    **document.metadata,
                    "section_id": section_id,
                    "section_title": section_title,
                    "chunk_id": chunk_id,
                    "chunk_index": chunk_index,
                }
                chunks.append(MarkdownChunk(id=chunk_id, text=chunk_text, metadata=metadata))

    return chunks
