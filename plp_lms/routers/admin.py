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
from services.auth_service import get_current_user, require_role, hash_password, safe_username, validate_password_strength, username_root_conflict
from sqlalchemy import func
from models.training_plan import TrainingPlan, TrainingPlanItem, TrainingPlanAssignment
from models.department import Department
from datetime import date, timedelta
from services.bulk_import_service import bulk_enrol_from_csv
from services.notification_service import create_notification
from services.audit_service import log_action
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
def list_users(
    request: Request, page: int = 1, per_page: int = 50,
    department_id: int = None,
    db: Session = Depends(get_db), user: User = Depends(get_current_user),
):
    query = db.query(User)
    if q := request.query_params.get("q"):
        query = query.filter(User.full_name.ilike(f"%{q}%") | User.email.ilike(f"%{q}%"))
    if department_id:
        query = query.filter(User.department_id == department_id)
    users = query.order_by(User.created_at.desc()).offset((page - 1) * per_page).limit(per_page).all()
    total = query.count()
    total_pages = (total + per_page - 1) // per_page
    success = request.query_params.get("success")
    error = request.query_params.get("error")
    departments = db.query(Department).filter(Department.is_active == True).order_by(Department.name).all()
    return templates.TemplateResponse("admin/users.html", {
        "request": request, "user": user, "users": users,
        "success": success, "error": error,
        "page": page, "per_page": per_page, "total": total, "total_pages": total_pages,
        "departments": departments, "selected_dept_id": department_id, "q": q or "",
    })


@router.get("/users/create", response_class=HTMLResponse, name="admin.create_user")
def create_user_page(request: Request, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    departments = db.query(Department).filter(Department.is_active == True).order_by(Department.name).all()
    return templates.TemplateResponse("admin/user_form.html", {"request": request, "user": user, "edit_user": None, "departments": departments})


@router.post("/users/create", name="admin.create_user_submit")
def create_user(
    request: Request,
    full_name: str = Form(...),
    email: str = Form(...),
    role: str = Form("learner"),
    password: str = Form(...),
    department_id: int = Form(None),
    csrf_token: str = Form(default=""),
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_current_user),
):
    existing = db.query(User).filter(func.lower(User.email) == email.lower()).first()
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
    username = safe_username(db, email)
    if username_root_conflict(db, username):
        flash(request, f"Username '{username}' conflicts with an existing username (same root with trailing digits)", "error")
        return RedirectResponse(url="/admin/users/create", status_code=302)
    new_user = User(
        username=username,
        email=email,
        password_hash=hash_password(password),
        full_name=full_name,
        role=role,
        department_id=department_id or None,
        force_password_change=True,
        requires_gdpr_consent=True,
        gdpr_consent_date=None,
    )
    db.add(new_user)
    db.commit()

    log = AuditLog(user_id=admin_user.id, action="create_user", target_type="user", target_id=new_user.id, notes=f"Created user {email}")
    db.add(log)
    db.commit()

    _auto_enrol_training_plans(db, new_user)
    db.commit()

    try:
        body = f"""
        <h2>Welcome to PLP LMS</h2>
        <p>Hello {full_name},</p>
        <p>An administrator has created an account for you on the PLP Learning Management System.</p>
        <p><strong>Username:</strong> {username}<br>
        <strong>Email:</strong> {email}</p>
        <p>Please log in at <a href="{BASE_URL}/auth/login">{BASE_URL}/auth/login</a> using your username or email. You will be prompted to set a new password on first login.</p>
        <p>If you have any questions, please contact your system administrator.</p>
        """
        send_email(email, "Welcome to PLP LMS – Your Account Has Been Created", body)
    except Exception:
        import logging
        logging.getLogger("plp_lms").warning("Failed to send welcome email to %s", email)

    flash(request, "User created successfully", "success")
    return RedirectResponse(url="/admin/users", status_code=302)


@router.get("/users/{user_id}/edit", response_class=HTMLResponse, name="admin.edit_user")
def edit_user_page(request: Request, user_id: int, db: Session = Depends(get_db), admin_user: User = Depends(get_current_user)):
    edit_user = db.query(User).filter(User.id == user_id).first()
    if not edit_user:
        return RedirectResponse(url="/admin/users", status_code=302)
    departments = db.query(Department).filter(Department.is_active == True).order_by(Department.name).all()
    return templates.TemplateResponse("admin/user_form.html", {"request": request, "user": admin_user, "edit_user": edit_user, "departments": departments})


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
    department_id: int = Form(None),
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
    email_exists = db.query(User).filter(func.lower(User.email) == email.lower(), User.id != user_id).first()
    if email_exists:
        flash(request, "Email already in use by another user", "error")
        return RedirectResponse(url=f"/admin/users/{user_id}/edit", status_code=302)
    username_exists = db.query(User).filter(func.lower(User.username) == username.lower(), User.id != user_id).first()
    if username_exists:
        flash(request, "Username already in use", "error")
        return RedirectResponse(url=f"/admin/users/{user_id}/edit", status_code=302)
    if username_root_conflict(db, username, exclude_user_id=user_id):
        flash(request, f"Username '{username}' conflicts with an existing username (same root with trailing digits)", "error")
        return RedirectResponse(url=f"/admin/users/{user_id}/edit", status_code=302)
    old_role = edit_user.role
    edit_user.full_name = full_name
    edit_user.username = username
    edit_user.email = email
    edit_user.role = role
    edit_user.is_active = is_active
    edit_user.force_password_change = force_password_change
    edit_user.department_id = department_id or None
    if new_password:
        try:
            validate_password_strength(new_password)
        except ValueError as e:
            flash(request, str(e), "error")
            return RedirectResponse(url=f"/admin/users/{user_id}/edit", status_code=302)
        edit_user.password_hash = hash_password(new_password)
        edit_user.token_version += 1
    db.commit()
    _auto_enrol_training_plans(db, edit_user)
    db.commit()
    if old_role != role:
        edit_user.token_version = (edit_user.token_version or 0) + 1
        log_action(db, admin_user.id, "change_role", "user", user_id, f"Role changed from {old_role} to {role}")
    notes = []
    if new_password:
        notes.append("password reset")
    log_action(db, admin_user.id, "edit_user", "user", user_id, f"Edited user {email}: {', '.join(notes)}" if notes else f"Edited user {email}")
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
def audit_log_page(
    request: Request,
    page: int = 1,
    per_page: int = 20,
    action: str = None,
    date_from: str = None,
    date_to: str = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    query = db.query(AuditLog)
    if action:
        query = query.filter(AuditLog.action == action)
    if date_from:
        query = query.filter(AuditLog.timestamp >= datetime.fromisoformat(date_from))
    if date_to:
        query = query.filter(AuditLog.timestamp <= datetime.fromisoformat(date_to))
    total = query.count()
    total_pages = max(1, (total + per_page - 1) // per_page)
    logs = query.order_by(AuditLog.timestamp.desc()).offset((page - 1) * per_page).limit(per_page).all()
    action_types = [r[0] for r in db.query(AuditLog.action).distinct().order_by(AuditLog.action).all()]
    return templates.TemplateResponse("admin/audit_log.html", {
        "request": request, "user": user, "logs": logs,
        "page": page, "per_page": per_page, "total": total, "total_pages": total_pages,
        "action": action, "date_from": date_from, "date_to": date_to,
        "action_types": action_types,
    })


@router.get("/audit-log/export", name="admin.audit_log_export")
def export_audit_log(
    request: Request,
    action: str = None,
    date_from: str = None,
    date_to: str = None,
    db: Session = Depends(get_db),
    user: User = Depends(require_role("superadmin")),
):
    import csv, io
    query = db.query(AuditLog)
    if action:
        query = query.filter(AuditLog.action == action)
    if date_from:
        query = query.filter(AuditLog.timestamp >= datetime.fromisoformat(date_from))
    if date_to:
        query = query.filter(AuditLog.timestamp <= datetime.fromisoformat(date_to))
    logs = query.order_by(AuditLog.timestamp.desc()).all()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Timestamp", "User ID", "User Name", "Action", "Target Type", "Target ID", "Notes"])
    for log in logs:
        writer.writerow([
            log.timestamp.strftime("%Y-%m-%d %H:%M:%S") if log.timestamp else "",
            log.user_id,
            log.user.full_name if log.user else "System",
            log.action,
            log.target_type or "",
            log.target_id or "",
            log.notes or "",
        ])
    from starlette.responses import StreamingResponse
    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=audit_log.csv"},
    )


def _auto_enrol_training_plans(db: Session, user: User):
    active_plans = db.query(TrainingPlan).filter(TrainingPlan.is_active == True).all()
    for plan in active_plans:
        existing = db.query(TrainingPlanAssignment).filter(
            TrainingPlanAssignment.plan_id == plan.id,
            TrainingPlanAssignment.user_id == user.id,
        ).first()
        if existing:
            continue
        items = db.query(TrainingPlanItem).filter(TrainingPlanItem.plan_id == plan.id).all()
        max_due = max((i.due_within_days for i in items), default=30)
        assignment = TrainingPlanAssignment(
            plan_id=plan.id,
            user_id=user.id,
            role_string=user.role,
            due_date=date.today() + timedelta(days=max_due),
        )
        db.add(assignment)


@router.get("/compliance", response_class=HTMLResponse, name="admin.compliance")
def compliance_dashboard(
    request: Request, department_id: int = None,
    db: Session = Depends(get_db), user: User = Depends(require_role("superadmin")),
):
    query = db.query(User).filter(User.is_active == True)
    if department_id:
        query = query.filter(User.department_id == department_id)
    users = query.order_by(User.full_name).all()
    plans = db.query(TrainingPlan).filter(TrainingPlan.is_active == True).all()
    departments = db.query(Department).filter(Department.is_active == True).order_by(Department.name).all()
    rows = []
    for u in users:
        for plan in plans:
            assignment = db.query(TrainingPlanAssignment).filter(
                TrainingPlanAssignment.plan_id == plan.id,
                TrainingPlanAssignment.user_id == u.id,
            ).first()
            if not assignment:
                continue
            items = db.query(TrainingPlanItem).filter(TrainingPlanItem.plan_id == plan.id).count()
            completed = 0
            for item in db.query(TrainingPlanItem).filter(TrainingPlanItem.plan_id == plan.id).all():
                from models.submission import Submission
                sub = db.query(Submission).filter(
                    Submission.user_id == u.id,
                    Submission.passed == True,
                    Submission.status == "released",
                ).first()
                if sub:
                    completed += 1
            pct = round(completed / items * 100, 1) if items else 0
            if pct >= 80:
                rag = "green"
            elif pct >= 50:
                rag = "amber"
            else:
                rag = "red"
            rows.append({"user": u, "plan": plan, "pct": pct, "rag": rag, "completed": completed, "total": items})
    return templates.TemplateResponse("admin/compliance.html", {"request": request, "user": user, "rows": rows, "departments": departments, "selected_dept_id": department_id})


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


@router.post("/users/{user_id}/unlock", name="admin.unlock_user")
def unlock_user(
    request: Request,
    user_id: int,
    csrf_token: str = Form(default=""),
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_current_user),
):
    target = db.query(User).filter(User.id == user_id).first()
    if not target:
        flash(request, "User not found", "error")
        return RedirectResponse(url="/admin/users", status_code=302)
    target.failed_login_attempts = 0
    target.locked_until = None
    target.is_active = True
    db.commit()
    log_action(db, admin_user.id, "unlock_user", "user", user_id, f"Unlocked user {target.email}")
    flash(request, "User account unlocked", "success")
    return RedirectResponse(url="/admin/users", status_code=302)


@router.post("/users/{user_id}/reset-password", name="admin.reset_password")
def reset_user_password(
    request: Request,
    user_id: int,
    new_password: str = Form(...),
    csrf_token: str = Form(default=""),
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_current_user),
):
    target = db.query(User).filter(User.id == user_id).first()
    if not target:
        flash(request, "User not found", "error")
        return RedirectResponse(url="/admin/users", status_code=302)
    try:
        validate_password_strength(new_password)
    except ValueError as e:
        flash(request, str(e), "error")
        return RedirectResponse(url=f"/admin/users/{user_id}/edit", status_code=302)
    target.password_hash = hash_password(new_password)
    target.token_version = (target.token_version or 0) + 1
    db.commit()
    log_action(db, admin_user.id, "reset_password", "user", user_id, f"Password reset for {target.email}")
    flash(request, "Password reset successfully", "success")
    return RedirectResponse(url="/admin/users", status_code=302)


@router.get("/departments", response_class=HTMLResponse, name="admin.departments")
def departments_page(request: Request, db: Session = Depends(get_db), user: User = Depends(require_role("superadmin"))):
    depts = db.query(Department).filter(Department.is_active == True).order_by(Department.name).all()
    managers = db.query(User).filter(User.is_active == True).order_by(User.full_name).all()
    return templates.TemplateResponse("admin/departments.html", {"request": request, "user": user, "departments": depts, "managers": managers})


@router.post("/departments/create", name="admin.departments_create")
def create_department(
    request: Request,
    name: str = Form(...),
    parent_id: int = Form(None),
    manager_id: int = Form(None),
    csrf_token: str = Form(default=""),
    db: Session = Depends(get_db),
    user: User = Depends(require_role("superadmin")),
):
    dept = Department(name=name, parent_id=parent_id or None, manager_id=manager_id or None)
    db.add(dept)
    db.commit()
    flash(request, f"Department '{name}' created", "success")
    return RedirectResponse(url="/admin/departments", status_code=302)


@router.post("/departments/{dept_id}/edit", name="admin.departments_edit")
def edit_department(
    request: Request,
    dept_id: int,
    name: str = Form(...),
    parent_id: int = Form(None),
    manager_id: int = Form(None),
    csrf_token: str = Form(default=""),
    db: Session = Depends(get_db),
    user: User = Depends(require_role("superadmin")),
):
    dept = db.query(Department).filter(Department.id == dept_id).first()
    if not dept:
        raise HTTPException(status_code=404)
    dept.name = name
    dept.parent_id = parent_id or None
    dept.manager_id = manager_id or None
    db.commit()
    flash(request, "Department updated", "success")
    return RedirectResponse(url="/admin/departments", status_code=302)


@router.post("/departments/{dept_id}/delete", name="admin.departments_delete")
def delete_department(
    request: Request,
    dept_id: int,
    csrf_token: str = Form(default=""),
    db: Session = Depends(get_db),
    user: User = Depends(require_role("superadmin")),
):
    dept = db.query(Department).filter(Department.id == dept_id).first()
    if not dept:
        raise HTTPException(status_code=404)
    dept.is_active = False
    db.commit()
    flash(request, "Department deactivated", "success")
    return RedirectResponse(url="/admin/departments", status_code=302)


# ---- Enrolment Requests ----

from models.enrolment_request import EnrolmentRequest as EnrolmentReq

enrolment_router = APIRouter(prefix="/admin/enrolment-requests", tags=["enrolment_requests"])


@enrolment_router.get("", response_class=HTMLResponse, name="admin.enrolment_requests")
def list_requests(request: Request, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    if user.role not in ("superadmin", "trainer"):
        raise HTTPException(status_code=403)
    requests = db.query(EnrolmentReq).order_by(EnrolmentReq.created_at.desc()).all()
    return templates.TemplateResponse("admin/enrolment_requests.html", {"request": request, "user": user, "requests": requests})


@enrolment_router.get("/{req_id}/approve", response_class=HTMLResponse, name="admin.enrolment_approve_page")
def approve_page(req_id: int, request: Request, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    if user.role not in ("superadmin", "trainer"):
        raise HTTPException(status_code=403)
    req = db.query(EnrolmentReq).filter(EnrolmentReq.id == req_id).first()
    if not req:
        raise HTTPException(status_code=404)
    cohorts = db.query(Cohort).filter(Cohort.course_id == req.course_id, Cohort.is_active == True).order_by(Cohort.name).all()
    return templates.TemplateResponse("admin/enrolment_approve.html", {"request": request, "user": user, "req": req, "cohorts": cohorts})


@enrolment_router.post("/{req_id}/approve", name="admin.enrolment_approve")
def approve_request(
    req_id: int, request: Request, cohort_id: int = Form(None), csrf_token: str = Form(default=""),
    db: Session = Depends(get_db), user: User = Depends(get_current_user),
):
    if user.role not in ("superadmin", "trainer"):
        raise HTTPException(status_code=403)
    req = db.query(EnrolmentReq).filter(EnrolmentReq.id == req_id).first()
    if not req or req.status != "pending":
        flash(request, "Request not found or already processed", "error")
        return RedirectResponse(url="/admin/enrolment-requests", status_code=302)
    if cohort_id:
        cohort = db.query(Cohort).filter(Cohort.id == cohort_id).first()
        if not cohort:
            flash(request, "Selected cohort not found", "error")
            return RedirectResponse(url=f"/admin/enrolment-requests/{req.id}/approve", status_code=302)
    else:
        cohort = db.query(Cohort).filter(Cohort.course_id == req.course_id, Cohort.is_active == True).order_by(Cohort.name).first()
        if not cohort:
            flash(request, "No active cohort available for this course", "error")
            return RedirectResponse(url=f"/admin/enrolment-requests/{req.id}/approve", status_code=302)
    enrol = Enrolment(user_id=req.user_id, cohort_id=cohort.id, enrolment_source="request")
    db.add(enrol)
    req.status = "approved"
    req.reviewed_by = user.id
    req.reviewed_at = datetime.utcnow()
    req.cohort_id = cohort.id
    db.commit()
    create_notification(db, req.user_id, "enrolment_request", f"Enrolment approved for {req.course.title}", f"Your enrolment request for {req.course.title} has been approved. You are enrolled in {cohort.name}.", action_url="/dashboard")
    flash(request, "Request approved and learner enrolled", "success")
    return RedirectResponse(url="/admin/enrolment-requests", status_code=302)


@enrolment_router.post("/{req_id}/decline", name="admin.enrolment_decline")
def decline_request(
    req_id: int, request: Request, csrf_token: str = Form(default=""),
    db: Session = Depends(get_db), user: User = Depends(get_current_user),
):
    if user.role not in ("superadmin", "trainer"):
        raise HTTPException(status_code=403)
    req = db.query(EnrolmentReq).filter(EnrolmentReq.id == req_id).first()
    if not req or req.status != "pending":
        flash(request, "Request not found or already processed", "error")
        return RedirectResponse(url="/admin/enrolment-requests", status_code=302)
    req.status = "declined"
    req.reviewed_by = user.id
    req.reviewed_at = datetime.utcnow()
    db.commit()
    create_notification(db, req.user_id, "enrolment_request", f"Enrolment declined for {req.course.title}", f"Your enrolment request for {req.course.title} has been declined.", action_url="/courses/catalogue")
    flash(request, "Request declined", "success")
    return RedirectResponse(url="/admin/enrolment-requests", status_code=302)
