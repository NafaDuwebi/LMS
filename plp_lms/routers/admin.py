from fastapi import APIRouter, Request, Depends, Form, UploadFile, File, HTTPException
from sqlalchemy import func
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from database import get_db
from models.user import User
from models.course import Course, LearningOutcome
from models.cohort import Cohort, Enrolment
from models.audit import AuditLog
from services.auth_service import get_current_user, require_role, hash_password, safe_username, validate_password_strength
from services.bulk_import_service import bulk_enrol_from_csv
from services.notification_service import create_notification
from services.email_service import send_email
from services.flash import flash
from config import BASE_URL
from datetime import datetime
from typing import List
import json

VALID_ROLES = {"superadmin", "trainer", "learner", "observer", "external_assessor"}

router = APIRouter(prefix="/admin", tags=["admin"], dependencies=[Depends(require_role("superadmin"))])
from template_utils import templates


@router.get("/users", response_class=HTMLResponse, name="admin.users")
def list_users(request: Request, page: int = 1, per_page: int = 50, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    users = db.query(User).order_by(User.created_at.desc()).offset((page - 1) * per_page).limit(per_page).all()
    total = db.query(func.count(User.id)).scalar()
    total_pages = (total + per_page - 1) // per_page
    success = request.query_params.get("success")
    error = request.query_params.get("error")
    return templates.TemplateResponse("admin/users.html", {"request": request, "user": user, "users": users, "success": success, "error": error, "page": page, "per_page": per_page, "total": total, "total_pages": total_pages})


@router.get("/users/create", response_class=HTMLResponse, name="admin.create_user")
def create_user_page(request: Request, user: User = Depends(get_current_user)):
    return templates.TemplateResponse("admin/user_form.html", {"request": request, "user": user, "edit_user": None})


@router.post("/users/create", name="admin.create_user_submit")
def create_user(
    request: Request,
    full_name: str = Form(...),
    email: str = Form(...),
    role: str = Form("learner"),
    password: str = Form(...),
    csrf_token: str = Form(default=""),
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_current_user),
):
    existing = db.query(User).filter(User.email == email).first()
    if existing:
        flash(request, "Email already exists", "error")
        return RedirectResponse(url="/admin/users/create", status_code=302)

    if role not in VALID_ROLES:
        flash(request, f"Invalid role: {role}", "error")
        return RedirectResponse(url="/admin/users/create", status_code=302)

    from services.auth_service import hash_password, validate_password_strength
    try:
        validate_password_strength(password)
    except ValueError as e:
        flash(request, str(e), "error")
        return RedirectResponse(url="/admin/users/create", status_code=302)
    new_user = User(
        username=safe_username(db, email),
        email=email,
        password_hash=hash_password(password),
        full_name=full_name,
        role=role,
        force_password_change=True,
        requires_gdpr_consent=True,
        gdpr_consent_date=None,
    )
    db.add(new_user)
    db.commit()

    log = AuditLog(user_id=admin_user.id, action="create_user", target_type="user", target_id=new_user.id, notes=f"Created user {email}")
    db.add(log)
    db.commit()

    flash(request, "User created successfully", "success")
    return RedirectResponse(url="/admin/users", status_code=302)


@router.get("/users/{user_id}/edit", response_class=HTMLResponse, name="admin.edit_user")
def edit_user_page(request: Request, user_id: int, db: Session = Depends(get_db), admin_user: User = Depends(get_current_user)):
    edit_user = db.query(User).filter(User.id == user_id).first()
    if not edit_user:
        return RedirectResponse(url="/admin/users", status_code=302)
    return templates.TemplateResponse("admin/user_form.html", {"request": request, "user": admin_user, "edit_user": edit_user})


@router.post("/users/{user_id}/edit", name="admin.edit_user_submit")
def edit_user(
    request: Request,
    user_id: int,
    full_name: str = Form(...),
    username: str = Form(...),
    email: str = Form(...),
    role: str = Form("learner"),
    is_active: bool = Form(False),
    new_password: str = Form(None),
    force_password_change: bool = Form(False),
    csrf_token: str = Form(default=""),
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_current_user),
):
    edit_user = db.query(User).filter(User.id == user_id).first()
    if not edit_user:
        flash(request, "User not found", "error")
        return RedirectResponse(url="/admin/users", status_code=302)
    if role not in VALID_ROLES:
        flash(request, f"Invalid role: {role}", "error")
        return RedirectResponse(url=f"/admin/users/{user_id}/edit", status_code=302)
    edit_user.full_name = full_name
    edit_user.username = username
    edit_user.email = email
    edit_user.role = role
    edit_user.is_active = is_active
    edit_user.force_password_change = force_password_change
    if new_password:
        try:
            validate_password_strength(new_password)
        except ValueError as e:
            flash(request, str(e), "error")
            return RedirectResponse(url=f"/admin/users/{user_id}/edit", status_code=302)
        edit_user.password_hash = hash_password(new_password)
        edit_user.token_version += 1
    db.commit()
    flash(request, "User updated successfully", "success")
    return RedirectResponse(url="/admin/users", status_code=302)


@router.get("/settings", response_class=HTMLResponse, name="admin.settings")
def settings_page(request: Request, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    from models.system_settings import SystemSetting
    def load(key, default):
        row = db.query(SystemSetting).filter(SystemSetting.key == key).first()
        return row.value if row else default
    settings = {
        "org_name": load("org_name", "PL Projects Ltd"),
        "min_attendance": load("min_attendance", "80"),
        "data_retention": load("data_retention", "3"),
        "max_upload": load("max_upload", "500"),
    }
    return templates.TemplateResponse("admin/settings.html", {"request": request, "user": user, "settings": settings})


@router.post("/settings", name="admin.settings_submit")
def update_settings(
    request: Request,
    org_name: str = Form(None),
    min_attendance: int = Form(80),
    data_retention: int = Form(3),
    max_upload: int = Form(500),
    csrf_token: str = Form(default=""),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    from models.system_settings import SystemSetting

    def upsert(key, value):
        row = db.query(SystemSetting).filter(SystemSetting.key == key).first()
        if row:
            row.value = str(value)
        else:
            db.add(SystemSetting(key=key, value=str(value)))

    upsert("org_name", org_name or "PL Projects Ltd")
    upsert("min_attendance", str(min_attendance))
    upsert("data_retention", str(data_retention))
    upsert("max_upload", str(max_upload))
    db.commit()

    flash(request, "Settings updated successfully", "success")
    settings = {"org_name": org_name or "PL Projects Ltd", "min_attendance": str(min_attendance), "data_retention": str(data_retention), "max_upload": str(max_upload)}
    return templates.TemplateResponse("admin/settings.html", {"request": request, "user": user, "settings": settings})


@router.get("/audit-log", response_class=HTMLResponse, name="admin.audit_log")
def audit_log_page(request: Request, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    logs = db.query(AuditLog).order_by(AuditLog.timestamp.desc()).limit(100).all()
    return templates.TemplateResponse("admin/audit_log.html", {"request": request, "user": user, "logs": logs})


@router.get("/gdpr-export/{target_user_id}", name="admin.gdpr_export")
def gdpr_export(target_user_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    import json, os, zipfile, io
    from datetime import datetime

    target = db.query(User).filter(User.id == target_user_id).first()
    if not target:
        raise HTTPException(status_code=404)

    EXCLUDED_FIELDS = {"password_hash", "reset_token", "cohort_token", "setup_token_expiry"}

    from models.cohort import Enrolment
    from models.submission import Submission
    from models.certificate import Certificate
    from models.training_record import TrainingRecord
    from models.rpl import RplClaim
    from models.skill import SkillClaim
    from models.notification import Notification

    enrolments = db.query(Enrolment).filter(Enrolment.user_id == target_user_id).all()
    submissions = db.query(Submission).filter(Submission.user_id == target_user_id).all()
    certificates = db.query(Certificate).filter(Certificate.user_id == target_user_id).all()
    training_records = db.query(TrainingRecord).filter(TrainingRecord.user_id == target_user_id).all()
    rpl_claims = db.query(RplClaim).filter(RplClaim.user_id == target_user_id).all()
    skill_claims = db.query(SkillClaim).filter(SkillClaim.user_id == target_user_id).all()

    data = {
        "user": {c.name: getattr(target, c.name) for c in target.__table__.columns if c.name not in EXCLUDED_FIELDS},
        "enrolments": [{c.name: str(getattr(en, c.name)) for c in en.__table__.columns} for en in enrolments],
        "submissions": [{c.name: str(getattr(s, c.name)) for c in s.__table__.columns} for s in submissions],
        "certificates": [{c.name: str(getattr(cert, c.name)) for c in cert.__table__.columns} for cert in certificates],
        "training_records": [{c.name: str(getattr(tr, c.name)) for c in tr.__table__.columns} for tr in training_records],
        "rpl_claims": [{c.name: str(getattr(r, c.name)) for c in r.__table__.columns} for r in rpl_claims],
        "skill_claims": [{c.name: str(getattr(sc, c.name)) for c in sc.__table__.columns} for sc in skill_claims],
        "notifications": [],
    }

    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w") as zf:
        zf.writestr("user_data.json", json.dumps(data, default=str, indent=2))

    from fastapi.responses import Response
    return Response(
        content=zip_buffer.getvalue(),
        media_type="application/zip",
        headers={"Content-Disposition": f"attachment; filename=gdpr_export_user_{target_user_id}.zip"},
    )


@router.post("/users/{user_id}/approve", name="admin.approve_user")
def approve_user(request: Request, user_id: int, db: Session = Depends(get_db), admin_user: User = Depends(get_current_user)):
    target = db.query(User).filter(User.id == user_id).first()
    if not target:
        flash(request, "User not found", "error")
        return RedirectResponse(url="/admin/users", status_code=302)
    target.is_active = True
    target.token_version = (target.token_version or 0) + 1
    log = AuditLog(user_id=admin_user.id, action="approve_user", target_type="user", target_id=user_id, notes=f"Approved user {target.email}")
    db.add(log)
    db.commit()
    send_email(target.email, "Your PLP LMS Account Has Been Approved", f"<p>Your account has been approved. Log in at <a href='{BASE_URL}/auth/login'>{BASE_URL}/auth/login</a></p>", target.id, db)
    flash(request, "User approved", "success")
    return RedirectResponse(url="/admin/users", status_code=302)


@router.post("/users/{user_id}/delete", name="admin.delete_user")
def delete_user(request: Request, user_id: int, db: Session = Depends(get_db), admin_user: User = Depends(get_current_user)):
    target = db.query(User).filter(User.id == user_id).first()
    if not target:
        flash(request, "User not found", "error")
        return RedirectResponse(url="/admin/users", status_code=302)
    if target.role == "superadmin":
        flash(request, "Cannot delete superadmin", "error")
        return RedirectResponse(url="/admin/users", status_code=302)
    target.token_version = (target.token_version or 0) + 1
    log = AuditLog(user_id=admin_user.id, action="delete_user", target_type="user", target_id=user_id, notes=f"Deleted user {target.email}")
    db.add(log)
    db.delete(target)
    db.commit()
    flash(request, "User deleted", "success")
    return RedirectResponse(url="/admin/users", status_code=302)
