import { useState, useEffect } from 'react'
import { useParams } from 'react-router-dom'
import { Phone, Search, Filter, Download } from 'lucide-react'

const TYPE_COLORS = {
  incoming: 'badge-green', outgoing: 'badge-cyan',
  missed: 'badge-red', rejected: 'badge-orange',
  voicemail: 'badge-purple', blocked: 'badge-muted',
}

export default function CallLogs({ API }) {
  const { deviceId } = useParams()
  const [calls, setCalls] = useState([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [pages, setPages] = useState(1)
  const [search, setSearch] = useState('')
  const [typeFilter, setTypeFilter] = useState('')
  const [loading, setLoading] = useState(true)
  const [stats, setStats] = useState({})

  const fetchCalls = (pg = 1, sq = search, tf = typeFilter) => {
    setLoading(true)
    let url = `${API}/api/evidence/${deviceId}/calls?page=${pg}&per_page=50`
    if (sq) url += `&search=${encodeURIComponent(sq)}`
    if (tf) url += `&type=${tf}`
    fetch(url).then(r => r.json()).then(data => {
      setCalls(data.items || [])
      setTotal(data.total || 0)
      setPages(data.pages || 1)
      setPage(pg)
      setLoading(false)
    })
  }

  useEffect(() => { fetchCalls() }, [deviceId])

  useEffect(() => {
    fetch(`${API}/api/evidence/${deviceId}/stats`).then(r => r.json()).then(setStats)
  }, [deviceId])

  const incoming = calls.filter(c => c.call_type === 'incoming').length
  const outgoing = calls.filter(c => c.call_type === 'outgoing').length
  const missed = calls.filter(c => c.call_type === 'missed').length
  const totalDur = calls.reduce((s, c) => s + (c.duration_seconds || 0), 0)
  const fmtDur = (s) => { const m = Math.floor(s/60); const h = Math.floor(m/60); return h ? `${h}h ${m%60}m` : `${m}m ${s%60}s` }

  return (
    <div>
      <div className="topbar">
        <div>
          <div className="topbar-title"><Phone size={16} style={{ marginRight:8 }} />Call Logs</div>
          <div className="topbar-subtitle">{total} records — Device #{deviceId}</div>
        </div>
        <div className="topbar-actions">
          <div className="input-group" style={{ width:220 }}>
            <Search size={14} className="input-icon" />
            <input className="input" placeholder="Search number or name…" value={search}
              onChange={e => { setSearch(e.target.value); fetchCalls(1, e.target.value, typeFilter) }} />
          </div>
          <select className="select" value={typeFilter}
            onChange={e => { setTypeFilter(e.target.value); fetchCalls(1, search, e.target.value) }}>
            <option value="">All Types</option>
            <option value="incoming">Incoming</option>
            <option value="outgoing">Outgoing</option>
            <option value="missed">Missed</option>
            <option value="rejected">Rejected</option>
          </select>
        </div>
      </div>
      <div className="page-content">
        {/* Mini stats */}
        <div className="stats-grid" style={{ gridTemplateColumns:'repeat(4,1fr)', marginBottom:16 }}>
          {[
            { label:'Incoming', value: stats.calls ? Math.round(calls.filter(c=>c.call_type==='incoming').length) : 0, color:'var(--green)' },
            { label:'Outgoing', value: calls.filter(c=>c.call_type==='outgoing').length, color:'var(--cyan)' },
            { label:'Missed', value: calls.filter(c=>c.call_type==='missed').length, color:'var(--red)' },
            { label:'Total Talk Time', value: fmtDur(totalDur), color:'var(--orange)' },
          ].map(({ label, value, color }) => (
            <div className="stat-card" key={label}>
              <div className="stat-value" style={{ fontSize:22, color }}>{value}</div>
              <div className="stat-label">{label}</div>
            </div>
          ))}
        </div>

        <div className="card" style={{ padding:0 }}>
          {loading ? (
            <div className="empty-state"><div className="spinner" /><div className="empty-state-text">Loading…</div></div>
          ) : calls.length === 0 ? (
            <div className="empty-state">
              <div className="empty-state-icon">📞</div>
              <div className="empty-state-text">No call records found</div>
            </div>
          ) : (
            <div className="table-wrapper">
              <table>
                <thead><tr>
                  <th>#</th>
                  <th>Number</th>
                  <th>Name</th>
                  <th>Type</th>
                  <th>Duration</th>
                  <th>Date / Time</th>
                  <th>Location</th>
                </tr></thead>
                <tbody>
                  {calls.map((c, i) => (
                    <tr key={c.id}>
                      <td className="muted">{(page-1)*50+i+1}</td>
                      <td className="mono">{c.number || '—'}</td>
                      <td style={{ fontWeight: c.name ? 500 : 400, color: c.name ? 'var(--text-primary)' : 'var(--text-muted)' }}>
                        {c.name || '(Unknown)'}
                      </td>
                      <td><span className={`badge ${TYPE_COLORS[c.call_type] || 'badge-muted'}`}>{c.call_type}</span></td>
                      <td className="mono" style={{ color: c.duration_seconds > 0 ? 'var(--text-code)' : 'var(--text-muted)' }}>
                        {c.duration_formatted || '—'}
                      </td>
                      <td className="muted">{c.timestamp ? new Date(c.timestamp).toLocaleString() : '—'}</td>
                      <td className="muted" style={{ fontSize:11 }}>{c.geocoded_location || '—'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
          {/* Pagination */}
          {pages > 1 && (
            <div className="pagination">
              <span className="pagination-info">{total} total</span>
              <button className="btn btn-secondary btn-sm" disabled={page<=1} onClick={() => fetchCalls(page-1)}>← Prev</button>
              <span style={{ fontSize:12, color:'var(--text-muted)' }}>Page {page} / {pages}</span>
              <button className="btn btn-secondary btn-sm" disabled={page>=pages} onClick={() => fetchCalls(page+1)}>Next →</button>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
