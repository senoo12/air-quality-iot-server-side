from fastapi import FastAPI
from app.api.v1.endpoints import router as api_router
from fastapi.middleware.cors import CORSMiddleware
from app.infrastructure.database import engine
from app.domain import models

# =====================================================================
# PATCH TIMEZONE GLOBAL FIX (MIGRASI DI SINI)
# =====================================================================
import fastapi.routing
from fastapi.encoders import jsonable_encoder
from datetime import datetime
from zoneinfo import ZoneInfo
from sqlalchemy.orm import Session
from sqlalchemy import text
from zoneinfo import ZoneInfo
from app.infrastructure.database import engine, get_db
from fastapi import FastAPI, Depends, status
import time

# 1. Simpan encoder bawaan asli FastAPI
original_jsonable_encoder = fastapi.encoders.jsonable_encoder

# 2. Buat encoder kustom untuk memaksa konversi datetime ke Asia/Jakarta
def custom_jsonable_encoder(obj, *args, **kwargs):
    if isinstance(obj, datetime):
        # Jika database (Neon) mengembalikan datetime tanpa info timezone (naive), pasang UTC
        if obj.tzinfo is None:
            obj = obj.replace(tzinfo=ZoneInfo("UTC"))
        # Paksa putar waktunya (+7 jam) ke Asia/Jakarta
        obj = obj.astimezone(ZoneInfo("Asia/Jakarta"))
        return obj.isoformat()
    return original_jsonable_encoder(obj, *args, **kwargs)

# 3. Bajak sistem internal encoder FastAPI
fastapi.encoders.jsonable_encoder = custom_jsonable_encoder
fastapi.routing.jsonable_encoder = custom_jsonable_encoder
# =====================================================================

# Jalankan skrip pembentukan tabel seperti biasa
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Air Quality Monitoring API", version="1.0")

# Catatan kecil: pastikan format origins Anda adalah list of strings biasa 
# agar CORS tidak error jika nanti asterisk ["*"] dilepas, contoh: origins = ["*"]
origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/debug-time", tags=["Debug"])
def check_my_timezone(db: Session = Depends(get_db)):
    # 1. Cek waktu local machine (Ubuntu Anda)
    local_time = datetime.now()
    local_tzname = time.tzname
    
    # 2. Cek apakah helper fungsi get_wib_time Anda bekerja dengan benar
    try:
        from app.core.config import get_wib_time
        helper_time = get_wib_time()
        helper_result = f"{helper_time} (Zone: {helper_time.tzinfo})"
    except Exception as e:
        helper_result = f"Error load helper: {str(e)}"

    # 3. Cek langsung apa maunya database Neon Postgres Anda saat ini
    try:
        # Menanyakan langsung ke PostgreSQL session timezone-nya apa
        db_tz = db.execute(text("SHOW TIMEZONE;")).scalar()
        # Menanyakan waktu saat ini versi database Neon
        db_now = db.execute(text("SELECT NOW();")).scalar()
    except Exception as e:
        db_tz = f"Error DB: {str(e)}"
        db_now = "Error DB"

    return {
        "1_ubuntu_system_time": str(local_time),
        "2_ubuntu_system_timezone_name": local_tzname,
        "3_python_helper_wib_function": helper_result,
        "4_neon_postgres_session_timezone": db_tz,
        "5_neon_postgres_current_time_raw": str(db_now),
        "6_neon_postgres_current_time_type": str(type(db_now))
    }

# Include semua route dari v1
app.include_router(api_router, prefix="/api/v1")

@app.get("/")
def root():
    return {"message": "Sistem Monitoring Sensor Berjalan"}