#!/bin/bash

# ════════════════════════════════════════════════════════════
#           سكريبت تشغيل بوت الراديو - Start Script
# ════════════════════════════════════════════════════════════

echo "════════════════════════════════════════════════════════"
echo "         🎵 بوت راديو تليجرام - Radio Bot 🎵"
echo "════════════════════════════════════════════════════════"
echo ""

# التحقق من Python
if ! command -v python3 &> /dev/null; then
    echo "❌ خطأ: Python 3 غير مثبت!"
    echo "الرجاء تثبيت Python 3.8 أو أحدث"
    exit 1
fi

echo "✅ Python موجود: $(python3 --version)"

# التحقق من FFmpeg
if ! command -v ffmpeg &> /dev/null; then
    echo "⚠️ تحذير: FFmpeg غير مثبت!"
    echo "لتثبيته:"
    echo "  Ubuntu/Debian: sudo apt install ffmpeg"
    echo "  CentOS/RHEL: sudo yum install ffmpeg"
    echo ""
fi

# التحقق من البيئة الافتراضية
if [ ! -d "venv" ]; then
    echo "📦 إنشاء البيئة الافتراضية..."
    python3 -m venv venv
    echo "✅ تم إنشاء البيئة الافتراضية"
fi

# تفعيل البيئة الافتراضية
echo "🔄 تفعيل البيئة الافتراضية..."
source venv/bin/activate

# تحديث pip
echo "🔄 تحديث pip..."
pip install --upgrade pip > /dev/null 2>&1

# تثبيت المتطلبات
if [ ! -f ".requirements_installed" ]; then
    echo "📥 تثبيت المتطلبات..."
    pip install -r requirements.txt
    
    if [ $? -eq 0 ]; then
        touch .requirements_installed
        echo "✅ تم تثبيت المتطلبات بنجاح"
    else
        echo "❌ فشل تثبيت المتطلبات"
        exit 1
    fi
else
    echo "✅ المتطلبات مثبتة مسبقاً"
fi

# التحقق من ملف الإعدادات
if [ ! -f "config.py" ]; then
    echo ""
    echo "❌ خطأ: ملف config.py غير موجود!"
    echo ""
    echo "الرجاء:"
    echo "1. نسخ ملف .env.example إلى .env"
    echo "2. تعديل الإعدادات في .env"
    echo "3. تشغيل: python generate_session.py"
    echo ""
    exit 1
fi

# إنشاء مجلد التحميلات
mkdir -p downloads

# إنشاء مجلد السجلات
mkdir -p logs

echo ""
echo "════════════════════════════════════════════════════════"
echo "              🚀 بدء تشغيل البوت..."
echo "════════════════════════════════════════════════════════"
echo ""

# تشغيل البوت
python3 bot.py

# عند الخروج
deactivate
