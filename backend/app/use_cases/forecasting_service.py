# app/use_cases/forecasting_service.py
import joblib
import pandas as pd
import numpy as np
from pathlib import Path
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from fastapi import HTTPException, status
from app.infrastructure.repositories import SensorRepository
from app.domain import models
from zoneinfo import ZoneInfo

class ForecastingService:
    def __init__(self, db: Session):
        self.db = db
        self.sensor_repo = SensorRepository(db)

        BASE_DIR   = Path(__file__).resolve().parents[3]
        model_path = BASE_DIR / "model" / "xgb_forecasting_model.joblib"

        if not model_path.exists():
            print(f"❌ [CRITICAL] File model tidak ditemukan di: {model_path}")
            self.forecasting_model = None
        else:
            self.forecasting_model = joblib.load(model_path)

        self.BASE_FEATURES = [
            'mq135', 'temperature', 'humidity',
            'ppm_nh3', 'ppm_co', 'ppm_co2', 'ppm_acetone'
        ]
        self.PPM_COLS   = ['ppm_nh3', 'ppm_co', 'ppm_co2', 'ppm_acetone']
        self.LABEL_MAP  = {0: "Bad", 1: "Good", 2: "Moderate"}
        self.LAG_STEPS  = 48
        self.JAKARTA_TZ = ZoneInfo("Asia/Jakarta")

    def predict_day_ahead_status(self, device_id: int) -> dict:
        if not self.forecasting_model:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Model forecasting EXP-06 belum dimuat di server."
            )

        # 1. Ambil history 49 data (asc: index 0 = t-48, index 48 = t-0)
        mq_history  = self.sensor_repo.get_mq135_forecast_lag_history(device_id, limit=49)
        dht_history = self.sensor_repo.get_dht22_forecast_lag_history(device_id, limit=49)

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

        latest_mq  = mq_history[48]
        latest_dht = dht_history[48]

        # ── WAKTU REQUEST (untuk kalkulasi target H+24) ───────────────
        # Gunakan waktu saat endpoint dipanggil, bukan waktu sensor
        now_request = datetime.now(tz=self.JAKARTA_TZ)

        # ── WAKTU SENSOR t-0 (untuk fitur hour & is_weekend ke model) ─
        # Model dilatih berdasarkan jam sensor membaca, bukan jam user request
        dt_sensor = latest_mq.created_at
        if dt_sensor.tzinfo is None:
            sensor_time_wib = dt_sensor.replace(tzinfo=self.JAKARTA_TZ)
        else:
            sensor_time_wib = dt_sensor.astimezone(self.JAKARTA_TZ)

        # 3. Build features (345 kolom)
        features = {}

        for lag in range(self.LAG_STEPS + 1):   # lag 0 s/d 48
            mq  = mq_history[48 - lag]           # index 48 = t-0, index 0 = t-48
            dht = dht_history[48 - lag]

            features[f'mq135_t-{lag}']       = float(mq.mq135)
            features[f'temperature_t-{lag}']  = float(dht.temperature)
            features[f'humidity_t-{lag}']     = float(dht.humidity)
            # PPM wajib di-log1p (model dilatih pada skala log1p)
            features[f'ppm_nh3_t-{lag}']     = float(np.log1p(mq.ppm_nh3))
            features[f'ppm_co_t-{lag}']      = float(np.log1p(mq.ppm_co))
            features[f'ppm_co2_t-{lag}']     = float(np.log1p(mq.ppm_co2))
            features[f'ppm_acetone_t-{lag}'] = float(np.log1p(mq.ppm_acetone))

        # Fitur kontekstual dari waktu SENSOR t-0 (bukan waktu request)
        features['hour']       = int(sensor_time_wib.hour)
        features['is_weekend'] = int(sensor_time_wib.weekday() >= 5)

        # Susun urutan kolom sesuai training
        feature_order = [
            f'{feat}_t-{lag}'
            for feat in self.BASE_FEATURES
            for lag in range(self.LAG_STEPS + 1)
        ] + ['hour', 'is_weekend']

        df_inference = pd.DataFrame([features])[feature_order]

        # Validasi jumlah fitur sebelum predict
        if df_inference.shape[1] != self.forecasting_model.n_features_in_:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=(
                    f"Mismatch fitur: "
                    f"dibangun={df_inference.shape[1]}, "
                    f"diharapkan={self.forecasting_model.n_features_in_}"
                )
            )

        try:
            # 4. Inferensi
            label_idx       = int(self.forecasting_model.predict(df_inference)[0])
            probabilities   = self.forecasting_model.predict_proba(df_inference)[0]
            predicted_label = self.LABEL_MAP[label_idx]
            confidence      = round(float(probabilities[label_idx]), 4)

            # 5. Target H+24 dari waktu REQUEST (bukan waktu sensor)
            #    → kalau request jam 14:02, target = besok jam 14:02
            target_dt_wib   = now_request + timedelta(hours=24)
            target_time_wib = target_dt_wib.replace(tzinfo=None).time()
            target_date_wib = target_dt_wib.replace(tzinfo=None).date()

            # 6. Cari anchor ConclusionFeature
            current_conclusion = self.db.query(models.ConclusionFeature)\
                .filter(models.ConclusionFeature.sensor_mq135_id == latest_mq.id)\
                .order_by(models.ConclusionFeature.created_at.desc())\
                .first()

            if not current_conclusion:
                raise ValueError(
                    "Gagal menemukan ConclusionFeature untuk log sensor t-0."
                )

            # 7. Simpan ke DB
            db_pred = self.sensor_repo.save_forecasting_prediction(
                conclusion_feature_id=current_conclusion.id,
                label_status=predicted_label,
                target_time=target_time_wib,
                target_date=target_date_wib,
                confidence=confidence
            )
            self.db.commit()
            print(
                f"🔮 [FORECAST] ID={db_pred.id} | {predicted_label} "
                f"| conf={confidence} "
                f"| target={target_date_wib} {target_time_wib} WIB"
                f"| sensor_hour={features['hour']}"
            )

            return {
                "id"                   : db_pred.id,
                "conclusion_feature_id": current_conclusion.id,
                "label_status"         : predicted_label,
                "target_time"          : db_pred.target_time,
                "target_date"          : db_pred.target_date,
                "confidence"           : confidence,
                "created_at"           : db_pred.created_at
            }

        except HTTPException:
            raise
        except Exception as e:
            self.db.rollback()
            print(f"❌ [FORECASTING FAILURE] {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Gagal mengeksekusi inferensi model forecasting: {str(e)}"
            )