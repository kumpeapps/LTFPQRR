#!/bin/bash

# LTFPQRR User Management CLI Wrapper
# This script runs the user management CLI inside the Docker container

CONTAINER_NAME="ltfpqrr-web-1"

# Check if container is running
if ! docker ps --format "table {{.Names}}" | grep -q "$CONTAINER_NAME"; then
    echo "Error: LTFPQRR web container is not running."
    echo "Please start the application first with: ./dev.sh start-dev"
    exit 1
fi

# Run the CLI command inside the container
docker exec -it "$CONTAINER_NAME" python manage_users.py "$@"
