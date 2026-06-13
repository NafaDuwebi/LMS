from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from database import get_db
from models.user import User
from models.assessment import Assessment
from models.skill import SkillClaim
from models.notification import Notification
from services.auth_service import get_current_user, require_role
from services.notification_service import get_unread_count

router = APIRouter(prefix="/external-assessor", tags=["external_assessor"])
from template_utils import templates


@router.get("/dashboard", response_class=HTMLResponse)
def assessor_dashboard(request: Request, user: User = Depends(require_role("external_assessor", "superadmin")), db: Session = Depends(get_db)):
    pending_claims = db.query(SkillClaim).filter(
        SkillClaim.status == "pending"
    ).order_by(SkillClaim.submitted_at.desc()).count()
    recent_claims = db.query(SkillClaim).filter(
        SkillClaim.status == "pending"
    ).order_by(SkillClaim.submitted_at.desc()).limit(5).all()
    return templates.TemplateResponse("external_assessor/dashboard.html", {
        "request": request, "user": user, "pending_claims": pending_claims,
        "recent_claims": recent_claims,
        "unread_count": get_unread_count(db, user.id),
    })


@router.get("/skills", response_class=HTMLResponse)
def assessor_skills_review(request: Request, user: User = Depends(require_role("external_assessor", "superadmin")), db: Session = Depends(get_db)):
    claims = db.query(SkillClaim).filter(SkillClaim.status == "pending").order_by(SkillClaim.submitted_at).all()
    return templates.TemplateResponse("v2/skills_review.html", {
        "request": request, "user": user, "claims": claims,
        "unread_count": get_unread_count(db, user.id),
    })


@router.get("/assessments", response_class=HTMLResponse)
def assessor_assessments(request: Request, user: User = Depends(require_role("external_assessor", "superadmin")), db: Session = Depends(get_db)):
    assessments = db.query(Assessment).filter(Assessment.is_published == True).order_by(Assessment.title).all()
    return templates.TemplateResponse("shared/assessments.html", {
        "request": request, "user": user, "assessments": assessments,
        "unread_count": get_unread_count(db, user.id),
    })
