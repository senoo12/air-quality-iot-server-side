from sqlalchemy.orm import Session
from app.domain import models
from datetime import date, time

# USER REPOSITORY 
class UserRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_username(self, username: str):
        return self.db.query(models.User).filter(models.User.username == username).first()

    def get_all_users(self):
        return self.db.query(models.User).all()

    def get_by_email(self, email: str):
        return self.db.query(models.User).filter(models.User.email == email).first()

    def create(self, username: str, hashed_password: str, email: str):
        db_user = models.User(
            username=username, 
            hashed_password=hashed_password, 
            email=email
        )
        self.db.add(db_user)
        self.db.commit()
        self.db.refresh(db_user)
        return db_user

    def admin_assign_device(self, user_id: int, device_name: str):
        device = models.Device(user_id=user_id, device_name=device_name)
        self.db.add(device)
        self.db.commit()
        self.db.refresh(device)
        return device


# DEVICE REPOSITORY
class DeviceRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_device(self, user_id: int, name: str):
        device = models.Device(user_id=user_id, device_name=name)
        self.db.add(device)
        self.db.commit()
        self.db.refresh(device)
        return device

    def get_user_devices(self, user_id: int):
        return self.db.query(models.Device).filter(models.Device.user_id == user_id).all()

    def get_device_by_id(self, device_id: int):
        return self.db.query(models.Device).filter(models.Device.id == device_id).first()


# SENSOR REPOSITORY
class SensorRepository:
    def __init__(self, db: Session):
        self.db = db

    # Simpan Log untuk MQ135
    def create_mq135_log(self, device_id: int, mq135: float, nh3: float, co: float, co2: float, acetone: float):
        db_log = models.SensorMQ135(
            device_id=device_id,
            mq135=mq135,
            ppm_nh3=nh3,
            ppm_co=co,
            ppm_co2=co2,
            ppm_acetone=acetone
        )
        self.db.add(db_log)
        self.db.commit()
        self.db.refresh(db_log)
        return db_log

    # Simpan Log untuk DHT22
    def create_dht22_log(self, device_id: int, temperature: float, humidity: float):
        db_log = models.SensorDHT22(
            device_id=device_id,
            temperature=temperature,
            humidity=humidity
        )
        self.db.add(db_log)
        self.db.commit()
        self.db.refresh(db_log)
        return db_log

    # PIPELINE TIME SERIES: Mengambil History 2 Jam (t-0 sampai t-3)
    def get_mq135_time_series_history(self, device_id: int) -> list[models.SensorMQ135]:
        """
        Mengambil 4 data MQ135 terbaru (t-0, t-1, t-2, t-3) untuk windowing 2 jam.
        Data diurutkan dari yang paling lama (t-3) ke paling baru (t-0) 
        agar siap dibentuk menjadi array/tensor oleh pipeline model.
        """
        subquery = self.db.query(models.SensorMQ135)\
            .filter(models.SensorMQ135.device_id == device_id)\
            .order_by(models.SensorMQ135.created_at.desc())\
            .limit(4).all()
        
        # kembali urutan agar sekuensial dari masa lalu ke sekarang: [t-3, t-2, t-1, t-0]
        return subquery[::-1]

    def get_dht22_time_series_history(self, device_id: int) -> list[models.SensorDHT22]:
        """
        Mengambil 4 data DHT22 terbaru (t-0, t-1, t-2, t-3) untuk windowing 2 jam.
        Urutan dibalik dari yang paling lama (t-3) ke paling baru (t-0).
        """
        subquery = self.db.query(models.SensorDHT22)\
            .filter(models.SensorDHT22.device_id == device_id)\
            .order_by(models.SensorDHT22.created_at.desc())\
            .limit(4).all()
        
        return subquery[::-1]

    # =========================================================================

    # Gabungkan fitur sensor untuk preprocessing (Conclusion Feature)
    def create_conclusion_feature(self, mq135_id: int, dht22_id: int, current_hour: time, is_weekend: bool):
        feature = models.ConclusionFeature(
            sensor_mq135_id=mq135_id,
            sensor_dht22_id=dht22_id,
            hour=current_hour,
            is_weekend=is_weekend
        )
        self.db.add(feature)
        self.db.commit()
        self.db.refresh(feature)
        return feature

    # Simpan hasil klasifikasi real-time
    def save_classification(self, conclusion_feature_id: int, label_status: str):
        classif = models.Classification(
            conclusion_feature_id=conclusion_feature_id,
            label_status=label_status
        )
        self.db.add(classif)
        self.db.commit()
        self.db.refresh(classif)
        return classif

    # DAY-AHEAD FORECASTING PIPELINE
    def get_mq135_forecast_lag_history(self, device_id: int, limit: int = 49) -> list[models.SensorMQ135]:
        """Mengambil 49 data terakhir dari yang terlama ke terbaru (t-48 s/d t-0) untuk forecasting"""
        subquery = self.db.query(models.SensorMQ135)\
            .filter(models.SensorMQ135.device_id == device_id)\
            .order_by(models.SensorMQ135.created_at.desc())\
            .limit(limit).subquery()
        return self.db.query(subquery).order_by(subquery.c.created_at.asc()).all()

    def get_dht22_forecast_lag_history(self, device_id: int, limit: int = 49) -> list[models.SensorDHT22]:
        """Mengambil 49 data terakhir dari yang terlama ke terbaru (t-48 s/d t-0) untuk forecasting"""
        subquery = self.db.query(models.SensorDHT22)\
            .filter(models.SensorDHT22.device_id == device_id)\
            .order_by(models.SensorDHT22.created_at.desc())\
            .limit(limit).subquery()
        return self.db.query(subquery).order_by(subquery.c.created_at.asc()).all()

    def save_forecasting_prediction(self, conclusion_feature_id: int, label_status: str, 
                                    target_time: time, target_date: date, confidence: float):
        """Menyimpan hasil ramalan 24 jam ke depan langsung ke dalam tabel predictions"""
        db_prediction = models.Prediction(
            conclusion_feature_id=conclusion_feature_id,
            label_status=label_status,
            target_time=target_time,
            target_date=target_date,
            confidence=confidence
        )
        self.db.add(db_prediction)
        self.db.flush()
        return db_prediction