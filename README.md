# Hive Mind - High-Frequency MoE Architecture

A massively parallel agent orchestration system where 10 specialized agents research and synthesize information simultaneously.

## 🏗️ Architecture

### Components

1. **Hot Memory (Redis Stack)**
   - Fast vector search with HNSW indexing
   - TTL-based eviction (1 hour)
   - Agent-scoped memory prefixes
   - Real-time semantic search across all agents

2. **Cold Memory (LanceDB)**
   - IVF-PQ compressed vector storage
   - Cross-Encoder reranking
   - Long-term archival of high-value findings

3. **Orchestrator (FastAPI)**
   - Async agent dispatch with `asyncio.gather()`
   - Streaming responses for real-time agent thoughts
   - Comprehensive metrics tracking

4. **MCP Agents**
   - Web Scout (Tavily)
   - Code Hunter (GitHub)
   - The Fixer (Stack Overflow)
   - The Watcher (YouTube)
   - The Scholar (ArXiv)
   - The Fact Checker (Wikipedia)
   - Privacy Scout (DuckDuckGo)
   - Deep Fetcher (Puppeteer)
   - Social Sentiment (Reddit)
   - Context Analyst (Filesystem)

## 🚀 Quick Start

### Prerequisites

- Docker and Docker Compose
- Python 3.10+
- Redis instance (or use provided Docker Stack)
- Google API Key (for Gemini models)

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd hive-mind
```

2. Copy environment template:
```bash
cp .env.example .env
```

3. Edit `.env` with your values:
```env
REDIS_PASSWORD=your_secure_password_here
GOOGLE_API_KEY=your_google_api_key_here
```

4. Build and start services:
```bash
docker-compose up -d
```

5. Verify services are running:
```bash
# Check Redis Stack
curl http://localhost:8001

# Check Orchestrator
curl http://localhost:8000/health
```

## 📖️ Usage

### Query the Hive Mind

**Simple Query:**
```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"query": "How do I implement vector search in Redis?", "max_agents": 5}'
```

**Streaming Query (Real-time Agent Thoughts):**
```bash
curl -X POST http://localhost:8000/query/stream \
  -H "Content-Type: application/json" \
  -d '{"query": "What are the best practices for async Python?", "max_agents": 3}'
```

**Filter Specific Agents:**
```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"query": "Redis vector search patterns", "agents": ["res_02_code", "res_06_wiki"]}'
```

### API Endpoints

- `GET /` - API information
- `GET /health` - Health check
- `GET /stats` - System statistics
- `GET /agents` - List all agents
- `GET /memory` - Memory statistics
- `POST /query` - Execute mission (parallel agents)
- `POST /query/stream` - Execute mission (streaming)

### Monitoring

- **RedisInsight UI**: http://localhost:8001
- **API Logs**: Check Docker logs: `docker-compose logs -f orchestrator`
- **System Stats**: http://localhost:8000/stats

## 🧪 Testing

Run all tests:
```bash
cd hive-mind
pytest tests/ -v
```

Run specific test file:
```bash
pytest tests/test_hot_memory.py -v
pytest tests/test_orchestrator.py -v
```

## 🔧 Configuration

Key settings in `.env`:

| Setting | Default | Description |
|----------|---------|-------------|
| `REDIS_PASSWORD` | Required | Redis authentication password |
| `GOOGLE_API_KEY` | Required | Google AI API key |
| `LOG_LEVEL` | INFO | Debug level (DEBUG, INFO, WARNING, ERROR) |
| `REDIS_TTL` | 3600 | Hot memory TTL in seconds (1 hour) |

## 📦 Project Structure

```
hive-mind/
├── docker-compose.yml
├── pyproject.toml
├── .env.example
├── orchestrator/
│   ├── __init__.py
│   ├── main.py           # FastAPI app
│   ├── config.py          # Configuration management
│   ├── memory/
│   │   ├── hot.py         # RedisVL wrapper
│   │   └── cold.py        # LanceDB wrapper
│   ├── agents/
│   │   ├── base.py        # Base MCP agent
│   │   ├── web_scout.py    # Web Scout agent
│   │   ├── code_hunter.py  # Code Hunter agent
│   │   └── registry.py     # Agent configuration loader
│   └── utils/
│       ├── logging.py     # Structured logging
│       └── metrics.py     # Performance monitoring
├── tests/
│   ├── conftest.py
│   ├── test_hot_memory.py
│   ├── test_cold_memory.py
│   ├── test_agents.py
│   └── test_orchestrator.py
├── schemas/
│   ├── redis_schema.yaml    # RedisVL index schema
│   └── agents_config.json   # Agent definitions
└── .gitignore
```

## 🎯 Design Decisions

### Why Redis Stack for Hot Memory?
- **Sub-second vector search**: HNSW provides ANN search at <1ms
- **Native Redis support**: Built-in persistence, replication, clustering
- **TTL-based eviction**: Automatic cleanup prevents memory bloat
- **Agent-scoped prefixes**: Easy filtering by agent ID

### Why LanceDB for Cold Memory?
- **Compressed storage**: IVF-PQ reduces memory usage by ~10x
- **Reranking support**: Cross-Encoder improves result relevance
- **Async operations**: Non-blocking I/O for large datasets
- **Hybrid search**: Vector + FTS with reranking

### Why 10 Agents Instead of 1?
- **Specialized knowledge domains**: Each agent excels at their specialty
- **Parallel execution**: All agents research simultaneously
- **Reduced latency**: Sub-second response vs. multi-minute single agent
- **Redundancy**: Multiple perspectives on the same question
- **Fault tolerance**: If one agent fails, others continue

## 🐛 Troubleshooting

### Redis Stack fails to start
```bash
# Check Docker logs
docker-compose logs redis-stack

# Verify password
docker-compose exec redis-stack redis-cli -a $REDIS_PASSWORD ping
```

### Agent initialization fails
```bash
# Check orchestrator logs
docker-compose logs orchestrator

# Verify MCP servers are accessible
# (In production, MCP servers would need to be running)
```

### Memory issues
```bash
# Check Redis memory usage
docker-compose exec redis-stack redis-cli -a $REDIS_PASSWORD info memory

# Prune manually if needed
# (API endpoint can be created for manual pruning)
```

## 📚 License

MIT License - Feel free to use and modify for your needs.

## 🤝 Contributing

Contributions are welcome! Please read the contributing guidelines before submitting PRs.
