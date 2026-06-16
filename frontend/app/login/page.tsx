'use client';

import React from 'react';
import { useAuth } from '@/src/presentation/hooks/useAuth';

export default function LoginPage() {
    const {
        username,
        setUsername,
        password,
        setPassword,
        loading,
        errorMsg,
        handleLogin,
    } = useAuth();

    return (
        <div className="min-h-screen bg-slate-950 flex flex-col justify-center py-12 sm:px-6 lg:px-8 font-sans">
            <div className="sm:mx-auto w-full max-w-md text-center">
                <span className="text-4xl">表达🌬️</span>
                <h2 className="mt-4 text-center text-3xl font-black tracking-tight text-white">
                    EcoAir IoT Portal
                </h2>
                <p className="mt-2 text-center text-sm text-slate-400">
                    Sistem Monitoring & Peramalan Kualitas Udara
                </p>
            </div>

            <div className="mt-8 sm:mx-auto w-full max-w-md">
                <div className="bg-slate-900 py-8 px-4 shadow-xl border border-slate-800 rounded-2xl sm:px-10">

                    {errorMsg && (
                        <div className="mb-4 p-3.5 bg-rose-950/40 border border-rose-800 text-rose-400 text-xs rounded-xl shadow-inner font-medium">
                            ⚠️ {errorMsg}
                        </div>
                    )}

                    <form className="space-y-6" onSubmit={handleLogin}>
                        <div>
                            <label htmlFor="username" className="block text-xs font-semibold text-slate-400 uppercase tracking-wider">
                                Username
                            </label>
                            <div className="mt-2">
                                <input
                                    id="username"
                                    name="username"
                                    type="text"
                                    required
                                    value={username}
                                    onChange={(e) => setUsername(e.target.value)}
                                    className="block w-full rounded-xl border-0 bg-slate-950 py-3 px-4 text-white shadow-sm ring-1 ring-inset ring-slate-800 placeholder:text-slate-600 focus:ring-2 focus:ring-inset focus:ring-emerald-500 sm:text-sm focus:outline-none transition-all"
                                    placeholder="Masukkan username Anda"
                                />
                            </div>
                        </div>

                        <div>
                            <label htmlFor="password" className="block text-xs font-semibold text-slate-400 uppercase tracking-wider">
                                Password
                            </label>
                            <div className="mt-2">
                                <input
                                    id="password"
                                    name="password"
                                    type="password"
                                    required
                                    value={password}
                                    onChange={(e) => setPassword(e.target.value)}
                                    className="block w-full rounded-xl border-0 bg-slate-950 py-3 px-4 text-white shadow-sm ring-1 ring-inset ring-slate-800 placeholder:text-slate-600 focus:ring-2 focus:ring-inset focus:ring-emerald-500 sm:text-sm focus:outline-none transition-all"
                                    placeholder="••••••••"
                                />
                            </div>
                        </div>

                        <div>
                            <button
                                type="submit"
                                disabled={loading}
                                className={`w-full flex justify-center py-3 px-4 border border-transparent rounded-xl shadow-lg font-bold text-sm text-white transition-all ${loading
                                        ? 'bg-slate-700 cursor-not-allowed'
                                        : 'bg-emerald-600 hover:bg-emerald-500 active:scale-98 shadow-emerald-900/20'
                                    }`}
                            >
                                {loading ? 'Memvalidasi Kredensial...' : 'Masuk ke Dasboard'}
                            </button>
                        </div>
                    </form>
                </div>
            </div>
        </div>
    );
}