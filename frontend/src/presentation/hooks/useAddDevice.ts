import { useState, useEffect } from 'react';
import { AirQualityRepositoryImpl } from "@/src/data/repositories/AirQualityRepositoryImpl";
import { UserDropdownEntity } from "@/src/domain/usecases/AirQualityRepository";

const repository = new AirQualityRepositoryImpl();

export function useAddDevice() {
    const [deviceName, setDeviceName] = useState<string>('');
    const [userTargetId, setUserTargetId] = useState<string>('');
    const [usersList, setUsersList] = useState<UserDropdownEntity[]>([]); // 💡 State simpan daftar user
    const [loading, setLoading] = useState<boolean>(false);
    const [loadingUsers, setLoadingUsers] = useState<boolean>(false);
    const [errorMsg, setErrorMsg] = useState<string | null>(null);
    const [successMsg, setSuccessMsg] = useState<string | null>(null);

    // 💡 Ambil daftar user dari backend untuk kebutuhan Dropdown Select
    useEffect(() => {
        const fetchUsers = async () => {
            const token = localStorage.getItem('access_token') || '';
            if (!token) return;

            setLoadingUsers(true);
            try {
                const list = await repository.getAllUsers(token);
                setUsersList(list);
            } catch (err: any) {
                console.error("Gagal memuat list user untuk select:", err.message);
            } finally {
                setLoadingUsers(false);
            }
        };

        fetchUsers();
    }, []);

    const handleCreateDevice = async (e: React.FormEvent) => {
        e.preventDefault();
        const token = localStorage.getItem('access_token') || '';

        if (!token) {
            setErrorMsg("Sesi Anda habis, silakan login kembali.");
            return;
        }

        if (!deviceName.trim() || !userTargetId) {
            setErrorMsg("Semua kolom input termasuk target user wajib dipilih.");
            return;
        }

        setLoading(true);
        setErrorMsg(null);
        setSuccessMsg(null);

        try {
            await repository.createDevice(deviceName, Number(userTargetId), token);

            setSuccessMsg(`🚀 Perangkat "${deviceName}" Berhasil Didaftarkan!`);
            setDeviceName('');
            setUserTargetId(''); // Reset select dropdown
        } catch (err: any) {
            setErrorMsg(err.message);
        } finally {
            setLoading(false);
        }
    };

    return {
        deviceName,
        setDeviceName,
        userTargetId,
        setUserTargetId,
        usersList,       // 💡 Diekspos ke UI View
        loadingUsers,    // 💡 Indikator loading data select
        loading,
        errorMsg,
        successMsg,
        handleCreateDevice
    };
}