import { useState, useEffect } from 'react';
import { AirQualityRepositoryImpl } from "@/src/data/repositories/AirQualityRepositoryImpl";
import { UserDropdownEntity } from "@/src/domain/usecases/AirQualityRepository";

const repository = new AirQualityRepositoryImpl();

export function useManageAdmin() {
    const [targetUserId, setTargetUserId] = useState<string>('');
    const [isAdminStatus, setIsAdminStatus] = useState<string>('true'); // Default set ke true (Jadikan Admin)
    const [usersList, setUsersList] = useState<UserDropdownEntity[]>([]);
    const [loading, setLoading] = useState<boolean>(false);
    const [loadingUsers, setLoadingUsers] = useState<boolean>(false);
    const [errorMsg, setErrorMsg] = useState<string | null>(null);
    const [successMsg, setSuccessMsg] = useState<string | null>(null);

    const fetchUsers = async () => {
        const token = localStorage.getItem('access_token') || '';
        if (!token) return;
        setLoadingUsers(true);
        try {
            const list = await repository.getAllUsers(token);
            setUsersList(list);
        } catch (err: any) {
            console.error(err.message);
        } finally {
            setLoadingUsers(false);
        }
    };

    useEffect(() => {
        fetchUsers();
    }, []);

    const handleUpdateStatus = async (e: React.FormEvent) => {
        e.preventDefault();
        const token = localStorage.getItem('access_token') || '';

        if (!targetUserId) {
            setErrorMsg("Silakan pilih user target terlebih dahulu.");
            return;
        }

        setLoading(true);
        setErrorMsg(null);
        setSuccessMsg(null);

        try {
            const statusBool = isAdminStatus === 'true';
            await repository.updateAdminStatus(Number(targetUserId), statusBool, token);

            setSuccessMsg(`✅ Hak akses User ID ${targetUserId} berhasil diperbarui menjadi ${statusBool ? 'ADMIN' : 'USER BIASA'}!`);
            setTargetUserId('');
        } catch (err: any) {
            setErrorMsg(err.message);
        } finally {
            setLoading(false);
        }
    };

    return {
        targetUserId,
        setTargetUserId,
        isAdminStatus,
        setIsAdminStatus,
        usersList,
        loadingUsers,
        loading,
        errorMsg,
        successMsg,
        handleUpdateStatus
    };
}