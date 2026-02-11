#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
بوت راديو تليجرام - الملف الرئيسي
Telegram Radio Bot - Main File
"""

import logging
from pyrogram import Client, filters
from pyrogram.types import Message
from config import *
from database import Database
from radio_manager import RadioManager
import asyncio

# إعداد السجلات
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# إنشاء البوت
app = Client(
    "radio_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

# إنشاء الحساب المساعد (UserBot)
userbot = Client(
    "radio_userbot",
    api_id=API_ID,
    api_hash=API_HASH,
    session_string=SESSION_STRING
)

# قاعدة البيانات ومدير الراديو
db = Database()
radio = RadioManager(userbot, db)


# ══════════════════════════════════════════════════════════════
#                         أوامر البوت
# ══════════════════════════════════════════════════════════════

@app.on_message(filters.command("start") & filters.private)
async def start_command(client: Client, message: Message):
    """أمر البدء"""
    welcome_text = """
🎵 **مرحباً بك في بوت الراديو!**

**الأوامر المتاحة:**

📻 **التشغيل:**
• `/play` - تشغيل الراديو
• `/pause` - إيقاف مؤقت
• `/resume` - استئناف التشغيل
• `/skip` - تخطي الأغنية الحالية
• `/stop` - إيقاف الراديو

🎵 **إدارة الأغاني:**
• `/add` - إضافة أغنية (رد على ملف أو أرسل رابط)
• `/playlist` - عرض قائمة التشغيل
• `/remove` - حذف أغنية
• `/shuffle` - خلط قائمة التشغيل

⚙️ **الإعدادات:**
• `/settings` - إعدادات الراديو
• `/status` - حالة التشغيل الحالية
• `/autoplay` - تفعيل/تعطيل التشغيل التلقائي

👥 **للإضافة في مجموعة:**
1. أضفني كمشرف في المجموعة/القناة
2. أرسل `/activate` لتفعيل الراديو
3. سيبدأ التشغيل تلقائياً!

━━━━━━━━━━━━━━━━━━━━
💡 **ملاحظة:** البوت يعمل تلقائياً ويعيد التشغيل عند انتهاء القائمة
    """
    await message.reply_text(welcome_text)


@app.on_message(filters.command("activate"))
async def activate_radio(client: Client, message: Message):
    """تفعيل الراديو في المجموعة/القناة"""
    if message.chat.type == "private":
        await message.reply_text("⚠️ هذا الأمر للمجموعات والقنوات فقط!")
        return
    
    # التحقق من الصلاحيات
    member = await message.chat.get_member(message.from_user.id)
    if member.status not in ["creator", "administrator"]:
        await message.reply_text("⚠️ هذا الأمر للمشرفين فقط!")
        return
    
    # تفعيل الراديو
    chat_id = message.chat.id
    db.add_chat(chat_id, message.chat.title)
    
    await message.reply_text(
        f"✅ **تم تفعيل الراديو!**\n\n"
        f"📻 المجموعة: {message.chat.title}\n"
        f"🆔 المعرف: `{chat_id}`\n\n"
        f"يمكنك الآن إضافة الأغاني والبدء بالتشغيل!"
    )


@app.on_message(filters.command("play"))
async def play_command(client: Client, message: Message):
    """تشغيل الراديو"""
    chat_id = message.chat.id
    
    # التحقق من تفعيل المجموعة
    if not db.is_chat_active(chat_id):
        await message.reply_text("⚠️ الرجاء تفعيل الراديو أولاً بإرسال `/activate`")
        return
    
    # بدء التشغيل
    status_msg = await message.reply_text("⏳ جاري بدء التشغيل...")
    
    result = await radio.start_playing(chat_id)
    
    if result["success"]:
        await status_msg.edit_text(
            f"▶️ **بدأ التشغيل!**\n\n"
            f"🎵 الأغنية: {result['current_song']}\n"
            f"📋 عدد الأغاني: {result['total_songs']}"
        )
    else:
        await status_msg.edit_text(f"❌ {result['message']}")


@app.on_message(filters.command("pause"))
async def pause_command(client: Client, message: Message):
    """إيقاف مؤقت"""
    chat_id = message.chat.id
    result = await radio.pause(chat_id)
    await message.reply_text(f"⏸️ {result['message']}")


@app.on_message(filters.command("resume"))
async def resume_command(client: Client, message: Message):
    """استئناف التشغيل"""
    chat_id = message.chat.id
    result = await radio.resume(chat_id)
    await message.reply_text(f"▶️ {result['message']}")


@app.on_message(filters.command("skip"))
async def skip_command(client: Client, message: Message):
    """تخطي الأغنية"""
    chat_id = message.chat.id
    result = await radio.skip(chat_id)
    
    if result["success"]:
        await message.reply_text(
            f"⏭️ **تم التخطي!**\n\n"
            f"🎵 الأغنية التالية: {result['next_song']}"
        )
    else:
        await message.reply_text(f"❌ {result['message']}")


@app.on_message(filters.command("stop"))
async def stop_command(client: Client, message: Message):
    """إيقاف الراديو"""
    chat_id = message.chat.id
    result = await radio.stop(chat_id)
    await message.reply_text(f"⏹️ {result['message']}")


@app.on_message(filters.command("add"))
async def add_song_command(client: Client, message: Message):
    """إضافة أغنية"""
    chat_id = message.chat.id
    
    # التحقق من الصلاحيات
    if message.chat.type != "private":
        member = await message.chat.get_member(message.from_user.id)
        if member.status not in ["creator", "administrator"]:
            await message.reply_text("⚠️ هذا الأمر للمشرفين فقط!")
            return
    
    # إضافة من رابط
    if len(message.command) > 1:
        url = message.command[1]
        status_msg = await message.reply_text("⏳ جاري تحميل الأغنية...")
        
        result = await radio.add_song_from_url(chat_id, url)
        
        if result["success"]:
            await status_msg.edit_text(
                f"✅ **تمت الإضافة!**\n\n"
                f"🎵 {result['title']}\n"
                f"⏱️ المدة: {result['duration']}"
            )
        else:
            await status_msg.edit_text(f"❌ {result['message']}")
    
    # إضافة من ملف
    elif message.reply_to_message and message.reply_to_message.audio:
        audio = message.reply_to_message.audio
        status_msg = await message.reply_text("⏳ جاري حفظ الأغنية...")
        
        result = await radio.add_song_from_file(chat_id, audio)
        
        if result["success"]:
            await status_msg.edit_text(
                f"✅ **تمت الإضافة!**\n\n"
                f"🎵 {result['title']}\n"
                f"⏱️ المدة: {result['duration']}"
            )
        else:
            await status_msg.edit_text(f"❌ {result['message']}")
    
    else:
        await message.reply_text(
            "📝 **طريقة الاستخدام:**\n\n"
            "1️⃣ `/add [رابط]` - إضافة من يوتيوب/ساوند كلاود\n"
            "2️⃣ رد على ملف صوتي بـ `/add` - إضافة ملف مباشر"
        )


@app.on_message(filters.command("playlist"))
async def playlist_command(client: Client, message: Message):
    """عرض قائمة التشغيل"""
    chat_id = message.chat.id
    songs = db.get_playlist(chat_id)
    
    if not songs:
        await message.reply_text("📋 قائمة التشغيل فارغة!\n\nأضف أغاني باستخدام `/add`")
        return
    
    playlist_text = "📋 **قائمة التشغيل:**\n\n"
    
    for i, song in enumerate(songs, 1):
        status = "▶️" if song['is_playing'] else ""
        playlist_text += f"{i}. {status} {song['title']} - `{song['duration']}`\n"
    
    playlist_text += f"\n📊 الإجمالي: {len(songs)} أغنية"
    
    await message.reply_text(playlist_text)


@app.on_message(filters.command("status"))
async def status_command(client: Client, message: Message):
    """حالة الراديو"""
    chat_id = message.chat.id
    status = await radio.get_status(chat_id)
    
    if status["is_playing"]:
        status_text = (
            f"▶️ **قيد التشغيل**\n\n"
            f"🎵 الأغنية: {status['current_song']}\n"
            f"⏱️ الوقت: {status['elapsed']} / {status['duration']}\n"
            f"📋 في القائمة: {status['queue_size']} أغنية\n"
            f"🔄 التكرار: {'مفعل' if status['autoplay'] else 'معطل'}"
        )
    else:
        status_text = "⏹️ **الراديو متوقف حالياً**"
    
    await message.reply_text(status_text)


@app.on_message(filters.command("autoplay"))
async def autoplay_command(client: Client, message: Message):
    """تفعيل/تعطيل التشغيل التلقائي"""
    chat_id = message.chat.id
    
    # التبديل بين التفعيل والتعطيل
    current_status = db.get_autoplay_status(chat_id)
    new_status = not current_status
    db.set_autoplay(chat_id, new_status)
    
    status_emoji = "✅" if new_status else "❌"
    status_text = "مفعل" if new_status else "معطل"
    
    await message.reply_text(
        f"{status_emoji} **التشغيل التلقائي {status_text}**\n\n"
        f"{'🔄 سيتم إعادة التشغيل تلقائياً عند انتهاء القائمة' if new_status else '⏹️ سيتوقف عند انتهاء القائمة'}"
    )


@app.on_message(filters.command("shuffle"))
async def shuffle_command(client: Client, message: Message):
    """خلط قائمة التشغيل"""
    chat_id = message.chat.id
    result = db.shuffle_playlist(chat_id)
    
    if result:
        await message.reply_text("🔀 **تم خلط قائمة التشغيل!**")
    else:
        await message.reply_text("❌ لا توجد أغاني لخلطها")


@app.on_message(filters.command("remove"))
async def remove_command(client: Client, message: Message):
    """حذف أغنية"""
    if len(message.command) < 2:
        await message.reply_text("📝 **الاستخدام:** `/remove [رقم الأغنية]`")
        return
    
    try:
        song_index = int(message.command[1]) - 1
        chat_id = message.chat.id
        
        result = db.remove_song(chat_id, song_index)
        
        if result:
            await message.reply_text("✅ **تم حذف الأغنية!**")
        else:
            await message.reply_text("❌ رقم أغنية غير صحيح")
    except ValueError:
        await message.reply_text("❌ الرجاء إدخال رقم صحيح")


# ══════════════════════════════════════════════════════════════
#                    معالج انضمام البوت للمجموعات
# ══════════════════════════════════════════════════════════════

@app.on_message(filters.new_chat_members)
async def bot_added_to_group(client: Client, message: Message):
    """عند إضافة البوت لمجموعة"""
    for member in message.new_chat_members:
        if member.id == (await client.get_me()).id:
            # البوت تمت إضافته
            welcome = (
                f"👋 **شكراً لإضافتي!**\n\n"
                f"📻 أنا بوت راديو تليجرام\n"
                f"🎵 سأقوم بتشغيل الأغاني تلقائياً\n\n"
                f"🚀 للبدء:\n"
                f"1. اجعلني مشرف\n"
                f"2. أرسل `/activate` لتفعيل الراديو\n"
                f"3. أضف أغاني بـ `/add`\n"
                f"4. ابدأ التشغيل بـ `/play`\n\n"
                f"📖 استخدم `/start` لعرض كل الأوامر"
            )
            await message.reply_text(welcome)


# ══════════════════════════════════════════════════════════════
#                         تشغيل البوت
# ══════════════════════════════════════════════════════════════

async def main():
    """تشغيل البوت والحساب المساعد"""
    logger.info("🚀 جاري بدء تشغيل البوت...")
    
    # بدء الحساب المساعد
    await userbot.start()
    logger.info("✅ الحساب المساعد جاهز")
    
    # بدء البوت
    await app.start()
    logger.info("✅ البوت جاهز")
    
    # بدء مدير الراديو
    asyncio.create_task(radio.auto_player_loop())
    logger.info("✅ نظام التشغيل التلقائي جاهز")
    
    logger.info("🎵 الراديو يعمل الآن!")
    
    # إبقاء البوت قيد التشغيل
    await asyncio.Event().wait()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("⏹️ تم إيقاف البوت")
