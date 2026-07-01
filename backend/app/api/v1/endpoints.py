# app/api/v1/endpoints.py
from fastapi import APIRouter, Depends, HTTPException, status, Header
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func  
from sqlalchemy.orm import joinedload
from typing import List, Optional

# Infrastruktur & Keamanan
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
from app.use_cases.log_testing_service import LogTestingService

router = APIRouter()

async def get_current_admin(token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)):
    user_repo = UserRepository(db)
    user_info = await decode_token(token)
    username = user_info.get("sub") 
    user = await user_repo.get_by_username(username)
    
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
async def register(user_data: schemas.UserCreate, db: AsyncSession = Depends(get_db)):
    auth_service = AuthService(db)
    
    # Jalankan use case pendaftaran user secara async
    await auth_service.register_user(user_data.username, user_data.password, user_data.email)
    
    # 💡 PERBAIKAN: Ambil data username langsung dari payload 'user_data' bawaan client
    # Ini menghindari error DetachedInstance karena malas membaca objek DB asinkronus
    return {
        "message": "User berhasil didaftarkan", 
        "username": user_data.username
    }

@router.post("/token", response_model=dict)
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)):
    auth_service = AuthService(db)
    return await auth_service.login_user(form_data.username, form_data.password)

@router.post("/refresh", response_model=dict)
async def refresh_access_token(refresh_token: str, db: AsyncSession = Depends(get_db)):  # 👈 Ubah ke AsyncSession
    auth_service = AuthService(db)
    return await auth_service.refresh_session(refresh_token)


@router.get("/users", response_model=List[schemas.UserResponse])
async def list_all_users(admin: models.User = Depends(get_current_admin), db: AsyncSession = Depends(get_db)):  # 👈 Ubah ke AsyncSession
    user_repo = UserRepository(db)
    return await user_repo.get_all_users()

@router.patch("/users/{user_id}/admin-status")
async def patch_user_admin_status(
    user_id: int, 
    payload: schemas.UpdateAdminSchema, 
    token: str = Depends(oauth2_scheme), 
    db: AsyncSession = Depends(get_db)
):
    auth_service = AuthService(db)
    updated_user = await auth_service.update_user_admin_role(
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
async def create_device(
    device_data: schemas.DeviceCreate, 
    user_target_id: int,
    admin: models.User = Depends(get_current_admin), 
    db: AsyncSession = Depends(get_db)
):
    device_service = DeviceService(db)
    return await device_service.register_new_device(user_target_id, device_data.device_name, status_active=device_data.status_active)

@router.get("/devices", response_model=List[schemas.DeviceResponse], tags=["Devices"])
async def list_my_devices(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
):
    device_service = DeviceService(db)
    return await device_service.get_user_device_list(token)

@router.patch("/devices/{device_id}/status", response_model=schemas.DeviceResponse, tags=["Devices"])
async def update_my_device_status(
    device_id: int,
    payload: schemas.DeviceStatusUpdate,
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
):
    device_service = DeviceService(db)
    return await device_service.change_device_status(token, device_id, payload.status_active)

# ==========================================
# 3. SENSOR & REAL-TIME CLASSIFICATION ENDPOINTS
# ==========================================
@router.post("/sensors/log", response_model=dict)
async def log_sensor_data(
    data: schemas.SensorLogCreate, 
    token: str = Depends(oauth2_scheme), 
    db: AsyncSession = Depends(get_db)
):
    user_info = await decode_token(token)
    sensor_service = SensorService(db)
    
    result = await sensor_service.log_data(
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
async def get_combined_sensor_history(
    device_id: int,
    limit: Optional[int] = None,
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
):
    user_info = await decode_token(token)
    current_user_id = user_info.get("id")
    
    device_repo = DeviceRepository(db)
    device = await device_repo.get_device_by_id(device_id)
    if not device or device.user_id != current_user_id:
        raise HTTPException(status_code=403, detail="Akses ditolak! Perangkat ini bukan milik Anda.")

    # 💡 REFAKTOR: Migrasi dari db.query() ke await db.execute(select())
    stmt = select(models.ConclusionFeature)\
        .options(
            joinedload(models.ConclusionFeature.sensor_mq135),  # Eager load untuk MQ135
            joinedload(models.ConclusionFeature.sensor_dht22)   # Eager load untuk DHT22
        )\
        .join(models.SensorMQ135, models.ConclusionFeature.sensor_mq135_id == models.SensorMQ135.id)\
        .join(models.SensorDHT22, models.ConclusionFeature.sensor_dht22_id == models.SensorDHT22.id)\
        .filter(models.SensorMQ135.device_id == device_id)\
        .order_by(models.ConclusionFeature.created_at.desc())\
        .limit(limit)
        
    result = await db.execute(stmt)
    return result.scalars().all()


@router.get("/classification/latest/{device_id}", response_model=schemas.ClassificationResponse)
async def get_latest_air_quality_classification(
    device_id: int,
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
):
    user_info = await decode_token(token)
    current_user_id = user_info.get("id")
    
    device_repo = DeviceRepository(db)
    device = await device_repo.get_device_by_id(device_id)
    if not device or device.user_id != current_user_id:
        raise HTTPException(status_code=403, detail="Akses ditolak! Perangkat ini bukan milik Anda.")
    
    # 💡 REFAKTOR: Migrasi dari db.query() ke await db.execute(select())
    stmt = select(models.Classification)\
        .join(models.ConclusionFeature)\
        .join(models.SensorMQ135)\
        .filter(models.SensorMQ135.device_id == device_id)\
        .order_by(models.Classification.created_at.desc())
        
    result = await db.execute(stmt)
    latest_class = result.scalars().first()
        
    if not latest_class:
        raise HTTPException(status_code=404, detail="Belum ada data klasifikasi untuk perangkat ini")
    return latest_class


@router.get("/history/classification/{device_id}", response_model=List[schemas.ClassificationHistoryResponse])
async def get_classification_history(
    device_id: int,
    status: Optional[str] = None,
    limit: Optional[int] = None,
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
):
    user_info = await decode_token(token)
    current_user_id = user_info.get("id")
    
    device_repo = DeviceRepository(db)
    device = await device_repo.get_device_by_id(device_id)
    if not device or device.user_id != current_user_id:
        raise HTTPException(status_code=403, detail="Akses ditolak! Perangkat ini bukan milik Anda.")

    stmt = select(models.Classification)\
        .join(models.ConclusionFeature)\
        .join(models.SensorMQ135)\
        .filter(models.SensorMQ135.device_id == device_id)

    if status and status.strip() != "" and status.lower() != "all":
        # Mengubah .status menjadi .label_status sesuai struktur data analitik Anda
        stmt = stmt.filter(func.lower(models.Classification.label_status) == status.lower().strip())
        
    stmt = stmt.order_by(models.Classification.created_at.desc()).limit(limit)
        
    result = await db.execute(stmt)
    return result.scalars().all()

@router.get("/forecast/day-ahead/{device_id}", response_model=schemas.PredictionResponse, tags=["Forecasting Pipeline"])
async def get_day_ahead_air_quality_forecast(
    device_id: int,
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
):
    user_info = await decode_token(token)
    current_user_id = user_info.get("id")
    
    device_repo = DeviceRepository(db)
    device = await device_repo.get_device_by_id(device_id)
    if not device or device.user_id != current_user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Akses ditolak! Perangkat IoT ini bukan terdaftar atas akun Anda."
        )

    forecast_service = ForecastingService(db)
    return await forecast_service.predict_day_ahead_status(device_id)

@router.post("/log_testing")
async def create_log(data: schemas.LogCreateSchema, db: AsyncSession = Depends(get_db)):
    service = LogTestingService(db)
    return await service.create_log(data.dict())

@router.post("/log_testing/bulk", status_code=status.HTTP_201_CREATED)
async def create_bulk_logs(
    payload: schemas.LogBulkCreateSchema, 
    db: AsyncSession = Depends(get_db)
):
    service = LogTestingService(db)
    await service.create_bulk_logs(payload.logs)
    return {"message": f"Berhasil menambahkan {len(payload.logs)} log."}

@router.get("/log_testing", response_model=List[schemas.LogTestingResponse])
async def get_logs(db: AsyncSession = Depends(get_db)):
    service = LogTestingService(db)
    logs = await service.get_all_logs_detailed()
    
    results = []
    for log in logs:
        cf = log.classification.conclusion_feature
        # Mengambil device_id dari sensor (asumsi keduanya memiliki device_id)
        d_id = cf.sensor_mq135.device_id 
        
        results.append({
            "id": log.id,
            "device_id": d_id,
            "mq135": cf.sensor_mq135.mq135,
            "temperature": cf.sensor_dht22.temperature,
            "humidity": cf.sensor_dht22.humidity,
            "ppm_nh3": cf.sensor_mq135.ppm_nh3,
            "ppm_co": cf.sensor_mq135.ppm_co,
            "ppm_co2": cf.sensor_mq135.ppm_co2,
            "ppm_acetone": cf.sensor_mq135.ppm_acetone,
            "mode": log.mode,
            "t_sensor": log.t_sensor,
            "t_send": log.t_send,
            "t_ack": log.t_ack,
            "t_actuator": log.t_actuator,
            "rtt_us": log.rtt_us,
            "e2e_us": log.e2e_us,
            "payload_bits": log.payload_bits,
            "payload_length": log.payload_length,
            "total_heap": log.total_heap,
            "free_heap": log.free_heap,
            "ram_load_pct": log.ram_load_pct,
            "voltage_v": log.voltage_v,
            "current_ma": log.current_ma,
            "power_mw": log.power_mw,
            "energy_mj": log.energy_mj,
            "actuator_status": log.actuator_status,
            "created_at": log.created_at
        })
    return results