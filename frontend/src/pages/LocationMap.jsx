import { useState, useEffect, useRef } from 'react'
import { useParams } from 'react-router-dom'
import { MapPin } from 'lucide-react'

export default function LocationMap({ API }) {
  const { deviceId } = useParams()
  const [locations, setLocations] = useState([])
  const [loading, setLoading] = useState(true)
  const mapRef = useRef(null)
  const leafletMap = useRef(null)

  useEffect(() => {
    fetch(`${API}/api/evidence/${deviceId}/locations`)
      .then(r => r.json())
      .then(data => {
        setLocations(data)
        setLoading(false)
      })
  }, [deviceId])

  useEffect(() => {
    if (loading || leafletMap.current) return
    if (typeof window === 'undefined') return
    // Dynamically load Leaflet CSS + JS
    const loadLeaflet = async () => {
      if (!window.L) {
        const link = document.createElement('link')
        link.rel = 'stylesheet'
        link.href = 'https://unpkg.com/leaflet@1.9.4/dist/leaflet.css'
        document.head.appendChild(link)
        await new Promise((resolve) => {
          const script = document.createElement('script')
          script.src = 'https://unpkg.com/leaflet@1.9.4/dist/leaflet.js'
          script.onload = resolve
          document.head.appendChild(script)
        })
      }
      const L = window.L
      if (!mapRef.current || leafletMap.current) return
      const map = L.map(mapRef.current, {
        center: locations.length ? [locations[0].latitude, locations[0].longitude] : [20.5937, 78.9629],
        zoom: locations.length ? 10 : 5,
      })
      L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
        attribution: '©OpenStreetMap ©CartoDB',
        subdomains: 'abcd', maxZoom: 19,
      }).addTo(map)

      const SOURCE_COLORS = {
        photo_exif: '#ff9100', gps: '#00e676', network: '#00e5ff',
        wifi: '#7c4dff', gps_provider: '#ffd600',
      }

      locations.forEach(loc => {
        const color = SOURCE_COLORS[loc.source] || '#00e5ff'
        const marker = L.circleMarker([loc.latitude, loc.longitude], {
          radius: 6, fillColor: color, color: '#000', weight: 1, opacity: 0.8, fillOpacity: 0.9
        }).addTo(map)
        marker.bindPopup(`
          <div style="font-family:sans-serif;font-size:12px;">
            <b>${loc.source || 'location'}</b><br/>
            Lat: ${loc.latitude.toFixed(6)}, Lon: ${loc.longitude.toFixed(6)}<br/>
            ${loc.source_ref ? `Ref: ${loc.source_ref}<br/>` : ''}
            ${loc.timestamp ? `Time: ${loc.timestamp.slice(0,19).replace('T',' ')}` : ''}
          </div>
        `)
      })
      leafletMap.current = map
    }
    loadLeaflet()
  }, [loading, locations])

  const srcGroups = {}
  locations.forEach(l => { srcGroups[l.source] = (srcGroups[l.source] || 0) + 1 })

  const SRC_COLORS = { photo_exif:'var(--orange)', gps:'var(--green)', network:'var(--cyan)', wifi:'var(--purple)', gps_provider:'var(--yellow)' }

  return (
    <div>
      <div className="topbar">
        <div>
          <div className="topbar-title"><MapPin size={16} style={{marginRight:8}} />Location Map</div>
          <div className="topbar-subtitle">{locations.length} location pins — Device #{deviceId}</div>
        </div>
        <div className="topbar-actions" style={{ gap:6 }}>
          {Object.entries(srcGroups).map(([src, count]) => (
            <span key={src} className="badge" style={{ background:`${SRC_COLORS[src] || 'var(--text-muted)'}15`, color: SRC_COLORS[src] || 'var(--text-muted)' }}>
              {src}: {count}
            </span>
          ))}
        </div>
      </div>
      <div className="page-content">
        {loading ? (
          <div className="empty-state"><div className="spinner" /><div className="empty-state-text">Loading locations…</div></div>
        ) : locations.length === 0 ? (
          <div className="empty-state"><div className="empty-state-icon">🗺️</div><div className="empty-state-text">No location data extracted</div></div>
        ) : (
          <>
            <div ref={mapRef} className="map-container" style={{ marginBottom:16 }} />
            <div className="card" style={{ padding:0 }}>
              <div className="table-wrapper">
                <table>
                  <thead><tr><th>#</th><th>Latitude</th><th>Longitude</th><th>Source</th><th>Reference</th><th>Time</th><th>Address</th></tr></thead>
                  <tbody>
                    {locations.slice(0,100).map((l,i) => (
                      <tr key={l.id}>
                        <td className="muted">{i+1}</td>
                        <td className="mono">{l.latitude?.toFixed(6)}</td>
                        <td className="mono">{l.longitude?.toFixed(6)}</td>
                        <td><span className="badge" style={{ background:`${SRC_COLORS[l.source]||'var(--text-muted)'}15`, color: SRC_COLORS[l.source]||'var(--text-muted)' }}>{l.source}</span></td>
                        <td className="muted">{l.source_ref?.slice(0,30) || '—'}</td>
                        <td className="muted">{l.timestamp?.slice(0,16).replace('T',' ') || '—'}</td>
                        <td className="muted">{l.address || '—'}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  )
}
