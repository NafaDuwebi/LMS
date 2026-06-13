from fastapi import APIRouter, Request, Depends, Form, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
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
from typing import Optional
import csv
import io

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


@router.get("/compliance/csv", name="reports.compliance_csv")
def compliance_report_csv(db: Session = Depends(get_db), user: User = Depends(require_role("superadmin", "trainer", "observer"))):
    data = generate_compliance_report(db)
    headers = ["cert_number", "learner", "course", "expiry", "days_remaining", "status"]
    csv_content = generate_csv(data, headers)
    from fastapi.responses import Response
    return Response(content=csv_content, media_type="text/csv", headers={"Content-Disposition": "attachment; filename=compliance_report.csv"})
