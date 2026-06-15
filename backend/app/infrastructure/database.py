import os
from sqlalchemy import create_engine, event
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
from datetime import datetime
from zoneinfo import ZoneInfo

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if DATABASE_URL and "sslmode" not in DATABASE_URL:
    DATABASE_URL += "?sslmode=require"

engine = create_engine(DATABASE_URL) # Hapus connect_args options karena Neon mengabaikannya
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# 👈 TAMBAHKAN EVENT LISTENER INI DI SINI
@event.listens_for(SessionLocal, "before_flush")
def force_wib_timezone(session, flush_context, instances):
    """Mencegat proses save/update untuk memastikan objek datetime menggunakan waktu Jakarta."""
    jakarta_tz = ZoneInfo("Asia/Jakarta")
    for obj in session.new | session.dirty:
        for attr in obj.__mapper__.attrs:
            # Cari field yang bertipe datetime
            value = getattr(obj, attr.key)
            if isinstance(value, datetime):
                if value.tzinfo is None:
                    # Jika naive, konversi langsung ke Asia/Jakarta
                    setattr(obj, attr.key, value.replace(tzinfo=jakarta_tz))
                else:
                    setattr(obj, attr.key, value.astimezone(jakarta_tz))

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()