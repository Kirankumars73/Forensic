import { useState, useEffect } from 'react'
import { BrowserRouter, Routes, Route, NavLink, useNavigate } from 'react-router-dom'
import {
  LayoutDashboard, Folder, Smartphone, Phone, MessageSquare,
  Users, Image, AppWindow, Mail, MapPin, Clock, Search,
  FileText, Shield, ChevronRight, Activity, Lock, Unlock
} from 'lucide-react'
import Dashboard from './pages/Dashboard.jsx'
import Cases from './pages/Cases.jsx'
import DeviceConnect from './pages/DeviceConnect.jsx'
import CallLogs from './pages/CallLogs.jsx'
import SMSViewer from './pages/SMSViewer.jsx'
import Contacts from './pages/Contacts.jsx'
import MediaGallery from './pages/MediaGallery.jsx'
import AppDataPage from './pages/AppDataPage.jsx'
import EmailsPage from './pages/EmailsPage.jsx'
import LocationMap from './pages/LocationMap.jsx'
import Timeline from './pages/Timeline.jsx'
import KeywordSearch from './pages/KeywordSearch.jsx'
import AuditLog from './pages/AuditLog.jsx'
import ReportPage from './pages/ReportPage.jsx'

const API = 'http://localhost:5000'

function Sidebar({ deviceId, unlocked }) {
  const navItems = [
    { label: 'Overview', icon: LayoutDashboard, path: '/' },
    { label: 'Cases', icon: Folder, path: '/cases' },
    { label: 'Device / Extract', icon: Smartphone, path: '/device' },
  ]
  const evidenceItems = deviceId ? [
    { label: 'Call Logs', icon: Phone, path: `/evidence/${deviceId}/calls` },
    { label: 'SMS / MMS', icon: MessageSquare, path: `/evidence/${deviceId}/sms` },
    { label: 'Contacts', icon: Users, path: `/evidence/${deviceId}/contacts` },
    { label: 'Media Gallery', icon: Image, path: `/evidence/${deviceId}/media` },
    { label: 'App Data', icon: AppWindow, path: `/evidence/${deviceId}/apps` },
    { label: 'Emails', icon: Mail, path: `/evidence/${deviceId}/emails` },
    { label: 'Location Map', icon: MapPin, path: `/evidence/${deviceId}/locations` },
    { label: 'Timeline', icon: Clock, path: `/evidence/${deviceId}/timeline` },
    { label: 'Keyword Search', icon: Search, path: `/evidence/${deviceId}/search` },
  ] : []

  const toolItems = deviceId ? [
    { label: 'Audit Log', icon: Shield, path: `/evidence/${deviceId}/audit` },
    { label: 'Generate Report', icon: FileText, path: `/evidence/${deviceId}/report` },
  ] : [
    { label: 'Audit Log', icon: Shield, path: `/audit` },
  ]

  return (
    <aside className="sidebar">
      <div className="sidebar-logo">
        <div className="sidebar-logo-icon">🔍</div>
        <div>
          <div className="sidebar-logo-text">ForensicX</div>
          <div className="sidebar-logo-sub">Mobile Forensics Platform</div>
        </div>
      </div>
      <nav className="sidebar-nav">
        <div className="sidebar-section-label">Navigation</div>
        {navItems.map(({ label, icon: Icon, path }) => (
          <NavLink key={path} to={path} end className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}>
            <Icon size={15} />
            {label}
          </NavLink>
        ))}
        {evidenceItems.length > 0 && (
          <>
            <div className="sidebar-section-label" style={{ marginTop: 8 }}>Evidence (Device #{deviceId})</div>
            {evidenceItems.map(({ label, icon: Icon, path }) => (
              <NavLink key={path} to={path} className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}>
                <Icon size={15} />
                {label}
              </NavLink>
            ))}
          </>
        )}
        <div className="sidebar-section-label" style={{ marginTop: 8 }}>Tools</div>
        {toolItems.map(({ label, icon: Icon, path }) => (
          <NavLink key={path} to={path} className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}>
            <Icon size={15} />
            {label}
          </NavLink>
        ))}
      </nav>
      <div style={{ padding: '12px 16px', borderTop: '1px solid var(--border)' }}>
        <div style={{
          display: 'flex', alignItems: 'center', gap: 6, fontSize: 10,
          color: unlocked ? 'var(--green)' : 'var(--red)',
          fontWeight: 600, marginBottom: 4
        }}>
          {unlocked ? <Unlock size={12} /> : <Lock size={12} />}
          {unlocked ? '🔓 Data Unlocked' : '🔒 Data Locked (Hashed)'}
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 10, color: 'var(--text-muted)' }}>
          <Activity size={12} />
          ForensicX v2.0 — Python/Flask + React
        </div>
      </div>
    </aside>
  )
}

export default function App() {
  const [deviceId, setDeviceIdRaw] = useState(() => {
    const saved = localStorage.getItem('forensicx_device_id')
    return saved ? parseInt(saved) : null
  })
  const [unlocked, setUnlocked] = useState(false)

  const setDeviceId = (id) => {
    setDeviceIdRaw(id)
    if (id) localStorage.setItem('forensicx_device_id', id)
    else localStorage.removeItem('forensicx_device_id')
  }

  // Auto-select first completed device if none stored
  useEffect(() => {
    if (!deviceId) {
      fetch(`${API}/api/devices`)
        .then(r => r.json())
        .then(devs => {
          const best = devs.find(d => d.acquisition_status === 'completed') || devs[0]
          if (best) setDeviceId(best.id)
        })
        .catch(() => {})
    }
  }, [])

  return (
    <BrowserRouter>
      <div className="app-layout">
        <Sidebar deviceId={deviceId} unlocked={unlocked} />
        <div className="main-area">
          <Routes>
            <Route path="/" element={<Dashboard deviceId={deviceId} setDeviceId={setDeviceId} API={API} unlocked={unlocked} setUnlocked={setUnlocked} />} />
            <Route path="/cases" element={<Cases API={API} setDeviceId={setDeviceId} unlocked={unlocked} />} />
            <Route path="/device" element={<DeviceConnect API={API} setDeviceId={setDeviceId} />} />
            <Route path="/evidence/:deviceId/calls" element={<CallLogs API={API} unlocked={unlocked} />} />
            <Route path="/evidence/:deviceId/sms" element={<SMSViewer API={API} unlocked={unlocked} />} />
            <Route path="/evidence/:deviceId/contacts" element={<Contacts API={API} unlocked={unlocked} />} />
            <Route path="/evidence/:deviceId/media" element={<MediaGallery API={API} unlocked={unlocked} />} />
            <Route path="/evidence/:deviceId/apps" element={<AppDataPage API={API} unlocked={unlocked} />} />
            <Route path="/evidence/:deviceId/emails" element={<EmailsPage API={API} unlocked={unlocked} />} />
            <Route path="/evidence/:deviceId/locations" element={<LocationMap API={API} unlocked={unlocked} />} />
            <Route path="/evidence/:deviceId/timeline" element={<Timeline API={API} unlocked={unlocked} />} />
            <Route path="/evidence/:deviceId/search" element={<KeywordSearch API={API} unlocked={unlocked} />} />
            <Route path="/evidence/:deviceId/audit" element={<AuditLog API={API} unlocked={unlocked} />} />
            <Route path="/evidence/:deviceId/report" element={<ReportPage API={API} />} />
            <Route path="/audit" element={<AuditLog API={API} unlocked={unlocked} />} />
          </Routes>
        </div>
      </div>
    </BrowserRouter>
  )
}
