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
