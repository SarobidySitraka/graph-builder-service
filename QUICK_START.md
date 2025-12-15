# Quick Start Guide 🚀

Guide rapide pour démarrer avec le Graph Builder Service en 5 minutes.

## 📋 Prérequis

- Python 3.11+
- Neo4j 5.15+ (ou Docker)
- Git

## 🎯 Méthode 1: Nouveau Projet (Recommandé)

### 1. Cloner et Setup

```bash
# Cloner le repository
git clone https://github.com/your-org/graph-builder-service.git
cd graph-builder-service

# Rendre le script exécutable
chmod +x scripts/setup.sh

# Lancer le setup automatique
./scripts/setup.sh
```

### 2. Configuration

```bash
# Éditer .env avec vos credentials
nano .env

# Variables essentielles à configurer:
# NEO4J_URI=bolt://localhost:7687
# NEO4J_USERNAME=neo4j
# NEO4J_PASSWORD=votre-mot-de-passe
# SECRET_KEY=votre-clé-secrète-unique
# API_KEY=votre-api-key
```

### 3. Démarrer Neo4j (avec Docker)

```bash
# Option A: Avec docker-compose (tout-en-un)
make docker-up

# Option B: Neo4j seulement
docker run -d \
  --name neo4j \
  -p 7474:7474 -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/votre-mot-de-passe \
  neo4j:5.15-community
```

### 4. Lancer le service

```bash
# Développement (avec auto-reload)
make dev

# Production
make run-prod
```

### 5. Tester

```bash
# Health check
curl http://localhost:8000/health

# Documentation interactive
open http://localhost:8000/docs
```

---

## 🔄 Méthode 2: Migration Projet Existant

### 1. Sauvegarder votre projet actuel

```bash
cp -r ingestion-service ingestion-service.backup
```

### 2. Lancer la migration automatique

```bash
# Télécharger le script
curl -O https://raw.githubusercontent.com/your-org/graph-builder-service/main/scripts/migrate_project.sh

# Rendre exécutable
chmod +x migrate_project.sh

# Lancer la migration
./migrate_project.sh
```

### 3. Copier les fichiers optimisés

Copiez les fichiers depuis les artifacts Claude dans votre nouveau projet :

```bash
cd graph-builder-service

# Core files
cp artifacts/core_config.py app/core/config.py
cp artifacts/core_logging.py app/core/logging.py

# Main application
cp artifacts/main_production.py app/main.py

# API files
cp artifacts/api_dependencies.py app/api/dependencies.py
cp artifacts/api_v1_router.py app/api/v1/router.py

# Endpoints
cp artifacts/files_router.py app/api/v1/endpoints/files.py
cp artifacts/databases_router.py app/api/v1/endpoints/databases.py
cp artifacts/sessions_router.py app/api/v1/endpoints/sessions.py
cp artifacts/graph_builder_router.py app/api/v1/endpoints/graph_builder.py
cp artifacts/health_endpoint.py app/api/v1/endpoints/health.py

# Services
cp artifacts/session_manager_fixed.py app/services/session_manager.py
```

### 4. Installer et configurer

```bash
# Installer les dépendances
make install

# Configurer l'environnement
cp .env.example .env
nano .env  # Éditer avec vos credentials
```

### 5. Tester la migration

```bash
# Test des imports
python3 -c "from app.main import app; print('✓ OK')"

# Lancer en mode dev
make dev

# Vérifier les endpoints
curl http://localhost:8000/health
curl http://localhost:8000/api/v1/health/detailed
```

---

## 🐳 Méthode 3: Docker (Production)

### Setup complet avec Docker

```bash
# 1. Cloner le projet
git clone https://github.com/your-org/graph-builder-service.git
cd graph-builder-service

# 2. Configuration
cp .env.example .env
nano .env

# 3. Build et démarrage
make docker-build
make docker-up

# 4. Vérification
curl http://localhost:8000/health

# Logs en temps réel
make docker-logs

# Arrêt
make docker-down
```

---

## 📚 Commandes Utiles

### Développement

```bash
# Démarrer le serveur dev
make dev

# Lancer les tests
make test

# Tests avec couverture
make test-cov

# Formater le code
make format

# Vérifier le code
make lint
```

### Docker

```bash
# Build l'image
make docker-build

# Démarrer les containers
make docker-up

# Arrêter les containers
make docker-down

# Voir les logs
make docker-logs

# Shell dans le container
make docker-shell
```

### Utilitaires

```bash
# Nettoyer cache et fichiers temporaires
make clean

# Backup Neo4j
make db-backup

# Health check
make health-check

# Initialiser Neo4j
make init-neo4j
```

---

## 🧪 Tester les Endpoints

### 1. Upload d'un fichier CSV

```bash
curl -X POST "http://localhost:8000/api/v1/files/upload_file" \
  -H "accept: application/json" \
  -F "files=@data/samples/customs_data.csv"
```

### 2. Connexion base de données

```bash
curl -X POST "http://localhost:8000/api/v1/databases/test_connection" \
  -H "Content-Type: application/json" \
  -d '{
    "db_type": "mysql",
    "host": "localhost",
    "port": 3306,
    "db": "mydb",
    "user": "root",
    "password": "password"
  }'
```

### 3. Lister les sessions

```bash
curl "http://localhost:8000/api/v1/sessions/list"
```

### 4. Health check détaillé

```bash
curl "http://localhost:8000/api/v1/health/detailed"
```

---

## 🐛 Dépannage Rapide

### Le serveur ne démarre pas

```bash
# Vérifier Python version
python3 --version  # Doit être >= 3.11

# Vérifier les dépendances
make install

# Vérifier .env
cat .env | grep NEO4J

# Tester les imports
python3 -c "from app.main import app"
```

### Neo4j ne se connecte pas

```bash
# Vérifier que Neo4j tourne
docker ps | grep neo4j

# Tester la connexion
python3 -c "
from neo4j import GraphDatabase
driver = GraphDatabase.driver('bolt://localhost:7687', auth=('neo4j', 'password'))
driver.verify_connectivity()
print('✓ Connexion OK')
"
```

### Port 8000 déjà utilisé

```bash
# Trouver le processus
lsof -i :8000

# Tuer le processus
kill -9 <PID>

# Ou utiliser un autre port
uv run uvicorn app.main:app --port 8080
```

---

## 📞 Support

- 📖 Documentation: `/docs` quand le serveur tourne
- 🐛 Issues: [GitHub Issues](https://github.com/your-org/graph-builder-service/issues)
- 💬 Discord: [Rejoindre](https://discord.gg/example)
- 📧 Email: support@example.com

---

## ✅ Checklist de Démarrage

- [ ] Python 3.11+ installé
- [ ] UV installé
- [ ] Dépendances installées (`make install`)
- [ ] `.env` configuré
- [ ] Neo4j lancé et accessible
- [ ] Serveur démarre (`make dev`)
- [ ] `/health` répond
- [ ] `/docs` accessible
- [ ] Upload de fichier fonctionne
- [ ] Tests passent (`make test`)

---

**🎉 Prêt à construire des graphes ! 🎉**