#!/bin/bash
# Script automatique de migration vers la nouvelle structure

set -e

BLUE='\033[0;34m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Migration vers Structure Optimisée${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# 1. Créer la structure de dossiers
echo -e "${BLUE}1. Création de la structure de dossiers...${NC}"
mkdir -p graph-builder-service/{app/{core,api/v1/endpoints,services/neo4j,models,db,utils},tests/{unit,integration,e2e},docker,scripts,docs,k8s,data/samples,logs,cache_dir}

# Créer tous les __init__.py
find graph-builder-service/app -type d -exec touch {}/__init__.py \;
touch graph-builder-service/tests/__init__.py

echo -e "${GREEN}✓ Structure créée${NC}"

# 2. Copier les fichiers de l'ancien projet (si existe)
if [ -d "ingestion-service" ]; then
    echo -e "${BLUE}2. Copie des fichiers existants...${NC}"

    # Models
    if [ -d "ingestion-service/app/models" ]; then
        cp -r ingestion-service/app/models/* graph-builder-service/app/models/ 2>/dev/null || true
    fi

    # Services
    if [ -d "ingestion-service/app/services" ]; then
        cp ingestion-service/app/services/*.py graph-builder-service/app/services/ 2>/dev/null || true
    fi

    # DB
    if [ -d "ingestion-service/app/db" ]; then
        cp -r ingestion-service/app/db/* graph-builder-service/app/db/ 2>/dev/null || true
    fi

    # Utils
    if [ -d "ingestion-service/app/utils" ]; then
        cp -r ingestion-service/app/utils/* graph-builder-service/app/utils/ 2>/dev/null || true
    fi

    # Data samples
    if [ -d "ingestion-service/data" ]; then
        cp -r ingestion-service/data/* graph-builder-service/data/samples/ 2>/dev/null || true
    fi

    echo -e "${GREEN}✓ Fichiers copiés${NC}"
else
    echo -e "${YELLOW}⚠️  Ancien projet non trouvé, création structure vide${NC}"
fi

# 3. Créer les fichiers de configuration
cd graph-builder-service

echo -e "${BLUE}3. Création des fichiers de configuration...${NC}"

# pyproject.toml
cat > pyproject.toml << 'EOF'
[project]
name = "graph-builder-service"
version = "0.1.0"
description = "Graph builder service for Neo4j"
requires-python = ">=3.11"

dependencies = [
    "fastapi>=0.109.0",
    "uvicorn[standard]>=0.27.0",
    "pydantic>=2.5.0",
    "pydantic-settings>=2.1.0",
    "python-dotenv>=1.0.0",
    "python-multipart>=0.0.6",
    "neo4j>=5.15.0",
    "sqlalchemy>=2.0.25",
    "polars>=0.20.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.4.3",
    "pytest-asyncio>=0.23.2",
    "black>=23.12.1",
    "ruff>=0.1.9",
]
EOF

# .env.example
cat > .env.example << 'EOF'
APP_NAME=GraphBuilderService
DEBUG=false
ENVIRONMENT=production
NEO4J_URI=bolt://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=change-me
SECRET_KEY=change-me-in-production
API_KEY=your-api-key
CORS_ORIGINS=http://localhost:3000,http://localhost:8080
EOF

# .gitignore
cat > .gitignore << 'EOF'
__pycache__/
*.py[cod]
.venv/
.env
logs/
cache_dir/
*.log
.pytest_cache/
.coverage
htmlcov/
EOF

echo -e "${GREEN}✓ Fichiers de configuration créés${NC}"

# 4. Créer Makefile
echo -e "${BLUE}4. Création du Makefile...${NC}"

cat > Makefile << 'EOF'
.PHONY: help install dev test

help:
	@echo "Available commands:"
	@echo "  make install   - Install dependencies"
	@echo "  make dev       - Run development server"
	@echo "  make test      - Run tests"

install:
	uv pip install -e ".[dev]"

dev:
	uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

test:
	uv run pytest tests/ -v
EOF

echo -e "${GREEN}✓ Makefile créé${NC}"

# 5. Créer README.md
echo -e "${BLUE}5. Création du README...${NC}"

cat > README.md << 'EOF'
# Graph Builder Service

Service FastAPI pour la construction de graphes Neo4j.

## Installation

```bash
# Installer uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# Installer les dépendances
make install

# Configurer l'environnement
cp .env.example .env
# Éditer .env avec vos credentials

# Lancer le service
make dev
```

## Documentation

API: http://localhost:8000/docs
EOF

echo -e "${GREEN}✓ README créé${NC}"

# 6. Message final
echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Migration terminée avec succès!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "Prochaines étapes:"
echo -e "1. ${BLUE}cd graph-builder-service${NC}"
echo -e "2. ${BLUE}cp .env.example .env${NC} et configurer vos credentials"
echo -e "3. ${BLUE}make install${NC} pour installer les dépendances"
echo -e "4. Copier les fichiers optimisés depuis les artifacts"
echo -e "5. ${BLUE}make dev${NC} pour démarrer le serveur"
echo ""
echo -e "${YELLOW}Note:${NC} Certains fichiers doivent être adaptés manuellement"
echo -e "Consultez ${BLUE}MIGRATION_GUIDE.md${NC} pour plus de détails"
echo ""