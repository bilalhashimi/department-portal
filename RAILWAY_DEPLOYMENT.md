# 🚂 **Railway Private Deployment Guide**

## 🎯 **Deploy Your Private Department Portal**

### **Step 1: Create Railway Account**
1. Go to [railway.app](https://railway.app)
2. **Sign up** with GitHub (recommended)
3. **Verify** your account

### **Step 2: Create New Project**
1. Click **"New Project"**
2. Choose **"Deploy from GitHub repo"**
3. **Connect your GitHub** account
4. **Select** your department-portal repository

### **Step 3: Add PostgreSQL Database**
1. In your Railway project dashboard
2. Click **"+ New"** → **"Database"** → **"PostgreSQL"**
3. Railway will **auto-create** the database
4. **DATABASE_URL** will be automatically provided

### **Step 4: Configure Environment Variables**
Go to your service → **Variables** tab and add these:

```bash
# Security & Privacy
DEBUG=False
SECRET_KEY=your-super-secret-key-change-this
ALLOWED_HOSTS=*

# Private Access (Admin Only)
REQUIRE_LOGIN=True
ADMIN_ONLY_UPLOADS=True
PRIVATE_PORTAL=True

# Basic Auth (Extra Security Layer)
BASIC_AUTH_USERNAME=your_department_admin
BASIC_AUTH_PASSWORD=secure_password_here

# Admin User (Auto-created on first deploy)
DJANGO_SUPERUSER_USERNAME=admin
DJANGO_SUPERUSER_EMAIL=admin@yourcompany.com
DJANGO_SUPERUSER_PASSWORD=admin_password_123

# File Settings
MAX_UPLOAD_SIZE=100MB
ALLOWED_EXTENSIONS=pdf,doc,docx,txt,md

# Simplified for Railway
USE_VECTOR_DB=False
USE_REDIS=False
USE_OLLAMA=False

# Railway Port
PORT=8000
```

### **Step 5: Deploy**
1. **Push** your code to GitHub
2. Railway will **auto-deploy**
3. **Wait** 5-10 minutes for build
4. **Access** your portal at the provided Railway URL

---

## 🔒 **Privacy & Security Features**

### **Layer 1: Admin-Only Access**
- Only users with admin role can upload documents
- Document visibility controls (private/department/public)
- Login required for all access

### **Layer 2: Basic Authentication** (Optional)
- Username/password prompt before accessing site
- Extra security layer

### **Layer 3: Railway Network Security**
- HTTPS automatically enabled
- Railway's security infrastructure
- Private database connections

### **Layer 4: Application Security**
- Django security middleware
- CSRF protection
- Secure session handling

---

## 🌐 **Accessing Your Private Portal**

### **Your Portal URLs:**
- **Main App**: `https://your-app-name.railway.app`
- **Admin Panel**: `https://your-app-name.railway.app/admin`

### **Default Login:**
- **Username**: `admin` (or what you set in DJANGO_SUPERUSER_USERNAME)
- **Password**: `admin_password_123` (change this!)

### **First Login Steps:**
1. **Access** admin panel
2. **Change** admin password immediately
3. **Create** additional user accounts if needed
4. **Test** document upload functionality

---

## 💰 **Railway Pricing**

### **Free Tier:**
- **$5 monthly credit** (covers small apps)
- **500MB RAM**
- **1GB Disk**
- **Perfect for testing** and small teams

### **If You Need More:**
- **Pro Plan**: $20/month
- **Unlimited** deployments
- **8GB RAM**, **100GB Disk**

---

## 🔧 **Post-Deployment**

### **Share with Your Team:**
1. **Send URL**: `https://your-app-name.railway.app`
2. **Share login**: Basic auth credentials (if enabled)
3. **Admin accounts**: Create accounts for team admins

### **Customize Domain (Optional):**
1. **Railway Settings** → **Domains**
2. **Add** custom domain: `portal.yourcompany.com`
3. **Railway handles** SSL automatically

### **Monitor Usage:**
1. **Railway Dashboard** → **Metrics**
2. **Monitor** resource usage
3. **Scale** if needed

---

## 🆘 **Troubleshooting**

### **Build Fails:**
- Check **deploy logs** in Railway dashboard
- Verify all environment variables are set
- Ensure Docker syntax is correct

### **Can't Access Portal:**
- Check Railway service is **running**
- Verify **PORT=8000** environment variable
- Check deployment logs for errors

### **Database Issues:**
- Ensure PostgreSQL addon is **connected**
- Check **DATABASE_URL** is automatically set
- Run migrations in Railway console

### **Login Issues:**
- Use admin credentials from environment variables
- Reset admin password via Railway console
- Check DJANGO_SUPERUSER_* variables

---

## ✅ **Success! Your Portal is Live**

🎉 **Your department portal is now accessible anywhere with:**
- ✅ **Private access** controls
- ✅ **Admin-only** uploads  
- ✅ **Document** visibility settings
- ✅ **24/7 availability**
- ✅ **HTTPS** security
- ✅ **Professional** deployment

**Share the URL with your team and start using your private department portal!** 🚀 