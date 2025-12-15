#!/bin/bash
# Setup script for Graph Builder Service

set -e

BLUE='\033[0;34m'
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Graph Builder Service Setup${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Check Python version
echo -e "${BLUE}Checking Python version...${NC}"
python_version=$(python3 --version 2>&1 | awk '{print $2}')
required_version="3.11"

if [[ $(echo -e "$python_version\n$required_version" | sort -V | head -n1) != "$required_version" ]]; then
    echo -e "${RED}✗ Python 3.11+ is required. Found: $python_version${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Python version OK: $python_version${NC}"

# Install uv if not installed
if ! command -v uv &> /dev/null; then
    echo -e "${BLUE}Installing uv...${NC}"
    curl -LsSf https://astral.sh/uv/install.sh | sh
    echo -e "${GREEN}✓ uv installed${NC}"
else
    echo -e "${GREEN}✓ uv already installed${NC}"
fi

# Create virtual environment
echo -e "${BLUE}Creating virtual environment...${NC}"
uv venv
source .venv/bin/activate
echo -e "${GREEN}✓ Virtual environment created${NC}"

# Install dependencies
echo -e "${BLUE}Installing dependencies...${NC}"
uv pip install -e ".[dev]"
echo -e "${GREEN}✓ Dependencies installed${NC}"

# Create .env file
if [ ! -f .env ]; then
    echo -e "${BLUE}Creating .env file...${NC}"
    cp .env.example .env
    echo -e "${GREEN}✓ .env file created${NC}"
    echo -e "${RED}⚠️  Please update .env with your credentials${NC}"
else
    echo -e "${GREEN}✓ .env file already exists${NC}"
fi

# Create necessary directories
echo -e "${BLUE}Creating necessary directories...${NC}"
mkdir -p cache_dir logs data/samples
echo -e "${GREEN}✓ Directories created${NC}"

# Install pre-commit hooks
echo -e "${BLUE}Installing pre-commit hooks...${NC}"
pre-commit install
echo -e "${GREEN}✓ Pre-commit hooks installed${NC}"

# Run tests
echo -e "${BLUE}Running tests...${NC}"
pytest tests/ -v --tb=short || echo -e "${RED}⚠️  Some tests failed${NC}"

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Setup Complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "Next steps:"
echo -e "1. Update ${BLUE}.env${NC} with your credentials"
echo -e "2. Start Neo4j: ${BLUE}docker-compose -f docker/docker-compose.yml up -d neo4j${NC}"
echo -e "3. Run the service: ${BLUE}make dev${NC}"
echo -e "4. Visit: ${BLUE}http://localhost:8000/docs${NC}"
echo ""