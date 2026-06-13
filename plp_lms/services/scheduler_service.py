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
