"""Application configuration class"""

import os
from typing import Optional

from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class Config:
    """Application configuration class"""

    # Environment
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "dev").lower()
    # Feature flags
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"

    # For Supabase, use the connection string from Supabase dashboard
    USER = os.getenv("POSTGRES_USER")
    PASSWORD = os.getenv("POSTGRES_PASSWORD")
    HOST = os.getenv("POSTGRES_HOST")
    PORT = os.getenv("POSTGRES_PORT", "6543")
    DATABASE = os.getenv("POSTGRES_DATABASE")

    # Construct the SQLAlchemy connection string
    DATABASE_URL = f"postgresql+psycopg2://{USER}:{PASSWORD}@{HOST}:{PORT}/{DATABASE}?sslmode=require"

    # API Configuration
    ADD_ARTICLE_API_KEY: Optional[str] = os.getenv("ADD_ARTICLE_API_KEY")

    # App Settings
    APP_TITLE: str = "Article Saver API"
    APP_VERSION: str = "2.0.0"
    RSS_FEED_TITLE: str = "My Personal Article Feed"
    RSS_FEED_DESCRIPTION: str = "Articles and links saved for later reading."
    RSS_FEED_LANGUAGE: str = "en"
    RSS_FEED_LIMIT: int = 50

    # CORS Settings
    CORS_ORIGINS: list = ["*"]
    CORS_METHODS: list = ["*"]
    CORS_HEADERS: list = ["*"]

    @classmethod
    def is_development(cls) -> bool:
        """Check if running in development environment"""
        return cls.ENVIRONMENT == "dev"

    @classmethod
    def is_production(cls) -> bool:
        """Check if running in production environment"""
        return cls.ENVIRONMENT == "prod"
