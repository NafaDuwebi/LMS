import os
import csv
import io
from fastapi import UploadFile
from sqlalchemy.orm import Session
from models.user import User
from models.cohort import Cohort, Enrolment
from services.auth_service import hash_password, create_setup_token, safe_username
import secrets
import string


def generate_temp_password(length=12):
    chars = string.ascii_letters + string.digits + "!@#$%"
    return "".join(secrets.choice(chars) for _ in range(length))


def bulk_enrol_from_csv(db: Session, cohort_id: int, file: UploadFile, base_url: str):
    from services.email_service import send_welcome_email
    import chardet

    content = file.file.read()
    encoding = chardet.detect(content)["encoding"] or "utf-8"
    decoded = content.decode(encoding)
    reader = csv.DictReader(io.StringIO(decoded))

    cohort = db.query(Cohort).filter(Cohort.id == cohort_id).first()
    if not cohort:
        return []

    results = []
    for row in reader:
        full_name = row.get("full_name", "").strip()
        email = row.get("email", "").strip().lower()
        organisation = row.get("organisation", "").strip()

        if not full_name or not email:
            continue

        existing = db.query(User).filter(User.email == email).first()
        if existing:
            en = db.query(Enrolment).filter(
                Enrolment.user_id == existing.id,
                Enrolment.cohort_id == cohort_id,
            ).first()
            if not en:
                en = Enrolment(user_id=existing.id, cohort_id=cohort_id, enrolment_source="bulk_import")
                db.add(en)
            results.append({"email": email, "status": "enrolled"})
            continue

        user = User(
            username=safe_username(db, email),
            email=email,
            password_hash=hash_password(secrets.token_urlsafe(16)),
            full_name=full_name,
            organisation=organisation,
            role="learner",
        )
        db.add(user)
        db.flush()

        en = Enrolment(user_id=user.id, cohort_id=cohort_id, enrolment_source="bulk_import")
        db.add(en)
        token = create_setup_token(db, user.id)
        results.append({"email": email, "status": "created"})
        send_welcome_email(email, token, base_url, user.id, db)

    db.commit()
    return results
