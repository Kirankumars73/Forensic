import { useState, useEffect } from 'react'
import { useParams } from 'react-router-dom'
import { Users, Search } from 'lucide-react'

export default function Contacts({ API }) {
  const { deviceId } = useParams()
  const [contacts, setContacts] = useState([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [pages, setPages] = useState(1)
  const [search, setSearch] = useState('')
  const [loading, setLoading] = useState(true)

  const fetch_ = (pg=1, sq=search) => {
    setLoading(true)
    let url = `${API}/api/evidence/${deviceId}/contacts?page=${pg}&per_page=50`
    if (sq) url += `&search=${encodeURIComponent(sq)}`
    fetch(url).then(r=>r.json()).then(data => {
      setContacts(data.items || [])
      setTotal(data.total || 0)
      setPages(data.pages || 1)
      setPage(pg)
      setLoading(false)
    })
  }
  useEffect(() => { fetch_() }, [deviceId])

  return (
    <div>
      <div className="topbar">
        <div>
          <div className="topbar-title"><Users size={16} style={{marginRight:8}} />Contacts</div>
          <div className="topbar-subtitle">{total} contacts — Device #{deviceId}</div>
        </div>
        <div className="topbar-actions">
          <div className="input-group" style={{ width:220 }}>
            <Search size={14} className="input-icon" />
            <input className="input" placeholder="Search name…" value={search}
              onChange={e => { setSearch(e.target.value); fetch_(1, e.target.value) }} />
          </div>
        </div>
      </div>
      <div className="page-content">
        <div className="card" style={{ padding:0 }}>
          {loading ? (
            <div className="empty-state"><div className="spinner" /></div>
          ) : contacts.length === 0 ? (
            <div className="empty-state"><div className="empty-state-icon">👤</div><div className="empty-state-text">No contacts</div></div>
          ) : (
            <div className="table-wrapper">
              <table>
                <thead><tr><th>#</th><th>Name</th><th>Phone Numbers</th><th>Emails</th><th>Organization</th><th>Times Contacted</th></tr></thead>
                <tbody>
                  {contacts.map((c, i) => {
                    const phones = Array.isArray(c.phone_numbers) ? c.phone_numbers : []
                    const emails = Array.isArray(c.emails) ? c.emails : []
                    return (
                      <tr key={c.id}>
                        <td className="muted">{(page-1)*50+i+1}</td>
                        <td style={{ fontWeight:600 }}>{c.name || '(No Name)'}</td>
                        <td className="mono">{phones.join(', ') || '—'}</td>
                        <td style={{ fontSize:12, color:'var(--cyan)' }}>{emails.join(', ') || '—'}</td>
                        <td className="muted">{c.organization || '—'}</td>
                        <td><span className={`badge ${c.times_contacted > 20 ? 'badge-orange' : 'badge-muted'}`}>{c.times_contacted || 0}</span></td>
                      </tr>
                    )
                  })}
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
