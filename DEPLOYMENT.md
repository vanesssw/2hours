# Production Deployment Guide - CRACK PROTOCOL

Domain: **crackis.online**

## Prerequisites

- Ubuntu 20.04/22.04 LTS server (min 2GB RAM, 2 CPU cores)
- Root or sudo access
- Domain `crackis.online` pointed to your server IP (A record)

---

## 1. Server Preparation

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install required packages
sudo apt install -y curl git ufw

# Configure firewall
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS
sudo ufw enable
```

---

## 2. Install Docker & Docker Compose

```bash
# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Add current user to docker group
sudo usermod -aG docker $USER
newgrp docker

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Verify installation
docker --version
docker-compose --version
```

---

## 3. Clone Project

```bash
# Create project directory
sudo mkdir -p /opt/crackprotocol
sudo chown $USER:$USER /opt/crackprotocol
cd /opt/crackprotocol

# Clone repository (or upload files via SCP/SFTP)
# git clone <your-repo-url> .
# OR upload files manually

# Set correct permissions
chmod +x backend/*.py
```

---

## 4. Production Configuration

### 4.1. Update `docker-compose.yml`

```bash
nano docker-compose.yml
```

Change environment variables:

```yaml
environment:
  - SECRET_PHRASE=<CHANGE_THIS_TO_SECURE_PHRASE>
  - SECRET_KEY=<GENERATE_SECURE_RANDOM_KEY_HERE>
  - POSTGRES_PASSWORD=<STRONG_DATABASE_PASSWORD>
  - DATABASE_URL=postgresql://crackprotocol:<STRONG_DATABASE_PASSWORD>@db:5432/crackprotocol
```

Generate secure keys:
```bash
# Generate SECRET_KEY
openssl rand -base64 32

# Generate POSTGRES_PASSWORD
openssl rand -base64 24
```

### 4.2. Update DeepSeek API Key

```bash
nano backend/.env
```

Add:
```
DEEPSEEK_API_KEY=sk-e492676cdd624446aa91818e022f2af2
SECRET_PHRASE=<YOUR_SECRET_PHRASE>
```

---

## 5. Setup Nginx with SSL (Certbot)

### 5.1. Install Certbot

```bash
sudo apt install -y certbot python3-certbot-nginx
```

### 5.2. Create Production Nginx Config

```bash
sudo nano /etc/nginx/sites-available/crackis.online
```

Paste:

```nginx
server {
    listen 80;
    server_name crackis.online www.crackis.online;

    # Redirect HTTP to HTTPS (will be configured by Certbot)
    location / {
        return 301 https://$server_name$request_uri;
    }
}

server {
    listen 443 ssl http2;
    server_name crackis.online www.crackis.online;

    # SSL certificates (will be added by Certbot)
    # ssl_certificate /etc/letsencrypt/live/crackis.online/fullchain.pem;
    # ssl_certificate_key /etc/letsencrypt/live/crackis.online/privkey.pem;

    # Security headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;

    # Proxy to Docker containers
    location /api/ {
        proxy_pass http://localhost:8000/api/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    location /docs {
        proxy_pass http://localhost:8000/docs;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /openapi.json {
        proxy_pass http://localhost:8000/openapi.json;
        proxy_set_header Host $host;
    }

    # Static files from Docker Nginx
    location / {
        proxy_pass http://localhost:80;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types text/plain text/css text/xml text/javascript application/javascript application/json;

    # Cache static assets
    location ~* \.(jpg|jpeg|png|gif|ico|css|js|svg|woff|woff2|ttf|eot)$ {
        proxy_pass http://localhost:80;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
```

### 5.3. Enable Site & Get SSL Certificate

```bash
# Enable site
sudo ln -s /etc/nginx/sites-available/crackis.online /etc/nginx/sites-enabled/

# Remove default site
sudo rm /etc/nginx/sites-enabled/default

# Test Nginx config
sudo nginx -t

# Restart Nginx
sudo systemctl restart nginx

# Get SSL certificate from Let's Encrypt
sudo certbot --nginx -d crackis.online -d www.crackis.online

# Follow prompts:
# - Enter email address
# - Agree to Terms of Service
# - Choose: Redirect HTTP to HTTPS (option 2)
```

Certbot will:
- Automatically update your Nginx config with SSL certificates
- Set up auto-renewal (certificates expire every 90 days)

### 5.4. Test Auto-renewal

```bash
sudo certbot renew --dry-run
```

---

## 6. Start Application

```bash
cd /opt/crackprotocol

# Start all services
docker-compose up -d --build

# Check status
docker-compose ps

# View logs
docker-compose logs -f
```

Expected output:
```
crackprotocol-db        healthy
crackprotocol-backend   healthy
crackprotocol-frontend  running
```

---

## 7. Verify Deployment

### 7.1. Check Services

```bash
# Check Docker containers
docker ps

# Check backend health
curl http://localhost:8000/

# Check database
docker exec crackprotocol-db psql -U crackprotocol -d crackprotocol -c "\dt"
```

### 7.2. Test Website

Open in browser:
- https://crackis.online
- https://crackis.online/terminal
- https://crackis.online/leaderboard
- https://crackis.online/api/stats

---

## 8. Maintenance Commands

### View Logs
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend
docker-compose logs -f db
```

### Restart Services
```bash
# Restart all
docker-compose restart

# Restart specific service
docker-compose restart backend
```

### Update Application
```bash
cd /opt/crackprotocol

# Pull latest changes (if using git)
git pull

# Rebuild and restart
docker-compose down
docker-compose up -d --build
```

### Database Backup
```bash
# Create backup
docker exec crackprotocol-db pg_dump -U crackprotocol crackprotocol > backup_$(date +%Y%m%d_%H%M%S).sql

# Restore from backup
cat backup_20260215_120000.sql | docker exec -i crackprotocol-db psql -U crackprotocol -d crackprotocol
```

### Monitor Resources
```bash
# Container stats
docker stats

# Disk usage
docker system df

# Clean up unused images
docker system prune -a
```

---

## 9. SSL Certificate Renewal

Certbot auto-renews certificates. To manually renew:

```bash
sudo certbot renew
sudo systemctl reload nginx
```

Check expiration:
```bash
sudo certbot certificates
```

---

## 10. Security Hardening

### 10.1. Change SSH Port (Optional)
```bash
sudo nano /etc/ssh/sshd_config
# Change: Port 22 → Port 2222
sudo systemctl restart sshd
sudo ufw allow 2222/tcp
sudo ufw delete allow 22/tcp
```

### 10.2. Disable Root Login
```bash
sudo nano /etc/ssh/sshd_config
# Set: PermitRootLogin no
sudo systemctl restart sshd
```

### 10.3. Setup Fail2ban
```bash
sudo apt install -y fail2ban
sudo systemctl enable fail2ban
sudo systemctl start fail2ban
```

### 10.4. Regular Updates
```bash
# Setup automatic security updates
sudo apt install -y unattended-upgrades
sudo dpkg-reconfigure --priority=low unattended-upgrades
```

---

## 11. Monitoring Setup (Optional)

### Install Prometheus + Grafana
```bash
# Add monitoring to docker-compose.yml or use external service
# Consider: Datadog, New Relic, or self-hosted Prometheus
```

### Simple Uptime Monitoring
```bash
# Install uptimekuma
docker run -d --restart=always -p 3001:3001 -v uptime-kuma:/app/data --name uptime-kuma louislam/uptime-kuma:1
# Access at: http://your-server-ip:3001
```

---

## 12. Troubleshooting

### Backend Can't Connect to Database
```bash
# Check if DB is healthy
docker-compose ps db

# View DB logs
docker-compose logs db

# Restart backend
docker-compose restart backend
```

### SSL Certificate Issues
```bash
# Check certificate status
sudo certbot certificates

# Renew manually
sudo certbot renew --force-renewal
```

### High Memory Usage
```bash
# Check container stats
docker stats

# Restart PostgreSQL if needed
docker-compose restart db
```

### Port Conflicts
```bash
# Check what's using port 80
sudo lsof -i :80

# Check what's using port 443
sudo lsof -i :443
```

---

## 13. Performance Tuning

### PostgreSQL Optimization
```bash
docker exec -it crackprotocol-db psql -U crackprotocol -d crackprotocol

# Run inside psql:
ALTER SYSTEM SET shared_buffers = '256MB';
ALTER SYSTEM SET effective_cache_size = '1GB';
ALTER SYSTEM SET maintenance_work_mem = '64MB';
SELECT pg_reload_conf();
```

### Nginx Caching
Add to nginx config:
```nginx
proxy_cache_path /var/cache/nginx levels=1:2 keys_zone=api_cache:10m max_size=100m;
proxy_cache api_cache;
proxy_cache_valid 200 5m;
```

---

## 14. Scaling (Future)

When traffic increases:

1. **Horizontal Scaling**: Add more backend instances
2. **Load Balancer**: Use Nginx upstream or cloud load balancer
3. **Database**: Switch to managed PostgreSQL (AWS RDS, DigitalOcean Managed DB)
4. **CDN**: CloudFlare or AWS CloudFront for static assets
5. **Redis Cache**: Add Redis for session management

---

## Support & Contacts

- Domain: https://crackis.online
- API Docs: https://crackis.online/docs
- Backend Health: https://crackis.online/api/stats

**Server Specs Recommendation:**
- **Development**: 2GB RAM, 1 CPU, 20GB SSD
- **Production (100 users)**: 4GB RAM, 2 CPU, 40GB SSD
- **High Traffic (1000+ users)**: 8GB RAM, 4 CPU, 80GB SSD + Load Balancer

---

## Quick Deployment Checklist

- [ ] Server setup (Ubuntu 22.04)
- [ ] Docker & Docker Compose installed
- [ ] Domain DNS pointed to server
- [ ] Project files uploaded to `/opt/crackprotocol`
- [ ] Environment variables configured
- [ ] Nginx installed and configured
- [ ] SSL certificate obtained via Certbot
- [ ] Docker containers running (`docker-compose up -d`)
- [ ] Website accessible at https://crackis.online
- [ ] Database backups configured
- [ ] Monitoring set up
- [ ] Firewall rules configured

**Estimated deployment time: 30-45 minutes**

Good luck with your production deployment! 🚀
