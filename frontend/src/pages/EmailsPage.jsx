import { useState, useEffect } from 'react'
import { useParams } from 'react-router-dom'
import { Mail, Search } from 'lucide-react'

const ADMIN_KEY = 'case-k-unlocked'

export default function EmailsPage({ API, unlocked }) {
  const { deviceId } = useParams()
  const [emails, setEmails] = useState([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [pages, setPages] = useState(1)
  const [search, setSearch] = useState('')
  const [loading, setLoading] = useState(true)
  const [selected, setSelected] = useState(null)

  const fetch_ = (pg=1, sq=search) => {
    setLoading(true)
    let url = `${API}/api/evidence/${deviceId}/emails?page=${pg}&per_page=50`
    if (sq) url += `&search=${encodeURIComponent(sq)}`
    const headers = unlocked ? { 'X-Admin-Key': ADMIN_KEY } : {}
    fetch(url, { headers }).then(r=>r.json()).then(data => {
      setEmails(data.items || [])
      setTotal(data.total || 0)
      setPages(data.pages || 1)
      setPage(pg)
      setLoading(false)
    })
  }
  useEffect(() => { fetch_() }, [deviceId, unlocked])

  return (
    <div>
      <div className="topbar">
        <div>
          <div className="topbar-title"><Mail size={16} style={{marginRight:8}} />Emails</div>
          <div className="topbar-subtitle">{total} emails — Device #{deviceId}</div>
        </div>
        <div className="topbar-actions">
          <div className="input-group" style={{ width:220 }}>
            <Search size={14} className="input-icon" />
            <input className="input" placeholder="Search subject or sender…" value={search}
              onChange={e => { setSearch(e.target.value); fetch_(1, e.target.value) }} />
          </div>
        </div>
      </div>
      <div className="page-content" style={{ display:'flex', gap:16, padding:16, height:'calc(100vh - 60px)', overflow:'hidden' }}>
        {/* Email List */}
        <div style={{ flex:'0 0 400px', overflowY:'auto', display:'flex', flexDirection:'column', gap:6 }}>
          {loading ? <div className="empty-state"><div className="spinner"/></div>
          : emails.length === 0 ? <div className="empty-state"><div className="empty-state-icon">📧</div><div className="empty-state-text">No emails</div></div>
          : emails.map(e => (
            <div key={e.id} onClick={() => setSelected(e)}
              style={{
                padding:'12px 14px', borderRadius:10, cursor:'pointer',
                background: selected?.id===e.id ? 'var(--cyan-faint)' : 'var(--bg-card)',
                border: `1px solid ${selected?.id===e.id ? 'var(--cyan)' : 'var(--border)'}`,
                transition:'var(--transition)',
              }}>
              <div style={{ fontWeight:600, fontSize:13, overflow:'hidden', textOverflow:'ellipsis', whiteSpace:'nowrap', color: selected?.id===e.id ? 'var(--cyan)' : 'var(--text-primary)' }}>
                {e.subject || '(No Subject)'}
              </div>
              <div style={{ fontSize:11, color:'var(--text-muted)', marginTop:2 }}>From: {e.sender}</div>
              <div style={{ display:'flex', gap:6, marginTop:5, alignItems:'center' }}>
                <span className={`badge ${e.folder==='sent' ? 'badge-cyan' : 'badge-muted'}`}>{e.folder}</span>
                {e.has_attachments && <span className="badge badge-orange">📎 Attachment</span>}
                <span style={{ fontSize:10, color:'var(--text-muted)', marginLeft:'auto' }}>{e.timestamp?.slice(0,10) || ''}</span>
              </div>
            </div>
          ))}
          {pages > 1 && (
            <div className="pagination" style={{ padding:'8px 0' }}>
              <button className="btn btn-secondary btn-sm" disabled={page<=1} onClick={() => fetch_(page-1)}>←</button>
              <span style={{ fontSize:11, color:'var(--text-muted)' }}>{page}/{pages}</span>
              <button className="btn btn-secondary btn-sm" disabled={page>=pages} onClick={() => fetch_(page+1)}>→</button>
            </div>
          )}
        </div>

        {/* Email Body */}
        <div style={{ flex:1, background:'var(--bg-card)', border:'1px solid var(--border)', borderRadius:12, padding:20, overflowY:'auto' }}>
          {!selected ? (
            <div className="empty-state">
              <div className="empty-state-icon">📧</div>
              <div className="empty-state-text">Select an email to view</div>
            </div>
          ) : (
            <>
              <div style={{ marginBottom:16 }}>
                <div style={{ fontSize:18, fontWeight:700, color:'var(--text-primary)', marginBottom:10 }}>{selected.subject || '(No Subject)'}</div>
                <div style={{ display:'grid', gridTemplateColumns:'80px 1fr', gap:6, fontSize:12 }}>
                  {[
                    ['From', selected.sender],
                    ['To', Array.isArray(selected.recipients) ? selected.recipients.join(', ') : selected.recipients],
                    ['Date', selected.timestamp?.slice(0,19).replace('T',' ')],
                    ['Folder', selected.folder],
                    ['Account', selected.account],
                  ].map(([k,v]) => (
                    <><div key={k+'-k'} style={{ color:'var(--text-muted)', fontWeight:600 }}>{k}:</div><div key={k+'-v'} style={{ color:'var(--text-primary)' }}>{v || '—'}</div></>
                  ))}
                </div>
              </div>
              <hr style={{ border:'none', borderTop:'1px solid var(--border)', margin:'16px 0' }} />
              <div style={{ fontSize:13, color:'var(--text-secondary)', lineHeight:1.7, whiteSpace:'pre-wrap' }}>
                {selected.body || '(No body)'}
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  )
}
