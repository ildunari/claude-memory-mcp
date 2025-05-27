#\!/bin/bash

# Memory MCP Server startup script
# This script ensures the environment is properly set up and starts the server

set -e

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Create virtual environment if it doesn't exist
if [ \! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
    echo "Installing dependencies..."
    source venv/bin/activate
    pip install -e .
else
    source venv/bin/activate
fi

# Set Python path to ensure imports work
export PYTHONPATH="$SCRIPT_DIR"

# Start the memory MCP server
echo "Starting Memory MCP Server..."
exec python3 -m memory_mcp "$@"
EOF < /dev/null