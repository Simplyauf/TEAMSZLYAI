"""
Vector Store Manager using Weaviate
Handles document storage, retrieval, and semantic search
"""

import weaviate
from typing import List, Dict, Any, Optional
import logging
from sentence_transformers import SentenceTransformer
import asyncio
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

from .config import settings

logger = logging.getLogger(__name__)


class VectorStoreManager:
    """Manages vector storage and retrieval using Weaviate"""

    def __init__(self):
        self.client = None
        self.embedding_model = SentenceTransformer(settings.embedding_model)
        self.executor = ThreadPoolExecutor(max_workers=4)

    async def initialize(self):
        """Initialize Weaviate client"""
        try:
            if settings.weaviate_api_key:
                auth_config = weaviate.AuthApiKey(api_key=settings.weaviate_api_key)
                self.client = weaviate.Client(
                    url=settings.weaviate_url,
                    auth_client_secret=auth_config
                )
            else:
                self.client = weaviate.Client(url=settings.weaviate_url)

            if not self.client.is_ready():
                raise Exception("Weaviate is not ready")

            await self._create_schema()

            logger.info("Vector store initialized successfully")

        except Exception:
            logger.exception("Failed to initialize vector store")
            raise

    async def _create_schema(self):
        """Create Weaviate schema for knowledge base"""
        schema = {
            "classes": [
                {
                    "class": "Document",
                    "description": "A document in the knowledge base",
                    "vectorizer": "none",
                    "properties": [
                        {"name": "content", "dataType": ["text"], "description": "Content"},
                        {"name": "source", "dataType": ["string"], "description": "Source"},
                        {"name": "source_id", "dataType": ["string"], "description": "Source ID"},
                        {"name": "title", "dataType": ["string"], "description": "Title"},
                        {"name": "author", "dataType": ["string"], "description": "Author"},
                        {"name": "timestamp", "dataType": ["date"], "description": "Timestamp"},
                        {"name": "channel", "dataType": ["string"], "description": "Channel"},
                        {
                            "name": "metadata",
                            "dataType": ["text"],  # Fixed: was "object"
                            "description": "Serialized JSON metadata"
                        }
                    ]
                }
            ]
        }

        try:
            existing_schema = self.client.schema.get()
            existing_classes = [cls["class"] for cls in existing_schema.get("classes", [])]

            if "Document" not in existing_classes:
                self.client.schema.create(schema)
                logger.info("Created Weaviate schema")
            else:
                logger.info("Weaviate schema already exists")

        except Exception:
            logger.exception("Failed to create schema")
            raise

    async def add_documents(self, documents: List[Dict[str, Any]]) -> List[str]:
        """Add documents to the vector store"""
        try:
            document_ids = []

            for doc in documents:
                content = doc.get("content", "")
                if not content:
                    continue

                embedding = await asyncio.to_thread(self.embedding_model.encode, content)

                timestamp = doc.get("timestamp")
                if isinstance(timestamp, datetime):
                    timestamp = timestamp.isoformat()

                metadata = doc.get("metadata", {})
                if isinstance(metadata, dict):
                    import json
                    metadata = json.dumps(metadata)

                weaviate_doc = {
                    "content": content,
                    "source": doc.get("source", "unknown"),
                    "source_id": doc.get("source_id", ""),
                    "title": doc.get("title", ""),
                    "author": doc.get("author", ""),
                    "timestamp": timestamp,
                    "channel": doc.get("channel", ""),
                    "metadata": metadata
                }

                doc_id = self.client.data_object.create(
                    data_object=weaviate_doc,
                    class_name="Document",
                    vector=embedding.tolist()
                )

                document_ids.append(doc_id)

            logger.info(f"Added {len(document_ids)} documents to vector store")
            return document_ids

        except Exception:
            logger.exception("Failed to add documents")
            raise

    async def search_documents(self, query: str, limit: int = 5, source_filter: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """Search for documents using semantic similarity"""
        try:
            query_embedding = await asyncio.to_thread(self.embedding_model.encode, query)

            near_vector = {"vector": query_embedding.tolist()}

            query_builder = (
                self.client.query
                .get("Document", ["content", "source", "source_id", "title", "author", "timestamp", "channel", "metadata"])
                .with_near_vector(near_vector)
                .with_limit(limit)
                .with_additional(["certainty", "distance"])
            )

            if source_filter:
                query_builder = query_builder.with_where({
                    "path": ["source"],
                    "operator": "ContainsAny",
                    "valueStringArray": source_filter
                })

            result = query_builder.do()

            documents = []
            if result.get("data", {}).get("Get", {}).get("Document"):
                for doc in result["data"]["Get"]["Document"]:
                    documents.append({
                        "content": doc.get("content", ""),
                        "source": doc.get("source", ""),
                        "source_id": doc.get("source_id", ""),
                        "title": doc.get("title", ""),
                        "author": doc.get("author", ""),
                        "timestamp": doc.get("timestamp", ""),
                        "channel": doc.get("channel", ""),
                        "metadata": doc.get("metadata", ""),
                        "certainty": doc.get("_additional", {}).get("certainty", 0),
                        "distance": doc.get("_additional", {}).get("distance", 1)
                    })

            return documents

        except Exception:
            logger.exception("Failed to search documents")
            raise

    async def health_check(self) -> bool:
        """Check if vector store is healthy"""
        try:
            return self.client.is_ready() if self.client else False
        except Exception:
            return False

    async def get_stats(self) -> Dict[str, Any]:
        """Get vector store statistics"""
        try:
            result = self.client.query.aggregate("Document").with_meta_count().do()

            count = result.get("data", {}).get("Aggregate", {}).get("Document", [{}])[0].get("meta", {}).get("count", 0)

            return {
                "total_documents": count,
                "embedding_model": settings.embedding_model,
                "embedding_dimension": settings.embedding_dimension
            }

        except Exception:
            logger.exception("Failed to get stats")
            return {"error": "Failed to fetch stats"}
