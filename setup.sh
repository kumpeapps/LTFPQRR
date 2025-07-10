#!/bin/bash

echo "Setting up LTFPQRR development environment with Docker..."

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "Error: Docker is not installed. Please install Docker first."
    echo "Visit: https://docs.docker.com/get-docker/"
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo "Error: Docker Compose is not installed. Please install Docker Compose first."
    echo "Visit: https://docs.docker.com/compose/install/"
    exit 1
fi

# Stop any existing containers
echo "Stopping existing containers..."
docker-compose down

# Build the application
echo "Building Docker containers..."
docker-compose build

# Start the services
echo "Starting services..."
docker-compose up -d

# Wait for services to be ready
echo "Waiting for services to be ready..."
echo "The application will automatically initialize the database on first startup..."
sleep 15

echo "Setup complete!"
echo ""
echo "The application is now running in Docker containers:"
echo "- Web application: http://localhost:5000"
echo "- Database: MySQL on port 3306"
echo "- Redis: Redis on port 6379"
echo ""
echo "Useful commands:"
echo "- View logs: docker-compose logs -f"
echo "- Stop services: docker-compose down"
echo "- Restart services: docker-compose restart"
echo "- Access shell: docker-compose exec web bash"
