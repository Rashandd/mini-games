# 🚀 VPS Deployment Guide — Mini Games Platform

Deploy the Mini Games Platform on a fresh **Ubuntu 22.04/24.04** VPS.

> [!IMPORTANT]
> This guide has **three deployment paths**. Choose one:
> | Mode | Use case | URL |
> |------|----------|-----|
> | **🧪 Quick Dev** | Development / testing on VPS, easiest | `http://YOUR_VPS_IP:5173` |
> | **Option A — Public IP** | Production, no domain needed | `http://YOUR_VPS_IP` |
> | **Option B — Domain + SSL** | Production with HTTPS | `https://games.yourdomain.com` |

---

## 📋 Prerequisites

| Requirement | Minimum |
|-------------|---------|
| **OS** | Ubuntu 22.04 / 24.04 LTS |
| **RAM** | 1 GB (2 GB recommended) |
| **Disk** | 10 GB free |
| **Access** | Root or sudo SSH access |
| **Domain** | Only needed for Option B |

---

## 🧪 Quick Dev Mode (Easiest)

> No Nginx, no build step. Both servers run as systemd services — survives SSH disconnect.
> Access at `http://YOUR_VPS_IP:5173` — includes hot reload!

### 1. Do Steps 1–5 from the Shared Steps below

(Install deps, setup PostgreSQL, clone repo, setup backend venv + `.env`)

For the `.env`, use:
```bash
cat > backend/.env << 'EOF'
DATABASE_URL=postgresql+asyncpg://minigames@/social_empires?host=/var/run/postgresql
JWT_SECRET=dev-secret-change-for-prod
HOST=0.0.0.0
PORT=5050
CORS_ORIGINS=["http://YOUR_VPS_IP:5173"]
EOF
```

### 2. Install frontend dependencies

```bash
cd /home/minigames/mini-games/frontend
npm install
```

### 3. Create systemd services

**Backend service:**
```bash
sudo tee /etc/systemd/system/minigames-backend.service << 'EOF'
[Unit]
Description=Mini Games Backend (Dev)
After=network.target postgresql.service
Requires=postgresql.service

[Service]
Type=simple
User=minigames
Group=minigames
WorkingDirectory=/home/minigames/mini-games/backend
Environment="PATH=/home/minigames/mini-games/backend/venv/bin:/usr/bin"
ExecStart=/home/minigames/mini-games/backend/venv/bin/python main.py --host all
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF
```

**Frontend dev service:**

> [!TIP]
> Find your node path first: `which node` — if you use **nvm**, it will be something like
> `/home/minigames/.nvm/versions/node/v24.13.1/bin/node`. Use that directory in both
> `Environment` and `ExecStart` below.

```bash
# Get your node bin directory
NODE_BIN=$(dirname $(which node))

sudo tee /etc/systemd/system/minigames-frontend.service << EOF
[Unit]
Description=Mini Games Frontend Dev Server
After=network.target minigames-backend.service

[Service]
Type=simple
User=minigames
Group=minigames
WorkingDirectory=/home/minigames/mini-games/frontend
Environment="PATH=${NODE_BIN}:/usr/local/bin:/usr/bin:/bin"
ExecStart=${NODE_BIN}/npx vite --host 0.0.0.0
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF
```

### 4. Enable & start both

```bash
sudo systemctl daemon-reload
sudo systemctl enable minigames-backend minigames-frontend
sudo systemctl start minigames-backend minigames-frontend
```

### 5. Open firewall ports

```bash
sudo ufw allow OpenSSH
sudo ufw allow 5173/tcp
sudo ufw allow 5050/tcp
sudo ufw enable
```

### 6. Open in browser

Go to `http://YOUR_VPS_IP:5173` ✅

Vite's built-in proxy forwards all `/api`, `/socket.io`, `/assets` calls to the backend automatically.

**Useful commands:**
```bash
# Check status
sudo systemctl status minigames-backend
sudo systemctl status minigames-frontend

# View logs
sudo journalctl -u minigames-backend -f
sudo journalctl -u minigames-frontend -f

# Restart both
sudo systemctl restart minigames-backend minigames-frontend
```

> [!NOTE]
> This is for **development only**. For production, use Option A or B below.

---

## Production Setup (Options A & B)

## Shared Steps (Both Options)

### Step 1 — Initial Server Setup

```bash
# SSH in
ssh root@YOUR_VPS_IP

# Update packages
apt update && apt upgrade -y

# Create deploy user
adduser minigames
usermod -aG sudo minigames
su - minigames
```

### Step 2 — Install Dependencies

```bash
# System packages
sudo apt install -y \
  python3.12 python3.12-venv python3.12-dev \
  postgresql postgresql-contrib \
  nginx git curl build-essential

# If python3.12 not in default repos:
sudo add-apt-repository ppa:deadsnakes/ppa -y
sudo apt update && sudo apt install -y python3.12 python3.12-venv python3.12-dev

# Node.js 20
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt install -y nodejs

# Verify
python3.12 --version && node --version && psql --version
```

### Step 3 — PostgreSQL Setup

```bash
sudo -u postgres psql
```

```sql
CREATE ROLE minigames WITH LOGIN;
CREATE DATABASE social_empires OWNER minigames;
\q
```

Test: `psql -d social_empires -c "SELECT 1;"`

### Step 4 — Clone the Project

```bash
cd /home/minigames
git clone https://github.com/Rashandd/mini-games.git
cd mini-games
```

### Step 5 — Backend Setup

```bash
cd /home/minigames/mini-games/backend
python3.12 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

Create `backend/.env` — **adjust `CORS_ORIGINS` based on your option:**

**For Option A (Public IP):**
```bash
cat > .env << 'EOF'
DATABASE_URL=postgresql+asyncpg://minigames@/social_empires?host=/var/run/postgresql
JWT_SECRET=CHANGE-ME-TO-RANDOM-64-CHAR-SECRET
HOST=127.0.0.1
PORT=5050
CORS_ORIGINS=["http://YOUR_VPS_IP"]
EOF
```

**For Option B (Domain):**
```bash
cat > .env << 'EOF'
DATABASE_URL=postgresql+asyncpg://minigames@/social_empires?host=/var/run/postgresql
JWT_SECRET=CHANGE-ME-TO-RANDOM-64-CHAR-SECRET
HOST=127.0.0.1
PORT=5050
CORS_ORIGINS=["https://games.yourdomain.com"]
EOF
```

> [!CAUTION]
> Generate a real JWT secret: `python3 -c "import secrets; print(secrets.token_urlsafe(64))"`

Test: `python main.py` → you should see `[+] Mini Games Platform running`. Ctrl+C to stop.

### Step 6 — Frontend Build

```bash
cd /home/minigames/mini-games/frontend
npm install
npm run build
```

This creates `dist/` with the production static files.

### Step 7 — Systemd Service (Backend)

```bash
sudo tee /etc/systemd/system/minigames.service << 'EOF'
[Unit]
Description=Mini Games Platform Backend
After=network.target postgresql.service
Requires=postgresql.service

[Service]
Type=simple
User=minigames
Group=minigames
WorkingDirectory=/home/minigames/mini-games/backend
Environment="PATH=/home/minigames/mini-games/backend/venv/bin:/usr/bin"
ExecStart=/home/minigames/mini-games/backend/venv/bin/python main.py
Restart=always
RestartSec=5
NoNewPrivileges=true
PrivateTmp=true

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable minigames
sudo systemctl start minigames

# Verify
sudo systemctl status minigames
```

---

## Option A — Public IP Setup (No Domain)

> Access the platform at `http://YOUR_VPS_IP`

### Step A8 — Nginx Config (IP-based)

```bash
sudo tee /etc/nginx/sites-available/minigames << 'NGINX'
server {
    listen 80 default_server;
    server_name _;

    # ── Frontend (React) ──
    root /home/minigames/mini-games/frontend/dist;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }

    # ── Backend API ──
    location /api/ {
        proxy_pass http://127.0.0.1:5050;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # ── Socket.IO (WebSocket) ──
    location /socket.io/ {
        proxy_pass http://127.0.0.1:5050;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_read_timeout 86400s;
        proxy_send_timeout 86400s;
    }

    # ── Game assets ──
    location /assets/ {
        proxy_pass http://127.0.0.1:5050;
        proxy_set_header Host $host;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    location /wave-drifter-assets/ {
        proxy_pass http://127.0.0.1:5050;
        proxy_set_header Host $host;
    }

    # ── Social Empires routes ──
    location ~ \.(php|xml)$ {
        proxy_pass http://127.0.0.1:5050;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /default01.static.socialpointgames.com/ {
        proxy_pass http://127.0.0.1:5050;
        proxy_set_header Host $host;
    }

    location /dynamic.flash1.dev.socialpoint.es/ {
        proxy_pass http://127.0.0.1:5050;
        proxy_set_header Host $host;
    }

    location /stub/ {
        proxy_pass http://127.0.0.1:5050;
        proxy_set_header Host $host;
    }

    client_max_body_size 10M;
}
NGINX
```

### Step A9 — Enable & Open Firewall

```bash
sudo ln -s /etc/nginx/sites-available/minigames /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl reload nginx

# Firewall
sudo ufw allow OpenSSH
sudo ufw allow 80/tcp
sudo ufw enable
```

### Step A10 — Verify

Open `http://YOUR_VPS_IP` in your browser — you should see the Mini Games login page!

**✅ Option A is complete.**

---

## Option B — Domain + SSL Setup

> Access the platform at `https://games.yourdomain.com`

### Prerequisites for Option B
- A domain (e.g. `games.yourdomain.com`) with an **A record** pointing to your VPS IP

### Step B8 — Nginx Config (Domain-based)

```bash
sudo tee /etc/nginx/sites-available/minigames << 'NGINX'
server {
    listen 80;
    server_name games.yourdomain.com;

    # ── Frontend (React) ──
    root /home/minigames/mini-games/frontend/dist;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }

    # ── Backend API ──
    location /api/ {
        proxy_pass http://127.0.0.1:5050;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # ── Socket.IO (WebSocket) ──
    location /socket.io/ {
        proxy_pass http://127.0.0.1:5050;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_read_timeout 86400s;
        proxy_send_timeout 86400s;
    }

    # ── Game assets ──
    location /assets/ {
        proxy_pass http://127.0.0.1:5050;
        proxy_set_header Host $host;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    location /wave-drifter-assets/ {
        proxy_pass http://127.0.0.1:5050;
        proxy_set_header Host $host;
    }

    # ── Social Empires routes ──
    location ~ \.(php|xml)$ {
        proxy_pass http://127.0.0.1:5050;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /default01.static.socialpointgames.com/ {
        proxy_pass http://127.0.0.1:5050;
        proxy_set_header Host $host;
    }

    location /dynamic.flash1.dev.socialpoint.es/ {
        proxy_pass http://127.0.0.1:5050;
        proxy_set_header Host $host;
    }

    location /stub/ {
        proxy_pass http://127.0.0.1:5050;
        proxy_set_header Host $host;
    }

    client_max_body_size 10M;
}
NGINX
```

### Step B9 — Enable Nginx

```bash
sudo ln -s /etc/nginx/sites-available/minigames /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl reload nginx
```

### Step B10 — SSL with Let's Encrypt

```bash
sudo apt install -y certbot python3-certbot-nginx
sudo certbot --nginx -d games.yourdomain.com

# Verify auto-renewal
sudo certbot renew --dry-run
```

Certbot automatically configures HTTPS and HTTP→HTTPS redirect.

### Step B11 — Firewall

```bash
sudo ufw allow OpenSSH
sudo ufw allow 'Nginx Full'
sudo ufw enable
```

### Step B12 — Verify

Open `https://games.yourdomain.com` in your browser!

**✅ Option B is complete.**

---

## 📦 Updating the App

```bash
cd /home/minigames/mini-games
git pull origin main

# Backend
cd backend && source venv/bin/activate && pip install -r requirements.txt
sudo systemctl restart minigames

# Frontend
cd ../frontend && npm install && npm run build
```

> [!TIP]
> Save this as `deploy.sh`:
> ```bash
> #!/bin/bash
> set -e
> cd /home/minigames/mini-games
> git pull origin main
> cd backend && source venv/bin/activate && pip install -r requirements.txt
> sudo systemctl restart minigames
> cd ../frontend && npm install && npm run build
> echo "✅ Deployment complete!"
> ```

---

## 🔧 Troubleshooting

| Problem | Fix |
|---------|-----|
| Backend won't start | `sudo journalctl -u minigames -n 50` |
| 502 Bad Gateway | `sudo systemctl restart minigames` |
| WebSocket fails | Check Nginx has `Upgrade` + `Connection` headers in `/socket.io/` |
| DB auth fails | Ensure you run as `minigames` user: `whoami` |
| Assets missing | `ls -la /home/minigames/mini-games/assets/` |
| Permission errors | `sudo chown -R minigames:minigames /home/minigames/mini-games` |

---

## 🏗️ Architecture

```
    ┌────────────────────┐
    │   Browser Client   │
    └─────────┬──────────┘
              │ HTTP/HTTPS
    ┌─────────▼──────────┐
    │      Nginx          │
    │  (Reverse Proxy)    │
    ├─────────────────────┤
    │ /          → dist/  │  React static
    │ /api/*     → :5050  │  FastAPI
    │ /socket.io → :5050  │  WebSocket
    │ /assets/*  → :5050  │  Game files
    └─────────┬──────────┘
              │ localhost:5050
    ┌─────────▼──────────┐
    │  FastAPI + Uvicorn  │
    │  + Socket.IO        │
    └─────────┬──────────┘
              │
    ┌─────────▼──────────┐
    │    PostgreSQL       │
    └────────────────────┘
```

---

## 📝 Quick Reference

| Action | Command |
|--------|---------|
| Start backend | `sudo systemctl start minigames` |
| Stop backend | `sudo systemctl stop minigames` |
| Restart backend | `sudo systemctl restart minigames` |
| View logs | `sudo journalctl -u minigames -f` |
| Reload Nginx | `sudo systemctl reload nginx` |
| Renew SSL | `sudo certbot renew` |
| DB shell | `psql -d social_empires` |
| Build frontend | `cd frontend && npm run build` |
