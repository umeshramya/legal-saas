# Quick Deployment Checklist

## For Detailed Instructions
Refer to the comprehensive [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) for complete deployment instructions across all platforms.

## 1. Choose Your Deployment Method

### 🐳 **Docker (Recommended)**
```bash
# Clone repository
git clone <your-repo>
cd legal-saas

# Copy environment file
cp .env.example .env
# Edit .env with your API keys and database credentials

# Start services
docker-compose up -d

# Check logs
docker-compose logs -f app
```

### ☁️ **Cloud Platforms (Quick Start)**
- **Render**: Deploy via GitHub with `render.yaml`
- **Railway**: `railway up` with PostgreSQL and Redis plugins
- **Heroku**: Deploy with Docker or buildpacks
- **AWS**: ECS/EKS with RDS and ElastiCache
- **Google Cloud**: Cloud Run with Cloud SQL and Memorystore

### 🖥️ **VPS (Hostinger, DigitalOcean, Linode)**
```bash
# Basic VPS setup
git clone <your-repo>
cd legal-saas

# Install dependencies
sudo apt-get update
sudo apt-get install docker.io docker-compose -y

# Deploy
sudo docker-compose -f docker-compose.prod.yml up -d
```

## 2. Environment Variables (Required)

Copy from `.env.example` and set:

### Essential Variables
```env
DATABASE_URL=postgresql+asyncpg://username:password@host:5432/database_name
REDIS_URL=redis://:password@host:6379/0
DEEPSEEK_API_KEY=your_deepseek_api_key
JWT_SECRET_KEY=your_secure_jwt_secret_key
```

### Optional Variables
```env
INDIAN_KANOON_API_KEY=your_indian_kanoon_api_key  # For Indian Kanoon integration
TESSERACT_PATH=/usr/bin/tesseract  # Only if Tesseract is in non-standard location
```

## 3. Database Setup

### PostgreSQL Required
- Version: 12+
- Database name: `legal_analysis`
- User with full permissions
- Connection pool: 20+ connections

### Redis Required
- Version: 7+
- Password authentication recommended
- Persistence enabled (AOF recommended)

## 4. Platform-Specific Quick Commands

### AWS ECS
```bash
# Build and push
docker build -t legal-analysis-saas .
docker tag legal-analysis-saas:latest your-account-id.dkr.ecr.region.amazonaws.com/legal-analysis-saas:latest
docker push your-account-id.dkr.ecr.region.amazonaws.com/legal-analysis-saas:latest

# Use ECS console to create service with RDS and ElastiCache
```

### Google Cloud Run
```bash
gcloud builds submit --tag gcr.io/your-project/legal-analysis-saas
gcloud run deploy legal-analysis-saas \
  --image gcr.io/your-project/legal-analysis-saas \
  --platform managed \
  --region us-central1 \
  --set-env-vars="DATABASE_URL=..." \
  --set-env-vars="REDIS_URL=..."
```

### Render
1. Connect GitHub repository
2. Add PostgreSQL and Redis services
3. Set environment variables
4. Deploy

### Railway
```bash
railway up
railway add postgresql
railway add redis
railway variables set DATABASE_URL=$DATABASE_URL
railway variables set REDIS_URL=$REDIS_URL
```

## 5. VPS with Systemd (Production)

### 1. Install Dependencies
```bash
sudo apt-get update
sudo apt-get install postgresql redis-server python3.11 python3.11-venv tesseract-ocr
```

### 2. Database Setup
```bash
sudo -u postgres psql -c "CREATE DATABASE legal_analysis;"
sudo -u postgres psql -c "CREATE USER legal_user WITH PASSWORD 'strong_password';"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE legal_analysis TO legal_user;"
```

### 3. Application Setup
```bash
# Clone and setup
git clone <your-repo> /opt/legal-saas
cd /opt/legal-saas
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Configure environment
cp .env.example .env
nano .env  # Edit with your settings
```

### 4. Systemd Services
```bash
# Copy service files from DEPLOYMENT_GUIDE.md
sudo nano /etc/systemd/system/legal-saas.service
sudo nano /etc/systemd/system/celery-worker.service

# Enable and start
sudo systemctl daemon-reload
sudo systemctl enable legal-saas celery-worker
sudo systemctl start legal-saas celery-worker
```

### 5. Nginx + SSL
```bash
sudo apt-get install nginx certbot python3-certbot-nginx
sudo nano /etc/nginx/sites-available/legal-saas
sudo ln -s /etc/nginx/sites-available/legal-saas /etc/nginx/sites-enabled/
sudo certbot --nginx -d your-domain.com
```

## 6. Verification Checklist

After deployment, verify:

### Health Check
```bash
curl http://your-domain.com/health
# Should return: {"status":"healthy","database":true,"redis":true,...}
```

### API Documentation
- Visit `http://your-domain.com/docs` for Swagger UI
- Visit `http://your-domain.com/redoc` for ReDoc

### Core Functionality Test
1. **File Upload**: POST to `/process/file` with a PDF
2. **AI Analysis**: POST to `/analyze/document` with text
3. **Kanoon Search**: POST to `/search/kanoon` with query (if API key configured)

## 7. Troubleshooting Quick Tips

### Application Won't Start
```bash
# Check logs
docker-compose logs app
# or
journalctl -u legal-saas -f

# Check database connection
psql "postgresql://username:password@host:5432/legal_analysis"
```

### Database Connection Errors
1. Verify `DATABASE_URL` is correct
2. Check PostgreSQL is running: `systemctl status postgresql`
3. Check firewall: Allow port 5432

### Redis Connection Errors
1. Verify `REDIS_URL` is correct
2. Check Redis is running: `systemctl status redis`
3. Test connection: `redis-cli ping`

### OCR/Tesseract Issues
```bash
# Verify installation
tesseract --version

# Test in Python
python -c "import pytesseract; print(pytesseract.get_tesseract_version())"
```

## 8. Next Steps

### Production Readiness
1. **Enable HTTPS**: SSL certificates (Auto-renew with Certbot)
2. **Set up monitoring**: Health checks, logging, alerts
3. **Configure backups**: Daily database backups
4. **Implement caching**: Redis caching for Indian Kanoon API
5. **Set up scaling**: Load balancer, multiple instances

### Security Checklist
- [ ] Change default passwords
- [ ] Enable firewall (UFW)
- [ ] Regular security updates
- [ ] API key rotation schedule
- [ ] Database encryption at rest

### Performance Optimization
- [ ] Database indexes optimized
- [ ] Redis memory limits configured
- [ ] CDN for static files
- [ ] Connection pooling tuned

## 9. Support Resources

- **Detailed Guide**: [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)
- **Tesseract OCR**: [CLOUD_DEPLOYMENT_TESSERACT.md](CLOUD_DEPLOYMENT_TESSERACT.md)
- **Project Documentation**: [README.md](README.md)
- **API Documentation**: `http://your-domain.com/docs`

## 10. Emergency Contacts

For issues with:
- **Database**: Check PostgreSQL logs, restore from backup
- **Redis**: Check memory usage, restart service
- **Application**: Check application logs, restart service
- **Deployment**: Rollback to previous version

---

**Note**: This is a quick reference. Always refer to the comprehensive deployment guide for detailed instructions and troubleshooting.