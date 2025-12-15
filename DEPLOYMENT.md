# Deployment Guide 🚀

Complete guide for deploying Graph Builder Service to production.

## 📋 Pre-Deployment Checklist

- [ ] All tests pass (`make test`)
- [ ] Code is linted (`make lint`)
- [ ] `.env` configured with production values
- [ ] Secret keys generated and secured
- [ ] Neo4j database provisioned
- [ ] Backup strategy in place
- [ ] Monitoring configured
- [ ] SSL certificates obtained (if applicable)

---

## 🐳 Docker Deployment

### 1. Build Docker Image

```bash
# Build production image
docker build -t graph-builder-service:latest -f docker/Dockerfile .

# Or using make
make docker-build

# Tag for registry
docker tag graph-builder-service:latest your-registry.com/graph-builder-service:v0.1.0
```

### 2. Push to Registry

```bash
# Login to registry
docker login your-registry.com

# Push image
docker push your-registry.com/graph-builder-service:v0.1.0
```

### 3. Run with Docker Compose

```bash
# Start full stack (recommended for production)
docker-compose -f docker/docker-compose.yml up -d

# Check logs
docker-compose -f docker/docker-compose.yml logs -f

# Stop services
docker-compose -f docker/docker-compose.yml down
```

### 4. Environment Configuration

Create `.env.production`:

```bash
# Application
APP_NAME=GraphBuilderService
DEBUG=false
ENVIRONMENT=production
LOG_LEVEL=INFO

# Neo4j (use strong passwords!)
NEO4J_URI=bolt://neo4j:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=<strong-password>

# Security
SECRET_KEY=<generate-with: openssl rand -hex 32>
API_KEY=<generate-with: openssl rand -hex 32>

# CORS (adjust for your domain)
CORS_ORIGINS=https://your-domain.com

# Database connections (if needed)
MYSQL_PASSWORD=<strong-password>
POSTGRES_PASSWORD=<strong-password>
```

Generate secrets:

```bash
openssl rand -hex 32  # For SECRET_KEY
openssl rand -hex 32  # For API_KEY
```

---

## ☸️ Kubernetes Deployment

### 1. Create Namespace

```bash
kubectl create namespace graph-builder
```

### 2. Create Secrets

```bash
# Create secret from .env file
kubectl create secret generic graph-builder-secrets \
  --from-env-file=.env.production \
  --namespace=graph-builder

# Or manually
kubectl create secret generic graph-builder-secrets \
  --from-literal=neo4j-password=your-password \
  --from-literal=secret-key=your-secret-key \
  --from-literal=api-key=your-api-key \
  --namespace=graph-builder
```

### 3. Apply Configurations

```bash
# Apply all manifests
kubectl apply -f k8s/ --namespace=graph-builder

# Or individually
kubectl apply -f k8s/configmap.yaml --namespace=graph-builder
kubectl apply -f k8s/secrets.yaml --namespace=graph-builder
kubectl apply -f k8s/deployment.yaml --namespace=graph-builder
kubectl apply -f k8s/service.yaml --namespace=graph-builder
kubectl apply -f k8s/ingress.yaml --namespace=graph-builder
```

### 4. Verify Deployment

```bash
# Check pods
kubectl get pods --namespace=graph-builder

# Check services
kubectl get services --namespace=graph-builder

# Check logs
kubectl logs -f deployment/graph-builder-service --namespace=graph-builder

# Check events
kubectl get events --namespace=graph-builder --sort-by='.lastTimestamp'
```

### 5. Scale Deployment

```bash
# Scale to 3 replicas
kubectl scale deployment graph-builder-service --replicas=3 --namespace=graph-builder

# Autoscaling
kubectl autoscale deployment graph-builder-service \
  --cpu-percent=70 \
  --min=2 \
  --max=10 \
  --namespace=graph-builder
```

---

## 🌐 Manual Deployment (VPS/VM)

### 1. System Requirements

- Ubuntu 20.04+ or CentOS 8+
- Python 3.11+
- 4GB RAM minimum (8GB recommended)
- 20GB disk space

### 2. Install Dependencies

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python 3.11
sudo apt install -y software-properties-common
sudo add-apt-repository ppa:deadsnakes/ppa
sudo apt install -y python3.11 python3.11-venv python3.11-dev

# Install system dependencies
sudo apt install -y build-essential libpq-dev curl git

# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### 3. Setup Application

```bash
# Create app user
sudo useradd -m -s /bin/bash appuser

# Clone repository
sudo -u appuser git clone https://github.com/your-org/graph-builder-service.git /home/appuser/app
cd /home/appuser/app

# Create virtual environment
sudo -u appuser uv venv

# Install dependencies
sudo -u appuser uv pip install -e .
```

### 4. Configure Environment

```bash
# Copy environment file
sudo -u appuser cp .env.example .env
sudo -u appuser nano .env

# Set proper permissions
sudo chmod 600 .env
```

### 5. Setup Systemd Service

Create `/etc/systemd/system/graph-builder.service`:

```ini
[Unit]
Description=Graph Builder Service
After=network.target

[Service]
Type=simple
User=appuser
WorkingDirectory=/home/appuser/app
Environment="PATH=/home/appuser/app/.venv/bin"
ExecStart=/home/appuser/app/.venv/bin/uvicorn app.main:app \
    --host 0.0.0.0 \
    --port 8000 \
    --workers 4

Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start:

```bash
sudo systemctl daemon-reload
sudo systemctl enable graph-builder
sudo systemctl start graph-builder
sudo systemctl status graph-builder
```

### 6. Setup Nginx Reverse Proxy

Install Nginx:

```bash
sudo apt install -y nginx
```

Create `/etc/nginx/sites-available/graph-builder`:

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
      
        # WebSocket support
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
      
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # File upload size limit
    client_max_body_size 100M;
}
```

Enable site:

```bash
sudo ln -s /etc/nginx/sites-available/graph-builder /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### 7. Setup SSL with Let's Encrypt

```bash
# Install certbot
sudo apt install -y certbot python3-certbot-nginx

# Obtain certificate
sudo certbot --nginx -d your-domain.com

# Auto-renewal is configured automatically
```

---

## 📊 Monitoring & Logging

### 1. Application Logs

```bash
# View systemd logs
sudo journalctl -u graph-builder -f

# View application logs
tail -f /home/appuser/app/logs/app.log
tail -f /home/appuser/app/logs/error.log
```

### 2. Log Rotation

Create `/etc/logrotate.d/graph-builder`:

```
/home/appuser/app/logs/*.log {
    daily
    rotate 30
    compress
    delaycompress
    notifempty
    create 0640 appuser appuser
    sharedscripts
    postrotate
        systemctl reload graph-builder
    endscript
}
```

### 3. Health Monitoring

Setup cron job for health checks:

```bash
# Add to crontab
*/5 * * * * curl -f http://localhost:8000/health || systemctl restart graph-builder
```

---

## 🔐 Security Hardening

### 1. Firewall Configuration

```bash
# Allow SSH, HTTP, HTTPS
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Deny direct access to app port
sudo ufw deny 8000/tcp

# Enable firewall
sudo ufw enable
```

### 2. Fail2Ban

```bash
# Install
sudo apt install -y fail2ban

# Configure
sudo nano /etc/fail2ban/jail.local
```

Add:

```ini
[nginx-limit-req]
enabled = true
filter = nginx-limit-req
logpath = /var/log/nginx/error.log
maxretry = 10
findtime = 600
bantime = 7200
```

### 3. Regular Updates

```bash
# Setup automatic security updates
sudo apt install -y unattended-upgrades
sudo dpkg-reconfigure --priority=low unattended-upgrades
```

---

## 💾 Backup Strategy

### 1. Database Backup

```bash
# Neo4j backup script
cat > /home/appuser/backup-neo4j.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="/home/appuser/backups/neo4j"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR

# Backup Neo4j
docker exec neo4j neo4j-admin backup \
    --backup-dir=/backups \
    --name=backup-$DATE

# Compress
tar -czf $BACKUP_DIR/neo4j-backup-$DATE.tar.gz /var/lib/neo4j/data

# Keep only last 30 days
find $BACKUP_DIR -name "*.tar.gz" -mtime +30 -delete
EOF

chmod +x /home/appuser/backup-neo4j.sh
```

### 2. Automated Backups

```bash
# Add to crontab (daily at 2 AM)
0 2 * * * /home/appuser/backup-neo4j.sh
```

---

## 🔄 Rolling Updates

### Docker Compose

```bash
# Pull new image
docker-compose -f docker/docker-compose.yml pull

# Restart with zero downtime
docker-compose -f docker/docker-compose.yml up -d
```

### Kubernetes

```bash
# Update image
kubectl set image deployment/graph-builder-service \
  graph-builder-service=your-registry.com/graph-builder-service:v0.2.0 \
  --namespace=graph-builder

# Monitor rollout
kubectl rollout status deployment/graph-builder-service --namespace=graph-builder

# Rollback if needed
kubectl rollout undo deployment/graph-builder-service --namespace=graph-builder
```

---

## 🐛 Troubleshooting

### Service Won't Start

```bash
# Check logs
sudo journalctl -u graph-builder -n 100

# Check port availability
sudo netstat -tlnp | grep 8000

# Check file permissions
ls -la /home/appuser/app
```

### High Memory Usage

```bash
# Check memory
free -h

# Restart service
sudo systemctl restart graph-builder

# Reduce workers in production
# Edit: /etc/systemd/system/graph-builder.service
# Change --workers 4 to --workers 2
```

### Database Connection Issues

```bash
# Test Neo4j connection
docker exec -it neo4j cypher-shell -u neo4j -p password

# Check network
ping neo4j
telnet neo4j 7687
```

---

## 📞 Support

For deployment issues:

- 📖 Docs: `/docs` when service is running
- 🐛 Issues: [GitHub Issues](https://github.com/your-org/graph-builder-service/issues)
- 💬 Discord: [Join our server](https://discord.gg/example)

---

**Production deployment complete! 🎉**
