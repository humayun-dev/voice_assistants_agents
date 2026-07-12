"""
A minimal RAG vector store -- no database server required.

Index is built once (offline, via scripts/build_index.py) and cached to
a JSON file. At runtime, the server just loads that JSON into memory and
does cosine-similarity search against it. Swap this file out for a real
pgvector-backed implementation later if the document set grows -- the
public functions (build_index / load_index / search) are the seam to
keep the same shape.
"""

import json
import os
import numpy as np

from app.services.embedding_client import get_embedding
from app.utils.logger import logger

_INDEX_PATH = os.path.join(os.path.dirname(__file__), "..", "config", "leave_rules_index.json")
_DOC_PATH = os.path.join(os.path.dirname(__file__), "..", "config", "leave_rules.txt")

_cached_index = None  # list[{"text": str, "embedding": list[float]}]


def _chunk_document(raw_text: str) -> list[str]:
    """Splits the reference document into chunks on blank-line boundaries.
    leave_rules.txt is already organized into clearly titled sections
    (PRIVILEGE LEAVE, SICK LEAVE, ...), so a blank-line split gives
    reasonably coherent, topic-sized chunks without any NLP needed."""

    raw_chunks = raw_text.split("\n\n")
    chunks = [c.strip() for c in raw_chunks if len(c.strip()) > 40]
    return chunks


async def build_index() -> None:
    """One-time (or whenever the document changes) step: chunk the
    document, embed every chunk, and write the result to disk."""

    with open(_DOC_PATH, "r", encoding="utf-8") as f:
        raw_text = f.read()

    chunks = _chunk_document(raw_text)
    logger.info(f"Chunked leave_rules.txt into {len(chunks)} chunks")

    entries = []
    for i, chunk in enumerate(chunks):
        embedding = await get_embedding(chunk)
        entries.append({"text": chunk, "embedding": embedding})
        logger.info(f"Embedded chunk {i + 1}/{len(chunks)}")

    with open(_INDEX_PATH, "w", encoding="utf-8") as f:
        json.dump(entries, f)

    logger.info(f"Index built: {_INDEX_PATH}")


def load_index() -> None:
    """Loads the pre-built index into memory. Call this once at server
    startup. Safe to call if the index doesn't exist yet -- retrieval
    will just return no results until build_index() has been run."""

    global _cached_index

    if not os.path.exists(_INDEX_PATH):
        logger.warning(
            "leave_rules_index.json not found. Run "
            "'python scripts/build_index.py' once before starting the "
            "server, otherwise search_leave_rules will return nothing."
        )
        _cached_index = []
        return

    with open(_INDEX_PATH, "r", encoding="utf-8") as f:
        _cached_index = json.load(f)

    logger.info(f"Loaded {len(_cached_index)} chunks into the vector index")


def _cosine_similarity(a: list[float], b: list[float]) -> float:
    a_vec = np.array(a)
    b_vec = np.array(b)
    denom = (np.linalg.norm(a_vec) * np.linalg.norm(b_vec))
    if denom == 0:
        return 0.0
    return float(np.dot(a_vec, b_vec) / denom)


async def search(query: str, top_k: int = 3) -> str:
    """Embeds the query and returns the top_k most relevant chunks,
    joined into one string ready to hand back to Gemini as a tool
    response."""

    if not _cached_index:
        return "No reference document has been indexed yet."

    query_embedding = await get_embedding(query)

    scored = [
        (_cosine_similarity(query_embedding, entry["embedding"]), entry["text"])
        for entry in _cached_index
    ]
    scored.sort(key=lambda x: x[0], reverse=True)

    top_chunks = [text for _, text in scored[:top_k]]
    return "\n\n---\n\n".join(top_chunks)
