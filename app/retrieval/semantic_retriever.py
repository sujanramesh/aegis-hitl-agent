from pathlib import Path
import math

from app.retrieval.embeddings import generate_embedding


RUNBOOK_DIRECTORY = (
    Path(__file__).resolve().parents[2]
    / "knowledge"
    / "runbooks"
)

_embedding_index: list[dict] | None = None


def chunk_markdown(content: str) -> list[str]:
    """
    Split a Markdown runbook into meaningful operational sections.

    Very small metadata-only sections are excluded because
    they provide little useful retrieval context.
    """

    chunks = []
    current_chunk = []

    for line in content.splitlines():

        if line.startswith("## ") and current_chunk:
            chunk = "\n".join(
                current_chunk
            ).strip()

            if _is_meaningful_chunk(chunk):
                chunks.append(chunk)

            current_chunk = []

        current_chunk.append(line)

    if current_chunk:
        chunk = "\n".join(
            current_chunk
        ).strip()

        if _is_meaningful_chunk(chunk):
            chunks.append(chunk)

    return chunks


def _is_meaningful_chunk(chunk: str) -> bool:
    """
    Exclude tiny metadata-only chunks that are unlikely
    to provide useful operational guidance.
    """

    meaningful_lines = [
        line.strip()
        for line in chunk.splitlines()
        if line.strip()
        and not line.strip().startswith("#")
    ]

    meaningful_text = " ".join(
        meaningful_lines
    )

    return len(meaningful_text) >= 40


def cosine_similarity(
    vector_a: list[float],
    vector_b: list[float],
) -> float:
    """
    Calculate cosine similarity between two embedding vectors.
    """

    if len(vector_a) != len(vector_b):
        raise ValueError(
            "Embedding vectors must have the same dimensions."
        )

    dot_product = sum(
        a * b
        for a, b in zip(
            vector_a,
            vector_b
        )
    )

    magnitude_a = math.sqrt(
        sum(a * a for a in vector_a)
    )

    magnitude_b = math.sqrt(
        sum(b * b for b in vector_b)
    )

    if magnitude_a == 0 or magnitude_b == 0:
        return 0.0

    return dot_product / (
        magnitude_a * magnitude_b
    )


def load_runbook_chunks() -> list[dict]:
    """
    Load meaningful chunks from all operational runbooks.
    """

    documents = []

    for runbook_path in sorted(
        RUNBOOK_DIRECTORY.glob("*.md")
    ):
        content = runbook_path.read_text(
            encoding="utf-8"
        )

        chunks = chunk_markdown(
            content
        )

        for index, chunk in enumerate(chunks):
            documents.append(
                {
                    "source": runbook_path.name,
                    "chunk_id": index,
                    "content": chunk,
                }
            )

    return documents


def build_embedding_index(
    force_rebuild: bool = False,
) -> list[dict]:
    """
    Build and cache embeddings for the operational
    runbook knowledge base.

    Document embeddings are generated once per process
    rather than once per search.
    """

    global _embedding_index

    if (
        _embedding_index is not None
        and not force_rebuild
    ):
        return _embedding_index

    documents = load_runbook_chunks()

    index = []

    for document in documents:

        embedding = generate_embedding(
            document["content"]
        )

        index.append(
            {
                **document,
                "embedding": embedding,
            }
        )

    _embedding_index = index

    return _embedding_index


def semantic_search(
    query: str,
    top_k: int = 3,
) -> list[dict]:
    """
    Retrieve the operational runbook chunks most
    semantically relevant to a natural-language query.
    """

    if not query or not query.strip():
        raise ValueError(
            "Semantic search query cannot be empty."
        )

    if top_k < 1:
        raise ValueError(
            "top_k must be at least 1."
        )

    index = build_embedding_index()

    if not index:
        return []

    query_embedding = generate_embedding(
        query
    )

    ranked_results = []

    for document in index:

        score = cosine_similarity(
            query_embedding,
            document["embedding"],
        )

        ranked_results.append(
            {
                "source": document["source"],
                "chunk_id": document["chunk_id"],
                "content": document["content"],
                "similarity_score": score,
            }
        )

    ranked_results.sort(
        key=lambda result: result[
            "similarity_score"
        ],
        reverse=True,
    )

    return ranked_results[:top_k]