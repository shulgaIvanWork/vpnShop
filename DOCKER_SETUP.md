# 🐳 Docker Setup Guide

## 📋 Overview

This project uses Docker Compose for easy development and deployment:

- **PostgreSQL** - Database
- **Redis** - Caching & FSM storage
- **Bot** - Main application
- **Worker** - Background tasks (optional)

---

## 🚀 Quick Start

### 1. Prerequisites

Install Docker:
- Windows: [Docker Desktop](https://www.docker.com/products/docker-desktop/)
- Linux: `sudo apt install docker.io docker-compose`

### 2. Configure Environment

```bash
# Copy and edit .env file
cp .env.example .env
nano .env  # or use any editor
```

Fill in:
- `MAX_BOT_TOKEN` - Your MAX bot token
- `BOT_DOMAIN` - Your domain or ngrok URL
- `YOOKASSA_*` - YooKassa credentials
- `YOOMONEY_*` - YooMoney credentials
- `POSTGRES_PASSWORD` - Choose a secure password

### 3. Start Services

```bash
# Start only PostgreSQL and Redis (for development)
docker-compose up -d postgres redis

# Start all services (including bot)
docker-compose up -d
```

### 4. Verify Services

```bash
# Check running containers
docker-compose ps

# View logs
docker-compose logs -f bot
docker-compose logs -f postgres
```

---

## 🗄️ Database Setup

### First Time Setup

```bash
# Start PostgreSQL
docker-compose up -d postgres

# Wait for PostgreSQL to be ready
docker-compose logs -f postgres
# Wait for: "database system is ready to accept connections"

# Run migrations (after Alembic is set up)
docker-compose run --rm alembic upgrade head
```

### Connect to Database

```bash
# Using psql
docker-compose exec postgres psql -U vpn_user -d vpn_shop

# Using pgAdmin or DBeaver
# Host: localhost
# Port: 5432
# User: vpn_user
# Password: (from .env)
# Database: vpn_shop
```

### Backup & Restore

```bash
# Backup
docker-compose exec postgres pg_dump -U vpn_user vpn_shop > backup.sql

# Restore
docker-compose exec -T postgres psql -U vpn_user vpn_shop < backup.sql
```

---

## 🔧 Development Workflow

### Run Bot Locally (with Docker DB)

```bash
# Start only DB services
docker-compose up -d postgres redis

# Run bot locally (for debugging)
cd max-vpn-bot
poetry install
poetry run python -m app
```

### Run Bot in Docker

```bash
# Build and start
docker-compose up -d --build bot

# View logs
docker-compose logs -f bot

# Restart after code changes
docker-compose restart bot
```

---

## 🌐 Webhook Setup

### For Development (ngrok)

1. Install ngrok: https://ngrok.com/download
2. Start ngrok:
   ```bash
   ngrok http 8080
   ```
3. Copy HTTPS URL (e.g., `https://abc123.ngrok.io`)
4. Update `.env`:
   ```env
   BOT_DOMAIN=https://abc123.ngrok.io
   ```

### For Production (Your Domain)

1. Point your domain to server IP
2. Setup SSL certificate (Let's Encrypt):
   ```bash
   sudo certbot certonly --standalone -d yourdomain.com
   ```
3. Update `.env`:
   ```env
   BOT_DOMAIN=https://yourdomain.com
   ```
4. Configure reverse proxy (Nginx example):
   ```nginx
   server {
       listen 443 ssl;
       server_name yourdomain.com;
       
       ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
       ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;
       
       location /webhook/yookassa {
           proxy_pass http://localhost:8080;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
       }
       
       location /webhook/yoomoney {
           proxy_pass http://localhost:8080;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
       }
   }
   ```

---

## 📦 Deployment to Hosting

### 1. Prepare Server

```bash
# Install Docker
curl -fsSL https://get.docker.com | sh

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

### 2. Upload Files

```bash
# Using git
git clone https://github.com/shulgaIvanWork/vpnShop.git
cd vpnShop/max-vpn-bot

# Or using scp
scp -r max-vpn-bot user@yourserver:~/
```

### 3. Configure

```bash
# Create .env file
nano .env

# Fill in all credentials
```

### 4. Deploy

```bash
# Build and start
docker-compose up -d --build

# Check status
docker-compose ps

# View logs
docker-compose logs -f
```

### 5. Setup Auto-Restart

```bash
# Docker containers already have restart: always in docker-compose.yml

# Auto-start on boot
sudo systemctl enable docker
```

---

## 🔍 Troubleshooting

### Container Won't Start

```bash
# Check logs
docker-compose logs bot

# Common issues:
# - Missing .env variables
# - Port already in use
# - Database not ready
```

### Database Connection Failed

```bash
# Check if PostgreSQL is running
docker-compose ps postgres

# Check PostgreSQL logs
docker-compose logs postgres

# Wait for readiness (takes ~10 seconds)
docker-compose logs -f postgres | grep "ready to accept connections"
```

### Rebuild After Code Changes

```bash
# Rebuild and restart
docker-compose up -d --build bot

# Or just restart (if only Python code changed)
docker-compose restart bot
```

### Clean Start

```bash
# Stop all containers
docker-compose down

# Remove volumes (WARNING: deletes database!)
docker-compose down -v

# Start fresh
docker-compose up -d
```

---

## 📊 Useful Commands

```bash
# View running containers
docker-compose ps

# View logs
docker-compose logs -f [service]

# Execute command in container
docker-compose exec bot bash
docker-compose exec postgres psql -U vpn_user -d vpn_shop

# Stop services
docker-compose stop
docker-compose start

# Remove containers (keep data)
docker-compose down

# Remove everything (including data)
docker-compose down -v --rmi all
```

---

## 🔐 Security Notes

1. **Never commit .env file**
2. **Use strong passwords**
3. **Enable SSL for production**
4. **Keep Docker images updated**
5. **Use Docker secrets for sensitive data (advanced)**

---

## 📚 Next Steps

After Docker setup:
1. Configure payment webhooks
2. Run database migrations
3. Test bot functionality
4. Setup monitoring (optional)

See `TODO_BEFORE_LAUNCH.md` for complete checklist.
