"""Content processing utilities for article extraction and cleaning"""

import hashlib
import httpx
import trafilatura
import nh3
from typing import Optional, Dict, Any
from urllib.parse import urlparse


class ContentProcessor:
    """Process and extract content from URLs"""

    def __init__(self):
        self.client = httpx.AsyncClient(
            timeout=30.0,
            follow_redirects=True,
            headers={
                "User-Agent": "Mozilla/5.0 (compatible; ArticleSaver/1.0; +https://github.com/marcorichetta/article-saver)"
            },
        )

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()

    async def fetch_url(self, url: str) -> Optional[str]:
        """Fetch content from URL"""
        try:
            response = await self.client.get(url)
            response.raise_for_status()
            return response.text
        except Exception as e:
            print(f"Error fetching URL {url}: {e}")
            return None

    def extract_content(
        self, html: str, url: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """Extract article content from HTML using trafilatura"""
        try:
            # Extract with metadata
            metadata = trafilatura.extract_metadata(html)

            # Extract main content as HTML (keeping formatting for KOReader)
            content = trafilatura.extract(
                html,
                include_comments=False,
                include_tables=True,
                include_images=True,
                output_format="html",
                url=url,
            )

            if not content:
                return None

            # Sanitize HTML to prevent XSS
            clean_content = self.sanitize_html(content)

            # Extract metadata
            title = (
                metadata.title if metadata and metadata.title else "Untitled Article"
            )
            author = metadata.author if metadata and metadata.author else None

            return {
                "title": title,
                "author": author,
                "content": clean_content,
                "metadata": {
                    "site_name": metadata.sitename if metadata else None,
                    "date": metadata.date if metadata else None,
                    "description": metadata.description if metadata else None,
                },
            }
        except Exception as e:
            print(f"Error extracting content: {e}")
            return None

    def sanitize_html(self, html: str) -> str:
        """Sanitize HTML content using nh3"""
        # Allow tags that are useful for reading on KOReader
        allowed_tags = {
            "h1",
            "h2",
            "h3",
            "h4",
            "h5",
            "h6",
            "p",
            "br",
            "hr",
            "strong",
            "b",
            "em",
            "i",
            "u",
            "ul",
            "ol",
            "li",
            "a",
            "img",
            "blockquote",
            "pre",
            "code",
            "table",
            "thead",
            "tbody",
            "tr",
            "th",
            "td",
            "div",
            "span",
        }

        allowed_attributes = {
            "a": {"href", "title"},
            "img": {"src", "alt", "title"},
        }

        return nh3.clean(
            html,
            tags=allowed_tags,
            attributes=allowed_attributes,
            link_rel="noopener noreferrer",
        )

    def calculate_content_hash(self, content: str) -> str:
        """Calculate SHA-256 hash of content for deduplication"""
        return hashlib.sha256(content.encode("utf-8")).hexdigest()

    def extract_domain(self, url: str) -> str:
        """Extract domain from URL"""
        parsed = urlparse(url)
        return parsed.netloc

    async def process_url(self, url: str) -> Optional[Dict[str, Any]]:
        """Complete processing pipeline for a URL"""
        # Fetch HTML
        html = await self.fetch_url(url)
        if not html:
            return None

        # Extract content
        extracted = self.extract_content(html, url)
        if not extracted:
            return None

        # Calculate content hash for deduplication
        content_hash = self.calculate_content_hash(extracted["content"])

        # Extract domain
        domain = self.extract_domain(url)

        return {
            "title": extracted["title"],
            "author": extracted["author"],
            "content": extracted["content"],
            "content_hash": content_hash,
            "source_url": url,
            "source_type": "url",
            "domain": domain,
            "extra_metadata": extracted["metadata"],
        }
