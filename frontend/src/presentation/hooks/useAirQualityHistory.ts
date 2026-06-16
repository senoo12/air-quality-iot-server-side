import { useState, useEffect } from 'react';
import { AirQualityRepositoryImpl } from "@/src/data/repositories/AirQualityRepositoryImpl";
import { Device, SensorLog, Classification } from "@/src/domain/entities/AirQuality";

const repository = new AirQualityRepositoryImpl();

export function useAirQualityHistory() {
    const [devices, setDevices] = useState<Device[]>([]);
    const [selectedDeviceId, setSelectedDeviceId] = useState<number | null>(null);
    const [sensorHistory, setSensorHistory] = useState<SensorLog[]>([]);
    const [classHistory, setClassHistory] = useState<Classification[]>([]);

    const [dataLimit, setDataLimit] = useState<number>(50);
    const [loading, setLoading] = useState<boolean>(false);
    const [errorMsg, setErrorMsg] = useState<string | null>(null);

    // 1. Ambil daftar perangkat secara aman
    useEffect(() => {
        const token = localStorage.getItem('access_token') || '';
        if (!token) {
            setErrorMsg("Sesi masuk Anda telah habis. Silakan login kembali.");
            return;
        }

        repository.getDevices(token)
            .then((data) => {
                setDevices(data);
                if (data.length > 0) setSelectedDeviceId(data[0].id);
            })
            .catch((err) => {
                console.error("Error getDevices:", err);
                setErrorMsg("Gagal mengambil daftar perangkat dari server VM.");
            });
    }, []);

    // 2. Fungsi utama untuk mengambil data sekuensial dari API
    const fetchHistoryData = async (deviceId: number, limit: number) => {
        const token = localStorage.getItem('access_token') || '';
        if (!token) return;

        setLoading(true);
        setErrorMsg(null);
        try {
            const [sensorData, classData] = await Promise.all([
                repository.getSensorHistory(deviceId, limit, token),
                repository.getHistoryClassification(deviceId, limit, token)
            ]);
            setSensorHistory(sensorData);
            setClassHistory(classData);
        } catch (err: any) {
            console.error("Error fetchHistoryData:", err);
            setErrorMsg("Gagal memuat rentang histori data pipeline.");
        } finally { // ✅ PERBAIKAN: Diubah menjadi 'finally'
            setLoading(false);
        }
    };

    useEffect(() => {
        if (selectedDeviceId) {
            fetchHistoryData(selectedDeviceId, dataLimit);
        }
    }, [selectedDeviceId, dataLimit]);

    // 💡 FUNGSI BARU: Untuk memicu refresh manual dari tombol UI
    const handleRefresh = async () => {
        if (selectedDeviceId) {
            await fetchHistoryData(selectedDeviceId, dataLimit);
        }
    };

    const countStatusDistribution = (status: "Good" | "Moderate" | "Bad") => {
        return classHistory.filter(item => item.status === status).length;
    };

    return {
        devices,
        selectedDeviceId,
        setSelectedDeviceId,
        sensorHistory,
        classHistory,
        dataLimit,
        setDataLimit,
        loading,
        errorMsg,
        countStatusDistribution,
        handleRefresh // 💡 Ekstrak fungsi ini ke lapisan UI
    };
}