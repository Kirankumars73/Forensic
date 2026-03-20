import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
EVIDENCE_DIR = os.path.join(BASE_DIR, "evidence_store")
THUMBNAILS_DIR = os.path.join(EVIDENCE_DIR, "thumbnails")
REPORTS_DIR = os.path.join(BASE_DIR, "reports")

os.makedirs(EVIDENCE_DIR, exist_ok=True)
os.makedirs(THUMBNAILS_DIR, exist_ok=True)
os.makedirs(REPORTS_DIR, exist_ok=True)


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "forensic-secret-key-2024")
    SQLALCHEMY_DATABASE_URI = f"sqlite:///{os.path.join(BASE_DIR, 'forensic.db')}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    EVIDENCE_DIR = EVIDENCE_DIR
    THUMBNAILS_DIR = THUMBNAILS_DIR
    REPORTS_DIR = REPORTS_DIR
    ADB_PATH = os.environ.get("ADB_PATH", r"C:\Users\kiran\Downloads\platform-tools-latest-windows\platform-tools\adb.exe")
    MAX_CONTENT_LENGTH = 500 * 1024 * 1024  # 500 MB upload limit
