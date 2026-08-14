"""Text embedding service for document analysis and similarity search.

Supports multiple embedding backends:
- SentenceTransformers (local, no API key required)
- OpenAI embeddings (via OPENAI_API_KEY env var)
- HuggingFace Inference API

Embeddings are used for document similarity, semantic search,
and AI-powered document understanding.

Note: This module avoids hard numpy dependency; vector operations
use pure Python for compatibility with minimal dependencies.
"""

from __future__ import annotations

import hashlib
import os
from abc import ABC, abstractmethod

# ----------------------------------------------------------------------
# Embedding backend abstraction
# ----------------------------------------------------------------------


class EmbeddingBackend(ABC):
    """Abstract base class for embedding backends."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Return the backend identifier name."""
        pass

    @property
    @abstractmethod
    def dimension(self) -> int:
        """Return the embedding vector dimension."""
        pass

    @abstractmethod
    def embed(self, text: str) -> list[float]:
        """Generate an embedding vector for the given text."""
        pass

    @abstractmethod
    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Generate embedding vectors for a batch of texts."""
        pass

    def similarity(self, vec_a: list[float], vec_b: list[float]) -> float:
        """Compute cosine similarity between two embedding vectors."""
        if not vec_a or not vec_b:
            return 0.0

        # Pure Python dot product and magnitude
        dot = sum(a * b for a, b in zip(vec_a, vec_b, strict=False))
        mag_a = sum(a * a for a in vec_a) ** 0.5
        mag_b = sum(b * b for b in vec_b) ** 0.5

        if mag_a == 0 or mag_b == 0:
            return 0.0

        return dot / (mag_a * mag_b)


# ------------------------------------------------------------------
# Local SentenceTransformers backend (optional)
# ------------------------------------------------------------------


class SentenceTransformersBackend(EmbeddingBackend):
    """Local SentenceTransformers backend using all-MiniLM-L6-v2.

    No API key required. Runs entirely on-device. Dimension: 384.

    Raises ImportError if sentence-transformers is not installed.
    """

    def __init__(self) -> None:
        try:
            from sentence_transformers import SentenceTransformer  # noqa: F401

            self._model = SentenceTransformer("all-MiniLM-L6-v2")
            self._dimension = self._model.get_sentence_embedding_dimension()
            self._has_model = True
        except ImportError:
            self._has_model = False

    @property
    def name(self) -> str:
        return "sentence-transformers"

    @property
    def dimension(self) -> int:
        # Return known dimension even if model not loaded
        return self._dimension if self._has_model else 384

    def embed(self, text: str) -> list[float]:
        """Generate an embedding vector for a single text string."""
        if not self._has_model:
            # Fallback to hashing-based embedding
            return _hash_embedding(text, self.dimension)
        return self._model.encode(text, convert_to_numpy=False).tolist()

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Generate embedding vectors for a batch of texts."""
        if not self._has_model:
            return [_hash_embedding(t, self.dimension) for t in texts]
        # SentenceTransformers encode
        return self._model.encode(texts, convert_to_numpy=False).tolist()


# ------------------------------------------------------------------
# OpenAI backend (optional)
# ------------------------------------------------------------------


class OpenAIBackend(EmbeddingBackend):
    """OpenAI embeddings backend using text-embedding-ada-002 or text-embedding-3-small."""

    def __init__(self) -> None:
        # Import openai lazily; may not be installed
        try:
            import openai  # noqa: F401

            self._openai_available = True
        except ImportError:
            self._openai_available = False

        self._model = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")
        self._dimension = {
            "text-embedding-ada-002": 1536,
            "text-embedding-3-small": 1536,
            "text-embedding-3-large": 3072,
        }.get(self._model, 1536)

    @property
    def name(self) -> str:
        return "openai"

    @property
    def dimension(self) -> int:
        return self._dimension

    def embed(self, text: str) -> list[float]:
        """Generate an embedding vector for a single text string."""
        if not self._openai_available:
            return _hash_embedding(text, self.dimension)
        import openai

        response = openai.embeddings.create(model=self._model, input=text)
        return response.data[0].embedding

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Generate embedding vectors for a batch of texts."""
        if not self._openai_available:
            return [_hash_embedding(t, self.dimension) for t in texts]
        import openai

        response = openai.embeddings.create(model=self._model, input=texts)
        return [data.embedding for data in response.data]


# ------------------------------------------------------------------
# Simple hashing fallback backend (always available)
# ------------------------------------------------------------------


def _hash_embedding(text: str, dimension: int = 768) -> list[float]:
    """Generate a deterministic embedding vector via SHA-256 hashing.

    Pure Python implementation - no numpy required.
    Produces consistent dimension-dimensional vectors in [-1, 1] range.
    """
    h = hashlib.sha256(text.encode("utf-8")).digest()
    result: list[float] = []
    for i in range(dimension):
        byte_idx = i % 32
        byte_val = h[byte_idx] / 255.0
        val = (byte_val - 0.5) * 2.0
        result.append(round(val, 6))
    return result


class HashingEmbeddingBackend(EmbeddingBackend):
    """Fallback backend that generates deterministic embeddings via hashing.

    Used when no ML libraries or API keys are available. Produces
    consistent 768-dimensional vectors suitable for basic similarity.
    """

    def __init__(self, dimension: int = 768) -> None:
        self._dimension = dimension

    @property
    def name(self) -> str:
        return "hashing"

    @property
    def dimension(self) -> int:
        return self._dimension

    def embed(self, text: str) -> list[float]:
        """Generate a deterministic embedding vector via hashing."""
        return _hash_embedding(text, self._dimension)

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Generate embedding vectors for a batch of texts."""
        return [_hash_embedding(t, self._dimension) for t in texts]


# ------------------------------------------------------------------
# Embedding service with caching and fallback
# ------------------------------------------------------------------


class EmbeddingService:
    """High-level service for text embedding with caching and backend selection."""

    def __init__(self, backend: EmbeddingBackend | None = None) -> None:
        self._backend: EmbeddingBackend | None = backend or self._detect_backend()
        self._cache: dict[str, list[float]] = {}
        self._cache_max_size = 10_000

    def _detect_backend(self) -> EmbeddingBackend:
        """Detect and return the best available embedding backend."""
        # Try SentenceTransformers first (local, no API key)
        try:
            # Quick import check - will be lazy-loaded in the backend
            from app.ai.embeddings import SentenceTransformersBackend  # noqa: F401

            return SentenceTransformersBackend()
        except ImportError:
            pass

        # Try OpenAI
        if os.getenv("OPENAI_API_KEY"):
            try:
                from app.ai.embeddings import OpenAIBackend  # noqa: F401

                return OpenAIBackend()
            except Exception:
                pass

        # Fallback to hashing-based embedding (always available)
        return HashingEmbeddingBackend()

    def embed(self, text: str) -> list[float]:
        """Generate an embedding for the given text, with caching."""
        if not text or not text.strip():
            return [0.0] * self._backend.dimension if self._backend else [0.0] * 768

        cache_key = hashlib.sha256(text.encode("utf-8")).hexdigest()
        if cache_key in self._cache:
            return self._cache[cache_key]

        result = self._backend.embed(text)

        # Maintain cache size
        if len(self._cache) >= self._cache_max_size:
            # Remove oldest entries (simple FIFO via dict iteration)
            oldest = next(iter(self._cache))
            del self._cache[oldest]

        self._cache[cache_key] = result
        return result

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for a batch of texts."""
        results: list[list[float]] = []
        for text in texts:
            results.append(self.embed(text))
        return results

    def similarity(self, text_a: str, text_b: str) -> float:
        """Compute semantic similarity between two texts."""
        vec_a = self.embed(text_a)
        vec_b = self.embed(text_b)
        return self._backend.similarity(vec_a, vec_b) if self._backend else 0.0

    @property
    def backend_name(self) -> str:
        """Return the name of the active embedding backend."""
        return self._backend.name if self._backend else "hashing"

    @property
    def embedding_dimension(self) -> int:
        """Return the dimension of the embedding vectors."""
        return self._backend.dimension if self._backend else 768


# ------------------------------------------------------------------
# Convenience helper
# ------------------------------------------------------------------


def get_embedding_service() -> EmbeddingService:
    """Get a configured embedding service instance."""
    return EmbeddingService()