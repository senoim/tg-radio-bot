import asyncio
from pyrogram import Client
from pytgcalls import PyTgCalls
from sqlalchemy.ext.asyncio import async_sessionmaker

from .config import BOT_TOKEN, API_ID, API_HASH, ASSISTANT_SESSION, DATABASE_URL, DEFAULT_LOOP
from .db import make_engine, init_db
from .handlers import setup_handlers
from .radio import attach_events

async def main():
    engine = make_engine(DATABASE_URL)
    await init_db(engine)
    SessionLocal = async_sessionmaker(engine, expire_on_commit=False)

    bot = Client("bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)
    assistant = Client("assistant", api_id=API_ID, api_hash=API_HASH, session_string=ASSISTANT_SESSION)

    await bot.start()
    await assistant.start()

    calls = PyTgCalls(assistant)
    await calls.start()

    # events للانتقال التلقائي
    attach_events(calls, bot, SessionLocal, DEFAULT_LOOP)

    # handlers
    setup_handlers(bot, calls, SessionLocal)

    print("✅ Radio bot is running...")
    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())
