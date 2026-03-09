import os
import hashlib
import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


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
