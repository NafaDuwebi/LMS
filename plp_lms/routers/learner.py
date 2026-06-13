from fastapi import APIRouter, Request, Depends, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session, joinedload
from database import get_db
from models.user import User
from models.course import Course, Module
from models.cohort import Cohort, Enrolment
from models.submission import Submission
from models.certificate import Certificate
from models.training_record import TrainingRecord
from services.auth_service import get_current_user, hash_password, verify_password, validate_password_strength
from services.progress_service import get_learner_progress
from services.notification_service import create_notification
from datetime import datetime
from services.flash import flash

router = APIRouter(prefix="/learner", tags=["learner"], dependencies=[Depends(get_current_user)])
from template_utils import templates


@router.get("/courses", response_class=HTMLResponse, name="learner.my_courses")
def my_courses(request: Request, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    enrolments = db.query(Enrolment).options(
        joinedload(Enrolment.cohort).joinedload(Cohort.course)
    ).filter(
        Enrolment.user_id == user.id,
        Enrolment.status.in_(["enrolled", "in_progress", "completed"]),
    ).all()
    course_progress = []
    for en in enrolments:
        if en.cohort and en.cohort.course:
            progress = get_learner_progress(db, user.id, en.cohort.course.id)
            course_progress.append({
                "enrolment": en,
                "course": en.cohort.course,
                "cohort": en.cohort,
                "progress": progress,
            })
    return templates.TemplateResponse("learner/my_courses.html", {"request": request, "user": user, "course_progress": course_progress})


@router.get("/course/{course_id}", response_class=HTMLResponse, name="learner.course_view")
def view_course(request: Request, course_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    course = db.query(Course).filter(Course.id == course_id, Course.is_published == True).first()
    if not course:
        raise HTTPException(status_code=404)

    # Check enrolment
    cohort = db.query(Cohort).join(Enrolment).filter(
        Enrolment.user_id == user.id,
        Enrolment.status.in_(["enrolled", "in_progress", "completed"]),
        Cohort.course_id == course_id,
    ).first()
    if not cohort:
        raise HTTPException(status_code=403, detail="Not enrolled")

    progress = get_learner_progress(db, user.id, course_id)
    return templates.TemplateResponse("learner/course_view.html", {"request": request, "user": user, "course": course, "progress": progress})


@router.get("/profile", response_class=HTMLResponse, name="learner.profile")
def profile_page(request: Request, user: User = Depends(get_current_user)):
    return templates.TemplateResponse("learner/profile.html", {"request": request, "user": user})


@router.post("/profile", name="learner.profile_update")
def update_profile(
    request: Request,
    full_name: str = Form(...),
    organisation: str = Form(None),
    job_title: str = Form(None),
    phone: str = Form(None),
    csrf_token: str = Form(default=""),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    db_user = db.query(User).filter(User.id == user.id).first()
    if db_user:
        db_user.full_name = full_name
        db_user.organisation = organisation
        db_user.job_title = job_title
        db_user.phone = phone
        db.commit()
    return templates.TemplateResponse("learner/profile.html", {"request": request, "user": db_user, "success": "Profile updated"})


@router.post("/change-password", name="learner.change_password")
def change_password(
    request: Request,
    current_password: str = Form(...),
    new_password: str = Form(...),
    csrf_token: str = Form(default=""),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    db_user = db.query(User).filter(User.id == user.id).first()
    if not verify_password(current_password, db_user.password_hash):
        return templates.TemplateResponse("learner/profile.html", {"request": request, "user": db_user, "error": "Current password incorrect"})
    try:
        validate_password_strength(new_password)
    except ValueError as e:
        return templates.TemplateResponse("learner/profile.html", {"request": request, "user": db_user, "error": str(e)})
    db_user.password_hash = hash_password(new_password)
    db_user.token_version += 1
    db.commit()
    return templates.TemplateResponse("learner/profile.html", {"request": request, "user": db_user, "success": "Password changed"})


@router.post("/request-deletion", name="learner.request_deletion")
def request_deletion(
    request: Request,
    csrf_token: str = Form(default=""),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    superadmins = db.query(User).filter(User.role == "superadmin", User.is_active == True).all()
    for sa in superadmins:
        create_notification(
            db, sa.id, "gdpr_deletion_request",
            f"Deletion request from {user.full_name} ({user.email})",
            f"Learner {user.full_name} ({user.email}) has requested account deletion.",
            action_url=f"/admin/users/{user.id}/edit",
        )
    flash(request, "Your account deletion request has been submitted to administrators.", "success")
    return RedirectResponse(url="/learner/profile", status_code=302)


@router.get("/training-record", response_class=HTMLResponse, name="learner.training_record")
def training_record(request: Request, success: str = None, error: str = None, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    enrolments = db.query(Enrolment).filter(
        Enrolment.user_id == user.id,
        Enrolment.status == "completed",
    ).all()
    certs = db.query(Certificate).filter(
        Certificate.user_id == user.id, Certificate.revoked == False
    ).all()
    external = db.query(TrainingRecord).filter(
        TrainingRecord.user_id == user.id
    ).all()
    return templates.TemplateResponse("learner/training_record.html", {
        "request": request, "user": user, "enrolments": enrolments,
        "certificates": certs, "external": external,
        "edit_record": None, "success": success, "error": error,
    })


@router.post("/training-record/add", name="learner.add_external_training")
def add_training_record(
    request: Request,
    title: str = Form(...),
    provider: str = Form(None),
    record_type: str = Form("external_training"),
    completion_date: str = Form(None),
    hours: float = Form(None),
    csrf_token: str = Form(default=""),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    record = TrainingRecord(
        user_id=user.id,
        record_type=record_type,
        title=title,
        provider=provider,
        completion_date=datetime.fromisoformat(completion_date) if completion_date else None,
        hours=hours,
    )
    db.add(record)
    db.commit()
    flash(request, "Training record added", "success")
    return RedirectResponse(url="/learner/training-record", status_code=302)


@router.get("/training-record/{record_id}/edit", response_class=HTMLResponse, name="learner.edit_training_record_form")
def edit_training_record_form(record_id: int, request: Request, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    record = db.query(TrainingRecord).filter(TrainingRecord.id == record_id, TrainingRecord.user_id == user.id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Training record not found")
    enrolments = db.query(Enrolment).filter(Enrolment.user_id == user.id, Enrolment.status == "completed").all()
    certs = db.query(Certificate).filter(Certificate.user_id == user.id, Certificate.revoked == False).all()
    external = db.query(TrainingRecord).filter(TrainingRecord.user_id == user.id).all()
    return templates.TemplateResponse("learner/training_record.html", {
        "request": request, "user": user, "enrolments": enrolments,
        "certificates": certs, "external": external,
        "edit_record": record, "success": None, "error": None,
    })


@router.post("/training-record/{record_id}/edit", name="learner.update_training_record")
def update_training_record(
    record_id: int,
    request: Request,
    title: str = Form(...),
    provider: str = Form(None),
    record_type: str = Form("external_training"),
    completion_date: str = Form(None),
    hours: float = Form(None),
    csrf_token: str = Form(default=""),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    record = db.query(TrainingRecord).filter(TrainingRecord.id == record_id, TrainingRecord.user_id == user.id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Training record not found")
    record.title = title
    record.provider = provider
    record.record_type = record_type
    record.completion_date = datetime.fromisoformat(completion_date) if completion_date else None
    record.hours = hours
    db.commit()
    flash(request, "Training record updated", "success")
    return RedirectResponse(url="/learner/training-record", status_code=302)


@router.post("/training-record/{record_id}/delete", name="learner.delete_training_record")
def delete_training_record(record_id: int, request: Request, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    record = db.query(TrainingRecord).filter(TrainingRecord.id == record_id, TrainingRecord.user_id == user.id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Training record not found")
    db.delete(record)
    db.commit()
    flash(request, "Training record deleted", "success")
    return RedirectResponse(url="/learner/training-record", status_code=302)


@router.get("/results", response_class=HTMLResponse, name="learner.results")
def my_results(request: Request, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    submissions = db.query(Submission).filter(
        Submission.user_id == user.id,
        Submission.status == "released",
    ).order_by(Submission.submitted_at.desc()).all()
    return templates.TemplateResponse("learner/results.html", {"request": request, "user": user, "submissions": submissions})


@router.get("/certificates", response_class=HTMLResponse, name="learner.certificates")
def my_certificates(request: Request, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    certs = db.query(Certificate).filter(
        Certificate.user_id == user.id, Certificate.revoked == False
    ).order_by(Certificate.issued_at.desc()).all()
    return templates.TemplateResponse("learner/certificates.html", {"request": request, "user": user, "certificates": certs})
