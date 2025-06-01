#!/bin/bash

# 🚀 Department Portal - Raspberry Pi Deployment Script
# This script automates the deployment process to your Raspberry Pi

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PI_USER="pi"
PI_HOST=""
PROJECT_DIR="~/department-portal"

# Functions
print_step() {
    echo -e "${BLUE}==>${NC} ${GREEN}$1${NC}"
}

print_warning() {
    echo -e "${YELLOW}Warning:${NC} $1"
}

print_error() {
    echo -e "${RED}Error:${NC} $1"
}

# Get Pi IP address
get_pi_ip() {
    echo -e "${BLUE}Please enter your Raspberry Pi's IP address or hostname (e.g., raspberrypi.local):${NC}"
    read -p "Pi IP/Hostname: " PI_HOST
    
    # Check if it's a hostname (contains letters) or IP address
    if [[ $PI_HOST =~ ^[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}$ ]]; then
        # It's an IP address - validate format
        echo "Using IP address: $PI_HOST"
    elif [[ $PI_HOST =~ ^[a-zA-Z0-9.-]+$ ]]; then
        # It's a hostname - validate it resolves
        if ping -c 1 "$PI_HOST" >/dev/null 2>&1; then
            echo "Hostname $PI_HOST resolved successfully"
        else
            print_error "Cannot resolve hostname: $PI_HOST"
            echo "Please check that your Pi is powered on and connected to the network"
            exit 1
        fi
    else
        print_error "Invalid IP address or hostname format"
        exit 1
    fi
}

# Test SSH connection
test_ssh() {
    print_step "Testing SSH connection to $PI_HOST..."
    if ssh -o ConnectTimeout=5 -o BatchMode=yes $PI_USER@$PI_HOST exit 2>/dev/null; then
        print_step "SSH connection successful!"
    else
        print_error "Cannot connect to Pi via SSH. Please check:"
        echo "  1. Pi is powered on and connected to network"
        echo "  2. SSH is enabled on the Pi"
        echo "  3. IP address is correct"
        echo "  4. You can access the Pi: ssh $PI_USER@$PI_HOST"
        exit 1
    fi
}

# Transfer files
transfer_files() {
    print_step "Transferring files to Raspberry Pi..."
    
    # Create project directory on Pi
    ssh $PI_USER@$PI_HOST "mkdir -p $PROJECT_DIR"
    
    # Transfer files using rsync
    rsync -avz --progress \
        --exclude 'node_modules' \
        --exclude '__pycache__' \
        --exclude '.git' \
        --exclude '*.pyc' \
        --exclude '.DS_Store' \
        --exclude 'venv' \
        --exclude '.env' \
        ./ $PI_USER@$PI_HOST:$PROJECT_DIR/
    
    print_step "Files transferred successfully!"
}

# Setup Pi environment
setup_pi() {
    print_step "Setting up Raspberry Pi environment..."
    
    ssh $PI_USER@$PI_HOST << 'EOF'
        # Update system
        sudo apt update && sudo apt upgrade -y
        
        # Install Docker if not present
        if ! command -v docker &> /dev/null; then
            echo "Installing Docker..."
            curl -fsSL https://get.docker.com -o get-docker.sh
            sudo sh get-docker.sh
            sudo usermod -aG docker $USER
            rm get-docker.sh
        fi
        
        # Install Docker Compose if not present
        if ! command -v docker-compose &> /dev/null; then
            echo "Installing Docker Compose..."
            sudo apt install -y docker-compose
        fi
        
        # Install additional tools
        sudo apt install -y git curl vim htop
        
        echo "Pi environment setup complete!"
EOF
}

# Deploy application
deploy_app() {
    print_step "Deploying application on Raspberry Pi..."
    
    # Update docker-compose.prod.yml with Pi IP
    sed -i.bak "s/PI_IP_PLACEHOLDER/$PI_HOST/g" docker-compose.prod.yml
    
    # Transfer updated docker-compose file
    scp docker-compose.prod.yml $PI_USER@$PI_HOST:$PROJECT_DIR/
    
    ssh $PI_USER@$PI_HOST << EOF
        cd $PROJECT_DIR
        
        # Stop any existing containers
        docker-compose -f docker-compose.prod.yml down 2>/dev/null || true
        
        # Build and start services
        echo "Building and starting services..."
        docker-compose -f docker-compose.prod.yml up -d --build
        
        # Wait for services to start
        echo "Waiting for services to start..."
        sleep 30
        
        # Check if backend is ready
        echo "Checking backend status..."
        for i in {1..30}; do
            if docker-compose -f docker-compose.prod.yml exec -T backend python manage.py check &>/dev/null; then
                echo "Backend is ready!"
                break
            fi
            echo "Waiting for backend... (\$i/30)"
            sleep 10
        done
        
        # Run migrations
        echo "Running database migrations..."
        docker-compose -f docker-compose.prod.yml exec -T backend python manage.py migrate
        
        # Check service status
        echo "Service status:"
        docker-compose -f docker-compose.prod.yml ps
EOF
    
    # Restore original docker-compose file
    mv docker-compose.prod.yml.bak docker-compose.prod.yml
}

# Create systemd service
create_service() {
    print_step "Creating systemd service for auto-start..."
    
    ssh $PI_USER@$PI_HOST << 'EOF'
        # Create systemd service file
        sudo tee /etc/systemd/system/department-portal.service > /dev/null << 'SERVICE'
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
SERVICE
        
        # Enable and start service
        sudo systemctl daemon-reload
        sudo systemctl enable department-portal.service
        sudo systemctl start department-portal.service
        
        echo "Systemd service created and enabled!"
EOF
}

# Create admin user
create_admin() {
    print_step "Setting up admin user..."
    echo -e "${YELLOW}You'll need to create an admin user for the portal.${NC}"
    echo "This will be done interactively on the Pi."
    
    ssh -t $PI_USER@$PI_HOST "cd $PROJECT_DIR && docker-compose -f docker-compose.prod.yml exec backend python manage.py createsuperuser"
}

# Final status check
check_status() {
    print_step "Checking final deployment status..."
    
    ssh $PI_USER@$PI_HOST << EOF
        cd $PROJECT_DIR
        echo "=== Service Status ==="
        docker-compose -f docker-compose.prod.yml ps
        
        echo -e "\n=== System Service Status ==="
        sudo systemctl status department-portal --no-pager
        
        echo -e "\n=== Resource Usage ==="
        docker stats --no-stream
EOF
    
    print_step "Deployment completed successfully! 🎉"
    echo ""
    echo -e "${GREEN}Your Department Portal is now running on:${NC}"
    echo -e "  Frontend: ${BLUE}http://$PI_HOST${NC}"
    echo -e "  Admin:    ${BLUE}http://$PI_HOST/admin${NC}"
    echo -e "  API:      ${BLUE}http://$PI_HOST:8000/api/v1${NC}"
    echo ""
    echo -e "${YELLOW}The portal will automatically start when you reboot your Pi!${NC}"
    echo ""
    echo -e "${GREEN}Useful commands for maintenance:${NC}"
    echo "  Check logs:    ssh $PI_USER@$PI_HOST 'cd $PROJECT_DIR && docker-compose -f docker-compose.prod.yml logs -f'"
    echo "  Restart:       ssh $PI_USER@$PI_HOST 'sudo systemctl restart department-portal'"
    echo "  Stop:          ssh $PI_USER@$PI_HOST 'sudo systemctl stop department-portal'"
}

# Main deployment process
main() {
    echo -e "${GREEN}🚀 Department Portal - Raspberry Pi Deployment${NC}"
    echo "=============================================="
    echo ""
    
    # Check if required files exist
    if [[ ! -f "docker-compose.prod.yml" ]]; then
        print_error "docker-compose.prod.yml not found. Please run this script from the project root."
        exit 1
    fi
    
    get_pi_ip
    test_ssh
    transfer_files
    setup_pi
    deploy_app
    create_service
    create_admin
    check_status
}

# Run main function
main 