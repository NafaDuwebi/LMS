import csv
import io
import os
from typing import List, Dict
from sqlalchemy.orm import Session, joinedload
from datetime import datetime
from config import BASE_URL, ORG_NAME


def generate_csv(data: List[Dict], headers: List[str]) -> str:
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(headers)
    for row in data:
        writer.writerow([row.get(h, "") for h in headers])
    return output.getvalue()


def generate_cohort_summary_report(db, cohort_id: int):
    from models.cohort import Cohort, Enrolment
    from models.attendance import AttendanceRecord
    from models.system_settings import SystemSetting
    cohort = db.query(Cohort).filter(Cohort.id == cohort_id).first()
    if not cohort:
        return None

    all_session_dates = set(r.session_date for r in db.query(AttendanceRecord).filter(AttendanceRecord.cohort_id == cohort_id).all())
    total_sessions = len(all_session_dates)
    min_attendance_setting = db.query(SystemSetting).filter_by(key="min_attendance").first()
    min_attendance = int(min_attendance_setting.value) if min_attendance_setting and min_attendance_setting.value else 80

    enrolments = db.query(Enrolment).options(joinedload(Enrolment.user)).filter(Enrolment.cohort_id == cohort_id).all()
    data = []
    for en in enrolments:
        attended = db.query(AttendanceRecord).filter(
            AttendanceRecord.enrolment_id == en.id,
            AttendanceRecord.attended == True,
        ).count()
        attendance_pct = round(attended / total_sessions * 100, 1) if total_sessions > 0 else None
        meets_attendance = attendance_pct >= min_attendance if attendance_pct is not None else None
        data.append({
            "learner_name": en.user.full_name if en.user else "",
            "email": en.user.email if en.user else "",
            "status": en.status,
            "enrolled_date": en.enrolled_at.strftime("%Y-%m-%d") if en.enrolled_at else "",
            "completion_date": en.completion_date.strftime("%Y-%m-%d") if en.completion_date else "",
            "final_score": en.final_score or "",
            "attendance_pct": attendance_pct,
            "meets_attendance": meets_attendance,
        })
    return data


def generate_learner_progress_report(db, course_id: int, user_id: int):
    from services.progress_service import get_learner_progress
    progress = get_learner_progress(db, user_id, course_id)
    if not progress:
        return None
    data = []
    for ms in progress["module_statuses"]:
        data.append({
            "module": ms["module"].title,
            "materials": ms["material_count"],
            "assessments": ms["assessment_count"],
            "passed": ms["passed_assessments"],
            "completed": "Yes" if ms["is_completed"] else "No",
        })
    return data


def generate_certificate_register_report(db):
    from models.certificate import Certificate
    certs = db.query(Certificate).filter(Certificate.revoked == False).all()
    data = []
    for c in certs:
        data.append({
            "cert_number": c.certificate_number,
            "learner": c.user.full_name if c.user else "",
            "course": c.course.title if c.course else "",
            "issued": c.issued_at.strftime("%Y-%m-%d") if c.issued_at else "",
            "expiry": c.expiry_date.strftime("%Y-%m-%d") if c.expiry_date else "N/A",
        })
    return data


def generate_compliance_report(db):
    from models.certificate import Certificate
    now = datetime.utcnow()

    certs = db.query(Certificate).filter(Certificate.revoked == False).all()

    data = []
    for c in certs:
        days_remaining = (c.expiry_date - now).days if c.expiry_date else None
        if days_remaining is None:
            status = "no_expiry"
        elif days_remaining <= 0:
            status = "expired"
        elif days_remaining <= 30:
            status = "expiring_soon"
        else:
            status = "valid"
        data.append({
            "cert_number": c.certificate_number,
            "learner": c.user.full_name if c.user else "",
            "course": c.course.title if c.course else "",
            "expiry": c.expiry_date.strftime("%Y-%m-%d") if c.expiry_date else "",
            "days_remaining": days_remaining or 0,
            "status": status,
        })
    return data
