import { useEffect, useState, type FormEvent } from 'react';
import { createRoot } from 'react-dom/client';
import './style.css';

type Item = { id: string; title: string };
async function request(path: string, options?: RequestInit) {
  const response = await fetch(path, options);
  if (!response.ok) throw new Error('処理できませんでした。接続を確認して再度お試しください。');
  return response.status === 204 ? null : response.json();
}

function App() {
  const [items, setItems] = useState<Item[]>([]);
  const [title, setTitle] = useState('');
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  async function reload() { setItems(await request('/api/items')); }
  useEffect(() => { reload().catch(e => setError(e.message)).finally(() => setLoading(false)); }, []);
  async function submit(event: FormEvent) {
    event.preventDefault(); setBusy(true); setError('');
    try {
      await request('/api/items', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ title: title.trim() }) });
      setTitle(''); await reload();
    } catch (e) { setError((e as Error).message); } finally { setBusy(false); }
  }
  async function remove(id: string) {
    setBusy(true); setError('');
    try { await request('/api/items/' + id, { method: 'DELETE' }); await reload(); }
    catch (e) { setError((e as Error).message); } finally { setBusy(false); }
  }
  return <main>
    <p className="eyebrow">__APP_NAME__</p>
    <h1>アイデアを、ひとつずつ。</h1>
    <p className="intro">思いついたことを記録して、次の一歩につなげましょう。</p>
    <form onSubmit={submit}>
      <label htmlFor="title">新しい項目</label>
      <div className="input-row"><input id="title" value={title} onChange={e => setTitle(e.target.value)} maxLength={120} required placeholder="何から始めますか？"/><button disabled={busy || !title.trim()}>追加</button></div>
    </form>
    {error && <p role="alert">{error}</p>}
    <section aria-label="保存した項目" aria-busy={loading || busy}>
      <h2>保存した項目 <span>{items.length}</span></h2>
      {loading ? <p role="status">読み込み中…</p> : items.length === 0 ? <p className="empty">まだ項目がありません。最初のひとつを追加しましょう。</p> :
        <ul>{items.map(item => <li key={item.id}><span>{item.title}</span><button className="delete" disabled={busy} aria-label={`${item.title}を削除`} onClick={() => remove(item.id)}>削除</button></li>)}</ul>}
    </section>
  </main>;
}
createRoot(document.getElementById('root')!).render(<App/>);
