# Knowledge Base System

A comprehensive knowledge base system that ingests data from multiple sources (starting with Slack) and provides intelligent query capabilities using open-source LLMs and vector search.

## 🏗️ Architecture

- **Backend**: FastAPI + Python
- **Vector Database**: Weaviate with open-source embeddings
- **LLM**: LLaMA via Ollama (fully open-source)
- **Data Ingestion**: n8n for workflow automation
- **Database**: PostgreSQL for metadata
- **Caching**: Redis
- **Containerization**: Docker Compose

## 🚀 Features

- **Multi-source Data Ingestion**: Extensible plugin architecture for different data sources
- **Slack Integration**: Ingest messages, conversations, and channel data
- **Semantic Search**: Vector-based similarity search using sentence transformers
- **RAG (Retrieval-Augmented Generation)**: Context-aware responses using LLaMA
- **Real-time Processing**: Background job processing with Redis
- **API-First**: RESTful API for all operations
- **Extensible**: Plugin-based architecture for future integrations

## 📋 Prerequisites

- Docker and Docker Compose
- At least 8GB RAM (for LLaMA model)
- 10GB free disk space

## 🛠️ Quick Start

### 1. Clone and Setup

```bash
git clone <your-repo>
cd teamszlyai
```

### 2. Environment Configuration

Create a `.env` file:

```bash
# API Configuration
DEBUG=false

# Database
POSTGRES_HOST=postgres
POSTGRES_PORT=5432
POSTGRES_DB=knowledge_base
POSTGRES_USER=kb_user
POSTGRES_PASSWORD=kb_password

# Vector Store
WEAVIATE_URL=http://weaviate:8080

# LLM Configuration
OLLAMA_URL=http://ollama:11434
OLLAMA_MODEL=llama3

# Embedding Configuration
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
EMBEDDING_DIMENSION=384

# Redis
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_DB=0

# Slack Integration (Optional)
SLACK_BOT_TOKEN=xoxb-your-bot-token
SLACK_APP_TOKEN=xapp-your-app-token
SLACK_SIGNING_SECRET=your-signing-secret

# Processing
CHUNK_SIZE=1000
CHUNK_OVERLAP=200
MAX_CONTEXT_LENGTH=4000

# Security
SECRET_KEY=your-secret-key-change-in-production
```

### 3. Start the System

```bash
# Start all services
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f backend
```

### 4. Initialize LLaMA Model

The system will automatically pull the LLaMA model on first startup. This may take several minutes.

```bash
# Monitor Ollama logs
docker-compose logs -f ollama
```

## 📡 API Usage

### Health Check

```bash
curl http://localhost:8000/health
```

### Query the Knowledge Base

```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What was discussed about the project timeline?",
    "context_limit": 5
  }'
```

### Ingest Slack Data

```bash
curl -X POST http://localhost:8000/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "source_type": "slack",
    "data": {
      "channel_id": "C1234567890",
      "limit": 100
    }
  }'
```

## 🔧 Configuration

### Slack Setup

1. Create a Slack App at https://api.slack.com/apps
2. Add Bot Token Scopes:
   - `channels:history`
   - `channels:read`
   - `users:read`
   - `chat:write`
3. Install the app to your workspace
4. Copy the Bot User OAuth Token to `SLACK_BOT_TOKEN`

### n8n Workflows

Access n8n at http://localhost:5678 (admin/password)

Create workflows to:

- Fetch Slack messages periodically
- Send data to the backend API
- Handle webhooks from external sources

## 🏗️ Development

### Project Structure

```
teamszlyai/
├── backend/
│   ├── core/                 # Core functionality
│   │   ├── config.py        # Configuration management
│   │   ├── database.py      # Database models and setup
│   │   ├── vector_store.py  # Weaviate integration
│   │   └── llm_manager.py   # LLaMA/Ollama integration
│   ├── services/            # Business logic
│   │   ├── knowledge_service.py  # Data ingestion
│   │   └── query_service.py      # RAG queries
│   ├── integrations/        # Data source integrations
│   │   └── slack.py         # Slack integration
│   ├── main.py             # FastAPI application
│   ├── requirements.txt    # Python dependencies
│   └── Dockerfile         # Backend container
├── database/
│   └── init.sql           # Database initialization
├── n8n/                   # n8n workflows
├── data/                  # Persistent data
├── docker-compose.yml     # Container orchestration
└── README.md
```

### Adding New Data Sources

1. Create a new integration in `backend/integrations/`
2. Implement the required methods:
   - `process_data()`: Convert source data to documents
   - `get_status()`: Return integration status
   - `get_description()`: Return integration description
3. Register the integration in `knowledge_service.py`

Example integration structure:

```python
class MyIntegration:
    async def process_data(self, data: Dict[str, Any], metadata: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        # Convert your data to document format
        documents = []
        # ... processing logic
        return documents

    async def get_status(self) -> Dict[str, Any]:
        return {"configured": True, "connected": True}

    def get_description(self) -> str:
        return "Description of your integration"
```

### Running Tests

```bash
# Run backend tests
docker-compose exec backend python -m pytest

# Run with coverage
docker-compose exec backend python -m pytest --cov=.
```

### Development Mode

For development with hot reload:

```bash
# Start only dependencies
docker-compose up -d weaviate ollama postgres redis n8n

# Run backend locally
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

## 🔍 Monitoring

### Service Health

```bash
# Check all services
curl http://localhost:8000/health

# Get knowledge base statistics
curl http://localhost:8000/stats

# List available sources
curl http://localhost:8000/sources
```

### Logs

```bash
# View all logs
docker-compose logs -f

# View specific service logs
docker-compose logs -f backend
docker-compose logs -f weaviate
docker-compose logs -f ollama
```

## 🚀 Production Deployment

### Security Considerations

1. Change default passwords in `.env`
2. Use proper SSL certificates
3. Configure firewall rules
4. Enable authentication for n8n
5. Use secrets management for API keys

### Scaling

- **Horizontal scaling**: Run multiple backend instances behind a load balancer
- **Vector store scaling**: Use Weaviate clustering
- **LLM scaling**: Deploy multiple Ollama instances
- **Database scaling**: Use PostgreSQL read replicas

### Backup

```bash
# Backup PostgreSQL
docker-compose exec postgres pg_dump -U kb_user knowledge_base > backup.sql

# Backup Weaviate
# Use Weaviate's backup functionality or volume snapshots
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License.

## 🆘 Troubleshooting

### Common Issues

**LLaMA model not loading:**

- Check available disk space (models are large)
- Monitor Ollama logs: `docker-compose logs -f ollama`
- Manually pull model: `docker-compose exec ollama ollama pull llama3`

**Weaviate connection issues:**

- Ensure Weaviate is healthy: `curl http://localhost:8080/v1/meta`
- Check vector store logs: `docker-compose logs -f weaviate`

**Slack integration not working:**

- Verify bot token and permissions
- Check Slack API rate limits
- Ensure bot is added to channels

**Out of memory errors:**

- Increase Docker memory limits
- Use smaller LLM models (e.g., `llama3:8b` instead of `llama3:70b`)
- Reduce chunk sizes in configuration

### Getting Help

- Check the logs: `docker-compose logs -f`
- Review the API documentation at `http://localhost:8000/docs`
- Open an issue on GitHub
