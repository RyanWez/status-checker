# 🚀 Fly.io Deployment Guide - Telegram Domain Checker Bot

## 📋 Prerequisites

1. **Install Fly.io CLI**
   ```bash
   # Windows (PowerShell)
   iwr https://fly.io/install.ps1 -useb | iex
   
   # Or download from: https://fly.io/docs/hands-on/install-flyctl/
   ```

2. **Authenticate with Fly.io**
   ```bash
   flyctl auth login
   ```

3. **Verify your environment variables are set in `.env`**

## 🎯 Step-by-Step Deployment

### Step 1: Prepare Your Application
```bash
# Make sure all files are ready
ls -la
# You should see: Dockerfile, fly.toml, requirements.txt, main.py, etc.
```

### Step 2: Create Fly.io Application
```bash
# Create new app (if not exists)
flyctl apps create telegram-domain-checker --org personal

# Or use existing app
flyctl apps list
```

### Step 3: Set Environment Variables
```bash
# Set your secrets (replace with your actual values)
flyctl secrets set TELEGRAM_TOKEN="your_bot_token_here"
flyctl secrets set ADMIN_CHAT_IDS="your_chat_ids_here"
flyctl secrets set MONGO_URL="your_mongodb_url_here"

# Verify secrets are set
flyctl secrets list
```

### Step 4: Deploy Application
```bash
# Deploy with single instance (free tier)
flyctl deploy --ha=false

# Monitor deployment
flyctl logs
```

### Step 5: Verify Deployment
```bash
# Check app status
flyctl status

# Check health endpoint
curl https://telegram-domain-checker.fly.dev/health

# Monitor logs
flyctl logs --follow
```

## ⚡ Performance Optimizations Applied

### 1. **Docker Optimizations**
- Multi-stage build for smaller image size
- Python 3.11 slim base image
- Optimized layer caching
- Non-root user for security
- Health checks for monitoring

### 2. **Application Performance**
- **Async HTTP Client**: Using `aiohttp` for concurrent domain checking
- **Connection Pooling**: Optimized TCP connector settings
- **Batch Processing**: Domains processed in batches of 50
- **DNS Caching**: 5-minute DNS cache for repeated checks
- **Timeout Optimization**: Reduced timeouts for faster processing
- **Memory Management**: Efficient resource usage

### 3. **Database Optimizations**
- **Bulk Operations**: Bulk updates for better performance
- **Connection Pooling**: MongoDB connection optimization
- **Indexed Queries**: Optimized database queries
- **Batch Inserts**: Bulk domain additions

### 4. **Fly.io Configuration**
- **Region Selection**: Singapore (sin) for Asia-Pacific
- **Resource Allocation**: 512MB RAM, 1 CPU (free tier)
- **Health Checks**: Automated health monitoring
- **Auto-scaling**: Configured for single instance
- **Restart Policy**: Always restart on failure

## 📊 Monitoring & Maintenance

### Health Monitoring
```bash
# Check health status
curl https://telegram-domain-checker.fly.dev/health

# View metrics
curl https://telegram-domain-checker.fly.dev/metrics

# Monitor logs
flyctl logs --follow
```

### Scaling (if needed)
```bash
# Scale to multiple instances (paid plans)
flyctl scale count 2

# Scale resources
flyctl scale memory 1024
flyctl scale cpu 2
```

### Updates & Redeployment
```bash
# Redeploy after changes
flyctl deploy

# Restart app
flyctl apps restart telegram-domain-checker
```

## 🔧 Troubleshooting

### Common Issues

1. **Bot not responding**
   ```bash
   # Check logs
   flyctl logs
   
   # Verify secrets
   flyctl secrets list
   
   # Check health
   curl https://telegram-domain-checker.fly.dev/health
   ```

2. **Database connection issues**
   ```bash
   # Verify MongoDB URL
   flyctl secrets list
   
   # Test connection locally
   python -c "from services.database import DatabaseService; db = DatabaseService('your_mongo_url'); print('Connected!')"
   ```

3. **Memory issues**
   ```bash
   # Check resource usage
   flyctl status
   
   # Scale memory if needed
   flyctl scale memory 1024
   ```

### Performance Monitoring
```bash
# Monitor resource usage
flyctl metrics

# Check response times
flyctl logs | grep "response_time"

# Monitor domain check performance
flyctl logs | grep "Processing batch"
```

## 💰 Cost Optimization (Free Tier)

### Free Tier Limits
- **Compute**: 160 hours/month shared CPU
- **Memory**: Up to 256MB (we use 512MB)
- **Storage**: 3GB persistent volume
- **Bandwidth**: 160GB/month

### Optimization Tips
1. **Single Instance**: Use `--ha=false` for deployment
2. **Auto-stop**: Configure auto-stop for inactive periods
3. **Resource Limits**: Monitor usage with `flyctl metrics`
4. **Efficient Checking**: Optimized domain checking intervals

## 🚀 Advanced Configuration

### Custom Domain (Optional)
```bash
# Add custom domain
flyctl certs create your-domain.com

# Configure DNS
# Add CNAME record: your-domain.com -> telegram-domain-checker.fly.dev
```

### Environment-specific Deployments
```bash
# Production deployment
flyctl deploy --config fly.production.toml

# Staging deployment
flyctl deploy --config fly.staging.toml
```

### Backup & Recovery
```bash
# Export app configuration
flyctl config save

# Create volume snapshots (if using volumes)
flyctl volumes snapshots create
```

## 👥 User Management Features

### New Role-Based Access Control
- **Admin**: Full access to all features
- **User**: Read-only access to all domains
- **Guest**: Limited access to assigned groups

### User Management Commands (Admin Only)
```bash
# Add users (multiple formats)
/adduser 123456789 john_doe user
/adduser @john_doe user  # If user interacted recently
/adduser 987654321 jane_admin admin

# Find users by username
/finduser @john_doe

# Remove users
/removeuser 123456789

# List all users (text format)
/listusers

# Interactive user management (NEW!)
/userlists

# View your account info
/userinfo
```

### Interactive User Management Features
- **📱 Interactive Interface**: `/userlists` shows users with clickable buttons
- **👤 User Details**: Click on any user to see detailed information
- **🔄 Role Changes**: Change user roles with interactive buttons
- **🗑️ User Removal**: Remove users with confirmation dialogs
- **📄 Pagination**: Navigate through large user lists
- **🔄 Real-time Updates**: Instant feedback on all operations

### Permission System
- **Admins**: Can add/remove domains, manage users, bulk operations, see delete buttons
- **Users**: Can view and check all domains, cannot modify, no delete buttons shown
- **Guests**: Can only view assigned groups, cannot modify anything, no delete buttons shown

### 🔔 Notification System
- **Domain Down Alerts**: Automatic notifications when domains go from UP to DOWN
- **All Users Notified**: Sent to all bot users (admins + registered users)
- **No Spam**: Only notifies on status changes, not repeated DOWN states
- **Detailed Info**: Includes domain name, error message, and timestamp
- **Real-time**: Notifications sent immediately when issues are detected

## 📈 Performance Metrics

### Expected Performance
- **Domain Checking**: 100+ domains in ~30 seconds
- **Response Time**: < 2 seconds for bot commands
- **Memory Usage**: ~200-400MB
- **CPU Usage**: Low (< 50% most of the time)
- **User Management**: Instant role-based access control

### Monitoring Commands
```bash
# Real-time logs
flyctl logs --follow

# App metrics
flyctl metrics

# Health check
curl -s https://telegram-domain-checker.fly.dev/health | jq

# Performance test
time curl https://telegram-domain-checker.fly.dev/health
```

## 🎉 Success!

Your Telegram Domain Checker Bot is now running on Fly.io with:
- ✅ High performance domain checking
- ✅ Automatic health monitoring  
- ✅ Optimized resource usage
- ✅ Production-ready configuration
- ✅ Free tier compatibility

**Bot URL**: https://telegram-domain-checker.fly.dev
**Health Check**: https://telegram-domain-checker.fly.dev/health
**Metrics**: https://telegram-domain-checker.fly.dev/metrics

Happy monitoring! 🚀