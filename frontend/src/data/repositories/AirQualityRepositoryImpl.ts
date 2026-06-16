import { AirQualityRepository, UserDropdownEntity } from "./AirQualityRepository";
import { Device, SensorLog, Classification, ForecastPrediction } from "@/src/domain/entities/AirQuality";

const API_BASE_URL = 'https://air-quality-sti-unj.duckdns.org/api/v1';

export class AirQualityRepositoryImpl implements AirQualityRepository {
    private getHeaders(token: string) {
        return {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
        };
    }

    async getDevices(token: string): Promise<Device[]> {
        const res = await fetch(`${API_BASE_URL}/devices`, { headers: this.getHeaders(token) });
        if (!res.ok) throw new Error('Gagal mengambil daftar perangkat.');
        const data = await res.json();
        return data.map((d: any) => ({
            id: d.id,
            deviceName: d.device_name,
            userId: d.user_id,
            isActive: d.status_active // 💡 Menyesuaikan mapping snake_case terbaru dari FastAPI
        }));
    }

    async toggleDeviceStatus(deviceId: number, status: boolean, token: string): Promise<Device> {
        // 💡 MENYESUAIKAN: Rute rute ke /status dan payload field ke status_active
        const res = await fetch(`${API_BASE_URL}/devices/${deviceId}/status`, {
            method: 'PATCH',
            headers: this.getHeaders(token),
            body: JSON.stringify({ status_active: status }),
        });

        if (!res.ok) {
            throw new Error('Gagal mengirimkan perintah kendali ke sakelar ESP32.');
        }

        const d = await res.json();
        return {
            id: d.id,
            deviceName: d.device_name,
            userId: d.user_id,
            isActive: d.status_active // 💡 Di-map kembali ke camelCase properti entitas frontend
        };
    }

    async getSensorHistory(deviceId: number, limit: number, token: string): Promise<SensorLog[]> {
        const res = await fetch(`${API_BASE_URL}/history/sensor/${deviceId}?limit=${limit}`, { headers: this.getHeaders(token) });
        if (!res.ok) throw new Error('Gagal memuat histori sensor.');
        const data = await res.json();
        return data.map((row: any) => ({
            id: row.id,
            timestamp: row.created_at,
            temperature: row.sensor_dht22.temperature,
            humidity: row.sensor_dht22.humidity,
            mq135Raw: row.sensor_mq135.mq135,
            co: row.sensor_mq135.ppm_co,
            nh3: row.sensor_mq135.ppm_nh3,
            co2: row.sensor_mq135.ppm_co2,
            acetone: row.sensor_mq135.ppm_acetone
        }));
    }

    async getLatestClassification(deviceId: number, token: string): Promise<Classification | null> {
        const res = await fetch(`${API_BASE_URL}/classification/latest/${deviceId}`, { headers: this.getHeaders(token) });
        if (res.status === 404) return null;
        if (!res.ok) throw new Error('Gagal memuat klasifikasi.');
        const d = await res.json();
        return { id: d.id, status: d.label_status, createdAt: d.created_at };
    }

    async getHistoryClassification(deviceId: number, limit: number, token: string): Promise<Classification[]> {
        const res = await fetch(`${API_BASE_URL}/history/classification/${deviceId}?limit=${limit}`, { headers: this.getHeaders(token) });
        if (!res.ok) throw new Error('Gagal memuat riwayat klasifikasi.');
        const data = await res.json();
        return data.map((d: any) => ({
            id: d.id,
            status: d.label_status,
            createdAt: d.created_at
        }));
    }

    async triggerForecast(deviceId: number, token: string): Promise<ForecastPrediction> {
        const res = await fetch(`${API_BASE_URL}/forecast/day-ahead/${deviceId}`, {
            method: 'GET',
            headers: this.getHeaders(token)
        });
        if (!res.ok) {
            const errData = await res.json();
            throw new Error(errData.detail || 'Gagal memicu model forecasting.');
        }
        const d = await res.json();
        return {
            id: d.id,
            status: d.label_status,
            targetTime: d.target_time,
            targetDate: d.target_date,
            confidence: d.confidence,
            createdAt: d.created_at
        };
    }

    async createDevice(deviceName: string, userTargetId: number, token: string): Promise<Device> {
        // Menyesuaikan query param ?user_target_id=X sesuai endpoint FastAPI Anda
        const res = await fetch(`${API_BASE_URL}/devices?user_target_id=${userTargetId}`, {
            method: 'POST',
            headers: this.getHeaders(token), // Menggunakan Content-Type: application/json & Authorization Bearer
            body: JSON.stringify({
                device_name: deviceName,
                status_active: true // Nilai default awal saat alat dibuat
            }),
        });

        if (!res.ok) {
            const errData = await res.json();
            throw new Error(errData.detail || 'Gagal mendaftarkan perangkat baru.');
        }

        const d = await res.json();
        return {
            id: d.id,
            deviceName: d.device_name,
            userId: d.user_id,
            isActive: d.status_active
        };
    }

    async getAllUsers(token: string): Promise<UserDropdownEntity[]> {
        const res = await fetch(`${API_BASE_URL}/users`, { // 💡 Sesuaikan endpoint list user di FastAPI Anda
            method: 'GET',
            headers: this.getHeaders(token),
        });

        if (!res.ok) {
            const errData = await res.json();
            throw new Error(errData.detail || 'Gagal mengambil daftar pengguna.');
        }

        const data = await res.json();

        // Mapping response array dari FastAPI (biasanya memuat id dan username)
        return data.map((u: any) => ({
            id: u.id,
            username: u.username
        }));
    }

    async updateAdminStatus(targetUserId: number, isAdminStatus: boolean, token: string): Promise<{ message: string }> {
        // Menembak endpoint PATCH dengan query param ?is_admin=true/false
        const res = await fetch(`${API_BASE_URL}/users/${targetUserId}/admin-status?is_admin=${isAdminStatus}`, {
            method: 'PATCH',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            }
        });

        if (!res.ok) {
            const errData = await res.json();
            throw new Error(errData.detail || 'Gagal mengubah hak akses status admin pengguna.');
        }

        return await res.json(); // Mengembalikan response sukses dari FastAPI
    }
}
