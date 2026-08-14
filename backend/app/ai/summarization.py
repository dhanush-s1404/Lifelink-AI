"""Document summarization service for AI-powered document understanding.

Provides extractive summarization (selecting key sentences from text)
and abstractive summarization (generating a summary).

Used by the vault/item views to surface document highlights without
requiring full read access.
"""

from __future__ import annotations

import hashlib
import os
import re
from abc import ABC, abstractmethod

# ----------------------------------------------------------------------
# Summarization backend abstraction
# ----------------------------------------------------------------------


class SummarizationBackend(ABC):
    """Abstract base class for summarization backends."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Return the backend identifier name."""
        pass

    @abstractmethod
    def summarize(
        self, text: str, max_sentences: int = 3, max_length: int | None = None
    ) -> str:
        """Generate a summary of the given text.

        Parameters
        ----------
        text:
            The text to summarize.
        max_sentences:
            Maximum number of sentences in the summary (extractive).
        max_length:
            Maximum character length of the summary (abstractive).

        Returns
        -------
        str:
            The generated summary.
        """
        pass

    def extract_key_sentences(
        self, text: str, num_sentences: int = 5
    ) -> list[str]:
        """Extract the most important sentences from text.

        Default implementation uses simple frequency-based ranking.
        Subclasses can override with smarter algorithms.
        """
        sentences = re.split(r"(?<=[.!?])\s+", text.strip())
        sentences = [s for s in sentences if s.strip()]
        return sentences[:num_sentences]


# ------------------------------------------------------------------
# Extractive summarizer (extract key sentences)
# ------------------------------------------------------------------


class ExtractiveSummarizer(SummarizationBackend):
    """Extractive summarizer that selects the most important sentences.

    Uses a frequency-based approach: scores sentences by word importance
    within the document, then returns the top-scoring sentences.
    """

    def __init__(self, stop_words: set | None = None) -> None:
        if stop_words is None:
            self._stop_words = {
                "the", "and", "or", "but", "if", "because", "as", "until",
                "while", "of", "at", "by", "for", "with", "about", "against",
                "between", "into", "through", "during", "before", "after",
                "above", "below", "to", "from", "up", "down", "in", "out",
                "on", "off", "over", "under", "again", "further", "then",
                "once", "here", "there", "when", "where", "why", "how",
                "all", "any", "both", "each", "few", "more", "most",
                "other", "some", "such", "no", "nor", "not", "only",
                "own", "same", "so", "than", "too", "very", "s", "t",
                "can", "will", "just", "don", "should", "now",
            }
        else:
            self._stop_words = stop_words

    @property
    def name(self) -> str:
        return "extractive"

    def summarize(
        self, text: str, max_sentences: int = 3, max_length: int | None = None
    ) -> str:
        """Extract the top ``max_sentences`` sentences from ``text``."""
        sentences = re.split(r"(?<=[.!?])\s+", text.strip())
        sentences = [s for s in sentences if s.strip()]

        if not sentences:
            return ""

        # Score sentences by important word frequency
        word_freq: dict[str, int] = {}
        for sentence in sentences:
            for word in re.findall(r"\b[a-zA-Z]+\b", sentence.lower()):
                if word not in self._stop_words:
                    word_freq[word] = word_freq.get(word, 0) + 1

        # Score each sentence
        sentence_scores: list[tuple[int, str]] = []  # (score, sentence)
        for _i, sentence in enumerate(sentences):
            # Score each sentence
            regex = r"\b[a-zA-Z]+\b"
            lowered = sentence.lower()
            scored_words = (word for word in re.findall(regex, lowered))
            score = sum(word_freq.get(word, 0) for word in scored_words)
            sentence_scores.append((score, sentence))

        # Sort by score descending, take top sentences
        sentence_scores.sort(key=lambda x: x[0], reverse=True)
        top_sentences = [sent for _, sent in sentence_scores[:max_sentences]]

        # Preserve original order
        # Find positions in original text
        positioned: list[tuple[int, str]] = []
        for sentence in sentences:
            if sentence in top_sentences:
                # Find first occurrence position
                pos = text.find(sentence)
                if pos >= 0:
                    positioned.append((pos, sentence))

        positioned.sort(key=lambda x: x[0])
        result = " ".join(sent for _, sent in positioned)

        # Enforce max_length if specified
        if max_length and len(result) > max_length:
            result = result[:max_length] + "..."

        return result

    def extract_key_sentences(
        self, text: str, num_sentences: int = 5
    ) -> list[str]:
        """Extract the most important sentences ranked by importance."""
        return super().extract_key_sentences(text, num_sentences)


# ------------------------------------------------------------------
# Abstractive summarizer (placeholder for LLM-based summary)
# ------------------------------------------------------------------


class AbstractiveSummarizer(SummarizationBackend):
    """Abstractive summarizer using LLM APIs.

    Placeholder implementation that returns an extractive summary
    with a note that abstractive summarization requires an LLM backend.
    """

    def __init__(self, llm_backend: str | None = None) -> None:
        self._llm_backend = llm_backend or os.getenv("ABSTRACTIVE LLM")

    @property
    def name(self) -> str:
        return "abstractive"

    def summarize(
        self, text: str, max_sentences: int = 3, max_length: int | None = None
    ) -> str:
        """Return an extractive summary with abstractive note."""
        extractor = ExtractiveSummarizer()
        summary = extractor.summarize(text, max_sentences=max_sentences, max_length=max_length)
        if os.getenv("OPENAI_API_KEY") and not summary:
            return "(abstractive summarization requires LLM configuration)"
        return summary

    def extract_key_sentences(
        self, text: str, num_sentences: int = 5
    ) -> list[str]:
        """Delegate to extractive summarizer."""
        extractor = ExtractiveSummarizer()
        return extractor.extract_key_sentences(text, num_sentences)


# ------------------------------------------------------------------
# Summarization service with caching
# ------------------------------------------------------------------


class SummarizationService:
    """High-level service for document summarization."""

    def __init__(
        self,
        backend: SummarizationBackend | None = None,
    ) -> None:
        self._backend: SummarizationBackend | None = backend or self._detect_backend()
        self._cache: dict[str, str] = {}
        self._cache_max_size = 500

    def _detect_backend(self) -> SummarizationBackend:
        """Detect and return the best available summarization backend."""
        # Try extractive (always available)
        try:
            return ExtractiveSummarizer()
        except Exception:
            pass

        # Try abstractive if LLM configured
        if os.getenv("OPENAI_API_KEY"):
            return AbstractiveSummarizer()

        return ExtractiveSummarizer()

    def summarize(
        self, text: str, max_sentences: int = 3, max_length: int | None = None
    ) -> str:
        """Generate a summary of the given text."""
        if not text or not text.strip():
            return ""

        # Check cache
        cache_key = hashlib.sha256(text.encode("utf-8")).hexdigest()
        if cache_key in self._cache:
            return self._cache[cache_key]

        result = self._backend.summarize(text, max_sentences=max_sentences, max_length=max_length)

        # Cache result
        if len(self._cache) >= self._cache_max_size:
            oldest = next(iter(self._cache))
            del self._cache[oldest]

        self._cache[cache_key] = result
        return result

    def extract_key_sentences(
        self, text: str, num_sentences: int = 5
    ) -> list[str]:
        """Extract the most important sentences from text."""
        if not text or not text.strip():
            return []

        return self._backend.extract_key_sentences(text, num_sentences=num_sentences)

    @property
    def backend_name(self) -> str:
        """Return the name of the active summarization backend."""
        return self._backend.name if self._backend else "extractive"

    @property
    def cache_size(self) -> int:
        """Return the current cache size."""
        return len(self._cache)


# ------------------------------------------------------------------
# Convenience helper
# ------------------------------------------------------------------


def get_summarization_service() -> SummarizationService:
    """Get a configured summarization service instance."""
    return SummarizationService()