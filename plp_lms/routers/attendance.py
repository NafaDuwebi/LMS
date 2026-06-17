from fastapi import APIRouter, Request, Depends, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from database import get_db
from models.user import User
from models.cohort import Cohort, Enrolment, AttendanceRecord
from services.auth_service import get_current_user, require_role
from datetime import date
from services.flash import flash

router = APIRouter(prefix="/attendance", tags=["attendance"])
from template_utils import templates


@router.get("/{cohort_id}", response_class=HTMLResponse, name="attendance.register")
def attendance_register(request: Request, cohort_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    cohort = db.query(Cohort).filter(Cohort.id == cohort_id).first()
    if not cohort:
        raise HTTPException(status_code=404)

    enrolments = db.query(Enrolment).filter(
        Enrolment.cohort_id == cohort_id,
        Enrolment.status.in_(["enrolled", "in_progress"]),
    ).all()

    session_dates = db.query(AttendanceRecord.session_date).filter(
        AttendanceRecord.cohort_id == cohort_id
    ).distinct().order_by(AttendanceRecord.session_date).all()
    session_dates = [s[0] for s in session_dates]

    attendance_map = {}
    for en in enrolments:
        records = db.query(AttendanceRecord).filter(
            AttendanceRecord.enrolment_id == en.id,
            AttendanceRecord.cohort_id == cohort_id,
        ).all()
        attendance_map[en.id] = {r.session_date: r for r in records}

    return templates.TemplateResponse("shared/attendance_register.html", {
        "request": request, "user": user, "cohort": cohort,
        "enrolments": enrolments, "session_dates": session_dates,
        "attendance_map": attendance_map,
    })


@router.post("/{cohort_id}/session", name="attendance.add_session")
def add_session(
    request: Request,
    cohort_id: int,
    session_date: str = Form(...),
    csrf_token: str = Form(default=""),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    cohort = db.query(Cohort).filter(Cohort.id == cohort_id).first()
    if not cohort:
        raise HTTPException(status_code=404)

    parsed_date = date.fromisoformat(session_date)
    enrolments = db.query(Enrolment).filter(
        Enrolment.cohort_id == cohort_id,
        Enrolment.status.in_(["enrolled", "in_progress"]),
    ).all()

    for en in enrolments:
        existing = db.query(AttendanceRecord).filter(
            AttendanceRecord.enrolment_id == en.id,
            AttendanceRecord.session_date == parsed_date,
        ).first()
        if not existing:
            record = AttendanceRecord(
                enrolment_id=en.id,
                cohort_id=cohort_id,
                session_date=parsed_date,
                recorded_by=user.id,
            )
            db.add(record)
    db.commit()
    flash(request, "Session created", "success")
    return RedirectResponse(url=f"/attendance/{cohort_id}", status_code=302)


@router.post("/{cohort_id}/record", name="attendance.save")
async def record_attendance(
    cohort_id: int,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    form_data = await request.form()
    cohort = db.query(Cohort).filter(Cohort.id == cohort_id).first()
    if not cohort:
        raise HTTPException(status_code=404)

    all_records = db.query(AttendanceRecord).filter(
        AttendanceRecord.cohort_id == cohort_id
    ).all()
    for record in all_records:
        record.attended = False

    for key, value in form_data.items():
        if key.startswith("attendance-"):
            parts = key.split("-", 2)
            if len(parts) == 3:
                enrolment_id = int(parts[1])
                session_date = date.fromisoformat(parts[2])
                record = db.query(AttendanceRecord).filter(
                    AttendanceRecord.enrolment_id == enrolment_id,
                    AttendanceRecord.session_date == session_date,
                ).first()
                if record:
                    record.attended = True
                    record.recorded_by = user.id

    for key, value in form_data.items():
        if key.startswith("notes-"):
            parts = key.split("-", 2)
            if len(parts) == 3:
                enrolment_id = int(parts[1])
                session_date = date.fromisoformat(parts[2])
                record = db.query(AttendanceRecord).filter(
                    AttendanceRecord.enrolment_id == enrolment_id,
                    AttendanceRecord.session_date == session_date,
                ).first()
                if record:
                    record.notes = value

    db.commit()
    flash(request, "Attendance recorded", "success")
    return RedirectResponse(url=f"/attendance/{cohort_id}", status_code=302)


@router.post("/{cohort_id}/session/delete", name="attendance.delete_session")
def delete_session(
    request: Request,
    cohort_id: int,
    session_date: str = Form(...),
    csrf_token: str = Form(default=""),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    parsed_date = date.fromisoformat(session_date)
    db.query(AttendanceRecord).filter(
        AttendanceRecord.cohort_id == cohort_id,
        AttendanceRecord.session_date == parsed_date,
    ).delete()
    db.commit()
    flash(request, "Session deleted", "success")
    return RedirectResponse(url=f"/attendance/{cohort_id}", status_code=302)
