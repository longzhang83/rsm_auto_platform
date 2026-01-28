#!/bin/bash

echo "Starting FastAPI Backend Server..."

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
cd "$SCRIPT_DIR/.."

if ! command -v uv &> /dev/null; then
    echo "ERROR: uv is not installed."
    echo "Please install uv from https://docs.astral.sh/uv/"
    exit 1
fi

cd backend
echo "Installing dependencies..."
uv sync

echo "Installing core business logic..."
uv pip install -e ../

echo "Starting server on http://localhost:7777"
uv run uvicorn app.main:app  --port 7777
