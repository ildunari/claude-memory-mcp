# Setup Guide - Claude Memory MCP with Qdrant

## Prerequisites
- macOS (for development with Claude Code)
- Docker Desktop installed and running
- Python 3.8-3.12
- Git

## Step 1: Clone and Setup

```bash
# Already done - repository is in:
cd /Users/kostamilovanovic/Documents/ProjectsCode/claude-memory-mcp

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements-qdrant.txt
```

## Step 2: Start Qdrant

```bash
# Make sure Docker is running first!
./start_qdrant_dev.sh
```

You should see:
- ✅ Qdrant running at http://localhost:6333
- 🎯 Web UI at http://localhost:6335

## Step 3: Test the Setup

```bash
# Test Qdrant connection
curl http://localhost:6333/health

# Test embedding generation (in Python)
python -c "
from sentence_transformers import SentenceTransformer
model = SentenceTransformer('all-MiniLM-L6-v2')
print('✅ Embeddings working!')
"
```

## Step 4: Run the Enhanced MCP Server

```bash
# With Qdrant backend
python -m memory_mcp --config config.qdrant.json

# Or with original JSON backend (fallback)
python -m memory_mcp
```

## Step 5: Add to MetaMCP

Since you have MetaMCP running, add this as a new server:

```javascript
// Use the add-mcp-server.js script
const server = {
  name: 'Claude Memory Qdrant',
  command: 'python',
  args: [
    '-m', 'memory_mcp',
    '--config', '/Users/kostamilovanovic/Documents/ProjectsCode/claude-memory-mcp/config.qdrant.json'
  ],
  env: {
    MEMORY_BACKEND: 'qdrant'
  }
};
```

## Next Steps

1. **Test locally** on Mac with CPU embeddings
2. **Set up Windows** GPU server when ready
3. **Migrate** any existing memories
4. **Deploy** for production use

## Quick Commands

```bash
# Start everything
./start_qdrant_dev.sh
source venv/bin/activate
python -m memory_mcp --config config.qdrant.json

# Stop everything
docker-compose -f docker-compose.qdrant.yml down

# View logs
docker-compose -f docker-compose.qdrant.yml logs -f

# Check Qdrant UI
open http://localhost:6335
```