import { useState, useEffect } from 'react'
import { useParams } from 'react-router-dom'
import { AppWindow, Search } from 'lucide-react'

const APP_COLORS = {
  whatsapp: '#25d366', chrome: '#4285f4', browser: '#ff9100',
  instagram: '#e1306c', telegram: '#2aabee', facebook: '#1877f2',
}

export default function AppDataPage({ API }) {
  const { deviceId } = useParams()
  const [data, setData] = useState([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [pages, setPages] = useState(1)
  const [appFilter, setAppFilter] = useState('')
  const [search, setSearch] = useState('')
  const [loading, setLoading] = useState(true)
  const [apps, setApps] = useState([])

  const fetch_ = (pg=1, sq=search, af=appFilter) => {
    setLoading(true)
    let url = `${API}/api/evidence/${deviceId}/apps?page=${pg}&per_page=50`
    if (af) url += `&app=${af}`
    if (sq) url += `&search=${encodeURIComponent(sq)}`
    fetch(url).then(r=>r.json()).then(d => {
      setData(d.items || [])
      setTotal(d.total || 0)
      setPages(d.pages || 1)
      setPage(pg)
      // Extract unique app names
      if (!af && !sq && pg === 1) setApps([...new Set((d.items||[]).map(x=>x.app_name).filter(Boolean))])
      setLoading(false)
    })
  }
  useEffect(() => { fetch_() }, [deviceId])

  return (
    <div>
      <div className="topbar">
        <div>
          <div className="topbar-title"><AppWindow size={16} style={{marginRight:8}} />App Data</div>
          <div className="topbar-subtitle">{total} records — WhatsApp, Browser, Social Media</div>
        </div>
        <div className="topbar-actions">
          <div className="input-group" style={{ width:200 }}>
            <Search size={14} className="input-icon" />
            <input className="input" placeholder="Search content…" value={search}
              onChange={e => { setSearch(e.target.value); fetch_(1, e.target.value, appFilter) }} />
          </div>
          <select className="select" value={appFilter} onChange={e => { setAppFilter(e.target.value); fetch_(1, search, e.target.value) }}>
            <option value="">All Apps</option>
            {apps.map(a => <option key={a} value={a}>{a}</option>)}
          </select>
        </div>
      </div>
      <div className="page-content">
        <div className="card" style={{ padding:0 }}>
          {loading ? (
            <div className="empty-state"><div className="spinner" /></div>
          ) : data.length === 0 ? (
            <div className="empty-state"><div className="empty-state-icon">📱</div><div className="empty-state-text">No app data</div></div>
          ) : (
            <div className="table-wrapper">
              <table>
                <thead><tr><th>#</th><th>App</th><th>Type</th><th>From</th><th>To</th><th>Content</th><th>Time</th></tr></thead>
                <tbody>
                  {data.map((d,i) => (
                    <tr key={d.id}>
                      <td className="muted">{(page-1)*50+i+1}</td>
                      <td>
                        <span style={{ display:'inline-flex', alignItems:'center', gap:6 }}>
                          <span style={{ width:8, height:8, borderRadius:'50%', background: APP_COLORS[d.app_name] || 'var(--text-muted)', flexShrink:0 }} />
                          <span style={{ fontWeight:600, textTransform:'capitalize' }}>{d.app_name}</span>
                        </span>
                      </td>
                      <td><span className="badge badge-muted">{d.data_type}</span></td>
                      <td className="muted">{d.sender?.slice(0,20) || '—'}</td>
                      <td className="muted">{d.recipient?.slice(0,20) || '—'}</td>
                      <td style={{ maxWidth:300 }}>
                        <div style={{ overflow:'hidden', textOverflow:'ellipsis', whiteSpace:'nowrap', fontSize:12 }}>
                          {d.content || '—'}
                        </div>
                      </td>
                      <td className="muted">{d.timestamp?.slice(0,16).replace('T',' ') || '—'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
          {pages > 1 && (
            <div className="pagination">
              <span className="pagination-info">{total} total</span>
              <button className="btn btn-secondary btn-sm" disabled={page<=1} onClick={() => fetch_(page-1)}>← Prev</button>
              <span style={{ fontSize:12, color:'var(--text-muted)' }}>Page {page} / {pages}</span>
              <button className="btn btn-secondary btn-sm" disabled={page>=pages} onClick={() => fetch_(page+1)}>Next →</button>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
