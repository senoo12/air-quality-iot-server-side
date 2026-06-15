# app/use_cases/sensor_service.py
from sqlalchemy.orm import Session
from datetime import datetime
from app.domain import models
from app.infrastructure.repositories import SensorRepository, DeviceRepository
from app.use_cases.classification_service import ClassificationService
from app.core.config import get_wib_time

class SensorService:
    def __init__(self, db: Session):
        self.db = db
        self.sensor_repo = SensorRepository(db)
        self.device_repo = DeviceRepository(db)
        self.classification_service = ClassificationService(db)

    def log_data(self, user_id: int, device_id: int, temp: float, hum: float, 
                 mq135: float, nh3: float, co: float, co2: float, acetone: float):
        
        # 1. Validasi Device & Hak Akses User
        device = self.device_repo.get_device_by_id(device_id)
        if not device or device.user_id != user_id:
            return {"status": "error", "message": "Unauthorized device"}
        
        now = datetime.utcnow()
        
        try:
            # =================================================================
            # BLOK TRANSAKSI BERBARENGAN (ATOMIC INSERT)
            # =================================================================
            
            # A. Buat Log Sensor MQ135 (Simpan ke memory database, ambil ID-nya)
            mq135_log = self.sensor_repo.create_mq135_log(
                device_id=device_id, mq135=mq135, nh3=nh3, co=co, co2=co2, acetone=acetone
            )
            self.db.flush() 

            # B. Buat Log Sensor DHT22 (Simpan ke memory database, ambil ID-nya)
            dht22_log = self.sensor_repo.create_dht22_log(
                device_id=device_id, temperature=temp, humidity=hum
            )
            self.db.flush() 

            # C. Buat Log ConclusionFeature SECARA BERBARENGAN
            # Mengikat langsung FK dari ID MQ135 dan DHT22 yang baru saja di-flush
            conclusion_feature = self.sensor_repo.create_conclusion_feature(
                mq135_id=mq135_log.id,
                dht22_id=dht22_log.id,
                current_hour=get_wib_time().time(),
                is_weekend=int(get_wib_time().weekday() >= 5)
            )
            self.db.flush()

            # Commit fase pertama: Pastikan ketiga data di atas masuk bersamaan ke DB
            self.db.commit()
            print(f"🔹 [SUCCESS] Data Sensor & ConclusionFeature (ID: {conclusion_feature.id}) sukses masuk DB berbarengan.")

        except Exception as e:
            self.db.rollback()
            print(f"❌ [CRITICAL] Gagal menyimpan data paket sensor berbarengan: {e}")
            return {"status": "error", "message": f"Gagal memproses data sensor: {str(e)}"}

        # =================================================================
        # FASE INFERENSI ML (XGBOOST CLASSIFICATION)
        # =================================================================
        # Jalankan inferensi time-series setelah data t-0 resmi terekam di DB
        air_quality_status = self.classification_service.process_time_series_classification(
            mq135_log=mq135_log, 
            dht22_log=dht22_log, 
            conclusion_id=conclusion_feature.id
        )

        return {
            "status": "success", 
            "message": "Data logged and conclusion attached successfully",
            "realtime_classification": air_quality_status if air_quality_status else "Classification Error"
        }