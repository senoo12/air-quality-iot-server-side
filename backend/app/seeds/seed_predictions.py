import sys
import os
from datetime import datetime, timedelta, timezone
import random

# Fix Path agar bisa import app
sys.path.append(os.getcwd())

from app.infrastructure.database import SessionLocal
from app.use_cases.sensor_service import SensorService
from app.domain import models

def seed_forecasting_data():
    db = SessionLocal()
    service = SensorService(db)
    
    device_id = 1
    user_id = 2

    print(f"Memulai Seeding 48 data dengan TSC trigger (Logika Window)...")

    # ambil waktu sekarang sebagai titik akhir
    now = datetime.now(timezone.utc)
    
    for i in range(48, 0, -1):
        timestamp = now - timedelta(minutes=30 * i)
        
        new_log = models.SensorLog(
            device_id=device_id,
            temperature=round(random.uniform(28, 32), 2),
            humidity=round(random.uniform(50, 70), 2),
            mq_value=round(random.uniform(30, 180), 2),
            timestamp=timestamp 
        )
        
        db.add(new_log)
        db.commit() 
        db.refresh(new_log)

        
        print(f"[{i}] Memproses Log pada {timestamp.strftime('%H:%M')}...")
        service.predict_tsc_window(user_id, new_log)

    print(f"48 Data Sensor & 48 Hasil TSC berhasil masuk secara kronologis.")
    
    # 3. Trigger Forecasting cukup 1x saja di akhir
    print("🧠 Menghitung prediksi forecasting untuk besok (T+24)...")
    service.predict_next_day(user_id, device_id)
    print("🚀 Seeding Selesai!")

if __name__ == "__main__":
    seed_forecasting_data()