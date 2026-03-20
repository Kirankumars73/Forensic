import os
import hashlib
import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


def _sha(value):
    """Return a short SHA-256 display hash for a value, or empty string if falsy."""
    if value is None or value == "" or value == []:
        return value
    raw = str(value).encode("utf-8")
    digest = hashlib.sha256(raw).hexdigest()
    return f"••••[{digest[:20]}]"


class Case(db.Model):
    __tablename__ = "cases"
    id = db.Column(db.Integer, primary_key=True)
    case_number = db.Column(db.String(64), unique=True, nullable=False)
    title = db.Column(db.String(256), nullable=False)
    investigator = db.Column(db.String(128), nullable=False)
    agency = db.Column(db.String(128))
    description = db.Column(db.Text)
    suspect_name = db.Column(db.String(128))
    status = db.Column(db.String(32), default="open")  # open, closed, archived
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    devices = db.relationship("Device", backref="case", lazy=True, cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id": self.id,
            "case_number": self.case_number,
            "title": self.title,
            "investigator": self.investigator,
            "agency": self.agency,
            "description": self.description,
            "suspect_name": self.suspect_name,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def to_hashed_dict(self):
        d = self.to_dict()
        d["investigator"] = _sha(d["investigator"])
        d["agency"] = _sha(d["agency"])
        d["description"] = _sha(d["description"])
        d["suspect_name"] = _sha(d["suspect_name"])
        return d


class Device(db.Model):
    __tablename__ = "devices"
    id = db.Column(db.Integer, primary_key=True)
    case_id = db.Column(db.Integer, db.ForeignKey("cases.id"), nullable=False)
    serial = db.Column(db.String(64))
    manufacturer = db.Column(db.String(128))
    model = db.Column(db.String(128))
    android_version = db.Column(db.String(32))
    imei = db.Column(db.String(32))
    phone_number = db.Column(db.String(32))
    sim_operator = db.Column(db.String(64))
    storage_total = db.Column(db.String(32))
    storage_used = db.Column(db.String(32))
    battery_level = db.Column(db.String(8))
    is_rooted = db.Column(db.Boolean, default=False)
    acquisition_type = db.Column(db.String(32))  # logical, filesystem, physical
    acquisition_status = db.Column(db.String(32), default="pending")  # pending, in_progress, completed, failed
    evidence_hash = db.Column(db.String(64))
    acquired_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)

    call_logs = db.relationship("CallLog", backref="device", lazy=True, cascade="all, delete-orphan")
    sms_messages = db.relationship("SMS", backref="device", lazy=True, cascade="all, delete-orphan")
    contacts = db.relationship("Contact", backref="device", lazy=True, cascade="all, delete-orphan")
    media_files = db.relationship("MediaFile", backref="device", lazy=True, cascade="all, delete-orphan")
    app_data = db.relationship("AppData", backref="device", lazy=True, cascade="all, delete-orphan")
    locations = db.relationship("Location", backref="device", lazy=True, cascade="all, delete-orphan")
    emails = db.relationship("Email", backref="device", lazy=True, cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id": self.id,
            "case_id": self.case_id,
            "serial": self.serial,
            "manufacturer": self.manufacturer,
            "model": self.model,
            "android_version": self.android_version,
            "imei": self.imei,
            "phone_number": self.phone_number,
            "sim_operator": self.sim_operator,
            "storage_total": self.storage_total,
            "storage_used": self.storage_used,
            "battery_level": self.battery_level,
            "is_rooted": self.is_rooted,
            "acquisition_type": self.acquisition_type,
            "acquisition_status": self.acquisition_status,
            "evidence_hash": self.evidence_hash,
            "acquired_at": self.acquired_at.isoformat() if self.acquired_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    def to_hashed_dict(self):
        d = self.to_dict()
        d["serial"] = _sha(d["serial"])
        d["imei"] = _sha(d["imei"])
        d["phone_number"] = _sha(d["phone_number"])
        d["sim_operator"] = _sha(d["sim_operator"])
        return d


class CallLog(db.Model):
    __tablename__ = "call_logs"
    id = db.Column(db.Integer, primary_key=True)
    device_id = db.Column(db.Integer, db.ForeignKey("devices.id"), nullable=False)
    number = db.Column(db.String(32))
    name = db.Column(db.String(128))
    call_type = db.Column(db.String(16))  # incoming, outgoing, missed, rejected
    duration_seconds = db.Column(db.Integer, default=0)
    timestamp = db.Column(db.DateTime)
    geocoded_location = db.Column(db.String(128))
    raw_data = db.Column(db.Text)

    def to_dict(self):
        return {
            "id": self.id,
            "device_id": self.device_id,
            "number": self.number,
            "name": self.name,
            "call_type": self.call_type,
            "duration_seconds": self.duration_seconds,
            "duration_formatted": self._fmt_duration(),
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "geocoded_location": self.geocoded_location,
        }

    def to_hashed_dict(self):
        d = self.to_dict()
        d["number"] = _sha(d["number"])
        d["name"] = _sha(d["name"]) if d["name"] else d["name"]
        d["geocoded_location"] = _sha(d["geocoded_location"]) if d["geocoded_location"] else d["geocoded_location"]
        return d

    def _fmt_duration(self):
        if not self.duration_seconds:
            return "0s"
        m, s = divmod(self.duration_seconds, 60)
        h, m = divmod(m, 60)
        if h:
            return f"{h}h {m}m {s}s"
        if m:
            return f"{m}m {s}s"
        return f"{s}s"


class SMS(db.Model):
    __tablename__ = "sms_messages"
    id = db.Column(db.Integer, primary_key=True)
    device_id = db.Column(db.Integer, db.ForeignKey("devices.id"), nullable=False)
    address = db.Column(db.String(32))
    contact_name = db.Column(db.String(128))
    body = db.Column(db.Text)
    sms_type = db.Column(db.String(16))  # received, sent, draft
    timestamp = db.Column(db.DateTime)
    thread_id = db.Column(db.String(32))
    read = db.Column(db.Boolean, default=True)
    is_mms = db.Column(db.Boolean, default=False)
    mms_subject = db.Column(db.String(256))
    raw_data = db.Column(db.Text)

    def to_dict(self):
        return {
            "id": self.id,
            "device_id": self.device_id,
            "address": self.address,
            "contact_name": self.contact_name,
            "body": self.body,
            "sms_type": self.sms_type,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "thread_id": self.thread_id,
            "read": self.read,
            "is_mms": self.is_mms,
            "mms_subject": self.mms_subject,
        }

    def to_hashed_dict(self):
        d = self.to_dict()
        d["address"] = _sha(d["address"])
        d["contact_name"] = _sha(d["contact_name"]) if d["contact_name"] else d["contact_name"]
        d["body"] = _sha(d["body"])
        d["mms_subject"] = _sha(d["mms_subject"]) if d["mms_subject"] else d["mms_subject"]
        return d


class Contact(db.Model):
    __tablename__ = "contacts"
    id = db.Column(db.Integer, primary_key=True)
    device_id = db.Column(db.Integer, db.ForeignKey("devices.id"), nullable=False)
    name = db.Column(db.String(256))
    phone_numbers = db.Column(db.Text)   # JSON list
    emails = db.Column(db.Text)          # JSON list
    organization = db.Column(db.String(256))
    last_contacted = db.Column(db.DateTime)
    times_contacted = db.Column(db.Integer, default=0)
    raw_data = db.Column(db.Text)

    def to_dict(self):
        import json
        return {
            "id": self.id,
            "device_id": self.device_id,
            "name": self.name,
            "phone_numbers": json.loads(self.phone_numbers) if self.phone_numbers else [],
            "emails": json.loads(self.emails) if self.emails else [],
            "organization": self.organization,
            "last_contacted": self.last_contacted.isoformat() if self.last_contacted else None,
            "times_contacted": self.times_contacted,
        }

    def to_hashed_dict(self):
        import json
        d = self.to_dict()
        d["name"] = _sha(d["name"])
        d["phone_numbers"] = [_sha(p) for p in d["phone_numbers"]]
        d["emails"] = [_sha(e) for e in d["emails"]]
        d["organization"] = _sha(d["organization"]) if d["organization"] else d["organization"]
        return d


class MediaFile(db.Model):
    __tablename__ = "media_files"
    id = db.Column(db.Integer, primary_key=True)
    device_id = db.Column(db.Integer, db.ForeignKey("devices.id"), nullable=False)
    filename = db.Column(db.String(512))
    file_type = db.Column(db.String(16))  # photo, video, audio, document
    file_size = db.Column(db.Integer)
    file_hash = db.Column(db.String(64))
    local_path = db.Column(db.String(1024))
    thumbnail_path = db.Column(db.String(1024))
    timestamp = db.Column(db.DateTime)
    # EXIF data
    camera_make = db.Column(db.String(64))
    camera_model = db.Column(db.String(64))
    gps_latitude = db.Column(db.Float)
    gps_longitude = db.Column(db.Float)
    gps_altitude = db.Column(db.Float)
    width = db.Column(db.Integer)
    height = db.Column(db.Integer)
    source_path = db.Column(db.String(1024))  # original path on device

    def to_dict(self):
        return {
            "id": self.id,
            "device_id": self.device_id,
            "filename": self.filename,
            "file_type": self.file_type,
            "file_size": self.file_size,
            "file_hash": self.file_hash,
            "local_path": self.local_path,
            "thumbnail_path": self.thumbnail_path,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "camera_make": self.camera_make,
            "camera_model": self.camera_model,
            "gps_latitude": self.gps_latitude,
            "gps_longitude": self.gps_longitude,
            "gps_altitude": self.gps_altitude,
            "width": self.width,
            "height": self.height,
            "source_path": self.source_path,
        }

    def to_hashed_dict(self):
        d = self.to_dict()
        d["filename"] = _sha(d["filename"])
        d["file_hash"] = _sha(d["file_hash"]) if d["file_hash"] else d["file_hash"]
        d["source_path"] = _sha(d["source_path"]) if d["source_path"] else d["source_path"]
        # Keep GPS as None in locked state — hashing coords breaks Leaflet and .toFixed()
        d["gps_latitude"] = None
        d["gps_longitude"] = None
        d["gps_altitude"] = None
        return d


class AppData(db.Model):
    __tablename__ = "app_data"
    id = db.Column(db.Integer, primary_key=True)
    device_id = db.Column(db.Integer, db.ForeignKey("devices.id"), nullable=False)
    app_name = db.Column(db.String(128))   # whatsapp, telegram, browser, instagram, etc.
    package = db.Column(db.String(256))
    data_type = db.Column(db.String(64))   # message, chat, history, post, note
    sender = db.Column(db.String(256))
    recipient = db.Column(db.String(256))
    content = db.Column(db.Text)
    timestamp = db.Column(db.DateTime)
    extra_metadata = db.Column(db.Text)    # JSON

    def to_dict(self):
        return {
            "id": self.id,
            "device_id": self.device_id,
            "app_name": self.app_name,
            "package": self.package,
            "data_type": self.data_type,
            "sender": self.sender,
            "recipient": self.recipient,
            "content": self.content,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "extra_metadata": self.extra_metadata,
        }

    def to_hashed_dict(self):
        d = self.to_dict()
        d["sender"] = _sha(d["sender"]) if d["sender"] else d["sender"]
        d["recipient"] = _sha(d["recipient"]) if d["recipient"] else d["recipient"]
        d["content"] = _sha(d["content"])
        return d


class Email(db.Model):
    __tablename__ = "emails"
    id = db.Column(db.Integer, primary_key=True)
    device_id = db.Column(db.Integer, db.ForeignKey("devices.id"), nullable=False)
    account = db.Column(db.String(256))      # which email account
    folder = db.Column(db.String(64))        # inbox, sent, drafts
    sender = db.Column(db.String(256))
    recipients = db.Column(db.Text)          # JSON list
    subject = db.Column(db.String(512))
    body = db.Column(db.Text)
    timestamp = db.Column(db.DateTime)
    has_attachments = db.Column(db.Boolean, default=False)
    message_id = db.Column(db.String(256))

    def to_dict(self):
        import json
        return {
            "id": self.id,
            "device_id": self.device_id,
            "account": self.account,
            "folder": self.folder,
            "sender": self.sender,
            "recipients": json.loads(self.recipients) if self.recipients else [],
            "subject": self.subject,
            "body": self.body,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "has_attachments": self.has_attachments,
            "message_id": self.message_id,
        }

    def to_hashed_dict(self):
        d = self.to_dict()
        d["account"] = _sha(d["account"])
        d["sender"] = _sha(d["sender"])
        d["recipients"] = [_sha(r) for r in d["recipients"]]
        d["subject"] = _sha(d["subject"])
        d["body"] = _sha(d["body"])
        d["message_id"] = _sha(d["message_id"]) if d["message_id"] else d["message_id"]
        return d


class Location(db.Model):
    __tablename__ = "locations"
    id = db.Column(db.Integer, primary_key=True)
    device_id = db.Column(db.Integer, db.ForeignKey("devices.id"), nullable=False)
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    altitude = db.Column(db.Float)
    accuracy = db.Column(db.Float)
    source = db.Column(db.String(64))    # gps, network, photo_exif, browser, wifi
    source_ref = db.Column(db.String(256))  # filename or app that had this location
    timestamp = db.Column(db.DateTime)
    address = db.Column(db.String(512))

    def to_dict(self):
        return {
            "id": self.id,
            "device_id": self.device_id,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "altitude": self.altitude,
            "accuracy": self.accuracy,
            "source": self.source,
            "source_ref": self.source_ref,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "address": self.address,
        }

    def to_hashed_dict(self):
        d = self.to_dict()
        # Keep lat/lon as None in locked state — hashing coords crashes Leaflet maps
        d["latitude"] = None
        d["longitude"] = None
        d["altitude"] = None
        d["address"] = _sha(d["address"]) if d["address"] else d["address"]
        d["source_ref"] = _sha(d["source_ref"]) if d["source_ref"] else d["source_ref"]
        return d


class AuditLog(db.Model):
    __tablename__ = "audit_logs"
    id = db.Column(db.Integer, primary_key=True)
    case_id = db.Column(db.Integer, db.ForeignKey("cases.id"))
    device_id = db.Column(db.Integer, db.ForeignKey("devices.id"))
    action = db.Column(db.String(128), nullable=False)
    actor = db.Column(db.String(128), default="system")
    details = db.Column(db.Text)
    hash_before = db.Column(db.String(64))
    hash_after = db.Column(db.String(64))
    timestamp = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    ip_address = db.Column(db.String(64))

    def to_dict(self):
        return {
            "id": self.id,
            "case_id": self.case_id,
            "device_id": self.device_id,
            "action": self.action,
            "actor": self.actor,
            "details": self.details,
            "hash_before": self.hash_before,
            "hash_after": self.hash_after,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "ip_address": self.ip_address,
        }

    def to_hashed_dict(self):
        d = self.to_dict()
        d["actor"] = _sha(d["actor"]) if d["actor"] and d["actor"] != "system" else d["actor"]
        d["details"] = _sha(d["details"]) if d["details"] else d["details"]
        return d
