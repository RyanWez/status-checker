# 🤖 Telegram Domain Status Checker Bot

A modern, modular Telegram bot that monitors domain health and provides instant notifications when domains go down. Built with Python using a clean, scalable architecture.

## ✨ Features

### 🔐 **Private & Secure**
- Private bot with admin-only access
- Environment-based configuration
- Secure authentication flow

### 🌐 **Domain Monitoring**
- Add/remove domains dynamically
- Automatic health checks every 5 minutes
- Manual on-demand checking
- Concurrent domain checking for speed

### 📱 **Modern Interactive UI**
- Interactive inline keyboards
- Paginated domain lists
- Real-time status updates
- Rich status indicators (✅ UP, 🚨 DOWN, ⚪ Unknown)

### 🔔 **Smart Notifications**
- Instant alerts when domains go DOWN
- No spam - only notifies on status changes
- Detailed error information
- Multi-admin support

### 📊 **Comprehensive Reporting**
- Domain status summaries
- Response time tracking
- Error details and history
- Sortable domain lists (DOWN domains first)

## 🏗️ Architecture

The bot follows a clean, modular architecture:

```
├── main.py                 # Main entry point & orchestration
├── config/
│   ├── __init__.py
│   └── settings.py         # Configuration management
├── services/
│   ├── __init__.py
│   ├── database.py         # MongoDB operations
│   └── checker.py          # Domain health checking
├── handlers/
│   ├── __init__.py
│   ├── authentication.py   # Login/logout flow
│   └── domains.py          # Domain management commands
├── requirements.txt        # Dependencies
├── test_bot.py            # Comprehensive test suite
└── .env                   # Environment variables
```

## 🚀 Quick Start

### 1. **Prerequisites**
- Python 3.8+
- MongoDB database
- Telegram Bot Token

### 2. **Installation**

```bash
# Clone the repository
git clone <repository-url>
cd telegram-domain-checker

# Install dependencies
pip install -r requirements.txt
```

### 3. **Configuration**

Create a `.env` file in the root directory:

```env
TELEGRAM_TOKEN="your_bot_token_here"
ADMIN_CHAT_IDS="123456789,987654321"  # Comma-separated admin user IDs
MONGO_URL="mongodb://localhost:27017/domain_checker"
```

### 4. **Run Tests**

```bash
python test_bot.py
```

### 5. **Start the Bot**

```bash
python main.py
```

## 📋 Commands

### **Basic Commands**
- `/start` - Authenticate and show welcome menu
- `/help` - Interactive help menu with categories
- `/logout` - Logout from the bot

### **Domain Management**
- `/add <domain>` - Add domain to monitoring
- `/remove <domain>` - Remove domain from monitoring
- `/list` - Show all monitored domains (paginated)
- `/checkall` or `/check` - Check all domains immediately

### **Interactive Features**
- **🔄 Refresh** - Quick domain status refresh
- **🗑️ Delete** - Remove domain with confirmation
- **🔍 Check** - Individual domain checking
- **📄 Pagination** - Navigate through large domain lists

## 🔧 Technical Details

### **Dependencies**
- `python-telegram-bot[job-queue]==20.0` - Telegram Bot API
- `pymongo==4.7.2` - MongoDB driver
- `python-dotenv==1.0.1` - Environment variable management
- `requests==2.31.0` - HTTP requests (sync)
- `aiohttp==3.9.3` - Async HTTP requests
- `apscheduler==3.10.4` - Background job scheduling

### **Database Schema**
```javascript
{
  domain: "example.com",
  added_at: ISODate("2024-01-01T00:00:00Z"),
  last_status: "up|down|unknown",
  last_checked: ISODate("2024-01-01T00:05:00Z"),
  last_response_time: 0.234,
  last_status_code: 200,
  last_error: null
}
```

### **Performance Features**
- **Concurrent Checking**: Multiple domains checked simultaneously
- **Connection Pooling**: Efficient HTTP connection management
- **Timeout Handling**: 10-second connection timeout
- **Error Recovery**: Graceful handling of network issues

### **Monitoring Schedule**
- **Automatic Checks**: Every 5 minutes
- **Initial Check**: 30 seconds after startup
- **Manual Checks**: On-demand via commands

## 🛠️ Development

### **Project Structure**
- **Modular Design**: Clean separation of concerns
- **Service Layer**: Business logic separated from presentation
- **Handler Layer**: Telegram-specific UI logic
- **Configuration**: Centralized settings management

### **Key Classes**
- `DomainBot`: Main orchestrator class
- `DatabaseService`: MongoDB operations
- `DomainChecker`: Health checking logic
- `DomainHandlers`: Telegram command handlers

### **Testing**
Run the comprehensive test suite:
```bash
python test_bot.py
```

Tests cover:
- Database operations
- Domain checking (sync/async)
- Configuration loading
- Integration testing

## 🔒 Security

- **Private Access**: Only authorized admin users
- **Environment Variables**: Sensitive data in `.env`
- **Input Validation**: Domain format validation
- **Error Handling**: Graceful error recovery

## 📈 Scalability

- **Concurrent Processing**: Handles multiple domains efficiently
- **Database Indexing**: Optimized MongoDB queries
- **Memory Efficient**: Minimal resource usage
- **Graceful Shutdown**: Proper cleanup on exit

## 🐛 Troubleshooting

### **Common Issues**

1. **Bot not responding**
   - Check Telegram token validity
   - Verify admin chat IDs
   - Check network connectivity

2. **Database connection failed**
   - Verify MongoDB URL
   - Check database server status
   - Ensure proper credentials

3. **Domain checks failing**
   - Check internet connectivity
   - Verify domain format
   - Review timeout settings

### **Logs**
The bot provides detailed logging:
```bash
python main.py
# Check logs for detailed error information
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests: `python test_bot.py`
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- Built with [python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot)
- Uses [MongoDB](https://www.mongodb.com/) for data persistence
- Powered by [APScheduler](https://apscheduler.readthedocs.io/) for background jobs

---

**Made with ❤️ for reliable domain monitoring**