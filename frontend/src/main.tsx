import React, { useEffect, useState } from 'react';
import { createRoot } from 'react-dom/client';
import './style.css';

type Stock = { code: string; name: string; price: number; change_pct: number };
type Sector = { id: string; name: string; change_pct: number; stocks: Stock[] };
type Market = { source: string; updated_at: string; sectors: Sector[] };
type SavedStock = Pick<Stock, 'code' | 'name'>;
async function api<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`/api/${path}`, init);
  if (!res.ok) { const body = await res.json().catch(() => ({})); throw new Error(typeof body.detail === 'string' ? body.detail : '请求失败，请稍后重试'); }
  return res.status === 204 ? undefined as T : res.json();
}
const gain = (value: number) => `${value >= 0 ? '+' : ''}${value.toFixed(2)}%`;
function App() {
  const [market, setMarket] = useState<Market | null>(null);
  const [watchlist, setWatchlist] = useState<SavedStock[]>([]);
  const [selected, setSelected] = useState('ai');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(true);
  const [pending, setPending] = useState(false);
  const [code, setCode] = useState('');
  async function refresh() {
    setLoading(true); setError('');
    try { const [m, w] = await Promise.all([api<Market>('market'), api<SavedStock[]>('watchlist')]); setMarket(m); setWatchlist(w); }
    catch (e) { setError((e as Error).message); } finally { setLoading(false); }
  }
  useEffect(() => { void refresh(); }, []);
  async function changeStock(stockCode: string, remove = false) {
    setPending(true); setError('');
    try {
      await api(remove ? `watchlist/${stockCode}` : 'watchlist', remove ? { method: 'DELETE' } : { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ code: stockCode }) });
      setWatchlist(await api<SavedStock[]>('watchlist')); setCode('');
    } catch (e) { setError((e as Error).message); } finally { setPending(false); }
  }
  const sector = market?.sectors.find(s => s.id === selected) ?? market?.sectors[0];
  return <main>
    <header><div><p className="eyebrow">市场观察台 / A SHARE RADAR</p><h1>A股热点雷达 <span className="badge">模拟数据</span></h1><p className="muted">聚焦热点板块，追踪板块领涨股</p></div><button onClick={() => void refresh()} disabled={loading || pending}>{loading ? '加载中…' : '刷新数据'}</button></header>
    <div className="notice">模拟数据演示 · 所有价格与涨跌幅均为虚构示例，不代表实时行情，不构成投资建议。</div>
    <div className="update">数据更新时间：{market ? new Date(market.updated_at).toLocaleString('zh-CN', { timeZone: 'Asia/Shanghai', hour12: false }) + '（北京时间）' : '尚未获取'} <span>手动刷新 · 模拟行情</span></div>
    {error && <div role="alert" className="error">{error} <button onClick={() => void refresh()}>重新加载</button></div>}
    <div className="grid"><section><div className="section-title"><h2>热点板块排行</h2><span>按涨幅排序</span></div>
      {market?.sectors.map((s, i) => <button key={s.id} className={`sector ${sector?.id === s.id ? 'active' : ''}`} onClick={() => setSelected(s.id)} aria-pressed={sector?.id === s.id}><span className="rank">{String(i + 1).padStart(2, '0')}</span><strong>{s.name}</strong><span className="up">{gain(s.change_pct)}</span></button>)}
      {!market && <p className="muted">{loading ? '正在加载板块…' : '暂无行情，请重新加载'}</p>}
    </section><section><div className="section-title"><h2>{sector?.name ?? '板块'} · 领涨股</h2><span>点击板块切换</span></div>
      <div className="table-wrap"><table><thead><tr><th>股票</th><th>价格（元）</th><th>涨跌幅</th><th>操作</th></tr></thead><tbody>{sector?.stocks.map(s => <tr key={s.code}><td><strong>{s.name}</strong><small>{s.code}</small></td><td>{s.price.toFixed(2)}</td><td className="up">{gain(s.change_pct)}</td><td><button disabled={pending || watchlist.some(w => w.code === s.code)} onClick={() => void changeStock(s.code)}>{watchlist.some(w => w.code === s.code) ? '已添加' : '+ 自选'}</button></td></tr>)}</tbody></table></div>
    </section></div>
    <section className="watch"><div className="section-title"><h2>我的自选 <span className="count">{watchlist.length}</span></h2><span>自动保存到 SQLite，刷新仍保留</span></div>
      <form onSubmit={e => { e.preventDefault(); void changeStock(code); }}><label htmlFor="stock-code">股票代码</label><input id="stock-code" placeholder="输入页面中的六位股票代码" value={code} onChange={e => setCode(e.target.value)} pattern="[0-9]{6}" required maxLength={6}/><button disabled={pending || loading}>添加自选</button></form>
      <div className="saved-list">{watchlist.map(s => <div className="saved" key={s.code}><div><strong>{s.name}</strong><small>{s.code}</small></div><button disabled={pending} onClick={() => void changeStock(s.code, true)} aria-label={`删除${s.name}`}>删除</button></div>)}</div>
      {!watchlist.length && <p className="empty">还没有自选股，从领涨股列表添加第一只吧。</p>}
    </section><footer>Stock Hotspot Radar · 模拟数据版本 · 自选列表为本地实例共享数据</footer>
  </main>;
}
createRoot(document.getElementById('root')!).render(<React.StrictMode><App/></React.StrictMode>);
