# 🚀 Fly.io မှာ Telegram Bot Deploy လုပ်နည်း

## 📋 လိုအပ်တဲ့ အရာများ

### 1. Fly.io CLI Install လုပ်ပါ
```bash
# Windows PowerShell မှာ
iwr https://fly.io/install.ps1 -useb | iex

# သို့မဟုတ် https://fly.io/docs/hands-on/install-flyctl/ ကနေ download လုပ်ပါ
```

### 2. Fly.io Account ဖွင့်ပြီး Login လုပ်ပါ
```bash
flyctl auth login
```

## 🎯 Deploy လုပ်နည်း (အဆင့်ဆင့်)

### အဆင့် ၁: Application ပြင်ဆင်ခြင်း
```bash
# File တွေ အားလုံး ရှိမရှိ စစ်ပါ
dir
# Dockerfile, fly.toml, requirements.txt, main.py စတာတွေ ရှိရမယ်
```

### အဆင့် ၂: Fly.io App ဖန်တီးခြင်း
```bash
# App အသစ် ဖန်တီးပါ
flyctl apps create telegram-domain-checker --org personal
```

### အဆင့် ၃: Environment Variables သတ်မှတ်ခြင်း
```bash
# သင့်ရဲ့ Bot Token နဲ့ အခြား settings တွေ သတ်မှတ်ပါ
flyctl secrets set TELEGRAM_TOKEN="သင့်ရဲ့_bot_token"
flyctl secrets set ADMIN_CHAT_IDS="သင့်ရဲ့_chat_ids"
flyctl secrets set MONGO_URL="သင့်ရဲ့_mongodb_url"
```

### အဆင့် ၄: Deploy လုပ်ခြင်း
```bash
# Windows မှာ
deploy.bat

# သို့မဟုတ် manual
flyctl deploy --ha=false
```

### အဆင့် ၅: စစ်ဆေးခြင်း
```bash
# App status စစ်ပါ
flyctl status

# Health check
curl https://telegram-domain-checker.fly.dev/health

# Logs ကြည့်ပါ
flyctl logs --follow
```

## ⚡ Performance Optimizations

### 1. Docker Optimizations
- ✅ Python 3.11 slim image သုံးထားတယ်
- ✅ Multi-stage build နဲ့ image size လျှော့ထားတယ်
- ✅ Layer caching optimize လုပ်ထားတယ်
- ✅ Security အတွက် non-root user သုံးထားတယ်

### 2. Application Performance
- ✅ **Async HTTP**: Domain checking အတွက် concurrent processing
- ✅ **Connection Pooling**: TCP connection optimize လုပ်ထားတယ်
- ✅ **Batch Processing**: Domain တွေကို batch လုပ်ပြီး process လုပ်တယ်
- ✅ **DNS Caching**: 5 မိနစ် DNS cache လုပ်ထားတယ်
- ✅ **Timeout Optimization**: Response time မြန်အောင် လုပ်ထားတယ်

### 3. Database Performance
- ✅ **Bulk Operations**: Database update တွေကို bulk လုပ်တယ်
- ✅ **Connection Pooling**: MongoDB connection optimize လုပ်ထားတယ်
- ✅ **Indexed Queries**: Database query တွေ မြန်အောင် လုပ်ထားတယ်

## 📊 Monitoring

### Health Check
```bash
# Bot ကောင်းမကောင်း စစ်ပါ
curl https://telegram-domain-checker.fly.dev/health

# Metrics ကြည့်ပါ
curl https://telegram-domain-checker.fly.dev/metrics

# Real-time logs
flyctl logs --follow
```

### Performance Monitoring
```bash
# Resource usage ကြည့်ပါ
flyctl metrics

# App status
flyctl status
```

## 💰 Free Tier အတွက် Optimization

### Free Tier Limits
- **Compute**: 160 hours/month
- **Memory**: 512MB သုံးထားတယ်
- **Storage**: 3GB
- **Bandwidth**: 160GB/month

### Cost သက်သာအောင် လုပ်နည်း
1. Single instance သုံးပါ (`--ha=false`)
2. Auto-stop configure လုပ်ပါ
3. Resource usage monitor လုပ်ပါ

## 🔧 Troubleshooting

### အဖြစ်များတဲ့ ပြဿနာများ

1. **Bot မတုံ့ပြန်ရင်**
   ```bash
   flyctl logs
   flyctl secrets list
   curl https://telegram-domain-checker.fly.dev/health
   ```

2. **Database connection ပြဿနာ**
   ```bash
   flyctl secrets list
   # MongoDB URL မှန်မမှန် စစ်ပါ
   ```

3. **Memory ပြဿနာ**
   ```bash
   flyctl status
   flyctl scale memory 1024  # လိုအပ်ရင်
   ```

## 🎉 အောင်မြင်ပါပြီ!

သင့်ရဲ့ Telegram Domain Checker Bot ဟာ Fly.io မှာ အောင်မြင်စွာ run နေပါပြီ:

- ✅ High performance domain checking
- ✅ Automatic health monitoring
- ✅ Optimized resource usage
- ✅ Production-ready configuration
- ✅ Free tier compatible

**Bot URL**: https://telegram-domain-checker.fly.dev
**Health Check**: https://telegram-domain-checker.fly.dev/health

## 📱 Bot Commands

### အခြေခံ Commands
- `/start` - Bot ကို စတင်ပါ
- `/help` - အကူအညီ menu
- `/list` - Domain list ကြည့်ပါ
- `/checkall` - Domain အားလုံး check လုပ်ပါ
- `/userinfo` - သင့် account info ကြည့်ပါ

### Admin Commands (Admin များအတွက်သာ)
- `/add domain.com` - Domain ထည့်ပါ
- `/remove domain.com` - Domain ဖယ်ပါ
- `/adduser <user_id> <username> [role]` - User ထည့်ပါ (ID နဲ့)
- `/adduser @username [role]` - User ထည့်ပါ (Username နဲ့)
- `/finduser @username` - Username ကနေ User ID ရှာပါ
- `/removeuser <user_id>` - User ဖယ်ပါ
- `/listusers` - User list ကြည့်ပါ (text format)
- `/userlists` - Interactive user management (အသစ်!)

### 📱 Interactive User Management
- **Button Interface**: `/userlists` နဲ့ user တွေကို button တွေနဲ့ manage လုပ်လို့ရတယ်
- **User Details**: User တစ်ယောက်ကို နှိပ်လိုက်ရင် အသေးစိတ် info ပြတယ်
- **Role Changes**: User role တွေကို button နဲ့ ပြောင်းလို့ရတယ်
- **Safe Removal**: User ဖယ်တဲ့အခါ confirmation dialog ပြတယ်
- **Pagination**: User အများကြီး ရှိရင် page လုပ်ပြီး ကြည့်လို့ရတယ်

### 🔔 Notification System
- **Domain Down Alerts**: Domain တွေ down ဖြစ်ရင် automatic notification ပို့ပေးတယ်
- **All Users**: Bot သုံးတဲ့သူ အားလုံးကို notification ပို့ပေးတယ် (admin + user + guest)
- **Smart Alerts**: Status ပြောင်းတဲ့အခါပဲ ပို့တယ်၊ spam မဖြစ်ဘူး
- **Detailed Info**: Domain name, error message, timestamp အပြည့်အစုံ ပါတယ်

### 👥 User Roles (အသုံးပြုသူ အမျိုးအစားများ)

#### 👑 Admin
- Domain add/remove လုပ်နိုင်တယ်
- User management လုပ်နိုင်တယ်
- Bulk operations လုပ်နိုင်တယ်
- Group အားလုံး access လုပ်နိုင်တယ်

#### 👤 User  
- Domain တွေကို ကြည့်နိုင်တယ်
- Check လုပ်နိုင်တယ်
- Group အားလုံး access လုပ်နိုင်တယ်
- Domain add/remove လုပ်လို့ မရဘူး
- Delete button တွေ မမြင်ရဘူး

#### 👥 Guest
- သတ်မှတ်ထားတဲ့ group တွေကိုပဲ ကြည့်နိုင်တယ်
- Check လုပ်နိုင်တယ်
- ဘာမှ modify လုပ်လို့ မရဘူး
- Delete button တွေ မမြင်ရဘူး

### Performance Features
- **150+ domains** ကို concurrent check လုပ်နိုင်တယ်
- **5 မိနစ်တိုင်း** automatic check လုပ်တယ်
- **Real-time notifications** domain down ရင် alert ပေးတယ်
- **Group management** domain တွေကို group လုပ်ပြီး organize လုပ်နိုင်တယ်

Happy monitoring! 🚀