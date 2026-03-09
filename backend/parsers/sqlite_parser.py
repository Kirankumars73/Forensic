"""
SQLite DB parser for Android app databases:
WhatsApp, browser history, contacts2.db, mmssms.db, etc.
"""
import os
import sqlite3
import datetime
import json
import logging

logger = logging.getLogger(__name__)


def _open_db(db_path):
    """Open a SQLite DB in read-only mode (copies to temp if needed)."""
    try:
        conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
        conn.row_factory = sqlite3.Row
        return conn
    except Exception:
        try:
            conn = sqlite3.connect(db_path)
            conn.row_factory = sqlite3.Row
            return conn
        except Exception as e:
            logger.error("Cannot open DB %s: %s", db_path, e)
            return None


def parse_whatsapp_db(db_path):
    """Parse WhatsApp msgstore.db and return list of messages."""
    conn = _open_db(db_path)
    if not conn:
        return []
    messages = []
    try:
        # WhatsApp schema (varies by version, try common column names)
        tables = [r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
        if "messages" in tables:
            cur = conn.execute("""
                SELECT
                    COALESCE(key_remote_jid, remote_jid, '') as jid,
                    COALESCE(key_from_me, from_me, 0) as from_me,
                    COALESCE(data, body, '') as content,
                    COALESCE(timestamp, 0) as ts,
                    status, media_url, media_name, latitude, longitude
                FROM messages
                ORDER BY timestamp DESC
                LIMIT 5000
            """)
            for row in cur.fetchall():
                ts_ms = row["ts"] or 0
                try:
                    ts = datetime.datetime.utcfromtimestamp(int(ts_ms) / 1000)
                except Exception:
                    ts = None
                jid = str(row["jid"] or "")
                phone = jid.split("@")[0] if "@" in jid else jid
                sender = "Me" if int(row["from_me"] or 0) else phone
                messages.append({
                    "app_name": "whatsapp",
                    "package": "com.whatsapp",
                    "data_type": "message",
                    "sender": sender,
                    "recipient": phone if sender == "Me" else "Me",
                    "content": str(row["content"] or ""),
                    "timestamp": ts,
                    "extra_metadata": json.dumps({
                        "status": row["status"],
                        "media_url": row["media_url"],
                        "media_name": row["media_name"],
                        "latitude": row["latitude"],
                        "longitude": row["longitude"],
                    }),
                })
    except Exception as e:
        logger.warning("WhatsApp DB parse error: %s", e)
    finally:
        conn.close()
    return messages


def parse_browser_db(db_path):
    """Parse Android browser2.db or Chrome History SQLite DB."""
    conn = _open_db(db_path)
    if not conn:
        return []
    records = []
    try:
        tables = [r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
        # Chrome History format
        if "urls" in tables:
            cur = conn.execute("SELECT url, title, visit_count, last_visit_time FROM urls ORDER BY last_visit_time DESC LIMIT 2000")
            for row in cur.fetchall():
                ts_us = row["last_visit_time"] or 0
                try:
                    # Chrome time: microseconds since 1601-01-01
                    epoch_diff = 11644473600  # seconds between 1601 and 1970
                    ts = datetime.datetime.utcfromtimestamp(ts_us / 1e6 - epoch_diff)
                except Exception:
                    ts = None
                records.append({
                    "app_name": "chrome",
                    "package": "com.android.chrome",
                    "data_type": "history",
                    "sender": "",
                    "recipient": "",
                    "content": f"[{row['title']}] {row['url']}",
                    "timestamp": ts,
                    "extra_metadata": json.dumps({"url": row["url"], "visit_count": row["visit_count"]}),
                })
        elif "bookmarks" in tables:
            # Native browser
            cur = conn.execute("SELECT url, title, date, visits FROM bookmarks ORDER BY date DESC LIMIT 2000")
            for row in cur.fetchall():
                ts_ms = row["date"] or 0
                try:
                    ts = datetime.datetime.utcfromtimestamp(int(ts_ms) / 1000)
                except Exception:
                    ts = None
                records.append({
                    "app_name": "browser",
                    "package": "com.android.browser",
                    "data_type": "history",
                    "sender": "",
                    "recipient": "",
                    "content": f"[{row['title']}] {row['url']}",
                    "timestamp": ts,
                    "extra_metadata": json.dumps({"url": row["url"], "visits": row["visits"]}),
                })
    except Exception as e:
        logger.warning("Browser DB parse error: %s", e)
    finally:
        conn.close()
    return records


def parse_sms_db(db_path):
    """Parse mmssms.db for SMS/MMS data."""
    conn = _open_db(db_path)
    if not conn:
        return []
    messages = []
    try:
        cur = conn.execute(
            "SELECT address, date, type, body, thread_id, read, subject FROM sms ORDER BY date DESC LIMIT 5000"
        )
        SMS_TYPES = {"1": "received", "2": "sent", "3": "draft"}
        for row in cur.fetchall():
            ts_ms = row["date"] or 0
            try:
                ts = datetime.datetime.utcfromtimestamp(int(ts_ms) / 1000)
            except Exception:
                ts = None
            messages.append({
                "address": str(row["address"] or ""),
                "contact_name": "",
                "body": str(row["body"] or ""),
                "sms_type": SMS_TYPES.get(str(row["type"]), "unknown"),
                "timestamp": ts,
                "thread_id": str(row["thread_id"] or ""),
                "read": int(row["read"] or 0) == 1,
                "is_mms": False,
                "raw_data": json.dumps(dict(row)),
            })
    except Exception as e:
        logger.warning("SMS DB parse error: %s", e)
    finally:
        conn.close()
    return messages


def parse_contacts_db(db_path):
    """Parse contacts2.db for contacts."""
    conn = _open_db(db_path)
    if not conn:
        return []
    contacts = {}
    try:
        cur = conn.execute("""
            SELECT c.display_name, d.data1, d.mimetype
            FROM contacts c
            JOIN data d ON d.contact_id = c._id
            WHERE d.mimetype IN ('vnd.android.cursor.item/phone_v2','vnd.android.cursor.item/email_v2')
        """)
        for row in cur.fetchall():
            name = row[0] or "Unknown"
            val = row[1] or ""
            mime = row[2] or ""
            if name not in contacts:
                contacts[name] = {"name": name, "phone_numbers": [], "emails": [], "organization": ""}
            if "phone" in mime:
                contacts[name]["phone_numbers"].append(val)
            elif "email" in mime:
                contacts[name]["emails"].append(val)
    except Exception as e:
        logger.warning("Contacts DB parse: %s", e)
    finally:
        conn.close()
    result = []
    for c in contacts.values():
        c["phone_numbers"] = json.dumps(list(set(c["phone_numbers"])))
        c["emails"] = json.dumps(list(set(c["emails"])))
        result.append(c)
    return result


def parse_calllog_db(db_path):
    """Parse calllog.db for call records."""
    conn = _open_db(db_path)
    if not conn:
        return []
    calls = []
    CALL_TYPES = {"1": "incoming", "2": "outgoing", "3": "missed"}
    try:
        cur = conn.execute(
            "SELECT number, date, duration, type, geocodedLocation, name FROM calls ORDER BY date DESC LIMIT 5000"
        )
        for row in cur.fetchall():
            ts_ms = row["date"] or 0
            try:
                ts = datetime.datetime.utcfromtimestamp(int(ts_ms) / 1000)
            except Exception:
                ts = None
            calls.append({
                "number": str(row["number"] or ""),
                "name": str(row["name"] or ""),
                "call_type": CALL_TYPES.get(str(row["type"]), "unknown"),
                "duration_seconds": int(row["duration"] or 0),
                "timestamp": ts,
                "geocoded_location": str(row["geocodedLocation"] or ""),
                "raw_data": json.dumps(dict(row)),
            })
    except Exception as e:
        logger.warning("Call log DB parse: %s", e)
    finally:
        conn.close()
    return calls


def parse_gmail_db(db_path):
    """Parse Gmail/Email provider database for emails."""
    conn = _open_db(db_path)
    if not conn:
        return []
    emails = []
    try:
        tables = [r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
        if "messages" in tables:
            cur = conn.execute("""
                SELECT fromAddress, toAddresses, subject, snippet, dateReceivedMs, read, hasAttachments
                FROM messages ORDER BY dateReceivedMs DESC LIMIT 1000
            """)
            for row in cur.fetchall():
                ts_ms = row["dateReceivedMs"] or 0
                try:
                    ts = datetime.datetime.utcfromtimestamp(int(ts_ms) / 1000)
                except Exception:
                    ts = None
                to_list = str(row["toAddresses"] or "").split(",")
                emails.append({
                    "account": "",
                    "folder": "inbox",
                    "sender": str(row["fromAddress"] or ""),
                    "recipients": json.dumps([r.strip() for r in to_list if r.strip()]),
                    "subject": str(row["subject"] or ""),
                    "body": str(row["snippet"] or ""),
                    "timestamp": ts,
                    "has_attachments": bool(row["hasAttachments"]),
                    "message_id": "",
                })
    except Exception as e:
        logger.warning("Gmail DB parse: %s", e)
    finally:
        conn.close()
    return emails
