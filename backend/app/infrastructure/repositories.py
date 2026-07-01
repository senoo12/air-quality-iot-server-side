from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.domain import models
from datetime import date, time

# =====================================================================
# REFAKTOR REPOSITORI ASYNCHRONOUS (NEON ASYNC COMPATIBLE)
# =====================================================================

class UserRepository:
    def __init__(self, db: AsyncSession):  # 👈 Gunakan AsyncSession
        self.db = db

    async def get_by_username(self, username: str):
        stmt = select(models.User).filter(models.User.username == username)
        result = await self.db.execute(stmt)
        return result.scalars().first()

    async def get_all_users(self):
        stmt = select(models.User)
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def get_by_email(self, email: str):
        result = await self.db.execute(select(models.User).filter(models.User.email == email))
        return result.scalars().first()
    
    async def get_by_id(self, user_id: int):
        result = await self.db.execute(select(models.User).filter(models.User.id == user_id))
        return result.scalars().first()

    async def create(self, username: str, hashed_password: str, email: str):
        db_user = models.User(
            username=username, 
            hashed_password=hashed_password, 
            email=email
        )
        self.db.add(db_user)
        await self.db.commit()
        await self.db.refresh(db_user)
        return db_user

    async def admin_assign_device(self, user_id: int, device_name: str):
        device = models.Device(user_id=user_id, device_name=device_name)
        self.db.add(device)
        await self.db.flush()
        return device
    
    async def update_admin_status(self, user_id: int, is_admin: bool):
        """Mengubah status is_admin dari user berdasarkan ID."""
        user = await self.get_by_id(user_id)
        if user:
            user.is_admin = is_admin
            await self.db.flush()
        return user


class DeviceRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_device(self, user_id: int, name: str, status_active: bool):
        device = models.Device(user_id=user_id, device_name=name, status_active=status_active)
        self.db.add(device)
        await self.db.commit()
        await self.db.refresh(device)
        return device
    
    async def update_token(self, device_id: int, token: str):
        device = await self.get_device_by_id(device_id)
        if device:
            device.device_token = token
            await self.db.commit()
            await self.db.refresh(device)
        return device

    async def get_device_by_id(self, device_id: int):
        result = await self.db.execute(select(models.Device).filter(models.Device.id == device_id))
        return result.scalars().first()

    async def get_user_devices(self, user_id: int):
        result = await self.db.execute(select(models.Device).filter(models.Device.user_id == user_id))
        return result.scalars().all()

    async def get_by_user_id(self, user_id: int):
        result = await self.db.execute(select(models.Device).filter(models.Device.user_id == user_id))
        return result.scalars().first()

    async def get_by_name(self, device_name: str):
        result = await self.db.execute(select(models.Device).filter(models.Device.device_name == device_name))
        return result.scalars().first()
    
    async def update_status(self, device_id: int, status_active: bool):
        db_device = await self.get_device_by_id(device_id)
        if db_device:
            db_device.status_active = status_active
            await self.db.flush()
        return db_device


class SensorRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_mq135_log(self, device_id: int, mq135: float, nh3: float, co: float, co2: float, acetone: float):
        db_log = models.SensorMQ135(
            device_id=device_id,
            mq135=mq135,
            ppm_nh3=nh3,
            ppm_co=co,
            ppm_co2=co2,
            ppm_acetone=acetone
        )
        self.db.add(db_log)
        await self.db.flush()
        return db_log

    async def create_dht22_log(self, device_id: int, temperature: float, humidity: float):
        db_log = models.SensorDHT22(
            device_id=device_id,
            temperature=temperature,
            humidity=humidity
        )
        self.db.add(db_log)
        await self.db.flush()
        return db_log

    async def get_mq135_time_series_history(self, device_id: int) -> list[models.SensorMQ135]:
        result = await self.db.execute(
            select(models.SensorMQ135)
            .filter(models.SensorMQ135.device_id == device_id)
            .order_by(models.SensorMQ135.created_at.desc())
            .limit(4)
        )
        subquery = result.scalars().all()
        return subquery[::-1]

    async def get_dht22_time_series_history(self, device_id: int) -> list[models.SensorDHT22]:
        result = await self.db.execute(
            select(models.SensorDHT22)
            .filter(models.SensorDHT22.device_id == device_id)
            .order_by(models.SensorDHT22.created_at.desc())
            .limit(4)
        )
        subquery = result.scalars().all()
        return subquery[::-1]

    async def create_conclusion_feature(self, mq135_id: int, dht22_id: int, current_hour: time, is_weekend: bool):
        feature = models.ConclusionFeature(
            sensor_mq135_id=mq135_id,
            sensor_dht22_id=dht22_id,
            hour=current_hour,
            is_weekend=is_weekend
        )
        self.db.add(feature)
        await self.db.flush()
        return feature

    async def save_classification(self, conclusion_feature_id: int, label_status: str):
        classif = models.Classification(
            conclusion_feature_id=conclusion_feature_id,
            label_status=label_status
        )
        self.db.add(classif)
        await self.db.flush()
        return classif

    async def get_mq135_forecast_lag_history(self, device_id: int, limit: int = 49) -> list[models.SensorMQ135]:
        stmt = (
            select(models.SensorMQ135)
            .filter(models.SensorMQ135.device_id == device_id)
            .order_by(models.SensorMQ135.created_at.desc())
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        subquery = result.scalars().all()
        # Urutkan asc berdasarkan waktu pembuatan (t-48 ke t-0)
        return sorted(subquery, key=lambda x: x.created_at)

    async def get_dht22_forecast_lag_history(self, device_id: int, limit: int = 49) -> list[models.SensorDHT22]:
        stmt = (
            select(models.SensorDHT22)
            .filter(models.SensorDHT22.device_id == device_id)
            .order_by(models.SensorDHT22.created_at.desc())
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        subquery = result.scalars().all()
        return sorted(subquery, key=lambda x: x.created_at)

    async def save_forecasting_prediction(self, conclusion_feature_id: int, label_status: str, 
                                          target_time: time, target_date: date, confidence: float):
        db_prediction = models.Prediction(
            conclusion_feature_id=conclusion_feature_id,
            label_status=label_status,
            target_time=target_time,
            target_date=target_date,
            confidence=confidence
        )
        self.db.add(db_prediction)
        await self.db.flush()
        return db_prediction

class LogTestingRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_log(self, log_data: dict) -> models.LogTesting:
        """Menyimpan log baru ke database."""
        new_log = models.LogTesting(**log_data)
        self.db.add(new_log)
        await self.db.commit()
        await self.db.refresh(new_log)
        return new_log
    
    async def create_bulk_logs(self, logs_data: list[dict]) -> list[models.LogTesting]:
            """Menyimpan banyak log sekaligus ke database."""
            # Sekarang logs_data adalah list of dict, jadi **log akan bekerja
            new_logs = [models.LogTesting(**log) for log in logs_data]
            self.db.add_all(new_logs)
            await self.db.commit()
            # Opsional: refresh untuk mendapatkan ID yang digenerate DB
            for log in new_logs:
                await self.db.refresh(log)
            return new_logs
    
    async def get_all_logs(self):
        """
        Mengambil semua log. 
        Catatan: Join kompleks dilakukan di Service layer untuk fleksibilitas query.
        """
        stmt = select(models.LogTesting).order_by(models.LogTesting.created_at.desc())
        result = await self.db.execute(stmt)
        return result.scalars().all()