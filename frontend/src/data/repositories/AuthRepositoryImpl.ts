import { AuthRepository } from "@/src/domain/usecases/AuthRepository";
import { UserToken } from "@/src/domain/entities/Auth";

const API_BASE_URL = 'http://34.101.207.101/api/v1';

export class AuthRepositoryImpl implements AuthRepository {
    async login(username: string, password: string): Promise<UserToken> {
        // Sesuai OAuth2PasswordRequestForm FastAPI, gunakan URLSearchParams (Form Data)
        const formData = new URLSearchParams();
        formData.append('username', username);
        formData.append('password', password);

        const res = await fetch(`${API_BASE_URL}/token`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
            },
            body: formData.toString(),
        });

        if (!res.ok) {
            const errData = await res.json();
            throw new Error(errData.detail || 'Username atau password salah.');
        }

        const data = await res.json();
        return {
            accessToken: data.access_token,
            refreshToken: data.refresh_token,
            tokenType: data.token_type,
        };
    }

    async refreshAccessToken(refreshToken: string): Promise<string> {
        const formData = new URLSearchParams();
        formData.append('refresh_token', refreshToken);

        const res = await fetch('http://34.101.207.101/api/v1/refresh', { // Sesuaikan endpoint refresh token di FastAPI Anda
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
            },
            body: formData.toString(),
        });

        if (!res.ok) {
            throw new Error('Sesi gagal diperbarui otomatis.');
        }

        const data = await res.json();
        return data.access_token; // Mengembalikan access_token baru gress
    }
}