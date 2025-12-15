# Migration Guide - Structure Projet Optimisée

Ce guide vous aide à migrer votre projet actuel vers la nouvelle structure optimisée.

## 📋 Vue d'ensemble

### Avant (Ancienne structure)
```
ingestion-service/
├── app/
│   ├── main.py (tout dans un fichier)
│   ├── services/
│   ├── models/
│   └── db/
```

### Après (Nouvelle structure)
```
graph-builder-service/
├── app/
│   ├── main.py (léger, orchestration)
│   ├── core/ (configuration centralisée)
│   ├── api/v1/endpoints/ (routes séparées)
│   ├── services/ (logique métier)
│   └── models/ (modèles Pydantic)
```

## 🚀 Étapes de Migration

### 1. Créer la nouvelle structure

```bash
# Créer le nouveau projet
mkdir -p graph-builder-service
cd graph-builder-service

# Créer la structure de dossiers
mkdir -p app/{core,api/v1/endpoints,services/neo4j,models,db,utils}
mkdir -p tests/{unit,integration,e2e}
mkdir -p docker scripts docs k8s data/samples logs cache_dir

# Créer les fichiers __init__.py
touch app/__init__.py
touch app/core/__init__.py
touch app/api/__init__.py
touch app/api/v1/__init__.py
touch app/api/v1/endpoints/__init__.py
touch app/services/__init__.py
touch app/services/neo4j/__init__.py
touch app/models/__init__.py
touch app/db/__init__.py
touch app/utils/__init__.py
touch tests/__init__.py
```

### 2. Copier les fichiers de configuration

```bash
# Copier depuis les artifacts fournis
# pyproject.toml
# .env.example
# .gitignore
# Makefile
# README.md
# docker/Dockerfile
# docker/docker-compose.yml
```

### 3. Migrer les fichiers core

```bash
# app/core/config.py - Nouvelle configuration centralisée
# app/core/logging.py - Système de logging
# app/core/exceptions.py - Exceptions personnalisées
# app/core/security.py - Authentification (si nécessaire)
```

### 4. Migrer les modèles

Déplacez vos modèles existants vers `app/models/`:

```bash
cp ancien-projet/app/models/*.py app/models/
```

Pas de changement nécessaire, juste organisation.

### 5. Migrer les services

#### Session Manager
```bash
# Utiliser le nouveau app/services/session_manager.py avec lazy init
# (fourni dans les artifacts)
```

#### Services Neo4j
```bash
# Créer la structure Neo4j
mkdir -p app/services/neo4j

# Fichiers à créer:
# - app/services/neo4j/__init__.py
# - app/services/neo4j/database.py (ancien neo4j_database.py)
# - app/services/neo4j/graph_creator.py (ancien neo4j_db.py optimisé)
# - app/services/neo4j/graph_api.py (neo4j_graph_creation_api.py)
# - app/services/neo4j/singleton.py (nouveau)
```

#### Autres services
```bash
# Copier et adapter
cp ancien-projet/app/services/ingest.py app/services/
cp ancien-projet/app/services/*_loader.py app/services/
```

### 6. Créer les endpoints API v1

Au lieu d'avoir tout dans `main.py`, créez des fichiers séparés :

```bash
# app/api/dependencies.py - Dépendances injectables
# app/api/v1/router.py - Router principal
# app/api/v1/endpoints/files.py
# app/api/v1/endpoints/databases.py
# app/api/v1/endpoints/sessions.py
# app/api/v1/endpoints/graph_builder.py
# app/api/v1/endpoints/neo4j.py
# app/api/v1/endpoints/health.py
```

### 7. Créer le nouveau main.py

Utilisez le `main.py` production-ready fourni dans les artifacts.

### 8. Configuration environnement

```bash
# 1. Créer .env depuis .env.example
cp .env.example .env

# 2. Éditer .env avec vos credentials
nano .env  # ou votre éditeur préféré

# 3. Variables importantes à configurer:
# - NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD
# - MYSQL_*, POSTGRES_*, ORACLE_* (selon vos besoins)
# - SECRET_KEY (générer une clé unique)
# - API_KEY
```

### 9. Installation des dépendances

```bash
# Installer uv si pas déjà fait
curl -LsSf https://astral.sh/uv/install.sh | sh

# Installer les dépendances
make install
# ou
uv pip install -e ".[dev]"
```

### 10. Tests de migration

```bash
# 1. Test des imports
python3 -c "from app.main import app; print('✓ Import OK')"

# 2. Test de démarrage
make dev
# ou
uv run uvicorn app.main:app --reload

# 3. Vérifier les endpoints
curl http://localhost:8000/health
curl http://localhost:8000/api/v1/health
```

## 📦 Mapping des fichiers

### Configuration
| Ancien | Nouveau |
|--------|---------|
| `app/config.py` | `app/core/config.py` |
| Variables éparpillées | Centralisé dans Settings |

### Services
| Ancien | Nouveau |
|--------|---------|
| `app/services/session_manager.py` | `app/services/session_manager.py` (optimisé) |
| `app/services/neo4j_db.py` | `app/services/neo4j/graph_creator.py` |
| `app/services/neo4j_database.py` | `app/services/neo4j/database.py` |
| Pas de singleton | `app/services/neo4j/singleton.py` |

### API
| Ancien | Nouveau |
|--------|---------|
| Tout dans `main.py` | `app/api/v1/endpoints/*.py` |
| Imports locaux | `app/api/dependencies.py` |

## ⚠️ Points d'attention

### 1. Imports
**Avant:**
```python
from app.services.session_manager import session_manager  # Import local
```

**Après:**
```python
from app.api.dependencies import SessionManagerDep

async def endpoint(session_manager: SessionManagerDep):
    # Injection de dépendance
```

### 2. Configuration
**Avant:**
```python
import os
from dotenv import load_dotenv

load_dotenv()
uri = os.getenv("URI")
```

**Après:**
```python
from app.core.config import settings

uri = settings.neo4j_uri
```

### 3. Neo4j Driver
**Avant:**
```python
# Création à chaque requête
driver = Neo4jGraphCreation(uri, user, password)
```

**Après:**
```python
# Singleton réutilisé
from app.services.neo4j.singleton import neo4j_driver
driver = neo4j_driver.get_driver()
```

## 🧪 Checklist de validation

- [ ] Le serveur démarre en < 3 secondes
- [ ] Tous les endpoints répondent
- [ ] Les logs sont structurés et lisibles
- [ ] Les tests passent
- [ ] `/health` et `/api/v1/health` fonctionnent
- [ ] Upload de fichiers fonctionne
- [ ] Connexion aux bases de données fonctionne
- [ ] Création de graphes Neo4j fonctionne
- [ ] Sessions sont persistées correctement

## 🐛 Dépannage

### Le serveur ne démarre pas
```bash
# Vérifier les imports
python3 -c "from app.core.config import settings; print(settings)"
python3 -c "from app.api.dependencies import get_session_manager; print('OK')"
```

### Erreurs d'import
```bash
# Vérifier que tous les __init__.py sont présents
find app -type d -exec test -f {}/__init__.py \; -print
```

### Neo4j ne se connecte pas
```bash
# Tester la connexion
python3 -c "
from app.core.config import settings
from neo4j import GraphDatabase
driver = GraphDatabase.driver(settings.neo4j_uri, auth=(settings.neo4j_username, settings.neo4j_password))
driver.verify_connectivity()
print('✓ Neo4j OK')
"
```

## 📚 Ressources

- Documentation FastAPI: https://fastapi.tiangolo.com
- Documentation Neo4j Python: https://neo4j.com/docs/python-manual
- Documentation Pydantic Settings: https://docs.pydantic.dev/latest/concepts/pydantic_settings/

## 🎯 Prochaines étapes

Après migration:
1. ✅ Ajouter des tests unitaires
2. ✅ Configurer CI/CD
3. ✅ Ajouter monitoring (Prometheus/Grafana)
4. ✅ Documentation API complète
5. ✅ Déploiement Docker/Kubernetes