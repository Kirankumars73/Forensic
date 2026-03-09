import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { Smartphone, Wifi, RefreshCw, Play, CheckCircle, AlertCircle } from 'lucide-react'

export default function DeviceConnect({ API, setDeviceId }) {
  const [adbDevices, setAdbDevices] = useState([])
  const [dbDevices, setDbDevices] = useState([])
  const [cases, setCases] = useState([])
  const [selectedCase, setSelectedCase] = useState('')
  const [selectedSerial, setSelectedSerial] = useState('')
  const [scanning, setScanning] = useState(false)
  const [extracting, setExtractingId] = useState(null)
  const [progress, setProgress] = useState({})
  const navigate = useNavigate()

  const loadCases = () => fetch(`${API}/api/cases`).then(r=>r.json()).then(setCases)
  const loadDbDevices = () => fetch(`${API}/api/devices`).then(r=>r.json()).then(setDbDevices)

  useEffect(() => { loadCases(); loadDbDevices() }, [])

  const scanADB = () => {
    setScanning(true)
    fetch(`${API}/api/devices/list-adb`)
      .then(r => r.json())
      .then(data => { setAdbDevices(data.devices || []); setScanning(false) })
      .catch(() => setScanning(false))
  }

  const startExtraction = () => {
    if (!selectedCase || !selectedSerial) return
    fetch(`${API}/api/devices/extract`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ case_id: parseInt(selectedCase), serial: selectedSerial }),
    }).then(r => r.json()).then(data => {
      const devId = data.device_id
      setExtractingId(devId)
      setDeviceId(devId)
      // Poll status
      const poll = setInterval(() => {
        fetch(`${API}/api/devices/extract/status/${devId}`)
          .then(r => r.json())
          .then(st => {
            setProgress(p => ({ ...p, [devId]: st }))
            if (st.done) {
              clearInterval(poll)
              loadDbDevices()
              if (!st.error) setTimeout(() => navigate(`/evidence/${devId}/calls`), 1000)
            }
          })
      }, 1500)
    })
  }

  const STATUS_ICON = { completed: <CheckCircle size={14} color="var(--green)" />, failed: <AlertCircle size={14} color="var(--red)" />, in_progress: <span className="spinner" style={{width:12,height:12}} />, pending: null }

  return (
    <div>
      <div className="topbar">
        <div>
          <div className="topbar-title"><Smartphone size={16} style={{marginRight:8}} />Device Connection & Extraction</div>
          <div className="topbar-subtitle">Connect Android device via USB/OTG with ADB (USB Debugging enabled)</div>
        </div>
      </div>
      <div className="page-content">
        <div style={{ display:'grid', gridTemplateColumns:'1fr 1fr', gap:16 }}>

          {/* ADB Scanner */}
          <div className="card">
            <div className="card-header">
              <div className="card-title">📱 ADB Device Scanner</div>
              <button className="btn btn-secondary btn-sm" onClick={scanADB} disabled={scanning}>
                <RefreshCw size={12} className={scanning ? 'spin' : ''} /> {scanning ? 'Scanning…' : 'Scan'}
              </button>
            </div>
            <div className="alert alert-info" style={{ marginBottom:12 }}>
              <span>ℹ️</span>
              <div style={{ fontSize:11 }}>
                <b>Requirements:</b> Android phone with <b>USB Debugging enabled</b> → Settings → Developer Options → USB Debugging.<br/>
                Connect via USB or OTG cable. Accept the ADB authorization prompt on the phone.
              </div>
            </div>
            {adbDevices.length === 0 ? (
              <div className="empty-state" style={{ padding:'20px 0' }}>
                <div className="empty-state-icon">🔌</div>
                <div className="empty-state-text">No ADB devices detected</div>
                <div className="empty-state-sub">Click Scan after connecting device</div>
              </div>
            ) : adbDevices.map(d => (
              <div key={d.serial} onClick={() => setSelectedSerial(d.serial)}
                style={{
                  padding:'12px 14px', borderRadius:10, cursor:'pointer', marginBottom:8,
                  background: selectedSerial===d.serial ? 'var(--cyan-faint)' : 'var(--bg-elevated)',
                  border: `1px solid ${selectedSerial===d.serial ? 'var(--cyan)' : 'var(--border)'}`,
                }}>
                <div style={{ fontWeight:700, color: selectedSerial===d.serial ? 'var(--cyan)' : 'var(--text-primary)' }}>
                  {d.model || d.serial}
                </div>
                <div style={{ fontSize:11, fontFamily:'monospace', color:'var(--text-muted)', marginTop:3 }}>{d.serial}</div>
                {d.transport && <span className="badge badge-green" style={{marginTop:6}}>Connected</span>}
              </div>
            ))}
          </div>

          {/* Extraction Config */}
          <div className="card">
            <div className="card-header">
              <div className="card-title">⚙️ Extraction Configuration</div>
            </div>
            <div className="form-group">
              <label className="form-label">Select Case</label>
              <select className="select" value={selectedCase} onChange={e => setSelectedCase(e.target.value)} style={{ width:'100%' }}>
                <option value="">— Select a case —</option>
                {cases.map(c => <option key={c.id} value={c.id}>{c.case_number} – {c.title}</option>)}
              </select>
            </div>
            <div className="form-group">
              <label className="form-label">Device Serial (from scan)</label>
              <input className="input" placeholder="e.g. R58M30ABCDE (auto-filled from scan)" value={selectedSerial}
                onChange={e => setSelectedSerial(e.target.value)} />
            </div>
            <div style={{ background:'var(--bg-elevated)', borderRadius:10, padding:12, marginBottom:14 }}>
              <div style={{ fontSize:12, fontWeight:700, color:'var(--text-secondary)', marginBottom:8 }}>Extraction will include:</div>
              {['Call logs', 'SMS / MMS', 'Contacts', 'Photos & Videos (with EXIF/GPS)', 'WhatsApp DB', 'Browser history', 'Chrome history', 'Gmail / Email', 'Location data', 'WiFi networks'].map(item => (
                <div key={item} style={{ fontSize:11, color:'var(--text-secondary)', padding:'2px 0' }}>✓ {item}</div>
              ))}
            </div>
            <button className="btn btn-primary btn-lg" style={{ width:'100%', justifyContent:'center' }}
              onClick={startExtraction} disabled={!selectedCase || !selectedSerial || extracting}>
              <Play size={15} /> Start Full Extraction
            </button>

            {/* Progress */}
            {extracting && progress[extracting] && (
              <div style={{ marginTop:14 }}>
                <div style={{ display:'flex', justifyContent:'space-between', fontSize:12, marginBottom:6 }}>
                  <span style={{ color:'var(--text-secondary)' }}>Step: {progress[extracting].step}</span>
                  <span style={{ color:'var(--cyan)' }}>{progress[extracting].progress}%</span>
                </div>
                <div className="progress-bar-wrap">
                  <div className="progress-bar-fill" style={{ width:`${progress[extracting].progress}%` }} />
                </div>
                {progress[extracting].done && !progress[extracting].error && (
                  <div className="alert alert-success" style={{ marginTop:10 }}>
                    ✅ Extraction complete! Redirecting to evidence…
                  </div>
                )}
                {progress[extracting].error && (
                  <div className="alert alert-danger" style={{ marginTop:10 }}>
                    ❌ Error: {progress[extracting].error}
                  </div>
                )}
              </div>
            )}
          </div>
        </div>

        {/* Previously extracted devices */}
        {dbDevices.length > 0 && (
          <div className="card" style={{ marginTop:16 }}>
            <div className="card-header">
              <div className="card-title">📋 Previously Extracted Devices</div>
            </div>
            <div className="table-wrapper">
              <table>
                <thead><tr><th>ID</th><th>Model</th><th>IMEI</th><th>Android</th><th>Status</th><th>Acquired</th><th></th></tr></thead>
                <tbody>
                  {dbDevices.map(d => (
                    <tr key={d.id}>
                      <td className="mono">#{d.id}</td>
                      <td style={{ fontWeight:500 }}>{d.manufacturer} {d.model || '—'}</td>
                      <td className="mono">{d.imei || '—'}</td>
                      <td className="muted">{d.android_version || '—'}</td>
                      <td>
                        <span className={`badge badge-${d.acquisition_status==='completed'?'green':d.acquisition_status==='in_progress'?'cyan':'red'}`}>
                          {STATUS_ICON[d.acquisition_status]} {d.acquisition_status}
                        </span>
                      </td>
                      <td className="muted">{d.acquired_at?.slice(0,10) || '—'}</td>
                      <td>
                        <button className="btn btn-secondary btn-sm" onClick={() => { setDeviceId(d.id); navigate(`/evidence/${d.id}/calls`) }}>
                          Open Evidence →
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
