"""
Knowledge Base API - Main FastAPI Application
Supports multiple data sources with extensible plugin architecture
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import os
import logging
from contextlib import asynccontextmanager

from core.config import settings
from core.database import init_db
from core.vector_store import VectorStoreManager
from core.llm_manager import LLMManager
from integrations.slack import SlackIntegration
from services.knowledge_service import KnowledgeService
from services.query_service import QueryService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global managers
vector_store_manager = None
llm_manager = None
knowledge_service = None
query_service = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize services on startup"""
    global vector_store_manager, llm_manager, knowledge_service, query_service

    logger.info("Starting Knowledge Base API...")

    # Initialize database
    await init_db()

    # Initialize managers
    vector_store_manager = VectorStoreManager()
    await vector_store_manager.initialize()

    llm_manager = LLMManager()
    await llm_manager.initialize()

    # Initialize services
    knowledge_service = KnowledgeService(vector_store_manager)
    query_service = QueryService(vector_store_manager, llm_manager)

    logger.info("Knowledge Base API initialized successfully")

    yield

    # Cleanup
    logger.info("Shutting down Knowledge Base API...")

app = FastAPI(
    title="Knowledge Base API",
    description="Extensible knowledge base with multiple data source integrations",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models
class QueryRequest(BaseModel):
    question: str
    context_limit: Optional[int] = 5
    source_filter: Optional[List[str]] = None

class QueryResponse(BaseModel):
    answer: str
    sources: List[Dict[str, Any]]
    confidence: float

class IngestRequest(BaseModel):
    source_type: str  # 'slack', 'file', 'url', etc.
    data: Dict[str, Any]
    metadata: Optional[Dict[str, Any]] = None

class IngestResponse(BaseModel):
    status: str
    message: str
    document_count: int

# API Routes
@app.get("/")
async def root():
    """Health check endpoint"""
    return {"message": "Knowledge Base API is running", "version": "1.0.0"}

@app.get("/health")
async def health_check():
    """Detailed health check"""
    health_status = {
        "api": "healthy",
        "vector_store": "unknown",
        "llm": "unknown"
    }

    try:
        if vector_store_manager:
            await vector_store_manager.health_check()
            health_status["vector_store"] = "healthy"
    except Exception as e:
        health_status["vector_store"] = f"unhealthy: {str(e)}"

    try:
        if llm_manager:
            await llm_manager.health_check()
            health_status["llm"] = "healthy"
    except Exception as e:
        health_status["llm"] = f"unhealthy: {str(e)}"

    return health_status

@app.post("/query", response_model=QueryResponse)
async def query_knowledge_base(request: QueryRequest):
    """Query the knowledge base"""
    if not query_service:
        raise HTTPException(status_code=503, detail="Query service not initialized")

    try:
        result = await query_service.query(
            question=request.question,
            context_limit=request.context_limit,
            source_filter=request.source_filter
        )
        return result
    except Exception as e:
        logger.error(f"Query error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/ingest", response_model=IngestResponse)
async def ingest_data(request: IngestRequest, background_tasks: BackgroundTasks):
    """Ingest data from various sources"""
    if not knowledge_service:
        raise HTTPException(status_code=503, detail="Knowledge service not initialized")

    try:
        # Process ingestion in background
        background_tasks.add_task(
            knowledge_service.ingest_data,
            request.source_type,
            request.data,
            request.metadata
        )

        return IngestResponse(
            status="accepted",
            message=f"Data ingestion started for source type: {request.source_type}",
            document_count=0  # Will be updated when processing completes
        )
    except Exception as e:
        logger.error(f"Ingestion error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/sources")
async def list_sources():
    """List available data sources and their status"""
    if not knowledge_service:
        raise HTTPException(status_code=503, detail="Knowledge service not initialized")

    return await knowledge_service.list_sources()

@app.get("/stats")
async def get_stats():
    """Get knowledge base statistics"""
    if not vector_store_manager:
        raise HTTPException(status_code=503, detail="Vector store not initialized")

    return await vector_store_manager.get_stats()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)