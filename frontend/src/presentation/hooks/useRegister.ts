import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { AuthRepositoryImpl } from "@/src/data/repositories/AuthRepositoryImpl";

const authRepository = new AuthRepositoryImpl();

export function useRegister() {
    const router = useRouter();
    const [username, setUsername] = useState('');
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [confirmPassword, setConfirmPassword] = useState('');
    const [loading, setLoading] = useState(false);
    const [errorMsg, setErrorMsg] = useState<string | null>(null);
    const [successMsg, setSuccessMsg] = useState<string | null>(null);

    const handleRegister = async (e: React.FormEvent) => {
        e.preventDefault();
        setLoading(true);
        setErrorMsg(null);
        setSuccessMsg(null);

        // Validasi Sederhana
        if (!username.trim() || !email.trim() || !password || !confirmPassword) {
            setErrorMsg("Semua kolom input wajib diisi.");
            setLoading(false);
            return;
        }

        if (password !== confirmPassword) {
            setErrorMsg("Konfirmasi password tidak cocok.");
            setLoading(false);
            return;
        }

        try {
            await authRepository.register({ username, email, password });

            setSuccessMsg("🚀 Akun berhasil didaftarkan! Mengalihkan ke halaman login...");

            // Otomatis pindah ke halaman login setelah 2 detik sukses
            setTimeout(() => {
                router.push('/login');
            }, 2000);

        } catch (err: any) {
            setErrorMsg(err.message);
        } finally {
            setLoading(false);
        }
    };

    return {
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
        handleRegister,
    };
}