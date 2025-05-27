#!/bin/bash

echo "🚀 Starting Qdrant Development Environment"
echo "========================================="

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker Desktop first."
    exit 1
fi

# Start Qdrant
echo "📦 Starting Qdrant vector database..."
docker-compose -f docker-compose.qdrant.yml up -d

# Wait for Qdrant to be ready
echo "⏳ Waiting for Qdrant to be ready..."
sleep 5

# Check if Qdrant is running
if curl -s http://localhost:6333/health > /dev/null; then
    echo "✅ Qdrant is running at http://localhost:6333"
    echo "🎯 Qdrant Web UI available at http://localhost:6335"
else
    echo "❌ Qdrant failed to start. Check logs with: docker-compose -f docker-compose.qdrant.yml logs"
    exit 1
fi

echo ""
echo "📝 Next steps:"
echo "1. Create Python virtual environment:"
echo "   python3 -m venv venv"
echo "   source venv/bin/activate"
echo ""
echo "2. Install dependencies:"
echo "   pip install -r requirements-qdrant.txt"
echo ""
echo "3. Run the MCP server:"
echo "   python -m memory_mcp --config config.qdrant.json"
echo ""
echo "4. Or migrate existing memories:"
echo "   python migrate_to_qdrant.py [path/to/memory.json]"