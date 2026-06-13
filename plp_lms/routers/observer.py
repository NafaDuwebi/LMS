from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from database import get_db
from models.user import User
from models.course import Course, Module, LearningOutcome
from models.cohort import Cohort, Enrolment
from models.assessment import Assessment, Question
from services.auth_service import get_current_user, require_role

router = APIRouter(prefix="/observer", tags=["observer"])
from template_utils import templates


@router.get("/courses", response_class=HTMLResponse)
def observer_courses(request: Request, user: User = Depends(require_role("observer", "superadmin")), db: Session = Depends(get_db)):
    courses = db.query(Course).filter(Course.is_published == True).order_by(Course.title).all()
    return templates.TemplateResponse("shared/courses.html", {"request": request, "user": user, "courses": courses})


@router.get("/courses/{course_id}", response_class=HTMLResponse)
def observer_course_view(request: Request, course_id: int, db: Session = Depends(get_db), user: User = Depends(require_role("observer", "superadmin"))):
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404)
    modules = db.query(Module).filter(Module.course_id == course_id).order_by(Module.order_index).all()
    outcomes = db.query(LearningOutcome).filter(LearningOutcome.course_id == course_id).order_by(LearningOutcome.order_index).all()
    assessments = db.query(Assessment).filter(Assessment.course_id == course_id).order_by(Assessment.created_at.desc()).all()
    return templates.TemplateResponse("shared/course_view.html", {
        "request": request, "user": user, "course": course,
        "modules": modules, "outcomes": outcomes, "assessments": assessments,
    })


@router.get("/cohorts", response_class=HTMLResponse)
def observer_cohorts(request: Request, user: User = Depends(require_role("observer", "superadmin")), db: Session = Depends(get_db)):
    cohorts = db.query(Cohort).filter(Cohort.is_active == True).order_by(Cohort.name).all()
    return templates.TemplateResponse("shared/cohorts.html", {"request": request, "user": user, "cohorts": cohorts})


@router.get("/cohorts/{cohort_id}", response_class=HTMLResponse)
def observer_cohort_view(request: Request, cohort_id: int, user: User = Depends(require_role("observer", "superadmin")), db: Session = Depends(get_db)):
    cohort = db.query(Cohort).filter(Cohort.id == cohort_id).first()
    if not cohort:
        raise HTTPException(status_code=404)
    enrolments = db.query(Enrolment).filter(Enrolment.cohort_id == cohort_id).all()
    return templates.TemplateResponse("shared/cohort_view.html", {
        "request": request, "user": user, "cohort": cohort,
        "enrolments": enrolments,
    })


@router.get("/assessments", response_class=HTMLResponse)
def observer_assessments(request: Request, user: User = Depends(require_role("observer", "superadmin")), db: Session = Depends(get_db)):
    assessments = db.query(Assessment).filter(Assessment.is_published == True).order_by(Assessment.title).all()
    return templates.TemplateResponse("shared/assessments.html", {"request": request, "user": user, "assessments": assessments})
