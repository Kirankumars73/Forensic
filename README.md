# 🔍 ForensicX — Mobile Digital Forensics Tool

A full-stack digital forensics application for extracting, analysing, and reporting evidence from Android devices via ADB (Android Debug Bridge). Built with a **Python Flask** backend and a **React (Vite)** frontend.

---

## ✨ Features

| Module | Description |
|---|---|
| 📱 **ADB Extraction** | Extract call logs, SMS messages, and contacts directly from connected Android devices via ADB |
| 🗂️ **Case Management** | Create and manage forensic cases, assign investigators, and track status |
| 🔌 **Device Management** | Register devices under cases, track device info and acquisition status |
| 🧾 **Evidence Management** | Store, categorise, and retrieve extracted digital evidence |
| 📊 **Timeline Analysis** | Build a chronological timeline of events from extracted data |
| 📄 **Report Generation** | Generate PDF forensic reports for cases with evidence summaries |
| 🔒 **Audit Logging** | Full audit trail of every action performed in the system |
| 🌱 **Demo Seeder** | Pre-load the database with realistic demo data for testing |

---

## 🗂️ Project Structure

```
forensic/
├── backend/                  # Flask API server
│   ├── app.py                # Application entry point
│   ├── config.py             # Configuration (DB, ADB path, etc.)
│   ├── models.py             # SQLAlchemy database models
│   ├── routes.py             # API route definitions
│   ├── requirements.txt      # Python dependencies
│   ├── acquisition/
│   │   └── adb_extractor.py  # ADB-based data extraction logic
│   ├── analysis/
│   │   └── timeline.py       # Timeline event construction
│   ├── parsers/              # Data parsers for various formats
│   ├── reporting/            # PDF report generation
│   ├── seed_demo_data.py     # Seed script for demo data
│   └── test_adb.py           # Standalone ADB extraction test
├── frontend/                 # React + Vite frontend
│   ├── src/                  # React components and pages
│   ├── index.html
│   └── package.json
├── start_backend.bat         # Windows quick-start for backend
├── start_frontend.bat        # Windows quick-start for frontend
└── TEACH_ME.md               # Developer learning notes
```

---

## ⚙️ Prerequisites

- **Python 3.10+**
- **Node.js 18+** and **npm**
- **ADB (Android Debug Bridge)** — part of [Android Platform Tools](https://developer.android.com/tools/releases/platform-tools)
- An Android device with **USB Debugging enabled**

---

## 🚀 How to Run

### 1. Clone the Repository

```bash
git clone https://github.com/Kirankumars73/Forensic.git
cd Forensic
```

### 2. Backend Setup

```bash
cd backend

# Create and activate a virtual environment
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS/Linux

# Install dependencies
pip install -r requirements.txt

# Start the Flask server
python app.py
```

The backend runs at: **http://localhost:5000**

### 3. Frontend Setup

Open a **new terminal**:

```bash
cd frontend

# Install Node dependencies
npm install

# Start the Vite dev server
npm run dev
```

The frontend runs at: **http://localhost:5173**

### 4. (Optional) Seed Demo Data

To populate the database with sample cases, devices, and evidence:

```bash
cd backend
python seed_demo_data.py
```

### 5. (Optional) Quick Start on Windows

Double-click the provided batch files:
- `start_backend.bat` — starts the Flask server
- `start_frontend.bat` — starts the React dev server

---

## 📱 ADB Extraction Test

To verify ADB extraction is working with a connected Android device:

```bash
cd backend
python test_adb.py
```

This will:
1. Scan for connected ADB devices
2. Extract call logs
3. Extract SMS messages
4. Extract contacts
5. Print results to the console

> **Note:** Enable **Developer Options → USB Debugging** on your Android device and accept the USB debugging prompt before running.

---

## 🔌 API Endpoints

| Prefix | Blueprint | Description |
|---|---|---|
| `/api/cases` | `cases_bp` | Case CRUD operations |
| `/api/devices` | `devices_bp` | Device registration & management |
| `/api/evidence` | `evidence_bp` | Evidence upload & retrieval |
| `/api/reports` | `reports_bp` | Report generation |
| `/api/audit` | `audit_bp` | Audit log access |
| `/api/admin` | `admin_bp` | Admin utilities |
| `/api/health` | — | Health check |

---

## 🛠️ Tech Stack

**Backend**
- Python, Flask, Flask-SQLAlchemy, Flask-CORS
- SQLite (default), ReportLab (PDF), Pillow, fpdf2
- ADB via subprocess

**Frontend**
- React 18, Vite, JavaScript

---

## 📜 License

MIT License — see [LICENSE](LICENSE) for details.
