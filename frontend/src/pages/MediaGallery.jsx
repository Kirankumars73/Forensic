import { useState, useEffect } from 'react'
import { useParams } from 'react-router-dom'
import { Image, MapPin, X } from 'lucide-react'

const ADMIN_KEY = 'case-k-unlocked'

export default function MediaGallery({ API, unlocked }) {
  const { deviceId } = useParams()
  const [media, setMedia] = useState([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [pages, setPages] = useState(1)
  const [filter, setFilter] = useState('')
  const [gpsOnly, setGpsOnly] = useState(false)
  const [loading, setLoading] = useState(true)
  const [selected, setSelected] = useState(null)

  const fetch_ = (pg=1, ft=filter, gps=gpsOnly) => {
    setLoading(true)
    let url = `${API}/api/evidence/${deviceId}/media?page=${pg}&per_page=60`
    if (ft) url += `&type=${ft}`
    if (gps) url += `&has_gps=true`
    const headers = unlocked ? { 'X-Admin-Key': ADMIN_KEY } : {}
    fetch(url, { headers }).then(r=>r.json()).then(data => {
      setMedia(data.items || [])
      setTotal(data.total || 0)
      setPages(data.pages || 1)
      setPage(pg)
      setLoading(false)
    })
  }
  useEffect(() => { fetch_() }, [deviceId, unlocked])

  const fileIcon = (type) => type === 'photo' ? '🖼️' : type === 'video' ? '🎥' : type === 'audio' ? '🎵' : '📄'

  return (
    <div>
      <div className="topbar">
        <div>
          <div className="topbar-title"><Image size={16} style={{marginRight:8}} />Media Gallery</div>
          <div className="topbar-subtitle">{total} files — Device #{deviceId}</div>
        </div>
        <div className="topbar-actions">
          <select className="select" value={filter} onChange={e => { setFilter(e.target.value); fetch_(1, e.target.value, gpsOnly) }}>
            <option value="">All Types</option>
            <option value="photo">Photos</option>
            <option value="video">Videos</option>
            <option value="audio">Audio</option>
            <option value="document">Documents</option>
          </select>
          <label style={{ display:'flex', alignItems:'center', gap:6, fontSize:12, color:'var(--text-secondary)', cursor:'pointer' }}>
            <input type="checkbox" checked={gpsOnly} onChange={e => { setGpsOnly(e.target.checked); fetch_(1, filter, e.target.checked) }} />
            GPS Only
          </label>
        </div>
      </div>
      <div className="page-content">
        {loading ? (
          <div className="empty-state"><div className="spinner" /></div>
        ) : media.length === 0 ? (
          <div className="empty-state"><div className="empty-state-icon">📷</div><div className="empty-state-text">No media files</div></div>
        ) : (
          <div className="media-grid">
            {media.map(m => (
              <div className="media-card" key={m.id} onClick={() => setSelected(m)}>
                <div className="media-thumb-placeholder">
                  <span style={{ fontSize:28 }}>{fileIcon(m.file_type)}</span>
                </div>
                <div className="media-meta">
                  <div className="media-name">{m.filename}</div>
                  <div className="media-date">{m.timestamp?.slice(0,10) || ''}</div>
                  <div style={{ display:'flex', gap:4, marginTop:4 }}>
                    <span className={`badge badge-${m.file_type==='photo' ? 'cyan' : m.file_type==='video' ? 'red' : 'muted'}`} style={{fontSize:8}}>{m.file_type}</span>
                    {m.gps_latitude && <span className="badge badge-green" style={{fontSize:8}}>📍 GPS</span>}
                    {m.camera_make && <span className="badge badge-muted" style={{fontSize:8}}>{m.camera_make}</span>}
                  </div>
                </div>
              </div>
            ))}
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

      {/* Lightbox Modal */}
      {selected && (
        <div className="modal-overlay" onClick={() => setSelected(null)}>
          <div className="modal" style={{ maxWidth:700 }} onClick={e => e.stopPropagation()}>
            <div className="modal-header">
              <div className="modal-title">{selected.filename}</div>
              <button className="btn btn-secondary btn-sm" onClick={() => setSelected(null)}><X size={14} /></button>
            </div>
            <div style={{ display:'grid', gridTemplateColumns:'1fr 1fr', gap:12, fontSize:12 }}>
              {[
                ['Type', selected.file_type], ['Size', selected.file_size ? `${(selected.file_size/1024/1024).toFixed(2)} MB` : '—'],
                ['Date Taken', selected.timestamp?.slice(0,19).replace('T',' ') || '—'],
                ['Camera', `${selected.camera_make || ''} ${selected.camera_model || ''}`.trim() || '—'],
                ['Resolution', selected.width ? `${selected.width}×${selected.height}` : '—'],
                ['SHA-256', selected.file_hash?.slice(0,24)+'…' || '—'],
                ['GPS Latitude', typeof selected.gps_latitude === 'number' ? selected.gps_latitude.toFixed(6) : '—'],
                ['GPS Longitude', typeof selected.gps_longitude === 'number' ? selected.gps_longitude.toFixed(6) : '—'],
                ['Altitude', selected.gps_altitude ? `${selected.gps_altitude}m` : '—'],
                ['Source Path', selected.source_path || '—'],
              ].map(([k,v]) => (
                <div key={k} style={{ background:'var(--bg-elevated)', borderRadius:8, padding:'10px 12px' }}>
                  <div style={{ fontSize:9, fontWeight:700, color:'var(--text-muted)', textTransform:'uppercase', letterSpacing:'0.08em', marginBottom:4 }}>{k}</div>
                  <div style={{ color:'var(--text-primary)', fontFamily: k==='SHA-256' ? 'monospace' : 'inherit', wordBreak:'break-all' }}>{v}</div>
                </div>
              ))}
            </div>
            {typeof selected.gps_latitude === 'number' && typeof selected.gps_longitude === 'number' && (
              <div style={{ marginTop:12 }}>
                <a href={`https://maps.google.com/?q=${selected.gps_latitude},${selected.gps_longitude}`}
                  target="_blank" rel="noopener noreferrer" className="btn btn-green" style={{ fontSize:12 }}>
                  <MapPin size={13} /> Open GPS Location in Maps
                </a>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
