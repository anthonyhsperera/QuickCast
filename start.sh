#!/bin/bash
set -e

# Use Railway's PORT or default to 8080
PORT=${PORT:-8080}

echo "Starting Gunicorn on port $PORT"

exec gunicorn --chdir backend --bind 0.0.0.0:$PORT --timeout 120 --workers 1 app:app
