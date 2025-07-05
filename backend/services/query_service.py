"""
Query Service - Handles RAG queries using vector search and LLM generation
"""

import logging
from typing import Dict, Any, List, Optional
import time

from core.vector_store import VectorStoreManager
from core.llm_manager import LLMManager

logger = logging.getLogger(__name__)


class QueryService:
    """Service for handling knowledge base queries using RAG"""

    def __init__(self, vector_store: VectorStoreManager, llm_manager: LLMManager):
        self.vector_store = vector_store
        self.llm_manager = llm_manager

    async def query(
        self,
        question: str,
        context_limit: int = 5,
        source_filter: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Process a query using RAG (Retrieval-Augmented Generation)

        Args:
            question: The user's question
            context_limit: Maximum number of context documents to retrieve
            source_filter: Optional list of sources to filter by

        Returns:
            Dictionary containing answer, sources, and confidence score
        """
        try:
            start_time = time.time()

            # Step 1: Retrieve relevant documents
            logger.info(f"Searching for documents related to: {question[:100]}...")
            documents = await self.vector_store.search_documents(
                query=question,
                limit=context_limit,
                source_filter=source_filter
            )

            if not documents:
                return {
                    "answer": "I couldn't find any relevant information in the knowledge base to answer your question.",
                    "sources": [],
                    "confidence": 0.0,
                    "query_time": time.time() - start_time
                }

            # Step 2: Calculate confidence based on document relevance
            confidence = self._calculate_confidence(documents)

            # Step 3: Generate answer using LLM with retrieved context
            logger.info(f"Generating answer using {len(documents)} context documents...")
            answer = await self.llm_manager.generate_response(
                prompt=question,
                context=documents,
                max_tokens=1000,
                temperature=0.1
            )

            # Step 4: Format sources for response
            sources = self._format_sources(documents)

            query_time = time.time() - start_time
            logger.info(f"Query completed in {query_time:.2f} seconds")

            return {
                "answer": answer,
                "sources": sources,
                "confidence": confidence,
                "query_time": query_time
            }

        except Exception as e:
            logger.error(f"Query failed: {str(e)}")
            raise

    def _calculate_confidence(self, documents: List[Dict[str, Any]]) -> float:
        """Calculate confidence score based on document relevance"""
        if not documents:
            return 0.0

        # Use the certainty scores from Weaviate
        certainties = [doc.get("certainty", 0) for doc in documents]

        # Weight by position (first results are more important)
        weighted_sum = 0
        total_weight = 0

        for i, certainty in enumerate(certainties):
            weight = 1.0 / (i + 1)  # Decreasing weight for later results
            weighted_sum += certainty * weight
            total_weight += weight

        confidence = weighted_sum / total_weight if total_weight > 0 else 0

        # Scale to 0-1 range and apply some adjustments
        confidence = min(max(confidence, 0), 1)

        # Boost confidence if we have multiple relevant documents
        if len(documents) >= 3 and confidence > 0.7:
            confidence = min(confidence * 1.1, 1.0)

        return round(confidence, 3)

    def _format_sources(self, documents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Format document sources for the response"""
        sources = []

        for doc in documents:
            source = {
                "content": doc.get("content", "")[:500] + "..." if len(doc.get("content", "")) > 500 else doc.get("content", ""),
                "source": doc.get("source", "unknown"),
                "title": doc.get("title", ""),
                "author": doc.get("author", ""),
                "timestamp": doc.get("timestamp", ""),
                "channel": doc.get("channel", ""),
                "relevance_score": doc.get("certainty", 0)
            }

            # Add source-specific formatting
            if doc.get("source") == "slack":
                source["display_name"] = f"#{doc.get('channel', 'unknown')} by {doc.get('author', 'unknown')}"
            else:
                source["display_name"] = doc.get("title", "") or f"{doc.get('source', 'unknown')} document"

            sources.append(source)

        return sources