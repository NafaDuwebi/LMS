from fastapi import APIRouter, Request, Depends, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session, joinedload
from database import get_db
from models.user import User
from models.course import Course
from models.cohort import Cohort, Enrolment
from models.submission import Submission
from services.auth_service import get_current_user, require_role

router = APIRouter(prefix="/trainer", tags=["trainer"], dependencies=[Depends(require_role("trainer", "superadmin"))])
from template_utils import templates


@router.get("/cohorts", response_class=HTMLResponse, name="trainer.cohorts")
def my_cohorts(request: Request, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    q = db.query(Cohort).options(joinedload(Cohort.course), joinedload(Cohort.trainer))
    if user.role == "superadmin":
        cohorts = q.all()
    else:
        cohorts = q.filter(Cohort.trainer_id == user.id).all()
    return templates.TemplateResponse("trainer/cohorts.html", {"request": request, "user": user, "cohorts": cohorts})


@router.get("/learners", response_class=HTMLResponse, name="trainer.learners")
def my_learners(request: Request, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    cohorts = db.query(Cohort).options(joinedload(Cohort.course)).filter(Cohort.trainer_id == user.id).all()
    cohort_ids = [c.id for c in cohorts]
    enrolments = db.query(Enrolment).options(joinedload(Enrolment.user)).filter(Enrolment.cohort_id.in_(cohort_ids)).all()
    return templates.TemplateResponse("trainer/learners.html", {"request": request, "user": user, "cohorts": cohorts, "enrolments": enrolments})


@router.get("/attendance", response_class=HTMLResponse, name="trainer.attendance")
def attendance_cohorts(request: Request, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    q = db.query(Cohort).options(joinedload(Cohort.course), joinedload(Cohort.trainer))
    if user.role == "superadmin":
        cohorts = q.all()
    else:
        cohorts = q.filter(Cohort.trainer_id == user.id).all()
    return templates.TemplateResponse("trainer/attendance_cohorts.html", {"request": request, "user": user, "cohorts": cohorts})


@router.get("/submissions", response_class=HTMLResponse, name="trainer.submissions")
def pending_submissions(request: Request, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    from models.assessment import Assessment
    course_ids = db.query(Cohort.course_id).filter(Cohort.trainer_id == user.id).distinct()
    submissions = db.query(Submission).options(
        joinedload(Submission.user), joinedload(Submission.assessment).joinedload(Assessment.course)
    ).join(Submission.assessment).filter(
        Submission.status == "submitted",
        Assessment.course_id.in_(course_ids),
    ).order_by(Submission.submitted_at).all()
    return templates.TemplateResponse("trainer/submissions.html", {"request": request, "user": user, "submissions": submissions})
