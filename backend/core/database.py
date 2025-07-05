"""
Database initialization and models
"""

from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql import func
import asyncio
import logging

from .config import settings

logger = logging.getLogger(__name__)

Base = declarative_base()

# Database Models
class DataSource(Base):
    """Track data sources and their sync status"""
    __tablename__ = "data_sources"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    source_type = Column(String)  # 'slack', 'file', 'url', etc.
    config = Column(JSON)  # Source-specific configuration
    last_sync = Column(DateTime(timezone=True))
    status = Column(String, default="active")  # active, paused, error
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class Document(Base):
    """Track processed documents"""
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    source_id = Column(String, index=True)  # ID from the source system
    source_type = Column(String, index=True)
    title = Column(String)
    content_hash = Column(String, index=True)  # Hash of content for deduplication
    vector_id = Column(String)  # ID in vector store
    metadata = Column(JSON)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class SyncLog(Base):
    """Log sync operations"""
    __tablename__ = "sync_logs"

    id = Column(Integer, primary_key=True, index=True)
    source_name = Column(String, index=True)
    operation = Column(String)  # 'sync', 'delete', 'update'
    status = Column(String)  # 'success', 'error', 'partial'
    message = Column(Text)
    documents_processed = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

# Database setup
engine = None
SessionLocal = None

async def init_db():
    """Initialize database connection and create tables"""
    global engine, SessionLocal

    try:
        # Create engine
        engine = create_engine(
            settings.database_url,
            pool_pre_ping=True,
            pool_recycle=300
        )

        # Create session factory
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

        # Create tables
        Base.metadata.create_all(bind=engine)

        logger.info("Database initialized successfully")

    except Exception as e:
        logger.error(f"Failed to initialize database: {str(e)}")
        raise

def get_db():
    """Get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()