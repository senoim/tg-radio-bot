from sqlalchemy import String, Integer, Boolean, BigInteger
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import select

class Base(DeclarativeBase):
    pass

class Song(Base):
    __tablename__ = "songs"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(256))
    file_id: Mapped[str] = mapped_column(String(512), nullable=False, unique=True)

class ChatSettings(Base):
    __tablename__ = "chat_settings"
    chat_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    loop: Mapped[bool] = mapped_column(Boolean, default=True)

def make_engine(db_url: str):
    # Railway Postgres URL عادة postgres:// ... نبدله لـ asyncpg
    if db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql+asyncpg://", 1)
    elif db_url.startswith("postgresql://"):
        db_url = db_url.replace("postgresql://", "postgresql+asyncpg://", 1)
    return create_async_engine(db_url, pool_pre_ping=True)

async def init_db(engine):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def get_loop(session, chat_id: int, default_loop: bool):
    row = (await session.execute(select(ChatSettings).where(ChatSettings.chat_id == chat_id))).scalar_one_or_none()
    if not row:
        row = ChatSettings(chat_id=chat_id, loop=default_loop)
        session.add(row)
        await session.commit()
    return row.loop

async def set_loop(session, chat_id: int, value: bool):
    row = (await session.execute(select(ChatSettings).where(ChatSettings.chat_id == chat_id))).scalar_one_or_none()
    if not row:
        row = ChatSettings(chat_id=chat_id, loop=value)
        session.add(row)
    else:
        row.loop = value
    await session.commit()
