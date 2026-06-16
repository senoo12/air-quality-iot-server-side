'use client';

import React from 'react';
import Link from 'next/link';
import { useRegister } from '@/src/presentation/hooks/useRegister';

export default function RegisterPage() {
    const {
        username,
        setUsername,
        email,
        setEmail,
        password,
        setPassword,
        confirmPassword,
        setConfirmPassword,
        loading,
        errorMsg,
        successMsg,
        handleRegister
    } = useRegister();

    return (
        <div className="min-h-screen bg-slate-900 flex flex-col justify-center items-center p-4">
            <div className="w-full max-w-md bg-white p-8 rounded-2xl border border-slate-200 shadow-2xl">

                {/* LOGO & TITLE */}
                <div className="text-center mb-6">
                    <h1 className="text-2xl font-black text-slate-900 tracking-wider">Air Quality IoT STI</h1>
                    <p className="text-xs text-slate-400 mt-1">Buat akun baru untuk memantau kualitas udara</p>
                </div>

                {/* NOTIFIKASI STATUS */}
                {errorMsg && (
                    <div className="mb-4 p-3 bg-rose-50 border border-rose-200 text-rose-700 rounded-xl text-xs font-medium">
                        ⚠️ {errorMsg}
                    </div>
                )}
                {successMsg && (
                    <div className="mb-4 p-3 bg-emerald-50 border border-emerald-200 text-emerald-700 rounded-xl text-xs font-semibold">
                        {successMsg}
                    </div>
                )}

                {/* FORM INPUT */}
                <form onSubmit={handleRegister} className="space-y-4">
                    <div>
                        <label className="block text-[10px] font-bold text-slate-500 uppercase tracking-wider mb-1">
                            Username
                        </label>
                        <input
                            type="text"
                            placeholder="Masukkan username baru"
                            value={username}
                            onChange={(e) => setUsername(e.target.value)}
                            className="w-full px-4 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-sm font-medium focus:outline-none focus:border-emerald-500 text-slate-800 transition-colors"
                            disabled={loading}
                        />
                    </div>

                    <div>
                        <label className="block text-[10px] font-bold text-slate-500 uppercase tracking-wider mb-1">
                            Alamat Email
                        </label>
                        <input
                            type="email"
                            placeholder="contoh@domain.com"
                            value={email}
                            onChange={(e) => setEmail(e.target.value)}
                            className="w-full px-4 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-sm font-medium focus:outline-none focus:border-emerald-500 text-slate-800 transition-colors"
                            disabled={loading}
                        />
                    </div>

                    <div>
                        <label className="block text-[10px] font-bold text-slate-500 uppercase tracking-wider mb-1">
                            Password
                        </label>
                        <input
                            type="password"
                            placeholder="••••••••"
                            value={password}
                            onChange={(e) => setPassword(e.target.value)}
                            className="w-full px-4 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-sm font-medium focus:outline-none focus:border-emerald-500 text-slate-800 transition-colors"
                            disabled={loading}
                        />
                    </div>

                    <div>
                        <label className="block text-[10px] font-bold text-slate-500 uppercase tracking-wider mb-1">
                            Konfirmasi Password
                        </label>
                        <input
                            type="password"
                            placeholder="••••••••"
                            value={confirmPassword}
                            onChange={(e) => setConfirmPassword(e.target.value)}
                            className="w-full px-4 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-sm font-medium focus:outline-none focus:border-emerald-500 text-slate-800 transition-colors"
                            disabled={loading}
                        />
                    </div>

                    <button
                        type="submit"
                        disabled={loading}
                        className={`w-full py-3 rounded-xl font-bold text-sm text-white shadow-md transition-all ${loading
                                ? 'bg-slate-300 cursor-not-allowed'
                                : 'bg-slate-900 hover:bg-slate-800 active:scale-[0.99]'
                            }`}
                    >
                        {loading ? 'Memproses Pendaftaran...' : '📝 Daftar Akun Baru'}
                    </button>
                </form>

                {/* PENGALIHAN KE LOGIN */}
                <div className="text-center mt-6 pt-4 border-t border-slate-100">
                    <p className="text-xs text-slate-400">
                        Sudah punya akun EcoAir?{' '}
                        <Link href="/login" className="text-emerald-600 font-bold hover:underline">
                            Masuk Sekarang
                        </Link>
                    </p>
                </div>

            </div>
        </div>
    );
}