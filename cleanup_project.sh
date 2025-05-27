#!/bin/bash
# Cleanup script to organize the project

echo "🧹 Cleaning up claude-memory-mcp project..."

# 1. Clean Python cache files
echo "Removing Python cache files..."
find . -type f -name "*.pyc" -delete
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null
find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null

# 2. Remove .DS_Store files
echo "Removing .DS_Store files..."
find . -name ".DS_Store" -delete

# 3. Create tests directory structure if needed
echo "Organizing test files..."
mkdir -p tests/integration
mkdir -p tests/unit

# 4. Move test files to appropriate directories
# Integration tests
for file in test_mcp_*.py test_qdrant_integration.py test_phase2_*.py test_hybrid_search.py; do
    if [ -f "$file" ]; then
        echo "Moving $file to tests/integration/"
        git mv "$file" tests/integration/ 2>/dev/null || mv "$file" tests/integration/
    fi
done

# Other test files to tests/
for file in test_*.py; do
    if [ -f "$file" ]; then
        echo "Moving $file to tests/"
        git mv "$file" tests/ 2>/dev/null || mv "$file" tests/
    fi
done

# 5. Create docs for status files
echo "Organizing documentation..."
mkdir -p docs/status
for file in *_STATUS.md *_SUCCESS.md *_COMPLETE.md; do
    if [ -f "$file" ]; then
        echo "Moving $file to docs/status/"
        git mv "$file" docs/status/ 2>/dev/null || mv "$file" docs/status/
    fi
done

# 6. Remove local storage
echo "Removing local storage..."
rm -rf qdrant_storage/
rm -rf venv/

# 7. Add to .gitignore if not already there
echo "Updating .gitignore..."
cat >> .gitignore << 'EOF'

# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
*.egg-info/
dist/
build/

# Virtual environments
venv/
env/
ENV/

# IDEs
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Local storage
qdrant_storage/
*.db
*.sqlite

# Logs
*.log
logs/

# Test coverage
.coverage
htmlcov/
.pytest_cache/
EOF

echo "✅ Cleanup complete!"
echo ""
echo "Summary of changes:"
echo "- Removed all cache files"
echo "- Organized test files into tests/ directory"
echo "- Moved status documentation to docs/status/"
echo "- Updated .gitignore"
echo ""
echo "Run 'git status' to see the changes"