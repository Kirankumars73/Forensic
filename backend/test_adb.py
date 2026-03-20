"""
test_adb.py - Direct ADB extraction test for calls and SMS
Run this from the backend directory:  python test_adb.py

It will:
1. List connected ADB devices
2. Extract call logs from the first authorized device
3. Extract SMS from the first authorized device
4. Print results to console

No database needed - pure standalone test.
"""
import sys
import json
import os

# Add backend to path
sys.path.insert(0, os.path.dirname(__file__))

from config import Config
from acquisition.adb_extractor import ADBExtractor

ADB_PATH = Config.ADB_PATH  # from config.py (platform-tools adb.exe)


def main():
    print("=" * 60)
    print("  ForensicX - ADB Extraction Test")
    print("=" * 60)

    # 1. List devices
    print("\n[1] Scanning for connected devices...")
    result = ADBExtractor.list_devices(ADB_PATH)

    if result["error"]:
        print(f"  ERROR: {result['error']}")
        print("  Make sure ADB is installed and in PATH.")
        return

    for warn in result["warnings"]:
        print(f"  WARNING: {warn}")

    devices = result["devices"]
    if not devices:
        print("  No authorized devices found.")
        print("  -> Connect your Android phone via USB")
        print("  -> Enable Developer Options > USB Debugging")
        print("  -> Accept the 'Allow USB debugging' prompt on the phone")
        return

    print(f"  Found {len(devices)} device(s):")
    for d in devices:
        print(f"    Serial: {d['serial']}  Model: {d.get('model', 'N/A')}")

    serial = devices[0]["serial"]
    print(f"\n  Using device: {serial}")

    # 2. Init extractor
    adb = ADBExtractor(
        adb_path=ADB_PATH,
        evidence_dir="evidence_store",
        device_serial=serial,
    )

    # 3. Extract call logs
    print("\n[2] Extracting call logs (content://call_log/calls)...")
    try:
        calls = adb.extract_call_logs()
        print(f"  ✅ Extracted {len(calls)} call log records")
        if calls:
            print("\n  --- First 5 calls ---")
            for c in calls[:5]:
                print(f"    {str(c['call_type']):10s} | {str(c['number']):20s} | {str(c['timestamp'])[:16]} | {c['duration_seconds']}s")
        else:
            print("  No call records found (phone may have no call history, or ADB permission denied)")
    except Exception as e:
        print(f"  ERROR extracting calls: {e}")

    # 4. Extract SMS
    print("\n[3] Extracting SMS (content://sms)...")
    try:
        sms = adb.extract_sms()
        print(f"  ✅ Extracted {len(sms)} SMS records")
        if sms:
            print("\n  --- First 5 SMS ---")
            for m in sms[:5]:
                body_preview = (m.get("body") or "")[:60].replace("\n", " ")
                print(f"    [{str(m['sms_type']):8s}] {str(m['address']):20s} | {body_preview}")
        else:
            print("  No SMS found (phone may have no messages, or ADB permission denied)")
    except Exception as e:
        print(f"  ERROR extracting SMS: {e}")

    # 5. Extract contacts
    print("\n[4] Extracting contacts...")
    try:
        contacts = adb.extract_contacts()
        print(f"  ✅ Extracted {len(contacts)} contacts")
        if contacts:
            for c in contacts[:3]:
                phones = json.loads(c.get("phone_numbers") or "[]")
                print(f"    {str(c['name']):30s} | {', '.join(phones[:2])}")
    except Exception as e:
        print(f"  ERROR extracting contacts: {e}")

    print("\n" + "=" * 60)
    print("  Test complete! If extraction worked, run 'python seed_demo_data.py'")
    print("  to load demo data, or use Device/Extract page to run full acquisition.")
    print("=" * 60)


if __name__ == "__main__":
    main()
