import { useState, useEffect } from 'react'
import { useParams } from 'react-router-dom'
import { MessageSquare, Search } from 'lucide-react'

const ADMIN_KEY = 'case-k-unlocked'

export default function SMSViewer({ API, unlocked }) {
  const { deviceId } = useParams()
  const [messages, setMessages] = useState([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [pages, setPages] = useState(1)
  const [search, setSearch] = useState('')
  const [loading, setLoading] = useState(true)
  const [selectedThread, setSelectedThread] = useState(null)

  const fetchSMS = (pg=1, sq=search) => {
    setLoading(true)
    let url = `${API}/api/evidence/${deviceId}/sms?page=${pg}&per_page=100`
    if (sq) url += `&search=${encodeURIComponent(sq)}`
    const headers = unlocked ? { 'X-Admin-Key': ADMIN_KEY } : {}
    fetch(url, { headers }).then(r=>r.json()).then(data => {
      setMessages(data.items || [])
      setTotal(data.total || 0)
      setPages(data.pages || 1)
      setPage(pg)
      setLoading(false)
    })
  }
  useEffect(() => { fetchSMS() }, [deviceId, unlocked])

  // Group by thread or address
  const threads = {}
  messages.forEach(m => {
    const key = m.thread_id || m.address || 'Unknown'
    if (!threads[key]) threads[key] = { id: key, address: m.address, name: m.contact_name, messages: [] }
    threads[key].messages.push(m)
  })
  const threadList = Object.values(threads).sort((a,b) => {
    const ta = a.messages[0]?.timestamp || ''
    const tb = b.messages[0]?.timestamp || ''
    return tb.localeCompare(ta)
  })
  const threadMsgs = selectedThread ? (threads[selectedThread]?.messages || []).sort((a,b) => (a.timestamp||'').localeCompare(b.timestamp||'')) : []

  return (
    <div>
      <div className="topbar">
        <div>
          <div className="topbar-title"><MessageSquare size={16} style={{mr:8}} /> SMS / MMS</div>
          <div className="topbar-subtitle">{total} messages — Device #{deviceId}</div>
        </div>
        <div className="topbar-actions">
          <div className="input-group" style={{ width:220 }}>
            <Search size={14} className="input-icon" />
            <input className="input" placeholder="Search messages…" value={search}
              onChange={e => { setSearch(e.target.value); fetchSMS(1, e.target.value) }} />
          </div>
        </div>
      </div>
      <div className="page-content" style={{ padding:0, display:'flex', height:'calc(100vh - 60px)', overflow:'hidden' }}>
        {/* Thread list */}
        <div style={{ width:280, minWidth:280, borderRight:'1px solid var(--border)', overflowY:'auto', background:'var(--bg-secondary)' }}>
          {loading ? (
            <div className="empty-state" style={{ padding:30 }}><div className="spinner" /></div>
          ) : threadList.length === 0 ? (
            <div className="empty-state" style={{ padding:30 }}>
              <div className="empty-state-icon">💬</div>
              <div className="empty-state-text">No SMS records</div>
            </div>
          ) : threadList.map(t => (
            <div key={t.id} onClick={() => setSelectedThread(t.id)}
              style={{
                padding:'12px 16px', cursor:'pointer', borderBottom:'1px solid var(--border)',
                background: selectedThread===t.id ? 'var(--cyan-faint)' : 'transparent',
                borderLeft: selectedThread===t.id ? '3px solid var(--cyan)' : '3px solid transparent',
              }}>
              <div style={{ fontWeight:600, fontSize:13, color: selectedThread===t.id ? 'var(--cyan)' : 'var(--text-primary)' }}>
                {t.name || t.address || '(Unknown)'}
              </div>
              <div style={{ fontSize:11, color:'var(--text-muted)', marginTop:2 }}>
                {t.address} · {t.messages.length} msgs
              </div>
              <div style={{ fontSize:11, color:'var(--text-secondary)', marginTop:4, overflow:'hidden', textOverflow:'ellipsis', whiteSpace:'nowrap' }}>
                {t.messages[t.messages.length-1]?.body?.slice(0,50) || ''}
              </div>
            </div>
          ))}
        </div>

        {/* Message viewer */}
        <div style={{ flex:1, display:'flex', flexDirection:'column', overflow:'hidden' }}>
          {!selectedThread ? (
            <div className="empty-state" style={{ flex:1 }}>
              <div className="empty-state-icon">💬</div>
              <div className="empty-state-text">Select a conversation</div>
            </div>
          ) : (
            <>
              <div style={{ padding:'12px 20px', borderBottom:'1px solid var(--border)', background:'var(--bg-secondary)' }}>
                <div style={{ fontWeight:700, color:'var(--text-primary)' }}>{threads[selectedThread]?.name || threads[selectedThread]?.address}</div>
                <div style={{ fontSize:11, color:'var(--text-muted)' }}>{threads[selectedThread]?.address} · {threadMsgs.length} messages</div>
              </div>
              <div style={{ flex:1, overflowY:'auto', padding:'16px 20px', display:'flex', flexDirection:'column', gap:6 }}>
                {threadMsgs.map(m => (
                  <div key={m.id} style={{ display:'flex', flexDirection:'column', alignItems: m.sms_type==='sent' ? 'flex-end' : 'flex-start' }}>
                    <div className={`sms-bubble ${m.sms_type==='sent' ? 'sent' : 'received'}`}>
                      {m.is_mms && <span className="badge badge-purple" style={{marginBottom:4, fontSize:9}}>MMS{m.mms_subject ? ` — ${m.mms_subject}` : ''}</span>}
                      <div>{m.body || '(empty)'}</div>
                    </div>
                    <div style={{ fontSize:10, color:'var(--text-muted)', margin:'2px 4px' }}>
                      {m.timestamp ? new Date(m.timestamp).toLocaleString() : ''}
                    </div>
                  </div>
                ))}
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  )
}
