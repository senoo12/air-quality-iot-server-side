'use client';

import React, { useState, useMemo } from 'react';
import Sidebar from '@/src/presentation/components/Sidebar';
import { useAirQualityHistory } from '@/src/presentation/hooks/useAirQualityHistory';

export default function HistoryPage() {
    const {
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
    } = useAirQualityHistory();

    const [labelFilter, setLabelFilter] = useState<string>('All');

    const getLabelBadgeColor = (label: string) => {
        if (label === 'Good') return 'bg-emerald-100 text-emerald-800 border-emerald-200';
        if (label === 'Moderate') return 'bg-amber-100 text-amber-800 border-amber-200';
        if (label === 'Bad') return 'bg-rose-100 text-rose-800 border-rose-200';
        return 'bg-slate-100 text-slate-800 border-slate-200';
    };

    // Join via conclusion_feature_id → sensor log id (O(1) lookup)
    const classMap = useMemo(() => {
        return new Map(
            classHistory.map((c: any) => [Number(c.conclusion_feature_id ?? c.id), c])
        );
    }, [classHistory]);

    const filteredRows = useMemo(() => {
        return sensorHistory.map((row) => {
            const matchingClassObj = classMap.get(Number(row.id)) as any;

            const rawStatus =
                matchingClassObj?.label_status ??
                matchingClassObj?.status ??
                'Unknown';

            const formattedStatus =
                rawStatus.trim().charAt(0).toUpperCase() +
                rawStatus.trim().slice(1).toLowerCase();

            return { ...row, status: formattedStatus };
        }).filter(row => {
            if (labelFilter === 'All') return true;
            return row.status.toLowerCase() === labelFilter.toLowerCase();
        });
    }, [sensorHistory, classMap, labelFilter]);

    return (
        <div className="flex bg-slate-50 min-h-screen text-slate-800">
            <Sidebar
                devices={devices}
                selectedDeviceId={selectedDeviceId}
                onSelectDevice={setSelectedDeviceId}
                showDeviceSelector={true}
            />

            <main className="flex-1 p-8 max-w-7xl mx-auto w-full">
                {errorMsg && (
                    <div className="mb-6 p-4 bg-rose-50 border border-rose-200 text-rose-700 rounded-xl text-sm shadow-sm">
                        ⚠️ <strong>Kesalahan Analitika:</strong> {errorMsg}
                    </div>
                )}

                {/* HEADER & PANEL KONTROL */}
                <header className="mb-8 flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-200 pb-5">
                    <div>
                        <h2 className="text-2xl font-bold tracking-tight text-slate-900">Riwayat & Log Analytics Sistem</h2>
                        <p className="text-sm text-slate-500 mt-1">Audit log penyerapan data sensor dan konsistensi status klasifikasi.</p>
                    </div>

                    <div className="flex items-center gap-3 self-start sm:self-center flex-wrap">

                        {/* TOMBOL REFRESH */}
                        <button
                            onClick={handleRefresh}
                            disabled={loading || !selectedDeviceId}
                            className={`px-4 py-2.5 rounded-xl text-xs font-bold transition-all border shadow-sm flex items-center gap-2 ${loading
                                ? 'bg-slate-100 text-slate-400 border-slate-200 cursor-not-allowed'
                                : 'bg-white hover:bg-slate-50 text-slate-700 border-slate-200 active:scale-95'
                                }`}
                        >
                            <svg
                                className={`h-3.5 w-3.5 text-slate-500 ${loading ? 'animate-spin text-slate-400' : ''}`}
                                fill="none"
                                viewBox="0 0 24 24"
                                stroke="currentColor"
                                strokeWidth="2.5"
                            >
                                <path strokeLinecap="round" strokeLinejoin="round" d="M16.023 9.348h4.992v-.001M2.985 19.644v-4.992m0 0h4.992m-4.993 0l3.181 3.183a8.25 8.25 0 0013.803-3.7M4.031 9.865a8.25 8.25 0 0113.803-3.7l3.181 3.182m0-4.991v4.99" />
                            </svg>
                            {loading ? 'Menyinkronkan...' : 'Refresh History'}
                        </button>

                        {/* DROPDOWN FILTER STATUS */}
                        <div className="flex items-center gap-2 bg-white px-4 py-2.5 rounded-xl border border-slate-200 shadow-sm">
                            <label className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Status:</label>
                            <select
                                value={labelFilter}
                                onChange={(e) => setLabelFilter(e.target.value)}
                                className="text-sm font-bold text-slate-900 bg-transparent focus:outline-none cursor-pointer"
                            >
                                <option value="All">Semua Label</option>
                                <option value="Good">🟢 Sehat (Good)</option>
                                <option value="Moderate">🟡 Sedang (Moderate)</option>
                                <option value="Bad">🔴 Buruk (Bad)</option>
                            </select>
                        </div>

                        {/* DROPDOWN LIMIT */}
                        <div className="flex items-center gap-2 bg-white px-4 py-2.5 rounded-xl border border-slate-200 shadow-sm">
                            <label className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Baris:</label>
                            <select
                                value={dataLimit}
                                onChange={(e) => setDataLimit(Number(e.target.value))}
                                className="text-sm font-bold text-slate-900 bg-transparent focus:outline-none cursor-pointer"
                            >
                                <option value={10}>10 Data</option>
                                <option value={50}>50 Data</option>
                                <option value={100}>100 Data</option>
                            </select>
                        </div>
                    </div>
                </header>

                {/* WIDGET METRIK */}
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-5 mb-8">
                    <div className="bg-white border border-slate-200 p-5 rounded-2xl shadow-sm flex items-center justify-between">
                        <div>
                            <span className="text-xs font-bold text-slate-400 uppercase tracking-wider">Total Udara SEHAT (Good)</span>
                            <span className="text-2xl font-black text-emerald-600 block mt-1">{countStatusDistribution('Good')} Kali</span>
                        </div>
                        <div className="text-2xl bg-emerald-50 p-3 rounded-xl border border-emerald-100">🟢</div>
                    </div>

                    <div className="bg-white border border-slate-200 p-5 rounded-2xl shadow-sm flex items-center justify-between">
                        <div>
                            <span className="text-xs font-bold text-slate-400 uppercase tracking-wider">Total Udara SEDANG (Moderate)</span>
                            <span className="text-2xl font-black text-amber-600 block mt-1">{countStatusDistribution('Moderate')} Kali</span>
                        </div>
                        <div className="text-2xl bg-amber-50 p-3 rounded-xl border border-amber-100">🟡</div>
                    </div>

                    <div className="bg-white border border-slate-200 p-5 rounded-2xl shadow-sm flex items-center justify-between">
                        <div>
                            <span className="text-xs font-bold text-slate-400 uppercase tracking-wider">Total Udara BURUK (Bad)</span>
                            <span className="text-2xl font-black text-rose-600 block mt-1">{countStatusDistribution('Bad')} Kali</span>
                        </div>
                        <div className="text-2xl bg-rose-50 p-3 rounded-xl border border-rose-100">🔴</div>
                    </div>
                </div>

                {/* TABEL */}
                <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
                    <div className="p-6 border-b border-slate-200 bg-slate-50/50">
                        <h3 className="text-base font-bold text-slate-900">Master Record Ingestion Table</h3>
                        <p className="text-xs text-slate-400 mt-0.5">Menampilkan run-time history audit koordinasi multi-tabel dari VM Server.</p>
                    </div>

                    <div className="overflow-x-auto">
                        {loading ? (
                            <div className="text-center py-16 text-slate-400 text-sm">Menghubungkan ke VM pipeline database...</div>
                        ) : filteredRows.length === 0 ? (
                            <div className="text-center py-16 text-slate-400 text-sm">Tidak ditemukan data history dengan kriteria ini.</div>
                        ) : (
                            <table className="w-full text-left border-collapse text-sm">
                                <thead>
                                    <tr className="bg-slate-50/80 text-slate-500 border-b border-slate-200 font-medium text-xs uppercase tracking-wider">
                                        <th className="p-4">Tanggal & Waktu</th>
                                        <th className="p-4">Status Klasifikasi</th>
                                        <th className="p-4">Suhu / Humid</th>
                                        <th className="p-4">MQ135 Raw</th>
                                        <th className="p-4">PPM CO</th>
                                        <th className="p-4">PPM NH3</th>
                                        <th className="p-4">PPM CO2</th>
                                        <th className="p-4">PPM Acetone</th>
                                    </tr>
                                </thead>
                                <tbody className="divide-y divide-slate-100 text-slate-700">
                                    {filteredRows.map((row) => (
                                        <tr key={row.id} className="hover:bg-slate-50/40 transition-colors">
                                            <td className="p-4 font-mono text-xs text-slate-400">
                                                {new Date(row.timestamp).toLocaleString('id-ID')}
                                            </td>
                                            <td className="p-4">
                                                <span className={`text-[11px] font-bold px-2.5 py-1 rounded-md border ${getLabelBadgeColor(row.status)}`}>
                                                    {row.status}
                                                </span>
                                            </td>
                                            <td className="p-4">
                                                <span className="font-semibold text-slate-900">{row.temperature.toFixed(1)}°C</span>
                                                <span className="text-xs text-slate-400 block">{row.humidity.toFixed(1)}% RH</span>
                                            </td>
                                            <td className="p-4 text-slate-500 font-mono text-xs">{row.mq135Raw.toFixed(0)}</td>
                                            <td className="p-4 font-mono font-bold text-slate-900">{row.co.toFixed(2)}</td>
                                            <td className="p-4 font-mono">{row.nh3.toFixed(0)}</td>
                                            <td className="p-4 font-mono">{row.co2.toFixed(0)}</td>
                                            <td className="p-4 font-mono text-slate-600">{row.acetone.toFixed(2)}</td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        )}
                    </div>
                </div>
            </main>
        </div>
    );
}