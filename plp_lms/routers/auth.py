import os
from fastapi import APIRouter, Request, Depends, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import func
from sqlalchemy.orm import Session
from database import get_db
from models.user import User
from services.auth_service import (
    hash_password, verify_password, create_access_token,
    get_current_user, require_role, check_account_locked,
    increment_failed_attempts, reset_failed_attempts,
    create_setup_token, validate_password_strength
)
from services.notification_service import create_notification
from services.email_service import send_email
from services.rate_limiter import limiter
from services.flash import flash
from datetime import datetime, timedelta
import secrets

router = APIRouter(prefix="/auth", tags=["auth"])
from template_utils import templates


@router.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse("auth/login.html", {"request": request, "error": None})


@router.post("/login")
@limiter.limit("5/minute")
def login(request: Request, username: str = Form(...), password: str = Form(...), csrf_token: str = Form(default=""), db: Session = Depends(get_db)):
    user = db.query(User).filter(
        (func.lower(User.username) == username.lower()) | (func.lower(User.email) == username.lower())
    ).first()

    if not user:
        return templates.TemplateResponse("auth/login.html", {"request": request, "error": "Invalid credentials"}, status_code=401)

    if not user.is_active:
        return templates.TemplateResponse("auth/login.html", {"request": request, "error": "Your account is pending admin approval. Please try again later."}, status_code=401)

    if check_account_locked(user):
        return templates.TemplateResponse("auth/login.html", {"request": request, "error": "Account locked. Try again later."}, status_code=401)

    if not verify_password(password, user.password_hash):
        increment_failed_attempts(db, user)
        return templates.TemplateResponse("auth/login.html", {"request": request, "error": "Invalid credentials"}, status_code=401)

    reset_failed_attempts(db, user)
    user.last_login = datetime.utcnow()
    db.commit()

    token = create_access_token({"sub": str(user.id), "role": user.role, "ver": user.token_version or 0})
    flash(request, "Login successful", "success")
    redirect_url = "/auth/first-login" if user.force_password_change or user.requires_gdpr_consent else "/dashboard"
    response = RedirectResponse(url=redirect_url, status_code=302)
    response.set_cookie(key="access_token", value=token, httponly=True, secure=os.getenv("ENV", "development") == "production", samesite="strict", max_age=28800)
    return response


@router.get("/gdpr-consent", response_class=HTMLResponse)
def gdpr_consent_page(request: Request, user: User = Depends(get_current_user)):
    return templates.TemplateResponse("auth/gdpr_consent.html", {"request": request, "user": user})


@router.post("/gdpr-consent")
def gdpr_consent_accept(request: Request, csrf_token: str = Form(default=""), db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    user.gdpr_consent_date = datetime.utcnow()
    user.requires_gdpr_consent = False
    db.commit()
    flash(request, "GDPR consent accepted", "success")
    return RedirectResponse(url="/dashboard", status_code=302)


@router.get("/first-login", response_class=HTMLResponse)
def first_login_page(request: Request, user: User = Depends(get_current_user)):
    if not user.force_password_change and not user.requires_gdpr_consent:
        return RedirectResponse(url="/dashboard", status_code=302)
    return templates.TemplateResponse("auth/first_login.html", {"request": request, "user": user, "error": None})


@router.post("/first-login")
def first_login_submit(
    request: Request,
    new_password: str = Form(None),
    gdpr_consent: bool = Form(False),
    csrf_token: str = Form(default=""),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if user.force_password_change:
        if not new_password:
            return templates.TemplateResponse("auth/first_login.html", {"request": request, "user": user, "error": "You must set a new password."}, status_code=400)
        try:
            validate_password_strength(new_password)
        except ValueError as e:
            return templates.TemplateResponse("auth/first_login.html", {"request": request, "user": user, "error": str(e)}, status_code=400)
        user.password_hash = hash_password(new_password)
        user.force_password_change = False

    if user.requires_gdpr_consent:
        if not gdpr_consent:
            return templates.TemplateResponse("auth/first_login.html", {"request": request, "user": user, "error": "You must consent to data processing to continue."}, status_code=400)
        user.gdpr_consent_date = datetime.utcnow()
        user.requires_gdpr_consent = False

    import json
    prefs = json.loads(user.notification_preferences or "{}")
    user.notification_preferences = json.dumps(prefs)

    db.commit()

    flash(request, "Account setup complete", "success")
    return RedirectResponse(url="/dashboard", status_code=302)


@router.get("/logout")
def logout(request: Request):
    request.session.clear()
    response = RedirectResponse(url="/auth/login", status_code=302)
    response.delete_cookie("access_token")
    response.delete_cookie("session")
    response.delete_cookie("csrf_token")
    return response


@router.get("/register", response_class=HTMLResponse)
def register_page(request: Request, token: str = None):
    return templates.TemplateResponse("auth/register.html", {"request": request, "token": token, "error": None})


@router.post("/register")
@limiter.limit("3/minute")
def register(
    request: Request,
    full_name: str = Form(...),
    username: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    org: str = Form(None),
    token: str = Form(None),
    gdpr_consent: bool = Form(False),
    csrf_token: str = Form(default=""),
    db: Session = Depends(get_db),
):
    if not gdpr_consent:
        return templates.TemplateResponse("auth/register.html", {"request": request, "token": token, "error": "You must consent to data processing"}, status_code=400)

    existing = db.query(User).filter(func.lower(User.email) == email.lower()).first()
    if existing:
        return templates.TemplateResponse("auth/register.html", {"request": request, "token": token, "error": "Email already registered"}, status_code=400)

    existing_username = db.query(User).filter(func.lower(User.username) == username.lower()).first()
    if existing_username:
        return templates.TemplateResponse("auth/register.html", {"request": request, "token": token, "error": "Username already taken"}, status_code=400)

    try:
        validate_password_strength(password)
    except ValueError as e:
        return templates.TemplateResponse("auth/register.html", {"request": request, "token": token, "error": str(e)}, status_code=400)

    user = User(
        username=username,
        email=email,
        password_hash=hash_password(password),
        full_name=full_name,
        organisation=org,
        role="learner",
        is_active=False,
        gdpr_consent_date=datetime.utcnow(),
        force_password_change=False,
    )
    db.add(user)
    db.flush()

    if token:
        from models.cohort import Cohort, Enrolment
        cohort = db.query(Cohort).filter(Cohort.enrolment_token == token, Cohort.is_active == True).first()
        if cohort:
            en = Enrolment(user_id=user.id, cohort_id=cohort.id, enrolment_source="self")
            db.add(en)
            create_notification(db, user.id, "enrolment", f"Enrolled in {cohort.name}")

    db.commit()
    # Notify admins
    admins = db.query(User).filter(User.role == "superadmin").all()
    for admin in admins:
        create_notification(db, admin.id, "approval", f"New registration pending: {full_name} ({email})")
    db.commit()
    flash(request, "Registration successful. Pending approval.", "success")
    return RedirectResponse(url="/auth/login?registered=1&pending=1", status_code=302)


@router.get("/join/{token}", response_class=HTMLResponse)
def join_cohort(request: Request, token: str, db: Session = Depends(get_db)):
    from models.cohort import Cohort
    cohort = db.query(Cohort).filter(Cohort.enrolment_token == token, Cohort.is_active == True).first()
    if not cohort:
        return templates.TemplateResponse("auth/register.html", {"request": request, "token": None, "error": "Invalid or expired enrolment token"}, status_code=404)
    return templates.TemplateResponse("auth/register.html", {"request": request, "token": token, "error": None, "cohort_name": cohort.name})


@router.get("/change-password", response_class=HTMLResponse)
def change_password_page(request: Request):
    return templates.TemplateResponse("auth/change_password.html", {"request": request, "error": None})


@router.post("/change-password")
def change_password(
    request: Request,
    current_password: str = Form(...),
    new_password: str = Form(...),
    csrf_token: str = Form(default=""),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if not verify_password(current_password, user.password_hash):
        return templates.TemplateResponse("auth/change_password.html", {"request": request, "error": "Current password is incorrect"}, status_code=400)

    try:
        validate_password_strength(new_password)
    except ValueError as e:
        return templates.TemplateResponse("auth/change_password.html", {"request": request, "error": str(e)}, status_code=400)

    user.password_hash = hash_password(new_password)
    user.force_password_change = False
    db.commit()

    flash(request, "Password changed successfully", "success")
    return RedirectResponse(url="/dashboard", status_code=302)


@router.get("/set-password", response_class=HTMLResponse)
def set_password_page(request: Request, token: str = None):
    return templates.TemplateResponse("auth/set_password.html", {"request": request, "token": token, "error": None})


@router.post("/set-password")
def set_password(
    request: Request,
    token: str = Form(...),
    new_password: str = Form(...),
    confirm_password: str = Form(...),
    csrf_token: str = Form(default=""),
    db: Session = Depends(get_db),
):
    if new_password != confirm_password:
        return templates.TemplateResponse("auth/set_password.html", {"request": request, "token": token, "error": "Passwords do not match"}, status_code=400)

    user = db.query(User).filter(User.cohort_token == token).first()
    if not user:
        return templates.TemplateResponse("auth/set_password.html", {"request": request, "token": None, "error": "Invalid or expired setup link"}, status_code=400)

    if user.setup_token_expiry and user.setup_token_expiry < datetime.utcnow():
        user.cohort_token = None
        user.setup_token_expiry = None
        db.commit()
        return templates.TemplateResponse("auth/set_password.html", {"request": request, "token": None, "error": "This setup link has expired. Please contact your administrator for a new one."}, status_code=400)

    user.password_hash = hash_password(new_password)
    user.cohort_token = None
    user.force_password_change = False
    db.commit()

    flash(request, "Password set successfully", "success")
    return RedirectResponse(url="/auth/login?password_set=1", status_code=302)


@router.get("/forgot-password", response_class=HTMLResponse)
def forgot_password_page(request: Request):
    return templates.TemplateResponse("auth/forgot_password.html", {"request": request, "error": None, "sent": False})


@router.post("/forgot-password")
@limiter.limit("3/minute")
def forgot_password(
    request: Request,
    email: str = Form(...),
    csrf_token: str = Form(default=""),
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(func.lower(User.email) == email.lower()).first()
    if user:
        token = secrets.token_urlsafe(32)
        user.reset_token = token
        user.reset_token_expiry = datetime.utcnow() + timedelta(hours=1)
        db.commit()
        from config import BASE_URL
        body = f'<p>Reset your password: <a href="{BASE_URL}/auth/reset-password?token={token}">{BASE_URL}/auth/reset-password?token={token}</a></p><p>This link expires in 1 hour.</p>'
        send_email(email, "Password Reset Request", body, user.id, db)
    flash(request, "If that email is registered, a password reset link has been sent", "success")
    return templates.TemplateResponse("auth/forgot_password.html", {"request": request, "error": None, "sent": True})


@router.get("/reset-password", response_class=HTMLResponse)
def reset_password_page(request: Request, token: str = None):
    return templates.TemplateResponse("auth/reset_password.html", {"request": request, "token": token, "error": None})


@router.post("/reset-password")
@limiter.limit("5/minute")
def reset_password(
    request: Request,
    token: str = Form(...),
    new_password: str = Form(...),
    confirm_password: str = Form(...),
    csrf_token: str = Form(default=""),
    db: Session = Depends(get_db),
):
    if new_password != confirm_password:
        return templates.TemplateResponse("auth/reset_password.html", {"request": request, "token": token, "error": "Passwords do not match"}, status_code=400)

    user = db.query(User).filter(User.reset_token == token).first()
    if not user:
        return templates.TemplateResponse("auth/reset_password.html", {"request": request, "token": None, "error": "Invalid reset link"}, status_code=400)

    if user.reset_token_expiry and user.reset_token_expiry < datetime.utcnow():
        return templates.TemplateResponse("auth/reset_password.html", {"request": request, "token": None, "error": "Reset link has expired"}, status_code=400)

    try:
        validate_password_strength(new_password)
    except ValueError as e:
        return templates.TemplateResponse("auth/reset_password.html", {"request": request, "token": token, "error": str(e)}, status_code=400)

    user.password_hash = hash_password(new_password)
    user.reset_token = None
    user.reset_token_expiry = None
    db.commit()

    flash(request, "Password reset successfully", "success")
    return RedirectResponse(url="/auth/login?password_reset=1", status_code=302)
