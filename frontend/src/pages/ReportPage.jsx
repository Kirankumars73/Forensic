import { useState } from 'react'
import { useParams } from 'react-router-dom'
import { FileText, Loader } from 'lucide-react'

export default function ReportPage({ API }) {
  const { deviceId } = useParams()
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [success, setSuccess] = useState(false)

  const generate = async () => {
    setLoading(true)
    setError(null)
    setSuccess(false)
    try {
      const res = await fetch(`${API}/api/report/${deviceId}`, { method: 'POST' })
      if (!res.ok) { const d = await res.json(); throw new Error(d.error || 'Report failed'); }
      const blob = await res.blob()
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `forensic_report_device_${deviceId}.pdf`
      a.click()
      URL.revokeObjectURL(url)
      setSuccess(true)
    } catch (e) {
      setError(e.message)
    }
    setLoading(false)
  }

  return (
    <div>
      <div className="topbar">
        <div>
          <div className="topbar-title"><FileText size={16} style={{marginRight:8}} />Generate Forensic Report</div>
          <div className="topbar-subtitle">Professional PDF report with all evidence, chain of custody, and thumbnails</div>
        </div>
      </div>
      <div className="page-content" style={{ maxWidth:600 }}>
        <div className="card">
          <div style={{ fontSize:15, fontWeight:700, marginBottom:12 }}>📄 PDF Forensic Report</div>
          <p style={{ fontSize:13, color:'var(--text-secondary)', lineHeight:1.7, marginBottom:16 }}>
            The generated report includes:
          </p>
          <ul style={{ fontSize:12, color:'var(--text-secondary)', lineHeight:2, marginBottom:20, paddingLeft:18 }}>
            <li>✅ Cover page with case & device metadata</li>
            <li>✅ Evidence summary table (counts of all evidence types)</li>
            <li>✅ Full call log table (up to 100 records)</li>
            <li>✅ SMS / MMS messages (up to 100 records)</li>
            <li>✅ Contacts list (up to 80 contacts)</li>
            <li>✅ Media file inventory with EXIF GPS data</li>
            <li>✅ Photo thumbnails grid (up to 24 thumbnails)</li>
            <li>✅ App data (WhatsApp, browser, social media)</li>
            <li>✅ Email records</li>
            <li>✅ Chain of custody / audit log table</li>
          </ul>
          {error && <div className="alert alert-danger" style={{marginBottom:12}}>❌ {error}</div>}
          {success && <div className="alert alert-success" style={{marginBottom:12}}>✅ Report downloaded successfully!</div>}
          <button className="btn btn-primary btn-lg" onClick={generate} disabled={loading} style={{ width:'100%', justifyContent:'center' }}>
            {loading ? <><span className="spinner" style={{width:16,height:16}} /> Generating PDF…</> : <><FileText size={16} /> Generate & Download PDF Report</>}
          </button>
          <div style={{ fontSize:11, color:'var(--text-muted)', marginTop:10, textAlign:'center' }}>
            Report generation may take 10–30 seconds depending on evidence size.
          </div>
        </div>

        <div className="alert alert-warn" style={{ marginTop:16 }}>
          <span>⚠️</span>
          <div style={{ fontSize:12 }}>
            <b>Legal Notice:</b> This report is intended for authorized forensic investigations only.
            Ensure you have proper legal authorization before distributing this document.
            Chain of custody records are automatically included to support court admissibility.
          </div>
        </div>
      </div>
    </div>
  )
}
