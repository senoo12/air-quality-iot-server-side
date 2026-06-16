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
        }

    def refresh_session(self, refresh_token: str) -> dict:
        """Validasi refresh token lama dan terbitkan access token baru."""
        try:
            payload = decode_token(refresh_token)
            username = payload.get("sub")
            user_id = payload.get("id")

            if not username or not user_id:
                raise HTTPException(status_code=401, detail="Format token tidak valid")

            # Terbitkan token baru
            new_access_token = create_access_token(data={"sub": username, "id": user_id})
            return {
                "access_token": new_access_token,
                "token_type": "bearer",
                "is_admin": user.is_admin
            }
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, 
                detail="Refresh token kadaluwarsa atau tidak valid, silakan login ulang"
            )