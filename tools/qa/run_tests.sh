#!/bin/bash
# Run all QA tests inside the flask-app container

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
CONTAINER="flask-app"

# Copy all test files into the container
echo "Copying test files to container..."
for f in "$SCRIPT_DIR"/test_*.py; do
    docker cp "$f" "$CONTAINER":/app/
done

# Ensure pytest is installed
docker exec "$CONTAINER" pip install pytest -q 2>&1 | tail -1

# Run all tests
echo "Running tests..."
docker exec "$CONTAINER" bash -c 'python -m pytest /app/test_*.py -v'
