import secrets, re, warnings
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
warnings.filterwarnings("ignore", message=".*bcrypt.*")
from fastapi import Request, HTTPException, Depends
from sqlalchemy.orm import Session
from database import get_db
from models.user import User
from config import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES, ACCOUNT_LOCKOUT_ATTEMPTS, ACCOUNT_LOCKOUT_MINUTES

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        return {}


def get_current_user(request: Request, db: Session = Depends(get_db)):
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(status_code=302, headers={"Location": "/auth/login"})
    payload = decode_token(token)
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=302, headers={"Location": "/auth/login"})
    user = db.query(User).filter(User.id == int(user_id)).first()
    if not user or not user.is_active:
        raise HTTPException(status_code=302, headers={"Location": "/auth/login"})
    if payload.get("ver") != user.token_version:
        raise HTTPException(status_code=302, headers={"Location": "/auth/login"})
    exp = payload.get("exp")
    if exp:
        remaining = exp - datetime.utcnow().timestamp()
        if remaining < 900:
            request.state.refresh_token = create_access_token({"sub": user.id, "role": user.role, "ver": user.token_version})
    if user.force_password_change:
        from fastapi.responses import RedirectResponse
        if "/auth/change-password" not in str(request.url):
            raise HTTPException(status_code=302, headers={"Location": "/auth/change-password"})
    if user.requires_gdpr_consent and "/auth/gdpr-consent" not in str(request.url):
        raise HTTPException(status_code=302, headers={"Location": "/auth/gdpr-consent"})
    return user


def require_role(*roles):
    def role_checker(user: User = Depends(get_current_user)):
        if user.role not in roles:
            raise HTTPException(status_code=403, detail="Access denied")
        return user
    return role_checker


def check_account_locked(user: User) -> bool:
    if user.locked_until and user.locked_until > datetime.utcnow():
        return True
    return False


def increment_failed_attempts(db: Session, user: User):
    user.failed_login_attempts = (user.failed_login_attempts or 0) + 1
    if user.failed_login_attempts >= ACCOUNT_LOCKOUT_ATTEMPTS:
        user.locked_until = datetime.utcnow() + timedelta(minutes=ACCOUNT_LOCKOUT_MINUTES)
    db.commit()


def validate_password_strength(password: str):
    if len(password) < 10:
        raise ValueError("Password must be at least 10 characters")
    if not re.search(r"[A-Z]", password):
        raise ValueError("Password must contain an uppercase letter")
    if not re.search(r"[a-z]", password):
        raise ValueError("Password must contain a lowercase letter")
    if not re.search(r"\d", password):
        raise ValueError("Password must contain a digit")
    if not re.search(r"[!@#$%^&*()_+\-=]", password):
        raise ValueError("Password must contain a special character")
    return True


def reset_failed_attempts(db: Session, user: User):
    user.failed_login_attempts = 0
    user.locked_until = None
    db.commit()


def safe_username(db, email):
    base = email.split("@")[0].lower()[:50]
    username = base
    counter = 1
    while db.query(User).filter(User.username == username).first():
        username = f"{base}{counter}"
        counter += 1
    return username


def create_setup_token(db, user_id):
    token = secrets.token_urlsafe(32)
    user = db.query(User).filter(User.id == user_id).first()
    user.cohort_token = token
    user.setup_token_expiry = datetime.utcnow() + timedelta(hours=48)
    db.commit()
    return token
