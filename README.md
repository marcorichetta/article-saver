# Article Saver v2

Save articles from URLs for later reading via RSS feed on KOReader.

## Features

-   🔗 Submit URLs for article extraction
-   📄 Automatic content extraction and cleaning
-   🗄️ PostgreSQL storage with deduplication
-   📡 RSS feed generation for KOReader
-   🔒 Optional API key authentication

## Setup

### PostgreSQL

1. Install Docker and Docker Compose, then start PostgreSQL:

    ```bash
    just db-up
    ```

1. Set up environment:

    ```bash
    cp .env.example .env
    # Edit .env if needed
    ```

1. Install dependencies:

    ```bash
    uv sync
    ```

1. Run the app:
    ```bash
    just dev
    ```

## Usage

### Submit an article

```bash
curl -X POST http://localhost:8000/submit \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com/article"}'
```

## API Endpoints

-   `GET /` - API information
-   `GET /docs` - API Docs
-   `POST /submit` - Submit URL for processing
-   `GET /rss` - RSS feed for KOReader
-   `GET /articles` - List articles with filtering

## Development

The database tables are automatically created on first run.

## Roadmap

-   [x] Phase 1: URL processing and RSS feed
-   [ ] Phase 2: Email integration via Resend.com
-   [ ] Phase 3: Read status tracking
-   [ ] Phase 4: Advanced features (tags, categories, search)
