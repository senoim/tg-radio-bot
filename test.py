#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
سكريبت اختبار بسيط - Simple Test Script
"""

print("=" * 60)
print("           🧪 اختبار مكونات البوت")
print("=" * 60)
print()

# اختبار استيراد المكتبات
print("📦 اختبار المكتبات...")

try:
    import pyrogram
    print("✅ Pyrogram")
except ImportError as e:
    print(f"❌ Pyrogram: {e}")

try:
    import yt_dlp
    print("✅ yt-dlp")
except ImportError as e:
    print(f"❌ yt-dlp: {e}")

try:
    import sqlite3
    print("✅ SQLite3")
except ImportError as e:
    print(f"❌ SQLite3: {e}")

print()
print("📄 اختبار الملفات...")

import os

files_to_check = [
    "bot.py",
    "config.py",
    "database.py",
    "radio_manager.py",
    "generate_session.py",
    "requirements.txt",
    "README.md"
]

for file in files_to_check:
    if os.path.exists(file):
        print(f"✅ {file}")
    else:
        print(f"❌ {file}")

print()
print("🗄️ اختبار قاعدة البيانات...")

try:
    from database import Database
    db = Database("test.db")
    print("✅ إنشاء قاعدة البيانات")
    
    # اختبار إضافة مجموعة
    db.add_chat(-100123456789, "مجموعة تجريبية")
    print("✅ إضافة مجموعة")
    
    # اختبار إضافة أغنية
    song_id = db.add_song(
        chat_id=-100123456789,
        title="أغنية تجريبية",
        duration=180,
        artist="فنان تجريبي",
        source_type="test"
    )
    print(f"✅ إضافة أغنية (ID: {song_id})")
    
    # اختبار قائمة التشغيل
    playlist = db.get_playlist(-100123456789)
    print(f"✅ قائمة التشغيل ({len(playlist)} أغنية)")
    
    # حذف قاعدة البيانات التجريبية
    os.remove("test.db")
    print("✅ تنظيف البيانات التجريبية")
    
except Exception as e:
    print(f"❌ خطأ في قاعدة البيانات: {e}")

print()
print("=" * 60)
print("           ✅ انتهى الاختبار")
print("=" * 60)
print()
print("💡 إذا ظهرت علامات ✅ لكل شيء، البوت جاهز للعمل!")
print("📖 اقرأ README.md للبدء")
print()
