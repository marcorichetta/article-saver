"""Database models for articles"""

from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, Index
from sqlalchemy.dialects.postgresql import JSONB
from .database import Base


class Article(Base):
    """Article model for storing processed articles"""

    __tablename__ = "articles"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(500), nullable=False)
    author = Column(String(200), nullable=True)
    source_url = Column(Text, nullable=True)
    source_type = Column(String(20), nullable=False, default="url")  # 'url' or 'email'
    content = Column(Text, nullable=False)  # Cleaned HTML content
    content_hash = Column(String(64), unique=True, index=True)  # For deduplication
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    read_status = Column(Boolean, default=False)
    extra_metadata = Column(JSONB, nullable=True)  # Flexible additional data

    # Create indexes
    __table_args__ = (
        Index("idx_created_at", "created_at"),
        Index("idx_read_status", "read_status"),
        Index("idx_source_type", "source_type"),
    )

    def __repr__(self):
        return f"<Article(id={self.id}, title='{self.title}', source_type='{self.source_type}')>"


class Source(Base):
    """Source model for tracking domains and processing rules"""

    __tablename__ = "sources"

    id = Column(Integer, primary_key=True, index=True)
    domain = Column(String(255), unique=True, index=True)
    source_type = Column(String(20), nullable=False)  # 'url' or 'email'
    processing_rules = Column(JSONB, nullable=True)  # Custom extraction rules
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        return f"<Source(id={self.id}, domain='{self.domain}', source_type='{self.source_type}')>"
