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
    db.commit()
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


def send_result_notification(db: Session, user_id: int, assessment_title: str, score: float, passed: bool):
    status = "passed" if passed else "did not pass"
    create_notification(
        db, user_id, "result",
        f"Assessment Result: {assessment_title}",
        f"You {status} {assessment_title} with a score of {score:.1f}%.",
        action_url="/learner/results",
    )


def send_certificate_notification(db: Session, user_id: int, course_title: str, cert_number: str):
    create_notification(
        db, user_id, "certificate",
        f"Certificate Issued: {course_title}",
        f"Your certificate {cert_number} for {course_title} has been issued.",
        action_url="/learner/certificates",
    )
