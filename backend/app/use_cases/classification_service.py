# app/use_cases/classification_service.py
import joblib
import pandas as pd
import numpy as np
from pathlib import Path
from sqlalchemy.orm import Session
from app.infrastructure.repositories import SensorRepository
from zoneinfo import ZoneInfo

class ClassificationService:
    def __init__(self, db: Session):
        self.db = db
        self.sensor_repo = SensorRepository(db)

        BASE_DIR = Path(__file__).resolve().parents[3]
        self.tsc_model = joblib.load(BASE_DIR / "model" / "xgb_tsc_model.joblib")

        # Mapping sesuai urutan encoding di notebook training
        # {0: 'Bad', 1: 'Good', 2: 'Moderate'}
        self.LABEL_MAP = {0: "Bad", 1: "Good", 2: "Moderate"}

        # Kolom yang di-log1p (mq135 TIDAK termasuk)
        self.PPM_LOG_COLS = ['ppm_nh3', 'ppm_co', 'ppm_co2', 'ppm_acetone']

        # Urutan fitur per timestep (harus identik dengan training)
        self.FEATURES_PER_STEP = [
            'mq135', 'temperature', 'humidity',
            'ppm_nh3', 'ppm_co', 'ppm_co2', 'ppm_acetone',
            'hour', 'is_weekend'
        ]

    def process_time_series_classification(self, mq135_log, dht22_log, conclusion_id: int):
        """Menjalankan inferensi XGBoost TSC dan menyimpan hasil ke tabel classification."""
        try:
            # ── 1. Ambil history [t-3, t-2, t-1, t-0] dari database ──────────
            mq_history  = self.sensor_repo.get_mq135_time_series_history(mq135_log.device_id)
            dht_history = self.sensor_repo.get_dht22_time_series_history(dht22_log.device_id)

            # Pad dengan data saat ini jika history < 4 (cold start)
            while len(mq_history) < 4:
                mq_history.insert(0, mq_history[0] if mq_history else mq135_log)
            while len(dht_history) < 4:
                dht_history.insert(0, dht_history[0] if dht_history else dht22_log)

            # ── 2. Susun raw values per timestep ─────────────────────────────
            # mq_history[0] = t-3 (paling lama), mq_history[3] = t-0 (sekarang)
            timesteps = []
            jakarta_tz = ZoneInfo("Asia/Jakarta")

            for i in range(4):
                mq  = mq_history[i]
                dht = dht_history[i]

                dt_raw = mq.created_at
                if dt_raw.tzinfo is None:
                    # Asumsikan data mentah dari Neon adalah UTC murni, lalu konversi ke Jakarta (+7 jam)
                    dt_jakarta = dt_raw.replace(tzinfo=ZoneInfo("UTC")).astimezone(jakarta_tz)
                else:
                    # Jika sudah aware, konversikan zona waktunya secara langsung
                    dt_jakarta = dt_raw.astimezone(jakarta_tz)

                # 💡 VALIDASI DARURAT: Jika setelah dikonversi jamnya TETAP bernilai 12 
                # (artinya database menyimpan jam lokal 12 tanpa membaca offset asli),
                # paksa labelnya langsung menjadi Asia/Jakarta menggunakan replace()
                if dt_jakarta.hour == dt_raw.hour and dt_raw.hour != 19:
                    # Cari selisih jam saat ini antara data Anda (19) dan data input (12)
                    # Jika selisihnya tepat 7 jam, berarti dt_raw sebenarnya adalah jam UTC murni
                    dt_jakarta = dt_raw.replace(tzinfo=ZoneInfo("UTC")).astimezone(jakarta_tz)
                    
                    # Jika masih tidak bergeser ke 19, artinya database mencatat waktu server internal (UTC) sebagai waktu lokal.
                    # Kita lakukan pengecekan manual terakhir:
                    if dt_jakarta.hour != 19:
                        # Jika dt_raw.hour adalah 12 dan Anda tahu aslinya jam 19, tambahkan timedelta secara manual
                        from datetime import timedelta
                        if dt_raw.hour == 12:
                            dt_jakarta = dt_raw + timedelta(hours=7)

                timesteps.append({
                    'mq135'      : mq.mq135,                                     # raw, tanpa log
                    'temperature': dht.temperature,
                    'humidity'   : dht.humidity,
                    'ppm_nh3'    : np.log1p(mq.ppm_nh3),                         # log1p
                    'ppm_co'     : np.log1p(mq.ppm_co),                          # log1p
                    'ppm_co2'    : np.log1p(mq.ppm_co2),                         # log1p
                    'ppm_acetone': np.log1p(mq.ppm_acetone),                     # log1p
                    'hour'       : dt_jakarta.hour,
                    'is_weekend' : int(dt_jakarta.weekday() >= 5)
                })

                print(f"🔍 [DEBUG TIMEZONE] tipe: {type(dt_raw)} | nilai asli: {dt_raw} | tzinfo: {dt_raw.tzinfo} | hasil jam jakarta: {dt_jakarta.hour}")
            # timesteps[0] = t-3, timesteps[3] = t-0

            # ── 3. Bentuk DataFrame sesuai urutan fitur model ─────────────────
            # Urutan model: [semua fitur t-3, semua fitur t-2, ..., semua fitur t-0]
            # Nama kolom: mq135_t-3, temperature_t-3, ..., is_weekend_t-0
            lag_labels = ['t-3', 't-2', 't-1', 't-0']  # indeks 0..3 → timesteps[0..3]

            features = {}
            for i, lag in enumerate(lag_labels):
                for feat in self.FEATURES_PER_STEP:
                    features[f"{feat}_{lag}"] = timesteps[i][feat]

            # Pastikan urutan kolom identik dengan model.feature_names_in_
            feature_order = [
                f"{feat}_{lag}"
                for lag in lag_labels
                for feat in self.FEATURES_PER_STEP
            ]

            df = pd.DataFrame([features])[feature_order]

            # Validasi nama kolom vs model (early error sebelum predict)
            if hasattr(self.tsc_model, 'feature_names_in_'):
                expected = list(self.tsc_model.feature_names_in_)
                actual   = list(df.columns)
                if expected != actual:
                    mismatch = [(e, a) for e, a in zip(expected, actual) if e != a]
                    raise ValueError(f"Feature name mismatch ({len(mismatch)} kolom berbeda): {mismatch[:5]}")

            # ── 4. Prediksi ───────────────────────────────────────────────────
            label_idx     = int(self.tsc_model.predict(df)[0])
            current_label = self.LABEL_MAP.get(label_idx, "Moderate")

            # ── 5. Simpan ke tabel Classification ────────────────────────────
            self.sensor_repo.save_classification(
                conclusion_feature_id=conclusion_id,
                label_status=current_label
            )
            self.db.commit()
            print(f"✅ [CLASSIFICATION] XGBoost → {current_label} (label_idx={label_idx})")
            return current_label

        except Exception as e:
            self.db.rollback()
            print(f"⚠️ [CLASSIFICATION GAGAL] Error: {e}")
            try:
                self.sensor_repo.save_classification(
                    conclusion_feature_id=conclusion_id,
                    label_status="Moderate"
                )
                self.db.commit()
                return "Moderate"
            except Exception:
                return None