import joblib
import pandas as pd
import numpy as np
from pathlib import Path
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi.concurrency import run_in_threadpool
from datetime import datetime, timedelta
from fastapi import HTTPException, status
from app.infrastructure.repositories import SensorRepository
from app.domain import models
from zoneinfo import ZoneInfo

class ForecastingService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.sensor_repo = SensorRepository(db)

        BASE_DIR   = Path(__file__).resolve().parents[3]
        model_path = BASE_DIR / "model" / "xgb_forecasting_model.joblib"

        if not model_path.exists():
            print(f"❌ [CRITICAL] File model tidak ditemukan di: {model_path}")
            self.forecasting_model = None
        else:
            self.forecasting_model = joblib.load(model_path)

        # 💡 Sesuai urutan list BASE_FEATURES saat training notebook kamu
        self.BASE_FEATURES = [
            'mq135', 'temperature', 'humidity',
            'ppm_nh3', 'ppm_co', 'ppm_co2', 'ppm_acetone'
        ]
        self.LABEL_MAP  = {0: "Bad", 1: "Good", 2: "Moderate"}
        self.LAG_STEPS  = 48
        self.JAKARTA_TZ = ZoneInfo("Asia/Jakarta")

    async def predict_day_ahead_status(self, device_id: int) -> dict:
        if not self.forecasting_model:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Model forecasting EXP-06 belum dimuat di server."
            )

        # 1. Ambil history 49 data dari database Neon
        mq_history  = await self.sensor_repo.get_mq135_forecast_lag_history(device_id, limit=49)
        dht_history = await self.sensor_repo.get_dht22_forecast_lag_history(device_id, limit=49)

        if not mq_history or not dht_history:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Data sensor pada device ini masih kosong."
            )

        # 2. Padding jika data < 49 (cold start)
        while len(mq_history) < 49:
            mq_history.insert(0, mq_history[0])
        while len(dht_history) < 49:
            dht_history.insert(0, dht_history[0])

        # ── WAKTU REQUEST & SENSOR AT t-0 ─────────────────────────────
        now_request = datetime.now(tz=self.JAKARTA_TZ)
        latest_mq_id = int(mq_history[48].id)  # Ambil ID integer primitif untuk filter anchor

        # 💡 DETOKSIFIKASI MUTLAK: Lepas objek ORM dari state session database
        mq_clean = [
            {
                "mq135": float(m.mq135),
                "ppm_nh3": float(m.ppm_nh3),
                "ppm_co": float(m.ppm_co),
                "ppm_co2": float(m.ppm_co2),
                "ppm_acetone": float(m.ppm_acetone),
                "created_at": m.created_at
            }
            for m in mq_history
        ]
        
        dht_clean = [
            {
                "temperature": float(d.temperature),
                "humidity": float(d.humidity)
            }
            for d in dht_history
        ]

        # Ambil record indeks ke-48 (t-0) dari list lokal murni
        latest_mq_clean = mq_clean[48]
        dt_sensor = latest_mq_clean["created_at"]
        if dt_sensor.tzinfo is None:
            sensor_time_wib = dt_sensor.replace(tzinfo=self.JAKARTA_TZ)
        else:
            sensor_time_wib = dt_sensor.astimezone(self.JAKARTA_TZ)

        # 3. Build features (345 kolom) menggunakan nama default skema f0 - f344
        # Harus urut: loop fitur baru loop lag, menghasilkan f0, f1, f2... sesuai training notebook
        feature_values = []
        
        for feat in self.BASE_FEATURES:
            for lag in range(self.LAG_STEPS + 1):  # lag 0 s/d 48
                mq  = mq_clean[48 - lag]
                dht = dht_clean[48 - lag]
                
                if feat == 'mq135':
                    val = mq["mq135"]
                elif feat == 'temperature':
                    val = dht["temperature"]
                elif feat == 'humidity':
                    val = dht["humidity"]
                elif feat == 'ppm_nh3':
                    val = float(np.log1p(mq["ppm_nh3"]))
                elif feat == 'ppm_co':
                    val = float(np.log1p(mq["ppm_co"]))
                elif feat == 'ppm_co2':
                    val = float(np.log1p(mq["ppm_co2"]))
                elif feat == 'ppm_acetone':
                    val = float(np.log1p(mq["ppm_acetone"]))
                
                feature_values.append(val)

        # Masukkan fitur kontekstual jam dan akhir pekan ke f343 dan f344
        feature_values.append(int(sensor_time_wib.hour))
        feature_values.append(int(sensor_time_wib.weekday() >= 5))

        # Bentuk nama kolom string f0 s/d f344 sesuai representasi asli model XGBoost kamu
        feature_names = [f"f{idx}" for idx in range(len(feature_values))]
        
        # Buat DataFrame dengan nama kolom f0, f1, ..., f344
        df_inference = pd.DataFrame([feature_values], columns=feature_names)

        # Validasi kecocokan jumlah kolom
        if df_inference.shape[1] != self.forecasting_model.n_features_in_:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Mismatch fitur: dibangun={df_inference.shape[1]}, diharapkan={self.forecasting_model.n_features_in_}"
            )

        try:
            # 4. Inferensi Model via Threadpool (Aman dari bentrokan exception sub-thread)
            def _execute_xgb_forecast():
                lbl_idx = int(self.forecasting_model.predict(df_inference)[0])
                probs   = self.forecasting_model.predict_proba(df_inference)[0]
                return lbl_idx, probs

            label_idx, probabilities = await run_in_threadpool(_execute_xgb_forecast)
            predicted_label = self.LABEL_MAP[label_idx]
            confidence      = round(float(probabilities[label_idx]), 4)

            # 5. Target H+24 dari waktu REQUEST
            target_dt_wib   = now_request + timedelta(hours=24)
            target_time_wib = target_dt_wib.replace(tzinfo=None).time()
            target_date_wib = target_dt_wib.replace(tzinfo=None).date()

            # 6. Cari anchor ConclusionFeature
            stmt = select(models.ConclusionFeature)\
                .filter(models.ConclusionFeature.sensor_mq135_id == latest_mq_id)\
                .order_by(models.ConclusionFeature.created_at.desc())\
                .limit(1)
            
            result = await self.db.execute(stmt)
            current_conclusion = result.scalars().first()

            if not current_conclusion:
                raise ValueError("Gagal menemukan ConclusionFeature untuk log sensor t-0.")

            # 7. Simpan ke DB secara asinkronus murni
            db_pred = await self.sensor_repo.save_forecasting_prediction(
                conclusion_feature_id=current_conclusion.id,
                label_status=predicted_label,
                target_time=target_time_wib,
                target_date=target_date_wib,
                confidence=confidence
            )
            
            # 💡 AMANKAN SEMUA ATRIBUT KE VARIABEL LOKAL SEBELUM COMMIT
            pred_id         = db_pred.id if db_pred.id else None
            pred_time       = db_pred.target_time
            pred_date       = db_pred.target_date
            pred_created_at = db_pred.created_at
            
            # Amankan ID conclusion ke dalam bentuk integer primitif biasa
            conclusion_id_val = int(current_conclusion.id) 

            # Eksekusi Commit tunggal secara aman
            await self.db.commit()
            
            print(
                f"🔮 [FORECAST] ID={pred_id} | {predicted_label} "
                f"| conf={confidence} "
                f"| target={target_date_wib} {target_time_wib} WIB"
                f"| sensor_hour={sensor_time_wib.hour}"
            )

            # Kembalikan data menggunakan variabel lokal murni bertipe data dasar Python
            return {
                "id"                   : pred_id,
                "conclusion_feature_id": conclusion_id_val,  # 👈 Gunakan variabel lokal primitif yang aman
                "label_status"         : predicted_label,
                "target_time"          : pred_time,
                "target_date"          : pred_date,
                "confidence"           : confidence,
                "created_at"           : pred_created_at
            }

        except HTTPException:
            raise
        except Exception as e:
            await self.db.rollback()
            print(f"❌ [FORECASTING FAILURE] {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Gagal mengeksekusi inferensi model forecasting: {str(e)}"
            )