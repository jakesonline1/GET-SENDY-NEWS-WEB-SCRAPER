'use client';

import Link from 'next/link';
import { useEffect, useState } from 'react';

type Pack = { id: number; title: string; status: string; breaking: boolean; tags: string[] };

export default function QueuePage() {
  const [packs, setPacks] = useState<Pack[]>([]);
  const [status, setStatus] = useState('');
  const [breakingOnly, setBreakingOnly] = useState(false);

  const load = async () => {
    const params = new URLSearchParams();
    if (status) params.set('status', status);
    if (breakingOnly) params.set('breaking', 'true');
    const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/content-packs?${params.toString()}`, {
    });
    const data = await res.json();
    setPacks(data);
  };

  useEffect(() => { load(); }, []);

  return (
    <main>
      <h1>Review Queue Dashboard</h1>
      <select value={status} onChange={(e) => setStatus(e.target.value)}>
        <option value="">All statuses</option>
        <option value="DRAFT_READY">DRAFT_READY</option>
        <option value="IN_REVIEW">IN_REVIEW</option>
        <option value="APPROVED">APPROVED</option>
      </select>
      <label>
        <input type="checkbox" checked={breakingOnly} onChange={(e) => setBreakingOnly(e.target.checked)} /> Breaking
      </label>
      <button onClick={load}>Apply filters</button>
      <ul>
        {packs.map((pack) => (
          <li key={pack.id}>
            <Link href={`/content-packs/${pack.id}`}>{pack.title}</Link> | {pack.status} {pack.breaking ? '🔥' : ''}
          </li>
        ))}
      </ul>
    </main>
  );
}
