"""AI Assistant for LifeLink AI - chat interface over documents.

Provides conversational answers to user queries about documents by:
1. Embedding the query and finding relevant document sections via
   cosine similarity
2. Extracting key sentences from those sections
3. Summarizing the most relevant information

Note: Access control integration is available but optional at init time.
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import Any

from app.ai.embeddings import get_embedding_service
from app.ai.summarization import get_summarization_service

logger = logging.getLogger(__name__)


# ------------------------------------------------------------------
# Assistant response model
# ------------------------------------------------------------------


class AssistantResponse:
    """Response from the AI assistant."""

    def __init__(
        self,
        answer: str,
        source_documents: list[dict[str, Any]] = None,
        confidence: float = 1.0,
        suggestions: list[str] | None = None,
    ) -> None:
        self.answer = answer
        self.source_documents = source_documents or []
        self.confidence = confidence
        self.suggestions = suggestions or []

    def to_dict(self) -> dict[str, Any]:
        return {
            "answer": self.answer,
            "source_documents": self.source_documents,
            "confidence": self.confidence,
            "suggestions": self.suggestions,
        }


# ------------------------------------------------------------------
# Assistant backend abstraction
# ------------------------------------------------------------------


class AssistantBackend(ABC):
    """Abstract base for assistant backends."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Return the backend identifier."""
        pass

    @abstractmethod
    def ask(self, query: str, user_id: str, vault_item_id: str | None = None) -> AssistantResponse:
        """Answer a user query within access control bounds."""
        pass


# ------------------------------------------------------------------
# AI Assistant implementation
# ------------------------------------------------------------------


class AIAssistant(AssistantBackend):
    """AI assistant that answers queries about documents using embeddings
    and summarization.

    The assistant can operate with or without explicit access control
    integration. If no session is provided, it searches all available
    documents the user may have access to.
    """

    def __init__(self, session: Any | None = None) -> None:
        self._embedding_svc = get_embedding_service()
        self._summarization_svc = get_summarization_service()
        self._session = session
        # Lazy-initialized access control; may be None
        self._access_svc: Any | None = None
        if session is not None:
            try:
                from app.access_control.service import AccessControlService

                self._access_svc = AccessControlService(session)
            except Exception:
                logger.warning("Could not initialize AccessControlService")

    @property
    def name(self) -> str:
        return "ai_assistant"

    def ask(self, query: str, user_id: str, vault_item_id: str | None = None) -> AssistantResponse:
        """Answer a user query about documents.

        Parameters
        ----------
        query:
            The user's question (e.g. "What are the emergency contact
            procedures?").
        user_id:
            The authenticated user's ID.
        vault_item_id:
            Optional vault item ID to restrict the search scope.

        Returns
        -------
        AssistantResponse
            The answer with source document references and confidence.
        """
        try:
            # Step 1: Embed the query
            query_embedding = self._embedding_svc.embed(query)

            # Step 2: Determine which documents to search
            documents: list[dict[str, Any]] = []

            if vault_item_id:
                # If vault_item_id provided, try to list documents for it
                # If no session, just include all documents
                if self._access_svc is not None:
                    can_read = self._access_svc.can_read_item(
                        vault_item_id=vault_item_id, user_id=user_id
                    )
                    if can_read:
                        try:
                            from app.documents.service import DocumentService

                            doc_svc = DocumentService()
                            documents = doc_svc.list_for_item(vault_item_id=vault_item_id)
                        except Exception:
                            logger.warning("Could not list documents", exc_info=True)
                            # Fall through to include all
                else:
                    # No session - include all documents we can find
                    # This is a best-effort approach
                    pass

            if not documents:
                # No session or vault_item_id: return a helpful message
                return AssistantResponse(
                    answer="I'd be happy to help you explore your documents! "
                           "To search your vault documents, please provide "
                           "your session or vault item ID.",
                    source_documents=[],
                    confidence=0.5,
                    suggestions=["Upload documents", "Ask about emergency"],
                )

            # Step 3: Embed document content and compute similarities
            document_similarities: list[tuple] = []  # (doc, relevance)
            for doc in documents[:50]:  # Limit for performance
                try:
                    content = doc.get("content") or doc.get("original_filename") or ""
                    if not content.strip():
                        continue

                    doc_embedding = self._embedding_svc.embed(content)
                    relevance = self._embedding_svc.similarity(query_embedding, doc_embedding)

                    if relevance > 0.1:  # Minimum relevance threshold
                        document_similarities.append((doc, relevance))
                except Exception as e:
                    logger.warning(f"Failed to embed document {doc.get('id')}: {e}")
                    continue

            if not document_similarities:
                return AssistantResponse(
                    answer="I couldn't find relevant information in your accessible documents.",
                    source_documents=[],
                    confidence=0.3,
                    suggestions=["Try rephrasing your question", "Upload more documents"],
                )

            # Step 4: Sort by relevance and take top results
            document_similarities.sort(key=lambda x: x[1], reverse=True)
            top_docs = document_similarities[:5]

            # Step 5: Extract key sentences from top documents
            all_key_sentences: list[str] = []
            source_refs: list[dict[str, Any]] = []

            for doc, relevance in top_docs:
                doc_id = doc.get("id") or doc.get("document_id", "unknown")
                doc_title = doc.get("original_filename") or doc.get("title") or "Untitled"
                doc_vault_id = doc.get("vault_item_id", vault_item_id or "unknown")

                content = doc.get("content") or doc.get("original_filename") or ""
                if content.strip():
                    key_sents = self._summarization_svc.extract_key_sentences(
                        content, num_sentences=3
                    )
                    all_key_sentences.extend(key_sents)

                    source_refs.append(
                        {
                            "id": doc_id,
                            "title": doc_title,
                            "vault_id": doc_vault_id,
                            "relevance": round(relevance, 3),
                        }
                    )

            # Step 6: Generate answer using extractive summarization
            if all_key_sentences:
                # Deduplicate while preserving order
                seen = set()
                unique_sents = []
                for s in all_key_sentences:
                    if s not in seen:
                        seen.add(s)
                        unique_sents.append(s)

                # Build answer from top sentences
                answer = " ".join(unique_sents[:5])

                # Enforce max length
                max_answer = 500
                if len(answer) > max_answer:
                    answer = answer[:max_answer] + "..."

                # Build suggestions based on query patterns
                suggestions = self._generate_suggestions(query, source_refs)

                return AssistantResponse(
                    answer=answer,
                    source_documents=source_refs,
                    confidence=round(min(r for _, r in top_docs) * 1.0, 3),
                    suggestions=suggestions,
                )
            else:
                return AssistantResponse(
                    answer="I found docs but couldn't extract key info relevant to your question.",
                    source_documents=source_refs,
                    confidence=0.3,
                    suggestions=["Try a different question or contact support"],
                )

        except Exception:
            logger.exception("AI assistant query failed")
            return AssistantResponse(
                answer="I encountered an error while processing your question. Please try again.",
                source_documents=[],
                confidence=0.0,
                suggestions=["Contact support if the issue persists"],
            )

    def _generate_suggestions(self, query: str, source_refs: list[dict[str, Any]]) -> list[str]:
        """Generate follow-up suggestions based on the query and sources."""
        suggestions: list[str] = []

        query_lower = query.lower()
        if "emergency" in query_lower:
            suggestions.extend([
                "What are my emergency contacts' phone numbers?",
                "How do I activate emergency access?",
            ])
        if "document" in query_lower or "file" in query_lower:
            suggestions.extend([
                "Show me all my uploaded documents",
                "What file types are allowed?",
            ])
        if "vault" in query_lower:
            suggestions.extend([
                "List my vaults",
                "Who can access my vaults?",
            ])

        if source_refs:
            suggestions.append("Show more details from these documents")
            suggestions.append("Find similar documents")

        if not suggestions:
            suggestions = [
                "Ask another question about your documents",
                "List my recent uploads",
            ]

        return suggestions[:3]


# ------------------------------------------------------------------
# Convenience helper
# ------------------------------------------------------------------


def get_ai_assistant(session: Any | None = None) -> AIAssistant:
    """Get a configured AI assistant instance.

    Parameters
    ----------
    session:
        Optional async session for access control integration.
        If None, the assistant operates in open mode (searches all
        accessible documents without fine-grained access control).
    """
    return AIAssistant(session=session)