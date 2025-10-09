# https://just.systems

default:
    @echo "Run 'just --list' to see available recipes."

# Start the development server
dev:
    uv run fastapi dev app/main.py

# Start PostgreSQL with Docker
db-up:
    docker compose up -d

# Stop PostgreSQL
db-down:
    docker compose down

# View PostgreSQL logs
db-logs:
    docker compose logs -f postgres

# Connect to PostgreSQL CLI
db-shell:
    docker compose exec postgres psql -U postgres -d article_saver

# Install/sync dependencies
install:
    uv sync

# Submit a test article
test-submit URL:
    curl -X POST http://localhost:8000/submit \
        -H "Content-Type: application/json" \
        -d '{"url": "{{URL}}"}'

# View RSS feed
test-rss:
    curl http://localhost:8000/rss

# List articles
test-list:
    curl http://localhost:8000/articles

# Test
test: db-up dev
    uv run python test_api.py