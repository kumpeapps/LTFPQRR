#!/bin/bash

# LTFPQRR User Management CLI Wrapper
# This script runs the user management CLI inside the Docker container

# Try to find the web container automatically
CONTAINER_NAME=$(docker ps --format "{{.Names}}" | grep -E "(ltfpqrr.*web|web.*ltfpqrr)" | head -1)

# If not found, try common container naming patterns
if [ -z "$CONTAINER_NAME" ]; then
    CONTAINER_NAME=$(docker ps --format "{{.Names}}" | grep -E "(ltfpqrr-web-1|ltfpqrr_web_1|web-1|web_1|bot-web-1)" | head -1)
fi

# If still not found, check for any container with "ltfpqrr" and port 5000
if [ -z "$CONTAINER_NAME" ]; then
    CONTAINER_NAME=$(docker ps --format "{{.Names}}" --filter "expose=5000" | grep ltfpqrr | head -1)
fi

# Check if container is running
if [ -z "$CONTAINER_NAME" ]; then
    echo "Error: LTFPQRR web container is not running."
    echo "Available containers:"
    docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | grep -E "(ltfpqrr|web)" || echo "  No LTFPQRR containers found"
    echo ""
    echo "Please start the application first with:"
    echo "  ./dev.sh start-dev  (for development)"
    echo "  docker-compose up -d  (for production)"
    exit 1
fi

echo "Using container: $CONTAINER_NAME"

# Run the CLI command inside the container
docker exec -it "$CONTAINER_NAME" python manage_users.py "$@"
