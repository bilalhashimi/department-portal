# 🚀 **Department Portal - Raspberry Pi Deployment Guide**

## 📋 **Prerequisites**

### **Raspberry Pi Requirements:**
- Raspberry Pi 4 (4GB+ RAM recommended)
- 32GB+ MicroSD card (Class 10 or better)
- Stable power supply
- Ethernet connection (recommended for stability)

### **Required Software on Pi:**
- Raspberry Pi OS (64-bit)
- Docker & Docker Compose
- Git

---

## 🔧 **Step 1: Prepare Your Raspberry Pi**

### **1.1 Install Raspberry Pi OS**
```bash
# Flash Raspberry Pi OS to SD card using Raspberry Pi Imager
# Enable SSH during setup for remote access
```

### **1.2 Initial Setup (SSH into your Pi)**
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install essential packages
sudo apt install -y git curl vim htop

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Install Docker Compose
sudo apt install -y docker-compose

# Reboot to apply changes
sudo reboot
```

---

## 📁 **Step 2: Transfer Your Project**

### **2.1 Create Project Directory**
```bash
# SSH into your Pi
mkdir -p ~/department-portal
cd ~/department-portal
```

### **2.2 Transfer Files (from your laptop)**
```bash
# Option A: Using Git (if you have a repository)
git clone [your-repo-url] .

# Option B: Using SCP (secure copy)
# Run this from your laptop terminal
scp -r /Users/ahmadbilal/Documents/Projects/Cusa\ Project\ /department-portal/* pi@[PI_IP_ADDRESS]:~/department-portal/

# Option C: Using rsync (recommended)
rsync -avz --exclude 'node_modules' --exclude '__pycache__' --exclude '.git' \
  /Users/ahmadbilal/Documents/Projects/Cusa\ Project\ /department-portal/ \
  pi@[PI_IP_ADDRESS]:~/department-portal/
```

---

## ⚙️ **Step 3: Configure for Production**

### **3.1 Create Production Docker Compose**
```yaml
# Save as docker-compose.prod.yml
version: '3.8'

services:
  # PostgreSQL Database
  postgres:
    image: postgres:14
    environment:
      POSTGRES_DB: dwportal
      POSTGRES_USER: dwadmin
      POSTGRES_PASSWORD: dwadminpw
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: unless-stopped
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U dwadmin -d dwportal"]
      interval: 30s
      timeout: 10s
      retries: 3

  # Vector Database (Qdrant)
  vector_db:
    image: qdrant/qdrant:latest
    ports:
      - "6333:6333"
      - "6334:6334"
    volumes:
      - qdrant_data:/qdrant/storage
    restart: unless-stopped
    environment:
      QDRANT__SERVICE__HTTP_PORT: 6333
      QDRANT__SERVICE__GRPC_PORT: 6334

  # Redis for caching
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    restart: unless-stopped
    command: redis-server --appendonly yes

  # Backend API
  backend:
    build: 
      context: ./backend
      dockerfile: Dockerfile.prod
    ports:
      - "8000:8000"
    environment:
      - DEBUG=False
      - DB_HOST=postgres
      - DB_NAME=dwportal
      - DB_USER=dwadmin
      - DB_PASSWORD=dwadminpw
      - VECTOR_DB_URL=http://vector_db:6333
      - REDIS_URL=redis://redis:6379/0
      - ALLOWED_HOSTS=*
    depends_on:
      postgres:
        condition: service_healthy
      vector_db:
        condition: service_started
      redis:
        condition: service_started
    volumes:
      - media_files:/app/media
    restart: unless-stopped

  # Frontend
  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile.prod
    ports:
      - "80:80"
    environment:
      - VITE_API_URL=http://[PI_IP_ADDRESS]:8000/api/v1
    depends_on:
      - backend
    restart: unless-stopped

  # Celery Worker
  celery:
    build: 
      context: ./backend
      dockerfile: Dockerfile.prod
    command: celery -A portal_backend worker --loglevel=info
    environment:
      - DEBUG=False
      - DB_HOST=postgres
      - DB_NAME=dwportal
      - DB_USER=dwadmin
      - DB_PASSWORD=dwadminpw
      - VECTOR_DB_URL=http://vector_db:6333
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      postgres:
        condition: service_healthy
      vector_db:
        condition: service_started
      redis:
        condition: service_started
    volumes:
      - media_files:/app/media
    restart: unless-stopped

  # Ollama for AI
  ollama:
    image: ollama/ollama:latest
    ports:
      - "11434:11434"
    volumes:
      - ollama_data:/root/.ollama
    restart: unless-stopped
    environment:
      - OLLAMA_HOST=0.0.0.0

volumes:
  postgres_data:
  qdrant_data:
  redis_data:
  media_files:
  ollama_data:
```

### **3.2 Create Production Dockerfiles**

**Backend Production Dockerfile:**
```dockerfile
# Save as backend/Dockerfile.prod
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project
COPY . .

# Collect static files
RUN python manage.py collectstatic --noinput

# Create non-root user
RUN adduser --disabled-password --gecos '' appuser
RUN chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 8000

# Run gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "2", "portal_backend.wsgi:application"]
```

**Frontend Production Dockerfile:**
```dockerfile
# Save as frontend/Dockerfile.prod
# Build stage
FROM node:18-alpine as build

WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production

COPY . .
RUN npm run build

# Production stage
FROM nginx:alpine

# Copy build files
COPY --from=build /app/dist /usr/share/nginx/html

# Copy nginx config
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

### **3.3 Create Nginx Configuration**
```nginx
# Save as frontend/nginx.conf
server {
    listen 80;
    server_name _;
    
    location / {
        root /usr/share/nginx/html;
        index index.html index.htm;
        try_files $uri $uri/ /index.html;
    }
    
    # Handle API requests
    location /api/ {
        proxy_pass http://backend:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    # Handle media files
    location /media/ {
        proxy_pass http://backend:8000;
    }
}
```

---

## 🚀 **Step 4: Deploy and Start Services**

### **4.1 Build and Start**
```bash
# SSH into your Pi
cd ~/department-portal

# Get your Pi's IP address
PI_IP=$(hostname -I | awk '{print $1}')
echo "Pi IP Address: $PI_IP"

# Update frontend environment variable
sed -i "s/\[PI_IP_ADDRESS\]/$PI_IP/g" docker-compose.prod.yml

# Build and start services
docker-compose -f docker-compose.prod.yml up -d --build

# Check status
docker-compose -f docker-compose.prod.yml ps
```

### **4.2 Initialize Database**
```bash
# Run migrations
docker-compose -f docker-compose.prod.yml exec backend python manage.py migrate

# Create superuser
docker-compose -f docker-compose.prod.yml exec backend python manage.py createsuperuser

# Load initial data (if you have fixtures)
# docker-compose -f docker-compose.prod.yml exec backend python manage.py loaddata initial_data.json
```

### **4.3 Setup AI Model (Optional)**
```bash
# Pull the AI model
docker-compose -f docker-compose.prod.yml exec ollama ollama pull phi3:mini
```

---

## 🔄 **Step 5: Auto-Start on Boot**

### **5.1 Create Systemd Service**
```bash
# Create service file
sudo nano /etc/systemd/system/department-portal.service
```

```ini
[Unit]
Description=Department Portal
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/home/pi/department-portal
ExecStart=/usr/bin/docker-compose -f docker-compose.prod.yml up -d
ExecStop=/usr/bin/docker-compose -f docker-compose.prod.yml down
TimeoutStartSec=0
User=pi

[Install]
WantedBy=multi-user.target
```

### **5.2 Enable Auto-Start**
```bash
# Enable the service
sudo systemctl enable department-portal.service

# Start the service
sudo systemctl start department-portal.service

# Check status
sudo systemctl status department-portal.service
```

---

## 🌐 **Step 6: Network Access**

### **6.1 Find Your Pi's IP**
```bash
# On the Pi
hostname -I

# Or check your router's admin panel
```

### **6.2 Access Your Portal**
- **Frontend**: `http://[PI_IP_ADDRESS]`
- **Admin**: `http://[PI_IP_ADDRESS]/admin`
- **API**: `http://[PI_IP_ADDRESS]:8000/api/v1`

---

## 🔧 **Step 7: Maintenance Commands**

### **7.1 Useful Commands**
```bash
# View logs
docker-compose -f docker-compose.prod.yml logs -f

# Restart services
sudo systemctl restart department-portal

# Update application
cd ~/department-portal
git pull  # if using Git
docker-compose -f docker-compose.prod.yml down
docker-compose -f docker-compose.prod.yml up -d --build

# Backup database
docker-compose -f docker-compose.prod.yml exec postgres pg_dump -U dwadmin dwportal > backup_$(date +%Y%m%d).sql

# Monitor resources
htop
docker stats
```

### **7.2 Troubleshooting**
```bash
# Check service status
sudo systemctl status department-portal

# Check Docker logs
docker-compose -f docker-compose.prod.yml logs

# Free up space
docker system prune -f
docker volume prune -f
```

---

## 🔒 **Step 8: Security & Performance**

### **8.1 Basic Security**
```bash
# Change default passwords
sudo passwd pi

# Configure firewall
sudo ufw enable
sudo ufw allow ssh
sudo ufw allow 80/tcp
sudo ufw allow 8000/tcp

# Update regularly
sudo apt update && sudo apt upgrade -y
```

### **8.2 Performance Optimization**
```bash
# Increase swap (for Pi with limited RAM)
sudo dphys-swapfile swapoff
sudo nano /etc/dphys-swapfile
# Set CONF_SWAPSIZE=2048
sudo dphys-swapfile setup
sudo dphys-swapfile swapon

# GPU memory split (reduce GPU memory for headless)
sudo raspi-config
# Advanced Options > Memory Split > Set to 16
```

---

## ✅ **Verification Checklist**

- [ ] Pi is accessible via SSH
- [ ] Docker and Docker Compose installed
- [ ] Project files transferred
- [ ] Services start successfully
- [ ] Database initialized with admin user
- [ ] Frontend accessible from other devices
- [ ] Auto-start service enabled
- [ ] Backup strategy in place

---

## 🆘 **Quick Help**

**If something goes wrong:**
1. Check logs: `docker-compose -f docker-compose.prod.yml logs`
2. Restart services: `sudo systemctl restart department-portal`
3. Check Pi resources: `htop` and `df -h`
4. Verify network: `ping [PI_IP_ADDRESS]`

**Your Portal will be accessible at:**
- **Main App**: `http://[PI_IP_ADDRESS]`
- **From any device on your network**
- **24/7 availability** (as long as Pi is powered) 