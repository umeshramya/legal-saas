# Legal Analysis SAAS Deployment Guide

## Table of Contents
1. [Architecture Overview](#architecture-overview)
2. [PostgreSQL Configuration](#postgresql-configuration)
3. [Redis Configuration](#redis-configuration)
4. [Docker Deployment](#docker-deployment)
5. [Cloud Platform Deployment](#cloud-platform-deployment)
6. [VPS Deployment (Hostinger, DigitalOcean, etc.)](#vps-deployment-hostinger-digitalocean-etc)
7. [Environment Variables](#environment-variables)
8. [Database Migration & Backup](#database-migration--backup)
9. [Scaling Considerations](#scaling-considerations)
10. [Monitoring & Maintenance](#monitoring--maintenance)
11. [Troubleshooting](#troubleshooting)

## Architecture Overview

Legal Analysis SAAS is a multi-service application with the following components:

### Core Services
1. **FastAPI Application** (`app`): Main API server (Port 8000)
2. **PostgreSQL** (`postgres`): Primary database (Port 5432)
3. **Redis** (`redis`): Cache and task queue (Port 6379)
4. **Celery Worker** (`celery-worker`): Background task processing
5. **Celery Beat** (`celery-beat`): Scheduled tasks

### Technology Stack
- **Backend**: FastAPI (Python 3.11+)
- **Database**: PostgreSQL 15+ with asyncpg driver
- **Cache/Task Queue**: Redis 7+
- **Task Processing**: Celery 5.3+
- **Containerization**: Docker & Docker Compose
- **OCR**: Tesseract OCR 5+

## PostgreSQL Configuration

### Current Implementation
The project uses PostgreSQL as the primary database with the following setup:

**Database Models** (`src/database/models.py`):
- `User`: Authentication and user management
- `Team`, `TeamMember`: Collaboration features
- `Case`, `Document`: Legal case management
- `Analysis`: AI analysis results
- `SearchQuery`, `AuditLog`: Search history and security

**Connection Settings** (`src/database/database.py`):
- Async SQLAlchemy with `create_async_engine`
- Connection pooling with `pool_pre_ping=True`
- Auto-creation of tables on startup via `init_db()`

### Production PostgreSQL Configuration

#### 1. **Database Optimization**
```sql
-- Run these commands in your PostgreSQL database
ALTER DATABASE legal_analysis SET maintenance_work_mem = '256MB';
ALTER DATABASE legal_analysis SET work_mem = '16MB';
ALTER DATABASE legal_analysis SET shared_buffers = '256MB';
ALTER DATABASE legal_analysis SET effective_cache_size = '1GB';
```

#### 2. **Connection Pooling**
Configure in `src/database/database.py`:
```python
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    pool_size=20,  # Increased for production
    max_overflow=30,
    pool_pre_ping=True,
    pool_recycle=3600,
)
```

#### 3. **Database Backups**
```bash
# Daily backup script (save as backup.sh)
#!/bin/bash
BACKUP_DIR="/backups/postgres"
DATE=$(date +%Y%m%d_%H%M%S)
pg_dump -U postgres legal_analysis | gzip > "$BACKUP_DIR/backup_$DATE.sql.gz"
# Keep last 30 days
find "$BACKUP_DIR" -name "*.sql.gz" -mtime +30 -delete
```

## Redis Configuration

### Current Status
Redis is configured in settings but **not fully implemented** in the current codebase.

### Planned Redis Usage

#### 1. **Session Management**
```python
# src/database/redis.py (to be created)
import redis.asyncio as redis
from src.config import settings

redis_client = redis.from_url(
    settings.REDIS_URL,
    encoding="utf-8",
    decode_responses=True,
    max_connections=20
)
```

#### 2. **Caching Layer**
```python
# Cache Indian Kanoon API responses (src/services/kanoon_service.py)
async def search_documents(self, query: str, use_cache: bool = True):
    cache_key = f"kanoon_search:{hash(query)}"
    if use_cache:
        cached = await redis_client.get(cache_key)
        if cached:
            return json.loads(cached)

    # API call
    result = await self._make_api_call(query)

    # Cache for 1 hour
    await redis_client.setex(cache_key, 3600, json.dumps(result))
    return result
```

#### 3. **Task Queue for Celery**
Configure Celery to use Redis as broker:
```python
# src/tasks/celery_app.py (to be created)
from celery import Celery
from src.config import settings

celery_app = Celery(
    "legal_saas",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=["src.tasks.document_tasks", "src.tasks.ai_tasks"]
)
```

### Redis Production Configuration

#### 1. **Redis Persistence**
Enable AOF (Append Only File) for data durability:
```redis
# In redis.conf or via CONFIG command
appendonly yes
appendfsync everysec
```

#### 2. **Memory Management**
```redis
# Set memory limits
maxmemory 1gb
maxmemory-policy allkeys-lru
```

#### 3. **Redis Security**
```redis
# Require password authentication
requirepass "your-strong-password-here"

# Rename dangerous commands
rename-command FLUSHDB ""
rename-command FLUSHALL ""
rename-command CONFIG ""
```

## Docker Deployment

### 1. **Local Development**
```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f app

# Stop services
docker-compose down
```

### 2. **Production Docker Compose**
Create `docker-compose.prod.yml`:
```yaml
version: '3.8'

services:
  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: legal_analysis
      POSTGRES_USER: ${DB_USER}
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./backups:/backups
    restart: unless-stopped
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${DB_USER}"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    command: redis-server --requirepass ${REDIS_PASSWORD} --appendonly yes
    volumes:
      - redis_data:/data
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "redis-cli", "-a", "${REDIS_PASSWORD}", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  app:
    build:
      context: .
      dockerfile: Dockerfile.prod
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    environment:
      DATABASE_URL: postgresql+asyncpg://${DB_USER}:${DB_PASSWORD}@postgres:5432/legal_analysis
      REDIS_URL: redis://:${REDIS_PASSWORD}@redis:6379/0
      DEBUG: "false"
    ports:
      - "8000:8000"
    volumes:
      - uploads:/app/uploads
    restart: unless-stopped

  celery-worker:
    build:
      context: .
      dockerfile: Dockerfile.prod
    depends_on:
      - redis
      - postgres
    environment:
      DATABASE_URL: postgresql+asyncpg://${DB_USER}:${DB_PASSWORD}@postgres:5432/legal_analysis
      REDIS_URL: redis://:${REDIS_PASSWORD}@redis:6379/0
    command: celery -A src.tasks.celery_app worker --loglevel=info --concurrency=4
    restart: unless-stopped

  celery-beat:
    build:
      context: .
      dockerfile: Dockerfile.prod
    depends_on:
      - redis
      - postgres
    environment:
      DATABASE_URL: postgresql+asyncpg://${DB_USER}:${DB_PASSWORD}@postgres:5432/legal_analysis
      REDIS_URL: redis://:${REDIS_PASSWORD}@redis:6379/0
    command: celery -A src.tasks.celery_app beat --loglevel=info
    restart: unless-stopped

volumes:
  postgres_data:
  redis_data:
  uploads:
```

### 3. **Production Dockerfile**
Create `Dockerfile.prod`:
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies including Tesseract
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    libtesseract-dev \
    poppler-utils \
    libmagic1 \
    tesseract-ocr-eng \
    tesseract-ocr-hin \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"

# Run with production settings
CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
```

## Cloud Platform Deployment

### AWS Deployment

#### Option 1: ECS/EKS (Recommended)
```bash
# Build and push Docker image
docker build -t legal-analysis-saas .
docker tag legal-analysis-saas:latest your-account-id.dkr.ecr.region.amazonaws.com/legal-analysis-saas:latest
docker push your-account-id.dkr.ecr.region.amazonaws.com/legal-analysis-saas:latest

# Use AWS RDS for PostgreSQL and ElastiCache for Redis
```

#### Option 2: EC2 with Docker Compose
```bash
# Install Docker on EC2
sudo apt-get update
sudo apt-get install docker.io docker-compose

# Clone and deploy
git clone https://github.com/your-repo/legal-saas.git
cd legal-saas
sudo docker-compose -f docker-compose.prod.yml up -d
```

#### Option 3: Elastic Beanstalk
```bash
# Create requirements.txt for Elastic Beanstalk
# Add platform-specific dependencies
echo "tesseract-ocr" > Aptfile
echo "libtesseract-dev" >> Aptfile
echo "poppler-utils" >> Aptfile

# Deploy using EB CLI
eb init -p python-3.11 legal-saas
eb create legal-saas-prod
```

### Google Cloud Platform (GCP)

#### Option 1: Cloud Run with Cloud SQL and Memorystore
```bash
# Build and push to Google Container Registry
gcloud builds submit --tag gcr.io/your-project/legal-analysis-saas

# Deploy to Cloud Run with environment variables
gcloud run deploy legal-analysis-saas \
  --image gcr.io/your-project/legal-analysis-saas \
  --platform managed \
  --region us-central1 \
  --set-env-vars="DATABASE_URL=your-cloudsql-connection-string" \
  --set-env-vars="REDIS_URL=your-memorystore-connection-string"
```

#### Option 2: GKE (Google Kubernetes Engine)
```yaml
# deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: legal-saas
spec:
  replicas: 3
  selector:
    matchLabels:
      app: legal-saas
  template:
    metadata:
      labels:
        app: legal-saas
    spec:
      containers:
      - name: app
        image: gcr.io/your-project/legal-analysis-saas
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: database-secret
              key: connection-string
```

### Microsoft Azure

#### Option 1: Azure Container Instances with Azure Database for PostgreSQL and Azure Cache for Redis
```bash
# Build and push to Azure Container Registry
az acr build --registry yourregistry --image legal-analysis-saas:latest .

# Deploy with environment variables
az container create \
  --resource-group your-rg \
  --name legal-saas \
  --image yourregistry.azurecr.io/legal-analysis-saas:latest \
  --environment-variables \
    DATABASE_URL="your-postgres-connection-string" \
    REDIS_URL="your-redis-connection-string"
```

#### Option 2: Azure App Service with Containers
```bash
# Create App Service with container
az webapp create \
  --resource-group your-rg \
  --plan your-app-service-plan \
  --name legal-saas-app \
  --deployment-container-image-name yourregistry.azurecr.io/legal-analysis-saas:latest
```

### Render.com

#### 1. **Database Setup**
- Use Render PostgreSQL database
- Get connection string from Render dashboard

#### 2. **Redis Setup**
- Use Render Redis instance
- Get connection string from Render dashboard

#### 3. **Web Service Setup**
```yaml
# render.yaml
services:
  - type: web
    name: legal-saas
    env: python
    buildCommand: pip install -r requirements.txt
    startCommand: uvicorn src.api.main:app --host 0.0.0.0 --port $PORT
    envVars:
      - key: DATABASE_URL
        fromDatabase:
          name: legal-analysis-db
          property: connectionString
      - key: REDIS_URL
        fromService:
          name: legal-analysis-redis
          type: redis
          property: connectionString
      - key: PYTHON_VERSION
        value: 3.11.0
```

### Railway.app

#### 1. **Deploy with PostgreSQL Plugin**
```bash
# Install Railway CLI
npm i -g @railway/cli

# Deploy project
railway up

# Add PostgreSQL plugin
railway add postgresql

# Add Redis plugin
railway add redis

# Set environment variables
railway variables set DATABASE_URL=$DATABASE_URL
railway variables set REDIS_URL=$REDIS_URL
```

### Heroku

#### 1. **Using Docker**
```bash
# Login to Heroku Container Registry
heroku container:login

# Create Heroku app
heroku create legal-saas

# Add Heroku PostgreSQL
heroku addons:create heroku-postgresql:hobby-dev

# Add Heroku Redis
heroku addons:create heroku-redis:hobby-dev

# Build and push
heroku container:push web

# Release
heroku container:release web
```

#### 2. **Using Buildpacks**
```bash
# Add Aptfile for system dependencies
echo "tesseract-ocr" > Aptfile
echo "libtesseract-dev" >> Aptfile
echo "poppler-utils" >> Aptfile

# Set buildpacks
heroku buildpacks:add heroku/python
heroku buildpacks:add heroku-community/apt

# Set environment variables
heroku config:set DATABASE_URL=$(heroku config:get DATABASE_URL)
heroku config:set REDIS_URL=$(heroku config:get REDIS_URL)
```

## VPS Deployment (Hostinger, DigitalOcean, Linode, etc.)

### 1. **Basic VPS Setup**

```bash
# Update system
sudo apt-get update
sudo apt-get upgrade -y

# Install Docker and Docker Compose
sudo apt-get install docker.io docker-compose -y

# Create project directory
sudo mkdir -p /opt/legal-saas
cd /opt/legal-saas
```

### 2. **Install PostgreSQL and Redis (Without Docker)**

```bash
# Install PostgreSQL
sudo apt-get install postgresql postgresql-contrib -y

# Create database and user
sudo -u postgres psql -c "CREATE DATABASE legal_analysis;"
sudo -u postgres psql -c "CREATE USER legal_user WITH PASSWORD 'strong_password';"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE legal_analysis TO legal_user;"

# Install Redis
sudo apt-get install redis-server -y

# Configure Redis password
sudo nano /etc/redis/redis.conf
# Add: requirepass your_redis_password
# Change: bind 0.0.0.0 (or specific IP)
sudo systemctl restart redis
```

### 3. **Install Python and Dependencies**

```bash
# Install Python 3.11
sudo apt-get install python3.11 python3.11-venv python3.11-dev -y

# Install Tesseract OCR
sudo apt-get install tesseract-ocr libtesseract-dev poppler-utils -y

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate

# Install Python dependencies
pip install -r requirements.txt
```

### 4. **Configure Systemd Services**

**Create `/etc/systemd/system/legal-saas.service`:**
```ini
[Unit]
Description=Legal Analysis SAAS
After=network.target postgresql.service redis-server.service

[Service]
Type=simple
User=www-data
WorkingDirectory=/opt/legal-saas
Environment="PATH=/opt/legal-saas/venv/bin"
Environment="DATABASE_URL=postgresql+asyncpg://legal_user:password@localhost:5432/legal_analysis"
Environment="REDIS_URL=redis://:your_redis_password@localhost:6379/0"
Environment="DEEPSEEK_API_KEY=your_api_key"
ExecStart=/opt/legal-saas/venv/bin/uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --workers 4
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**Create `/etc/systemd/system/celery-worker.service`:**
```ini
[Unit]
Description=Celery Worker for Legal SAAS
After=network.target redis-server.service

[Service]
Type=simple
User=www-data
WorkingDirectory=/opt/legal-saas
Environment="PATH=/opt/legal-saas/venv/bin"
Environment="DATABASE_URL=postgresql+asyncpg://legal_user:password@localhost:5432/legal_analysis"
Environment="REDIS_URL=redis://:your_redis_password@localhost:6379/0"
ExecStart=/opt/legal-saas/venv/bin/celery -A src.tasks.celery_app worker --loglevel=info --concurrency=4
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### 5. **Configure Nginx as Reverse Proxy**

```bash
# Install Nginx
sudo apt-get install nginx -y

# Configure site
sudo nano /etc/nginx/sites-available/legal-saas
```

**Nginx Configuration:**
```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # WebSocket support
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }

    # File uploads
    client_max_body_size 50M;

    # Static files (if any)
    location /static/ {
        alias /opt/legal-saas/static/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    location /uploads/ {
        alias /opt/legal-saas/uploads/;
        expires 30d;
        add_header Cache-Control "public";
    }
}
```

```bash
# Enable site
sudo ln -s /etc/nginx/sites-available/legal-saas /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### 6. **SSL with Let's Encrypt**

```bash
# Install Certbot
sudo apt-get install certbot python3-certbot-nginx -y

# Get SSL certificate
sudo certbot --nginx -d your-domain.com

# Auto-renewal setup
sudo certbot renew --dry-run
```

### 7. **Firewall Configuration**

```bash
# Configure UFW firewall
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

## Environment Variables

### Required Variables
```env
# Database
DATABASE_URL=postgresql+asyncpg://username:password@host:5432/database_name

# Redis
REDIS_URL=redis://:password@host:6379/0

# AI Services
DEEPSEEK_API_KEY=your_deepseek_api_key
DEEPSEEK_BASE_URL=https://api.deepseek.com

# Indian Kanoon (Optional)
INDIAN_KANOON_API_KEY=your_indian_kanoon_api_key

# JWT Authentication
JWT_SECRET_KEY=your_secure_jwt_secret_key
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7

# Application Settings
DEBUG=false
MAX_UPLOAD_SIZE_MB=50
ALLOWED_ORIGINS=["http://localhost:3000", "https://your-domain.com"]

# OCR Configuration
TESSERACT_PATH=/usr/bin/tesseract  # Auto-detected if not set
OCR_ENABLED=true
MAX_OCR_THREADS=3
```

### Platform-Specific Examples

**AWS RDS Connection:**
```env
DATABASE_URL=postgresql+asyncpg://username:password@your-rds-endpoint.rds.amazonaws.com:5432/legal_analysis
```

**Google Cloud SQL Connection:**
```env
DATABASE_URL=postgresql+asyncpg://username:password@/legal_analysis?host=/cloudsql/your-project:region:instance-name
```

**Azure Database for PostgreSQL:**
```env
DATABASE_URL=postgresql+asyncpg://username@server-name:password@server-name.postgres.database.azure.com:5432/legal_analysis
```

## Database Migration & Backup

### 1. **Alembic Migrations (Recommended)**
```bash
# Install Alembic
pip install alembic

# Initialize
alembic init alembic

# Configure alembic.ini
sqlalchemy.url = postgresql+asyncpg://username:password@localhost/legal_analysis

# Create migration
alembic revision --autogenerate -m "Initial migration"

# Apply migration
alembic upgrade head
```

### 2. **Manual Backup Strategy**
```bash
#!/bin/bash
# backup.sh
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backups"

# PostgreSQL backup
pg_dump -U postgres legal_analysis | gzip > "$BACKUP_DIR/postgres_$DATE.sql.gz"

# Redis backup (if using RDB)
redis-cli SAVE
cp /var/lib/redis/dump.rdb "$BACKUP_DIR/redis_$DATE.rdb"

# Upload to cloud storage (AWS S3 example)
aws s3 cp "$BACKUP_DIR/postgres_$DATE.sql.gz" s3://your-bucket/backups/
aws s3 cp "$BACKUP_DIR/redis_$DATE.rdb" s3://your-bucket/backups/

# Clean old backups (keep 30 days)
find "$BACKUP_DIR" -name "*.sql.gz" -mtime +30 -delete
find "$BACKUP_DIR" -name "*.rdb" -mtime +30 -delete
```

### 3. **Database Restoration**
```bash
# Restore PostgreSQL
gunzip -c backup.sql.gz | psql -U postgres legal_analysis

# Restore Redis
systemctl stop redis
cp backup.rdb /var/lib/redis/dump.rdb
systemctl start redis
```

## Scaling Considerations

### 1. **Database Scaling**
- **Read Replicas**: For read-heavy operations
- **Connection Pooling**: Use PgBouncer or connection pooler
- **Index Optimization**: Regular index maintenance

### 2. **Application Scaling**
- **Horizontal Scaling**: Multiple app instances behind load balancer
- **Stateless Design**: Store sessions in Redis, not local memory
- **CDN for Static Files**: Use Cloudflare or similar for uploads

### 3. **Redis Scaling**
- **Redis Cluster**: For high availability
- **Redis Sentinel**: For automatic failover
- **Memory Optimization**: Use data compression techniques

### 4. **File Storage Scaling**
- **Object Storage**: Use S3, GCS, or Azure Blob Storage for uploads
- **CDN Integration**: Serve processed documents via CDN

## Monitoring & Maintenance

### 1. **Health Checks**
```bash
# Database health
pg_isready -U postgres

# Redis health
redis-cli ping

# Application health
curl http://localhost:8000/health
```

### 2. **Logging Configuration**
```python
# src/config/logging.py
import logging
from logging.handlers import RotatingFileHandler

def setup_logging():
    handler = RotatingFileHandler(
        'app.log',
        maxBytes=10485760,  # 10MB
        backupCount=10
    )
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    handler.setFormatter(formatter)

    logger = logging.getLogger()
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
```

### 3. **Performance Monitoring**
- **PostgreSQL**: pg_stat_statements, pgBadger
- **Redis**: redis-cli --stat, RedisInsight
- **Application**: Prometheus + Grafana, Datadog

### 4. **Regular Maintenance Tasks**
```bash
# Weekly PostgreSQL maintenance
psql -U postgres -c "VACUUM ANALYZE;"

# Monthly index reindex
psql -U postgres -c "REINDEX DATABASE legal_analysis;"

# Redis memory optimization
redis-cli MEMORY PURGE
```

## Troubleshooting

### Common Issues and Solutions

#### 1. **Database Connection Issues**
```bash
# Check PostgreSQL is running
systemctl status postgresql

# Check connection from app
psql -U postgres -h localhost -d legal_analysis

# Check max connections
psql -U postgres -c "SHOW max_connections;"
```

#### 2. **Redis Connection Issues**
```bash
# Check Redis is running
systemctl status redis

# Test connection
redis-cli ping

# Check memory usage
redis-cli info memory
```

#### 3. **OCR/Tesseract Issues**
```bash
# Verify Tesseract installation
tesseract --version

# Test OCR
python -c "
import pytesseract
from PIL import Image
img = Image.new('RGB', (100, 50), color='white')
print(pytesseract.image_to_string(img))
"

# Check Tesseract path
python -c "import pytesseract; print(pytesseract.pytesseract.tesseract_cmd)"
```

#### 4. **Application Performance Issues**
```bash
# Check system resources
htop
free -h

# Check application logs
journalctl -u legal-saas -f

# Check database performance
psql -U postgres -c "SELECT * FROM pg_stat_activity WHERE state = 'active';"
```

#### 5. **File Upload Issues**
```bash
# Check disk space
df -h

# Check upload directory permissions
ls -la /opt/legal-saas/uploads/

# Check Nginx client body size
grep client_max_body_size /etc/nginx/nginx.conf
```

### Emergency Procedures

#### 1. **Database Recovery**
```bash
# Stop application
systemctl stop legal-saas

# Restore from backup
gunzip -c latest_backup.sql.gz | psql -U postgres legal_analysis

# Start application
systemctl start legal-saas
```

#### 2. **Redis Data Loss**
```bash
# Restore from RDB file
systemctl stop redis
cp backup.rdb /var/lib/redis/dump.rdb
systemctl start redis
```

#### 3. **Application Rollback**
```bash
# Revert to previous Docker image
docker-compose pull
docker-compose up -d --force-recreate

# Or revert git commit
git checkout previous-commit-hash
docker-compose build
docker-compose up -d
```

## Security Best Practices

### 1. **Network Security**
- Use VPC/private networking for database and Redis
- Restrict database access to application servers only
- Use SSL/TLS for all connections

### 2. **Authentication & Authorization**
- Rotate API keys and JWT secrets regularly
- Implement rate limiting on authentication endpoints
- Use strong password policies

### 3. **Data Protection**
- Encrypt sensitive data at rest
- Implement data retention policies
- Regular security audits and penetration testing

### 4. **Compliance Considerations**
- **GDPR**: Implement data deletion requests
- **HIPAA**: If handling health-related legal cases
- **Local Regulations**: Comply with Indian data protection laws

## Support and Resources

### Official Documentation
- **FastAPI**: https://fastapi.tiangolo.com
- **SQLAlchemy**: https://docs.sqlalchemy.org
- **Redis**: https://redis.io/documentation
- **Celery**: https://docs.celeryq.dev

### Monitoring Tools
- **PostgreSQL**: pgAdmin, DBeaver, DataGrip
- **Redis**: RedisInsight, Redmon
- **Application**: Grafana, Prometheus, New Relic

### Deployment Platforms Documentation
- **AWS**: https://docs.aws.amazon.com
- **Google Cloud**: https://cloud.google.com/docs
- **Azure**: https://docs.microsoft.com/azure
- **Docker**: https://docs.docker.com

---

*This deployment guide is maintained as part of the Legal Analysis SAAS project. For updates and latest recommendations, refer to the project repository.*