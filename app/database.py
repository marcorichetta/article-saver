"""Database configuration and session management"""

from sqlalchemy import create_engine
from sqlalchemy.pool import NullPool
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv

from app.config import Config

load_dotenv()


# Create SQLAlchemy engine
# https://supabase.com/docs/guides/troubleshooting/using-sqlalchemy-with-supabase-FUqebT#deploying-to-auto-scaling-servers

# Handle deprecated postgres:// URL scheme
# https://github.com/sqlalchemy/sqlalchemy/issues/6083#issuecomment-801478013

# Create the SQLAlchemy engine
# If using Transaction Pooler or Session Pooler, we want to ensure we disable SQLAlchemy client side pooling -
# https://docs.sqlalchemy.org/en/20/core/pooling.html#switching-pool-implementations
engine = create_engine(Config.DATABASE_URL, poolclass=NullPool)


# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()


def get_db():
    """Dependency for FastAPI endpoints to get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Initialize database tables"""
    Base.metadata.create_all(bind=engine)
