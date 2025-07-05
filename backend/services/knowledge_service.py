"""
Knowledge Service - Handles data ingestion from multiple sources
"""

import logging
import hashlib
from typing import Dict, Any, List, Optional
from datetime import datetime
import asyncio

from core.vector_store import VectorStoreManager
from core.config import settings
from integrations.slack import SlackIntegration

logger = logging.getLogger(__name__)


class KnowledgeService:
    """Service for ingesting and managing knowledge from various sources"""

    def __init__(self, vector_store: VectorStoreManager):
        self.vector_store = vector_store
        self.integrations = {
            "slack": SlackIntegration()
        }

    async def ingest_data(self, source_type: str, data: Dict[str, Any], metadata: Optional[Dict[str, Any]] = None):
        """
        Ingest data from a specific source type

        Args:
            source_type: Type of source ('slack', 'file', 'url', etc.)
            data: Source-specific data
            metadata: Additional metadata
        """
        try:
            logger.info(f"Starting data ingestion for source type: {source_type}")

            if source_type not in self.integrations:
                raise ValueError(f"Unsupported source type: {source_type}")

            integration = self.integrations[source_type]

            # Process data through the integration
            documents = await integration.process_data(data, metadata)

            if not documents:
                logger.warning(f"No documents extracted from {source_type} data")
                return

            # Chunk documents if they're too large
            chunked_documents = self._chunk_documents(documents)

            # Add documents to vector store
            document_ids = await self.vector_store.add_documents(chunked_documents)

            logger.info(f"Successfully ingested {len(document_ids)} documents from {source_type}")

        except Exception as e:
            logger.error(f"Failed to ingest data from {source_type}: {str(e)}")
            raise

    def _chunk_documents(self, documents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Chunk large documents into smaller pieces for better retrieval
        """
        chunked_docs = []

        for doc in documents:
            content = doc.get("content", "")

            if len(content) <= settings.chunk_size:
                # Document is small enough, no chunking needed
                chunked_docs.append(doc)
            else:
                # Split into chunks
                chunks = self._split_text(content, settings.chunk_size, settings.chunk_overlap)

                for i, chunk in enumerate(chunks):
                    chunked_doc = doc.copy()
                    chunked_doc["content"] = chunk
                    chunked_doc["source_id"] = f"{doc.get('source_id', '')}_chunk_{i}"
                    chunked_doc["title"] = f"{doc.get('title', '')} (Part {i+1})"
                    chunked_doc["metadata"] = {
                        **(doc.get("metadata", {})),
                        "chunk_index": i,
                        "total_chunks": len(chunks),
                        "original_source_id": doc.get("source_id", "")
                    }
                    chunked_docs.append(chunked_doc)

        return chunked_docs

    def _split_text(self, text: str, chunk_size: int, overlap: int) -> List[str]:
        """
        Split text into overlapping chunks
        """
        if len(text) <= chunk_size:
            return [text]

        chunks = []
        start = 0

        while start < len(text):
            end = start + chunk_size

            # Try to break at sentence boundaries
            if end < len(text):
                # Look for sentence endings within the last 100 characters
                sentence_end = text.rfind('.', start, end)
                if sentence_end > start + chunk_size - 100:
                    end = sentence_end + 1
                else:
                    # Look for paragraph breaks
                    para_break = text.rfind('\n\n', start, end)
                    if para_break > start + chunk_size - 200:
                        end = para_break + 2
                    else:
                        # Look for line breaks
                        line_break = text.rfind('\n', start, end)
                        if line_break > start + chunk_size - 100:
                            end = line_break + 1

            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)

            # Move start position with overlap
            start = end - overlap
            if start >= len(text):
                break

        return chunks

    async def list_sources(self) -> Dict[str, Any]:
        """List available data sources and their status"""
        sources = {}

        for source_type, integration in self.integrations.items():
            try:
                status = await integration.get_status()
                sources[source_type] = {
                    "available": True,
                    "status": status,
                    "description": integration.get_description()
                }
            except Exception as e:
                sources[source_type] = {
                    "available": False,
                    "error": str(e),
                    "description": integration.get_description()
                }

        return sources