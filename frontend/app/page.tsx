'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';

export default function LoginPage() {
  const [email, setEmail] = useState('admin@getsendy.dev');
  const [password, setPassword] = useState('password123');
  const [error, setError] = useState('');
  const router = useRouter();

  const login = async () => {
    const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password }),
    });
    if (!res.ok) {
      setError('Login failed');
      return;
    }
    const data = await res.json();
    localStorage.setItem('token', data.access_token);
    router.push('/queue');
  };

  return (
    <main>
      <h1>Get Sendy Review Queue</h1>
      <input value={email} onChange={(e) => setEmail(e.target.value)} placeholder="email" />
      <br />
      <input value={password} onChange={(e) => setPassword(e.target.value)} placeholder="password" type="password" />
      <br />
      <button onClick={login}>Log in</button>
      {error && <p>{error}</p>}
    </main>
  );
}
