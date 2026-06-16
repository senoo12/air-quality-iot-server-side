import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { AuthRepositoryImpl } from "@/src/data/repositories/AuthRepositoryImpl";

const authRepository = new AuthRepositoryImpl();

export function useAuth() {
    const router = useRouter();
    const [username, setUsername] = useState('');
    const [password, setPassword] = useState('');
    const [loading, setLoading] = useState(false);
    const [errorMsg, setErrorMsg] = useState<string | null>(null);

    const handleLogin = async (e: React.FormEvent) => {
        e.preventDefault();
        setLoading(true);
        setErrorMsg(null);

        try {
            const tokenData = await authRepository.login(username, password);

            // Simpan token ke localStorage untuk digunakan di halaman dashboard & history
            localStorage.setItem('access_token', tokenData.accessToken);
            localStorage.setItem('refresh_token', tokenData.refreshToken);

            // Redirect ke halaman dasbor utama
            router.push('/dashboard');
        } catch (err: any) {
            setErrorMsg(err.message);
        } finally {
            setLoading(false);
        }
    };

    return {
        username,
        setUsername,
        password,
        setPassword,
        loading,
        errorMsg,
        handleLogin,
    };
}