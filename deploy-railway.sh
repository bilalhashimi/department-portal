#!/bin/bash

# 🚂 Railway Deployment Preparation Script

echo "🚂 Preparing Department Portal for Railway Deployment..."
echo "=================================================="

# Check if git is initialized
if [ ! -d ".git" ]; then
    echo "Initializing Git repository..."
    git init
    git add .
    git commit -m "Initial commit - Department Portal"
fi

# Generate a secure secret key
echo ""
echo "🔐 Generating secure SECRET_KEY..."
SECRET_KEY=$(python3 -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())")
echo "SECRET_KEY=$SECRET_KEY"
echo ""

echo "📋 Railway Deployment Checklist:"
echo "================================"
echo ""
echo "✅ Files created:"
echo "   - railway.json (Railway config)"
echo "   - Dockerfile.railway (Optimized for Railway)"
echo "   - railway-env-template.txt (Environment variables)"
echo "   - RAILWAY_DEPLOYMENT.md (Complete guide)"
echo ""
echo "🔧 Next Steps:"
echo "1. 📚 Read RAILWAY_DEPLOYMENT.md for complete instructions"
echo "2. 🌐 Go to https://railway.app and create account"
echo "3. 🔗 Connect your GitHub repository"
echo "4. 🛢️ Add PostgreSQL database"
echo "5. ⚙️ Set environment variables from railway-env-template.txt"
echo "6. 🚀 Deploy!"
echo ""
echo "🔒 Privacy Features Included:"
echo "   - Admin-only access controls"
echo "   - Document visibility settings"  
echo "   - Optional basic authentication"
echo "   - HTTPS encryption"
echo ""
echo "💡 Your SECRET_KEY (copy this to Railway):"
echo "SECRET_KEY=$SECRET_KEY"
echo ""
echo "🎯 After deployment, your portal will be accessible at:"
echo "https://your-app-name.railway.app"
echo ""
echo "Happy deploying! 🚂✨" 