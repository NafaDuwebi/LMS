import os
from dotenv import load_dotenv

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY or len(SECRET_KEY) < 64:
    raise RuntimeError("SECRET_KEY environment variable must be set and at least 64 characters long")
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./plp_lms.db")
UPLOAD_DIR = os.getenv("UPLOAD_DIR", os.path.join(os.path.dirname(os.path.abspath(__file__)), "uploads"))
CERTIFICATE_DIR = os.getenv("CERTIFICATE_DIR", os.path.join(os.path.dirname(os.path.abspath(__file__)), "certificates"))
MAX_UPLOAD_MB = int(os.getenv("MAX_UPLOAD_MB", "50"))
if MAX_UPLOAD_MB > 200:
    import logging
    logging.warning("MAX_UPLOAD_MB is set to %s — values over 200 may impact performance", MAX_UPLOAD_MB)
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.office365.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
FROM_EMAIL = os.getenv("FROM_EMAIL", "training@plprojects.co.uk")
ORG_NAME = os.getenv("ORG_NAME", "PL Projects Ltd")
ORG_LOGO_PATH = os.getenv("ORG_LOGO_PATH", "./static/logo.png")
BASE_URL = os.getenv("BASE_URL", "http://localhost:8000")
DEFAULT_CERT_VALIDITY_YEARS = int(os.getenv("DEFAULT_CERT_VALIDITY_YEARS", "0"))
DATA_RETENTION_YEARS = int(os.getenv("DATA_RETENTION_YEARS", "3"))
MIN_ATTENDANCE_THRESHOLD = int(os.getenv("MIN_ATTENDANCE_THRESHOLD", "80"))

ALGORITHM = "HS256"

SETTING_MAP = {
    "org_name": ("ORG_NAME", "PL Projects Ltd"),
    "min_attendance": ("MIN_ATTENDANCE_THRESHOLD", "80"),
    "data_retention": ("DATA_RETENTION_YEARS", "3"),
    "max_upload": ("MAX_UPLOAD_MB", "500"),
}

def get_setting(key, default=None):
    """Load a setting from the database with env var and default fallback."""
    env_var, env_default = SETTING_MAP.get(key, (None, default))
    val = os.getenv(env_var) if env_var else None
    if val is not None:
        return val
    try:
        from database import SessionLocal
        from models.system_settings import SystemSetting
        db = SessionLocal()
        try:
            row = db.query(SystemSetting).filter(SystemSetting.key == key).first()
            if row:
                return row.value
        finally:
            db.close()
    except Exception:
        pass
    return env_default if env_var else default
ACCESS_TOKEN_EXPIRE_MINUTES = 60
ACCOUNT_LOCKOUT_ATTEMPTS = 5
ACCOUNT_LOCKOUT_MINUTES = 30
