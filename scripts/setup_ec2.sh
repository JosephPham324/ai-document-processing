#!/usr/bin/env bash
# ==============================================================================
# AWS EC2 Setup Script for Document Processing AI Agent
# Tested on Ubuntu 24.04 LTS (x86_64)
# ==============================================================================

set -euo pipefail

echo "=========================================================="
echo "🚀 Initializing AWS EC2 Instance for AI Document Processing"
echo "=========================================================="

# 1. Update OS packages
echo "📦 Updating system packages..."
sudo apt-get update && sudo apt-get upgrade -y
sudo apt-get install -y ca-certificates curl gnupg git ufw

# 2. Configure 2GB Swap (prevents Out-Of-Memory kills on t2/t3.micro instances)
if [ ! -f /swapfile ]; then
    echo "💾 Creating 2GB swapfile for memory stability..."
    sudo fallocate -l 2G /swapfile
    sudo chmod 600 /swapfile
    sudo mkswap /swapfile
    sudo swapon /swapfile
    echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
    echo "✓ Swapfile enabled."
else
    echo "✓ Swapfile already exists."
fi

# 3. Install Docker Engine and Docker Compose V2
if ! command -v docker &> /dev/null; then
    echo "🐳 Installing Docker Engine and Docker Compose..."
    sudo apt-get install -y docker.io docker-compose-v2
    sudo systemctl enable docker
    sudo systemctl start docker
    sudo usermod -aG docker "$USER"
    echo "✓ Docker installed successfully."
else
    echo "✓ Docker is already installed."
fi

# 4. Enable firewall rules (UFW)
echo "🛡️ Configuring host firewall..."
sudo ufw allow 22/tcp || true
sudo ufw allow 80/tcp || true
sudo ufw allow 443/tcp || true
sudo ufw --force enable || true

echo "=========================================================="
echo "✅ EC2 Setup Complete!"
echo "=========================================================="
echo ""
echo "Next steps to run the application:"
echo "1. Activate docker group permissions in current session:"
echo "   newgrp docker"
echo ""
echo "2. Configure your Cloudflare domain in .env:"
echo "   echo 'DOMAIN=docproc.yourdomain.com' >> .env"
echo ""
echo "3. Build and launch services with automatic HTTPS:"
echo "   docker compose up -d --build"
echo ""
echo "4. Access your dashboard at:"
echo "   https://<YOUR_DOMAIN>"
echo "=========================================================="
