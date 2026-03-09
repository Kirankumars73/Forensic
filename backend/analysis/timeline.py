"""
Timeline analysis module: merges all evidence into a unified chronological feed.
"""
import datetime


def build_timeline(device_id, call_logs=None, sms_messages=None, media_files=None,
                   app_data=None, emails=None, locations=None):
    """
    Merge all evidence types into a single sorted timeline list.
    Each entry: { timestamp, event_type, summary, device_id, source_id }
    """
    events = []

    for c in (call_logs or []):
        ts = c.get("timestamp")
        if not ts:
            continue
        events.append({
            "timestamp": ts.isoformat() if hasattr(ts, "isoformat") else str(ts),
            "event_type": "call",
            "summary": f"{c.get('call_type','call').capitalize()} call {'from' if c.get('call_type')=='incoming' else 'to'} {c.get('number') or 'Unknown'} ({c.get('duration_formatted','?')})",
            "device_id": device_id,
            "source_id": c.get("id"),
            "icon": "phone",
            "metadata": {"number": c.get("number"), "type": c.get("call_type"), "duration": c.get("duration_seconds")},
        })

    for s in (sms_messages or []):
        ts = s.get("timestamp")
        if not ts:
            continue
        body = (s.get("body") or "")[:80]
        events.append({
            "timestamp": ts.isoformat() if hasattr(ts, "isoformat") else str(ts),
            "event_type": "sms",
            "summary": f"SMS {s.get('sms_type','')}: {s.get('address','')} — \"{body}\"",
            "device_id": device_id,
            "source_id": s.get("id"),
            "icon": "message-square",
            "metadata": {"address": s.get("address"), "type": s.get("sms_type")},
        })

    for m in (media_files or []):
        ts = m.get("timestamp")
        if not ts:
            continue
        events.append({
            "timestamp": ts.isoformat() if hasattr(ts, "isoformat") else str(ts),
            "event_type": "media",
            "summary": f"📸 {m.get('file_type','file').capitalize()}: {m.get('filename','')}",
            "device_id": device_id,
            "source_id": m.get("id"),
            "icon": "image",
            "metadata": {"filename": m.get("filename"), "type": m.get("file_type"),
                         "lat": m.get("gps_latitude"), "lon": m.get("gps_longitude")},
        })

    for a in (app_data or []):
        ts = a.get("timestamp")
        if not ts:
            continue
        content = (a.get("content") or "")[:60]
        events.append({
            "timestamp": ts.isoformat() if hasattr(ts, "isoformat") else str(ts),
            "event_type": "app_data",
            "summary": f"[{a.get('app_name','app').upper()}] {a.get('sender','')} → {a.get('recipient','')}: \"{content}\"",
            "device_id": device_id,
            "source_id": a.get("id"),
            "icon": "message-circle",
            "metadata": {"app": a.get("app_name"), "type": a.get("data_type")},
        })

    for e in (emails or []):
        ts = e.get("timestamp")
        if not ts:
            continue
        events.append({
            "timestamp": ts.isoformat() if hasattr(ts, "isoformat") else str(ts),
            "event_type": "email",
            "summary": f"📧 Email: {e.get('subject','(no subject)')} from {e.get('sender','')}",
            "device_id": device_id,
            "source_id": e.get("id"),
            "icon": "mail",
            "metadata": {"sender": e.get("sender"), "subject": e.get("subject")},
        })

    for loc in (locations or []):
        ts = loc.get("timestamp")
        if not ts:
            continue
        events.append({
            "timestamp": ts.isoformat() if hasattr(ts, "isoformat") else str(ts),
            "event_type": "location",
            "summary": f"📍 Location: {loc.get('latitude'):.4f}, {loc.get('longitude'):.4f} ({loc.get('source','')})",
            "device_id": device_id,
            "source_id": loc.get("id"),
            "icon": "map-pin",
            "metadata": {"lat": loc.get("latitude"), "lon": loc.get("longitude"), "source": loc.get("source")},
        })

    # Sort by timestamp descending (most recent first)
    events.sort(key=lambda x: x.get("timestamp") or "", reverse=True)
    return events


def keyword_search(keyword, call_logs=None, sms_messages=None, app_data=None, emails=None):
    """Search all text fields for a keyword. Returns list of hit dicts."""
    kw = keyword.lower()
    hits = []

    for c in (call_logs or []):
        if kw in str(c.get("number", "")).lower() or kw in str(c.get("name", "")).lower():
            hits.append({"type": "call", "field": "number/name", "value": c.get("number"), "record": c})

    for s in (sms_messages or []):
        if kw in str(s.get("body", "")).lower() or kw in str(s.get("address", "")).lower():
            body = s.get("body", "")
            idx = body.lower().find(kw)
            snippet = body[max(0, idx - 30): idx + 60] if idx >= 0 else body[:80]
            hits.append({"type": "sms", "field": "body", "value": snippet, "record": s})

    for a in (app_data or []):
        content = str(a.get("content", "")).lower()
        if kw in content:
            raw = a.get("content", "")
            idx = raw.lower().find(kw)
            snippet = raw[max(0, idx - 30): idx + 80]
            hits.append({"type": "app_data", "field": "content", "value": snippet, "record": a})

    for e in (emails or []):
        if kw in str(e.get("subject", "")).lower() or kw in str(e.get("body", "")).lower():
            hits.append({"type": "email", "field": "subject/body", "value": e.get("subject"), "record": e})

    return hits
