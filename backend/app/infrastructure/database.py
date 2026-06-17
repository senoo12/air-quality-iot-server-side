import os
from urllib.parse import urlparse, urlunparse, parse_qsl, urlencode
from sqlalchemy import event
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import declarative_base, sessionmaker, Session
import asyncpg  # 👈 Tambahkan import asyncpg secara langsung
from dotenv import load_dotenv
from datetime import datetime
from zoneinfo import ZoneInfo

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

# =====================================================================
# INTERSEPTOR KONEKSI NATIVE ASYNCPG (ANTI VERSION MISMATCH)
# =====================================================================
if DATABASE_URL:
    # 1. Pastikan skema menggunakan postgresql+asyncpg
    if DATABASE_URL.startswith("postgresql://"):
        DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)
    elif DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+asyncpg://", 1)

    # 2. Amankan query options bawaan Neon agar tidak hilang
    parsed_url = urlparse(DATABASE_URL)
    query_params = dict(parse_qsl(parsed_url.query))
    
    # Buang sslmode dari string URL agar tidak memicu error duplikasi/type error
    if "sslmode" in query_params:
        query_params.pop("sslmode")
    if "channel_binding" in query_params:
        query_params.pop("channel_binding")
        
    new_query_string = urlencode(query_params)
    parsed_url = parsed_url._replace(query=new_query_string)
    DATABASE_URL = urlunparse(parsed_url)

# 3. Buat fungsi creator kustom untuk menyaring keyword terlarang secara paksa
def custom_asyncpg_creator():
    """Membongkar URL dan memanggil asyncpg.connect murni tanpa parameter ilegal."""
    # Konversi URL SQLAlchemy kembali ke format DSN standar yang dipahami asyncpg murni
    raw_dsn = DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://", 1)
    
    async def connect():
        # Ambil koneksi murni dari asyncpg dengan memaksa ssl=True (Neon kompatibel)
        return await asyncpg.connect(raw_dsn, ssl=True)
    return connect
# =====================================================================

# Buat Async Engine dengan mendelegasikan pembuatan koneksi ke fungsi creator kita
async_engine = create_async_engine(
    DATABASE_URL,
    pool_size=20,
    max_overflow=40,
    pool_timeout=30,
    pool_pre_ping=True,
    async_creator=custom_asyncpg_creator()  # 👈 BAJAK KONEKSI DI SINI
)

AsyncSessionLocal = sessionmaker(
    autocommit=False, 
    autoflush=False, 
    bind=async_engine, 
    class_=AsyncSession
)

Base = declarative_base()

@event.listens_for(Session, "before_flush")
def force_wib_timezone(session, flush_context, instances):
    jakarta_tz = ZoneInfo("Asia/Jakarta")
    for obj in session.new | session.dirty:
        for attr in obj.__mapper__.attrs:
            if hasattr(attr, 'key'):
                value = getattr(obj, attr.key)
                if isinstance(value, datetime):
                    if value.tzinfo is None:
                        setattr(obj, attr.key, value.replace(tzinfo=jakarta_tz))
                    else:
                        setattr(obj, attr.key, value.astimezone(jakarta_tz))

async def get_db():
    async with AsyncSessionLocal() as db:
        try:
            yield db
            await db.commit()
        except Exception:
            await db.rollback()
            raise
        finally:
            await db.close()