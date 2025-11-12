#!/bin/bash
set -e

echo "🚀 DocFix Deployment Script for Hostinger VPS"
echo "=============================================="

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo -e "${RED}Please run as root (use sudo)${NC}"
    exit 1
fi

echo -e "${GREEN}[1/7] Updating system packages...${NC}"
apt-get update
apt-get upgrade -y

echo -e "${GREEN}[2/7] Installing system dependencies...${NC}"
apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    git \
    nginx \
    certbot \
    python3-certbot-nginx \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1

echo -e "${GREEN}[3/7] Installing Docker...${NC}"
if ! command -v docker &> /dev/null; then
    curl -fsSL https://get.docker.com -o get-docker.sh
    sh get-docker.sh
    systemctl enable docker
    systemctl start docker
    rm get-docker.sh
else
    echo "Docker already installed"
fi

if ! command -v docker-compose &> /dev/null; then
    curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    chmod +x /usr/local/bin/docker-compose
fi

echo -e "${GREEN}[4/7] Cloning repository...${NC}"
APP_DIR="/opt/docfix"
if [ -d "$APP_DIR" ]; then
    echo "Application directory exists, updating..."
    cd $APP_DIR
    git pull
else
    git clone https://github.com/zaharenok/PDF_dewrapper.git $APP_DIR
    cd $APP_DIR
fi

echo -e "${GREEN}[5/7] Setting up application...${NC}"
mkdir -p uploads results static
chmod 755 uploads results static

# Create environment file
cat > .env << EOF
LOG_LEVEL=INFO
UPLOAD_DIR=/opt/docfix/uploads
RESULTS_DIR=/opt/docfix/results
EOF

echo -e "${GREEN}[6/7] Building Docker containers...${NC}"
docker-compose down || true
docker-compose build
docker-compose up -d

echo -e "${GREEN}[7/7] Waiting for application to start...${NC}"
sleep 10

# Check if application is running
if curl -f http://localhost:8000/health > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Application is running successfully!${NC}"
    echo -e "${YELLOW}Health check: http://localhost:8000/health${NC}"
else
    echo -e "${RED}❌ Application failed to start. Check logs with: docker-compose logs${NC}"
    exit 1
fi

echo ""
echo -e "${GREEN}=============================================="
echo "🎉 Deployment completed!"
echo "=============================================="
echo ""
echo "Application is running at: http://localhost:8000"
echo ""
echo "Next steps:"
echo "1. Configure Nginx reverse proxy (see nginx-config.conf)"
echo "2. Set up SSL certificate with: certbot --nginx -d your-domain.com"
echo "3. Configure firewall: ufw allow 80 && ufw allow 443"
echo ""
echo "Useful commands:"
echo "  - View logs: docker-compose logs -f"
echo "  - Restart: docker-compose restart"
echo "  - Stop: docker-compose down"
echo "  - Update: git pull && docker-compose build && docker-compose up -d"
echo ""
