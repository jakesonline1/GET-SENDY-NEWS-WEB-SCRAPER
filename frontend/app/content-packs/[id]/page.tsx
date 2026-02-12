'use client';

import { useEffect, useState } from 'react';

export default function DetailPage({ params }: { params: { id: string } }) {
  const [pack, setPack] = useState<any>(null);
  const [notes, setNotes] = useState('');

  const load = async () => {
    const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/content-packs/${params.id}`, {
    });
    const data = await res.json();
    setPack(data);
    setNotes(data.reviewer_notes || '');
  };

  useEffect(() => { load(); }, []);

  const save = async () => {
    await fetch(`${process.env.NEXT_PUBLIC_API_URL}/content-packs/${params.id}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ reviewer_notes: notes }),
    });
    load();
  };

  const approve = async () => {
    await fetch(`${process.env.NEXT_PUBLIC_API_URL}/content-packs/${params.id}/approve`, {
      method: 'POST',
    });
    load();
  };

  const reject = async () => {
    await fetch(`${process.env.NEXT_PUBLIC_API_URL}/content-packs/${params.id}/reject`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ reviewer_notes: notes || 'Needs changes' }),
    });
    load();
  };

  const exportJson = async () => {
    const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/content-packs/${params.id}/export`, {
    });
    const data = await res.json();
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `content-pack-${params.id}-handoff.json`;
    a.click();
  };

  if (!pack) return <p>Loading...</p>;

  return (
    <main>
      <h1>{pack.title}</h1>
      <p>Status: {pack.status}</p>
      <p>{pack.summary}</p>
      <h3>Bullets</h3>
      <ul>{pack.bullets.map((b: string) => <li key={b}>{b}</li>)}</ul>
      <h3>Tags + Why tagged</h3>
      <ul>{pack.tags.map((t: string) => <li key={t}>{t} — {pack.why_tagged[t]}</li>)}</ul>
      <h3>Creative Drafts</h3>
      {pack.drafts.map((d: any) => (
        <div key={d.id} style={{ border: '1px solid #ddd', padding: 12, marginBottom: 10 }}>
          <b>Headlines</b>
          <ul>{d.headline_options.map((h: string) => <li key={h}>{h}</li>)}</ul>
          <b>Cover spec</b>
          <pre>{JSON.stringify(d.cover_spec, null, 2)}</pre>
          <b>Caption short</b><p>{d.caption_short}</p>
          <b>Caption long</b><p>{d.caption_long}</p>
          <b>Carousel outline</b><pre>{JSON.stringify(d.carousel_outline, null, 2)}</pre>
        </div>
      ))}
      <h3>Attribution requirements</h3>
      <p>Required credit: {pack.attribution?.required_credit_line}</p>
      <p>Notes: {pack.attribution?.notes}</p>
      <p>Safe to repost: {pack.attribution?.safe_to_repost}</p>
      <textarea value={notes} onChange={(e) => setNotes(e.target.value)} placeholder="Reviewer notes" rows={4} cols={50} />
      <br />
      <button onClick={save}>Save edits</button>
      <button onClick={approve}>Approve</button>
      <button onClick={reject}>Reject</button>
      <button onClick={exportJson}>Export JSON handoff package</button>
      <p>Distance units are stored in km. UI miles toggle planned in v2.</p>
    </main>
  );
}
