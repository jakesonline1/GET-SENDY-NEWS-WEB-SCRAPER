'use client';

import Link from 'next/link';

export default function HomePage() {
  return (
    <main>
      <h1>Get Sendy Review Queue</h1>
      <p>Authentication is temporarily bypassed for local testing and tuning.</p>
      <Link href="/queue">Open review queue</Link>
    </main>
  );
}
