@echo off
echo 🚀 Starting deployment to Fly.io...

REM Check if flyctl is installed
flyctl version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ flyctl is not installed. Please install it first:
    echo    https://fly.io/docs/hands-on/install-flyctl/
    pause
    exit /b 1
)

REM Check if user is authenticated
flyctl auth whoami >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Not authenticated with Fly.io. Please run:
    echo    flyctl auth login
    pause
    exit /b 1
)

echo 🔧 Setting up environment variables...

REM Check if app exists, if not create it
flyctl apps show telegram-domain-checker >nul 2>&1
if %errorlevel% neq 0 (
    echo 📱 Creating new Fly.io app...
    flyctl apps create telegram-domain-checker --org personal
)

echo 🔐 Setting up secrets...
flyctl secrets set TELEGRAM_TOKEN="8018331092:AAEvZ1vqaawJGJ7FngNJD3ijqj0LogsNCkA" ADMIN_CHAT_IDS="5741184861,6993283728" MONGO_URL="mongodb+srv://iravwyuhor:WkfDwy4aR8jbkSD0@domainmonitor.nzk39ze.mongodb.net/?retryWrites=true&w=majority&appName=domainMonitor"

echo 🚀 Deploying application...
flyctl deploy --ha=false

echo ✅ Deployment completed!
echo 📊 Checking app status...
flyctl status

echo.
echo 🎉 Your Telegram bot is now deployed on Fly.io!
echo 📱 App URL: https://telegram-domain-checker.fly.dev
echo 📊 Monitor: flyctl logs
echo 🔧 Scale: flyctl scale count 1

pause