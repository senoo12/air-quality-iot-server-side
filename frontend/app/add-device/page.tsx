'use client';

import React, { useEffect, useState } from 'react';
import Sidebar from '@/src/presentation/components/Sidebar';
import { useAddDevice } from '@/src/presentation/hooks/useAddDevice';
import { AirQualityRepositoryImpl } from "@/src/data/repositories/AirQualityRepositoryImpl";
import { Device } from "@/src/domain/entities/AirQuality";

const airQualityRepository = new AirQualityRepositoryImpl();

export default function AddDevicePage() {
    const {
        deviceName,
        setDeviceName,
        userTargetId,
        setUserTargetId,
        usersList = [],
        loadingUsers,
        loading,
        errorMsg,
        successMsg,
        handleCreateDevice
    } = useAddDevice();

    // 💡 SINKRONISASI DAFTAR ALAT (STATE LOKAL)
    const [devices, setDevices] = useState<Device[]>([]);
    const [selectedDeviceId, setSelectedDeviceId] = useState<number | null>(null);

    // Fetch daftar device milik admin/user aktif saat halaman dibuka
    useEffect(() => {
        const fetchUserDevices = async () => {
            const token = localStorage.getItem('access_token') || '';
            if (!token) return;

            try {
                const data = await airQualityRepository.getDevices(token);
                setDevices(data);
                if (data.length > 0) {
                    setSelectedDeviceId(data[0].id); // Default select device pertama
                }
            } catch (error) {
                console.error("Gagal memuat daftar perangkat di sidebar:", error);
            }
        };

        fetchUserDevices();
    }, [successMsg]); // 💡 Mengambil ulang data otomatis jika baru saja sukses mendaftarkan alat baru

    return (
        <div className="flex bg-slate-50 min-h-screen text-slate-800">

            {/* 💡 SEKARANG DIUMPAN SECARA DINAMIS */}
            <Sidebar
                showDeviceSelector={true}
                devices={devices}
                selectedDeviceId={selectedDeviceId}
                onSelectDevice={(id) => setSelectedDeviceId(id)}
            />

            <main className="flex-1 p-8 max-w-2xl mx-auto w-full self-center">
                <div className="bg-white p-8 rounded-2xl border border-slate-200 shadow-xl">

                    {/* HEADER */}
                    <div className="mb-6 border-b border-slate-100 pb-4">
                        <h2 className="text-xl font-black text-slate-900 tracking-tight flex items-center gap-2">
                            🛠️ Panel Registrasi Perangkat IoT
                        </h2>
                        <p className="text-xs text-slate-400 mt-1">
                            Khusus hak akses Administrator. Daftarkan modul ESP32/Wokwi ke akun pengguna secara akurat.
                        </p>
                    </div>

                    {/* NOTIFIKASI */}
                    {errorMsg && (
                        <div className="mb-4 p-3.5 bg-rose-50 border border-rose-200 text-rose-700 rounded-xl text-xs font-medium">
                            ⚠️ {errorMsg}
                        </div>
                    )}
                    {successMsg && (
                        <div className="mb-4 p-3.5 bg-emerald-50 border border-emerald-200 text-emerald-700 rounded-xl text-xs font-semibold">
                            {successMsg}
                        </div>
                    )}

                    {/* FORM INPUT */}
                    <form onSubmit={handleCreateDevice} className="space-y-4">
                        {/* INPUT 1: NAMA PERANGKAT */}
                        <div>
                            <label className="block text-xs font-bold text-slate-500 uppercase tracking-wider mb-1.5">
                                Nama Perangkat IoT
                            </label>
                            <input
                                type="text"
                                placeholder="Contoh: device-sti-o1"
                                value={deviceName}
                                onChange={(e) => setDeviceName(e.target.value)}
                                className="w-full px-4 py-3 bg-slate-50 border border-slate-200 rounded-xl text-sm font-medium focus:outline-none focus:border-amber-500 transition-colors"
                                disabled={loading}
                            />
                        </div>

                        {/* INPUT 2: DROPDOWN SELECT TARGET USER */}
                        <div>
                            <label className="block text-xs font-bold text-slate-500 uppercase tracking-wider mb-1.5">
                                Target Pemilik Perangkat (User)
                            </label>
                            <div className="relative">
                                <select
                                    value={userTargetId}
                                    onChange={(e) => setUserTargetId(e.target.value)}
                                    className="w-full px-4 py-3 bg-slate-50 border border-slate-200 rounded-xl text-sm font-medium focus:outline-none focus:border-amber-500 transition-colors appearance-none cursor-pointer disabled:bg-slate-100 disabled:cursor-not-allowed"
                                    disabled={loading || loadingUsers}
                                >
                                    <option value="">
                                        {loadingUsers ? "⏳ Memuat daftar pengguna..." : "👤 -- Pilih Username Target --"}
                                    </option>

                                    {usersList.map((user) => (
                                        <option key={user.id} value={user.id}>
                                            {user.username} (ID: {user.id})
                                        </option>
                                    ))}
                                </select>

                                <div className="pointer-events-none absolute inset-y-0 right-0 flex items-center px-4 text-slate-400 text-xs">
                                    ▼
                                </div>
                            </div>
                        </div>

                        {/* TOMBOL SUBMIT */}
                        <button
                            type="submit"
                            disabled={loading || loadingUsers}
                            className={`w-full py-3.5 mt-2 rounded-xl font-bold text-sm text-white shadow-md transition-all ${loading || loadingUsers
                                ? 'bg-slate-300 cursor-not-allowed'
                                : 'bg-amber-500 hover:bg-amber-600 active:scale-[0.99]'
                                }`}
                        >
                            {loading ? 'Mendaftarkan Perangkat...' : '📥 Daftarkan Alat Baru'}
                        </button>
                    </form>

                </div>
            </main>
        </div>
    );
}