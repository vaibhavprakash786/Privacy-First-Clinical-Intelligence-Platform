#!/bin/bash
# ============================================
# VaidyaMitra EC2 Deployment Script
# ============================================
# Usage: chmod +x deploy.sh && ./deploy.sh
# Requires: Ubuntu/Amazon Linux 2 EC2 instance

set -e

echo "================================================"
echo "  VaidyaMitra - EC2 Deployment"
echo "  Privacy-First Clinical Intelligence for Bharat"
echo "================================================"
echo ""

# ---- Step 1: Install Docker ----
if ! command -v docker &> /dev/null; then
    echo "📦 Installing Docker..."
    sudo yum update -y 2>/dev/null || sudo apt-get update -y
    sudo yum install -y docker 2>/dev/null || sudo apt-get install -y docker.io
    sudo systemctl start docker
    sudo systemctl enable docker
    sudo usermod -aG docker $USER
    echo "✅ Docker installed"
else
    echo "✅ Docker already installed"
fi

# ---- Step 2: Install Docker Compose ----
if ! command -v docker compose &> /dev/null; then
    echo "📦 Installing Docker Compose..."
    DOCKER_COMPOSE_VERSION="v2.24.0"
    sudo curl -L "https://github.com/docker/compose/releases/download/${DOCKER_COMPOSE_VERSION}/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
    echo "✅ Docker Compose installed"
else
    echo "✅ Docker Compose already installed"
fi

# ---- Step 3: Check .env file ----
if [ ! -f "./backend/.env" ]; then
    echo ""
    echo "⚠️  No .env file found in backend/"
    echo "   Creating from template..."
    cp ./backend/.env.example ./backend/.env
    echo ""
    echo "🔧 Please edit backend/.env with your AWS credentials:"
    echo "   nano ./backend/.env"
    echo ""
    echo "Required settings:"
    echo "   AWS_ACCESS_KEY_ID=your_access_key"
    echo "   AWS_SECRET_ACCESS_KEY=your_secret_key"
    echo ""
    read -p "Press Enter after configuring .env to continue..."
fi

# ---- Step 4: Build and Start ----
echo ""
echo "🔨 Building containers..."
docker compose build --no-cache

echo ""
echo "🚀 Starting VaidyaMitra..."
docker compose up -d

echo ""
echo "⏳ Waiting for services to be healthy..."
sleep 10

# ---- Step 5: Verify ----
echo ""
echo "🔍 Checking service status..."
docker compose ps

echo ""
echo "================================================"
echo "  ✅ VaidyaMitra deployed successfully!"
echo ""
echo "  🌐 Frontend:  http://$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4 2>/dev/null || echo 'localhost')"
echo "  📡 API Docs:  http://$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4 2>/dev/null || echo 'localhost')/api/docs"
echo ""
echo "  📋 Useful commands:"
echo "     docker compose logs -f       # View logs"
echo "     docker compose restart       # Restart services"
echo "     docker compose down          # Stop services"
echo "     docker compose up -d --build # Rebuild & restart"
echo "================================================"
