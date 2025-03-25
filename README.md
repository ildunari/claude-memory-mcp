# Claude Memory MCP Server

An MCP (Model Context Protocol) server implementation that provides persistent memory capabilities for Large Language Models, specifically designed to integrate with the Claude desktop application.

## Overview

This project implements optimal memory techniques based on comprehensive research of current approaches in the field. It provides a standardized way for Claude to maintain persistent memory across conversations and sessions.

## Features

- **Tiered Memory Architecture**: Short-term, long-term, and archival memory tiers
- **Multiple Memory Types**: Support for conversations, knowledge, entities, and reflections
- **Semantic Search**: Retrieve memories based on semantic similarity
- **Memory Consolidation**: Automatic consolidation of short-term memories into long-term memory
- **Memory Management**: Importance-based memory retention and forgetting
- **Claude Integration**: Ready-to-use integration with Claude desktop application
- **MCP Protocol Support**: Compatible with the Model Context Protocol

## Architecture

The MCP server follows a functional domain-based architecture with the following components:

```
┌─────────────────────────────────────────────────────────┐
│                   Claude Desktop                        │
└───────────────────────────┬─────────────────────────────┘
                            │
┌───────────────────────────▼─────────────────────────────┐
│                     MCP Interface                       │
│  ┌─────────────────┐  ┌─────────────────┐  ┌──────────┐ │
│  │ Tool Definitions│  │ Request Handler │  │ Security │ │
│  └─────────────────┘  └─────────────────┘  └──────────┘ │
└───────────────────────────┬─────────────────────────────┘
                            │
┌───────────────────────────▼─────────────────────────────┐
│                Memory Domain Manager                    │
├─────────────────┬─────────────────┬────────────────────┤
│  Episodic Domain│  Semantic Domain│  Temporal Domain   │
├─────────────────┴─────────────────┴────────────────────┤
│                  Persistence Domain                    │
└─────────────────────────────────────────────────────────┘
```

### Functional Domains

1. **Episodic Domain**: Manages session-based interactions and contextual memory
2. **Semantic Domain**: Handles knowledge organization and retrieval
3. **Temporal Domain**: Controls time-aware processing of memories
4. **Persistence Domain**: Manages storage optimization and retrieval

## Installation

### Prerequisites

- Python 3.8 or higher
- pip package manager

### Installation Steps

1. Clone the repository:
   ```
   git clone https://github.com/WhenMoon-afk/claude-memory-mcp.git
   cd claude-memory-mcp
   ```

2. Install dependencies:
   ```
   pip install -e .
   ```

3. Run the setup script:
   ```
   chmod +x setup.sh
   ./setup.sh
   ```

## Claude Desktop Integration

To integrate with the Claude desktop application, add the following to your Claude configuration file:

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

## Memory File Structure

The memory system uses a JSON-based file structure with the following components:

```json
{
  "metadata": {
    "version": "1.0",
    "created_at": "ISO-8601 timestamp",
    "updated_at": "ISO-8601 timestamp"
  },
  "memory_index": {
    // Vector index for fast semantic search
  },
  "short_term_memory": [
    // Recent and frequently accessed memories
  ],
  "long_term_memory": [
    // Older or less frequently accessed memories
  ],
  "archived_memory": [
    // Rarely accessed but potentially valuable memories
  ],
  "memory_schema": {
    // Schema definitions for memory entries
  },
  "config": {
    // Configuration settings for memory management
  }
}
```

## Usage

### Starting the Server

```bash
python -m memory_mcp
```

### Available Tools

- `store_memory`: Store new information in memory
- `retrieve_memory`: Retrieve relevant memories based on query
- `list_memories`: List available memories with filtering options
- `update_memory`: Update existing memory entries
- `delete_memory`: Remove specific memories
- `memory_stats`: Get statistics about the memory store

## Development

### Project Structure

```
memory_mcp/
├── memory/
│   ├── models.py         # Memory data models
│   ├── storage.py        # Memory storage operations
│   ├── retrieval.py      # Memory retrieval operations
│   └── consolidation.py  # Memory consolidation operations
├── domains/
│   ├── episodic.py       # Episodic memory domain
│   ├── semantic.py       # Semantic knowledge domain
│   ├── temporal.py       # Temporal processing domain
│   └── persistence.py    # Storage and retrieval domain
├── mcp/
│   ├── server.py         # MCP server implementation
│   ├── tools.py          # MCP tool definitions
│   └── handler.py        # Request handling
├── security/
│   └── validation.py     # Input validation
└── utils/
    ├── embeddings.py     # Vector embedding utilities
    └── schema.py         # Schema validation
```

### Running Tests

```
pytest
```

## Research Background

This implementation is based on comprehensive research of current LLM persistent memory techniques:

- **OS-Inspired Memory Management**: Tiered memory architecture similar to MemGPT
- **Biological-Inspired Episodic Memory**: Context-sensitive memory retrieval
- **Vector Embeddings**: Semantic search inspired by vector database approaches
- **Self-Reflection**: Memory consolidation through periodic review

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgements

- Based on research of optimal memory techniques for LLMs
- Implements the Model Context Protocol for integration with Claude
