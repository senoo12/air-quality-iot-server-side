'use client';

import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { Device } from "@/src/domain/entities/AirQuality";

interface SidebarProps {
    devices?: Device[];
    selectedDeviceId?: number | null;
    onSelectDevice?: (id: number) => void;
    showDeviceSelector?: boolean;
}

export default function Sidebar({
    devices = [],
    selectedDeviceId = null,
    onSelectDevice,
    showDeviceSelector = true
}: SidebarProps) {
    const pathname = usePathname();
    const [isAdmin, setIsAdmin] = useState<boolean>(false);

    // 💡 SINKRONISASI JWT: Membaca status admin dari localStorage saat komponen dimuat
    useEffect(() => {
        const token = localStorage.getItem('access_token');
        if (token) {
            try {
                // Decode bagian payload JWT (indeks ke-1 setelah pemisah titik)
                const base64Url = token.split('.')[1];
                const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
                const jsonPayload = decodeURIComponent(
                    window.atob(base64)
                        .split('')
                        .map((c) => '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2))
                        .join('')
                );

                const payload = JSON.parse(jsonPayload);
                console.log("🔍 [DEBUG SIDEBAR JWT PAYLOAD]:", payload);
                // Menyesuaikan klaim 'is_admin' dari payload token FastAPI Anda
                if (payload && (payload.is_admin === true || payload.is_admin === 'true')) {
                    setIsAdmin(true);
                }
            } catch (error) {
                console.error("Gagal membaca payload akses token admin:", error);
            }
        }
    }, []);

    // FUNGSI LOGOUT: Menghapus token dari memori browser
    const handleLogout = () => {
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        // Alihkan paksa ke halaman login
        window.location.href = '/login';
    };

    return (
        <aside className="w-64 bg-slate-900 text-slate-100 flex flex-col min-h-screen border-r border-slate-800 shrink-0 justify-between">
            {/* BAGIAN ATAS MENU */}
            <div className="flex-1 flex flex-col">
                <div className="p-6 border-b border-slate-800">
                    <h1 className="text-xl font-bold tracking-wider flex items-center gap-2">🌬️ EcoAir IoT</h1>
                    <p className="text-xs text-slate-400 mt-1">Clean Architecture Layout</p>
                </div>

                <nav className="p-4 space-y-6">
                    <div>
                        <span className="px-3 text-xs font-semibold text-slate-400 uppercase tracking-wider block mb-2">Menu</span>
                        <div className="space-y-1">
                            <Link
                                href="/dashboard"
                                className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all ${pathname === '/' ? 'bg-slate-800 text-white border-l-4 border-emerald-500 rounded-l-none' : 'text-slate-400 hover:bg-slate-800/50 hover:text-white'}`}
                            >
                                📊 Dasbor Real-Time
                            </Link>
                            <Link
                                href="/history"
                                className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all ${pathname === '/history' ? 'bg-slate-800 text-white border-l-4 border-emerald-500 rounded-l-none' : 'text-slate-400 hover:bg-slate-800/50 hover:text-white'}`}
                            >
                                📜 Riwayat & Analytics
                            </Link>
                        </div>
                    </div>

                    {/* 💡 MENU KONDISIONAL: Hanya muncul jika user adalah Admin (is_admin == true) */}
                    {isAdmin && (
                        <div>
                            <span className="px-3 text-xs font-semibold text-amber-400 uppercase tracking-wider block mb-2">Panel Administrator</span>
                            <div className="space-y-1">
                                <Link
                                    href="/admin/add-device"
                                    className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all ${pathname === '/admin/add-device' ? 'bg-slate-800 text-amber-400 border-l-4 border-amber-500 rounded-l-none' : 'text-slate-400 hover:bg-slate-800/50 hover:text-amber-300'}`}
                                >
                                    🛠️ Registrasi Alat Baru
                                </Link>
                            </div>
                        </div>
                    )}

                    {showDeviceSelector && (
                        <div>
                            <span className="px-3 text-xs font-semibold text-slate-400 uppercase tracking-wider block mb-2">Perangkat IoT</span>
                            <div className="space-y-1 max-h-40 overflow-y-auto">
                                {devices.map((device) => (
                                    <button
                                        key={device.id}
                                        onClick={() => onSelectDevice && onSelectDevice(device.id)}
                                        className={`w-full text-left px-3 py-2 rounded-lg text-xs font-medium transition-all flex items-center justify-between ${selectedDeviceId === device.id ? 'bg-emerald-600 text-white shadow-md' : 'text-slate-400 hover:bg-slate-800 hover:text-white'}`}
                                    >
                                        <span>{device.deviceName}</span>
                                        <span className="text-[10px] bg-slate-800 px-1.5 py-0.5 rounded text-slate-400">ID: {device.id}</span>
                                    </button>
                                ))}
                            </div>
                        </div>
                    )}
                </nav>
            </div>

            {/* BAGIAN BAWAH: TOMBOL LOGOUT INTERAKTIF */}
            <div className="p-4 border-t border-slate-800 space-y-3 bg-slate-950/20">
                <button
                    onClick={handleLogout}
                    className="w-full text-left px-3 py-2 rounded-lg text-xs font-medium text-rose-400 hover:bg-rose-950/30 hover:text-rose-300 transition-all flex items-center gap-2"
                >
                    🚪 Keluar dari Akun (Logout)
                </button>
                <div className="text-[10px] text-slate-600 text-center">Clean Arch Frontend</div>
            </div>
        </aside>
    );
}