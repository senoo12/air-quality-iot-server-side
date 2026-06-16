import React from 'react';
import './globals.css';
import AuthGuard from '@/src/presentation/components/AuthGuard'; // <-- 1. Impor Guard

export const metadata = {
  title: 'Air Quality ML Pipeline Dashboard',
  description: 'Next.js Frontend for FastAPI and XGBoost Forecasting Deployment',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="id">
      <body>
        {/* 2. Bungkus children agar seluruh halaman terproteksi secara mutlak */}
        <AuthGuard>
          {children}
        </AuthGuard>
      </body>
    </html>
  );
}