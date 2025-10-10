"""Database configuration and session management"""

from sqlalchemy import create_engine
from sqlalchemy.pool import NullPool
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv

from app.config import Config

load_dotenv()


# Create SQLAlchemy engine
# https://supabase.com/docs/guides/troubleshooting/using-sqlalchemy-with-supabase-FUqebT#deploying-to-auto-scaling-servers
engine = create_engine(Config.POSTGRES_URL, client_encoding="utf8", poolclass=NullPool)

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
