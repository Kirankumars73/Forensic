import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { BarChart2, Phone, MessageSquare, Users, Image, Mail, MapPin, Activity, Folder, ChevronRight } from 'lucide-react'
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, LineChart, Line, CartesianGrid, Legend } from 'recharts'

export default function Dashboard({ deviceId, setDeviceId, API }) {
  const [cases, setCases] = useState([])
  const [stats, setStats] = useState(null)
  const [loading, setLoading] = useState(true)
  const navigate = useNavigate()

  useEffect(() => {
    fetch(`${API}/api/cases`).then(r => r.json()).then(data => {
      setCases(data)
      setLoading(false)
    }).catch(() => setLoading(false))
    // Auto-select first device
    if (!deviceId) {
      fetch(`${API}/api/devices`).then(r => r.json()).then(devs => {
        const completed = devs.find(d => d.acquisition_status === 'completed') || devs[0]
        if (completed) setDeviceId(completed.id)
      }).catch(() => {})
    }
  }, [])

  useEffect(() => {
    if (!deviceId) return
    fetch(`${API}/api/evidence/${deviceId}/stats`).then(r => r.json()).then(setStats)
  }, [deviceId])

  const statCards = stats ? [
    { label: 'Call Logs', value: stats.calls, icon: Phone, color: 'var(--green)' },
    { label: 'SMS / MMS', value: stats.sms, icon: MessageSquare, color: 'var(--cyan)' },
    { label: 'Contacts', value: stats.contacts, icon: Users, color: 'var(--purple)' },
    { label: 'Photos', value: stats.photos, icon: Image, color: 'var(--orange)' },
    { label: 'Videos', value: stats.videos, icon: Activity, color: 'var(--red)' },
    { label: 'App Data', value: stats.app_data, icon: BarChart2, color: 'var(--yellow)' },
    { label: 'Emails', value: stats.emails, icon: Mail, color: 'var(--cyan-dim)' },
    { label: 'Locations', value: stats.locations, icon: MapPin, color: 'var(--green-dim)' },
  ] : []

  const chartData = stats ? [
    { name: 'Calls', value: stats.calls, fill: '#00e676' },
    { name: 'SMS', value: stats.sms, fill: '#00e5ff' },
    { name: 'Contacts', value: stats.contacts, fill: '#7c4dff' },
    { name: 'Photos', value: stats.photos, fill: '#ff9100' },
    { name: 'Videos', value: stats.videos, fill: '#ff1744' },
    { name: 'App Data', value: stats.app_data, fill: '#ffd600' },
    { name: 'Emails', value: stats.emails, fill: '#00bcd4' },
    { name: 'Locations', value: stats.locations, fill: '#00c853' },
  ] : []

  const CustomTooltip = ({ active, payload, label }) => {
    if (active && payload && payload.length) {
      return (
        <div style={{ background: 'var(--bg-elevated)', border: '1px solid var(--border)', borderRadius: 8, padding: '8px 14px', fontSize: 12 }}>
          <div style={{ color: 'var(--text-muted)' }}>{label}</div>
          <div style={{ color: 'var(--cyan)', fontWeight: 700, fontSize: 16 }}>{payload[0].value}</div>
        </div>
      )
    }
    return null
  }

  return (
    <div>
      {/* Topbar */}
      <div className="topbar">
        <div>
          <div className="topbar-title">🔍 ForensicX Dashboard</div>
          <div className="topbar-subtitle">Mobile Device Evidence Analysis Platform</div>
        </div>
        <div className="topbar-actions">
          {deviceId && (
            <span className="badge badge-green pulse-glow">Device #{deviceId} Active</span>
          )}
          <button className="btn btn-primary btn-sm" onClick={() => navigate('/device')}>+ New Extraction</button>
        </div>
      </div>

      <div className="page-content">
        {/* No device selected */}
        {!deviceId && !loading && (
          <div className="alert alert-info">
            <span>ℹ️</span>
            <div>
              <div style={{ fontWeight: 600 }}>No device selected</div>
              <div style={{ fontSize: 11, marginTop: 3, color: 'var(--text-secondary)' }}>
                Go to <b>Cases</b> to open an existing case, or <b>Device / Extract</b> to start a new extraction.
                Run <code style={{ background:'var(--bg-elevated)', padding:'1px 4px', borderRadius:3 }}>python seed_demo_data.py</code> in the backend to load demo data.
              </div>
            </div>
          </div>
        )}

        {/* Stat Cards */}
        {stats && (
          <>
            <div className="stats-grid">
              {statCards.map(({ label, value, icon: Icon, color }) => (
                <div className="stat-card" key={label}>
                  <div className="stat-icon" style={{ background: `${color}15` }}>
                    <Icon size={18} color={color} />
                  </div>
                  <div className="stat-value">{value?.toLocaleString()}</div>
                  <div className="stat-label">{label}</div>
                </div>
              ))}
            </div>

            {/* Charts */}
            <div className="charts-row">
              <div className="card">
                <div className="card-header">
                  <div className="card-title">Evidence Overview</div>
                </div>
                <ResponsiveContainer width="100%" height={220}>
                  <BarChart data={chartData} barCategoryGap="30%">
                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" />
                    <XAxis dataKey="name" tick={{ fill: 'var(--text-muted)', fontSize: 10 }} axisLine={false} tickLine={false} />
                    <YAxis tick={{ fill: 'var(--text-muted)', fontSize: 10 }} axisLine={false} tickLine={false} />
                    <Tooltip content={<CustomTooltip />} />
                    <Bar dataKey="value" radius={[4, 4, 0, 0]}>
                      {chartData.map((entry, i) => (
                        <rect key={i} fill={entry.fill} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>
              <div className="card">
                <div className="card-header">
                  <div className="card-title">Quick Navigation</div>
                </div>
                <div style={{ display:'flex', flexDirection:'column', gap:8 }}>
                  {[
                    { label: 'View Call Logs', path: `/evidence/${deviceId}/calls`, color: 'var(--green)' },
                    { label: 'Browse SMS Messages', path: `/evidence/${deviceId}/sms`, color: 'var(--cyan)' },
                    { label: 'Media Gallery', path: `/evidence/${deviceId}/media`, color: 'var(--orange)' },
                    { label: 'App Data (WhatsApp etc.)', path: `/evidence/${deviceId}/apps`, color: 'var(--purple)' },
                    { label: 'Location Map', path: `/evidence/${deviceId}/locations`, color: 'var(--green-dim)' },
                    { label: 'Timeline', path: `/evidence/${deviceId}/timeline`, color: 'var(--yellow)' },
                    { label: 'Generate PDF Report', path: `/evidence/${deviceId}/report`, color: 'var(--red)' },
                  ].map(({ label, path, color }) => (
                    <button key={path} onClick={() => navigate(path)} className="btn btn-secondary" style={{ justifyContent:'space-between', textAlign:'left' }}>
                      <span style={{ color }}>{label}</span>
                      <ChevronRight size={14} color="var(--text-muted)" />
                    </button>
                  ))}
                </div>
              </div>
            </div>
          </>
        )}

        {/* Cases List */}
        <div className="card">
          <div className="card-header">
            <div className="card-title"><Folder size={13} style={{ marginRight:6 }} />Recent Cases</div>
            <button className="btn btn-secondary btn-sm" onClick={() => navigate('/cases')}>View All</button>
          </div>
          {cases.length === 0 ? (
            <div className="empty-state" style={{ padding:'30px 0' }}>
              <div className="empty-state-text">No cases yet</div>
              <div className="empty-state-sub">Create a case to begin</div>
            </div>
          ) : (
            <div className="table-wrapper">
              <table>
                <thead><tr>
                  <th>Case #</th><th>Title</th><th>Investigator</th><th>Suspect</th><th>Status</th><th>Created</th>
                </tr></thead>
                <tbody>
                  {cases.slice(0, 5).map(c => (
                    <tr key={c.id} style={{ cursor:'pointer' }} onClick={() => navigate('/cases')}>
                      <td className="mono">{c.case_number}</td>
                      <td style={{ fontWeight:500 }}>{c.title}</td>
                      <td className="muted">{c.investigator}</td>
                      <td className="muted">{c.suspect_name || '—'}</td>
                      <td><span className={`badge badge-${c.status === 'open' ? 'green' : 'muted'}`}>{c.status}</span></td>
                      <td className="muted">{c.created_at?.slice(0,10)}</td>
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
