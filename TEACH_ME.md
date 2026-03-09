# 📖 ForensicX — Complete Project Guide

> Everything you need to understand this project: what it does, how it works, every package used and why, and every important function explained.

---

## 🔍 What Is This Project?

**ForensicX** is a **Web-Based Mobile Forensics Platform**. It is a tool used by investigators to:

1. **Extract data from an Android phone** connected via USB/OTG cable
2. **Store and analyze that data** in a database on a computer
3. **View the evidence** through a beautiful web dashboard in the browser
4. **Generate a professional PDF report** with all findings

### Real-World Use Case
When police seize a suspect's phone, they use tools like ForensicX to:
- Pull **call logs** (who they called, how long, when)
- Pull **SMS messages** (what they texted)
- Pull **photos** (with hidden GPS location data baked in)
- Pull **WhatsApp chats**, browser history, emails
- Build a **timeline** of all activity
- Search for **keywords** like "transfer", "delete", "meet"
- Generate a **court-admissible PDF report** with chain of custody

---

## 🏗️ Project Structure

```
forensic/
│
├── backend/               ← Python/Flask server (the "brain")
│   ├── app.py             ← Starts the web server
│   ├── config.py          ← Settings and file paths
│   ├── models.py          ← Database table definitions
│   ├── routes.py          ← URL endpoints (API)
│   ├── seed_demo_data.py  ← Fills DB with fake data for testing
│   ├── requirements.txt   ← List of Python packages to install
│   │
│   ├── acquisition/       ← HOW data is pulled from the phone
│   │   └── adb_extractor.py
│   │
│   ├── parsers/           ← HOW pulled data is read and decoded
│   │   ├── media_parser.py
│   │   └── sqlite_parser.py
│   │
│   ├── analysis/          ← HOW data is analyzed
│   │   └── timeline.py
│   │
│   └── reporting/         ← HOW the PDF report is made
│       └── pdf_generator.py
│
├── frontend/              ← React website (what you see in browser)
│   └── src/
│       ├── App.jsx        ← Main layout + navigation
│       ├── index.css      ← All visual styling
│       └── pages/         ← Each page of the website
│           ├── Dashboard.jsx
│           ├── Cases.jsx
│           ├── DeviceConnect.jsx
│           ├── CallLogs.jsx
│           ├── SMSViewer.jsx
│           ├── Contacts.jsx
│           ├── MediaGallery.jsx
│           ├── AppDataPage.jsx
│           ├── EmailsPage.jsx
│           ├── LocationMap.jsx
│           ├── Timeline.jsx
│           ├── KeywordSearch.jsx
│           ├── AuditLog.jsx
│           └── ReportPage.jsx
│
├── start_backend.bat      ← Double-click to start backend
└── start_frontend.bat     ← Double-click to start frontend
```

---

## ⚙️ How It Works — Data Flow

```
  Android Phone
  (USB/OTG Cable)
       │
       ▼
  ADB (Android Debug Bridge)
  ← runs shell commands on the phone remotely →
       │
       ▼
  adb_extractor.py
  ← pulls: calls, SMS, contacts, photos, app DBs →
       │
       ▼
  Parsers (media_parser, sqlite_parser)
  ← reads the raw files, extracts meaning →
       │
       ▼
  Flask Backend + SQLite Database
  ← stores everything in tables →
       │
       ▼
  REST API (routes.py)
  ← serves data as JSON to the browser →
       │
       ▼
  React Frontend (browser)
  ← user sees dashboards, tables, maps, charts →
       │
       ▼
  PDF Report (pdf_generator.py)
  ← user downloads a forensic report →
```

---

## 📦 Python Packages (Backend) — What & Why

### `Flask` (core web framework)
- **What**: A lightweight Python web framework
- **Why**: It lets us create a web server with URL routes like `/api/cases` or `/api/evidence/1/calls`
- **Used in**: `app.py`, `routes.py`
- **Example**:
  ```python
  @app.route("/api/cases")   # when browser visits this URL...
  def list_cases():
      return jsonify(cases)  # ...send back JSON data
  ```

### `Flask-SQLAlchemy`
- **What**: Connects Flask to a SQL database using Python objects
- **Why**: Instead of writing raw SQL, we define Python classes and they become database tables automatically
- **Used in**: `models.py`, `routes.py`
- **Example**:
  ```python
  class CallLog(db.Model):   # This becomes a "call_logs" table
      number = db.Column(db.String(32))   # column: phone number
      duration_seconds = db.Column(db.Integer)  # column: duration
  ```

### `Flask-CORS`
- **What**: Cross-Origin Resource Sharing header handler
- **Why**: Without this, the browser blocks React (port 5173) from talking to Flask (port 5000). This package allows it.
- **Used in**: `app.py`
- **Example**: `CORS(app, origins=["http://localhost:5173"])`

### `Flask-Migrate` + `alembic`
- **What**: Database migration tool
- **Why**: Lets you change the database schema (add/remove columns) without losing data

### `SQLAlchemy`
- **What**: The underlying ORM (Object Relational Mapper)
- **Why**: Translates Python code into SQL database queries
- **Example**: `CallLog.query.filter_by(device_id=1).all()` becomes `SELECT * FROM call_logs WHERE device_id=1`

### `Pillow`
- **What**: Python Imaging Library — reads and edits image files
- **Why**: Used to open photos and extract EXIF metadata (camera info, GPS coordinates), and to generate thumbnail images
- **Used in**: `parsers/media_parser.py`
- **Example**:
  ```python
  from PIL import Image
  with Image.open("photo.jpg") as img:
      exif = img._getexif()   # get hidden camera data
      gps_info = exif["GPSInfo"]  # get GPS coordinates!
  ```

### `reportlab`
- **What**: Professional PDF generation library
- **Why**: Creates the forensic PDF report with tables, headers, images, colors
- **Used in**: `reporting/pdf_generator.py`
- **Example**:
  ```python
  from reportlab.platypus import Table, TableStyle
  t = Table(data)  # create a table
  doc.build(story) # render the PDF
  ```

### `python-dotenv`
- **What**: Reads `.env` files for environment variables
- **Why**: Keeps secrets (like API keys, database passwords) out of code

### `psutil`
- **What**: System and process utilities
- **Why**: Can check system info, running processes, network connections

### `python-dateutil`
- **What**: Powerful date/time parsing library
- **Why**: Android timestamps come in many formats (milliseconds, Unix time, etc.) — this helps parse them

### `exifread`
- **What**: Reads EXIF metadata from image files
- **Why**: Alternative to Pillow's EXIF reader — more detailed GPS/camera data extraction
- **Used in**: `parsers/media_parser.py`

### `requests`
- **What**: HTTP library for making web requests
- **Why**: Useful for making API calls from backend code (e.g., reverse geocoding GPS to address)

### `subprocess` (built-in Python)
- **What**: Runs external programs from Python
- **Why**: Runs ADB commands on the connected Android phone
- **Used in**: `acquisition/adb_extractor.py`
- **Example**:
  ```python
  import subprocess
  result = subprocess.run(["adb", "shell", "content", "query",
                          "--uri", "content://sms"],
                          capture_output=True, text=True)
  print(result.stdout)  # raw SMS data from phone
  ```

### `sqlite3` (built-in Python)
- **What**: Reads SQLite database files
- **Why**: Android apps store data in SQLite `.db` files. This module opens and queries them.
- **Used in**: `parsers/sqlite_parser.py`
- **Example**:
  ```python
  conn = sqlite3.connect("msgstore.db")       # open WhatsApp DB
  rows = conn.execute("SELECT * FROM messages") # get all messages
  ```

### `json` (built-in Python)
- **What**: Converts between Python dictionaries and JSON strings
- **Why**: All API responses are in JSON format

### `hashlib` (built-in Python)
- **What**: Cryptographic hash functions
- **Why**: We compute SHA-256 hash of every extracted file to prove it wasn't tampered with (chain of custody)
- **Example**:
  ```python
  import hashlib
  h = hashlib.sha256()
  h.update(file_bytes)
  hash_value = h.hexdigest()  # "a3f7bc..." — unique fingerprint
  ```

### `threading` (built-in Python)
- **What**: Run code in parallel threads
- **Why**: Data extraction takes minutes. We run it in a background thread so the web UI stays responsive and can show a progress bar
- **Used in**: `routes.py`

### `re` (built-in Python)
- **What**: Regular expressions — pattern matching in text
- **Why**: ADB output is raw text — we use regex to extract values like IMEI numbers, property values

---

## 📦 npm Packages (Frontend) — What & Why

### `react` + `react-dom`
- **What**: Facebook's UI library for building interactive interfaces
- **Why**: Everything in the browser is built with React components
- **Example**: `<CallLogs />` is a React component that shows call log data

### `vite`
- **What**: Super-fast development build tool
- **Why**: Replaces old Create React App. Starts the dev server in milliseconds with hot-reloading (changes appear instantly in browser)

### `react-router-dom`
- **What**: Client-side routing for React
- **Why**: Lets users navigate between pages (Dashboard → Call Logs → Timeline) without page reloads
- **Used in**: `App.jsx`
- **Example**:
  ```jsx
  <Route path="/evidence/:deviceId/calls" element={<CallLogs />} />
  // When URL is /evidence/1/calls → show CallLogs component
  ```

### `recharts`
- **What**: Chart library built for React
- **Why**: Draws the bar charts and line charts on the Dashboard
- **Used in**: `Dashboard.jsx`
- **Example**:
  ```jsx
  <BarChart data={chartData}>
    <Bar dataKey="value" />
  </BarChart>
  ```

### `lucide-react`
- **What**: Beautiful icon library with 1000+ SVG icons
- **Why**: All UI icons (Phone, Mail, Shield, MapPin etc.) come from here
- **Used in**: Every page
- **Example**: `<Phone size={16} color="var(--cyan)" />`

### `leaflet` (loaded at runtime, not npm)
- **What**: Open-source interactive map library
- **Why**: Shows GPS location pins on the Location Map page, using dark CartoDB map tiles
- **Used in**: `LocationMap.jsx`

---

## 🔧 Key Functions Explained

### `backend/acquisition/adb_extractor.py`

#### `ADBExtractor.__init__()`
Sets up the extractor with ADB path, the target device serial number, and a callback for audit logging.

#### `ADBExtractor._run(*args)`
Core helper — runs any ADB command and returns the output as text:
```python
result = self._run("shell", "getprop", "ro.product.model")
# Equivalent to running: adb shell getprop ro.product.model
```

#### `ADBExtractor._content_query(uri)`
Runs `adb shell content query --uri <uri>` and parses the `Row: key=value, key=value` output into a list of Python dictionaries. This is how we get SMS, calls, contacts from Android's content providers.

#### `ADBExtractor.list_devices(adb_path)` — **Static method**
Runs `adb devices -l` and returns a list of connected device serials. This is what the "Scan" button calls.

#### `ADBExtractor.get_device_info()`
Reads all device properties using `getprop`, and extracts:
- Manufacturer, model, Android version from `ro.product.*`
- IMEI using `service call iphonesubinfo 1`
- Phone number using `service call iphonesubinfo 11`
- Battery level from `dumpsys battery`
- Root status by attempting `su -c 'echo rooted'`

#### `ADBExtractor.extract_call_logs()`
Queries `content://call_log/calls` and maps raw type numbers to labels:
- `"1"` → `"incoming"`, `"2"` → `"outgoing"`, `"3"` → `"missed"`, etc.
- Timestamps are Unix milliseconds → converted to readable datetime

#### `ADBExtractor.extract_sms()` / `extract_mms()`
Queries `content://sms` and `content://mms` and maps type numbers:
- `"1"` → `"received"`, `"2"` → `"sent"`, `"3"` → `"draft"`

#### `ADBExtractor.extract_contacts()`
Queries `content://contacts/phones` and groups results by `contact_id` so each person has one record with all their phone numbers and emails.

#### `ADBExtractor.extract_media()`
Pulls entire folders from the phone using `adb pull`:
- `/sdcard/DCIM` (Camera photos)
- `/sdcard/Pictures`
- `/sdcard/Movies`
- `/sdcard/Download`
- `/sdcard/WhatsApp/Media`

#### `ADBExtractor.extract_app_dbs()`
Tries to pull app databases using **4 different methods** (in order):
1. **Root Pull**: `adb pull /data/data/com.whatsapp/databases/msgstore.db` (needs rooted phone)
2. **ADB Backup**: `adb backup -noapk com.whatsapp` (works for some apps)
3. **Run-As**: `adb shell run-as com.whatsapp cp <db> /sdcard/tmp` (works for debug builds)
4. **Public Backup**: Pulls WhatsApp's encrypted backup from `/sdcard/WhatsApp/Databases/`

#### `ADBExtractor.full_acquisition()`
**The master function** — calls all extraction steps in sequence, firing progress callbacks so the UI can show a progress bar. Returns everything in one dict.

---

### `backend/parsers/media_parser.py`

#### `parse_media_file(file_path, thumbnail_dir)`
Opens an image file and:
1. Reads dimensions (`img.width`, `img.height`)
2. Reads EXIF data with `img._getexif()` 
3. Extracts `DateTimeOriginal` → file timestamp
4. Extracts `GPSInfo` → converts DMS (degrees/minutes/seconds) to decimal latitude/longitude
5. Generates a 320×320 thumbnail saved as JPEG

#### `_gps_to_decimal(gps_tuple, ref)`
Converts GPS coordinates from EXIF format (degrees, minutes, seconds + N/S/E/W reference) to simple decimal degrees. Example: `(28, 36, 50.4, "N")` → `28.6140`

#### `_sha256(path)`
Reads a file in 1MB chunks and computes its SHA-256 hash — used to prove the file hasn't been modified since extraction.

#### `parse_media_directory(directory)`
Walks an entire folder recursively and runs `parse_media_file` on every image/video/audio file found.

---

### `backend/parsers/sqlite_parser.py`

#### `parse_whatsapp_db(db_path)`
Opens `msgstore.db` (WhatsApp's SQLite database) and queries the `messages` table. Maps `key_from_me=0` → "received", `key_from_me=1` → "sent". Extracts JID (WhatsApp ID like `919876543210@s.whatsapp.net`) and strips the phone number.

#### `parse_browser_db(db_path)`
Handles two formats:
- **Chrome**: queries `urls` table. Chrome stores time as microseconds since 1601-01-01 (not 1970!), so it subtracts 11,644,473,600 seconds to convert.
- **Native Android browser**: queries `bookmarks` table.

#### `parse_sms_db(db_path)`
Reads the native Android `mmssms.db` file (raw database backup of all SMS). Same data as the content provider query but from the file itself — useful when root access is available.

#### `parse_contacts_db(db_path)`
Joins `contacts` and `data` tables in `contacts2.db`, filtering mimetype for phone numbers (`vnd.android.cursor.item/phone_v2`) and emails (`vnd.android.cursor.item/email_v2`).

#### `parse_calllog_db(db_path)` 
Reads `calllog.db` directly and maps type integers to call type names.

#### `parse_gmail_db(db_path)`
Queries Gmail's `messages` table for subject, sender, recipients, timestamp (stored as milliseconds).

---

### `backend/analysis/timeline.py`

#### `build_timeline(device_id, call_logs, sms_messages, media_files, app_data, emails, locations)`
Takes all evidence types and merges them into a single list. Each entry has:
- `timestamp` — when it happened
- `event_type` — "call", "sms", "media", "app_data", "email", "location"
- `summary` — human-readable description (e.g. "Incoming call from +91-98765-43210 (3m 42s)")
- `icon` — Lucide icon name for the UI

Sorts everything by timestamp descending (newest first). This creates the unified timeline view.

#### `keyword_search(keyword, call_logs, sms_messages, app_data, emails)`
Case-insensitive string search across all text fields:
- Call logs: checks `number` and `name`
- SMS: checks `body` and `address`
- App data: checks `content`
- Emails: checks `subject` and `body`

Returns a list of "hits" with the matching snippet and the original record for display.

---

### `backend/reporting/pdf_generator.py`

#### `generate_report(output_path, case_data, device_data, ...)`
Builds a professional multi-section PDF using ReportLab's `SimpleDocTemplate` and `Platypus` (layout engine). Sections:
1. **Cover Page** — Case info + device metadata tables
2. **Evidence Summary** — Table with counts of all evidence
3. **Call Logs** — Up to 100 rows, color-coded by type
4. **SMS / MMS** — Up to 100 messages
5. **Contacts** — Up to 80 contacts
6. **Media Files** — File inventory + thumbnail grid (24 thumbnails)
7. **App Data** — WhatsApp, browser, social media records
8. **Emails** — Subject, sender, date table
9. **Chain of Custody** — Full audit log table

#### `_header_footer(canvas, doc)`
A callback function called on every page. Draws:
- Dark blue header bar with "MOBILE FORENSICS REPORT — CONFIDENTIAL" text and page number
- Dark blue footer bar with generation timestamp

---

### `backend/routes.py`

#### `list_cases()` / `create_case()` / `get_case()` / `update_case()`
Basic CRUD (Create Read Update Delete) for investigation cases.

#### `list_adb_devices()`
Calls `ADBExtractor.list_devices()` and returns JSON list of connected phone serials.

#### `start_extraction()`
- Creates a `Device` record in the DB
- Logs an audit entry: "EXTRACTION_STARTED"
- Spawns a **background thread** calling `_run_extraction()`
- Returns `{"device_id": 1}` immediately so UI doesn't hang

#### `_run_extraction(device_id, serial, case_id, app)`
**The big orchestrator** running inside a thread:
1. Get device info → update DB record
2. Extract call logs → save each as `CallLog` row
3. Extract SMS + MMS → save as `SMS` rows
4. Extract contacts → save as `Contact` rows
5. Pull media files → parse EXIF → save as `MediaFile` rows → auto-add GPS as `Location` rows
6. Pull app databases → parse each (WhatsApp/Chrome/Gmail) → save as `AppData` / `Email` rows
7. Extract location data from content providers → save as `Location` rows
8. Mark device `acquisition_status = "completed"`

Updates `_extraction_status[device_id]` dict at each step so the frontend progress bar can poll `/api/devices/extract/status/<id>`.

#### `get_timeline(device_id)`
Fetches all evidence from DB, calls `build_timeline()`, returns JSON list of all events sorted by time.

#### `search_evidence(device_id)`
Takes `?q=keyword` from URL, fetches all evidence, calls `keyword_search()`, returns hits.

#### `generate_report_endpoint(device_id)`
Fetches all evidence, calls `generate_report()`, returns the PDF file as a download response.

#### `get_audit_log()`
Returns all `AuditLog` entries — every action ever taken on the evidence.

---

### `backend/models.py` — Database Tables

| Model | Table | What it stores |
|---|---|---|
| `Case` | `cases` | Investigation case (number, title, investigator, agency) |
| `Device` | `devices` | The phone (model, IMEI, status, acquisition info) |
| `CallLog` | `call_logs` | One row per call (number, type, duration, timestamp) |
| `SMS` | `sms_messages` | One row per message (address, body, type, thread) |
| `Contact` | `contacts` | One row per person (name, phones JSON, emails JSON) |
| `MediaFile` | `media_files` | One row per file (name, hash, GPS, camera, thumbnail) |
| `AppData` | `app_data` | One row per app message/event (WhatsApp, Chrome, etc.) |
| `Email` | `emails` | One row per email (sender, recipients, subject, body) |
| `Location` | `locations` | One row per location pin (lat, lon, source, timestamp) |
| `AuditLog` | `audit_logs` | One row per action (chain of custody entries) |

Each model has a `.to_dict()` method that converts the Python object to a JSON-safe dictionary for the API.

---

### `backend/seed_demo_data.py`

Creates **realistic synthetic data** without needing a real phone:
- 1 case (Operation Shadow Network)
- 1 device (Samsung Galaxy S23 Ultra)
- 120 call logs with random types, durations, names
- 85 SMS + 12 MMS with suspicious-looking content
- 245 contacts
- 312 media files with fake GPS coordinates across India
- 150 WhatsApp messages, 45 browser history, 30 Instagram DMs
- 60 emails
- Location pins in Mumbai, Delhi, Bangalore, Chennai, Hyderabad
- 13 chain-of-custody audit log entries

---

## 🌐 React Pages — What Each Does

| Page | File | What it shows |
|---|---|---|
| Dashboard | `Dashboard.jsx` | Stats overview, bar chart, quick navigation, recent cases |
| Cases | `Cases.jsx` | List of investigations, form to create new case |
| Device Connect | `DeviceConnect.jsx` | ADB scanner, extraction wizard, real-time progress bar |
| Call Logs | `CallLogs.jsx` | Searchable table of calls with duration, type badges |
| SMS Viewer | `SMSViewer.jsx` | WhatsApp-style threaded conversation view |
| Contacts | `Contacts.jsx` | Contact list with phones, emails, organization |
| Media Gallery | `MediaGallery.jsx` | Photo/video grid with EXIF lightbox + Google Maps link |
| App Data | `AppDataPage.jsx` | WhatsApp, Chrome, Instagram records with app filter |
| Emails | `EmailsPage.jsx` | Two-pane email client view (list + body) |
| Location Map | `LocationMap.jsx` | Leaflet dark map with color-coded pins by source |
| Timeline | `Timeline.jsx` | Chronological feed of all 1056 events |
| Keyword Search | `KeywordSearch.jsx` | Search with highlighted matches in results |
| Audit Log | `AuditLog.jsx` | Chain of custody table (immutable) |
| Report | `ReportPage.jsx` | One-click PDF generation and download |

---

## 🔐 Legal & Forensics Concepts Used

### Chain of Custody
Every action is recorded in `AuditLog`: who did what, when, what device, what for. This proves the evidence hasn't been tampered with in court.

### Evidence Integrity (SHA-256 Hashing)
Every file extracted from the phone is hashed. If the hash matches later, the file is unchanged. Used in `media_parser.py`.

### Logical Acquisition
Pulling data using ADB (Android Debug Bridge) without physically touching the storage chip. Less invasive. Used for calls, SMS, media.

### Content Providers
Android exposes data through URIs like `content://sms`, `content://call_log/calls`. These are the official APIs to read phone data — same system that apps like Contacts or Messaging use.

### EXIF Data
Hidden metadata embedded in every JPEG photo. Includes: camera make/model, date taken, **GPS latitude/longitude**. We extract this to show where a photo was taken.

### SQLite
Android apps store almost everything in SQLite `.db` files. WhatsApp's messages DB, browser history, Gmail — all SQLite. We open these files and query them.

---

## 🚀 How to Run the Project

### Step 1 — Install Dependencies (once)
```bat
cd forensic\backend
pip install -r requirements.txt
cd ..\frontend
npm install
```

### Step 2 — Seed Demo Data (once)
```bat
cd forensic\backend
python seed_demo_data.py
```

### Step 3 — Start Backend (Terminal 1)
```bat
cd forensic\backend
python app.py
# Server runs at: http://localhost:5000
```

### Step 4 — Start Frontend (Terminal 2)
```bat
cd forensic\frontend
npm run dev
# Website runs at: http://localhost:5173
```

**Or just double-click**: `start_backend.bat` and `start_frontend.bat`

---

## 📡 API Quick Reference

| Method | URL | What it does |
|---|---|---|
| GET | `/api/health` | Check if backend is running |
| GET | `/api/cases` | Get all cases |
| POST | `/api/cases` | Create new case |
| GET | `/api/devices/list-adb` | Scan for connected phones |
| POST | `/api/devices/extract` | Start extraction (non-blocking) |
| GET | `/api/devices/extract/status/<id>` | Get extraction progress % |
| GET | `/api/evidence/<id>/stats` | Count of each evidence type |
| GET | `/api/evidence/<id>/calls` | Call logs (paginated, searchable) |
| GET | `/api/evidence/<id>/sms` | SMS messages (paginated) |
| GET | `/api/evidence/<id>/contacts` | Contacts (paginated) |
| GET | `/api/evidence/<id>/media` | Media files (filterable by type) |
| GET | `/api/evidence/<id>/apps` | App data (filterable by app) |
| GET | `/api/evidence/<id>/emails` | Emails |
| GET | `/api/evidence/<id>/locations` | GPS location pins |
| GET | `/api/evidence/<id>/timeline` | All events chronologically |
| GET | `/api/evidence/<id>/search?q=word` | Keyword search across all evidence |
| POST | `/api/report/<id>` | Generate + download PDF report |
| GET | `/api/audit` | Chain of custody log |

---

*ForensicX — Built with Python/Flask + React. For educational and authorized forensic use only.*
