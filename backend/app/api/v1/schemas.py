from pydantic import BaseModel, EmailStr
from datetime import datetime, date, time
from typing import List, Optional

# ==========================================
# 1. AUTH SCHEMAS
# ==========================================
class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str
    created_at: datetime
    updated_at: datetime

class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    is_admin: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ==========================================
# 2. DEVICE SCHEMAS
# ==========================================
class DeviceCreate(BaseModel):
    device_name: str
    status_active: bool = True

class DeviceResponse(DeviceCreate):
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class DeviceStatusUpdate(BaseModel):
    status_active: bool

# ==========================================
# 3. INDIVIDUAL SENSOR LOG RESPONSES
# ==========================================
class SensorMQ135Response(BaseModel):
    id: int
    device_id: int
    mq135: float
    ppm_nh3: float
    ppm_co: float
    ppm_co2: float
    ppm_acetone: float
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class SensorDHT22Response(BaseModel):
    id: int
    device_id: int
    temperature: float
    humidity: float
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ==========================================
# 4. PIPELINE SCHEMAS (INGESTION & HISTORY)
# ==========================================
class SensorLogCreate(BaseModel):
    """
    Skema input data dari IoT (ESP32/Wokwi).
    Menerima parameter data lingkungan makro dan gas terurai untuk pipeline.
    """
    device_id: int
    temperature: float
    humidity: float
    mq135: float
    ppm_nh3: float
    ppm_co: float
    ppm_co2: float
    ppm_acetone: float

class SensorHistoryCombinedResponse(BaseModel):
    """
    Skema response untuk endpoint /history/sensor.
    Menyatukan relasi antara conclusion_feature dengan log MQ135 dan DHT22.
    """
    id: int  # ID dari conclusion_feature
    sensor_mq135_id: int
    sensor_dht22_id: int
    hour: time
    is_weekend: bool
    created_at: datetime
    
    # Nested data dari hasil join tabel
    sensor_mq135: SensorMQ135Response
    sensor_dht22: SensorDHT22Response

    class Config:
        from_attributes = True


# ==========================================
# 5. CLASSIFICATION SCHEMAS (REAL-TIME STATUS)
# ==========================================
class ClassificationResponse(BaseModel):
    """
    Skema untuk data klasifikasi tunggal/terbaru.
    """
    id: int
    conclusion_feature_id: int
    label_status: str
    created_at: datetime

    class Config:
        from_attributes = True


class ClassificationHistoryResponse(BaseModel):
    """
    Skema untuk list riwayat tracking status kualitas udara.
    """
    id: int
    conclusion_feature_id: int
    label_status: str
    created_at: datetime

    class Config:
        from_attributes = True


# ==========================================
# 6. PREDICTION SCHEMAS (FORECASTING - BERDASARKAN ERD FINAL)
# ==========================================
class PredictionCreate(BaseModel):
    conclusion_feature_id: int
    label_status: str
    target_time: time
    target_date: date
    confidence: float

class PredictionResponse(BaseModel):
    id: int
    conclusion_feature_id: int
    label_status: str
    target_time: time
    target_date: date
    confidence: float
    created_at: datetime
    
    class Config:
        from_attributes = True