from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATA_DIR = PROJECT_ROOT / "data" / "policies"


@dataclass(frozen=True)
class PolicyDocument:
    """Loaded Markdown policy document with flat metadata."""

    path: Path
    body: str
    metadata: Dict[str, str]


def parse_front_matter(raw_text: str) -> tuple[Dict[str, str], str]:
    lines = raw_text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}, raw_text

    end_index: Optional[int] = None
    for index, line in enumerate(lines[1:], start=1):
        if line.strip() == "---":
            end_index = index
            break

    if end_index is None:
        return {}, raw_text

    metadata: Dict[str, str] = {}
    for line in lines[1:end_index]:
        if not line.strip() or line.strip().startswith("#"):
            continue
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        metadata[key.strip()] = value.strip()

    body = "\n".join(lines[end_index + 1 :]).strip()
    return metadata, body


def extract_markdown_title(body: str, fallback: str) -> str:
    for line in body.splitlines():
        if line.startswith("# "):
            return line[2:].strip()
    return fallback


def load_policy_documents(data_dir: Path | str = DEFAULT_DATA_DIR) -> List[PolicyDocument]:
    base_dir = Path(data_dir)
    documents: List[PolicyDocument] = []

    for path in sorted(base_dir.glob("*.md")):
        raw_text = path.read_text(encoding="utf-8")
        metadata, body = parse_front_matter(raw_text)
        doc_title = metadata.get("doc_title") or extract_markdown_title(body, path.stem)

        normalized = {
            "doc_id": metadata.get("doc_id", path.stem),
            "doc_title": doc_title,
            "category": metadata.get("category", "uncategorized"),
            "role_tags": metadata.get("role_tags", "all_staff"),
            "department_tags": metadata.get("department_tags", "general"),
            "version": metadata.get("version", "v1.0-demo"),
            "effective_date": metadata.get("effective_date", "2026-01-01-demo"),
            "language": metadata.get("language", "en"),
            "confidentiality": metadata.get("confidentiality", "public_sample"),
            "keywords": metadata.get("keywords", ""),
            "source_file": str(path.relative_to(PROJECT_ROOT)).replace("\\", "/"),
        }

        documents.append(PolicyDocument(path=path, body=body, metadata=normalized))

    return documents


def iter_document_metadata(documents: Iterable[PolicyDocument]) -> Iterable[Dict[str, str]]:
    for document in documents:
        yield document.metadata
