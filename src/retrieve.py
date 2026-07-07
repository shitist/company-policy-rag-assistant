from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Optional, Sequence

from src.build_index import (
    COLLECTION_NAME,
    DEFAULT_CHROMA_PATH,
    get_chroma_client,
    get_embedding_function,
    rebuild_index,
)


def get_collection(persist_path: Path | str = DEFAULT_CHROMA_PATH, auto_build: bool = True):
    client = get_chroma_client(persist_path)
    try:
        collection = client.get_collection(
            name=COLLECTION_NAME,
            embedding_function=get_embedding_function(),
        )
    except Exception:
        if not auto_build:
            raise
        rebuild_index(persist_path=persist_path)
        collection = client.get_collection(
            name=COLLECTION_NAME,
            embedding_function=get_embedding_function(),
        )

    if auto_build and collection.count() == 0:
        rebuild_index(persist_path=persist_path)
        collection = client.get_collection(
            name=COLLECTION_NAME,
            embedding_function=get_embedding_function(),
        )

    return collection


def build_category_where(categories: Optional[Sequence[str]]) -> Optional[Dict[str, object]]:
    selected = [category for category in categories or [] if category]
    if not selected:
        return None
    if len(selected) == 1:
        return {"category": selected[0]}
    return {"category": {"$in": selected}}


def tag_matches(metadata: Dict[str, object], selected_role: Optional[str]) -> bool:
    if not selected_role or selected_role == "all":
        return True

    role_tags = str(metadata.get("role_tags", ""))
    department_tags = str(metadata.get("department_tags", ""))
    tags = {tag.strip() for tag in f"{role_tags},{department_tags}".split(",") if tag.strip()}
    return selected_role in tags or "all_staff" in tags


def retrieve_chunks(
    question: str,
    categories: Optional[Sequence[str]] = None,
    role_filter: Optional[str] = None,
    top_k: int = 4,
    persist_path: Path | str = DEFAULT_CHROMA_PATH,
) -> List[Dict[str, object]]:
    collection = get_collection(persist_path=persist_path)
    count = collection.count()
    if count == 0:
        return []

    requested = min(max(top_k * 5, top_k), count)
    where = build_category_where(categories)
    result = collection.query(
        query_texts=[question],
        n_results=requested,
        where=where,
        include=["documents", "metadatas", "distances"],
    )

    ids = result.get("ids", [[]])[0]
    documents = result.get("documents", [[]])[0]
    metadatas = result.get("metadatas", [[]])[0]
    distances = result.get("distances", [[]])[0]

    chunks: List[Dict[str, object]] = []
    for chunk_id, text, metadata, distance in zip(ids, documents, metadatas, distances):
        metadata = metadata or {}
        if not tag_matches(metadata, role_filter):
            continue
        chunks.append(
            {
                "id": chunk_id,
                "text": text,
                "metadata": metadata,
                "distance": distance,
            }
        )
        if len(chunks) >= top_k:
            break

    return chunks
