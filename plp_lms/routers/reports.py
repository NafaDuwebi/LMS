from fastapi import APIRouter, Request, Depends, Form, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse, Response
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from database import get_db
from models.user import User
from models.course import Course
from models.cohort import Cohort
from services.auth_service import get_current_user, require_role
from services.report_service import (
    generate_cohort_summary_report,
    generate_learner_progress_report,
    generate_certificate_register_report,
    generate_compliance_report,
    generate_csv,
)
from services.report_export_service import generate_report_pdf, generate_report_xlsx
from typing import Optional
from io import BytesIO

router = APIRouter(prefix="/reports", tags=["reports"])
from template_utils import templates


@router.get("", response_class=HTMLResponse, name="reports.index")
def reports_page(request: Request, user: User = Depends(require_role("superadmin", "trainer", "observer")), db: Session = Depends(get_db)):
    cohorts = db.query(Cohort).filter(Cohort.is_active == True).all()
    courses = db.query(Course).filter(Course.is_published == True).all()
    return templates.TemplateResponse("shared/reports.html", {
        "request": request, "user": user, "cohorts": cohorts, "courses": courses,
    })


@router.get("/cohort-summary", name="reports.cohort_summary")
def cohort_summary_report(request: Request, cohort_id: Optional[int] = None, db: Session = Depends(get_db), user: User = Depends(require_role("superadmin", "trainer", "observer"))):
    if cohort_id is None:
        return templates.TemplateResponse("shared/_report_fragment.html", {"request": request, "error": "Please select a cohort"})
    data = generate_cohort_summary_report(db, cohort_id)
    return templates.TemplateResponse("shared/_report_fragment.html", {"request": request, "data": data})


@router.get("/learner-progress", name="reports.learner_progress")
def learner_progress_report(request: Request, course_id: Optional[int] = None, learner_id: Optional[int] = None, db: Session = Depends(get_db), user: User = Depends(require_role("superadmin", "trainer", "observer"))):
    if course_id is None or learner_id is None:
        return templates.TemplateResponse("shared/_report_fragment.html", {"request": request, "error": "Please select a course and learner"})
    data = generate_learner_progress_report(db, course_id, learner_id)
    return templates.TemplateResponse("shared/_report_fragment.html", {"request": request, "data": data})


@router.get("/certificate-register", name="reports.certificate_register")
def certificate_register_report(request: Request, db: Session = Depends(get_db), user: User = Depends(require_role("superadmin", "trainer", "observer"))):
    data = generate_certificate_register_report(db)
    return templates.TemplateResponse("shared/_report_fragment.html", {"request": request, "data": data})


@router.get("/compliance", name="reports.compliance")
def compliance_report(request: Request, db: Session = Depends(get_db), user: User = Depends(require_role("superadmin", "trainer", "observer"))):
    data = generate_compliance_report(db)
    return templates.TemplateResponse("shared/_report_fragment.html", {"request": request, "data": data})


def _respond_xlsx(data, headers, filename):
    buf = generate_report_xlsx(filename.replace(".xlsx", "").replace("_", " ").title(), headers, data)
    return FileResponse(buf, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", filename=filename, headers={"Content-Disposition": f"attachment; filename={filename}"})


def _respond_pdf(data, headers, filename):
    title = filename.replace(".pdf", "").replace("_", " ").title()
    buf = generate_report_pdf(title, headers, data)
    return FileResponse(buf, media_type="application/pdf", filename=filename, headers={"Content-Disposition": f"attachment; filename={filename}"})


def _respond_csv(data, headers, filename):
    csv_content = generate_csv(data, headers)
    return Response(content=csv_content, media_type="text/csv", headers={"Content-Disposition": f"attachment; filename={filename}"})


COHORT_HEADERS = ["learner_name", "email", "status", "enrolled_date", "completion_date", "final_score", "attendance_pct", "meets_attendance"]


@router.get("/cohort-summary/pdf", name="reports.cohort_summary_pdf")
def cohort_summary_pdf(cohort_id: int, db: Session = Depends(get_db), user: User = Depends(require_role("superadmin", "trainer", "observer"))):
    data = generate_cohort_summary_report(db, cohort_id) or []
    return _respond_pdf(data, COHORT_HEADERS, "cohort_summary.pdf")


@router.get("/cohort-summary/xlsx", name="reports.cohort_summary_xlsx")
def cohort_summary_xlsx(cohort_id: int, db: Session = Depends(get_db), user: User = Depends(require_role("superadmin", "trainer", "observer"))):
    data = generate_cohort_summary_report(db, cohort_id) or []
    return _respond_xlsx(data, COHORT_HEADERS, "cohort_summary.xlsx")


PROGRESS_HEADERS = ["module", "materials", "assessments", "passed", "completed"]


@router.get("/learner-progress/pdf", name="reports.learner_progress_pdf")
def learner_progress_pdf(course_id: int, learner_id: int, db: Session = Depends(get_db), user: User = Depends(require_role("superadmin", "trainer", "observer"))):
    data = generate_learner_progress_report(db, course_id, learner_id) or []
    return _respond_pdf(data, PROGRESS_HEADERS, "learner_progress.pdf")


@router.get("/learner-progress/xlsx", name="reports.learner_progress_xlsx")
def learner_progress_xlsx(course_id: int, learner_id: int, db: Session = Depends(get_db), user: User = Depends(require_role("superadmin", "trainer", "observer"))):
    data = generate_learner_progress_report(db, course_id, learner_id) or []
    return _respond_xlsx(data, PROGRESS_HEADERS, "learner_progress.xlsx")


CERT_HEADERS = ["cert_number", "learner", "course", "issued", "expiry"]


@router.get("/certificate-register/pdf", name="reports.certificate_register_pdf")
def certificate_register_pdf(db: Session = Depends(get_db), user: User = Depends(require_role("superadmin", "trainer", "observer"))):
    data = generate_certificate_register_report(db) or []
    return _respond_pdf(data, CERT_HEADERS, "certificate_register.pdf")


@router.get("/certificate-register/xlsx", name="reports.certificate_register_xlsx")
def certificate_register_xlsx(db: Session = Depends(get_db), user: User = Depends(require_role("superadmin", "trainer", "observer"))):
    data = generate_certificate_register_report(db) or []
    return _respond_xlsx(data, CERT_HEADERS, "certificate_register.xlsx")


@router.get("/certificate-register/csv", name="reports.certificate_register_csv")
def certificate_register_csv(db: Session = Depends(get_db), user: User = Depends(require_role("superadmin", "trainer", "observer"))):
    data = generate_certificate_register_report(db) or []
    return _respond_csv(data, CERT_HEADERS, "certificate_register.csv")


COMPLIANCE_HEADERS = ["cert_number", "learner", "course", "expiry", "days_remaining", "status"]


@router.get("/compliance/pdf", name="reports.compliance_pdf")
def compliance_report_pdf(db: Session = Depends(get_db), user: User = Depends(require_role("superadmin", "trainer", "observer"))):
    data = generate_compliance_report(db) or []
    return _respond_pdf(data, COMPLIANCE_HEADERS, "compliance_report.pdf")


@router.get("/compliance/xlsx", name="reports.compliance_xlsx")
def compliance_report_xlsx(db: Session = Depends(get_db), user: User = Depends(require_role("superadmin", "trainer", "observer"))):
    data = generate_compliance_report(db) or []
    return _respond_xlsx(data, COMPLIANCE_HEADERS, "compliance_report.xlsx")


@router.get("/compliance/csv", name="reports.compliance_csv")
def compliance_report_csv(db: Session = Depends(get_db), user: User = Depends(require_role("superadmin", "trainer", "observer"))):
    data = generate_compliance_report(db) or []
    return _respond_csv(data, COMPLIANCE_HEADERS, "compliance_report.csv")
