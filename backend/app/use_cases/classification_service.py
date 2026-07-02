import joblib
import pandas as pd
import numpy as np
from pathlib import Path
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.concurrency import run_in_threadpool
from app.infrastructure.repositories import SensorRepository
from zoneinfo import ZoneInfo
 
 
class ClassificationService:
    """
    Service layer untuk Time Series Classification (TSC) nowcasting.
    Menggunakan model XGBoost A3 (Window=4, lag t-0 s/d t-3).
    """
 
    FEATURES_PER_STEP = [
        'mq135', 'temperature', 'humidity',
        'ppm_nh3', 'ppm_co', 'ppm_co2', 'ppm_acetone',
        'hour', 'is_weekend'
    ]
    LAG_LABELS = ['t-3', 't-2', 't-1', 't-0']
    LABEL_MAP  = {0: "Bad", 1: "Good", 2: "Moderate"}
 
    def __init__(self, db: AsyncSession):
        self.db          = db
        self.sensor_repo = SensorRepository(db)
        self.jakarta_tz  = ZoneInfo("Asia/Jakarta")
 
        model_path = Path(__file__).resolve().parents[3] / "model" / "xgb_tsc_model.joblib"
        self.tsc_model = joblib.load(model_path)
        print(f"✅ [TSC] Model dimuat — fitur: {self.tsc_model.n_features_in_}")

    async def process_time_series_classification(
        self, current_mq: dict, current_dht: dict, conclusion_id: int, device_id: int, save_to_db: bool = True
    ):
        """Menjalankan inferensi XGBoost TSC dari gabungan data history ORM dan data payload primitif."""
        
        # 1. Ambil history [t-3, t-2, t-1] dari database
        mq_history  = await self.sensor_repo.get_mq135_time_series_history(device_id)
        dht_history = await self.sensor_repo.get_dht22_time_series_history(device_id)
 
        # Cold start padding: Gunakan data primitif dictionary saat ini jika tabel history masih kosong
        while len(mq_history) < 4:
            mq_history.insert(0, mq_history[0] if mq_history else current_mq)
        while len(dht_history) < 4:
            dht_history.insert(0, dht_history[0] if dht_history else current_dht)
 
        # 2. Susun timesteps [t-3, t-2, t-1, t-0] menggunakan pembacaan dinamis helper
        timesteps = []
        for i in range(4):
            mq  = mq_history[i]
            dht = dht_history[i]
            
            # 💡 SOLUSI ABSOLUT: Ambil nilainya dan paksa detasemen dari state ORM 
            # dengan menampungnya langsung ke tipe data primitif Python
            mq135_val     = float(self._get_val(mq, "mq135"))
            temp_val      = float(self._get_val(dht, "temperature"))
            hum_val       = float(self._get_val(dht, "humidity"))
            nh3_val       = float(self._get_val(mq, "ppm_nh3"))
            co_val        = float(self._get_val(mq, "ppm_co"))
            co2_val       = float(self._get_val(mq, "ppm_co2"))
            acetone_val   = float(self._get_val(mq, "ppm_acetone"))
            
            # Ambil data waktu dan langsung amankan ke tipe datetime biasa
            created_time  = self._get_val(mq, "created_at")
            dt_wib        = self._to_jakarta(created_time)
            
            timesteps.append({
                'mq135'      : mq135_val,
                'temperature': temp_val,
                'humidity'   : hum_val,
                'ppm_nh3'    : float(np.log1p(nh3_val)),
                'ppm_co'     : float(np.log1p(co_val)),
                'ppm_co2'    : float(np.log1p(co2_val)),
                'ppm_acetone': float(np.log1p(acetone_val)),
                'hour'       : int(dt_wib.hour),
                'is_weekend' : int(dt_wib.weekday() >= 5)
            })
 
        # 3. Bentuk DataFrame (urutan: t-3 dulu → t-0 terakhir)
        features = {}
        for i, lag in enumerate(self.LAG_LABELS):
            for feat in self.FEATURES_PER_STEP:
                features[f"{feat}_{lag}"] = timesteps[i][feat]
 
        feature_order = [
            f"{feat}_{lag}" for lag in self.LAG_LABELS for feat in self.FEATURES_PER_STEP
        ]
        df = pd.DataFrame([features])[feature_order]
 
        # Validasi nama kolom vs model
        if hasattr(self.tsc_model, 'feature_names_in_'):
            expected = list(self.tsc_model.feature_names_in_)
            actual   = list(df.columns)
            if expected != actual:
                mismatch = [(e, a) for e, a in zip(expected, actual) if e != a]
                raise ValueError(f"Feature name mismatch ({len(mismatch)} kolom berbeda): {mismatch[:5]}")
 
        # 4. Prediksi ML (Isolasi Thread CPU-bound)
        label_idx     = await run_in_threadpool(lambda: int(self.tsc_model.predict(df)[0]))
        current_label = self.LABEL_MAP[label_idx]

        if save_to_db:
            await self.sensor_repo.save_classification(
            conclusion_feature_id=conclusion_id,
            label_status=current_label
        )
        await self.db.flush()
 
        print(f"✅ [TSC] {current_label} (label_idx={label_idx})")
        return current_label
 
    # ─────────────────────────────────────────────────────────────
    # PRIVATE HELPERS
    # ─────────────────────────────────────────────────────────────
    
    def _get_val(self, obj, key: str):
        """Helper dinamis untuk membaca data baik dari objek ORM maupun dictionary."""
        if isinstance(obj, dict):
            return obj.get(key)
        return getattr(obj, key)

    def _to_jakarta(self, dt):
        if dt.tzinfo is None:
            return dt.replace(tzinfo=ZoneInfo("UTC")).astimezone(self.jakarta_tz)
        return dt.astimezone(self.jakarta_tz)