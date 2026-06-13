from fastapi import APIRouter, Request, Depends
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session, joinedload
from database import get_db
from models.user import User
from models.course import Course
from models.cohort import Cohort, Enrolment
from models.assessment import Assessment
from models.submission import Submission
from models.notification import Notification
from models.certificate import Certificate
from models.audit import AuditLog
from services.auth_service import get_current_user
from services.notification_service import get_unread_count
from sqlalchemy import func

router = APIRouter(dependencies=[Depends(get_current_user)])
from template_utils import templates


def get_common_context(request: Request, user: User, db: Session):
    return {
        "request": request,
        "user": user,
        "unread_count": get_unread_count(db, user.id),
    }


@router.get("/dashboard")
def dashboard(request: Request, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if user.role == "superadmin":
        return admin_dashboard(request, user, db)
    elif user.role == "trainer":
        return trainer_dashboard(request, user, db)
    elif user.role == "observer":
        return observer_dashboard(request, user, db)
    elif user.role == "external_assessor":
        from routers.external_assessor import assessor_dashboard as ext_assessor_dashboard
        return ext_assessor_dashboard(request, user, db)
    else:
        return learner_dashboard(request, user, db)


def admin_dashboard(request, user, db):
    total_learners = db.query(User).filter(User.role == "learner", User.is_active == True).count()
    total_trainers = db.query(User).filter(User.role == "trainer", User.is_active == True).count()
    active_cohorts = db.query(Cohort).filter(Cohort.is_active == True).count()
    total_courses = db.query(Course).count()
    pending_marking = db.query(Submission).filter(Submission.status == "submitted").count()
    expiring_certs = db.query(Certificate).filter(
        Certificate.revoked == False,
        Certificate.expiry_date.isnot(None),
    ).count()

    recent_enrolments = db.query(Enrolment).order_by(Enrolment.enrolled_at.desc()).limit(5).all()

    return templates.TemplateResponse("admin/dashboard.html", {
        **get_common_context(request, user, db),
        "total_learners": total_learners,
        "total_trainers": total_trainers,
        "active_cohorts": active_cohorts,
        "total_courses": total_courses,
        "pending_marking": pending_marking,
        "expiring_certs": expiring_certs,
        "recent_enrolments": recent_enrolments,
    })


def trainer_dashboard(request, user, db):
    my_cohorts = db.query(Cohort).filter(Cohort.trainer_id == user.id).count()
    pending = db.query(Submission).join(Submission.assessment).join(Assessment.course).join(
        Course.cohorts
    ).filter(
        Cohort.trainer_id == user.id,
        Submission.status == "submitted",
    ).count()
    upcoming_sessions = db.query(Cohort).filter(
        Cohort.trainer_id == user.id,
        Cohort.is_active == True,
    ).count()

    cohorts = db.query(Cohort).filter(Cohort.trainer_id == user.id).all()

    return templates.TemplateResponse("trainer/dashboard.html", {
        **get_common_context(request, user, db),
        "my_cohorts": my_cohorts,
        "pending_marking": pending,
        "upcoming_sessions": upcoming_sessions,
        "cohorts": cohorts,
    })


def learner_dashboard(request, user, db):
    enrolments = db.query(Enrolment).options(
        joinedload(Enrolment.cohort).joinedload(Cohort.course)
    ).filter(
        Enrolment.user_id == user.id,
        Enrolment.status.in_(["enrolled", "in_progress", "completed"]),
    ).all()

    notifications = db.query(Notification).filter(
        Notification.user_id == user.id, Notification.is_read == False
    ).order_by(Notification.created_at.desc()).limit(5).all()

    return templates.TemplateResponse("learner/dashboard.html", {
        **get_common_context(request, user, db),
        "enrolments": enrolments,
        "notifications": notifications,
    })


def observer_dashboard(request, user, db):
    cohorts = db.query(Cohort).filter(Cohort.is_active == True).all()
    return templates.TemplateResponse("shared/observer_dashboard.html", {
        **get_common_context(request, user, db),
        "cohorts": cohorts,
    })
