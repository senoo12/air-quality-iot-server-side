import asyncio
import sys
import os

# Tambahkan root directory backend ke sys.path agar impor modul 'app' terdeteksi lancar
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

# 💡 PERBAIKAN: Ganti SessionLocal menjadi AsyncSessionLocal sesuai struktur database.py kamu
from app.infrastructure.database import AsyncSessionLocal 
from backend.app.seeds.good_classification_seeder import AccuracyTestSeeder

async def main():
    print("⚡ Inisialisasi Klien Seeder Otomatis Folder app/seeds/...")
    # 💡 PERBAIKAN: Gunakan AsyncSessionLocal() di sini
    async with AsyncSessionLocal() as session:
        seeder = AccuracyTestSeeder(session)
        # Menembak user perf_user_2199 yang dipakai di pytest
        await seeder.seed_all_test_scenarios(target_username="perf_user_2199")
    print("✨ Selesai. Kondisi data di DB Neon sekarang sudah ideal.")

if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())