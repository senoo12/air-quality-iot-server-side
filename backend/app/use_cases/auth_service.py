# app/use_cases/auth_service.py
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.infrastructure.repositories import UserRepository
from app.infrastructure.security import (
    verify_password, 
    get_password_hash, 
    create_access_token, 
    create_refresh_token, 
    decode_token
)

class AuthService:
    def __init__(self, db: Session):
        self.user_repo = UserRepository(db)

    def register_user(self, username: str, password: str, email: str):
        if self.user_repo.get_by_username(username):
            raise HTTPException(status_code=400, detail="Username sudah terdaftar")
        
        if self.user_repo.get_by_email(email):
            raise HTTPException(status_code=400, detail="Email sudah terdaftar")
        
        hashed = get_password_hash(password)
        return self.user_repo.create(username=username, hashed_password=hashed, email=email)

    def login_user(self, username: str, password: str) -> dict:
        """Memproses login dan langsung mengembalikan pasangan token JWT."""
        user = self.user_repo.get_by_username(username)
        if not user or not verify_password(password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Username atau password salah",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Generate tokens dengan menyertakan payload standard
        token_payload = {"sub": user.username, "id": user.id}
        access_token = create_access_token(data=token_payload)
        refresh_token = create_refresh_token(data=token_payload)

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "is_admin": user.is_admin,
            "is_superuser": user.is_superuser
        }

    def refresh_session(self, refresh_token: str) -> dict:
        """Validasi refresh token lama dan terbitkan access token baru."""
        try:
            payload = decode_token(refresh_token)
            username = payload.get("sub")
            user_id = payload.get("id")

            if not username or not user_id:
                raise HTTPException(status_code=401, detail="Format token tidak valid")

            # 1. Ambil data user dari database berdasarkan username atau ID
            user = self.user_repo.get_by_username(username)
            if not user:
                raise HTTPException(status_code=401, detail="User tidak ditemukan")

            # Terbitkan token baru
            new_access_token = create_access_token(data={"sub": username, "id": user_id})
            return {
                "access_token": new_access_token,
                "token_type": "bearer",
                "is_admin": user.is_admin # Sekarang 'user' sudah aman diakses
            }
        except HTTPException as he:
            # Biarkan HTTPException yang sengaja kita buat lolos tanpa tertimpa error 401 general
            raise he
        except Exception as e:
            # Anda bisa print(e) di sini saat debugging untuk melihat jika ada error internal lain
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, 
                detail="Refresh token kadaluwarsa atau tidak valid, silakan login ulang"
            )
    
    def update_user_admin_role(self, token: str, target_user_id: int, is_admin: bool):
        """
        Mengubah status is_admin milik user lain.
        Hanya bisa dilakukan jika aktor yang login memiliki is_superuser == True.
        """
        try:
            # 1. Dekode token untuk mencari username aktor
            actor_info = decode_token(token)
            actor_username = actor_info.get("sub")
            
            # 2. Ambil data aktor dari database
            actor = self.user_repo.get_by_username(actor_username)
            if not actor:
                raise HTTPException(status_code=401, detail="Aktor (Superuser) tidak dikenali")
                
            # 3. Validasi: Apakah aktor benar-back-end seorang superuser?
            if not actor.is_superuser:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Akses ditolak. Hanya Superuser yang dapat mengubah jabatan Admin."
                )
                
            # 4. Validasi: Pastikan user target ada di database
            target_user = self.user_repo.get_by_id(target_user_id)
            if not target_user:
                raise HTTPException(
                    status_code=404, 
                    detail=f"User target dengan ID {target_user_id} tidak ditemukan"
                )
                
            # 5. Eksekusi update melalui repository yang baru kita buat
            return self.user_repo.update_admin_status(target_user_id, is_admin)

        except HTTPException as he:
            # 🟢 PENTING: Melemparkan HTTPException asli (403, 404) agar tidak tertimpa ke 401
            raise he
        except Exception as e:
            # Menangkap real error jika ada masalah lain (misal masalah library JWT atau database)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, 
                detail="Token tidak valid atau telah kadaluwarsa"
            )