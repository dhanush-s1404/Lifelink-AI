"""AI foundation module for LifeLink AI.

Provides AI/ML services for document understanding, including:
- Text embedding generation (semantic search, similarity)
- Document summarization (extractive and abstractive)
- AI assistant chat interface
- Vector search functionality

These services integrate with the vault/item/document model layer
to enable AI-powered features across the application.
"""

from __future__ import annotations

from app.ai.assistant import AIAssistant, get_ai_assistant  # noqa: F401
from app.ai.embeddings import EmbeddingService, get_embedding_service
from app.ai.summarization import SummarizationService, get_summarization_service
from app.search import get_search_service as get_search_service  # noqa: F401

__all__ = [
    "EmbeddingService",
    "get_embedding_service",
    "get_search_service",
    "SummarizationService",
    "get_summarization_service",
    "AIAssistant",
    "get_ai_assistant",
]