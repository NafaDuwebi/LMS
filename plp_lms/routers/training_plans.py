from fastapi import APIRouter, Request, Depends, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from sqlalchemy import func
from database import get_db
from models.user import User
from models.course import Course
from models.cohort import Enrolment
from models.training_plan import TrainingPlan, TrainingPlanItem, TrainingPlanAssignment
from services.auth_service import get_current_user, require_role
from services.flash import flash
from datetime import date, timedelta

router = APIRouter(prefix="/training-plans", tags=["training_plans"])
from template_utils import templates


@router.get("", response_class=HTMLResponse, name="training_plans.list")
def list_plans(request: Request, db: Session = Depends(get_db), user: User = Depends(require_role("superadmin", "trainer"))):
    plans = db.query(TrainingPlan).order_by(TrainingPlan.created_at.desc()).all()
    return templates.TemplateResponse("v2/training_plans.html", {"request": request, "user": user, "plans": plans})


@router.get("/create", response_class=HTMLResponse, name="training_plans.create")
def create_plan_page(request: Request, db: Session = Depends(get_db), user: User = Depends(require_role("superadmin", "trainer"))):
    courses = db.query(Course).order_by(Course.title).all()
    return templates.TemplateResponse("v2/training_plan_form.html", {"request": request, "user": user, "plan": None, "courses": courses})


@router.post("/create", name="training_plans.create_submit")
def create_plan(
    request: Request,
    title: str = Form(...),
    description: str = Form(None),
    is_active: bool = Form(False),
    csrf_token: str = Form(default=""),
    db: Session = Depends(get_db),
    user: User = Depends(require_role("superadmin", "trainer")),
):
    plan = TrainingPlan(title=title, description=description, is_active=is_active)
    db.add(plan)
    db.commit()
    flash(request, "Training plan created", "success")
    return RedirectResponse(url="/training-plans", status_code=302)


@router.get("/{plan_id}/edit", response_class=HTMLResponse, name="training_plans.edit")
def edit_plan_page(
    request: Request, plan_id: int, db: Session = Depends(get_db),
    user: User = Depends(require_role("superadmin", "trainer")),
):
    plan = db.query(TrainingPlan).filter(TrainingPlan.id == plan_id).first()
    if not plan:
        raise HTTPException(status_code=404)
    items = db.query(TrainingPlanItem).filter(TrainingPlanItem.plan_id == plan_id).all()
    courses = db.query(Course).order_by(Course.title).all()
    return templates.TemplateResponse("v2/training_plan_form.html", {"request": request, "user": user, "plan": plan, "items": items, "courses": courses})


@router.post("/{plan_id}/edit", name="training_plans.edit_submit")
def edit_plan(
    request: Request,
    plan_id: int,
    title: str = Form(...),
    description: str = Form(None),
    is_active: bool = Form(False),
    csrf_token: str = Form(default=""),
    db: Session = Depends(get_db),
    user: User = Depends(require_role("superadmin", "trainer")),
):
    plan = db.query(TrainingPlan).filter(TrainingPlan.id == plan_id).first()
    if not plan:
        raise HTTPException(status_code=404)
    plan.title = title
    plan.description = description
    plan.is_active = is_active
    db.commit()
    flash(request, "Training plan updated", "success")
    return RedirectResponse(url="/training-plans", status_code=302)


@router.post("/{plan_id}/add-item", name="training_plans.add_item")
def add_item(
    request: Request,
    plan_id: int,
    course_id: int = Form(...),
    due_within_days: int = Form(30),
    is_mandatory: bool = Form(True),
    csrf_token: str = Form(default=""),
    db: Session = Depends(get_db),
    user: User = Depends(require_role("superadmin", "trainer")),
):
    plan = db.query(TrainingPlan).filter(TrainingPlan.id == plan_id).first()
    if not plan:
        raise HTTPException(status_code=404)
    existing = db.query(TrainingPlanItem).filter(
        TrainingPlanItem.plan_id == plan_id, TrainingPlanItem.course_id == course_id
    ).first()
    if existing:
        flash(request, "Course already in plan", "error")
    else:
        item = TrainingPlanItem(plan_id=plan_id, course_id=course_id, due_within_days=due_within_days, is_mandatory=is_mandatory)
        db.add(item)
        db.commit()
        flash(request, "Course added to plan", "success")
    return RedirectResponse(url=f"/training-plans/{plan_id}/edit", status_code=302)


@router.post("/items/{item_id}/delete", name="training_plans.delete_item")
def delete_item(
    request: Request,
    item_id: int,
    csrf_token: str = Form(default=""),
    db: Session = Depends(get_db),
    user: User = Depends(require_role("superadmin", "trainer")),
):
    item = db.query(TrainingPlanItem).filter(TrainingPlanItem.id == item_id).first()
    if item:
        plan_id = item.plan_id
        db.delete(item)
        db.commit()
        flash(request, "Course removed from plan", "success")
        return RedirectResponse(url=f"/training-plans/{plan_id}/edit", status_code=302)
    raise HTTPException(status_code=404)


@router.post("/{plan_id}/delete", name="training_plans.delete")
def delete_plan(
    request: Request,
    plan_id: int,
    csrf_token: str = Form(default=""),
    db: Session = Depends(get_db),
    user: User = Depends(require_role("superadmin")),
):
    plan = db.query(TrainingPlan).filter(TrainingPlan.id == plan_id).first()
    if not plan:
        raise HTTPException(status_code=404)
    db.delete(plan)
    db.commit()
    flash(request, "Training plan deleted", "success")
    return RedirectResponse(url="/training-plans", status_code=302)
