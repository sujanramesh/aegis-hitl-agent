import os
import time

from dotenv import load_dotenv
from google import genai
from google.genai import types, errors


# =========================================================
# Configuration
# =========================================================

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise ValueError("GEMINI_API_KEY is not configured")


EMBEDDING_MODEL = "gemini-embedding-2"
EMBEDDING_DIMENSION = 768

MAX_EMBEDDING_ATTEMPTS = 3
INITIAL_RETRY_DELAY_SECONDS = 1


# =========================================================
# Gemini client
# =========================================================

client = genai.Client(
    api_key=api_key
)


# =========================================================
# Application-level embedding exception
# =========================================================

class EmbeddingUnavailableError(Exception):
    """
    Raised when the embedding provider remains unavailable
    after controlled retry attempts.

    This allows the Aegis retrieval layer to degrade
    gracefully instead of exposing provider failures
    directly to the workflow.
    """

    pass


# =========================================================
# Embedding resilience
# =========================================================

def _is_retryable_error(error: Exception) -> bool:
    """
    Determine whether an embedding provider error is
    transient and therefore safe to retry.
    """

    status_code = getattr(
        error,
        "status_code",
        None
    )

    if status_code is None:
        status_code = getattr(
            error,
            "code",
            None
        )

    return status_code in {
        429,
        500,
        502,
        503,
        504,
    }


def _embed_content_with_retry(**kwargs):
    """
    Execute a Gemini embedding request with bounded
    retries and exponential backoff.
    """

    delay = INITIAL_RETRY_DELAY_SECONDS

    for attempt in range(
        1,
        MAX_EMBEDDING_ATTEMPTS + 1
    ):

        try:
            return client.models.embed_content(
                **kwargs
            )

        except (
            errors.ClientError,
            errors.ServerError,
        ) as error:

            if not _is_retryable_error(error):
                raise

            if attempt == MAX_EMBEDDING_ATTEMPTS:

                print(
                    "[Aegis Embedding] Final provider failure: "
                    f"{type(error).__name__}: {error}"
                )

                raise EmbeddingUnavailableError(
                    "Gemini embedding service remained unavailable "
                    f"after {MAX_EMBEDDING_ATTEMPTS} attempts. "
                    f"Last provider error: {error}"
                ) from error

            print(
                f"[Aegis Embedding] Attempt {attempt} failed "
                f"with a transient provider error. "
                f"Retrying in {delay} second(s)..."
            )

            time.sleep(delay)

            delay *= 2


# =========================================================
# Public embedding interface
# =========================================================

def generate_embedding(text: str) -> list[float]:
    """
    Convert text into a dense semantic embedding vector.

    The resulting vector can be compared with other
    embeddings using cosine similarity.

    Transient Gemini failures are handled through bounded
    retries before an EmbeddingUnavailableError is raised.
    """

    if not text or not text.strip():
        raise ValueError(
            "Cannot generate an embedding for empty text."
        )

    response = _embed_content_with_retry(
        model=EMBEDDING_MODEL,
        contents=text,
        config=types.EmbedContentConfig(
            output_dimensionality=EMBEDDING_DIMENSION
        ),
    )

    if not response.embeddings:
        raise RuntimeError(
            "Gemini returned no embedding."
        )

    values = response.embeddings[0].values

    if values is None:
        raise RuntimeError(
            "Gemini returned an empty embedding vector."
        )

    return list(values)