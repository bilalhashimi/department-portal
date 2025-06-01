#!/bin/bash

# 📶 Department Portal - Local WiFi Network Deployment
# Run the portal on your local network for WiFi access

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}📶 Starting Department Portal for WiFi Network Access${NC}"
echo "========================================================"

# Get local IP address
LOCAL_IP=$(ifconfig | grep "inet " | grep -v 127.0.0.1 | awk '{print $2}' | head -1)
echo -e "${GREEN}🌐 Local IP Address: ${LOCAL_IP}${NC}"

# Check if PostgreSQL is running
echo -e "\n${YELLOW}🔍 Checking PostgreSQL...${NC}"
if ! pgrep -x "postgres" > /dev/null; then
    echo -e "${RED}❌ PostgreSQL is not running${NC}"
    echo "Please start PostgreSQL first:"
    echo "  brew services start postgresql"
    exit 1
fi
echo -e "${GREEN}✅ PostgreSQL is running${NC}"

# Setup database if needed
echo -e "\n${YELLOW}🗄️ Setting up database...${NC}"
cd backend

# Create database if it doesn't exist
createdb department_portal 2>/dev/null || echo "Database already exists"

# Copy environment file
cp .env.local .env

# Install dependencies
echo -e "\n${YELLOW}📦 Installing Python dependencies...${NC}"
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi
source venv/bin/activate
pip install -r requirements.txt

# Run migrations
echo -e "\n${YELLOW}🔄 Running database migrations...${NC}"
python manage.py makemigrations
python manage.py migrate

# Create superuser if needed
echo -e "\n${YELLOW}👤 Creating admin user...${NC}"
python manage.py shell << EOF
from accounts.models import User
if not User.objects.filter(email='admin@department.local').exists():
    User.objects.create_superuser(
        email='admin@department.local',
        password='admin123',
        first_name='Admin',
        last_name='User',
        role='admin'
    )
    print("✅ Admin user created: admin@department.local / admin123")
else:
    print("✅ Admin user already exists: admin@department.local / admin123")
EOF

# Start Django server on network IP
echo -e "\n${GREEN}🚀 Starting Django server on ${LOCAL_IP}:8000${NC}"
echo -e "${BLUE}Access URLs:${NC}"
echo -e "  • Main App: ${GREEN}http://${LOCAL_IP}:8000${NC}"
echo -e "  • Admin: ${GREEN}http://${LOCAL_IP}:8000/admin${NC}"
echo -e "  • API: ${GREEN}http://${LOCAL_IP}:8000/api${NC}"
echo ""
echo -e "${YELLOW}📱 Share these URLs with anyone on your WiFi network!${NC}"
echo -e "${YELLOW}Admin Login: admin@department.local / admin123${NC}"
echo ""
echo -e "${BLUE}Press Ctrl+C to stop the server${NC}"
echo "========================================================"

# Start server
python manage.py runserver ${LOCAL_IP}:8000 