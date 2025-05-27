# Claude Memory MCP Server

An MCP (Model Context Protocol) server implementation that provides persistent memory capabilities for Large Language Models, specifically designed to integrate with the Claude desktop application.

![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)

## Overview

This project implements optimal memory techniques based on comprehensive research of current approaches in the field. It provides a standardized way for Claude to maintain persistent memory across conversations and sessions.

## Features

- **Tiered Memory Architecture**: Short-term, long-term, and archival memory tiers
- **Multiple Memory Types**: Support for conversations, knowledge, entities, and reflections
- **Semantic Search**: Retrieve memories based on semantic similarity
- **Memory Management**: Store and retrieve memories through explicit Claude commands
- **Memory Consolidation**: Automatic consolidation of short-term memories into long-term memory
- **Importance-based Retention**: Smart memory retention and forgetting based on importance
- **Claude Integration**: Ready-to-use integration with Claude desktop application
- **MCP Protocol Support**: Compatible with the Model Context Protocol
- **Docker Support**: Easy deployment using Docker containers

## Quick Start

### Option 1: Using Docker (Recommended)

```bash
# Clone the repository
git clone https://github.com/WhenMoon-afk/claude-memory-mcp.git
cd claude-memory-mcp

# Start with Docker Compose
docker-compose up -d
```

Configure Claude Desktop to use the containerized MCP server (see [Docker Usage Guide](docs/docker_usage.md) for details).

### Option 2: Standard Installation

1. **Prerequisites**:
   - Python 3.8-3.12
   - pip package manager

2. **Installation**:
   ```bash
   # Clone the repository
   git clone https://github.com/WhenMoon-afk/claude-memory-mcp.git
   cd claude-memory-mcp
   
   # Install dependencies
   pip install -r requirements.txt
   
   # Run setup script
   chmod +x setup.sh
   ./setup.sh
   ```

3. **Claude Desktop Integration**:

   Add the following to your Claude configuration file:

   ```json
   {
     "mcpServers": {
       "memory": {
         "command": "python",
         "args": ["-m", "memory_mcp"],
         "env": {
           "MEMORY_FILE_PATH": "/path/to/your/memory.json"
         }
       }
     }
   }
   ```

## Using Memory with Claude

The Memory MCP Server enables Claude to remember information across conversations through explicit memory management. 

1. **Storing Memories**: Claude can store memories when instructed:
   - Important facts and information
   - User preferences and context
   - Conversations and decisions

2. **Memory Recall**: To see what Claude remembers, simply ask:
   - "What do you remember about me?"
   - "What do you know about my preferences?"

3. **System Prompt**: For optimal memory usage, add this to your Claude system prompt:

   ```
   This Claude instance has been enhanced with persistent memory capabilities.
   Claude can store important information when requested and recall it across
   conversations. Use the memory tools to explicitly save and retrieve information.
   ```

See the [User Guide](docs/user_guide.md) for detailed usage instructions and examples.

## Documentation

- [User Guide](docs/user_guide.md)
- [Docker Usage Guide](docs/docker_usage.md)
- [Compatibility Guide](docs/compatibility.md)
- [Architecture](docs/architecture.md)
- [Claude Integration Guide](docs/claude_integration.md)

## Examples

The `examples` directory contains scripts demonstrating how to interact with the Memory MCP Server:

- `store_memory_example.py`: Example of storing a memory
- `retrieve_memory_example.py`: Example of retrieving memories

## Recent Updates (v0.2.2)

### 🎉 Major Updates (2025-05-27)
- **Fixed Memory Stats**: Domain-specific memory type counts now display correctly
- **Architecture Clarification**: Removed auto-capture features that are incompatible with MCP architecture
- **Improved Stability**: Fixed initialization issues that were causing the tool to hang
- **Focused on Core Features**: Memory storage and retrieval work reliably through explicit Claude commands

## Troubleshooting

If you encounter issues:

1. Check the [Compatibility Guide](docs/compatibility.md) for dependency requirements
2. Ensure your Python version is 3.8-3.12
3. For NumPy issues, use: `pip install "numpy>=1.20.0,<2.0.0"`
4. Try using Docker for simplified deployment

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.