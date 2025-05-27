#!/usr/bin/env python3
"""Test script to verify memory-mcp server starts correctly."""

import sys
import subprocess

# Run the server directly
result = subprocess.run([
    sys.executable, 
    "-m", 
    "memory_mcp", 
    "--config", 
    "config.qdrant.json"
], capture_output=True, text=True, timeout=2, cwd="/Users/kosta/Documents/ProjectsCode/claude-memory-mcp")

print("STDOUT:")
print(result.stdout)
print("\nSTDERR:")
print(result.stderr)
print(f"\nReturn code: {result.returncode}")