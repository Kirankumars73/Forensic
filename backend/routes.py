"""
Flask REST API Routes - Cases, Devices, Evidence, Reports
"""
import os
import json
import datetime
import threading
import logging

from flask import Blueprint, request, jsonify, send_file, current_app
from models import db, Case, Device, CallLog, SMS, Contact, MediaFile, AppData, Email, Location, AuditLog
from acquisition.adb_extractor import ADBExtractor
from parsers.media_parser import parse_media_file, parse_media_directory
from parsers.sqlite_parser import (
    parse_whatsapp_db, parse_browser_db, parse_sms_db,
    parse_contacts_db, parse_calllog_db, parse_gmail_db
)
from analysis.timeline import build_timeline, keyword_search
from reporting.pdf_generator import generate_report

logger = logging.getLogger(__name__)

ADMIN_KEY = "case-k-unlocked"

def _is_unlocked():
    """Return True if the request includes the valid admin unlock header."""
    return request.headers.get("X-Admin-Key", "") == ADMIN_KEY

def _serialize(obj, unlocked=None):
    """Return plain or hashed dict depending on unlock state."""
    if unlocked is None:
        unlocked = _is_unlocked()
    return obj.to_dict() if unlocked else obj.to_hashed_dict()

# -------------------------
# Blueprint: Admin Unlock
# -------------------------
admin_bp = Blueprint("admin", __name__)

@admin_bp.route("/api/admin/unlock", methods=["POST"])
def check_unlock():
    data = request.get_json() or {}
    passphrase = data.get("passphrase", "").strip().lower()
    if passphrase == "case k":
        return jsonify({"unlocked": True, "key": ADMIN_KEY})
    return jsonify({"unlocked": False}), 401

# -------------------------
# Blueprint: Cases
# -------------------------
cases_bp = Blueprint("cases", __name__)

@cases_bp.route("/api/cases", methods=["GET"])
def list_cases():
    cases = Case.query.order_by(Case.created_at.desc()).all()
    unlocked = _is_unlocked()
    return jsonify([_serialize(c, unlocked) for c in cases])

@cases_bp.route("/api/cases", methods=["POST"])
def create_case():
    data = request.get_json()
    case = Case(
        case_number=data.get("case_number", f"CASE-{datetime.datetime.utcnow().strftime('%Y%m%d%H%M%S')}"),
        title=data.get("title", "Untitled Case"),
        investigator=data.get("investigator", "Unknown"),
        agency=data.get("agency", ""),
        description=data.get("description", ""),
        suspect_name=data.get("suspect_name", ""),
        status=data.get("status", "open"),
    )
    db.session.add(case)
    db.session.commit()
    _log_audit(case.id, None, "CASE_CREATED", f"Case {case.case_number} created")
    return jsonify(case.to_dict()), 201

@cases_bp.route("/api/cases/<int:case_id>", methods=["GET"])
def get_case(case_id):
    case = Case.query.get_or_404(case_id)
    return jsonify(_serialize(case))

@cases_bp.route("/api/cases/<int:case_id>", methods=["PUT"])
def update_case(case_id):
    case = Case.query.get_or_404(case_id)
    data = request.get_json()
    for field in ("title", "investigator", "agency", "description", "suspect_name", "status"):
        if field in data:
            setattr(case, field, data[field])
    case.updated_at = datetime.datetime.utcnow()
    db.session.commit()
    return jsonify(case.to_dict())

@cases_bp.route("/api/cases/<int:case_id>", methods=["DELETE"])
def delete_case(case_id):
    case = Case.query.get_or_404(case_id)
    db.session.delete(case)
    db.session.commit()
    return jsonify({"message": "Case deleted"})

# -------------------------
# Blueprint: Devices
# -------------------------
devices_bp = Blueprint("devices", __name__)

@devices_bp.route("/api/devices/list-adb", methods=["GET"])
def list_adb_devices():
    """List connected ADB devices."""
    adb_path = current_app.config.get("ADB_PATH", "adb")
    result = ADBExtractor.list_devices(adb_path=adb_path)
    return jsonify(result)

@devices_bp.route("/api/devices", methods=["GET"])
def list_devices():
    devs = Device.query.order_by(Device.created_at.desc()).all()
    # Device list used for selection — always return full dict so IDs/status work
    return jsonify([d.to_dict() for d in devs])

@devices_bp.route("/api/devices/<int:device_id>", methods=["GET"])
def get_device(device_id):
    dev = Device.query.get_or_404(device_id)
    return jsonify(_serialize(dev))

_extraction_status = {}  # device_id → {progress, step, done, error}

@devices_bp.route("/api/devices/extract", methods=["POST"])
def start_extraction():
    """Start data extraction from an ADB device. Non-blocking; poll /status."""
    data = request.get_json()
    case_id = data.get("case_id")
    serial = data.get("serial")
    if not case_id or not serial:
        return jsonify({"error": "case_id and serial are required"}), 400

    Case.query.get_or_404(case_id)

    device = Device(case_id=case_id, serial=serial, acquisition_status="in_progress",
                    acquisition_type="logical", created_at=datetime.datetime.utcnow())
    db.session.add(device)
    db.session.commit()

    _log_audit(case_id, device.id, "EXTRACTION_STARTED", f"Logical acquisition started on device {serial}")

    thread = threading.Thread(target=_run_extraction, args=(device.id, serial, case_id, current_app._get_current_object()))
    thread.daemon = True
    thread.start()

    return jsonify({"message": "Extraction started", "device_id": device.id})

def _run_extraction(device_id, serial, case_id, app):
    """Background extraction thread."""
    with app.app_context():
        def audit(action, details):
            _log_audit(case_id, device_id, action, details)

        def progress_cb(step, pct):
            _extraction_status[device_id] = {"progress": pct, "step": step, "done": False}

        try:
            adb = ADBExtractor(
                adb_path=app.config["ADB_PATH"],
                evidence_dir=app.config["EVIDENCE_DIR"],
                case_id=case_id,
                device_serial=serial,
                audit_callback=audit,
            )

            # Enrich device record with metadata
            dev_info = adb.get_device_info()
            device = Device.query.get(device_id)
            device.manufacturer = dev_info.get("manufacturer")
            device.model = dev_info.get("model")
            device.android_version = dev_info.get("android_version")
            device.imei = dev_info.get("imei")
            device.phone_number = dev_info.get("phone_number")
            device.sim_operator = dev_info.get("sim_operator")
            storage = dev_info.get("storage_info", {})
            device.storage_total = storage.get("total")
            device.storage_used = storage.get("used")
            device.battery_level = dev_info.get("battery_level")
            device.is_rooted = dev_info.get("is_rooted", False)
            db.session.commit()

            _extraction_status[device_id] = {"progress": 5, "step": "Device Info", "done": False}

            # Call logs
            call_data = adb.extract_call_logs()
            for c in call_data:
                ts = c.get("timestamp")
                db.session.add(CallLog(
                    device_id=device_id,
                    number=c.get("number"), name=c.get("name"),
                    call_type=c.get("call_type"), duration_seconds=c.get("duration_seconds", 0),
                    timestamp=ts, geocoded_location=c.get("geocoded_location"),
                    raw_data=c.get("raw_data"),
                ))
            db.session.commit()
            _extraction_status[device_id] = {"progress": 20, "step": "Call Logs", "done": False}

            # SMS
            sms_data = adb.extract_sms()
            mms_data = adb.extract_mms()
            for s in sms_data + mms_data:
                db.session.add(SMS(
                    device_id=device_id, address=s.get("address"),
                    contact_name=s.get("contact_name", ""), body=s.get("body"),
                    sms_type=s.get("sms_type"), timestamp=s.get("timestamp"),
                    thread_id=s.get("thread_id"), read=s.get("read", True),
                    is_mms=s.get("is_mms", False), mms_subject=s.get("mms_subject"),
                    raw_data=s.get("raw_data"),
                ))
            db.session.commit()
            _extraction_status[device_id] = {"progress": 35, "step": "SMS / MMS", "done": False}

            # Contacts
            contact_data = adb.extract_contacts()
            for ct in contact_data:
                db.session.add(Contact(
                    device_id=device_id, name=ct.get("name"),
                    phone_numbers=ct.get("phone_numbers"),
                    emails=ct.get("emails"),
                    organization=ct.get("organization"),
                    times_contacted=ct.get("times_contacted", 0),
                    raw_data=ct.get("raw_data"),
                ))
            db.session.commit()
            _extraction_status[device_id] = {"progress": 50, "step": "Contacts", "done": False}

            # Media
            thumb_dir = app.config["THUMBNAILS_DIR"]
            media_pulled = adb.extract_media(evidence_dir=app.config["EVIDENCE_DIR"])
            for mf in media_pulled:
                local = mf.get("local_path", "")
                if not os.path.exists(local):
                    continue
                meta = parse_media_file(local, thumbnail_dir=thumb_dir)
                if not meta:
                    continue
                db.session.add(MediaFile(
                    device_id=device_id,
                    filename=meta.get("filename"), file_type=meta.get("file_type"),
                    file_size=meta.get("file_size"), file_hash=meta.get("file_hash"),
                    local_path=meta.get("local_path"), thumbnail_path=meta.get("thumbnail_path"),
                    timestamp=meta.get("timestamp"),
                    camera_make=meta.get("camera_make"), camera_model=meta.get("camera_model"),
                    gps_latitude=meta.get("gps_latitude"), gps_longitude=meta.get("gps_longitude"),
                    gps_altitude=meta.get("gps_altitude"),
                    width=meta.get("width"), height=meta.get("height"),
                    source_path=mf.get("source_path"),
                ))
                # Auto-add location from photo EXIF
                if meta.get("gps_latitude") and meta.get("gps_longitude"):
                    db.session.add(Location(
                        device_id=device_id,
                        latitude=meta["gps_latitude"], longitude=meta["gps_longitude"],
                        altitude=meta.get("gps_altitude"), accuracy=0,
                        source="photo_exif", source_ref=meta.get("filename"),
                        timestamp=meta.get("timestamp"),
                    ))
            db.session.commit()
            _extraction_status[device_id] = {"progress": 70, "step": "Media Files", "done": False}

            # App databases
            app_dbs = adb.extract_app_dbs(evidence_dir=app.config["EVIDENCE_DIR"])
            for app_name, info in app_dbs.items():
                db_path = info.get("path", "")
                if not os.path.exists(db_path):
                    continue
                records = []
                if "whatsapp" in app_name:
                    records = parse_whatsapp_db(db_path)
                elif "browser" in app_name or "chrome" in app_name:
                    records = parse_browser_db(db_path)
                elif "gmail" in app_name or "email" in app_name:
                    email_records = parse_gmail_db(db_path)
                    for er in email_records:
                        db.session.add(Email(
                            device_id=device_id, account=er.get("account"),
                            folder=er.get("folder"), sender=er.get("sender"),
                            recipients=er.get("recipients"), subject=er.get("subject"),
                            body=er.get("body"), timestamp=er.get("timestamp"),
                            has_attachments=er.get("has_attachments"), message_id=er.get("message_id"),
                        ))
                    records = []
                elif "sms" in app_name:
                    for s in parse_sms_db(db_path):
                        db.session.add(SMS(
                            device_id=device_id, address=s.get("address"),
                            body=s.get("body"), sms_type=s.get("sms_type"),
                            timestamp=s.get("timestamp"), thread_id=s.get("thread_id"),
                            read=s.get("read"), is_mms=False, raw_data=s.get("raw_data"),
                        ))
                    records = []
                elif "call_log" in app_name:
                    for cl in parse_calllog_db(db_path):
                        db.session.add(CallLog(
                            device_id=device_id, number=cl.get("number"),
                            name=cl.get("name"), call_type=cl.get("call_type"),
                            duration_seconds=cl.get("duration_seconds", 0),
                            timestamp=cl.get("timestamp"),
                            geocoded_location=cl.get("geocoded_location"),
                            raw_data=cl.get("raw_data"),
                        ))
                    records = []

                for r in records:
                    db.session.add(AppData(
                        device_id=device_id, app_name=r.get("app_name"),
                        package=r.get("package"), data_type=r.get("data_type"),
                        sender=r.get("sender"), recipient=r.get("recipient"),
                        content=r.get("content"), timestamp=r.get("timestamp"),
                        extra_metadata=r.get("extra_metadata"),
                    ))
            db.session.commit()
            _extraction_status[device_id] = {"progress": 90, "step": "App Databases", "done": False}

            # Locations from content providers
            loc_data = adb.extract_locations_from_content()
            for loc in loc_data:
                db.session.add(Location(
                    device_id=device_id, latitude=loc["latitude"], longitude=loc["longitude"],
                    altitude=loc.get("altitude"), accuracy=loc.get("accuracy"),
                    source=loc.get("source"), source_ref=loc.get("source_ref"),
                    timestamp=loc.get("timestamp"),
                ))
            db.session.commit()

            device.acquisition_status = "completed"
            device.acquired_at = datetime.datetime.utcnow()
            db.session.commit()
            _log_audit(case_id, device_id, "EXTRACTION_COMPLETE", f"Extraction completed successfully")
            _extraction_status[device_id] = {"progress": 100, "step": "Complete", "done": True}

        except Exception as e:
            logger.exception("Extraction failed for device %d: %s", device_id, e)
            device = Device.query.get(device_id)
            if device:
                device.acquisition_status = "failed"
                db.session.commit()
            _extraction_status[device_id] = {"progress": 0, "step": "Error", "done": True, "error": str(e)}
            _log_audit(case_id, device_id, "EXTRACTION_FAILED", str(e))

@devices_bp.route("/api/devices/extract/status/<int:device_id>", methods=["GET"])
def extraction_status(device_id):
    status = _extraction_status.get(device_id, {"progress": 0, "step": "Not Started", "done": False})
    return jsonify(status)

# -------------------------
# Blueprint: Evidence
# -------------------------
evidence_bp = Blueprint("evidence", __name__)

def _paginate(query, request):
    page = int(request.args.get("page", 1))
    per_page = int(request.args.get("per_page", 50))
    return query.paginate(page=page, per_page=per_page, error_out=False)

@evidence_bp.route("/api/evidence/<int:device_id>/calls", methods=["GET"])
def get_calls(device_id):
    q = CallLog.query.filter_by(device_id=device_id).order_by(CallLog.timestamp.desc())
    search = request.args.get("search", "")
    if search:
        q = q.filter(db.or_(CallLog.number.contains(search), CallLog.name.contains(search)))
    call_type = request.args.get("type", "")
    if call_type:
        q = q.filter(CallLog.call_type == call_type)
    pag = _paginate(q, request)
    unlocked = _is_unlocked()
    return jsonify({
        "items": [_serialize(c, unlocked) for c in pag.items],
        "total": pag.total, "page": pag.page, "pages": pag.pages
    })

@evidence_bp.route("/api/evidence/<int:device_id>/sms", methods=["GET"])
def get_sms(device_id):
    q = SMS.query.filter_by(device_id=device_id).order_by(SMS.timestamp.desc())
    search = request.args.get("search", "")
    if search:
        q = q.filter(db.or_(SMS.body.contains(search), SMS.address.contains(search)))
    pag = _paginate(q, request)
    unlocked = _is_unlocked()
    return jsonify({
        "items": [_serialize(s, unlocked) for s in pag.items],
        "total": pag.total, "page": pag.page, "pages": pag.pages
    })

@evidence_bp.route("/api/evidence/<int:device_id>/contacts", methods=["GET"])
def get_contacts(device_id):
    q = Contact.query.filter_by(device_id=device_id).order_by(Contact.name)
    search = request.args.get("search", "")
    if search:
        q = q.filter(Contact.name.contains(search))
    pag = _paginate(q, request)
    unlocked = _is_unlocked()
    return jsonify({
        "items": [_serialize(c, unlocked) for c in pag.items],
        "total": pag.total, "page": pag.page, "pages": pag.pages
    })

@evidence_bp.route("/api/evidence/<int:device_id>/media", methods=["GET"])
def get_media(device_id):
    q = MediaFile.query.filter_by(device_id=device_id).order_by(MediaFile.timestamp.desc())
    file_type = request.args.get("type", "")
    if file_type:
        q = q.filter(MediaFile.file_type == file_type)
    has_gps = request.args.get("has_gps", "")
    if has_gps == "true":
        q = q.filter(MediaFile.gps_latitude != None)
    pag = _paginate(q, request)
    unlocked = _is_unlocked()
    return jsonify({
        "items": [_serialize(m, unlocked) for m in pag.items],
        "total": pag.total, "page": pag.page, "pages": pag.pages
    })

@evidence_bp.route("/api/evidence/<int:device_id>/media/thumbnail/<int:media_id>", methods=["GET"])
def get_thumbnail(device_id, media_id):
    mf = MediaFile.query.get_or_404(media_id)
    if mf.thumbnail_path and os.path.exists(mf.thumbnail_path):
        return send_file(mf.thumbnail_path, mimetype="image/jpeg")
    elif mf.local_path and os.path.exists(mf.local_path):
        return send_file(mf.local_path)
    return jsonify({"error": "Thumbnail not found"}), 404

@evidence_bp.route("/api/evidence/<int:device_id>/apps", methods=["GET"])
def get_apps(device_id):
    q = AppData.query.filter_by(device_id=device_id).order_by(AppData.timestamp.desc())
    app_name = request.args.get("app", "")
    if app_name:
        q = q.filter(AppData.app_name == app_name)
    search = request.args.get("search", "")
    if search:
        q = q.filter(AppData.content.contains(search))
    pag = _paginate(q, request)
    unlocked = _is_unlocked()
    return jsonify({
        "items": [_serialize(a, unlocked) for a in pag.items],
        "total": pag.total, "page": pag.page, "pages": pag.pages
    })

@evidence_bp.route("/api/evidence/<int:device_id>/emails", methods=["GET"])
def get_emails(device_id):
    q = Email.query.filter_by(device_id=device_id).order_by(Email.timestamp.desc())
    search = request.args.get("search", "")
    if search:
        q = q.filter(db.or_(Email.subject.contains(search), Email.sender.contains(search), Email.body.contains(search)))
    pag = _paginate(q, request)
    unlocked = _is_unlocked()
    return jsonify({
        "items": [_serialize(e, unlocked) for e in pag.items],
        "total": pag.total, "page": pag.page, "pages": pag.pages
    })

@evidence_bp.route("/api/evidence/<int:device_id>/locations", methods=["GET"])
def get_locations(device_id):
    locs = Location.query.filter_by(device_id=device_id).order_by(Location.timestamp.desc()).all()
    unlocked = _is_unlocked()
    return jsonify([_serialize(l, unlocked) for l in locs])

@evidence_bp.route("/api/evidence/<int:device_id>/timeline", methods=["GET"])
def get_timeline(device_id):
    unlocked = _is_unlocked()
    calls = [_serialize(c, unlocked) for c in CallLog.query.filter_by(device_id=device_id).all()]
    sms = [_serialize(s, unlocked) for s in SMS.query.filter_by(device_id=device_id).all()]
    media = [_serialize(m, unlocked) for m in MediaFile.query.filter_by(device_id=device_id).all()]
    apps = [_serialize(a, unlocked) for a in AppData.query.filter_by(device_id=device_id).all()]
    em = [_serialize(e, unlocked) for e in Email.query.filter_by(device_id=device_id).all()]
    locs = [_serialize(l, unlocked) for l in Location.query.filter_by(device_id=device_id).all()]
    events = build_timeline(device_id, call_logs=calls, sms_messages=sms,
                             media_files=media, app_data=apps, emails=em, locations=locs)
    return jsonify({"events": events, "total": len(events)})

@evidence_bp.route("/api/evidence/<int:device_id>/search", methods=["GET"])
def search_evidence(device_id):
    kw = request.args.get("q", "")
    if not kw:
        return jsonify({"hits": [], "total": 0})
    unlocked = _is_unlocked()
    calls = [_serialize(c, unlocked) for c in CallLog.query.filter_by(device_id=device_id).all()]
    sms = [_serialize(s, unlocked) for s in SMS.query.filter_by(device_id=device_id).all()]
    apps = [_serialize(a, unlocked) for a in AppData.query.filter_by(device_id=device_id).all()]
    em = [_serialize(e, unlocked) for e in Email.query.filter_by(device_id=device_id).all()]
    hits = keyword_search(kw, call_logs=calls, sms_messages=sms, app_data=apps, emails=em)
    return jsonify({"hits": hits, "total": len(hits), "keyword": kw})

@evidence_bp.route("/api/evidence/<int:device_id>/stats", methods=["GET"])
def get_stats(device_id):
    return jsonify({
        "calls": CallLog.query.filter_by(device_id=device_id).count(),
        "sms": SMS.query.filter_by(device_id=device_id).count(),
        "contacts": Contact.query.filter_by(device_id=device_id).count(),
        "photos": MediaFile.query.filter_by(device_id=device_id, file_type="photo").count(),
        "videos": MediaFile.query.filter_by(device_id=device_id, file_type="video").count(),
        "audio": MediaFile.query.filter_by(device_id=device_id, file_type="audio").count(),
        "app_data": AppData.query.filter_by(device_id=device_id).count(),
        "emails": Email.query.filter_by(device_id=device_id).count(),
        "locations": Location.query.filter_by(device_id=device_id).count(),
    })

# -------------------------
# Blueprint: Reports
# -------------------------
reports_bp = Blueprint("reports", __name__)

@reports_bp.route("/api/report/<int:device_id>", methods=["POST"])
def generate_report_endpoint(device_id):
    device = Device.query.get_or_404(device_id)
    case = Case.query.get_or_404(device.case_id)

    calls = [c.to_dict() for c in CallLog.query.filter_by(device_id=device_id).all()]
    sms = [s.to_dict() for s in SMS.query.filter_by(device_id=device_id).all()]
    contacts = [c.to_dict() for c in Contact.query.filter_by(device_id=device_id).all()]
    media = [m.to_dict() for m in MediaFile.query.filter_by(device_id=device_id).all()]
    apps = [a.to_dict() for a in AppData.query.filter_by(device_id=device_id).all()]
    em = [e.to_dict() for e in Email.query.filter_by(device_id=device_id).all()]
    locs = [l.to_dict() for l in Location.query.filter_by(device_id=device_id).all()]
    audit = [a.to_dict() for a in AuditLog.query.filter_by(device_id=device_id).order_by(AuditLog.timestamp).all()]

    events = build_timeline(device_id, call_logs=calls, sms_messages=sms,
                             media_files=media, app_data=apps, emails=em, locations=locs)

    reports_dir = current_app.config["REPORTS_DIR"]
    filename = f"forensic_report_{case.case_number}_{device_id}_{datetime.datetime.utcnow().strftime('%Y%m%d%H%M%S')}.pdf"
    output_path = os.path.join(reports_dir, filename)

    try:
        generate_report(
            output_path=output_path,
            case_data=case.to_dict(),
            device_data=device.to_dict(),
            call_logs=calls, sms_messages=sms, contacts=contacts,
            media_files=media, app_data=apps, emails=em,
            audit_logs=audit, timeline_events=events,
            thumbnail_dir=current_app.config["THUMBNAILS_DIR"],
        )
        _log_audit(case.id, device_id, "REPORT_GENERATED", f"PDF report generated: {filename}")
        return send_file(output_path, as_attachment=True, download_name=filename, mimetype="application/pdf")
    except Exception as e:
        logger.exception("Report generation failed: %s", e)
        return jsonify({"error": str(e)}), 500

# -------------------------
# Blueprint: Audit Log
# -------------------------
audit_bp = Blueprint("audit", __name__)

@audit_bp.route("/api/audit", methods=["GET"])
def get_audit_log():
    case_id = request.args.get("case_id")
    device_id = request.args.get("device_id")
    q = AuditLog.query.order_by(AuditLog.timestamp.desc())
    if case_id:
        q = q.filter_by(case_id=int(case_id))
    if device_id:
        q = q.filter_by(device_id=int(device_id))
    logs = q.limit(500).all()
    unlocked = _is_unlocked()
    return jsonify([_serialize(a, unlocked) for a in logs])

# ---- Helper ----
def _log_audit(case_id, device_id, action, details, actor="system"):
    try:
        entry = AuditLog(
            case_id=case_id, device_id=device_id,
            action=action, actor=actor, details=details,
            timestamp=datetime.datetime.utcnow(),
        )
        db.session.add(entry)
        db.session.commit()
    except Exception as e:
        logger.error("Audit log error: %s", e)
