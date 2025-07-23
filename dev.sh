#!/bin/bash

# LTFPQRR Development Script
# Use this script for all development tasks

set -e

PROJECT_NAME="ltfpqrr"
COMPOSE_FILE="docker-compose.yml"

show_help() {
    echo "LTFPQRR Development Script"
    echo ""
    echo "Usage: ./dev.sh [command]"
    echo ""
    echo "Commands:"
    echo "  start-dev      Start development environment"
    echo "  stop           Stop all services"
    echo "  rebuild-dev    Rebuild and restart development environment"
    echo "  logs           Show logs for all services"
    echo "  logs-web       Show logs for web service"
    echo "  logs-db        Show logs for database service"
    echo "  reset-db       Reset database (WARNING: This will delete all data)"
    echo "  shell          Open shell in web container"
    echo "  db-shell       Open MySQL shell"
    echo "  migrate        Run database migrations"
    echo "  makemigrations Generate new migration"
    echo "  test           Run tests"
    echo "  status         Show container status"
    echo "  clean          Clean up containers and volumes"
    echo "  push-beta      Build and push Docker image (like beta workflow)"
    echo "  help           Show this help message"
}

start_dev() {
    echo "Starting LTFPQRR development environment..."
    docker-compose -f $COMPOSE_FILE up -d
    echo "Development environment started!"
    echo "Web application: http://localhost:8000"
}

stop_services() {
    echo "Stopping all services..."
    docker-compose -f $COMPOSE_FILE down
    echo "All services stopped!"
}

rebuild_dev() {
    echo "Rebuilding development environment..."
    docker-compose -f $COMPOSE_FILE down
    docker-compose -f $COMPOSE_FILE build --no-cache
    docker-compose -f $COMPOSE_FILE up -d
    echo "Development environment rebuilt and started!"
    echo "Web application: http://localhost:8000"
}

show_logs() {
    docker-compose -f $COMPOSE_FILE logs -f
}

show_web_logs() {
    docker-compose -f $COMPOSE_FILE logs -f web
}

show_db_logs() {
    docker-compose -f $COMPOSE_FILE logs -f db
}

reset_database() {
    echo "WARNING: This will delete all data in the database!"
    read -p "Are you sure you want to continue? (y/N) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "Resetting database..."
        docker-compose -f $COMPOSE_FILE down
        docker volume rm ${PROJECT_NAME}_mysql_data 2>/dev/null || true
        docker-compose -f $COMPOSE_FILE up -d
        echo "Database reset complete!"
    else
        echo "Database reset cancelled."
    fi
}

open_shell() {
    docker-compose -f $COMPOSE_FILE exec web /bin/bash
}

open_db_shell() {
    docker-compose -f $COMPOSE_FILE exec db mysql -u ltfpqrr_user -pltfpqrr_password ltfpqrr
}

run_migrations() {
    echo "Running database migrations..."
    docker-compose -f $COMPOSE_FILE exec web python migrate.py upgrade
}

make_migrations() {
    echo "Generating new migration..."
    if [ -z "$2" ]; then
        echo "Please provide a migration message:"
        echo "Usage: ./dev.sh makemigrations \"migration message\""
        exit 1
    fi
    docker-compose -f $COMPOSE_FILE exec web python migrate.py autogenerate --message "$2"
}

run_tests() {
    echo "Running tests..."
    docker-compose -f $COMPOSE_FILE exec web python -m pytest tests/ -v
}

show_status() {
    echo "Container status:"
    docker-compose -f $COMPOSE_FILE ps
    echo ""
    echo "Health checks:"
    docker-compose -f $COMPOSE_FILE exec web python -c "
from app import app, db
with app.app_context():
    try:
        db.session.execute('SELECT 1')
        print('✓ Database connection: OK')
    except Exception as e:
        print(f'✗ Database connection: FAILED - {e}')
"
}

clean_up() {
    echo "Cleaning up containers and volumes..."
    docker-compose -f $COMPOSE_FILE down -v
    docker system prune -f
    echo "Cleanup complete!"
}

build_beta() {
    echo "Building and pushing Docker image (like beta workflow)..."
    
    # Registry and image configuration (matching beta workflow)
    REGISTRY="harbor.vm.kumpeapps.com"
    IMAGE_NAME="kumpeapps-web/ltfpqrr-web-app"
    IMAGE_TAG="latest-beta"
    FULL_IMAGE_NAME="${REGISTRY}/${IMAGE_NAME}:${IMAGE_TAG}"
    
    echo "Building and pushing image: $FULL_IMAGE_NAME"
    echo "Platforms: linux/amd64,linux/arm/v7,linux/arm64 (matching beta workflow)"
    
    # Check if Docker is logged in to Harbor registry
    echo "Checking Harbor registry login status..."
    
    # Check if we have stored credentials for this registry
    if grep -q "$REGISTRY" ~/.docker/config.json 2>/dev/null; then
        echo "✅ Harbor registry login verified (credentials found)"
    else
        echo "⚠️  No stored credentials found for Harbor registry"
        echo "Please log in to Harbor registry:"
        echo "  docker login $REGISTRY"
        echo ""
        read -p "Would you like to log in now? (y/N) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            docker login "$REGISTRY"
            if [ $? -ne 0 ]; then
                echo "❌ Harbor registry login failed. Aborting build."
                exit 1
            fi
            echo "✅ Harbor registry login successful"
        else
            echo "❌ Cannot push to registry without login. Aborting."
            exit 1
        fi
    fi
    
    # Set up Docker Buildx if not already available
    if ! docker buildx ls | grep -q "default"; then
        echo "Setting up Docker Buildx..."
        docker buildx create --use --name multiarch-builder 2>/dev/null || true
        docker buildx use multiarch-builder 2>/dev/null || docker buildx use default
    fi
    
    # Build and push the image with multiple platforms (exactly like the beta workflow)
    echo "Building and pushing multi-platform image..."
    docker buildx build \
        --platform linux/amd64,linux/arm/v7,linux/arm64 \
        --tag "$FULL_IMAGE_NAME" \
        --build-arg BUILDKIT_INLINE_CACHE=1 \
        --cache-from type=gha \
        --cache-to type=gha,mode=max \
        --push \
        .
    
    echo "✅ Docker image built and pushed successfully: $FULL_IMAGE_NAME"
    echo ""
    echo "This image was built and pushed with the same configuration as the beta workflow:"
    echo "- Platforms: linux/amd64, linux/arm/v7, linux/arm64"
    echo "- Cache: GitHub Actions compatible"
    echo "- Build args: BUILDKIT_INLINE_CACHE=1"
    echo "- Registry: Harbor (harbor.vm.kumpeapps.com)"
    echo ""
    echo "The image is now available in the registry and can be deployed."
}

# Main command handling
case "$1" in
    start-dev)
        start_dev
        ;;
    stop)
        stop_services
        ;;
    rebuild-dev)
        rebuild_dev
        ;;
    logs)
        show_logs
        ;;
    logs-web)
        show_web_logs
        ;;
    logs-db)
        show_db_logs
        ;;
    reset-db)
        reset_database
        ;;
    shell)
        open_shell
        ;;
    db-shell)
        open_db_shell
        ;;
    migrate)
        run_migrations
        ;;
    makemigrations)
        make_migrations "$@"
        ;;
    test)
        run_tests
        ;;
    status)
        show_status
        ;;
    clean)
        clean_up
        ;;
    push-beta)
        build_beta
        ;;
    help)
        show_help
        ;;
    *)
        echo "Unknown command: $1"
        echo ""
        show_help
        exit 1
        ;;
esac
