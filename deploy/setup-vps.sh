#!/bin/bash
set -euo pipefail

# Contabo VPS Setup — LinkedIn LeadGen Dashboard
# Run as root on a fresh Ubuntu 22.04 VPS

echo "=== Updating system ==="
apt-get update && apt-get upgrade -y

echo "=== Installing Docker ==="
curl -fsSL https://get.docker.com | bash
systemctl enable --now docker

echo "=== Installing Nginx ==="
apt-get install -y nginx certbot python3-certbot-nginx

echo "=== Cloning project ==="
cd /opt
git clone https://github.com/your-org/linkedin-leadgen.git
cd linkedin-leadgen

echo "=== Starting services ==="
docker compose up -d --build

echo "=== Configuring Nginx reverse proxy ==="
cat > /etc/nginx/sites-available/leadgen << 'NGINX'
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
    }

    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 120s;
    }
}
NGINX

ln -sf /etc/nginx/sites-available/leadgen /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default
nginx -t && systemctl reload nginx

echo "=== Setting up SSL ==="
certbot --nginx -d your-domain.com --non-interactive --agree-tos -m admin@your-domain.com

echo "=== Setup complete ==="
echo "Dashboard: https://your-domain.com"
echo "Backend API: https://your-domain.com/api/health"
