from fastapi import APIRouter, Request, Depends, Form, UploadFile, File, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from database import get_db
from models.user import User
from models.course import Course
from models.cohort import Cohort, Enrolment
from services.auth_service import get_current_user, require_role, hash_password, create_setup_token, safe_username
from services.email_service import send_welcome_email
from services.bulk_import_service import bulk_enrol_from_csv
from services.notification_service import create_notification
from services.audit_service import log_action
from services.flash import flash
from datetime import datetime, date, timedelta
from config import DATA_RETENTION_YEARS
import secrets
import string

VALID_ENROLMENT_STATUSES = frozenset({"enrolled", "in_progress", "completed", "dropped"})

router = APIRouter(prefix="/cohorts", tags=["cohorts"])
from template_utils import templates


def generate_token(length=8):
    chars = string.ascii_uppercase + string.digits
    return "".join(secrets.choice(chars) for _ in range(length))


@router.get("", response_class=HTMLResponse, name="cohorts.list_cohorts")
def list_cohorts(request: Request, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if user.role == "superadmin":
        cohorts = db.query(Cohort).order_by(Cohort.created_at.desc()).all()
    elif user.role == "trainer":
        cohorts = db.query(Cohort).filter(Cohort.trainer_id == user.id).order_by(Cohort.created_at.desc()).all()
    else:
        cohorts = db.query(Cohort).filter(Cohort.is_active == True).all()
    return templates.TemplateResponse("shared/cohorts.html", {"request": request, "user": user, "cohorts": cohorts})


@router.get("/create", response_class=HTMLResponse, name="cohorts.create_cohort")
def create_cohort_page(request: Request, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    courses = db.query(Course).filter(Course.is_published == True).all()
    trainers = db.query(User).filter(User.role == "trainer", User.is_active == True).all()
    return templates.TemplateResponse("shared/cohort_form.html", {"request": request, "user": user, "cohort": None, "courses": courses, "trainers": trainers})


@router.post("/create", name="cohorts.create_cohort_submit")
def create_cohort(
    request: Request,
    name: str = Form(...),
    course_id: int = Form(...),
    trainer_id: int = Form(None),
    start_date: str = Form(None),
    end_date: str = Form(None),
    max_learners: int = Form(30),
    delivery_mode: str = Form("online"),
    venue: str = Form(None),
    csrf_token: str = Form(default=""),
    db: Session = Depends(get_db),
    user: User = Depends(require_role("superadmin", "trainer")),
):
    token = generate_token()
    cohort = Cohort(
        name=name,
        course_id=course_id,
        trainer_id=trainer_id,
        start_date=date.fromisoformat(start_date) if start_date else None,
        end_date=date.fromisoformat(end_date) if end_date else None,
        max_learners=max_learners,
        enrolment_token=token,
        delivery_mode=delivery_mode,
        venue=venue,
    )
    db.add(cohort)
    db.commit()
    log_action(db, user.id, "create_cohort", "cohort", cohort.id, f"Created cohort {name} for course {course_id}")
    flash(request, "Cohort created", "success")
    return RedirectResponse(url=f"/cohorts/{cohort.id}", status_code=302)


@router.get("/{cohort_id}", response_class=HTMLResponse, name="cohorts.view")
def view_cohort(request: Request, cohort_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    cohort = db.query(Cohort).filter(Cohort.id == cohort_id).first()
    if not cohort:
        raise HTTPException(status_code=404)
    enrolments = db.query(Enrolment).filter(Enrolment.cohort_id == cohort_id).all()
    total = len(enrolments)
    completed = sum(1 for e in enrolments if e.status == "completed")
    in_progress = sum(1 for e in enrolments if e.status == "in_progress")
    scores = [e.final_score for e in enrolments if e.final_score is not None]
    avg_score = round(sum(scores) / len(scores), 1) if scores else 0
    error_map = {"user_not_found": "User not found with that email", "already_enrolled": "Learner is already enrolled in this cohort"}
    error = error_map.get(request.query_params.get("error"), request.query_params.get("error"))
    success = request.query_params.get("success")
    return templates.TemplateResponse("shared/cohort_view.html", {
        "request": request, "user": user, "cohort": cohort,
        "enrolments": enrolments, "total": total, "completed": completed,
        "in_progress": in_progress, "avg_score": avg_score,
        "error": error, "success": success,
    })


@router.get("/{cohort_id}/edit", response_class=HTMLResponse, name="cohorts.edit_cohort")
def edit_cohort_page(request: Request, cohort_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    cohort = db.query(Cohort).filter(Cohort.id == cohort_id).first()
    courses = db.query(Course).filter(Course.is_published == True).all()
    trainers = db.query(User).filter(User.role == "trainer", User.is_active == True).all()
    return templates.TemplateResponse("shared/cohort_form.html", {"request": request, "user": user, "cohort": cohort, "courses": courses, "trainers": trainers})


@router.post("/{cohort_id}/edit", name="cohorts.edit_cohort_submit")
def edit_cohort(
    request: Request,
    cohort_id: int,
    name: str = Form(...),
    course_id: int = Form(...),
    trainer_id: int = Form(None),
    start_date: str = Form(None),
    end_date: str = Form(None),
    max_learners: int = Form(30),
    is_active: bool = Form(False),
    delivery_mode: str = Form("online"),
    venue: str = Form(None),
    csrf_token: str = Form(default=""),
    db: Session = Depends(get_db),
    user: User = Depends(require_role("superadmin", "trainer")),
):
    cohort = db.query(Cohort).filter(Cohort.id == cohort_id).first()
    if not cohort:
        raise HTTPException(status_code=404)
    cohort.name = name
    cohort.course_id = course_id
    cohort.trainer_id = trainer_id
    cohort.start_date = date.fromisoformat(start_date) if start_date else None
    cohort.end_date = date.fromisoformat(end_date) if end_date else None
    cohort.max_learners = max_learners
    cohort.is_active = is_active
    cohort.delivery_mode = delivery_mode
    cohort.venue = venue
    db.commit()
    flash(request, "Cohort updated", "success")
    return RedirectResponse(url=f"/cohorts/{cohort_id}", status_code=302)


@router.post("/{cohort_id}/delete", name="cohorts.delete_cohort")
def delete_cohort(request: Request, cohort_id: int, db: Session = Depends(get_db), user: User = Depends(require_role("superadmin"))):
    cohort = db.query(Cohort).filter(Cohort.id == cohort_id).first()
    if cohort:
        db.delete(cohort)
        db.commit()
        flash(request, "Cohort deleted", "success")
    return RedirectResponse(url="/cohorts", status_code=302)


@router.post("/{cohort_id}/enrol", name="cohorts.enrol_learner")
def enrol_learner(
    request: Request,
    cohort_id: int,
    email: str = Form(...),
    create_if_not_found: bool = Form(False),
    csrf_token: str = Form(default=""),
    db: Session = Depends(get_db),
    user: User = Depends(require_role("superadmin", "trainer")),
):
    cohort = db.query(Cohort).filter(Cohort.id == cohort_id).first()
    if not cohort:
        raise HTTPException(status_code=404)

    learner = db.query(User).filter(User.email == email).first()
    if not learner:
        if create_if_not_found and user.role == "superadmin":
            import logging
            logging.getLogger("plp_lms").warning("Creating user on the fly for enrolment: %s by %s", email, user.username)
            from config import BASE_URL
            learner = User(
                username=safe_username(db, email),
                email=email,
                password_hash=hash_password(secrets.token_urlsafe(16)),
                full_name=email.split("@")[0],
                role="learner",
            )
            db.add(learner)
            db.flush()
            token = create_setup_token(db, learner.id)
            send_welcome_email(email, token, BASE_URL, learner.id, db)
        else:
            flash(request, "No account found for this email address. Please check the email or ask the learner to register first.", "error")
            return RedirectResponse(url=f"/cohorts/{cohort_id}?error=no_account", status_code=302)

    existing = db.query(Enrolment).filter(
        Enrolment.user_id == learner.id, Enrolment.cohort_id == cohort_id
    ).first()
    if existing:
        flash(request, "Learner is already enrolled in this cohort", "error")
        return RedirectResponse(url=f"/cohorts/{cohort_id}?error=already_enrolled", status_code=302)

    en = Enrolment(user_id=learner.id, cohort_id=cohort_id, enrolment_source="admin")
    db.add(en)
    create_notification(db, learner.id, "enrolment", f"Enrolled in cohort {cohort.name}")
    log_action(db, user.id, "enrol_learner", "enrolment", en.id, f"Enrolled learner {learner.email} in cohort {cohort.name} ({cohort_id})")
    db.commit()
    flash(request, "Learner enrolled", "success")
    return RedirectResponse(url=f"/cohorts/{cohort_id}?success=enrolled", status_code=302)


@router.post("/{cohort_id}/bulk-import", name="cohorts.bulk_enrol")
async def bulk_import(
    request: Request,
    cohort_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user: User = Depends(require_role("superadmin", "trainer")),
):
    from config import BASE_URL
    results = bulk_enrol_from_csv(db, cohort_id, file, BASE_URL)
    flash(request, "Learners imported", "success")
    return RedirectResponse(url=f"/cohorts/{cohort_id}", status_code=302)


@router.post("/{cohort_id}/enrolments/{enrolment_id}/status", name="cohorts.update_enrolment_status")
def update_enrolment_status(
    request: Request,
    cohort_id: int,
    enrolment_id: int,
    status: str = Form("enrolled"),
    csrf_token: str = Form(default=""),
    db: Session = Depends(get_db),
    user: User = Depends(require_role("superadmin", "trainer")),
):
    if status not in VALID_ENROLMENT_STATUSES:
        flash(request, f"Invalid enrolment status: {status}", "error")
        return RedirectResponse(url=f"/cohorts/{cohort_id}", status_code=302)

    en = db.query(Enrolment).filter(Enrolment.id == enrolment_id).first()
    if en:
        en.status = status
        if status == "completed":
            en.completion_date = datetime.utcnow()
            en.retention_review_date = (datetime.utcnow() + timedelta(days=365*DATA_RETENTION_YEARS)).date()
        db.commit()
        flash(request, "Enrolment status updated", "success")
    return RedirectResponse(url=f"/cohorts/{cohort_id}", status_code=302)
