# 🍓 **Raspberry Pi Setup Checklist**

## ✅ **Before You Start**

### **Hardware Setup:**
- [ ] Raspberry Pi 4 (4GB+ RAM recommended)
- [ ] 32GB+ MicroSD card (Class 10)
- [ ] Stable power supply connected
- [ ] Ethernet cable connected (recommended)
- [ ] Pi is powered on and booted

### **Initial Pi Configuration:**
- [ ] Raspberry Pi OS installed (64-bit preferred)
- [ ] SSH enabled during setup
- [ ] Pi connected to your network
- [ ] You know the Pi's IP address
- [ ] You can SSH into the Pi: `ssh pi@[PI_IP]`

---

## 🚀 **Automated Deployment**

### **Step 1: Run the Deployment Script**
```bash
# From your laptop, in the project directory
./deploy-to-pi.sh
```

The script will:
1. ✅ Test SSH connection to your Pi
2. ✅ Transfer all project files
3. ✅ Install Docker and Docker Compose
4. ✅ Build and start all services
5. ✅ Setup database and migrations
6. ✅ Create auto-start service
7. ✅ Help you create an admin user

### **Step 2: Access Your Portal**
- **Frontend**: `http://[PI_IP]`
- **Admin Panel**: `http://[PI_IP]/admin`
- **API**: `http://[PI_IP]:8000/api/v1`

---

## 🔧 **Manual Deployment (Alternative)**

If the automated script doesn't work, follow the detailed guide in `RASPBERRY_PI_DEPLOYMENT.md`

---

## 📱 **Post-Deployment**

### **Verify Everything Works:**
- [ ] Can access frontend from laptop/phone
- [ ] Can login to admin panel
- [ ] Document upload works (admin only)
- [ ] AI search functions properly
- [ ] Services restart after Pi reboot

### **Optional Optimizations:**
- [ ] Set up regular database backups
- [ ] Configure port forwarding for external access
- [ ] Set up monitoring/alerts
- [ ] Update frontend API URL in other devices

---

## 🆘 **Troubleshooting Commands**

```bash
# SSH into your Pi
ssh pi@[PI_IP]

# Check service status
sudo systemctl status department-portal

# View application logs
cd ~/department-portal
docker-compose -f docker-compose.prod.yml logs -f

# Restart everything
sudo systemctl restart department-portal

# Check resource usage
htop
docker stats

# Free up space if needed
docker system prune -f
```

---

## 🌟 **Benefits of Pi Deployment**

✅ **24/7 Availability** - Runs continuously  
✅ **Low Power** - Consumes only ~5-10W  
✅ **Network Access** - Available to all devices on your network  
✅ **Auto-Start** - Restarts automatically after power outages  
✅ **Cost Effective** - One-time setup, no monthly fees  
✅ **Local Control** - Your data stays on your network  

---

## 📝 **Important Notes**

- The Pi will use its own IP address, different from your laptop
- Update any bookmarks/shortcuts to use the new Pi IP
- The admin-only upload restrictions are still in place
- All document visibility settings work the same
- AI features require the Ollama service to be running (may be slow on Pi)

---

## 🔄 **Maintenance Schedule**

**Weekly:**
- Check available disk space: `df -h`
- Monitor service health: `docker-compose ps`

**Monthly:**
- Update Pi OS: `sudo apt update && sudo apt upgrade`
- Backup database: `docker-compose exec postgres pg_dump...`

**As Needed:**
- Update application code when you make changes
- Scale resources if performance is slow 