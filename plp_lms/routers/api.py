from fastapi import APIRouter, Query, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import or_
from database import get_db
from models.user import User
from services.auth_service import get_current_user

router = APIRouter(prefix="/api", tags=["api"])


@router.get("/users/search")
def search_users(
    q: str = Query("", min_length=1),
    role: str = Query(None),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    query = db.query(User.id, User.full_name, User.email).filter(User.is_active == True)
    if role:
        query = query.filter(User.role == role)
    if q:
        query = query.filter(
            or_(User.full_name.ilike(f"%{q}%"), User.email.ilike(f"%{q}%"))
        )
    results = query.order_by(User.full_name).limit(20).all()
    return JSONResponse([
        {"id": r.id, "full_name": r.full_name, "email": r.email} for r in results
    ])
