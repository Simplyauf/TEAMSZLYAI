@echo off
REM Knowledge Base System - Quick Start Script for Windows

echo 🚀 Starting Knowledge Base System...

REM Check if .env exists
if not exist .env (
    echo 📝 Creating .env file from template...
    copy .env.example .env
    echo ⚠️  Please edit .env file with your configuration before continuing
    echo    Especially add your Slack tokens if you want Slack integration
    pause
)

REM Create data directories
echo 📁 Creating data directories...
mkdir data\weaviate 2>nul
mkdir data\postgres 2>nul
mkdir data\redis 2>nul
mkdir data\ollama 2>nul
mkdir data\n8n 2>nul

REM Start the system
echo 🐳 Starting Docker containers...
docker-compose up -d

REM Wait for services to be ready
echo ⏳ Waiting for services to start...
timeout /t 10 /nobreak >nul

echo.
echo 🎉 Knowledge Base System is starting up!
echo.
echo 📊 Service URLs:
echo    • Backend API: http://localhost:8000
echo    • API Documentation: http://localhost:8000/docs
echo    • n8n Workflows: http://localhost:5678 (admin/password)
echo    • Weaviate: http://localhost:8080
echo.
echo 📝 Next steps:
echo    1. Configure Slack integration in .env if needed
echo    2. Set up n8n workflows for data ingestion
echo    3. Test the API with: curl http://localhost:8000/health
echo.
echo 📖 View logs with: docker-compose logs -f
echo 🛑 Stop with: docker-compose down
echo.
pause