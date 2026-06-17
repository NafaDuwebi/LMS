from fastapi import APIRouter, Request, Depends, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, FileResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from database import get_db
from models.user import User
from models.course import Course
from models.cohort import Enrolment
from models.certificate import Certificate
from services.auth_service import get_current_user, require_role
from services.certificate_service import generate_certificate_pdf, revoke_certificate
from services.notification_service import send_certificate_notification
from services.audit_service import log_action
from services.flash import flash
import os

router = APIRouter(prefix="/certificates", tags=["certificates"])
from template_utils import templates


@router.get("", response_class=HTMLResponse, name="certificates.list")
def list_certificates(request: Request, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if user.role == "learner":
        certs = db.query(Certificate).filter(Certificate.user_id == user.id).order_by(Certificate.issued_at.desc()).all()
    elif user.role == "superadmin":
        certs = db.query(Certificate).order_by(Certificate.issued_at.desc()).all()
    else:
        from models.cohort import Cohort
        course_ids = db.query(Cohort.course_id).filter(Cohort.trainer_id == user.id).distinct()
        certs = db.query(Certificate).filter(Certificate.course_id.in_(course_ids)).order_by(Certificate.issued_at.desc()).all()
    return templates.TemplateResponse("shared/certificates.html", {"request": request, "user": user, "certificates": certs})


@router.post("/issue/{enrolment_id}", name="certificates.issue")
def issue_certificate(
    request: Request,
    enrolment_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if user.role not in ("superadmin", "trainer"):
        raise HTTPException(status_code=403, detail="Not authorised")

    enrolment = db.query(Enrolment).filter(Enrolment.id == enrolment_id, Enrolment.status == "completed").first()
    if not enrolment:
        flash(request, "Enrolment not completed", "error")
        return RedirectResponse(url="/cohorts", status_code=302)

    existing = db.query(Certificate).filter(
        Certificate.user_id == enrolment.user_id,
        Certificate.course_id == enrolment.cohort.course_id,
        Certificate.revoked == False,
    ).first()
    if existing:
        flash(request, "Certificate already issued for this learner", "warning")
        return RedirectResponse(url=f"/cohorts/{enrolment.cohort_id}", status_code=302)

    learner = enrolment.user
    course = enrolment.cohort.course
    cert = generate_certificate_pdf(db, learner, course, enrolment)
    send_certificate_notification(db, learner.id, course.title, cert.certificate_number)
    log_action(db, user.id, "issue_certificate", "certificate", cert.id, f"Issued certificate {cert.certificate_number} to {learner.email} for {course.title}")
    cohort_id = enrolment.cohort_id
    flash(request, f"Certificate issued for {learner.full_name}", "success")
    return RedirectResponse(url=f"/cohorts/{cohort_id}", status_code=302)


@router.post("/{cert_id}/revoke", name="certificates.revoke")
def revoke(
    request: Request,
    cert_id: int,
    reason: str = Form(...),
    csrf_token: str = Form(default=""),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    cert = db.query(Certificate).filter(Certificate.id == cert_id).first()
    log_action(db, user.id, "revoke_certificate", "certificate", cert_id, f"Revoked certificate {cert.certificate_number if cert else ''}: {reason}")
    revoke_certificate(db, cert_id, reason)
    flash(request, "Certificate revoked", "success")
    return RedirectResponse(url="/certificates", status_code=302)


@router.get("/{cert_id}/download", name="certificates.download")
def download_certificate(cert_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    cert = db.query(Certificate).filter(Certificate.id == cert_id).first()
    if not cert or not cert.pdf_path or not os.path.exists(cert.pdf_path):
        raise HTTPException(status_code=404)
    return FileResponse(cert.pdf_path, filename=f"certificate_{cert.certificate_number}.pdf", headers={"Content-Disposition": f"attachment; filename=\"certificate_{cert.certificate_number}.pdf\""})


@router.get("/verify/{cert_number}", name="certificates.verify")
def verify_certificate(cert_number: str, request: Request, db: Session = Depends(get_db)):
    cert = db.query(Certificate).filter(Certificate.certificate_number == cert_number).first()
    valid = cert and not cert.revoked
    return templates.TemplateResponse("shared/verify_certificate.html", {
        "request": request, "certificate": cert, "valid": valid,
    })
