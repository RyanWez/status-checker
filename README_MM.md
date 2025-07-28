# Telegram Domain Status Checker Bot

Domain များရဲ့ အခြေအနေကို စောင့်ကြည့်ပြီး domain တစ်ခုခု down ဖြစ်သွားရင် အကြောင်းကြားပေးတဲ့ private Telegram bot တစ်ခုဖြစ်ပါတယ်။

## လုပ်ဆောင်နိုင်သော အရာများ

- **Private Authentication**: Admin user (ADMIN_CHAT_ID ဖြင့် သတ်မှတ်ထားသော) တစ်ယောက်ပဲ bot ကို အသုံးပြုနိုင်ပါတယ်
- **Domain Management**: Domain များကို ထည့်ခြင်း၊ ဖယ်ရှားခြင်း၊ စာရင်းကြည့်ခြင်း
- **အလိုအလျောက် စောင့်ကြည့်မှု**: 1 နာရီတိုင်း domain များကို စစ်ဆေးပါတယ်
- **ထူးခြားသော အကြောင်းကြားမှု**: Domain တစ်ခု "down" ဖြစ်သွားမှသာ အကြောင်းကြားပါတယ်
- **ရေရှည် သိမ်းဆည်းမှု**: MongoDB ကို အသုံးပြုပြီး domain data များကို သိမ်းဆည်းပါတယ်
- **လက်ဖြင့် စစ်ဆေးမှု**: Domain များအားလုံးကို ချက်ချင်း စစ်ဆေးနိုင်ပါတယ်

## Commands များ

- `/start` - အတည်ပြုပြီး အသုံးပြုနိုင်သော commands များကို ပြရန်
- `/add <domain>` - Domain တစ်ခုကို စောင့်ကြည့်မှုထဲ ထည့်ရန် (ဥပမာ: `/add google.com`)
- `/remove <domain>` - Domain တစ်ခုကို စောင့်ကြည့်မှုမှ ဖယ်ရှားရန်
- `/list` - စောင့်ကြည့်နေသော domain များအားလုံးကို status နှင့်အတူ ပြရန်
- `/checkall` သို့မဟုတ် `/check` - Domain များအားလုံးကို လက်ဖြင့် စစ်ဆေးရန်
- `/help` - အကူအညီ message ကို ပြရန်

## Setup လုပ်ပုံ

### 1. Dependencies များ Install လုပ်ရန်

```bash
python -m venv venv
```

```bash
.\venv\Scripts\Activate.ps1
```

```bash
pip install -r requirements.txt
```

### 2. Environment Variables များ သတ်မှတ်ရန်

`.env` file တစ်ခု ဖန်တီးပြီး အောက်ပါအတိုင်း ရေးပါ:

```env
TELEGRAM_TOKEN="သင့်ရဲ့_bot_token_ကို_ဒီမှာ_ထည့်ပါ"
ADMIN_CHAT_ID="သင့်ရဲ့_chat_id_ကို_ဒီမှာ_ထည့်ပါ"
MONGO_URL="သင့်ရဲ့_mongodb_connection_string"
```

### 3. သင့်ရဲ့ Chat ID ရယူရန်

1. [@userinfobot](https://t.me/userinfobot) နှင့် စကားပြောပါ
2. မည်သည့် message မဆို ပို့ပြီး သင့်ရဲ့ chat ID ကို ရယူပါ
3. ဤ ID ကို ADMIN_CHAT_ID အဖြစ် အသုံးပြုပါ

### 4. Telegram Bot ဖန်တီးရန်

1. [@BotFather](https://t.me/botfather) ကို message ပို့ပါ
2. `/newbot` ပို့ပြီး လမ်းညွှန်ချက်များကို လိုက်နာပါ
3. Bot token ကို TELEGRAM_TOKEN ထဲ ကူးထည့်ပါ

### 5. MongoDB Setup လုပ်ရန်

အောက်ပါတို့ကို အသုံးပြုနိုင်ပါတယ်:
- **Local MongoDB**: `mongodb://localhost:27017/domain_checker`
- **MongoDB Atlas**: သင့်ရဲ့ Atlas cluster မှ connection string ကို ရယူပါ

### 6. Bot ကို Run လုပ်ရန်

```bash
python domain_checker_bot.py
```

## Testing

အရာအားလုံး မှန်ကန်စွာ configure လုပ်ထားမှန်း စစ်ဆေးရန် test script ကို run လုပ်ပါ:

```bash
python test_bot.py
```

## လုပ်ဆောင်ပုံ

1. **Authentication**: Configure လုပ်ထားသော admin user တစ်ယောက်ပဲ bot ကို အသုံးပြုနိုင်ပါတယ်
2. **Domain Storage**: Domain များကို metadata နှင့်အတူ MongoDB ထဲ သိမ်းဆည်းပါတယ်
3. **Health Checks**: Domain များရဲ့ accessibility ကို HTTP requests များဖြင့် စစ်ဆေးပါတယ်
4. **Scheduled Monitoring**: APScheduler က ၅ မိနစ်တိုင်း စစ်ဆေးပါတယ်
5. **Smart Alerts**: Status က "down" ဖြစ်သွားမှသာ အကြောင်းကြားပါတယ်

## Domain Check Logic

- Protocol မရှိရင် `https://` prefix ကို အလိုအလျောက် ထည့်ပါတယ်
- HTTP 200 status ကို "up" အဖြစ် သတ်မှတ်ပါတယ်
- Response time နှင့် error details များကို မှတ်တမ်းတင်ပါတယ်
- နောက်ဆုံး စစ်ဆေးချိန် နှင့် status ကို သိမ်းဆည်းပါတယ်

## Deployment

Bot ကို အောက်ပါ platform များမှာ deploy လုပ်နိုင်ပါတယ်:
- Fly.io
- Heroku
- Railway
- VPS servers

သင့်ရဲ့ deployment platform မှာ environment variables များကို သတ်မှတ်ရန် မမေ့ပါနှင့်။

## Logs

Bot က အောက်ပါ အသေးစိတ် logging များ ပေးပါတယ်:
- MongoDB connection status
- Domain check results
- Scheduler activity
- Error messages

## လုံခြုံရေး

- Sensitive data အားလုံးကို environment variables များမှ load လုပ်ပါတယ်
- Configure လုပ်ထားသော admin တစ်ယောက်ပဲ bot ကို အသုံးပြုနိုင်ပါတယ်
- MongoDB credentials များကို လုံခြုံစွာ ထားရှိပါတယ်
- Sensitive information များကို log မှာ မပါဝင်ပါ

## ပြဿနာ ဖြေရှင်းပုံ

1. **Bot မတုံ့ပြန်ရင်**: TELEGRAM_TOKEN နှင့် bot permissions များကို စစ်ဆေးပါ
2. **Authentication မအောင်မြင်ရင်**: ADMIN_CHAT_ID က သင့်ရဲ့ Telegram chat ID နှင့် ကိုက်ညီမှန်း စစ်ဆေးပါ
3. **Database errors ရရင်**: MONGO_URL နှင့် MongoDB connectivity ကို စစ်ဆေးပါ
4. **Domain checks မအောင်မြင်ရင်**: Internet connectivity နှင့် domain accessibility ကို စစ်ဆေးပါ

Configuration ပြဿနာများကို ရှာဖွေရန် `python test_bot.py` ကို run လုပ်ပါ။