import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from config import SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD, FROM_EMAIL


def send_email(to_email: str, subject: str, body_html: str, user_id: int = None, db=None):
    if not SMTP_USER or not SMTP_PASSWORD:
        return
    msg = MIMEMultipart("alternative")
    msg["From"] = FROM_EMAIL
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.attach(MIMEText(body_html, "html"))
    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.send_message(msg)
    except Exception as e:
        import logging
        logging.error('Email send failed: %s', e)
    if user_id and db:
        from models.message import Message
        from datetime import datetime
        msg_record = Message(user_id=user_id, subject=subject, body=body_html, sent_at=datetime.utcnow())
        db.add(msg_record)
        db.commit()


def send_welcome_email(email: str, token: str, base_url: str, user_id: int = None, db=None):
    subject = "Set your PLP LMS password"
    body = f'<p>Set your password: <a href="{base_url}/auth/set-password?token={token}">{base_url}/auth/set-password?token={token}</a></p>'
    send_email(email, subject, body, user_id, db)


def send_certificate_email(email: str, cert_num: str, base_url: str, user_id: int = None, db=None):
    subject = "Your PLP Certificate has been issued"
    body = f"""
    <h2>Certificate Issued</h2>
    <p>Your certificate <strong>{cert_num}</strong> has been issued.</p>
    <p>You can download it from your learner profile.</p>
    <p>Verify: <a href="{base_url}/verify/{cert_num}">{base_url}/verify/{cert_num}</a></p>
    """
    send_email(email, subject, body, user_id, db)


def send_reminder_email(email: str, subject: str, message: str, user_id: int = None, db=None):
    body = f"""
    <h2>PLP LMS Reminder</h2>
    <p>{message}</p>
    """
    send_email(email, subject, body, user_id, db)
