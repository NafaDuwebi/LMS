import os, uuid
from datetime import datetime, timedelta
from config import CERTIFICATE_DIR, BASE_URL, ORG_NAME


def generate_certificate_number(db) -> str:
    year = datetime.utcnow().year
    return f"PLP-{year}-{uuid.uuid4().hex[:8].upper()}"


def generate_certificate_pdf(db, user, course, enrolment):
    from models.certificate import Certificate
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import mm
    from reportlab.pdfgen import canvas
    from reportlab.lib.colors import HexColor

    cert_num = generate_certificate_number(db)
    filename = f"cert_{cert_num}.pdf"
    filepath = os.path.join(CERTIFICATE_DIR, filename)

    c = canvas.Canvas(filepath, pagesize=A4)
    width, height = A4

    c.setStrokeColor(HexColor("#1A2B4A"))
    c.setLineWidth(3)
    c.rect(20, 20, width - 40, height - 40)
    c.setLineWidth(1)
    c.rect(25, 25, width - 50, height - 50)

    c.setFillColor(HexColor("#1A2B4A"))
    c.setFont("Helvetica-Bold", 24)
    c.drawCentredString(width / 2, height - 100, ORG_NAME)

    c.setFont("Helvetica", 14)
    c.setFillColor(HexColor("#555555"))
    c.drawCentredString(width / 2, height - 130, "Certificate of Completion")

    c.setStrokeColor(HexColor("#C9912B"))
    c.setLineWidth(1)
    c.line(200, height - 145, width - 200, height - 145)

    c.setFillColor(HexColor("#333333"))
    c.setFont("Helvetica", 12)
    c.drawCentredString(width / 2, height - 175, "This is to certify that")

    c.setFillColor(HexColor("#1A2B4A"))
    c.setFont("Helvetica-Bold", 20)
    c.drawCentredString(width / 2, height - 210, user.full_name)

    c.setFillColor(HexColor("#333333"))
    c.setFont("Helvetica", 12)
    c.drawCentredString(width / 2, height - 240, f"has successfully completed the course")

    c.setFillColor(HexColor("#1A2B4A"))
    c.setFont("Helvetica-Bold", 16)
    c.drawCentredString(width / 2, height - 270, course.title)

    if course.awarding_body:
        c.setFillColor(HexColor("#555555"))
        c.setFont("Helvetica", 11)
        c.drawCentredString(width / 2, height - 295, f"Awarding Body: {course.awarding_body}")

    c.setFont("Helvetica", 11)
    c.drawCentredString(width / 2, height - 320, f"Certificate Number: {cert_num}")
    c.drawCentredString(width / 2, height - 340, f"Issue Date: {datetime.utcnow().strftime('%d %B %Y')}")

    if course.cert_validity_years and course.cert_validity_years > 0:
        expiry = datetime.utcnow() + timedelta(days=365 * course.cert_validity_years)
        c.drawCentredString(width / 2, height - 360, f"Expiry Date: {expiry.strftime('%d %B %Y')}")

    c.setFont("Helvetica-Oblique", 9)
    c.setFillColor(HexColor("#999999"))
    c.drawCentredString(width / 2, 60, "This certificate is the property of PL Projects Ltd. Verify at " + BASE_URL + "/verify/" + cert_num)

    c.showPage()
    c.save()

    expiry_date = None
    if course.cert_validity_years and course.cert_validity_years > 0:
        expiry_date = datetime.utcnow() + timedelta(days=365 * course.cert_validity_years)

    cert = Certificate(
        user_id=user.id,
        course_id=course.id,
        enrolment_id=enrolment.id if enrolment else None,
        certificate_number=cert_num,
        pdf_path=filepath,
        expiry_date=expiry_date,
    )
    db.add(cert)
    db.commit()
    db.refresh(cert)
    return cert


def revoke_certificate(db, cert_id: int, reason: str):
    from models.certificate import Certificate
    cert = db.query(Certificate).filter(Certificate.id == cert_id).first()
    if cert:
        cert.revoked = True
        cert.revoked_reason = reason
        cert.revoked_at = datetime.utcnow()
        db.commit()
    return cert
