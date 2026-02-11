# 🚀 دليل الإعداد السريع - Quick Setup Guide

## التنصيب في 5 دقائق!

### 1️⃣ تثبيت المتطلبات الأساسية

```bash
# Ubuntu/Debian
sudo apt update
sudo apt install python3 python3-pip python3-venv ffmpeg git -y

# CentOS/RHEL
sudo yum install python3 python3-pip ffmpeg git -y
```

### 2️⃣ تحميل البوت

```bash
cd ~
git clone <repository-url> telegram_radio_bot
cd telegram_radio_bot
```

### 3️⃣ الحصول على المعلومات المطلوبة

#### A. API ID و API Hash
1. اذهب إلى: https://my.telegram.org
2. سجل دخول
3. انتقل لـ "API Development Tools"
4. احفظ API ID و API Hash

#### B. Bot Token
1. افتح [@BotFather](https://t.me/BotFather)
2. أرسل `/newbot`
3. اتبع التعليمات
4. احفظ البوت توكن

### 4️⃣ إعداد الملفات

```bash
# نسخ ملف الإعدادات
cp .env.example .env

# تعديل الملف
nano .env
# أو استخدم أي محرر نصوص
```

املأ المعلومات:
```env
API_ID=12345678
API_HASH=abc123def456
BOT_TOKEN=123456:ABC-DEF...
```

### 5️⃣ إنشاء Session String

```bash
# تفعيل البيئة الافتراضية
python3 -m venv venv
source venv/bin/activate

# تثبيت المتطلبات
pip install pyrogram TgCrypto

# إنشاء Session
python generate_session.py
```

أدخل:
- API ID
- API Hash  
- رقم الهاتف (مع رمز الدولة: +964...)
- رمز التحقق

انسخ Session String وضعه في `.env`:
```env
SESSION_STRING=النص_الطويل_هنا
```

### 6️⃣ تشغيل البوت

```bash
# طريقة 1: استخدام السكريبت الجاهز
./start.sh

# طريقة 2: يدوياً
source venv/bin/activate
pip install -r requirements.txt
python bot.py
```

### 7️⃣ استخدام البوت

1. ابحث عن البوت في تليجرام
2. أرسل `/start`
3. أضف البوت لمجموعتك كمشرف
4. أرسل `/activate`
5. أضف أغاني: `/add [رابط]`
6. شغل: `/play`

---

## ✅ قائمة التحقق السريعة

- [ ] Python 3.8+ مثبت
- [ ] FFmpeg مثبت
- [ ] API ID و API Hash من my.telegram.org
- [ ] Bot Token من @BotFather
- [ ] Session String تم إنشاؤه
- [ ] ملف .env تم إعداده
- [ ] البوت يعمل بدون أخطاء

---

## 🆘 مشاكل شائعة

### البوت لا يرد
```bash
# تحقق من التوكن في .env
# أعد تشغيل البوت
```

### خطأ في Session String
```bash
# أعد إنشاء Session
python generate_session.py
```

### خطأ FFmpeg
```bash
# أعد تثبيت FFmpeg
sudo apt install --reinstall ffmpeg
```

---

## 📞 الدعم

إذا واجهت مشاكل:
1. راجع ملف README.md الكامل
2. تحقق من السجلات: `tail -f bot.log`
3. تأكد من صحة جميع المعلومات في .env

---

**وقت الإعداد المتوقع:** 5-10 دقائق  
**الصعوبة:** سهل - متوسط  
**الدعم:** متوفر في README.md
