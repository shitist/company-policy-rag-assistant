from __future__ import annotations

import os
from pathlib import Path
from typing import List

import chromadb
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction

from src.chunk_docs import MarkdownChunk, chunk_documents
from src.load_docs import DEFAULT_DATA_DIR, PROJECT_ROOT, load_policy_documents


COLLECTION_NAME = "company_policy_rag_v1"
DEFAULT_CHROMA_PATH = PROJECT_ROOT / "chroma_db"
DEFAULT_EMBEDDING_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"


def load_environment() -> None:
    try:
        from dotenv import load_dotenv

        load_dotenv(PROJECT_ROOT / ".env")
    except Exception:
        return


def get_embedding_model_name() -> str:
    return os.getenv("EMBEDDING_MODEL", DEFAULT_EMBEDDING_MODEL)


def get_embedding_function(model_name: str | None = None) -> SentenceTransformerEmbeddingFunction:
    return SentenceTransformerEmbeddingFunction(model_name=model_name or get_embedding_model_name())


def get_chroma_client(persist_path: Path | str = DEFAULT_CHROMA_PATH) -> chromadb.PersistentClient:
    return chromadb.PersistentClient(path=str(persist_path))


def rebuild_index(
    data_dir: Path | str = DEFAULT_DATA_DIR,
    persist_path: Path | str = DEFAULT_CHROMA_PATH,
    collection_name: str = COLLECTION_NAME,
) -> int:
    load_environment()
    documents = load_policy_documents(data_dir)
    chunks = chunk_documents(documents)
    client = get_chroma_client(persist_path)

    try:
        client.delete_collection(collection_name)
    except Exception:
        pass

    collection = client.get_or_create_collection(
        name=collection_name,
        embedding_function=get_embedding_function(),
        metadata={"hnsw:space": "cosine"},
    )

    if not chunks:
        return 0

    collection.add(
        ids=[chunk.id for chunk in chunks],
        documents=[chunk.text for chunk in chunks],
        metadatas=[chunk.metadata for chunk in chunks],
    )
    return len(chunks)


def preview_chunks(data_dir: Path | str = DEFAULT_DATA_DIR) -> List[MarkdownChunk]:
    return chunk_documents(load_policy_documents(data_dir))


def main() -> None:
    count = rebuild_index()
    print(f"Built Chroma collection '{COLLECTION_NAME}' with {count} chunks.")


if __name__ == "__main__":
    main()
