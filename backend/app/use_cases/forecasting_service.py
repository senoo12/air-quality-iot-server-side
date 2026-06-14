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
        self.PPM_COLS  = ['ppm_nh3', 'ppm_co', 'ppm_co2', 'ppm_acetone']
        self.LABEL_MAP = {0: "Bad", 1: "Good", 2: "Moderate"}
        self.LAG_STEPS = 48   # t-0 s/d t-48 = 49 titik

    def predict_day_ahead_status(self, device_id: int) -> dict:
        if not self.forecasting_model:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Model forecasting EXP-06 belum dimuat di server."
            )

        # 1. Ambil history 49 data, urutan asc: index 0 = t-48, index 48 = t-0
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

        # 3. Build features
        # mq_history[48] = t-0 (terbaru), mq_history[0] = t-48 (terlama)
        # Loop: lag=0 → ambil index 48 (t-0), lag=48 → ambil index 0 (t-48)
        latest_mq  = mq_history[48]
        latest_dht = dht_history[48]
        features   = {}

        for lag in range(self.LAG_STEPS + 1):   # 0, 1, ..., 48
            mq  = mq_history[48 - lag]
            dht = dht_history[48 - lag]

            features[f'mq135_t-{lag}']       = float(mq.mq135)
            features[f'temperature_t-{lag}']  = float(dht.temperature)
            features[f'humidity_t-{lag}']     = float(dht.humidity)
            # PPM wajib di-log1p (model dilatih pada skala log1p)
            features[f'ppm_nh3_t-{lag}']     = float(np.log1p(mq.ppm_nh3))
            features[f'ppm_co_t-{lag}']      = float(np.log1p(mq.ppm_co))
            features[f'ppm_co2_t-{lag}']     = float(np.log1p(mq.ppm_co2))
            features[f'ppm_acetone_t-{lag}'] = float(np.log1p(mq.ppm_acetone))

        # Fitur kontekstual dari t-0
        features['hour']       = int(latest_mq.created_at.hour)
        features['is_weekend'] = int(latest_mq.created_at.weekday() >= 5)

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
                detail=f"Mismatch fitur: "
                       f"dibangun={df_inference.shape[1]}, "
                       f"diharapkan={self.forecasting_model.n_features_in_}"
            )

        try:
            # 4. Inferensi
            label_idx       = int(self.forecasting_model.predict(df_inference)[0])
            probabilities   = self.forecasting_model.predict_proba(df_inference)[0]
            predicted_label = self.LABEL_MAP[label_idx]
            confidence      = round(float(probabilities[label_idx]), 4)

            # 5. Target waktu H+24
            now_runtime  = latest_mq.created_at
            target_dt    = now_runtime + timedelta(hours=24)

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
                target_time=target_dt.time(),
                target_date=target_dt.date(),
                confidence=confidence
            )
            self.db.commit()
            print(f"🔮 [FORECAST] ID={db_pred.id} | {predicted_label} | conf={confidence}")

            return {
                "id"                   : db_pred.id,
                "conclusion_feature_id": current_conclusion.id,
                "label_status"         : predicted_label,
                "target_time"          : target_dt.time(),
                "target_date"          : target_dt.date(),
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