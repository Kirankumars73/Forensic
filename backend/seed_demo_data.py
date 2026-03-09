"""
Demo Data Seeder - populates the database with realistic synthetic forensic data.
Run this to test the UI without a real device.
"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

import json
import random
import datetime
from app import create_app
from models import db, Case, Device, CallLog, SMS, Contact, MediaFile, AppData, Email, Location, AuditLog

NAMES = ["Alice Johnson", "Bob Smith", "Charlie Brown", "Diana Prince", "Eve Torres",
         "Frank Castle", "Grace Kelly", "Hank Pym", "Iris West", "Jake Peralta"]
NUMBERS = ["+91-98765-43210", "+91-87654-32109", "+91-76543-21098", "+91-65432-10987",
           "+91-54321-09876", "+44-7911-123456", "+1-555-0123", "+91-99887-76655", "+91-11122-33445"]
SMS_BODIES = [
    "Hey, are you coming to the meeting tomorrow?",
    "I've transferred the money. Check your account.",
    "Don't tell anyone about this. Delete after reading.",
    "The package has been delivered to the usual place.",
    "Call me on an encrypted line ASAP",
    "Meet me at the old warehouse at midnight",
    "Transfer done. ₹5,00,000. Account confirmed.",
    "I have the documents you asked for",
    "Airport pickup at 3 PM. Don't be late.",
    "Password: Falcon@9871. Don't save this.",
    "Lunch tomorrow at 1pm?",
    "Happy birthday! 🎂",
    "Your OTP is 847291. Valid for 10 minutes.",
    "Flight confirmed PNR: XY7890",
    "Bill amount: ₹12,450. Paid successfully.",
]
WA_MESSAGES = [
    "Sent the file. Check your email.",
    "Don't use phone for this. Come personally.",
    "Boss wants the report by Friday.",
    "Can you run a background check on this guy?",
    "Delete this conversation after reading.",
    "The deal is set for next week.",
    "50% upfront, rest on delivery.",
    "Use the encrypted app next time.",
]
SUBJECTS = [
    "Confidential: Project Falcon Update",
    "Re: Transaction Authorization",
    "Meeting Agenda - Internal",
    "Urgent: Password Reset Request",
    "Invoice #INV-2024-00899",
    "Travel Itinerary - March 2024",
    "Weekly Report Attached",
    "Please review the attached contract",
]
APPS = ["instagram", "twitter", "snapchat", "telegram", "facebook"]
URLS = [
    "https://www.google.com/search?q=how+to+transfer+money+anonymously",
    "https://protonmail.com",
    "https://www.whatsapp.com",
    "https://www.instagram.com/p/ABC123",
    "https://en.wikipedia.org/wiki/Digital_forensics",
    "https://www.amazon.in/orders",
]


def rand_ts(days_back=365):
    delta = datetime.timedelta(days=random.randint(0, days_back), seconds=random.randint(0, 86400))
    return datetime.datetime.utcnow() - delta


def seed():
    app = create_app()
    with app.app_context():
        db.create_all()

        # Create case
        case = Case(
            case_number="CASE-2024-001",
            title="Operation Shadow Network - Mobile Evidence Analysis",
            investigator="Det. Kiran Sharma",
            agency="Cyber Crime Investigation Unit",
            description="Suspected financial fraud and illegal communication via encrypted apps. Device seized from suspect.",
            suspect_name="John Doe",
            status="open",
            created_at=datetime.datetime.utcnow() - datetime.timedelta(days=5),
        )
        db.session.add(case)
        db.session.commit()

        # Create device
        device = Device(
            case_id=case.id,
            serial="R58M30ABCDE",
            manufacturer="Samsung",
            model="Galaxy S23 Ultra",
            android_version="14",
            imei="358239045678901",
            phone_number="+91-98765-43210",
            sim_operator="Airtel",
            storage_total="256 GB",
            storage_used="189 GB",
            battery_level="78%",
            is_rooted=False,
            acquisition_type="logical",
            acquisition_status="completed",
            acquired_at=datetime.datetime.utcnow() - datetime.timedelta(days=4),
            created_at=datetime.datetime.utcnow() - datetime.timedelta(days=4),
        )
        db.session.add(device)
        db.session.commit()
        did = device.id

        # Audit log - seizure
        def audit(action, details, days_back=4):
            db.session.add(AuditLog(
                case_id=case.id, device_id=did, action=action,
                actor="Det. Kiran Sharma", details=details,
                timestamp=datetime.datetime.utcnow() - datetime.timedelta(days=days_back),
            ))

        audit("DEVICE_SEIZED", "Device physically seized from suspect premises. Placed in Faraday bag.", 4)
        audit("DEVICE_PHOTOGRAPHED", "Device photographed front, back, ports. IMEI noted.", 4)
        audit("ADB_ENABLED", "USB debugging enabled. ADB connection established.", 4)
        audit("EXTRACTION_STARTED", "Logical acquisition started on Samsung Galaxy S23 Ultra.", 4)
        audit("EXTRACT_CALL_LOGS", "Extracted 120 call log records via content://call_log/calls", 4)
        audit("EXTRACT_SMS", "Extracted 85 SMS records via content://sms", 4)
        audit("EXTRACT_MMS", "Extracted 12 MMS records via content://mms", 4)
        audit("EXTRACT_CONTACTS", "Extracted 245 contacts", 4)
        audit("EXTRACT_MEDIA", "Pulled 312 media files (photos, videos) from /sdcard/DCIM", 4)
        audit("EXTRACT_APP_DBS", "Pulled WhatsApp msgstore.db via root backup fallback", 4)
        audit("EXTRACT_BROWSER", "Extracted 45 browser history records", 4)
        audit("EXTRACTION_COMPLETE", "All extraction steps completed. SHA-256 hash computed.", 4)
        audit("REPORT_GENERATED", "PDF forensic report generated and archived.", 0)
        db.session.commit()

        # Call logs
        call_types = ["incoming", "outgoing", "missed", "rejected"]
        for i in range(120):
            ct = random.choice(call_types)
            dur = random.randint(5, 3600) if ct != "missed" else 0
            n = random.choice(NUMBERS)
            name = random.choice(NAMES) if random.random() > 0.3 else ""
            db.session.add(CallLog(
                device_id=did, number=n, name=name, call_type=ct,
                duration_seconds=dur, timestamp=rand_ts(90),
                geocoded_location=random.choice(["Mumbai, MH", "Delhi, DL", "Bangalore, KA", "", "Chennai, TN"]),
                raw_data=json.dumps({"raw": "adb_content_query"}),
            ))
        db.session.commit()

        # SMS
        for i in range(85):
            stype = random.choice(["received", "sent", "received", "received"])
            db.session.add(SMS(
                device_id=did,
                address=random.choice(NUMBERS),
                contact_name=random.choice(NAMES) if random.random() > 0.4 else "",
                body=random.choice(SMS_BODIES),
                sms_type=stype,
                timestamp=rand_ts(90),
                thread_id=str(random.randint(1, 20)),
                read=random.random() > 0.2,
                is_mms=False,
                raw_data=json.dumps({}),
            ))
        # MMS
        for i in range(12):
            db.session.add(SMS(
                device_id=did,
                address=random.choice(NUMBERS),
                contact_name=random.choice(NAMES),
                body="[MMS Attachment]",
                sms_type="received",
                timestamp=rand_ts(60),
                thread_id=str(random.randint(1, 20)),
                read=True,
                is_mms=True,
                mms_subject="Photo/Video shared",
                raw_data=json.dumps({}),
            ))
        db.session.commit()

        # Contacts
        for n in NAMES:
            phones = random.sample(NUMBERS, random.randint(1, 3))
            db.session.add(Contact(
                device_id=did, name=n,
                phone_numbers=json.dumps(phones),
                emails=json.dumps([f"{n.replace(' ','').lower()}@gmail.com"]),
                organization=random.choice(["Acme Corp", "GloboCorp", "", "Freelance", "Govt Dept"]),
                times_contacted=random.randint(0, 50),
                raw_data=json.dumps({}),
            ))
        # Extra random contacts
        for i in range(235):
            fname = random.choice(["Raj","Priya","Amit","Neha","Rahul","Anita","Vijay","Sonia","Arjun","Deepa"])
            lname = random.choice(["Kumar","Sharma","Verma","Patel","Singh","Gupta","Joshi","Mehta"])
            db.session.add(Contact(
                device_id=did, name=f"{fname} {lname}",
                phone_numbers=json.dumps([random.choice(NUMBERS)]),
                emails=json.dumps([f"{fname.lower()}{random.randint(1,99)}@gmail.com"]),
                organization="",
                times_contacted=random.randint(0, 10),
                raw_data=json.dumps({}),
            ))
        db.session.commit()

        # Media files (synthetic — no real files, just metadata records)
        for i in range(312):
            ftype = random.choice(["photo", "photo", "photo", "video", "audio"])
            ext = {"photo": "jpg", "video": "mp4", "audio": "aac"}[ftype]
            fname = f"IMG_{20240101 + i:08d}.{ext}"
            ts = rand_ts(365)
            lat = round(random.uniform(8.0, 37.0), 6) if random.random() > 0.4 else None
            lon = round(random.uniform(68.0, 97.0), 6) if lat else None
            mf = MediaFile(
                device_id=did, filename=fname, file_type=ftype,
                file_size=random.randint(200000, 8000000),
                file_hash=os.urandom(32).hex(),
                local_path=f"evidence_store/media/device/{fname}",
                thumbnail_path=None, timestamp=ts,
                camera_make=random.choice(["Samsung", "Google", "Apple", ""]),
                camera_model=random.choice(["Galaxy S23", "Pixel 7", "iPhone 14", ""]),
                gps_latitude=lat, gps_longitude=lon,
                gps_altitude=round(random.uniform(0, 600), 1) if lat else None,
                width=random.choice([3024, 4032, 1920]),
                height=random.choice([4032, 3024, 1080]),
                source_path=f"/sdcard/DCIM/Camera/{fname}",
            )
            db.session.add(mf)
            if lat and lon:
                db.session.add(Location(
                    device_id=did, latitude=lat, longitude=lon,
                    altitude=round(random.uniform(0, 600), 1),
                    accuracy=5.0, source="photo_exif", source_ref=fname, timestamp=ts,
                ))
        db.session.commit()

        # WhatsApp data
        for i in range(150):
            sender_name = random.choice(NAMES)
            db.session.add(AppData(
                device_id=did, app_name="whatsapp", package="com.whatsapp",
                data_type="message",
                sender=random.choice([sender_name, "Me"]),
                recipient=sender_name if sender_name != "Me" else random.choice(NAMES),
                content=random.choice(WA_MESSAGES),
                timestamp=rand_ts(60),
                extra_metadata=json.dumps({"status": "read", "media_url": None}),
            ))
        # Browser history
        for i in range(45):
            db.session.add(AppData(
                device_id=did, app_name="chrome", package="com.android.chrome",
                data_type="history", sender="", recipient="",
                content=random.choice(URLS),
                timestamp=rand_ts(30),
                extra_metadata=json.dumps({"visit_count": random.randint(1, 10)}),
            ))
        # Instagram
        for i in range(30):
            db.session.add(AppData(
                device_id=did, app_name="instagram", package="com.instagram.android",
                data_type="message",
                sender=random.choice(NAMES), recipient="Me",
                content=random.choice(["Seen 👀", "Nice pic!", "When are you free?", "DM me"]),
                timestamp=rand_ts(30),
                extra_metadata=json.dumps({}),
            ))
        db.session.commit()

        # Emails
        for i in range(60):
            to_list = random.sample([f"{n.replace(' ','').lower()}@gmail.com" for n in NAMES], random.randint(1,3))
            db.session.add(Email(
                device_id=did,
                account="johndoe2024@gmail.com",
                folder=random.choice(["inbox", "sent", "inbox", "inbox"]),
                sender=f"{random.choice(NAMES).replace(' ','').lower()}@gmail.com",
                recipients=json.dumps(to_list),
                subject=random.choice(SUBJECTS),
                body="Please find the attached document as requested. Let me know if you need anything else.",
                timestamp=rand_ts(90),
                has_attachments=random.random() > 0.6,
                message_id=f"<{os.urandom(8).hex()}@gmail.com>",
            ))
        db.session.commit()

        # Locations (cell tower / GPS)
        cities = [
            (19.0760, 72.8777, "Mumbai"), (28.6139, 77.2090, "Delhi"),
            (12.9716, 77.5946, "Bangalore"), (13.0827, 80.2707, "Chennai"),
            (17.3850, 78.4867, "Hyderabad"),
        ]
        for city_lat, city_lon, city_name in cities:
            for _ in range(random.randint(5, 20)):
                db.session.add(Location(
                    device_id=did,
                    latitude=round(city_lat + random.uniform(-0.05, 0.05), 6),
                    longitude=round(city_lon + random.uniform(-0.05, 0.05), 6),
                    altitude=round(random.uniform(0, 100), 1),
                    accuracy=random.uniform(5, 50),
                    source=random.choice(["gps", "network", "wifi"]),
                    source_ref=city_name,
                    timestamp=rand_ts(90),
                    address=f"{city_name}, India",
                ))
        db.session.commit()

        print("=" * 60)
        print("✅ Demo data seeded successfully!")
        print(f"   Case: {case.case_number}")
        print(f"   Device: {device.model} (ID={device.id})")
        print(f"   Call logs: 120 | SMS: 97 | Contacts: 245")
        print(f"   Media: 312 | WhatsApp msgs: 150 | Emails: 60")
        print(f"   Locations: {Location.query.filter_by(device_id=did).count()}")
        print("=" * 60)
        print(f"\nNow start the backend: python app.py")
        print(f"Frontend: cd ../frontend && npm run dev")


if __name__ == "__main__":
    seed()
