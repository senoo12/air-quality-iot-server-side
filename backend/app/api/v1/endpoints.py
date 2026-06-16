# app/api/v1/endpoints.py
from fastapi import APIRouter, Depends, HTTPException, status, Header
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from typing import List

# Infrasruktur & Keamanan
from app.infrastructure.database import get_db
from app.infrastructure.security import oauth2_scheme, decode_token
from app.infrastructure.repositories import UserRepository, DeviceRepository

# Skema & Domain Model
from app.api.v1 import schemas
from app.domain import models

# Use Cases / Service Layer
from app.use_cases.auth_service import AuthService
from app.use_cases.device_service import DeviceService
from app.use_cases.sensor_service import SensorService
from app.use_cases.forecasting_service import ForecastingService
from app.use_cases.classification_service import ClassificationService

router = APIRouter()

def get_current_admin(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    user_info = decode_token(token)
    user_repo = UserRepository(db)
    
    username = user_info.get("sub") 
    user = user_repo.get_by_username(username)
    
    if not user:
        raise HTTPException(status_code=401, detail="User tidak ditemukan")
    
    if not user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Akses ditolak! Anda bukan Administrator."
        )
    return user


# ==========================================
# AUTH ENDPOINTS (REGISTER, LOGIN, REFRESH)
# ==========================================

@router.post("/register", response_model=dict, status_code=status.HTTP_201_CREATED)
def register(user_data: schemas.UserCreate, db: Session = Depends(get_db)):
    auth_service = AuthService(db)
    user = auth_service.register_user(user_data.username, user_data.password, user_data.email)
    return {"message": "User berhasil didaftarkan", "username": user.username}


@router.post("/token", response_model=dict)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    auth_service = AuthService(db)
    # Semua proses pencocokan password dan pembuatan token dikerjakan di service
    return auth_service.login_user(form_data.username, form_data.password)


@router.post("/refresh", response_model=dict)
def refresh_access_token(refresh_token: str, db: Session = Depends(get_db)):
    auth_service = AuthService(db)
    # Proses pembongkaran dan validasi refresh token dikerjakan di service
    return auth_service.refresh_session(refresh_token)


@router.get("/users", response_model=List[schemas.UserResponse])
def list_all_users(admin: models.User = Depends(get_current_admin), db: Session = Depends(get_db)):
    user_repo = UserRepository(db)
    return user_repo.get_all_users()

@router.patch("/users/{user_id}/admin-status")
def patch_user_admin_status(
    user_id: int, 
    payload: schemas.UpdateAdminSchema, 
    token: str = Depends(oauth2_scheme), # 🟢 Menggunakan Depends(oauth2_scheme) menggantikan Header(...)
    db: Session = Depends(get_db)
):
    """
    Endpoint khusus Superuser untuk mengubah status is_admin dari user tertentu.
    """
    # 💡 Anda tidak perlu lagi melakukan split "Bearer " secara manual!
    # oauth2_scheme otomatis memotong teks "Bearer " dan memberikan string token murninya saja.
    
    auth_service = AuthService(db)
    updated_user = auth_service.update_user_admin_role(
        token=token, 
        target_user_id=user_id, 
        is_admin=payload.is_admin
    )
    
    return {
        "status": "success",
        "message": f"Status admin user ID {user_id} berhasil diperbarui menjadi {payload.is_admin}.",
        "data": {
            "id": updated_user.id,
            "username": updated_user.username,
            "is_admin": updated_user.is_admin
        }
    }

# ==========================================
# 2. DEVICE ENDPOINTS
# ==========================================

@router.post("/devices", response_model=schemas.DeviceResponse, status_code=status.HTTP_201_CREATED, tags=["Devices"])
def create_device(
    device_data: schemas.DeviceCreate, 
    user_target_id: int,
    admin: models.User = Depends(get_current_admin), 
    db: Session = Depends(get_db)
):
    """Mendaftarkan perangkat IoT baru ke user tertentu (Khusus Admin)."""
    device_service = DeviceService(db)
    return device_service.register_new_device(user_target_id, device_data.device_name, status_active=device_data.status_active)


@router.get("/devices", response_model=List[schemas.DeviceResponse], tags=["Devices"])
def list_my_devices(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    """Melihat daftar seluruh perangkat IoT yang dimiliki oleh user aktif saat ini."""
    device_service = DeviceService(db)
    return device_service.get_user_device_list(token)

@router.patch("/devices/{device_id}/status", response_model=schemas.DeviceResponse, tags=["Devices"])
def update_my_device_status(
    device_id: int,
    payload: schemas.DeviceStatusUpdate,
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    """
    Endpoint untuk user mengubah status (nyala/mati) perangkat IoT miliknya sendiri.
    Sistem akan menolak jika user mencoba mengubah device milik orang lain.
    """
    device_service = DeviceService(db)
    return device_service.change_device_status(token, device_id, payload.status_active)

# ==========================================
# 3. SENSOR & REAL-TIME CLASSIFICATION ENDPOINTS
# ==========================================

@router.post("/sensors/log", response_model=dict)
def log_sensor_data(
    data: schemas.SensorLogCreate, 
    token: str = Depends(oauth2_scheme), 
    db: Session = Depends(get_db)
):
    """
    Endpoint masukan data dari perangkat IoT (ESP32/Wokwi).
    Menerima parameter data lingkungan makro dan mikro gas terurai.
    """
    user_info = decode_token(token)
    sensor_service = SensorService(db)
    
    result = sensor_service.log_data(
        user_id=user_info.get("id"),
        device_id=data.device_id,
        temp=data.temperature,
        hum=data.humidity,
        mq135=data.mq135,
        nh3=data.ppm_nh3,
        co=data.ppm_co,
        co2=data.ppm_co2,
        acetone=data.ppm_acetone
    )
    
    if isinstance(result, dict) and result.get("status") == "error":
        raise HTTPException(status_code=403, detail=result["message"])
        
    return result


@router.get("/history/sensor/{device_id}", response_model=List[schemas.SensorHistoryCombinedResponse])
def get_combined_sensor_history(
    device_id: int,
    limit: int = 50,
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    """
    Mengambil riwayat data sensor terintegrasi (MQ135 + DHT22) 
    melalui tabel perantara conclusion_feature berdasarkan Device ID dan User ID.
    """
    user_info = decode_token(token)
    current_user_id = user_info.get("id")
    
    # Validasi kepemilikan device
    device_repo = DeviceRepository(db)
    device = device_repo.get_device_by_id(device_id)
    if not device or device.user_id != current_user_id:
        raise HTTPException(status_code=403, detail="Akses ditolak! Perangkat ini bukan milik Anda.")

    # Jalankan query join tiga tabel secara langsung untuk efisiensi pipeline
    history = db.query(models.ConclusionFeature)\
        .join(models.SensorMQ135, models.ConclusionFeature.sensor_mq135_id == models.SensorMQ135.id)\
        .join(models.SensorDHT22, models.ConclusionFeature.sensor_dht22_id == models.SensorDHT22.id)\
        .filter(models.SensorMQ135.device_id == device_id)\
        .order_by(models.ConclusionFeature.created_at.desc())\
        .limit(limit).all()
        
    return history


@router.get("/classification/latest/{device_id}", response_model=schemas.ClassificationResponse)
def get_latest_air_quality_classification(
    device_id: int,
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    """
    Menarik hasil klasifikasi status kualitas udara real-time terakhir (Good/Moderate/Bad)
    berdasarkan conclusion_feature dari device tertentu.
    """
    user_info = decode_token(token)
    current_user_id = user_info.get("id")
    
    # Validasi kepemilikan device terlebih dahulu
    device_repo = DeviceRepository(db)
    device = device_repo.get_device_by_id(device_id)
    if not device or device.user_id != current_user_id:
        raise HTTPException(status_code=403, detail="Akses ditolak! Perangkat ini bukan milik Anda.")
    
    # Ambil data klasifikasi terbaru lewat query join
    latest_class = db.query(models.Classification)\
        .join(models.ConclusionFeature)\
        .join(models.SensorMQ135)\
        .filter(models.SensorMQ135.device_id == device_id)\
        .order_by(models.Classification.created_at.desc())\
        .first()
        
    if not latest_class:
        raise HTTPException(status_code=404, detail="Belum ada data klasifikasi untuk perangkat ini")
        
    return latest_class


@router.get("/history/classification/{device_id}", response_model=List[schemas.ClassificationHistoryResponse])
def get_classification_history(
    device_id: int,
    limit: int = 50,
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    """
    Mengambil daftar seluruh riwayat track record hasil klasifikasi status kualitas udara 
    dari tabel classification berdasarkan Device ID dan User ID untuk kebutuhan analytics/grafik.
    """
    user_info = decode_token(token)
    current_user_id = user_info.get("id")
    
    # Validasi kepemilikan device
    device_repo = DeviceRepository(db)
    device = device_repo.get_device_by_id(device_id)
    if not device or device.user_id != current_user_id:
        raise HTTPException(status_code=403, detail="Akses ditolak! Perangkat ini bukan milik Anda.")

    # Ambil riwayat log status kualitas udara melintasi relasi database
    history_class = db.query(models.Classification)\
        .join(models.ConclusionFeature)\
        .join(models.SensorMQ135)\
        .filter(models.SensorMQ135.device_id == device_id)\
        .order_by(models.Classification.created_at.desc())\
        .limit(limit).all()
        
    return history_class

@router.get("/forecast/day-ahead/{device_id}", response_model=schemas.PredictionResponse, tags=["Forecasting Pipeline"])
def get_day_ahead_air_quality_forecast(
    device_id: int,
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    """
    Endpoint ramalan kualitas udara 24 jam ke depan (Day-Ahead Forecasting).
    
    Flow Kerja:
    1. Memvalidasi kepemilikan token pengguna terhadap id perangkat IoT target.
    2. Menarik tren data runtunan waktu 24 jam ke belakang (49 log lag).
    3. Memetakan 345 kolom fitur input runtime ke dalam model XGBoost EXP-06.
    4. Menyimpan dan mengembalikan model data ramalan ke dalam struktur tabel 'predictions'.
    """
    # 1. Validasi Kepemilikan Device Pengguna
    user_info = decode_token(token)
    current_user_id = user_info.get("id")
    
    device_repo = DeviceRepository(db)
    device = device_repo.get_device_by_id(device_id)
    if not device or device.user_id != current_user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Akses ditolak! Perangkat IoT ini bukan terdaftar atas akun Anda."
        )

    # 2. Eksekusi Proses Peramalan Melalui Service Layer
    forecast_service = ForecastingService(db)
    return forecast_service.predict_day_ahead_status(device_id)