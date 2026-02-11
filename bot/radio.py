import os, asyncio
from typing import Dict, List, Optional

from pyrogram import Client
from pytgcalls import PyTgCalls
from pytgcalls.types.input_stream import AudioPiped
from pytgcalls import idle
from pytgcalls.types import Update
from pytgcalls.types.stream import StreamAudioEnded

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .db import Song, get_loop

CACHE_DIR = "cache"
os.makedirs(CACHE_DIR, exist_ok=True)

class RadioState:
    def __init__(self):
        self.active: Dict[int, bool] = {}
        self.index: Dict[int, int] = {}
        self.lock = asyncio.Lock()

state = RadioState()

async def _download_song(bot: Client, file_id: str, song_id: int) -> str:
    path = os.path.join(CACHE_DIR, f"{song_id}.mp3")
    if os.path.exists(path) and os.path.getsize(path) > 0:
        return path
    await bot.download_media(file_id, file_name=path)
    return path

async def _get_playlist(db: AsyncSession) -> List[Song]:
    res = await db.execute(select(Song).order_by(Song.id.asc()))
    return list(res.scalars().all())

async def _play_current(chat_id: int, bot: Client, calls: PyTgCalls, db: AsyncSession):
    playlist = await _get_playlist(db)
    if not playlist:
        raise RuntimeError("EMPTY_PLAYLIST")

    i = state.index.get(chat_id, 0)
    if i >= len(playlist):
        state.index[chat_id] = 0
        i = 0

    song = playlist[i]
    path = await _download_song(bot, song.file_id, song.id)
    # بدل join كل مرة، نستخدم change_stream إذا كان موجود، لكن لضمان التوافق:
    try:
        await calls.change_stream(chat_id, AudioPiped(path))
    except Exception:
        await calls.join_group_call(chat_id, AudioPiped(path))

async def start_radio(chat_id: int, bot: Client, calls: PyTgCalls, db: AsyncSession, default_loop: bool) -> str:
    async with state.lock:
        if state.active.get(chat_id):
            return "✅ الراديو شغال أصلاً."
        playlist = await _get_playlist(db)
        if not playlist:
            return "❌ ماكو أغاني بالقائمة العامة. ارسل ملفات صوت للبوت حتى يحفظها تلقائياً."
        state.active[chat_id] = True
        state.index[chat_id] = 0

    try:
        await _play_current(chat_id, bot, calls, db)
        return "✅ تم تشغيل الراديو."
    except Exception as e:
        async with state.lock:
            state.active[chat_id] = False
        return f"❌ فشل التشغيل: {e}"

async def stop_radio(chat_id: int, calls: PyTgCalls) -> str:
    async with state.lock:
        state.active[chat_id] = False
        state.index.pop(chat_id, None)
    try:
        await calls.leave_group_call(chat_id)
    except Exception:
        pass
    return "⏹️ تم إيقاف الراديو."

def attach_events(calls: PyTgCalls, bot: Client, SessionLocal, default_loop: bool):
    @calls.on_stream_end()
    async def on_stream_end(_, update: Update):
        # هذا event يصير عند انتهاء الصوت
        if not isinstance(update, StreamAudioEnded):
            return
        chat_id = update.chat_id

        async with state.lock:
            if not state.active.get(chat_id):
                return
            state.index[chat_id] = state.index.get(chat_id, 0) + 1

        async with SessionLocal() as db:
            playlist = await _get_playlist(db)
            if not playlist:
                # إذا صارت فاضية فجأة
                await stop_radio(chat_id, calls)
                return

            loop_enabled = await get_loop(db, chat_id, default_loop)

            # إذا وصلنا لنهاية القائمة
            if state.index.get(chat_id, 0) >= len(playlist):
                if loop_enabled:
                    state.index[chat_id] = 0
                else:
                    await stop_radio(chat_id, calls)
                    return

            # شغل اللي بعدها
            try:
                await _play_current(chat_id, bot, calls, db)
            except Exception:
                # إذا فشل، يحاول مرة ثانية على اللي بعدها
                async with state.lock:
                    state.index[chat_id] = state.index.get(chat_id, 0) + 1
