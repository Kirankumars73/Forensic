"""
ADB Extraction Engine
Acquires data from Android devices via USB/OTG using Android Debug Bridge.
Supports logical acquisition: call logs, SMS, MMS, contacts, media files,
app databases (WhatsApp, browser, Instagram, Gmail), and device metadata.
"""
import os
import json
import subprocess
import datetime
import hashlib
import shutil
import tempfile
import re
import logging

logger = logging.getLogger(__name__)

# ADB call type mapping
ADB_CALL_TYPES = {
    "1": "incoming",
    "2": "outgoing",
    "3": "missed",
    "4": "voicemail",
    "5": "rejected",
    "6": "blocked",
}

# SMS type mapping
ADB_SMS_TYPES = {
    "1": "received",
    "2": "sent",
    "3": "draft",
    "4": "outbox",
    "5": "failed",
    "6": "queued",
}


class ADBExtractor:
    """Main class for extracting forensic data from Android via ADB."""

    def __init__(self, adb_path="adb", evidence_dir="evidence_store", case_id=None, device_serial=None, audit_callback=None):
        self.adb = adb_path
        self.evidence_dir = evidence_dir
        self.case_id = case_id
        self.serial = device_serial
        self._audit = audit_callback or (lambda action, details: None)
        self._serial_flag = ["-s", device_serial] if device_serial else []

    # ------------------------------------------------------------------
    # Core ADB Helpers
    # ------------------------------------------------------------------

    def _run(self, *args, timeout=60):
        """Run an adb command and return stdout as a string."""
        cmd = [self.adb] + self._serial_flag + list(args)
        logger.debug("ADB CMD: %s", " ".join(cmd))
        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=timeout, encoding="utf-8", errors="replace"
            )
            return result.stdout.strip()
        except subprocess.TimeoutExpired:
            logger.warning("ADB command timed out: %s", args)
            return ""
        except FileNotFoundError:
            logger.error("ADB binary not found at '%s'. Install Android SDK Platform-Tools.", self.adb)
            return ""
        except Exception as e:
            logger.error("ADB error: %s", e)
            return ""

    def _shell(self, *args, timeout=60):
        """Run adb shell command."""
        return self._run("shell", *args, timeout=timeout)

    def _content_query(self, uri, projection=None):
        """Query a content URI and return a list of row dicts."""
        cmd = f"content query --uri {uri}"
        if projection:
            cmd += f" --projection {projection}"
        raw = self._shell(cmd, timeout=90)
        if not raw or "Row:" not in raw:
            return []
        rows = []
        for line in raw.split("Row:"):
            line = line.strip()
            if not line:
                continue
            row = {}
            # Parse key=value pairs; values may contain commas
            pairs = re.split(r",\s*(?=\w+=)", line)
            for pair in pairs:
                if "=" in pair:
                    k, _, v = pair.partition("=")
                    row[k.strip()] = v.strip()
            rows.append(row)
        return rows

    # ------------------------------------------------------------------
    # Device Detection
    # ------------------------------------------------------------------

    @staticmethod
    def list_devices(adb_path="adb"):
        """Return a list of connected device serials."""
        try:
            result = subprocess.run(
                [adb_path, "devices", "-l"],
                capture_output=True, text=True, timeout=10
            )
            lines = result.stdout.strip().splitlines()
            devices = []
            for line in lines[1:]:  # skip the header
                line = line.strip()
                if not line or "offline" in line or "unauthorized" in line:
                    continue
                parts = line.split()
                if len(parts) >= 2 and parts[1] == "device":
                    info = {"serial": parts[0]}
                    for p in parts[2:]:
                        if ":" in p:
                            k, _, v = p.partition(":")
                            info[k] = v
                    devices.append(info)
            return devices
        except Exception as e:
            logger.error("list_devices error: %s", e)
            return []

    # ------------------------------------------------------------------
    # Device Info
    # ------------------------------------------------------------------

    def get_device_info(self):
        """Read device properties and return a dict."""
        props = {}
        raw = self._shell("getprop")
        for line in raw.splitlines():
            m = re.match(r"\[(.+?)\]:\s*\[(.*)]\s*$", line)
            if m:
                props[m.group(1)] = m.group(2)

        info = {
            "serial": self.serial,
            "manufacturer": props.get("ro.product.manufacturer", "Unknown"),
            "model": props.get("ro.product.model", "Unknown"),
            "android_version": props.get("ro.build.version.release", "Unknown"),
            "sdk_version": props.get("ro.build.version.sdk", "Unknown"),
            "build_fingerprint": props.get("ro.build.fingerprint", ""),
            "imei": self._get_imei(),
            "phone_number": self._get_phone_number(),
            "sim_operator": props.get("gsm.operator.alpha", props.get("gsm.sim.operator.alpha", "")),
            "storage_info": self._get_storage(),
            "battery_level": self._get_battery(),
            "is_rooted": self._check_root(),
        }
        self._audit("DEVICE_INFO", f"Read device info from {info['model']}")
        return info

    def _get_imei(self):
        out = self._shell("service call iphonesubinfo 1")
        # Try to parse the IMEI from the raw Parcel output
        digits = re.findall(r"'([0-9\.]+)'", out)
        imei = "".join(d.replace(".", "") for d in digits if d.replace(".", "").isdigit())
        imei = re.sub(r"\D", "", imei)
        if len(imei) >= 15:
            return imei[:15]
        # fallback via dumpsys
        out2 = self._shell("dumpsys iphonesubinfo")
        m = re.search(r"Device ID = ([0-9]+)", out2)
        return m.group(1) if m else "N/A"

    def _get_phone_number(self):
        out = self._shell("service call iphonesubinfo 11")
        digits = re.findall(r"'([0-9\+\-\.]+)'", out)
        number = "".join(d.replace(".", "") for d in digits)
        return number or "N/A"

    def _get_storage(self):
        out = self._shell("df /sdcard")
        lines = out.splitlines()
        if len(lines) >= 2:
            parts = lines[1].split()
            if len(parts) >= 4:
                return {"total": parts[1], "used": parts[2], "free": parts[3]}
        return {"total": "N/A", "used": "N/A", "free": "N/A"}

    def _get_battery(self):
        out = self._shell("dumpsys battery")
        m = re.search(r"level:\s*(\d+)", out)
        return f"{m.group(1)}%" if m else "N/A"

    def _check_root(self):
        out = self._shell("su -c 'echo rooted'")
        return "rooted" in out.lower()

    # ------------------------------------------------------------------
    # Call Logs
    # ------------------------------------------------------------------

    def extract_call_logs(self):
        """Extract all call logs. Returns list of dicts."""
        self._audit("EXTRACT_CALL_LOGS", "Starting call log extraction via content://call_log/calls")
        rows = self._content_query("content://call_log/calls")
        calls = []
        for r in rows:
            call_type_raw = r.get("type", r.get("calltype", "0"))
            ts_ms = r.get("date", "0")
            try:
                ts = datetime.datetime.utcfromtimestamp(int(ts_ms) / 1000)
            except Exception:
                ts = None
            calls.append({
                "number": r.get("number", ""),
                "name": r.get("cachedname", r.get("cached_name", "")),
                "call_type": ADB_CALL_TYPES.get(call_type_raw, f"type_{call_type_raw}"),
                "duration_seconds": int(r.get("duration", "0") or 0),
                "timestamp": ts,
                "geocoded_location": r.get("geocodedlocation", r.get("geocoded_location", "")),
                "raw_data": json.dumps(r),
            })
        # Also try alternate URI
        if not calls:
            rows2 = self._content_query("content://com.android.contacts/call_log/calls")
            for r in rows2:
                ts_ms = r.get("date", "0")
                try:
                    ts = datetime.datetime.utcfromtimestamp(int(ts_ms) / 1000)
                except Exception:
                    ts = None
                calls.append({
                    "number": r.get("number", ""),
                    "name": r.get("cachedname", ""),
                    "call_type": ADB_CALL_TYPES.get(r.get("type", "0"), "unknown"),
                    "duration_seconds": int(r.get("duration", "0") or 0),
                    "timestamp": ts,
                    "geocoded_location": "",
                    "raw_data": json.dumps(r),
                })
        self._audit("EXTRACT_CALL_LOGS", f"Extracted {len(calls)} call log records")
        logger.info("Extracted %d call logs", len(calls))
        return calls

    # ------------------------------------------------------------------
    # SMS / MMS
    # ------------------------------------------------------------------

    def extract_sms(self):
        """Extract SMS messages. Returns list of dicts."""
        self._audit("EXTRACT_SMS", "Starting SMS extraction via content://sms")
        rows = self._content_query("content://sms")
        messages = []
        for r in rows:
            ts_ms = r.get("date", "0")
            try:
                ts = datetime.datetime.utcfromtimestamp(int(ts_ms) / 1000)
            except Exception:
                ts = None
            msg_type = ADB_SMS_TYPES.get(r.get("type", "1"), "unknown")
            messages.append({
                "address": r.get("address", ""),
                "contact_name": r.get("contact_name", ""),
                "body": r.get("body", ""),
                "sms_type": msg_type,
                "timestamp": ts,
                "thread_id": r.get("thread_id", ""),
                "read": r.get("read", "1") == "1",
                "is_mms": False,
                "raw_data": json.dumps(r),
            })
        self._audit("EXTRACT_SMS", f"Extracted {len(messages)} SMS records")
        logger.info("Extracted %d SMS", len(messages))
        return messages

    def extract_mms(self):
        """Extract MMS messages."""
        self._audit("EXTRACT_MMS", "Starting MMS extraction via content://mms")
        rows = self._content_query("content://mms")
        messages = []
        for r in rows:
            ts = r.get("date", "0")
            try:
                ts_dt = datetime.datetime.utcfromtimestamp(int(ts))
            except Exception:
                ts_dt = None
            messages.append({
                "address": r.get("ct_l", ""),
                "contact_name": "",
                "body": r.get("sub", ""),
                "sms_type": "received" if r.get("m_type") == "132" else "sent",
                "timestamp": ts_dt,
                "thread_id": r.get("thread_id", ""),
                "read": r.get("read", "1") == "1",
                "is_mms": True,
                "mms_subject": r.get("sub", ""),
                "raw_data": json.dumps(r),
            })
        self._audit("EXTRACT_MMS", f"Extracted {len(messages)} MMS records")
        return messages

    # ------------------------------------------------------------------
    # Contacts
    # ------------------------------------------------------------------

    def extract_contacts(self):
        """Extract contacts from the device."""
        self._audit("EXTRACT_CONTACTS", "Extracting contacts via content://contacts/phones")
        rows = self._content_query("content://contacts/phones")
        # Try modern URI
        if not rows:
            rows = self._content_query("content://com.android.contacts/data/phones")
        contact_map = {}
        for r in rows:
            name = r.get("display_name", r.get("name", "Unknown"))
            number = r.get("number", r.get("data1", ""))
            cid = r.get("contact_id", r.get("_id", name))
            if cid not in contact_map:
                contact_map[cid] = {
                    "name": name,
                    "phone_numbers": [],
                    "emails": [],
                    "organization": r.get("company", ""),
                    "times_contacted": int(r.get("times_contacted", "0") or 0),
                    "last_contacted": None,
                    "raw_data": json.dumps(r),
                }
            if number:
                contact_map[cid]["phone_numbers"].append(number)
        # Try to get emails
        email_rows = self._content_query("content://com.android.contacts/data/emails")
        for r in email_rows:
            cid = r.get("contact_id", "")
            email = r.get("data1", "")
            if cid in contact_map and email:
                contact_map[cid]["emails"].append(email)

        contacts = list(contact_map.values())
        for c in contacts:
            c["phone_numbers"] = json.dumps(list(set(c["phone_numbers"])))
            c["emails"] = json.dumps(list(set(c["emails"])))
        self._audit("EXTRACT_CONTACTS", f"Extracted {len(contacts)} contacts")
        logger.info("Extracted %d contacts", len(contacts))
        return contacts

    # ------------------------------------------------------------------
    # Media Files (Photos, Videos, Audio)
    # ------------------------------------------------------------------

    def extract_media(self, evidence_dir=None):
        """Pull media files from device storage. Returns list of local paths."""
        self._audit("EXTRACT_MEDIA", "Starting media extraction from /sdcard")
        dest_dir = evidence_dir or self.evidence_dir
        media_dir = os.path.join(dest_dir, "media", self.serial or "device")
        os.makedirs(media_dir, exist_ok=True)

        # Pull common media directories
        source_dirs = [
            "/sdcard/DCIM",
            "/sdcard/Pictures",
            "/sdcard/Movies",
            "/sdcard/Download",
            "/sdcard/WhatsApp/Media",
            "/sdcard/Telegram",
            "/sdcard/Instagram",
        ]

        pulled_files = []
        for src in source_dirs:
            # check if dir exists
            check = self._shell(f"ls {src} 2>/dev/null | head -1")
            if not check or "No such file" in check:
                continue
            dest_sub = os.path.join(media_dir, src.replace("/sdcard/", "").replace("/", "_"))
            os.makedirs(dest_sub, exist_ok=True)
            logger.info("Pulling media from %s ...", src)
            result = self._run("pull", src, dest_sub, timeout=300)
            # Walk pulled files
            for root, dirs, files in os.walk(dest_sub):
                for f in files:
                    full = os.path.join(root, f)
                    pulled_files.append({"local_path": full, "source_path": src + "/" + f})

        self._audit("EXTRACT_MEDIA", f"Pulled {len(pulled_files)} media files")
        logger.info("Pulled %d media files total", len(pulled_files))
        return pulled_files

    # ------------------------------------------------------------------
    # App Database Extraction
    # ------------------------------------------------------------------

    def extract_app_dbs(self, evidence_dir=None):
        """Try to pull app databases (requires root or backup method)."""
        self._audit("EXTRACT_APP_DBS", "Attempting to pull app databases")
        dest_dir = evidence_dir or self.evidence_dir
        app_dir = os.path.join(dest_dir, "app_dbs", self.serial or "device")
        os.makedirs(app_dir, exist_ok=True)

        app_targets = {
            "whatsapp": {
                "package": "com.whatsapp",
                "db_path": "/data/data/com.whatsapp/databases/msgstore.db",
                "wa_path": "/sdcard/WhatsApp/Databases/msgstore.db.crypt15",
            },
            "telegram": {
                "package": "org.telegram.messenger",
                "db_path": "/data/data/org.telegram.messenger/files/cache4.db",
            },
            "instagram": {
                "package": "com.instagram.android",
                "db_path": "/data/data/com.instagram.android/databases/direct.db",
            },
            "browser_chrome": {
                "package": "com.android.chrome",
                "db_path": "/data/data/com.android.chrome/app_chrome/Default/History",
            },
            "browser_native": {
                "package": "com.android.browser",
                "db_path": "/data/data/com.android.browser/databases/browser2.db",
            },
            "gmail": {
                "package": "com.google.android.gm",
                "db_path": "/data/data/com.google.android.gm/databases/",
            },
            "sms_backup": {
                "package": "com.android.providers.telephony",
                "db_path": "/data/data/com.android.providers.telephony/databases/mmssms.db",
            },
            "contacts_backup": {
                "package": "com.android.providers.contacts",
                "db_path": "/data/data/com.android.providers.contacts/databases/contacts2.db",
            },
            "call_log_backup": {
                "package": "com.android.providers.contacts",
                "db_path": "/data/data/com.android.providers.contacts/databases/calllog.db",
            },
        }

        pulled_dbs = {}
        is_rooted = self._check_root()

        for app_name, info in app_targets.items():
            db_path = info.get("db_path", "")
            local_db = os.path.join(app_dir, f"{app_name}.db")

            # Method 1: Direct pull (works with root)
            if is_rooted and db_path:
                result = self._run("pull", db_path, local_db, timeout=60)
                if os.path.exists(local_db):
                    pulled_dbs[app_name] = {"path": local_db, "method": "root_pull"}
                    self._audit("EXTRACT_APP_DBS", f"Pulled {app_name} DB via root: {db_path}")
                    continue

            # Method 2: adb backup (no root needed for some apps)
            backup_file = os.path.join(app_dir, f"{app_name}.ab")
            if info.get("package"):
                pkg = info["package"]
                try:
                    subprocess.run(
                        [self.adb] + self._serial_flag + ["backup", "-noapk", pkg, "-f", backup_file],
                        timeout=30, capture_output=True
                    )
                    if os.path.exists(backup_file) and os.path.getsize(backup_file) > 50:
                        pulled_dbs[app_name] = {"path": backup_file, "method": "adb_backup", "format": "ab"}
                        self._audit("EXTRACT_APP_DBS", f"Backed up {app_name} via adb backup")
                        continue
                except Exception as e:
                    logger.debug("adb backup failed for %s: %s", app_name, e)

            # Method 3: run-as (for debuggable apps)
            if db_path:
                pkg = info.get("package", "")
                if pkg:
                    tmp_path = f"/sdcard/forensic_tmp_{app_name}.db"
                    cp_out = self._shell(f"run-as {pkg} cp {db_path} {tmp_path}")
                    pull_result = self._run("pull", tmp_path, local_db, timeout=30)
                    self._shell(f"rm -f {tmp_path}")
                    if os.path.exists(local_db):
                        pulled_dbs[app_name] = {"path": local_db, "method": "run_as"}
                        self._audit("EXTRACT_APP_DBS", f"Pulled {app_name} DB via run-as")

            # Method 4: WhatsApp public backup
            wa_public = info.get("wa_path", "")
            if wa_public and app_name == "whatsapp":
                local_wa = os.path.join(app_dir, "whatsapp_backup.crypt15")
                self._run("pull", wa_public, local_wa, timeout=60)
                if os.path.exists(local_wa):
                    pulled_dbs["whatsapp_crypt"] = {"path": local_wa, "method": "public_backup"}

        logger.info("Pulled app DBs for: %s", list(pulled_dbs.keys()))
        return pulled_dbs

    # ------------------------------------------------------------------
    # Browser History (direct content query)
    # ------------------------------------------------------------------

    def extract_browser_history(self):
        """Extract browser bookmarks and history via content query."""
        self._audit("EXTRACT_BROWSER", "Extracting browser history via content://browser/bookmarks")
        history = []
        rows = self._content_query("content://browser/bookmarks")
        if not rows:
            rows = self._content_query("content://com.android.browser.home/bookmarks")
        for r in rows:
            ts_ms = r.get("date", "0")
            try:
                ts = datetime.datetime.utcfromtimestamp(int(ts_ms) / 1000)
            except Exception:
                ts = None
            is_bookmark = r.get("bookmark", "0") == "1"
            history.append({
                "url": r.get("url", ""),
                "title": r.get("title", ""),
                "visits": int(r.get("visits", "1") or 1),
                "is_bookmark": is_bookmark,
                "timestamp": ts,
            })
        self._audit("EXTRACT_BROWSER", f"Extracted {len(history)} browser history records")
        return history

    # ------------------------------------------------------------------
    # Location (GPS logs via content providers)
    # ------------------------------------------------------------------

    def extract_locations_from_content(self):
        """Try to get location from Android location history providers."""
        self._audit("EXTRACT_LOCATION", "Extracting location from device content providers")
        locations = []
        # Google Location history (requires appropriate permissions)
        uris = [
            "content://com.google.android.gms.chimera.container/.location.LocationHistory",
            "content://com.google.android.location.history/locations",
        ]
        for uri in uris:
            rows = self._content_query(uri)
            for r in rows:
                try:
                    lat = float(r.get("latitude", 0))
                    lon = float(r.get("longitude", 0))
                    if lat and lon:
                        ts_ms = r.get("timestamp", r.get("time", "0"))
                        ts = datetime.datetime.utcfromtimestamp(int(ts_ms) / 1000) if ts_ms else None
                        locations.append({
                            "latitude": lat / 1e7 if abs(lat) > 90 else lat,
                            "longitude": lon / 1e7 if abs(lon) > 180 else lon,
                            "altitude": float(r.get("altitude", 0)),
                            "accuracy": float(r.get("accuracy", 0)),
                            "source": "gps_provider",
                            "source_ref": uri,
                            "timestamp": ts,
                        })
                except Exception:
                    pass
        return locations

    # ------------------------------------------------------------------
    # WiFi Networks
    # ------------------------------------------------------------------

    def extract_wifi_networks(self):
        """Extract saved WiFi networks."""
        self._audit("EXTRACT_WIFI", "Extracting WiFi network list")
        wifi = []
        raw = self._shell("cat /data/misc/wifi/WifiConfigStore.xml 2>/dev/null || cat /data/misc/wifi/wpa_supplicant.conf 2>/dev/null")
        # Simple SSID extraction
        ssids = re.findall(r'ssid="([^"]+)"', raw, re.IGNORECASE)
        ssids += re.findall(r'<string name="SSID">&quot;(.+?)&quot;</string>', raw)
        for s in set(ssids):
            wifi.append({"ssid": s})
        return wifi

    # ------------------------------------------------------------------
    # Full Acquisition Orchestrator
    # ------------------------------------------------------------------

    def full_acquisition(self, evidence_dir=None, progress_callback=None):
        """
        Run all extraction steps in sequence.
        progress_callback(step_name, progress_pct) called after each step.
        Returns a dict with all extracted data.
        """
        dest_dir = evidence_dir or self.evidence_dir
        results = {
            "device_info": {},
            "call_logs": [],
            "sms": [],
            "mms": [],
            "contacts": [],
            "media_files": [],
            "app_dbs": {},
            "browser_history": [],
            "locations": [],
            "wifi_networks": [],
            "errors": [],
        }

        steps = [
            ("Device Info", self.get_device_info, "device_info"),
            ("Call Logs", self.extract_call_logs, "call_logs"),
            ("SMS Messages", self.extract_sms, "sms"),
            ("MMS Messages", self.extract_mms, "mms"),
            ("Contacts", self.extract_contacts, "contacts"),
            ("Browser History", self.extract_browser_history, "browser_history"),
            ("Location Data", self.extract_locations_from_content, "locations"),
            ("WiFi Networks", self.extract_wifi_networks, "wifi_networks"),
        ]

        total = len(steps) + 2  # +2 for media and app dbs
        done = 0

        for step_name, func, key in steps:
            try:
                logger.info("Running step: %s", step_name)
                results[key] = func()
                done += 1
                if progress_callback:
                    progress_callback(step_name, int(done / total * 100))
            except Exception as e:
                logger.error("Error in %s: %s", step_name, e)
                results["errors"].append({"step": step_name, "error": str(e)})

        # Media (slow, pulls files)
        try:
            results["media_files"] = self.extract_media(evidence_dir=dest_dir)
            done += 1
            if progress_callback:
                progress_callback("Media Files", int(done / total * 100))
        except Exception as e:
            logger.error("Media extraction error: %s", e)
            results["errors"].append({"step": "Media Files", "error": str(e)})

        # App databases
        try:
            results["app_dbs"] = self.extract_app_dbs(evidence_dir=dest_dir)
            done += 1
            if progress_callback:
                progress_callback("App Databases", 100)
        except Exception as e:
            logger.error("App DB extraction error: %s", e)
            results["errors"].append({"step": "App Databases", "error": str(e)})

        self._audit("FULL_ACQUISITION", f"Acquisition complete. Errors: {len(results['errors'])}")
        return results
