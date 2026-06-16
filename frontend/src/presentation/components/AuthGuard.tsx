'use client';

import { useEffect, useState } from 'react';
import { useRouter, usePathname } from 'next/navigation';
import { jwtDecode } from 'jwt-decode'; // Mengurai isi payload JWT

export default function AuthGuard({ children }: { children: React.ReactNode }) {
    const router = useRouter();
    const pathname = usePathname();
    const [authorized, setAuthorized] = useState(false);

    const checkAuth = async () => {
        const token = localStorage.getItem('access_token');
        const refreshToken = localStorage.getItem('refresh_token');

        // 1. JIKA MAU MASUK HALAMAN LOGIN
        if (pathname === '/login') {
            if (token) {
                router.push('/');
            } else {
                setAuthorized(true);
            }
            return;
        }

        // 2. JIKA MAU MASUK HALAMAN TERPROTEKSI TAPI TIDAK ADA TOKEN
        if (!token) {
            setAuthorized(false);
            router.push('/login');
            return;
        }

        // 3. VALIDASI MASA AKTIF TOKEN (VALIDATE EXPIRATION)
        try {
            const decoded: any = jwtDecode(token);
            const currentTime = Date.now() / 1000; // Ubah ke satuan detik

            // Jika token masih aktif (berikan buffer 10 detik sebelum meledak)
            if (decoded.exp > currentTime + 10) {
                setAuthorized(true);
            } else {
                // 💡 TOKEN HABIS! LAKUKAN SILENT REFRESH TOKEN
                if (refreshToken) {
                    console.log("🔄 Access Token Kedaluwarsa. Mencoba memperbarui sesi...");

                    const formData = new URLSearchParams();
                    formData.append('refresh_token', refreshToken);

                    const res = await fetch('http://34.101.207.101/api/v1/refresh', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
                        body: formData.toString(),
                    });

                    if (res.ok) {
                        const data = await res.json();
                        localStorage.setItem('access_token', data.access_token);
                        console.log("✅ Sesi berhasil diperbarui otomatis tanpa kick user!");
                        setAuthorized(true);
                    } else {
                        // Jika refresh token juga hangus
                        throw new Error("Refresh token expired");
                    }
                } else {
                    throw new Error("No refresh token");
                }
            }
        } catch (error) {
            // Jika semua token gagal divalidasi, bersihkan storage dan tendang ke login
            console.log("❌ Sesi kedaluwarsa mutlak. Mengalihkan ke halaman login.");
            localStorage.removeItem('access_token');
            localStorage.removeItem('refresh_token');
            setAuthorized(false);
            router.push('/login');
        }
    };

    useEffect(() => {
        checkAuth();
    }, [pathname, router]);

    if (!authorized) {
        return (
            <div className="min-h-screen bg-slate-950 flex flex-col items-center justify-center text-slate-400 text-sm font-sans">
                <svg className="animate-spin h-5 w-5 text-emerald-500 mb-3" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                </svg>
                Menyinkronkan Sesi Keamanan...
            </div>
        );
    }

    return <>{children}</>;
}