import { useState, useEffect } from 'react';
import { AirQualityRepositoryImpl } from "@/src/data/repositories/AirQualityRepositoryImpl";
import { Device, SensorLog, Classification } from "@/src/domain/entities/AirQuality";

const repository = new AirQualityRepositoryImpl();

export function useAirQualityHistory() {
    const [devices, setDevices] = useState<Device[]>([]);
    const [selectedDeviceId, setSelectedDeviceId] = useState<number | null>(null);
    const [sensorHistory, setSensorHistory] = useState<SensorLog[]>([]);
    const [classHistory, setClassHistory] = useState<any[]>([]);
    const [metricClassHistory, setMetricClassHistory] = useState<any[]>([]);

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

    const fetchHistoryData = async (deviceId: number, limit: number) => {
        const token = localStorage.getItem('access_token') || '';
        if (!token) return;

        setLoading(true);
        setErrorMsg(null);
        try {
            const [sensorData, classData, metricData] = await Promise.all([
                repository.getSensorHistory(deviceId, limit, token),
                repository.getHistoryClassification(deviceId, limit, token),
                repository.getHistoryClassification(deviceId, 2000, token)
            ]);
            
            console.log("RAW classData[0]:", JSON.stringify(classData[0]));
            console.log("RAW sensorData[0]:", JSON.stringify(sensorData[0]));
            console.log("Keys classData[0]:", classData[0] ? Object.keys(classData[0]) : 'EMPTY');

            setSensorHistory(sensorData);
            // Simpan raw response tanpa mapping agar field asli (label_status, conclusion_feature_id) tetap ada
            setClassHistory(classData);
            setMetricClassHistory(metricData);
        } catch (err: any) {
            console.error("Error fetchHistoryData:", err);
            setErrorMsg("Gagal memuat rentang histori data pipeline.");
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        if (selectedDeviceId) {
            fetchHistoryData(selectedDeviceId, dataLimit);
        }
    }, [selectedDeviceId, dataLimit]);

    const handleRefresh = async () => {
        if (selectedDeviceId) {
            await fetchHistoryData(selectedDeviceId, dataLimit);
        }
    };

    // Hitung distribusi dari metricClassHistory (data masif 2000 baris)
    // Handle semua kemungkinan field name: label_status (raw API) atau status (setelah mapping repo)
    const countStatusDistribution = (status: "Good" | "Moderate" | "Bad") => {
        return metricClassHistory.filter(item => {
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