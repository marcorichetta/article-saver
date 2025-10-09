# https://just.systems

default:
    @echo "Run 'just --list' to see available recipes."

dev:
    uv run fastapi dev app/main.py