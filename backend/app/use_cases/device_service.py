# app/use_cases/device_service.py
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.infrastructure.repositories import DeviceRepository
from app.infrastructure.security import decode_token

class DeviceService:
    def __init__(self, db: Session):
        self.device_repo = DeviceRepository(db)

    def register_new_device(self, user_target_id: int, device_name: str):
        """Logika pembuatan device baru yang dipicu oleh Administrator."""
        # Anda bisa menambahkan validasi tambahan di sini jika diperlukan,
        # misalnya mengecek apakah nama device sudah terpakai atau belum.
        return self.device_repo.create_device(user_target_id, device_name)

    def get_user_device_list(self, token: str) -> list:
        """Membongkar token JWT dan mengambil daftar device milik user tersebut."""
        try:
            user_info = decode_token(token)
            user_id = user_info.get("id")
            
            if not user_id:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED, 
                    detail="Token tidak mengenali identitas User"
                )
                
            return self.device_repo.get_user_devices(user_id)
            
        except Exception as e:
            if isinstance(e, HTTPException):
                raise e
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, 
                detail="Token tidak valid atau telah kadaluwarsa"
            )