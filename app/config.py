import json
import os
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from firebase_admin import credentials, initialize_app, firestore

# Load environment variables
load_dotenv(dotenv_path="../.env", verbose=True)

FIREBASE_CREDENTIALS_PATH = os.environ.get(
    "FIREBASE_CREDENTIALS_PATH", Path().cwd() / "firebase-creds.json"
)


class Config:
    """Application configuration class"""

    # Environment
    ENVIRONMENT: str = os.environ.get("ENVIRONMENT", "dev").lower()

    # API Configuration
    ADD_ARTICLE_API_KEY: Optional[str] = os.environ.get("ADD_ARTICLE_API_KEY")

    # App Settings
    APP_TITLE: str = "Article Saver API"
    APP_VERSION: str = "1.0.0"
    RSS_FEED_TITLE: str = "Mi Feed de Artículos Personal (Python)"
    RSS_FEED_DESCRIPTION: str = (
        "Artículos y enlaces guardados personalmente con Python y Firebase."
    )
    RSS_FEED_LANGUAGE: str = "es-es"
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


def initialize_firebase():
    """Initialize Firebase and return Firestore client"""
    try:
        if Config.is_development():
            # En desarrollo, usar archivo JSON local para credenciales
            cred_path = FIREBASE_CREDENTIALS_PATH
            creds = credentials.Certificate(cred_path)
        else:
            # En producción, usar variable de entorno
            creds_str = os.environ.get("FIREBASE_SERVICE_ACCOUNT_KEY")
            if not creds_str:
                raise ValueError(
                    "FIREBASE_SERVICE_ACCOUNT_KEY environment variable not set"
                )
            creds_json: dict = json.loads(creds_str)
            creds = credentials.Certificate(creds_json)

        initialize_app(creds)
        db = firestore.client()
        print("Firestore client initialized successfully")
        yield db

    except Exception as e:
        print(f"Error initializing Firestore client: {e}")
        raise RuntimeError("Failed to initialize Firestore client") from e
