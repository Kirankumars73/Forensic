import { useState, useEffect } from 'react'
import { useParams } from 'react-router-dom'
import { Shield } from 'lucide-react'

const ADMIN_KEY = 'case-k-unlocked'

export default function AuditLog({ API, unlocked }) {
  const { deviceId } = useParams()
  const [logs, setLogs] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    let url = `${API}/api/audit`
    if (deviceId) url += `?device_id=${deviceId}`
    const headers = unlocked ? { 'X-Admin-Key': ADMIN_KEY } : {}
    fetch(url, { headers }).then(r => r.json()).then(data => {
      setLogs(data)
      setLoading(false)
    }).catch(e => {
      console.error("Audit log fetch failed:", e)
      setLoading(false)
    })
  }, [deviceId, unlocked])

  return (
    <div>
      <div className="topbar">
        <div>
          <div className="topbar-title"><Shield size={16} style={{marginRight:8}} />Chain of Custody / Audit Log</div>
          <div className="topbar-subtitle">{logs.length} immutable log entries</div>
        </div>
        <div className="topbar-actions">
          <span className="badge badge-green">🔒 Tamper-Evident</span>
        </div>
      </div>
      <div className="page-content">
        <div className="alert alert-info" style={{ marginBottom:16 }}>
          <span>🛡️</span>
          <div>
            <b>Chain of Custody:</b> Every action on this evidence is recorded here automatically.
            These logs are immutable and timestamped, forming the legal chain of custody record.
          </div>
        </div>
        <div className="card" style={{ padding:0 }}>
          {loading ? (
            <div className="empty-state"><div className="spinner" /></div>
          ) : logs.length === 0 ? (
            <div className="empty-state"><div className="empty-state-icon">🔐</div><div className="empty-state-text">No audit logs</div></div>
          ) : (
            <div className="table-wrapper">
              <table>
                <thead><tr><th>#</th><th>Timestamp (UTC)</th><th>Action</th><th>Actor</th><th>Case ID</th><th>Device ID</th><th>Details</th></tr></thead>
                <tbody>
                  {logs.map((log, i) => (
                    <tr key={log.id}>
                      <td className="muted">{i+1}</td>
                      <td className="mono">{log.timestamp?.slice(0,19).replace('T',' ') || '—'}</td>
                      <td>
                        <span className="badge badge-cyan">{log.action}</span>
                      </td>
                      <td style={{ fontWeight:500 }}>{log.actor || 'system'}</td>
                      <td className="muted">{log.case_id || '—'}</td>
                      <td className="muted">{log.device_id || '—'}</td>
                      <td style={{ fontSize:12, color:'var(--text-secondary)', maxWidth:300 }}>
                        <div style={{ overflow:'hidden', textOverflow:'ellipsis', whiteSpace:'nowrap' }}>
                          {log.details || '—'}
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
