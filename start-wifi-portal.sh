#!/bin/bash

# 📶 Department Portal - Complete WiFi Network Deployment
# Starts both frontend and backend for network access

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m' # No Color

echo -e "${PURPLE}🌐 DEPARTMENT PORTAL - WiFi Network Deployment${NC}"
echo "========================================================="

# Get local IP address
LOCAL_IP=$(ifconfig | grep "inet " | grep -v 127.0.0.1 | awk '{print $2}' | head -1)
echo -e "${GREEN}📡 Your Network IP: ${LOCAL_IP}${NC}"

# Check prerequisites
echo -e "\n${YELLOW}🔍 Checking prerequisites...${NC}"

# Check PostgreSQL
if ! pgrep -x "postgres" > /dev/null; then
    echo -e "${RED}❌ PostgreSQL is not running${NC}"
    echo "Starting PostgreSQL..."
    brew services start postgresql || {
        echo -e "${RED}Failed to start PostgreSQL. Please install and start it manually.${NC}"
        exit 1
    }
    sleep 3
fi
echo -e "${GREEN}✅ PostgreSQL is running${NC}"

# Check Node.js
if ! command -v node &> /dev/null; then
    echo -e "${RED}❌ Node.js is not installed${NC}"
    echo "Please install Node.js from https://nodejs.org/"
    exit 1
fi
echo -e "${GREEN}✅ Node.js is available${NC}"

# Check Python
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python3 is not installed${NC}"
    echo "Please install Python3"
    exit 1
fi
echo -e "${GREEN}✅ Python3 is available${NC}"

# Setup Backend
echo -e "\n${BLUE}🔧 Setting up Backend...${NC}"
cd backend

# Create database if it doesn't exist
echo -e "${YELLOW}📊 Setting up database...${NC}"
createdb department_portal 2>/dev/null && echo -e "${GREEN}✅ Database created${NC}" || echo -e "${YELLOW}ℹ️ Database already exists${NC}"

# Copy environment file
cp .env.local .env 2>/dev/null || true

# Create virtual environment and install dependencies
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}🐍 Creating Python virtual environment...${NC}"
    python3 -m venv venv
fi

echo -e "${YELLOW}📦 Installing Python dependencies...${NC}"
source venv/bin/activate
pip install -r requirements.txt > /dev/null

# Run migrations
echo -e "${YELLOW}🔄 Running database migrations...${NC}"
python manage.py makemigrations > /dev/null
python manage.py migrate > /dev/null

# Create admin user
echo -e "${YELLOW}👤 Setting up admin user...${NC}"
python manage.py shell << EOF > /dev/null
from accounts.models import User
if not User.objects.filter(email='admin@department.local').exists():
    User.objects.create_superuser(
        email='admin@department.local',
        password='admin123',
        first_name='Admin',
        last_name='User',
        role='admin'
    )
    print("Admin user created")
EOF

# Setup Frontend
echo -e "\n${BLUE}🎨 Setting up Frontend...${NC}"
cd ../frontend

echo -e "${YELLOW}📦 Installing frontend dependencies...${NC}"
if [ ! -d "node_modules" ]; then
    npm install > /dev/null
fi

# Function to start backend
start_backend() {
    echo -e "${GREEN}🚀 Starting Backend Server...${NC}"
    cd backend
    source venv/bin/activate
    python manage.py runserver ${LOCAL_IP}:8000 &
    BACKEND_PID=$!
    echo $BACKEND_PID > ../backend.pid
    cd ..
}

# Function to start frontend
start_frontend() {
    echo -e "${GREEN}🎨 Starting Frontend Server...${NC}"
    cd frontend
    npm run dev &
    FRONTEND_PID=$!
    echo $FRONTEND_PID > ../frontend.pid
    cd ..
}

# Start both servers
echo -e "\n${PURPLE}🚀 Starting Department Portal...${NC}"

start_backend
sleep 3
start_frontend

# Wait for servers to start
echo -e "\n${YELLOW}⏳ Waiting for servers to start...${NC}"
sleep 5

# Display access information
echo -e "\n${GREEN}🎉 DEPARTMENT PORTAL IS READY!${NC}"
echo "========================================================="
echo -e "${BLUE}📱 Access from any device on your WiFi network:${NC}"
echo ""
echo -e "  ${GREEN}🌐 Main Portal:${NC}    http://${LOCAL_IP}:5173"
echo -e "  ${GREEN}⚙️  Admin Panel:${NC}    http://${LOCAL_IP}:8000/admin"
echo -e "  ${GREEN}🔌 API Endpoint:${NC}   http://${LOCAL_IP}:8000/api"
echo ""
echo -e "${YELLOW}👤 Admin Login Credentials:${NC}"
echo -e "  Email: ${GREEN}admin@department.local${NC}"
echo -e "  Password: ${GREEN}admin123${NC}"
echo ""
echo -e "${BLUE}📋 Features Available:${NC}"
echo -e "  ✅ Document Upload (Admin Only)"
echo -e "  ✅ Document Search & Browse"
echo -e "  ✅ User Authentication"
echo -e "  ✅ Mobile Responsive Design"
echo -e "  ✅ File Preview & Download"
echo ""
echo -e "${PURPLE}📱 Share this URL with others on your WiFi:${NC}"
echo -e "  ${GREEN}http://${LOCAL_IP}:5173${NC}"
echo ""
echo -e "${YELLOW}🛑 To stop the servers, press Ctrl+C${NC}"
echo "========================================================="

# Cleanup function
cleanup() {
    echo -e "\n${YELLOW}🛑 Stopping servers...${NC}"
    
    if [ -f backend.pid ]; then
        kill $(cat backend.pid) 2>/dev/null || true
        rm backend.pid
    fi
    
    if [ -f frontend.pid ]; then
        kill $(cat frontend.pid) 2>/dev/null || true
        rm frontend.pid
    fi
    
    echo -e "${GREEN}✅ Servers stopped${NC}"
    exit 0
}

# Set trap to cleanup on exit
trap cleanup SIGINT SIGTERM

# Keep script running
wait 