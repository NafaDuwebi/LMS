from sqlalchemy.orm import Session
from models.notification import Notification
from datetime import datetime, timedelta


def create_notification(db: Session, user_id: int, type: str, title: str, message: str = None, action_url: str = None):
    notif = Notification(
        user_id=user_id,
        type=type,
        title=title,
        message=message,
        action_url=action_url,
    )
    db.add(notif)
    return notif


def get_unread_count(db: Session, user_id: int) -> int:
    return db.query(Notification).filter(
        Notification.user_id == user_id,
        Notification.is_read == False,
    ).count()


def get_notifications(db: Session, user_id: int, limit: int = 50):
    return db.query(Notification).filter(
        Notification.user_id == user_id,
    ).order_by(Notification.created_at.desc()).limit(limit).all()


def mark_as_read(db: Session, notification_id: int):
    notif = db.query(Notification).filter(Notification.id == notification_id).first()
    if notif:
        notif.is_read = True
        db.commit()
    return notif


def mark_all_read(db: Session, user_id: int):
    db.query(Notification).filter(
        Notification.user_id == user_id,
        Notification.is_read == False,
    ).update({"is_read": True})
    db.commit()


def send_enrolment_notification(db: Session, user_id: int, cohort_name: str):
    create_notification(
        db, user_id, "enrolment",
        f"Enrolled in {cohort_name}",
        f"You have been enrolled in {cohort_name}.",
    )
    from services.email_service import send_email
    from models.user import User
    from config import BASE_URL
    import json
    learner = db.query(User).get(user_id)
    if learner:
        prefs = json.loads(learner.notification_preferences or "{}")
        if not prefs.get("email_on_enrolment", True):
            return
        html_body = f'<p>Hi {learner.full_name},</p><p>You have been enrolled in <strong>{cohort_name}</strong>.</p><p><a href="{BASE_URL}/learner/courses">View your courses here</a></p>'
        send_email(learner.email, f"Enrolled in {cohort_name}", html_body, learner.id, db)


def send_result_notification(db: Session, user_id: int, assessment_title: str, score: float, passed: bool):
    status = "passed" if passed else "did not pass"
    create_notification(
        db, user_id, "result",
        f"Assessment Result: {assessment_title}",
        f"You {status} {assessment_title} with a score of {score:.1f}%.",
        action_url="/learner/results",
    )
    from services.email_service import send_email
    from models.user import User
    from config import BASE_URL
    import json
    learner = db.query(User).get(user_id)
    if learner:
        prefs = json.loads(learner.notification_preferences or "{}")
        if not prefs.get("email_on_result", True):
            return
        score_display = f"{score:.1f}"
        outcome = "Passed" if passed else "Not Passed"
        html_body = f'<p>Hi {learner.full_name},</p><p>Your submission for <strong>{assessment_title}</strong> has been marked.</p><p>Score: {score_display}% &mdash; {outcome}.</p><p><a href="{BASE_URL}/learner/results">View your full feedback here</a></p>'
        send_email(learner.email, f'Result released: {assessment_title}', html_body, learner.id, db)


def send_certificate_notification(db: Session, user_id: int, course_title: str, cert_number: str):
    create_notification(
        db, user_id, "certificate",
        f"Certificate Issued: {course_title}",
        f"Your certificate {cert_number} for {course_title} has been issued.",
        action_url="/learner/certificates",
    )
    from services.email_service import send_email
    from models.user import User
    from config import BASE_URL
    import json
    learner = db.query(User).get(user_id)
    if learner:
        prefs = json.loads(learner.notification_preferences or "{}")
        if not prefs.get("email_on_certificate", True):
            return
        html_body = f'<p>Hi {learner.full_name},</p><p>Your certificate <strong>{cert_number}</strong> for <strong>{course_title}</strong> has been issued.</p><p><a href="{BASE_URL}/learner/certificates">View your certificates here</a></p>'
        send_email(learner.email, f"Certificate issued: {course_title}", html_body, learner.id, db)
