import { useState, useEffect } from 'react';
import { AirQualityRepositoryImpl } from "@/src/data/repositories/AirQualityRepositoryImpl";
import { Device, SensorLog, Classification, ForecastPrediction } from "@/src/domain/entities/AirQuality";

const repository = new AirQualityRepositoryImpl();
const JWT_TOKEN = typeof window !== 'undefined' ? localStorage.getItem('access_token') || '' : '';

export function useAirQuality() {
    const [devices, setDevices] = useState<Device[]>([]);
    const [selectedDeviceId, setSelectedDeviceId] = useState<number | null>(null);
    const [latestSensor, setLatestSensor] = useState<SensorLog | null>(null);
    const [latestClass, setLatestClass] = useState<Classification | null>(null);
    const [forecast, setForecast] = useState<ForecastPrediction | null>(null);

    const [loading, setLoading] = useState<boolean>(false);
    const [loadingForecast, setLoadingForecast] = useState<boolean>(false);
    const [loadingToggle, setLoadingToggle] = useState<boolean>(false); // 💡 Loading khusus sakelar
    const [errorMsg, setErrorMsg] = useState<string | null>(null);

    useEffect(() => {
        if (!JWT_TOKEN) return;
        repository.getDevices(JWT_TOKEN)
            .then((data) => {
                setDevices(data);
                if (data.length > 0) setSelectedDeviceId(data[0].id);
            })
            .catch((err) => setErrorMsg(err.message));
    }, []);

    // Ambil data device aktif saat ini berdasarkan ID terpilih
    const currentDevice = devices.find(d => d.id === selectedDeviceId) || null;

    // 💡 FUNGSI BARU: Mengubah status ON/OFF ESP32
    const handleTogglePower = async () => {
        if (!selectedDeviceId || !currentDevice) return;

        setLoadingToggle(true);
        setErrorMsg(null);

        const targetStatus = !currentDevice.isActive; // Balik status saat ini

        try {
            const updatedDevice = await repository.toggleDeviceStatus(selectedDeviceId, targetStatus, JWT_TOKEN);

            // Perbarui state array devices lokal agar UI langsung berubah warna sakelarnya
            setDevices(prev => prev.map(d => d.id === selectedDeviceId ? updatedDevice : d));
        } catch (err: any) {
            setErrorMsg(err.message);
        } finally {
            setLoadingToggle(false);
        }
    };

    const fetchLatestDashboardData = async (deviceId: number) => {
        setLoading(true);
        setErrorMsg(null);
        try {
            const [sensorData, currentClass] = await Promise.all([
                repository.getSensorHistory(deviceId, 1, JWT_TOKEN),
                repository.getLatestClassification(deviceId, JWT_TOKEN)
            ]);
            setLatestSensor(sensorData.length > 0 ? sensorData[0] : null);
            setLatestClass(currentClass);
        } catch (err: any) {
            setErrorMsg(err.message);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        if (selectedDeviceId) {
            setForecast(null);
            fetchLatestDashboardData(selectedDeviceId);
        }
    }, [selectedDeviceId]);

    const handleRefresh = async () => {
        if (selectedDeviceId) await fetchLatestDashboardData(selectedDeviceId);
    };

    const executeForecasting = async () => {
        if (!selectedDeviceId) return;
        setLoadingForecast(true);
        setErrorMsg(null);
        try {
            const result = await repository.triggerForecast(selectedDeviceId, JWT_TOKEN);
            setForecast(result);
        } catch (err: any) {
            setErrorMsg(err.message);
        } finally {
            setLoadingForecast(false);
        }
    };

    return {
        devices,
        selectedDeviceId,
        setSelectedDeviceId,
        currentDevice, // 💡 Keluarkan objek device terpilih saat ini
        latestSensor,
        latestClass,
        forecast,
        loading,
        loadingForecast,
        loadingToggle, // 💡 Keluarkan status loading toggle
        errorMsg,
        executeForecasting,
        handleRefresh,
        handleTogglePower // 💡 Keluarkan fungsi sakelar untuk UI tombol
    };
}