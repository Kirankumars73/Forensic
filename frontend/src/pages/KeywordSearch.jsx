import { useState, useEffect } from 'react'
import { useParams } from 'react-router-dom'
import { Search } from 'lucide-react'

const TYPE_COLORS = { call:'badge-green', sms:'badge-cyan', app_data:'badge-purple', email:'badge-yellow' }

const ADMIN_KEY = 'case-k-unlocked'

export default function KeywordSearch({ API, unlocked }) {
  const { deviceId } = useParams()
  const [query, setQuery] = useState('')
  const [hits, setHits] = useState([])
  const [total, setTotal] = useState(0)
  const [loading, setLoading] = useState(false)

  const search_ = (q) => {
    if (!q.trim()) { setHits([]); return }
    setLoading(true)
    const headers = unlocked ? { 'X-Admin-Key': ADMIN_KEY } : {}
    fetch(`${API}/api/evidence/${deviceId}/search?q=${encodeURIComponent(q)}`, { headers })
      .then(r => r.json())
      .then(data => {
        setHits(data.hits || [])
        setTotal(data.total || 0)
        setLoading(false)
      })
  }

  return (
    <div>
      <div className="topbar">
        <div>
          <div className="topbar-title"><Search size={16} style={{marginRight:8}} />Keyword Search</div>
          <div className="topbar-subtitle">Search across calls, SMS, app data, and emails</div>
        </div>
      </div>
      <div className="page-content">
        <div className="card" style={{ marginBottom:16 }}>
          <div style={{ display:'flex', gap:10 }}>
            <div className="input-group" style={{ flex:1 }}>
              <Search size={16} className="input-icon" />
              <input className="input" placeholder='Search for keywords, phone numbers, URLs… (e.g. "password", "₹", "DM me")'
                value={query}
                onChange={e => setQuery(e.target.value)}
                onKeyDown={e => e.key==='Enter' && search_(query)}
                style={{ fontSize:14 }}
              />
            </div>
            <button className="btn btn-primary" onClick={() => search_(query)} disabled={loading}>
              {loading ? <><span className="spinner" style={{width:14,height:14}} /> Searching…</> : 'Search'}
            </button>
          </div>
          <div style={{ marginTop:10, fontSize:12, color:'var(--text-muted)' }}>
            Tip: Try searching for suspicious keywords like <span style={{color:'var(--orange)'}}>transfer, password, delete, anonymous, meet</span>
          </div>
        </div>

        {hits.length > 0 && (
          <div className="card">
            <div className="card-header">
              <div className="card-title">Results: {total} hits for &ldquo;{query}&rdquo;</div>
            </div>
            <div style={{ display:'flex', flexDirection:'column', gap:8 }}>
              {hits.map((h, i) => (
                <div key={i} style={{ background:'var(--bg-elevated)', border:'1px solid var(--border)', borderRadius:10, padding:'12px 14px' }}>
                  <div style={{ display:'flex', gap:8, alignItems:'center', marginBottom:6 }}>
                    <span className={`badge ${TYPE_COLORS[h.type] || 'badge-muted'}`}>{h.type}</span>
                    <span className="badge badge-muted">{h.field}</span>
                  </div>
                  <div style={{ fontSize:13, color:'var(--text-primary)', lineHeight:1.5 }}>
                    {h.value?.split(new RegExp(`(${query})`, 'gi')).map((part, pi) =>
                      part.toLowerCase() === query.toLowerCase()
                        ? <mark key={pi} style={{ background:'rgba(255,214,0,0.25)', color:'var(--yellow)', borderRadius:3, padding:'0 2px' }}>{part}</mark>
                        : part
                    )}
                  </div>
                  {h.record?.timestamp && (
                    <div style={{ fontSize:10, color:'var(--text-muted)', marginTop:5 }}>
                      {new Date(h.record.timestamp).toLocaleString()}
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}
        {query && !loading && hits.length === 0 && (
          <div className="empty-state">
            <div className="empty-state-icon">🔍</div>
            <div className="empty-state-text">No results for &ldquo;{query}&rdquo;</div>
          </div>
        )}
      </div>
    </div>
  )
}
