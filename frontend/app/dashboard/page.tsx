'use client';

import React from 'react';
import Sidebar from '@/src/presentation/components/Sidebar';
import { useAirQuality } from '@/src/presentation/hooks/useAirQuality';
import Link from 'next/link';

export default function DashboardPage() {
  const {
    devices,
    selectedDeviceId,
    setSelectedDeviceId,
    currentDevice,
    latestSensor,
    latestClass,
    forecast,
    loading,
    loadingForecast,
    loadingToggle,
    errorMsg,
    executeForecasting,
    handleRefresh,
    handleTogglePower 
  } = useAirQuality();

  const getLabelBadgeColor = (label: string | undefined) => {
    if (label === 'Good') return 'bg-emerald-100 text-emerald-800 border-emerald-200';
    if (label === 'Moderate') return 'bg-amber-100 text-amber-800 border-amber-200';
    if (label === 'Bad') return 'bg-rose-100 text-rose-800 border-rose-200';
    return 'bg-slate-100 text-slate-800 border-slate-200';
  };

  return (
    <div className="flex bg-slate-50 min-h-screen text-slate-800">
      <Sidebar devices={devices} selectedDeviceId={selectedDeviceId} onSelectDevice={setSelectedDeviceId} />

      <main className="flex-1 p-8 max-w-7xl mx-auto w-full">
        {errorMsg && <div className="mb-6 p-4 bg-rose-50 border border-rose-200 text-rose-700 rounded-xl text-sm">⚠️ {errorMsg}</div>}

        {/* HEADER AREA */}
        <header className="mb-8 border-b border-slate-200 pb-5 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div className="flex items-center gap-4">

            {/* 💡 TOMBOL POWER HARDWARE SAKELAR ON/OFF ESP32 */}
            <button
              onClick={handleTogglePower}
              disabled={loadingToggle || !selectedDeviceId}
              className={`p-3 rounded-2xl border transition-all duration-300 shadow-md ${!selectedDeviceId
                  ? 'bg-slate-200 cursor-not-allowed'
                  : currentDevice?.isActive
                    ? 'bg-rose-600 text-white border-rose-700 hover:bg-rose-500 active:scale-95 shadow-rose-900/20'
                    : 'bg-slate-800 text-slate-400 border-slate-900 hover:bg-slate-700 hover:text-white active:scale-95'
                }`}
              title={currentDevice?.isActive ? "Matikan Alat ESP32" : "Nyalakan Alat ESP32"}
            >
              {loadingToggle ? (
                <svg className="animate-spin h-5 w-5 text-current" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                </svg>
              ) : (
                <span className="text-base font-bold flex items-center gap-1.5">
                  {currentDevice?.isActive ? '🔴 Hardware ON' : '⚫ Hardware OFF'}
                </span>
              )}
            </button>

            <div>
              <h2 className="text-2xl font-bold tracking-tight text-slate-900">Dasbor Utama Real-Time</h2>
              <p className="text-sm text-slate-500 mt-0.5">Pengendalian modul IoT dan monitoring inferensi XGBoost TSC.</p>
            </div>
          </div>

          <div className="flex items-center gap-3 self-start sm:self-center">
            <button
              onClick={handleRefresh}
              disabled={loading || !selectedDeviceId}
              className={`px-4 py-2.5 rounded-xl text-xs font-bold transition-all border shadow-sm flex items-center gap-2 ${loading ? 'bg-slate-100 text-slate-400 border-slate-200 cursor-not-allowed' : 'bg-white hover:bg-slate-50 text-slate-700 border-slate-200 active:scale-95'}`}
            >
              <svg className={`h-3.5 w-3.5 text-slate-500 ${loading ? 'animate-spin text-slate-400' : ''}`} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2.5">
                <path strokeLinecap="round" strokeLinejoin="round" d="M16.023 9.348h4.992v-.001M2.985 19.644v-4.992m0 0h4.992m-4.993 0l3.181 3.183a8.25 8.25 0 0013.803-3.7M4.031 9.865a8.25 8.25 0 0113.803-3.7l3.181 3.182m0-4.991v4.99" />
              </svg>
              {loading ? 'Menyinkronkan...' : 'Refresh Data'}
            </button>

            <Link href="/history" className="px-4 py-2.5 bg-white border border-slate-200 hover:bg-slate-50 text-slate-700 rounded-xl text-xs font-bold transition-all shadow-sm flex items-center gap-1.5">
              📜 Lihat History Log
            </Link>
          </div>
        </header>

        {/* METRIKS UTAMA & PANEL KONTROL FORECAST */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
          <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm flex flex-col justify-between">
            <div>
              <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider block">Klasifikasi Saat Ini (t-0)</span>
              <div className="mt-4">
                <span className={`text-2xl font-black px-4 py-2 rounded-xl border inline-block ${getLabelBadgeColor(latestClass?.status)}`}>
                  {latestClass?.status || 'NO DATA'}
                </span>
              </div>
            </div>
            <div className="text-xs text-slate-400 mt-6 pt-3 border-t border-slate-100">
              Sinkronisasi: {latestClass ? new Date(latestClass.createdAt).toLocaleString('id-ID') : '—'}
            </div>
          </div>

          <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm lg:col-span-2 flex flex-col justify-between">
            <div>
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                <div>
                  <span className="text-xs font-semibold text-emerald-600 uppercase tracking-wider block">Day-Ahead Analytics Pipeline</span>
                  <h3 className="text-lg font-bold text-slate-900 mt-1">Peramalan Kualitas Udara (Model EXP-06)</h3>
                </div>
                <button
                  onClick={executeForecasting}
                  disabled={loadingForecast || !selectedDeviceId}
                  className="px-5 py-3 rounded-xl font-bold text-sm text-white bg-slate-900 hover:bg-slate-800 transition-all shadow-md"
                >
                  {loadingForecast ? 'Mengekstrak 49 Lag...' : '🔮 Jalankan Prediksi'}
                </button>
              </div>

              <div className="mt-5 p-4 bg-slate-50 border border-slate-200 rounded-xl">
                {forecast ? (
                  <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 text-sm">
                    <div>Hasil: <span className={`font-bold px-1.5 py-0.5 rounded text-xs border ${getLabelBadgeColor(forecast.status)}`}>{forecast.status}</span></div>
                    <div>Target: <strong className="text-slate-800">{forecast.targetDate} ({forecast.targetTime})</strong></div>
                    <div>Confidence: <strong className="text-emerald-600">{(forecast.confidence * 100).toFixed(2)}%</strong></div>
                  </div>
                ) : (
                  <p className="text-xs text-slate-400 text-center py-2">Klik tombol di atas untuk memicu peramalan rentet waktu 24 jam ke depan menggunakan model XGBoost.</p>
                )}
              </div>
            </div>
          </div>
        </div>

        {/* TABEL DATA SENSOR TERKINI */}
        <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
          <div className="p-6 border-b border-slate-200 bg-slate-50/50">
            <h3 className="text-base font-bold text-slate-900">Data Sensor Terkini (Most Recent Packet)</h3>
            <p className="text-xs text-slate-400 mt-0.5">Satu-satunya data tangkapan paling mutakhir yang dikirim oleh modul perangkat keras IoT Anda.</p>
          </div>

          <div className="overflow-x-auto">
            {loading ? (
              <div className="text-center py-12 text-slate-400 text-sm">Memuat data dari VM Server...</div>
            ) : !latestSensor ? (
              <div className="text-center py-12 text-slate-400 text-sm">Tidak ditemukan data sensor masuk untuk perangkat ini.</div>
            ) : (
              <table className="w-full text-left border-collapse text-sm">
                <thead>
                  <tr className="bg-slate-50 text-slate-500 border-b border-slate-200 font-medium text-xs uppercase tracking-wider">
                    <th className="p-4">Waktu Terima</th>
                    <th className="p-4">MQ135 Raw</th>
                    <th className="p-4">Temperature (°C)</th>
                    <th className="p-4">Humidity (%)</th>
                    <th className="p-4">PPM NH3</th>
                    <th className="p-4">PPM CO</th>
                    <th className="p-4">PPM CO2</th>
                    <th className="p-4">PPM Acetone</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 text-slate-700">
                  <tr className="bg-emerald-50/10 hover:bg-slate-50 transition-colors">
                    <td className="p-4 font-mono text-xs text-slate-400">
                      {new Date(latestSensor.timestamp).toLocaleString('id-ID')}
                    </td>
                    <td className="p-4 font-mono text-slate-600">{latestSensor.mq135Raw.toFixed(1)}</td>
                    <td className="p-4 font-semibold text-slate-900">{latestSensor.temperature.toFixed(1)}°C</td>
                    <td className="p-4">{latestSensor.humidity.toFixed(1)}%</td>
                    <td className="p-4 font-mono">{latestSensor.nh3.toFixed(1)}</td>
                    <td className="p-4 font-mono font-bold text-emerald-700">{latestSensor.co.toFixed(2)}</td>
                    <td className="p-4 font-mono">{latestSensor.co2.toFixed(1)}</td>
                    <td className="p-4 font-mono text-slate-600">{latestSensor.acetone.toFixed(2)}</td>
                  </tr>
                </tbody>
              </table>
            )}
          </div>
        </div>
      </main>
    </div>
  );
}