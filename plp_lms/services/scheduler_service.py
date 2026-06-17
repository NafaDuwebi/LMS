from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime, time

scheduler = AsyncIOScheduler()


def flag_retention_records():
    from database import SessionLocal
    db = SessionLocal()
    try:
        from models.cohort import Enrolment
        from datetime import date
        expired = db.query(Enrolment).filter(Enrolment.retention_review_date <= date.today(), Enrolment.retention_status == "active").all()
        for en in expired:
            en.retention_status = "flagged"
        db.commit()
    finally:
        db.close()


def deliver_reports_task():
    from database import SessionLocal
    from models.report_subscription import ReportSubscription
    from services.report_service import generate_cohort_summary_report, generate_certificate_register_report, generate_compliance_report
    from services.email_service import send_email

    db = SessionLocal()
    now = datetime.utcnow()
    try:
        subs = db.query(ReportSubscription).filter(ReportSubscription.is_active == True).all()
        for sub in subs:
            t = sub.send_time or time(8, 0)
            if now.hour != t.hour or now.minute != t.minute:
                continue
            if sub.frequency == "weekly" and (sub.day_of_week is None or now.weekday() != sub.day_of_week):
                continue
            if sub.frequency == "monthly" and (sub.day_of_month is None or now.day != sub.day_of_month):
                continue

            if sub.report_id == 1:
                data = generate_cohort_summary_report(db, 0)
                subject = "Cohort Summary Report"
            elif sub.report_id == 3:
                data = generate_certificate_register_report(db)
                subject = "Certificate Register Report"
            elif sub.report_id == 4:
                data = generate_compliance_report(db)
                subject = "Compliance Report"
            else:
                continue

            body = f"<h2>{subject}</h2><pre>{data}</pre>"
            recipients = sub.recipient_emails or []
            for email_addr in recipients:
                send_email(email_addr, subject, body)

            sub.last_sent_at = now
        db.commit()
    finally:
        db.close()


def check_mandatory_training_reminders():
    from database import SessionLocal
    from models.user import User
    from models.training_plan import TrainingPlanAssignment, TrainingPlan, TrainingPlanItem
    from models.submission import Submission
    from services.email_service import send_email
    from datetime import date, timedelta

    db = SessionLocal()
    try:
        today = date.today()
        due_soon = today + timedelta(days=7)
        assignments = db.query(TrainingPlanAssignment).join(TrainingPlan).filter(
            TrainingPlan.is_active == True,
            TrainingPlanAssignment.due_date <= due_soon,
            TrainingPlanAssignment.due_date >= today,
        ).all()
        for a in assignments:
            user = db.query(User).filter(User.id == a.user_id).first()
            if not user or not user.email:
                continue
            items = db.query(TrainingPlanItem).filter(TrainingPlanItem.plan_id == a.plan_id).all()
            incomplete = 0
            for item in items:
                sub = db.query(Submission).filter(
                    Submission.user_id == user.id,
                    Submission.passed == True,
                    Submission.status == "released",
                ).first()
                if not sub:
                    incomplete += 1
            if incomplete > 0:
                plan = db.query(TrainingPlan).filter(TrainingPlan.id == a.plan_id).first()
                subject = f"Reminder: Mandatory training due in {incomplete} course(s)"
                body = f"<p>Hi {user.full_name},</p><p>You have {incomplete} mandatory training course(s) due by {a.due_date} as part of plan '{plan.title}'.</p><p>Please log in to complete them.</p>"
                send_email(user.email, subject, body)
    finally:
        db.close()
