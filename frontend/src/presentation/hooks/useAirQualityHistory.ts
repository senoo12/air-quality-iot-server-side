import { useState, useEffect } from 'react';
import { AirQualityRepositoryImpl } from "@/src/data/repositories/AirQualityRepositoryImpl";
import { Device, SensorLog, Classification } from "@/src/domain/entities/AirQuality";

const repository = new AirQualityRepositoryImpl();

export function useAirQualityHistory() {
    const [devices, setDevices] = useState<Device[]>([]);
    const [selectedDeviceId, setSelectedDeviceId] = useState<number | null>(null);
    const [sensorHistory, setSensorHistory] = useState<SensorLog[]>([]);
    const [classHistory, setClassHistory] = useState<any[]>([]);

    const [dataLimit, setDataLimit] = useState<number>(50);
    const [loading, setLoading] = useState<boolean>(false);
    const [errorMsg, setErrorMsg] = useState<string | null>(null);

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

    const fetchAllData = async (deviceId: number) => {
        const token = localStorage.getItem('access_token') || '';
        if (!token) return;

        setLoading(true);
        setErrorMsg(null);
        try {
            // Ambil seluruh data secara dinamis dari DB (limit = null) tanpa hardcode
            const [sensorData, classData] = await Promise.all([
                repository.getSensorHistory(deviceId, null, token),
                repository.getHistoryClassification(deviceId, null, token)
            ]);

            setSensorHistory(sensorData);
            setClassHistory(classData);
        } catch (err: any) {
            console.error("Error fetchAllData:", err);
            setErrorMsg("Gagal memuat rentang histori data pipeline.");
        } finally {
            setLoading(false);
        }
    };

    // Pemicu saat Device berubah
    useEffect(() => {
        if (selectedDeviceId) {
            fetchAllData(selectedDeviceId);
        }
    }, [selectedDeviceId]);

    const handleRefresh = async () => {
        if (selectedDeviceId) {
            await fetchAllData(selectedDeviceId);
        }
    };

    // Hitung distribusi dari classHistory (seluruh data dinamis dari DB)
    const countStatusDistribution = (status: "Good" | "Moderate" | "Bad") => {
        return classHistory.filter(item => {
            const s: string = item.label_status ?? item.status ?? '';
            return s.toLowerCase() === status.toLowerCase();
        }).length;
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
        handleRefresh
    };
}