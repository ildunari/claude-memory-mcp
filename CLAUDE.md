# CLAUDE.md

## Static Socket Configuration

**CRITICAL**: claude-memory-mcp MUST use port 3006 exclusively:
- **Tailscale Access**: http://100.x.x.x:3006 (replace x.x.x with your Tailscale IP)
- **NEVER use `serve` command or dynamic ports**
- **MCP server should run on port 3006 when TCP transport is used**

## Development Commands

- Check package.json for available scripts
- Use appropriate start command for port 3006

## Project Overview

claude-memory-mcp is a Model Context Protocol (MCP) server that provides memory capabilities for Claude AI assistants, enabling persistent storage and retrieval of information across conversations.

## Architecture

- **Type**: MCP Server
- **Transport**: Standard I/O or TCP (port 3006)
- **Features**: Memory storage, conversation persistence, data retrieval