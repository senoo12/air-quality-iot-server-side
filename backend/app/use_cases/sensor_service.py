from datetime import datetime

from typing import Optional
from app.domain import models
from app.infrastructure.repositories import SensorRepository, DeviceRepository
from app.use_cases.classification_service import ClassificationService
from app.core.config import get_wib_time
from sqlalchemy.ext.asyncio import AsyncSession
 
class SensorService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.sensor_repo = SensorRepository(db)
        self.device_repo = DeviceRepository(db)
        self.classification_service = ClassificationService(db)
 
    async def log_data(self, user_id: int, device_id: int, temp: float, hum: float,
                       mq135: float, nh3: float, co: float, co2: float, acetone: float,
                       label_status: Optional[str] = None):
 
        # 1. Validasi Device & Hak Akses User
        device = await self.device_repo.get_by_user_id(user_id)
        if not device or int(device.id) != int(device_id):
            return {"status": "error", "message": "Unauthorized device"}
 
        try:
            # ── A. Log MQ135 ──────────────────────────────────────────
            mq135_log = await self.sensor_repo.create_mq135_log(
                device_id=device_id, mq135=mq135, nh3=nh3, co=co, co2=co2, acetone=acetone
            )
 
            # ── B. Log DHT22 ──────────────────────────────────────────
            dht22_log = await self.sensor_repo.create_dht22_log(
                device_id=device_id, temperature=temp, humidity=hum
            )
 
            # ── C. ConclusionFeature ──────────────────────────────────
            conclusion_feature = await self.sensor_repo.create_conclusion_feature(
                mq135_id=mq135_log.id,
                dht22_id=dht22_log.id,
                current_hour=get_wib_time().time(),
                is_weekend=int(get_wib_time().weekday() >= 5)
            )
 
            await self.db.flush()
            print(f"🔹 [SUCCESS] Sensor & ConclusionFeature (ID: {conclusion_feature.id}) sukses masuk DB.")
            
            # 💡 AMANKAN DATA LOKAL SEBAGAI DICTIONARY MURNI (ANTI EXPIRED ORM ATTRIBUTE)
            current_mq_data = {
                "mq135": float(mq135),
                "ppm_nh3": float(nh3),
                "ppm_co": float(co),
                "ppm_co2": float(co2),
                "ppm_acetone": float(acetone),
                "created_at": datetime.utcnow()  # Atur penanda waktu murni
            }
            
            current_dht_data = {
                "temperature": float(temp),
                "humidity": float(hum)
            }
            
            conclusion_id = conclusion_feature.id

        except Exception as e:
            await self.db.rollback()
            print(f"❌ [CRITICAL] Gagal menyimpan data sensor: {e}")
            return {"status": "error", "message": f"Gagal memproses data sensor: {str(e)}"}

        # ── Inferensi ML atau Pakai Label Lokal ──────────────────────
        if label_status:
            # 1. Simpan label dari Edge ke DB secara manual
            await self.sensor_repo.save_classification(
                conclusion_feature_id=conclusion_id,
                label_status=label_status
            )
            await self.db.commit()
            air_quality_status = label_status
        else:
            # 2. Jika tidak ada, baru jalankan ML (yang di dalamnya sudah ada save_to_db=True)
            air_quality_status = await self.classification_service.process_time_series_classification(
                current_mq=current_mq_data,
                current_dht=current_dht_data,
                conclusion_id=conclusion_id,
                device_id=device_id,
                save_to_db=True
            )
            await self.db.commit() # Commit hasil prediksi ML
 
        return {
            "status": "success",
            "message": "Data logged successfully",
            "realtime_classification": air_quality_status
        }