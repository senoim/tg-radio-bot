#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
مولد Session String للحساب المساعد
Session String Generator for UserBot
"""

from pyrogram import Client

print("=" * 60)
print("      مولد Session String - الحساب المساعد")
print("=" * 60)
print()

# طلب المعلومات من المستخدم
API_ID = input("أدخل API ID: ")
API_HASH = input("أدخل API Hash: ")

print()
print("سيتم طلب رمز التحقق على تليجرام...")
print()

# إنشاء Session String
with Client(
    name="radio_userbot",
    api_id=int(API_ID),
    api_hash=API_HASH,
    in_memory=True
) as app:
    session_string = app.export_session_string()
    
    print()
    print("=" * 60)
    print("✅ تم إنشاء Session String بنجاح!")
    print("=" * 60)
    print()
    print("انسخ هذا النص وضعه في ملف config.py:")
    print()
    print(f'SESSION_STRING = "{session_string}"')
    print()
    print("=" * 60)
    print("⚠️ تحذير: احتفظ بهذا النص سرياً ولا تشاركه مع أحد!")
    print("=" * 60)
