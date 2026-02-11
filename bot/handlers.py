from pyrogram import filters
from pyrogram.types import Message
from sqlalchemy import select

from .config import DEVS, AUTO_START, DEFAULT_LOOP
from .db import Song, set_loop
from .radio import start_radio, stop_radio

def is_dev(user_id: int) -> bool:
    return user_id in DEVS

def setup_handlers(bot, calls, SessionLocal):

    async def dev_guard(m: Message) -> bool:
        return bool(m.from_user and is_dev(m.from_user.id))

    # ===== معلومات =====
    @bot.on_message(filters.command("start"))
    async def start_cmd(_, m: Message):
        await m.reply(
            "🎧 بوت راديو (Playlist عامة)\n\n"
            "✅ إرسال أغنية بالخاص للبوت = تنحفظ تلقائياً\n"
            "الأوامر:\n"
            "/on تشغيل\n"
            "/off إيقاف\n"
            "/list قائمة\n"
            "/loop on|off تكرار\n"
            "/stats إحصائيات\n"
        )

    # ===== Auto Save (Private) =====
    @bot.on_message((filters.audio | filters.voice) & filters.private)
    async def auto_add_private(_, m: Message):
        if not m.from_user or not is_dev(m.from_user.id):
            return

        media = m.audio or m.voice
        title = getattr(media, "title", None) or getattr(media, "file_name", None) or "Song"
        file_id = media.file_id

        async with SessionLocal() as db:
            exists = (await db.execute(select(Song).where(Song.file_id == file_id))).scalar_one_or_none()
            if exists:
                return await m.reply("ℹ️ الأغنية موجودة أصلاً بالقائمة العامة.")
            db.add(Song(title=title[:256], file_id=file_id))
            await db.commit()

        await m.reply("✅ تم حفظ الأغنية تلقائياً بالقائمة العامة.")

    # ===== تشغيل/إيقاف =====
    @bot.on_message(filters.command("on"))
    async def on_cmd(_, m: Message):
        if not await dev_guard(m):
            return
        async with SessionLocal() as db:
            txt = await start_radio(m.chat.id, bot, calls, db, DEFAULT_LOOP)
        await m.reply(txt)

    @bot.on_message(filters.command("off"))
    async def off_cmd(_, m: Message):
        if not await dev_guard(m):
            return
        txt = await stop_radio(m.chat.id, calls)
        await m.reply(txt)

    # ===== قائمة =====
    @bot.on_message(filters.command("list"))
    async def list_cmd(_, m: Message):
        async with SessionLocal() as db:
            res = await db.execute(select(Song).order_by(Song.id.asc()))
            songs = list(res.scalars().all())
        if not songs:
            return await m.reply("ماكو أغاني بعد. ارسل ملفات صوت بالخاص حتى تنحفظ تلقائياً.")
        text = "\n".join([f"{s.id}) {s.title}" for s in songs[:80]])
        await m.reply(f"🎼 قائمة الأغاني (أول 80):\n{text}")

    # ===== Loop =====
    @bot.on_message(filters.command("loop"))
    async def loop_cmd(_, m: Message):
        if not await dev_guard(m):
            return
        if len(m.command) < 2 or m.command[1] not in ("on", "off"):
            return await m.reply("اكتب: /loop on أو /loop off")
        val = m.command[1] == "on"
        async with SessionLocal() as db:
            await set_loop(db, m.chat.id, val)
        await m.reply(f"🔁 loop = {'ON' if val else 'OFF'}")

    # ===== Stats =====
    @bot.on_message(filters.command("stats"))
    async def stats_cmd(_, m: Message):
        async with SessionLocal() as db:
            res = await db.execute(select(Song))
            count = len(list(res.scalars().all()))
        await m.reply(f"📊 عدد الأغاني بالقائمة العامة: {count}")

    # ===== Auto-start عند إضافة البوت (اختياري) =====
    @bot.on_my_chat_member()
    async def on_added(_, update):
        if not AUTO_START:
            return
        try:
            chat = update.chat
            # مجرد محاولة تشغيل
            async with SessionLocal() as db:
                await start_radio(chat.id, bot, calls, db, DEFAULT_LOOP)
        except Exception:
            pass
