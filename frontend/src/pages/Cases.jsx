import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { Folder, Plus, X } from 'lucide-react'

export default function Cases({ API, setDeviceId }) {
  const [cases, setCases] = useState([])
  const [showForm, setShowForm] = useState(false)
  const [devices, setDevices] = useState({})
  const navigate = useNavigate()
  const [form, setForm] = useState({ case_number:'', title:'', investigator:'', agency:'', suspect_name:'', description:'' })

  const load = () => {
    fetch(`${API}/api/cases`).then(r=>r.json()).then(setCases)
    fetch(`${API}/api/devices`).then(r=>r.json()).then(devList => {
      const map = {}
      devList.forEach(d => { if (!map[d.case_id]) map[d.case_id] = []; map[d.case_id].push(d) })
      setDevices(map)
    })
  }
  useEffect(() => { load() }, [])

  const submit = () => {
    fetch(`${API}/api/cases`, {
      method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify(form)
    }).then(r=>r.json()).then(() => { load(); setShowForm(false); setForm({case_number:'',title:'',investigator:'',agency:'',suspect_name:'',description:''}) })
  }

  const openDevice = (d) => { setDeviceId(d.id); navigate(`/evidence/${d.id}/calls`) }

  return (
    <div>
      <div className="topbar">
        <div>
          <div className="topbar-title"><Folder size={16} style={{marginRight:8}} />Cases</div>
          <div className="topbar-subtitle">{cases.length} cases</div>
        </div>
        <div className="topbar-actions">
          <button className="btn btn-primary" onClick={() => setShowForm(true)}>
            <Plus size={14} /> New Case
          </button>
        </div>
      </div>
      <div className="page-content">

        {showForm && (
          <div className="modal-overlay" onClick={() => setShowForm(false)}>
            <div className="modal" onClick={e => e.stopPropagation()}>
              <div className="modal-header">
                <div className="modal-title">Create New Case</div>
                <button className="btn btn-secondary btn-sm" onClick={() => setShowForm(false)}><X size={14} /></button>
              </div>
              <div className="form-row">
                <div className="form-group">
                  <label className="form-label">Case Number</label>
                  <input className="input" placeholder="CASE-2024-001" value={form.case_number}
                    onChange={e => setForm(f => ({...f, case_number: e.target.value}))} />
                </div>
                <div className="form-group">
                  <label className="form-label">Investigator</label>
                  <input className="input" placeholder="Det. Name" value={form.investigator}
                    onChange={e => setForm(f => ({...f, investigator: e.target.value}))} />
                </div>
              </div>
              <div className="form-group">
                <label className="form-label">Case Title</label>
                <input className="input" placeholder="Operation name / case description" value={form.title}
                  onChange={e => setForm(f => ({...f, title: e.target.value}))} />
              </div>
              <div className="form-row">
                <div className="form-group">
                  <label className="form-label">Agency</label>
                  <input className="input" placeholder="Cyber Crime Unit" value={form.agency}
                    onChange={e => setForm(f => ({...f, agency: e.target.value}))} />
                </div>
                <div className="form-group">
                  <label className="form-label">Suspect Name</label>
                  <input className="input" placeholder="Suspect / Subject" value={form.suspect_name}
                    onChange={e => setForm(f => ({...f, suspect_name: e.target.value}))} />
                </div>
              </div>
              <div className="form-group">
                <label className="form-label">Description</label>
                <textarea className="input" rows={3} placeholder="Case notes…" value={form.description}
                  onChange={e => setForm(f => ({...f, description: e.target.value}))} style={{ resize:'vertical' }} />
              </div>
              <button className="btn btn-primary" style={{width:'100%', justifyContent:'center'}} onClick={submit}>
                Create Case
              </button>
            </div>
          </div>
        )}

        <div style={{ display:'flex', flexDirection:'column', gap:12 }}>
          {cases.length === 0 ? (
            <div className="empty-state">
              <div className="empty-state-icon">📁</div>
              <div className="empty-state-text">No cases yet</div>
              <button className="btn btn-primary" onClick={() => setShowForm(true)}>Create First Case</button>
            </div>
          ) : cases.map(c => {
            const devs = devices[c.id] || []
            return (
              <div className="card" key={c.id} style={{ display:'flex', gap:20, alignItems:'flex-start' }}>
                <div style={{ flex:1 }}>
                  <div style={{ display:'flex', gap:8, alignItems:'center', marginBottom:6 }}>
                    <span className="mono" style={{ color:'var(--cyan)', fontWeight:700, fontSize:13 }}>{c.case_number}</span>
                    <span className={`badge badge-${c.status==='open'?'green':'muted'}`}>{c.status}</span>
                  </div>
                  <div style={{ fontWeight:700, fontSize:16, color:'var(--text-primary)', marginBottom:4 }}>{c.title}</div>
                  <div style={{ fontSize:12, color:'var(--text-secondary)', marginBottom:10 }}>
                    Investigator: <b>{c.investigator}</b>
                    {c.agency && <span> · {c.agency}</span>}
                    {c.suspect_name && <span> · Suspect: <b style={{ color:'var(--orange)' }}>{c.suspect_name}</b></span>}
                  </div>
                  {devs.length > 0 && (
                    <div style={{ display:'flex', gap:8, flexWrap:'wrap' }}>
                      {devs.map(d => (
                        <button key={d.id} className="btn btn-secondary btn-sm" onClick={() => openDevice(d)} style={{ fontSize:11 }}>
                          📱 {d.manufacturer || ''} {d.model || `Device #${d.id}`}
                          <span className={`badge badge-${d.acquisition_status==='completed'?'green':'orange'}`} style={{marginLeft:4}}>{d.acquisition_status}</span>
                        </button>
                      ))}
                    </div>
                  )}
                  {devs.length === 0 && (
                    <button className="btn btn-secondary btn-sm" onClick={() => navigate('/device')} style={{ fontSize:11 }}>
                      + Add Device / Extract
                    </button>
                  )}
                </div>
                <div style={{ fontSize:11, color:'var(--text-muted)', whiteSpace:'nowrap' }}>
                  {c.created_at?.slice(0,10)}
                </div>
              </div>
            )
          })}
        </div>
      </div>
    </div>
  )
}
