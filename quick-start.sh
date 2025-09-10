#!/bin/bash

# WhatsApp Revenue Copilot - Quick Start Script
# This script sets up and launches the entire system with one command

set -e

echo "🚀 WhatsApp Revenue Copilot - Quick Start"
echo "========================================"

# Check prerequisites
echo "📋 Checking prerequisites..."

if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

echo "✅ Docker and Docker Compose are installed"

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "📝 Creating environment file from template..."
    cp infra/env.sample .env
    echo "⚠️  Please edit .env file with your actual API keys and configuration"
    echo "   Required: OPENAI_API_KEY, Google credentials, WhatsApp tokens"
    echo ""
    read -p "Press Enter when you've configured .env file..."
fi

# Create data directories
echo "📁 Creating data directories..."
mkdir -p data/chroma
mkdir -p data/n8n
mkdir -p data/backups

# Build and start services
echo "🏗️  Building and starting services..."
cd infra
docker-compose down 2>/dev/null || true
docker-compose up --build -d

echo "⏳ Waiting for services to start..."
sleep 30

# Check service health
echo "🏥 Checking service health..."

services=(
    "http://localhost:8001/health:Agent A"
    "http://localhost:8002/health:Agent B"  
    "http://localhost:8000/health:Intent Classifier"
    "http://localhost:8000/api/v1/heartbeat:Chroma"
)

all_healthy=true

for service in "${services[@]}"; do
    IFS=':' read -ra ADDR <<< "$service"
    url="${ADDR[0]}"
    name="${ADDR[1]}"
    
    if curl -f "$url" > /dev/null 2>&1; then
        echo "✅ $name is healthy"
    else
        echo "❌ $name is not responding"
        all_healthy=false
    fi
done

if [ "$all_healthy" = true ]; then
    echo ""
    echo "🎉 All services are running successfully!"
    echo ""
    echo "📱 Service URLs:"
    echo "   • n8n Dashboard: http://localhost:5678 (admin/admin123)"
    echo "   • Agent A API: http://localhost:8001"
    echo "   • Agent B API: http://localhost:8002"
    echo "   • Chroma Database: http://localhost:8000"
    echo "   • Intent Classifier: http://localhost:8000"
    echo ""
    echo "📚 Next Steps:"
    echo "   1. Open n8n at http://localhost:5678"
    echo "   2. Import workflows from n8n/workflows/"
    echo "   3. Configure WhatsApp webhook URL"
    echo "   4. Test with the demo script in docs/demo-script.md"
    echo ""
    echo "🧪 Run tests: python test_runner.py"
    echo "📖 Full documentation: README.md"
    echo ""
    echo "✨ Your WhatsApp Revenue Copilot is ready!"
else
    echo ""
    echo "⚠️  Some services are not healthy. Check the logs:"
    echo "   docker-compose logs -f"
    echo ""
    echo "🔧 Troubleshooting:"
    echo "   • Verify .env configuration"
    echo "   • Check Docker resource limits"
    echo "   • Ensure ports 5678, 8000, 8001, 8002 are available"
fi

cd ..
