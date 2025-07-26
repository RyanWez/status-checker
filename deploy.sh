#!/bin/bash

# Deployment script for Fly.io
# Make sure you have flyctl installed and authenticated

echo "🚀 Starting deployment to Fly.io..."

# Check if flyctl is installed
if ! command -v flyctl &> /dev/null; then
    echo "❌ flyctl is not installed. Please install it first:"
    echo "   curl -L https://fly.io/install.sh | sh"
    exit 1
fi

# Check if user is authenticated
if ! flyctl auth whoami &> /dev/null; then
    echo "❌ Not authenticated with Fly.io. Please run:"
    echo "   flyctl auth login"
    exit 1
fi

# Set environment variables (if not already set)
echo "🔧 Setting up environment variables..."

# Check if app exists, if not create it
if ! flyctl apps show telegram-domain-checker &> /dev/null; then
    echo "📱 Creating new Fly.io app..."
    flyctl apps create telegram-domain-checker --org personal
fi

# Set secrets (environment variables)
echo "🔐 Setting up secrets..."
flyctl secrets set \
    TELEGRAM_TOKEN="8018331092:AAEvZ1vqaawJGJ7FngNJD3ijqj0LogsNCkA" \
    ADMIN_CHAT_IDS="5741184861" \
    MONGO_URL="mongodb+srv://iravwyuhor:WkfDwy4aR8jbkSD0@domainmonitor.nzk39ze.mongodb.net/?retryWrites=true&w=majority&appName=domainMonitor"

# Deploy the application
echo "🚀 Deploying application..."
flyctl deploy --ha=false

# Check deployment status
echo "✅ Deployment completed!"
echo "📊 Checking app status..."
flyctl status

echo ""
echo "🎉 Your Telegram bot is now deployed on Fly.io!"
echo "📱 App URL: https://telegram-domain-checker.fly.dev"
echo "📊 Monitor: flyctl logs"
echo "🔧 Scale: flyctl scale count 1"