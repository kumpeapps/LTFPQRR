#!/bin/bash
"""
LTFPQRR Auto-Renewal Management Script for Docker

This script provides easy management commands for the Docker-based
auto-renewal system.
"""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_header() {
    echo -e "${BLUE}=== $1 ===${NC}"
}

# Check if Docker and docker-compose are available
check_requirements() {
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed or not in PATH"
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        print_error "docker-compose is not installed or not in PATH"
        exit 1
    fi
}

# Show status of all services
show_status() {
    print_header "LTFPQRR Services Status"
    docker-compose ps
    echo ""
    
    print_header "Scheduler Health"
    if docker-compose ps scheduler | grep -q "Up"; then
        print_status "Scheduler service is running"
        
        # Check if scheduler is healthy
        if docker-compose exec scheduler python3 -c "import os; exit(0 if os.path.exists('/app/logs/scheduler.pid') else 1)" 2>/dev/null; then
            print_status "Scheduler daemon is healthy"
        else
            print_warning "Scheduler daemon may not be running properly"
        fi
    else
        print_error "Scheduler service is not running"
    fi
}

# Show recent logs
show_logs() {
    local lines=${1:-50}
    print_header "Scheduler Logs (last $lines lines)"
    docker-compose logs --tail=$lines scheduler
}

# Follow logs in real-time
follow_logs() {
    print_header "Following Scheduler Logs (Ctrl+C to stop)"
    docker-compose logs -f scheduler
}

# Check renewal status
check_renewals() {
    print_header "Checking Renewal Status"
    docker-compose exec web python3 scripts/check_renewals.py
}

# Run manual renewal
run_renewals() {
    print_header "Running Manual Renewal Process"
    docker-compose exec web python3 scripts/manual_renewal.py
}

# Send test reminders
send_reminders() {
    print_header "Sending Renewal Reminders"
    docker-compose exec web python3 scripts/send_renewal_reminders.py
}

# Cleanup expired subscriptions
cleanup_expired() {
    print_header "Cleaning Up Expired Subscriptions"
    docker-compose exec web python3 scripts/cleanup_expired.py
}

# Restart scheduler service
restart_scheduler() {
    print_header "Restarting Scheduler Service"
    docker-compose restart scheduler
    sleep 3
    show_status
}

# Show help
show_help() {
    echo "LTFPQRR Auto-Renewal Management"
    echo ""
    echo "Usage: $0 [command]"
    echo ""
    echo "Commands:"
    echo "  status          Show service status and health"
    echo "  logs [lines]    Show recent scheduler logs (default: 50 lines)"
    echo "  follow          Follow scheduler logs in real-time"
    echo "  check           Check renewal system status"
    echo "  renew           Run manual renewal process"
    echo "  remind          Send renewal reminder emails"
    echo "  cleanup         Cleanup expired subscriptions"
    echo "  restart         Restart scheduler service"
    echo "  help            Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 status                # Show system status"
    echo "  $0 logs 100             # Show last 100 log lines"
    echo "  $0 follow               # Follow logs in real-time"
    echo "  $0 check                # Check renewal status"
    echo "  $0 renew                # Run renewals manually"
}

# Main script logic
main() {
    check_requirements
    
    case "${1:-help}" in
        "status")
            show_status
            ;;
        "logs")
            show_logs "${2:-50}"
            ;;
        "follow")
            follow_logs
            ;;
        "check")
            check_renewals
            ;;
        "renew")
            run_renewals
            ;;
        "remind")
            send_reminders
            ;;
        "cleanup")
            cleanup_expired
            ;;
        "restart")
            restart_scheduler
            ;;
        "help"|"--help"|"-h")
            show_help
            ;;
        *)
            print_error "Unknown command: $1"
            echo ""
            show_help
            exit 1
            ;;
    esac
}

# Run main function
main "$@"
