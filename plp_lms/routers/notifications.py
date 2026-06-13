from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from database import get_db
from models.user import User
from models.notification import Notification
from services.auth_service import get_current_user
from services.notification_service import get_unread_count, get_notifications, mark_as_read, mark_all_read
from services.flash import flash

router = APIRouter(prefix="/notifications", tags=["notifications"])
from template_utils import templates


@router.get("", response_class=HTMLResponse, name="notifications.list")
def list_notifications(request: Request, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    notifications = get_notifications(db, user.id)
    return templates.TemplateResponse("shared/notifications.html", {
        "request": request, "user": user, "notifications": notifications,
    })


@router.post("/mark-read/{notification_id}", name="notifications.mark_read")
def mark_read(request: Request, notification_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    mark_as_read(db, notification_id)
    flash(request, "Notification marked as read", "success")
    return RedirectResponse(url="/notifications", status_code=302)


@router.post("/mark-all-read", name="notifications.mark_all_read")
def mark_all(request: Request, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    mark_all_read(db, user.id)
    flash(request, "All notifications marked as read", "success")
    return RedirectResponse(url="/notifications", status_code=302)


@router.get("/unread-count", name="notifications.unread_count")
def unread_count(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    count = get_unread_count(db, user.id)
    return JSONResponse({"count": count})
