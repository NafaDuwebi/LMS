from fastapi import APIRouter, Request, Depends, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, FileResponse
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
from datetime import datetime, date
from services.flash import flash
from config import ORG_NAME

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
    import json
    try:
        prefs = json.loads(user.notification_preferences) if user.notification_preferences else {}
    except (json.JSONDecodeError, TypeError):
        prefs = {}
    return templates.TemplateResponse("learner/profile.html", {"request": request, "user": user, "prefs": prefs})


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


@router.post("/profile/preferences", name="learner.profile_preferences")
def update_preferences(
    request: Request,
    email_on_result: str = Form(""),
    email_on_certificate: str = Form(""),
    email_on_enrolment: str = Form(""),
    csrf_token: str = Form(default=""),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    import json
    db_user = db.query(User).filter(User.id == user.id).first()
    if db_user:
        prefs = {
            "email_on_result": email_on_result == "yes",
            "email_on_certificate": email_on_certificate == "yes",
            "email_on_enrolment": email_on_enrolment == "yes",
        }
        db_user.notification_preferences = json.dumps(prefs)
        db.commit()
    flash(request, "Notification preferences updated", "success")
    return RedirectResponse(url="/learner/profile", status_code=302)


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


@router.get("/training-record/download", name="learner.training_record_download")
def download_training_record(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    from io import BytesIO
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import mm
    from reportlab.pdfgen import canvas
    from reportlab.lib.colors import HexColor

    enrolments = db.query(Enrolment).filter(
        Enrolment.user_id == user.id, Enrolment.status == "completed"
    ).all()
    certs = db.query(Certificate).filter(
        Certificate.user_id == user.id, Certificate.revoked == False
    ).all()
    external = db.query(TrainingRecord).filter(
        TrainingRecord.user_id == user.id
    ).all()

    buf = BytesIO()
    pdf = canvas.Canvas(buf, pagesize=A4)
    width, height = A4
    y = height - 20 * mm
    primary = HexColor("#1A2B4A")
    accent = HexColor("#C9912B")

    pdf.setFont("Helvetica-Bold", 18)
    pdf.setFillColor(primary)
    pdf.drawString(20 * mm, y, "Training Transcript")
    y -= 8 * mm

    pdf.setFont("Helvetica", 11)
    pdf.setFillColor(HexColor("#333333"))
    pdf.drawString(20 * mm, y, f"Learner: {user.full_name}")
    y -= 5 * mm
    pdf.drawString(20 * mm, y, f"Organisation: {ORG_NAME}")
    y -= 5 * mm
    pdf.drawString(20 * mm, y, f"Generated: {date.today().strftime('%d %B %Y')}")
    y -= 12 * mm

    def section_header(text):
        nonlocal y
        pdf.setFont("Helvetica-Bold", 13)
        pdf.setFillColor(primary)
        pdf.drawString(20 * mm, y, text)
        y -= 7 * mm
        pdf.setStrokeColor(accent)
        pdf.setLineWidth(0.5)
        pdf.line(20 * mm, y, width - 20 * mm, y)
        y -= 5 * mm

    def table_row(cols, widths, bold=False):
        nonlocal y
        pdf.setFont("Helvetica-Bold" if bold else "Helvetica", 9)
        pdf.setFillColor(HexColor("#1A2B4A") if bold else HexColor("#333333"))
        x = 20 * mm
        for i, text in enumerate(cols):
            pdf.drawString(x, y, str(text))
            x += widths[i]
        y -= 4.5 * mm

    # Completed courses
    section_header("Completed Courses")
    col_w = [50 * mm, 40 * mm, 25 * mm, 30 * mm]
    table_row(["Course", "Cohort", "Score", "Completed"], col_w, bold=True)
    y -= 1 * mm
    for en in enrolments:
        ctitle = en.cohort.course.title if en.cohort and en.cohort.course else ""
        cname = en.cohort.name if en.cohort else ""
        cdate = en.completion_date.strftime("%d %b %Y") if en.completion_date else ""
        table_row([ctitle, cname, f"{en.final_score}%" if en.final_score else "", cdate], col_w)
        y -= 2 * mm
        if y < 30 * mm:
            pdf.showPage()
            y = height - 20 * mm
    y -= 6 * mm

    # External training
    section_header("External Training")
    col_w2 = [40 * mm, 35 * mm, 18 * mm, 30 * mm]
    table_row(["Title", "Provider", "Hours", "Completed"], col_w2, bold=True)
    y -= 1 * mm
    for t in external:
        cdate = t.completion_date.strftime("%d %b %Y") if t.completion_date else ""
        table_row([t.title, t.provider or "", str(t.hours or ""), cdate], col_w2)
        y -= 2 * mm
        if y < 30 * mm:
            pdf.showPage()
            y = height - 20 * mm
    y -= 6 * mm

    # Active certificates
    section_header("Active Certificates")
    col_w3 = [45 * mm, 40 * mm, 25 * mm, 25 * mm]
    table_row(["Certificate #", "Course", "Issued", "Expiry"], col_w3, bold=True)
    y -= 1 * mm
    for c in certs:
        issued = c.issued_at.strftime("%d %b %Y") if c.issued_at else ""
        expiry = c.expiry_date.strftime("%d %b %Y") if c.expiry_date else "N/A"
        table_row([c.certificate_number, c.course.title if c.course else "", issued, expiry], col_w3)
        y -= 2 * mm
        if y < 30 * mm:
            pdf.showPage()
            y = height - 20 * mm

    pdf.save()
    buf.seek(0)
    filename = f"training_transcript_{user.username}_{date.today()}.pdf"
    return FileResponse(buf, media_type="application/pdf", filename=filename, headers={"Content-Disposition": f"attachment; filename={filename}"})


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
