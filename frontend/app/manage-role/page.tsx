'use client';

import React from 'react';
import Sidebar from '@/src/presentation/components/Sidebar';
import { useManageAdmin } from '@/src/presentation/hooks/useManageAdmin';

export default function ManageRolePage() {
    const {
        targetUserId,
        setTargetUserId,
        isAdminStatus,
        setIsAdminStatus,
        usersList = [],
        loadingUsers,
        loading,
        errorMsg,
        successMsg,
        handleUpdateStatus
    } = useManageAdmin();

    return (
        <div className="flex bg-slate-50 min-h-screen text-slate-800">
            <Sidebar showDeviceSelector={false} />

            <main className="flex-1 p-8 max-w-2xl mx-auto w-full self-center">
                <div className="bg-white p-8 rounded-2xl border border-slate-200 shadow-xl">

                    {/* HEADER */}
                    <div className="mb-6 border-b border-slate-100 pb-4">
                        <h2 className="text-xl font-black text-slate-900 tracking-tight flex items-center gap-2">
                            👑 Kontrol Otoritas Pengguna (Superuser)
                        </h2>
                        <p className="text-xs text-slate-400 mt-1">
                            Mengubah, mengangkat, atau mencabut hak eksklusif status administrator perangkat lingkungan makro.
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

                    {/* FORM CONTROL */}
                    <form onSubmit={handleUpdateStatus} className="space-y-4">
                        {/* SELECT USER TARGET */}
                        <div>
                            <label className="block text-xs font-bold text-slate-500 uppercase tracking-wider mb-1.5">
                                Pilih Pengguna Target
                            </label>
                            <div className="relative">
                                <select
                                    value={targetUserId}
                                    onChange={(e) => setTargetUserId(e.target.value)}
                                    className="w-full px-4 py-3 bg-slate-50 border border-slate-200 rounded-xl text-sm font-medium focus:outline-none focus:border-rose-500 appearance-none cursor-pointer disabled:bg-slate-100"
                                    disabled={loading || loadingUsers}
                                >
                                    <option value="">
                                        {loadingUsers ? "⏳ Memuat data user..." : "👤 -- Pilih Akun Target --"}
                                    </option>
                                    {usersList.map((user) => (
                                        <option key={user.id} value={user.id}>
                                            {user.username} (ID: {user.id})
                                        </option>
                                    ))}
                                </select>
                                <div className="pointer-events-none absolute inset-y-0 right-0 flex items-center px-4 text-slate-400 text-xs">▼</div>
                            </div>
                        </div>

                        {/* SELECT STATUS TARGET */}
                        <div>
                            <label className="block text-xs font-bold text-slate-500 uppercase tracking-wider mb-1.5">
                                Set Tingkatan Otoritas
                            </label>
                            <div className="relative">
                                <select
                                    value={isAdminStatus}
                                    onChange={(e) => setIsAdminStatus(e.target.value)}
                                    className="w-full px-4 py-3 bg-slate-50 border border-slate-200 rounded-xl text-sm font-medium focus:outline-none focus:border-rose-500 appearance-none cursor-pointer"
                                    disabled={loading}
                                >
                                    <option value="true">🛠️ Angkat Menjadi Administrator</option>
                                    <option value="false">👤 Turunkan Menjadi User Biasa</option>
                                </select>
                                <div className="pointer-events-none absolute inset-y-0 right-0 flex items-center px-4 text-slate-400 text-xs">▼</div>
                            </div>
                        </div>

                        {/* SUBMIT BUTTON */}
                        <button
                            type="submit"
                            disabled={loading || loadingUsers}
                            className={`w-full py-3.5 mt-2 rounded-xl font-bold text-sm text-white shadow-md transition-all ${loading || loadingUsers
                                    ? 'bg-slate-300 cursor-not-allowed'
                                    : 'bg-rose-600 hover:bg-rose-700 active:scale-[0.99]'
                                }`}
                        >
                            {loading ? 'Memperbarui Otoritas Sesi...' : '🔒 Eksekusi Perubahan Otoritas'}
                        </button>
                    </form>

                </div>
            </main>
        </div>
    );
}