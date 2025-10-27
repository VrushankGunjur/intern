#!/bin/bash

echo "Startup Idea Agent Setup"
echo "=========================="
echo ""

# Check if .env exists
if [ -f .env ]; then
    echo "[OK] .env file already exists"
else
    echo "[SETUP] Creating .env file from template..."
    cp .env.example .env
    echo "[ACTION REQUIRED] Please edit .env and add your credentials:"
    echo "   - ANTHROPIC_API_KEY"
    echo "   - GMAIL_USER"
    echo "   - GMAIL_APP_PASSWORD"
    echo ""
    read -p "Press Enter after you've edited .env..."
fi

# Create data directory
if [ -d data ]; then
    echo "[OK] data directory already exists"
else
    echo "[SETUP] Creating data directory..."
    mkdir -p data
fi

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "[ERROR] Docker is not running. Please start Docker and try again."
    exit 1
fi

echo "[OK] Docker is running"
echo ""

# Build and start
echo "[BUILD] Building Docker image..."
docker-compose build

echo ""
echo "[START] Starting agent..."
docker-compose up -d

echo ""
echo "[SUCCESS] Agent is now running"
echo ""
echo "To view logs:"
echo "  docker-compose logs -f"
echo ""
echo "To stop the agent:"
echo "  docker-compose down"
echo ""
echo "Monitor your inbox at team@heysanctum.com for startup ideas."
