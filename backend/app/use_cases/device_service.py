from datetime import timedelta
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status
from app.infrastructure.repositories import DeviceRepository, UserRepository
from app.infrastructure.security import decode_token, create_access_token, create_access_token_for_device

class DeviceService:
    def __init__(self, db: AsyncSession):
        self.device_repo = DeviceRepository(db)
        self.user_repo = UserRepository(db)

    async def register_new_device(self, user_target_id: int, device_name: str, status_active: bool = True):
        # 1. Validasi: Cek apakah user ada
        user_exists = await self.user_repo.get_by_id(user_target_id)
        if not user_exists:
            raise HTTPException(
                status_code=404, 
                detail=f"User dengan ID {user_target_id} tidak ditemukan"
            )
        
        user_has_device = await self.device_repo.get_by_user_id(user_target_id)
        if user_has_device:
            raise HTTPException(
                status_code=400,
                detail=f"User dengan ID {user_target_id} sudah memiliki perangkat terdaftar (Maksimal 1 perangkat per user)."
            )
        
        # 2. Validasi: Cek apakah device_name sudah terdaftar global
        device_exists = await self.device_repo.get_by_name(device_name)
        if device_exists:
            raise HTTPException(
                status_code=400, 
                detail=f"Device dengan nama '{device_name}' sudah terdaftar"
            )
        
        # 3. Jika semua validasi lolos, simpan device baru ke DB
        new_device = await self.device_repo.create_device(user_target_id, device_name, status_active=status_active)
        print(f"DEBUG: Device berhasil dibuat. ID: {new_device.id}, Name: {new_device.device_name}")
        
        # 💡 4. GENERATE LONG-LIVED ACCESS TOKEN (Masa aktif 10 Tahun)
        # Ambil ID device yang baru saja terbit dari database
        token_payload = {
            "sub": f"device_{new_device.device_name}",
            "id": new_device.id, # 👈 Sangat penting untuk identifikasi parameter URL {device_id} nanti
            "is_device": True    # Flag pembeda dari akun user biasa (manusia)
        }
        
        long_expiry = timedelta(days=3650) # 10 Tahun
        device_token = await create_access_token_for_device(data=token_payload, expires_delta=long_expiry)

        await self.device_repo.update_token(new_device.id, device_token)
        
        # 💡 5. Kembalikan objek dictionary gabungan data device + token abadi
        return {
            "id": new_device.id,
            "device_name": new_device.device_name,
            "user_id": new_device.user_id,
            "status_active": new_device.status_active,
            "device_token": device_token,
            "created_at": new_device.created_at,
            "updated_at": new_device.updated_at
        }
    
    async def get_user_device_list(self, token: str) -> list:
        """Membongkar token JWT dan mengambil daftar device milik user tersebut."""
        try:
            user_info = await decode_token(token)
            user_id = user_info.get("id")
            
            if not user_id:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED, 
                    detail="Token tidak mengenali identitas User"
                )
                
            return await self.device_repo.get_user_devices(user_id)
            
        except Exception as e:
            if isinstance(e, HTTPException):
                raise e
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, 
                detail="Token tidak valid atau telah kadaluwarsa"
            )

    async def change_device_status(self, token: str, device_id: int, status_active: bool):
        try:
            # 1. Dekode token JWT untuk mendapatkan ID user yang sedang login
            user_info = await decode_token(token)
            current_user_id = user_info.get("id")
            
            if not current_user_id:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token tidak mengenali identitas User."
                )
            
            # 2. Ambil data device dari database lewat repository untuk diperiksa
            device = await self.device_repo.get_device_by_id(device_id)
            if not device:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Device dengan ID {device_id} tidak ditemukan."
                )
            
            # 3. Validasi Kepemilikan (Ownership)
            # Memastikan user_id di tabel devices sama dengan ID user dari token JWT
            if device.user_id != current_user_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Akses ditolak. Anda bukan pemilik dari perangkat IoT ini."
                )
            
            # 4. Jika validasi lolos, lakukan pembaruan status ke database
            return await self.device_repo.update_status(device_id, status_active)
            
        except Exception as e:
            if isinstance(e, HTTPException):
                raise e
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, 
                detail="Token tidak valid atau telah kadaluwarsa"
            )