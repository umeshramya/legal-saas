#!/bin/bash
# VPS Setup Script for Legal Analysis SAAS
# Usage: sudo bash setup-vps.sh

set -e

echo "=== Legal Analysis SAAS VPS Setup ==="

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "Please run as root (use sudo)"
    exit 1
fi

# Update system
echo "Updating system packages..."
apt-get update
apt-get upgrade -y

# Install Docker and Docker Compose
echo "Installing Docker and Docker Compose..."
apt-get install docker.io docker-compose -y

# Create application directory
echo "Creating application directory..."
mkdir -p /opt/legal-saas
cd /opt/legal-saas

# Clone repository (if not already present)
if [ ! -f "docker-compose.yml" ]; then
    echo "Cloning repository..."
    git clone https://github.com/your-repo/legal-saas.git /opt/legal-saas-temp
    mv /opt/legal-saas-temp/* /opt/legal-saas/
    rm -rf /opt/legal-saas-temp
fi

# Set up environment file
if [ ! -f ".env" ]; then
    echo "Setting up environment file..."
    if [ -f ".env.production.example" ]; then
        cp .env.production.example .env
        echo "Please edit /opt/legal-saas/.env with your production values"
        echo "Required edits:"
        echo "  - DATABASE_URL, DB_USER, DB_PASSWORD"
        echo "  - REDIS_URL, REDIS_PASSWORD"
        echo "  - DEEPSEEK_API_KEY"
        echo "  - JWT_SECRET_KEY"
        echo "  - ALLOWED_HOSTS, CORS_ORIGINS"
        read -p "Press Enter after editing .env file..."
    else
        echo "Error: .env.production.example not found"
        exit 1
    fi
fi

# Set permissions
echo "Setting permissions..."
chown -R www-data:www-data /opt/legal-saas
chmod -R 755 /opt/legal-saas

# Create uploads directory
mkdir -p uploads
chown www-data:www-data uploads

# Start services with production compose
echo "Starting services..."
docker-compose -f docker-compose.prod.yml up -d

# Wait for services to start
echo "Waiting for services to start..."
sleep 10

# Check if services are running
echo "Checking service status..."
docker-compose -f docker-compose.prod.yml ps

# Check application health
echo "Checking application health..."
HEALTH_CHECK=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/health || true)
if [ "$HEALTH_CHECK" = "200" ]; then
    echo "✅ Application is healthy!"
else
    echo "⚠️  Application health check failed (HTTP $HEALTH_CHECK)"
    echo "Check logs: docker-compose -f docker-compose.prod.yml logs app"
fi

echo ""
echo "=== Setup Complete ==="
echo "Application is running at: http://$(curl -s ifconfig.me):8000"
echo ""
echo "Next steps:"
echo "1. Set up Nginx reverse proxy (see DEPLOYMENT_GUIDE.md)"
echo "2. Configure SSL with Let's Encrypt"
echo "3. Set up firewall (ufw allow 22,80,443)"
echo "4. Configure backups (see DEPLOYMENT_GUIDE.md)"
echo ""
echo "For detailed instructions, refer to DEPLOYMENT_GUIDE.md"