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

from .config import settings

logger = logging.getLogger(__name__)


class VectorStoreManager:
    """Manages vector storage and retrieval using Weaviate"""

    def __init__(self):
        self.client = None
        self.embedding_model = None
        self.executor = ThreadPoolExecutor(max_workers=4)

    async def initialize(self):
        """Initialize Weaviate client and embedding model"""
        try:
            # Initialize Weaviate client
            if settings.weaviate_api_key:
                auth_config = weaviate.AuthApiKey(api_key=settings.weaviate_api_key)
                self.client = weaviate.Client(
                    url=settings.weaviate_url,
                    auth_client_secret=auth_config
                )
            else:
                self.client = weaviate.Client(url=settings.weaviate_url)

            # Test connection
            if not self.client.is_ready():
                raise Exception("Weaviate is not ready")

            # Initialize embedding model
            loop = asyncio.get_event_loop()
            self.embedding_model = await loop.run_in_executor(
                self.executor,
                SentenceTransformer,
                settings.embedding_model
            )

            # Create schema if it doesn't exist
            await self._create_schema()

            logger.info("Vector store initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize vector store: {str(e)}")
            raise

    async def _create_schema(self):
        """Create Weaviate schema for knowledge base"""
        schema = {
            "classes": [
                {
                    "class": "Document",
                    "description": "A document in the knowledge base",
                    "vectorizer": "none",  # We'll provide our own vectors
                    "properties": [
                        {
                            "name": "content",
                            "dataType": ["text"],
                            "description": "The content of the document"
                        },
                        {
                            "name": "source",
                            "dataType": ["string"],
                            "description": "Source of the document (slack, file, etc.)"
                        },
                        {
                            "name": "source_id",
                            "dataType": ["string"],
                            "description": "Unique identifier from the source"
                        },
                        {
                            "name": "title",
                            "dataType": ["string"],
                            "description": "Title or subject of the document"
                        },
                        {
                            "name": "author",
                            "dataType": ["string"],
                            "description": "Author of the document"
                        },
                        {
                            "name": "timestamp",
                            "dataType": ["date"],
                            "description": "When the document was created"
                        },
                        {
                            "name": "channel",
                            "dataType": ["string"],
                            "description": "Channel or category (for Slack messages)"
                        },
                        {
                            "name": "metadata",
                            "dataType": ["object"],
                            "description": "Additional metadata as JSON"
                        }
                    ]
                }
            ]
        }

        try:
            # Check if schema already exists
            existing_schema = self.client.schema.get()
            existing_classes = [cls["class"] for cls in existing_schema.get("classes", [])]

            if "Document" not in existing_classes:
                self.client.schema.create(schema)
                logger.info("Created Weaviate schema")
            else:
                logger.info("Weaviate schema already exists")

        except Exception as e:
            logger.error(f"Failed to create schema: {str(e)}")
            raise

    async def add_documents(self, documents: List[Dict[str, Any]]) -> List[str]:
        """Add documents to the vector store"""
        try:
            document_ids = []

            for doc in documents:
                # Generate embedding
                content = doc.get("content", "")
                if not content:
                    continue

                loop = asyncio.get_event_loop()
                embedding = await loop.run_in_executor(
                    self.executor,
                    self.embedding_model.encode,
                    content
                )

                # Prepare document for Weaviate
                weaviate_doc = {
                    "content": content,
                    "source": doc.get("source", "unknown"),
                    "source_id": doc.get("source_id", ""),
                    "title": doc.get("title", ""),
                    "author": doc.get("author", ""),
                    "timestamp": doc.get("timestamp"),
                    "channel": doc.get("channel", ""),
                    "metadata": doc.get("metadata", {})
                }

                # Add to Weaviate
                doc_id = self.client.data_object.create(
                    data_object=weaviate_doc,
                    class_name="Document",
                    vector=embedding.tolist()
                )

                document_ids.append(doc_id)

            logger.info(f"Added {len(document_ids)} documents to vector store")
            return document_ids

        except Exception as e:
            logger.error(f"Failed to add documents: {str(e)}")
            raise

    async def search_documents(self, query: str, limit: int = 5, source_filter: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """Search for documents using semantic similarity"""
        try:
            # Generate query embedding
            loop = asyncio.get_event_loop()
            query_embedding = await loop.run_in_executor(
                self.executor,
                self.embedding_model.encode,
                query
            )

            # Build Weaviate query
            near_vector = {"vector": query_embedding.tolist()}

            query_builder = (
                self.client.query
                .get("Document", ["content", "source", "source_id", "title", "author", "timestamp", "channel", "metadata"])
                .with_near_vector(near_vector)
                .with_limit(limit)
                .with_additional(["certainty", "distance"])
            )

            # Apply source filter if provided
            if source_filter:
                where_filter = {
                    "path": ["source"],
                    "operator": "ContainsAny",
                    "valueStringArray": source_filter
                }
                query_builder = query_builder.with_where(where_filter)

            result = query_builder.do()

            documents = []
            if "data" in result and "Get" in result["data"] and "Document" in result["data"]["Get"]:
                for doc in result["data"]["Get"]["Document"]:
                    documents.append({
                        "content": doc.get("content", ""),
                        "source": doc.get("source", ""),
                        "source_id": doc.get("source_id", ""),
                        "title": doc.get("title", ""),
                        "author": doc.get("author", ""),
                        "timestamp": doc.get("timestamp", ""),
                        "channel": doc.get("channel", ""),
                        "metadata": doc.get("metadata", {}),
                        "certainty": doc.get("_additional", {}).get("certainty", 0),
                        "distance": doc.get("_additional", {}).get("distance", 1)
                    })

            return documents

        except Exception as e:
            logger.error(f"Failed to search documents: {str(e)}")
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
            # Get document count
            result = self.client.query.aggregate("Document").with_meta_count().do()

            count = 0
            if "data" in result and "Aggregate" in result["data"] and "Document" in result["data"]["Aggregate"]:
                count = result["data"]["Aggregate"]["Document"][0]["meta"]["count"]

            return {
                "total_documents": count,
                "embedding_model": settings.embedding_model,
                "embedding_dimension": settings.embedding_dimension
            }

        except Exception as e:
            logger.error(f"Failed to get stats: {str(e)}")
            return {"error": str(e)}