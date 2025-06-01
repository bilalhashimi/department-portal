# 📶 WiFi Network Setup Guide

Run the Department Portal on your local WiFi network for easy access from any device.

## 🚀 Quick Start

### Option 1: One-Command Setup (Recommended)
```bash
./start-wifi-portal.sh
```

### Option 2: Backend Only
```bash
./run-local-wifi.sh
```

## 📋 Prerequisites

Before running the portal, ensure you have:

- ✅ **PostgreSQL** installed and running
- ✅ **Node.js** (v16 or higher)
- ✅ **Python 3.8+**
- ✅ **Git** (for version control)

### Installing Prerequisites

**macOS (using Homebrew):**
```bash
# Install PostgreSQL
brew install postgresql
brew services start postgresql

# Install Node.js
brew install node

# Python should be pre-installed, verify:
python3 --version
```

**Ubuntu/Debian:**
```bash
# Install PostgreSQL
sudo apt update
sudo apt install postgresql postgresql-contrib
sudo systemctl start postgresql

# Install Node.js
sudo apt install nodejs npm

# Install Python
sudo apt install python3 python3-pip python3-venv
```

## 🌐 Access Information

Once started, the portal will be available at:

### 📱 **Main URLs:**
- **Portal:** `http://192.168.7.230:5173` (Your actual IP will be shown)
- **Admin Panel:** `http://192.168.7.230:8000/admin`
- **API:** `http://192.168.7.230:8000/api`

### 👤 **Default Admin Login:**
- **Email:** `admin@department.local`
- **Password:** `admin123`

## 📱 Device Access

### For Phones/Tablets:
1. Connect to the same WiFi network
2. Open browser and go to: `http://192.168.7.230:5173`
3. Add to home screen for app-like experience

### For Other Computers:
1. Connect to the same WiFi network
2. Open any browser
3. Navigate to the portal URL

## 🔧 Configuration

### Network IP Detection
The script automatically detects your local IP address. If you need to manually set it:

```bash
# Backend (.env.local)
DJANGO_HOST=192.168.7.230
DJANGO_PORT=8000

# Frontend (.env.local)
VITE_API_URL=http://192.168.7.230:8000/api/v1
```

### Security Settings
For local network use, these settings are configured:

```python
# Django settings
ALLOWED_HOSTS = ["*"]  # Allow all hosts
CORS_ALLOW_ALL_ORIGINS = True  # Allow all CORS requests
DEBUG = True  # Enable debug mode
```

## 📊 Features Available

### ✅ **Core Features:**
- Document upload (admin only)
- Document search and browsing
- User authentication
- File preview and download
- Mobile-responsive design

### ⚠️ **AI Features (Optional):**
- Vector search (requires Qdrant)
- AI chat assistant (requires Ollama)
- Document indexing (requires Celery + Redis)

## 🛠️ Troubleshooting

### Common Issues:

**1. PostgreSQL not running:**
```bash
# macOS
brew services start postgresql

# Linux
sudo systemctl start postgresql
```

**2. Port already in use:**
```bash
# Kill processes on ports 8000 or 5173
lsof -ti:8000 | xargs kill -9
lsof -ti:5173 | xargs kill -9
```

**3. Permission denied:**
```bash
chmod +x start-wifi-portal.sh
```

**4. Database connection error:**
```bash
# Create database manually
createdb department_portal
```

**5. Can't access from other devices:**
- Check firewall settings
- Ensure devices are on same WiFi network
- Try the specific IP address shown in the terminal

### Getting Your Network IP:
```bash
# macOS/Linux
ifconfig | grep "inet " | grep -v 127.0.0.1

# Windows
ipconfig | findstr "IPv4"
```

## 🛑 Stopping the Portal

Press `Ctrl+C` in the terminal where the script is running, or:

```bash
# Kill background processes
pkill -f "runserver"
pkill -f "npm run dev"
```

## 🔒 Security Notes

**For Local Network Use Only:**
- This setup is designed for trusted local networks
- Default settings allow broad access for convenience
- Change admin password for production use
- Consider enabling HTTPS for sensitive documents

## 📚 Advanced Setup

### Custom Domain (Optional):
1. Edit `/etc/hosts` on devices
2. Add: `192.168.7.230 department.local`
3. Access via: `http://department.local:5173`

### Port Forwarding (Router Access):
1. Configure router port forwarding
2. Forward external port to `192.168.7.230:5173`
3. Access from internet via router's public IP

---

## 🎉 Enjoy Your Department Portal!

Your portal is now accessible to everyone on your WiFi network. Perfect for:
- 🏠 Home offices
- 🏢 Small businesses  
- 🎓 Educational environments
- 👥 Team collaboration

Need help? Check the logs in the terminal or refer to the main documentation. 