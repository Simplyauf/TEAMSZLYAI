#!/bin/bash

# Knowledge Base System - Quick Start Script

echo "🚀 Starting Knowledge Base System..."

# Check if .env exists
if [ ! -f .env ]; then
    echo "📝 Creating .env file from template..."
    cp .env.example .env
    echo "⚠️  Please edit .env file with your configuration before continuing"
    echo "   Especially add your Slack tokens if you want Slack integration"
    read -p "Press Enter to continue after editing .env..."
fi

# Create data directories
echo "📁 Creating data directories..."
mkdir -p data/weaviate data/postgres data/redis data/ollama data/n8n

# Start the system
echo "🐳 Starting Docker containers..."
docker-compose up -d

# Wait for services to be ready
echo "⏳ Waiting for services to start..."
sleep 10

# Check service health
echo "🔍 Checking service health..."

# Check backend
if curl -s http://localhost:8000/health > /dev/null; then
    echo "✅ Backend API is running"
else
    echo "❌ Backend API is not responding"
fi

# Check Weaviate
if curl -s http://localhost:8080/v1/meta > /dev/null; then
    echo "✅ Weaviate is running"
else
    echo "❌ Weaviate is not responding"
fi

# Check n8n
if curl -s http://localhost:5678 > /dev/null; then
    echo "✅ n8n is running"
else
    echo "❌ n8n is not responding"
fi

echo ""
echo "🎉 Knowledge Base System is starting up!"
echo ""
echo "📊 Service URLs:"
echo "   • Backend API: http://localhost:8000"
echo "   • API Documentation: http://localhost:8000/docs"
echo "   • n8n Workflows: http://localhost:5678 (admin/password)"
echo "   • Weaviate: http://localhost:8080"
echo ""
echo "📝 Next steps:"
echo "   1. Configure Slack integration in .env if needed"
echo "   2. Set up n8n workflows for data ingestion"
echo "   3. Test the API with: curl http://localhost:8000/health"
echo ""
echo "📖 View logs with: docker-compose logs -f"
echo "🛑 Stop with: docker-compose down"