import { useState, useEffect } from 'react'
import { useParams } from 'react-router-dom'
import { Clock } from 'lucide-react'

const EVENT_COLORS = {
  call: 'var(--green)', sms: 'var(--cyan)', media: 'var(--orange)',
  app_data: 'var(--purple)', email: 'var(--yellow)', location: 'var(--green-dim)',
}
const EVENT_ICONS = { call: '📞', sms: '💬', media: '📸', app_data: '📱', email: '📧', location: '📍' }

export default function Timeline({ API }) {
  const { deviceId } = useParams()
  const [events, setEvents] = useState([])
  const [total, setTotal] = useState(0)
  const [loading, setLoading] = useState(true)
  const [typeFilter, setTypeFilter] = useState('')
  const [visible, setVisible] = useState(100)

  useEffect(() => {
    fetch(`${API}/api/evidence/${deviceId}/timeline`)
      .then(r => r.json())
      .then(data => {
        setEvents(data.events || [])
        setTotal(data.total || 0)
        setLoading(false)
      })
  }, [deviceId])

  const filtered = typeFilter ? events.filter(e => e.event_type === typeFilter) : events
  const shown = filtered.slice(0, visible)

  return (
    <div>
      <div className="topbar">
        <div>
          <div className="topbar-title"><Clock size={16} style={{marginRight:8}} />Timeline</div>
          <div className="topbar-subtitle">{total} events — unified chronological view</div>
        </div>
        <div className="topbar-actions">
          <select className="select" value={typeFilter} onChange={e => setTypeFilter(e.target.value)}>
            <option value="">All Events</option>
            <option value="call">Calls</option>
            <option value="sms">SMS</option>
            <option value="media">Media</option>
            <option value="app_data">App Data</option>
            <option value="email">Emails</option>
            <option value="location">Locations</option>
          </select>
        </div>
      </div>
      <div className="page-content">
        {loading ? (
          <div className="empty-state"><div className="spinner" /></div>
        ) : filtered.length === 0 ? (
          <div className="empty-state"><div className="empty-state-icon">⏱️</div><div className="empty-state-text">No timeline events</div></div>
        ) : (
          <div className="card">
            <div className="card-header">
              <div className="card-title">Chronological Evidence Feed ({filtered.length} events)</div>
            </div>
            <div className="timeline-feed">
              {shown.map((ev, i) => (
                <div key={i} className="timeline-event">
                  <div className="timeline-dot" style={{ background: `${EVENT_COLORS[ev.event_type] || 'var(--text-muted)'}20` }}>
                    <span style={{ fontSize:14 }}>{EVENT_ICONS[ev.event_type] || '●'}</span>
                  </div>
                  <div className="timeline-content">
                    <div className="timeline-summary">{ev.summary}</div>
                    <div className="timeline-ts">{ev.timestamp?.slice(0,19).replace('T',' ') || ''}</div>
                  </div>
                  <span className="badge" style={{
                    background: `${EVENT_COLORS[ev.event_type]||'var(--text-muted)'}15`,
                    color: EVENT_COLORS[ev.event_type]||'var(--text-muted)',
                    alignSelf: 'flex-start', marginTop: 4, flexShrink: 0
                  }}>{ev.event_type}</span>
                </div>
              ))}
            </div>
            {visible < filtered.length && (
              <div style={{ textAlign:'center', padding:'16px 0' }}>
                <button className="btn btn-secondary" onClick={() => setVisible(v => v + 100)}>
                  Load More ({filtered.length - visible} remaining)
                </button>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
