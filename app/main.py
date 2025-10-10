from datetime import datetime, timezone
from typing import Optional, List
from typing_extensions import Annotated

from fastapi import FastAPI, HTTPException, Header, Request, Depends
from fastapi.concurrency import asynccontextmanager
from fastapi.responses import Response
from fastapi.middleware.cors import CORSMiddleware
from feedgen.feed import FeedGenerator
from pydantic import BaseModel, HttpUrl
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from .config import Config
from .database import get_db, init_db
from .models import Article
from .processor import ContentProcessor


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create the database and tables
    init_db()
    print("Database initialized successfully")
    yield
    # Cleanup can be added here if needed


app = FastAPI(title=Config.APP_TITLE, version=Config.APP_VERSION, lifespan=lifespan)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=Config.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=Config.CORS_METHODS,
    allow_headers=Config.CORS_HEADERS,
)


# Pydantic models
class ArticleSubmit(BaseModel):
    """Model for URL submission"""

    url: HttpUrl


class ArticleResponse(BaseModel):
    """Model for article response"""

    id: int
    title: str
    author: Optional[str]
    source_url: Optional[str]
    source_type: str
    created_at: datetime
    read_status: bool


@app.get("/")
def home():
    return Response(
        content=f"""
        <html>
            <head><title>Article Saver</title></head>
            <body>
                <h1>Article Saver API</h1>
                <p>Service is running</p>
                <p>Visit <a href="/docs">/docs</a> for API documentation.</p>
                <p>Version: {Config.APP_VERSION}</p>
            </body>
        </html>
        """,
        media_type="text/html",
    )


@app.post("/submit", response_model=ArticleResponse)
async def submit_article(
    article: ArticleSubmit,
    x_api_key: Annotated[str | None, Header()] = None,
    db: Session = Depends(get_db),
):
    """Submit a URL for article extraction and storage"""

    # API Key verification
    if x_api_key is None or x_api_key != Config.ADD_ARTICLE_API_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized")

    try:
        # Process the URL
        async with ContentProcessor() as processor:
            processed = await processor.process_url(str(article.url))

        if not processed:
            raise HTTPException(
                status_code=400,
                detail="Failed to extract content from URL. The URL may be invalid or the content may not be extractable.",
            )

        # Check for duplicate content
        existing = (
            db.query(Article)
            .filter(Article.content_hash == processed["content_hash"])
            .first()
        )

        if existing:
            return ArticleResponse(
                id=existing.id,
                title=existing.title,
                author=existing.author,
                source_url=existing.source_url,
                source_type=existing.source_type,
                created_at=existing.created_at,
                read_status=existing.read_status,
            )

        # Create new article
        new_article = Article(
            title=processed["title"],
            author=processed["author"],
            source_url=processed["source_url"],
            source_type=processed["source_type"],
            content=processed["content"],
            content_hash=processed["content_hash"],
            extra_metadata=processed["extra_metadata"],
        )

        db.add(new_article)
        db.commit()
        db.refresh(new_article)

        return ArticleResponse(
            id=new_article.id,
            title=new_article.title,
            author=new_article.author,
            source_url=new_article.source_url,
            source_type=new_article.source_type,
            created_at=new_article.created_at,
            read_status=new_article.read_status,
        )

    except IntegrityError as e:
        db.rollback()
        print(f"Database integrity error: {e}")
        raise HTTPException(status_code=409, detail="Article already exists")
    except Exception as e:
        db.rollback()
        print(f"Error processing article: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to process article: {str(e)}"
        )


@app.get("/rss")
async def rss_feed(request: Request, db: Session = Depends(get_db)):
    """Generate RSS feed from stored articles"""

    try:
        # Create feed generator
        fg = FeedGenerator()
        fg.title(Config.RSS_FEED_TITLE)
        fg.link(href=str(request.url), rel="self")
        fg.description(Config.RSS_FEED_DESCRIPTION)
        fg.language(Config.RSS_FEED_LANGUAGE)

        # Fetch recent articles
        articles = (
            db.query(Article)
            .order_by(Article.created_at.desc())
            .limit(Config.RSS_FEED_LIMIT)
            .all()
        )

        # Add each article as a feed entry
        for article in articles:
            fe = fg.add_entry()
            fe.title(article.title)

            # Use source URL if available, otherwise use article ID
            link = article.source_url or f"{str(request.base_url)}articles/{article.id}"
            fe.link(href=link, rel="alternate")
            fe.guid(link, permalink=True)

            # Set publication date
            fe.pubDate(article.created_at.replace(tzinfo=timezone.utc))

            # Add author if available
            if article.author:
                fe.author({"name": article.author})

            # Add content as HTML
            fe.content(article.content, type="html")

        # Generate RSS XML
        rss_feed_xml = fg.rss_str(pretty=True)

        return Response(
            content=rss_feed_xml,
            media_type="application/rss+xml; charset=utf-8",
            status_code=200,
        )

    except Exception as e:
        print(f"Error generating RSS feed: {e}")
        error_xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
<channel>
    <title>Error - {Config.RSS_FEED_TITLE}</title>
    <link>#</link>
    <description>Failed to generate RSS feed: {str(e)}</description>
</channel>
</rss>"""
        return Response(
            content=error_xml, media_type="application/xml", status_code=500
        )


@app.get("/articles")
async def list_articles(
    skip: int = 0,
    limit: int = 20,
    unread_only: bool = False,
    db: Session = Depends(get_db),
):
    """List articles with pagination and filtering"""

    if Config.DEBUG:
        print(Config.POSTGRES_URL)

    query = db.query(Article)

    if unread_only:
        query = query.filter(Article.read_status.is_(False))

    articles = query.order_by(Article.created_at.desc()).offset(skip).limit(limit).all()

    return {
        "articles": [
            ArticleResponse(
                id=a.id,
                title=a.title,
                author=a.author,
                source_url=a.source_url,
                source_type=a.source_type,
                created_at=a.created_at,
                read_status=a.read_status,
            )
            for a in articles
        ],
        "skip": skip,
        "limit": limit,
        "total": query.count(),
    }
