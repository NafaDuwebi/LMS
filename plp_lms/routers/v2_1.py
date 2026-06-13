import magic
from fastapi import APIRouter, Request, Depends, Form, UploadFile, File, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from database import get_db
from models.user import User
from models.course import Course
from models.cohort import Cohort, Enrolment
from models.learning_path import LearningPath, LearningPathCourse, LearningPathEnrolment
from models.skill import Skill, SkillClaim
from models.document import EnrolmentDocumentRequirement, EnrolmentDocumentSubmission
from models.message import Message
from models.rpl import RplClaim
from models.report_subscription import ReportSubscription
from models.retention import RetentionLog
from models.audit import AuditLog
from services.auth_service import get_current_user, require_role
from services.notification_service import create_notification
from services.email_service import send_email
from config import BASE_URL, DATA_RETENTION_YEARS, MAX_UPLOAD_MB
from datetime import datetime, date, timedelta
import os, uuid, json
from services.flash import flash

VALID_SKILL_CLAIM_STATUSES = frozenset({"approved", "rejected"})
VALID_DOCUMENT_STATUSES = frozenset({"approved", "rejected"})
VALID_RPL_STATUSES = frozenset({"approved", "rejected"})

router = APIRouter(tags=["v2.1"])
from template_utils import templates

from config import UPLOAD_DIR, CERTIFICATE_DIR

ALLOWED_MIME = {"pdf":"application/pdf","docx":"application/vnd.openxmlformats-officedocument.wordprocessingml.document","pptx":"application/vnd.openxmlformats-officedocument.presentationml.presentation","mp4":"video/mp4","png":"image/png","jpg":"image/jpeg"}


# ─── Improvement 1: Learning Paths ─────────────────────────────────

@router.get("/learning-paths", response_class=HTMLResponse)
def list_paths(request: Request, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if user.role == "learner":
        enrolments = db.query(LearningPathEnrolment).filter(LearningPathEnrolment.user_id == user.id).all()
        path_ids = [e.path_id for e in enrolments]
        paths = db.query(LearningPath).filter(LearningPath.id.in_(path_ids), LearningPath.is_published == True).all() if path_ids else []
    else:
        paths = db.query(LearningPath).order_by(LearningPath.created_at.desc()).all()
    return templates.TemplateResponse("v2/learning_paths.html", {"request": request, "user": user, "paths": paths})


@router.get("/learning-paths/create", response_class=HTMLResponse)
def create_path_page(request: Request, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    courses = db.query(Course).filter(Course.is_published == True).all()
    return templates.TemplateResponse("v2/learning_path_form.html", {"request": request, "user": user, "path": None, "courses": courses})


@router.post("/learning-paths/create")
def create_path(
    request: Request,
    title: str = Form(...),
    description: str = Form(None),
    csrf_token: str = Form(default=""),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    path = LearningPath(title=title, description=description, created_by=user.id)
    db.add(path)
    db.commit()
    flash(request, "Learning path created", "success")
    return RedirectResponse(url=f"/learning-paths/{path.id}", status_code=302)


@router.get("/learning-paths/{path_id}", response_class=HTMLResponse)
def view_path(request: Request, path_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    path = db.query(LearningPath).filter(LearningPath.id == path_id).first()
    if not path:
        raise HTTPException(status_code=404)
    courses = db.query(LearningPathCourse).filter(LearningPathCourse.path_id == path_id).order_by(LearningPathCourse.order_index).all()
    for i, lpc in enumerate(courses):
        if lpc.unlock_on_previous and i > 0:
            prev = courses[i - 1]
            from models.cohort import Cohort, Enrolment
            prev_enrolment = db.query(Enrolment).join(Cohort).filter(
                Enrolment.user_id == user.id, Cohort.course_id == prev.course_id,
                Enrolment.status == "completed"
            ).first()
            lpc.is_unlocked = prev_enrolment is not None
        else:
            lpc.is_unlocked = True
    enrolment = db.query(LearningPathEnrolment).filter(
        LearningPathEnrolment.path_id == path_id, LearningPathEnrolment.user_id == user.id
    ).first() if user.role == "learner" else None
    all_courses = db.query(Course).order_by(Course.title).all()
    return templates.TemplateResponse("v2/learning_path_view.html", {
        "request": request, "user": user, "path": path, "path_courses": courses, "enrolment": enrolment,
        "courses": all_courses,
    })


@router.post("/learning-paths/{path_id}/add-course")
def add_course_to_path(
    path_id: int,
    request: Request,
    course_id: int = Form(...),
    csrf_token: str = Form(default=""),
    db: Session = Depends(get_db),
    user: User = Depends(require_role("superadmin", "trainer")),
):
    count = db.query(LearningPathCourse).filter(LearningPathCourse.path_id == path_id).count()
    lpc = LearningPathCourse(path_id=path_id, course_id=course_id, order_index=count + 1)
    db.add(lpc)
    db.commit()
    flash(request, "Course added to learning path", "success")
    return RedirectResponse(url=f"/learning-paths/{path_id}", status_code=302)


@router.post("/learning-paths/{path_id}/enrol")
def enrol_in_path(
    path_id: int,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    existing = db.query(LearningPathEnrolment).filter(
        LearningPathEnrolment.path_id == path_id, LearningPathEnrolment.user_id == user.id
    ).first()
    if existing:
        return RedirectResponse(url=f"/learning-paths/{path_id}", status_code=302)

    enr = LearningPathEnrolment(user_id=user.id, path_id=path_id, status="enrolled")
    db.add(enr)
    db.flush()

    # Auto-enrol in first course
    first = db.query(LearningPathCourse).filter(
        LearningPathCourse.path_id == path_id
    ).order_by(LearningPathCourse.order_index).first()
    if first:
        cohort = db.query(Cohort).filter(
            Cohort.course_id == first.course_id, Cohort.is_active == True
        ).first()
        if cohort:
            enrol = db.query(Enrolment).filter(
                Enrolment.user_id == user.id, Enrolment.cohort_id == cohort.id
            ).first()
            if not enrol:
                enrol = Enrolment(user_id=user.id, cohort_id=cohort.id, enrolment_source="self")
                db.add(enrol)
                create_notification(db, user.id, "enrolment", f"Auto-enrolled in {cohort.name}")

    db.commit()
    create_notification(db, user.id, "enrolment", f"Enrolled in learning path: {db.query(LearningPath).filter(LearningPath.id == path_id).first().title}")
    flash(request, "Enrolled in learning path", "success")
    return RedirectResponse(url="/learner/courses", status_code=302)


@router.post("/learning-paths/{path_id}/delete-course/{lpc_id}")
def remove_course_from_path(path_id: int, lpc_id: int, request: Request, db: Session = Depends(get_db), user: User = Depends(require_role("superadmin", "trainer"))):
    path = db.query(LearningPath).filter(LearningPath.id == path_id).first()
    if not path:
        flash(request, "Learning path not found", "error")
        return RedirectResponse(url="/learning-paths", status_code=302)
    if path.created_by != user.id and user.role != "superadmin":
        flash(request, "You do not have permission to modify this learning path", "error")
        return RedirectResponse(url=f"/learning-paths/{path_id}", status_code=302)
    db.query(LearningPathCourse).filter(LearningPathCourse.id == lpc_id).delete()
    db.commit()
    flash(request, "Course removed from learning path", "success")
    return RedirectResponse(url=f"/learning-paths/{path_id}", status_code=302)


# ─── Improvement 2: Skills Sign-off ────────────────────────────────

@router.get("/skills/manage/{course_id}", response_class=HTMLResponse)
def manage_skills(request: Request, course_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    course = db.query(Course).filter(Course.id == course_id).first()
    skills = db.query(Skill).filter(Skill.course_id == course_id).all()
    return templates.TemplateResponse("v2/skills_manage.html", {"request": request, "user": user, "course": course, "skills": skills})


@router.post("/skills/create/{course_id}")
def create_skill(
    course_id: int,
    request: Request,
    title: str = Form(...),
    description: str = Form(None),
    how_to_demonstrate: str = Form(None),
    csrf_token: str = Form(default=""),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    skill = Skill(title=title, description=description, how_to_demonstrate=how_to_demonstrate, course_id=course_id, created_by=user.id)
    db.add(skill)
    db.commit()
    flash(request, "Skill created", "success")
    return RedirectResponse(url=f"/skills/manage/{course_id}", status_code=302)


@router.get("/skills/my", response_class=HTMLResponse)
def my_skills(request: Request, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    claims = db.query(SkillClaim).filter(SkillClaim.user_id == user.id).order_by(SkillClaim.submitted_at.desc()).all()
    return templates.TemplateResponse("v2/my_skills.html", {"request": request, "user": user, "claims": claims})


@router.get("/skills/claim/{skill_id}", response_class=HTMLResponse)
def claim_skill_page(request: Request, skill_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    skill = db.query(Skill).filter(Skill.id == skill_id).first()
    if not skill:
        raise HTTPException(status_code=404)
    return templates.TemplateResponse("v2/skill_claim_form.html", {"request": request, "user": user, "skill": skill})


@router.post("/skills/claim/{skill_id}")
async def submit_skill_claim(
    skill_id: int,
    request: Request,
    claim_comment: str = Form(...),
    file: UploadFile = File(None),
    csrf_token: str = Form(default=""),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    skill = db.query(Skill).filter(Skill.id == skill_id).first()
    if not skill:
        raise HTTPException(status_code=404)

    evidence_path = None
    if file and file.filename:
        ext = file.filename.rsplit(".", 1)[-1] if "." in file.filename else ""
        content = await file.read()
        if len(content) > MAX_UPLOAD_MB * 1024 * 1024:
            raise HTTPException(413, f"File exceeds maximum size of {MAX_UPLOAD_MB}MB")
        mime = magic.from_buffer(content, mime=True)
        if ext not in ALLOWED_MIME or mime != ALLOWED_MIME[ext]:
            raise HTTPException(400, "File type not permitted")
        filename = f"skill_{uuid.uuid4()}.{ext}"
        evidence_path = os.path.join(UPLOAD_DIR, filename)
        os.makedirs(UPLOAD_DIR, exist_ok=True)
        with open(evidence_path, "wb") as f:
            f.write(content)

    claim = SkillClaim(
        skill_id=skill_id, user_id=user.id, claim_comment=claim_comment,
        evidence_path=evidence_path, status="pending",
    )
    db.add(claim)
    db.commit()

    # Notify admin if reviewer assigned
    reviewer = db.query(User).filter(
        User.role.in_(["superadmin", "trainer", "external_assessor"])
    ).first()
    if reviewer:
        create_notification(db, reviewer.id, "skill_claim", f"New skill claim from {user.full_name}", action_url="/skills/review")

    create_notification(db, user.id, "skill_claim", f"Skill claim submitted: {skill.title}")
    flash(request, "Skill claim submitted", "success")
    return RedirectResponse(url="/skills/my", status_code=302)


@router.get("/skills/review", response_class=HTMLResponse)
def skills_review_queue(request: Request, user: User = Depends(require_role("superadmin", "trainer", "external_assessor")), db: Session = Depends(get_db)):
    if user.role == "external_assessor":
        claims = db.query(SkillClaim).filter(
            SkillClaim.reviewer_id == user.id, SkillClaim.status == "pending"
        ).order_by(SkillClaim.submitted_at).all()
    else:
        claims = db.query(SkillClaim).filter(SkillClaim.status == "pending").order_by(SkillClaim.submitted_at).all()
    return templates.TemplateResponse("v2/skills_review.html", {"request": request, "user": user, "claims": claims})


@router.post("/skills/review/{claim_id}")
def review_skill_claim(
    claim_id: int,
    request: Request,
    status: str = Form(...),
    reviewer_comment: str = Form(None),
    csrf_token: str = Form(default=""),
    db: Session = Depends(get_db),
    user: User = Depends(require_role("superadmin", "trainer", "external_assessor")),
):
    if status not in VALID_SKILL_CLAIM_STATUSES:
        flash(request, f"Invalid status: {status}", "error")
        return RedirectResponse(url="/skills/review", status_code=302)
    claim = db.query(SkillClaim).filter(SkillClaim.id == claim_id).first()
    if not claim:
        raise HTTPException(status_code=404)
    claim.status = status
    claim.reviewer_comment = reviewer_comment
    claim.reviewed_at = datetime.utcnow()
    claim.reviewer_id = user.id
    db.commit()

    create_notification(db, claim.user_id, "skill_claim", f"Skill claim '{claim.skill.title}' was {status}")
    log = AuditLog(user_id=user.id, action="review_skill_claim", target_type="skill_claim", target_id=claim_id, notes=f"Status: {status}")
    db.add(log)
    db.commit()
    flash(request, "Skill claim reviewed", "success")
    return RedirectResponse(url="/skills/review", status_code=302)


# ─── Improvement 4: Document Requirements ──────────────────────────

@router.get("/documents/requirements/{cohort_id}", response_class=HTMLResponse)
def manage_doc_requirements(request: Request, cohort_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    cohort = db.query(Cohort).filter(Cohort.id == cohort_id).first()
    reqs = db.query(EnrolmentDocumentRequirement).filter(EnrolmentDocumentRequirement.cohort_id == cohort_id).all()
    return templates.TemplateResponse("v2/doc_requirements.html", {"request": request, "user": user, "cohort": cohort, "requirements": reqs})


@router.post("/documents/requirements/{cohort_id}/add")
def add_doc_requirement(
    cohort_id: int,
    request: Request,
    document_label: str = Form(...),
    instructions: str = Form(None),
    is_required: bool = Form(False),
    csrf_token: str = Form(default=""),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    req = EnrolmentDocumentRequirement(cohort_id=cohort_id, document_label=document_label, instructions=instructions, is_required=is_required)
    db.add(req)
    db.commit()
    flash(request, "Document requirement added", "success")
    return RedirectResponse(url=f"/documents/requirements/{cohort_id}", status_code=302)


@router.get("/documents/upload/{cohort_id}", response_class=HTMLResponse)
def upload_docs_page(request: Request, cohort_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    cohort = db.query(Cohort).filter(Cohort.id == cohort_id).first()
    reqs = db.query(EnrolmentDocumentRequirement).filter(EnrolmentDocumentRequirement.cohort_id == cohort_id).all()
    submissions = db.query(EnrolmentDocumentSubmission).filter(
        EnrolmentDocumentSubmission.user_id == user.id,
        EnrolmentDocumentSubmission.requirement_id.in_([r.id for r in reqs]) if reqs else [],
    ).all()
    sub_map = {s.requirement_id: s for s in submissions}
    return templates.TemplateResponse("v2/doc_upload.html", {
        "request": request, "user": user, "cohort": cohort,
        "requirements": reqs, "submissions": sub_map,
    })


@router.post("/documents/upload/{cohort_id}")
async def upload_document(
    cohort_id: int,
    request: Request,
    requirement_id: int = Form(...),
    file: UploadFile = File(...),
    csrf_token: str = Form(default=""),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    ext = file.filename.rsplit(".", 1)[-1] if "." in file.filename else ""
    content = await file.read()
    if len(content) > MAX_UPLOAD_MB * 1024 * 1024:
        raise HTTPException(413, f"File exceeds maximum size of {MAX_UPLOAD_MB}MB")
    mime = magic.from_buffer(content, mime=True)
    if ext not in ALLOWED_MIME or mime != ALLOWED_MIME[ext]:
        raise HTTPException(400, "File type not permitted")
    filename = f"doc_{uuid.uuid4()}.{ext}"
    file_path = os.path.join(UPLOAD_DIR, filename)
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    with open(file_path, "wb") as f:
        f.write(content)

    sub = EnrolmentDocumentSubmission(requirement_id=requirement_id, user_id=user.id, file_path=file_path)
    db.add(sub)
    db.commit()
    flash(request, "Document uploaded", "success")
    return RedirectResponse(url=f"/documents/upload/{cohort_id}", status_code=302)


@router.get("/documents/review", response_class=HTMLResponse)
def doc_review_queue(request: Request, user: User = Depends(require_role("superadmin", "trainer")), db: Session = Depends(get_db)):
    submissions = db.query(EnrolmentDocumentSubmission).filter(
        EnrolmentDocumentSubmission.status == "pending"
    ).order_by(EnrolmentDocumentSubmission.uploaded_at).all()
    return templates.TemplateResponse("v2/doc_review.html", {"request": request, "user": user, "submissions": submissions})


@router.post("/documents/review/{sub_id}")
def review_document(
    sub_id: int,
    request: Request,
    status: str = Form(...),
    rejection_reason: str = Form(None),
    csrf_token: str = Form(default=""),
    db: Session = Depends(get_db),
    user: User = Depends(require_role("superadmin", "trainer")),
):
    if status not in VALID_DOCUMENT_STATUSES:
        flash(request, f"Invalid status: {status}", "error")
        return RedirectResponse(url="/documents/review", status_code=302)
    sub = db.query(EnrolmentDocumentSubmission).filter(EnrolmentDocumentSubmission.id == sub_id).first()
    if not sub:
        raise HTTPException(status_code=404)
    sub.status = status
    sub.reviewed_by = user.id
    sub.reviewed_at = datetime.utcnow()
    sub.rejection_reason = rejection_reason if status == "rejected" else None
    db.commit()
    log = AuditLog(user_id=user.id, action="review_document", target_type="document_submission", target_id=sub_id, notes=f"Status: {status}")
    db.add(log)
    db.commit()
    flash(request, "Document submission reviewed", "success")
    return RedirectResponse(url="/documents/review", status_code=302)


# ─── Improvement 5: Message Centre ─────────────────────────────────

@router.get("/messages", response_class=HTMLResponse)
def list_messages(request: Request, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    msgs = db.query(Message).filter(Message.user_id == user.id).order_by(Message.sent_at.desc()).all()
    return templates.TemplateResponse("v2/messages.html", {"request": request, "user": user, "messages": msgs})


@router.get("/messages/{msg_id}", response_class=HTMLResponse)
def view_message(msg_id: int, request: Request, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    msg = db.query(Message).filter(Message.id == msg_id, Message.user_id == user.id).first()
    if not msg:
        raise HTTPException(status_code=404)
    if not msg.is_read:
        msg.is_read = True
        msg.read_at = datetime.utcnow()
        db.commit()
    return templates.TemplateResponse("v2/message_view.html", {"request": request, "user": user, "message": msg})


@router.post("/messages/{msg_id}/delete")
def delete_message(msg_id: int, request: Request, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    db.query(Message).filter(Message.id == msg_id, Message.user_id == user.id).delete()
    db.commit()
    flash(request, "Message deleted", "success")
    return RedirectResponse(url="/messages", status_code=302)


# ─── Improvement 6: RPL Claims ─────────────────────────────────────

@router.get("/rpl/claim/{course_id}", response_class=HTMLResponse)
def rpl_claim_page(request: Request, course_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    course = db.query(Course).filter(Course.id == course_id).first()
    return templates.TemplateResponse("v2/rpl_form.html", {"request": request, "user": user, "course": course})


@router.post("/rpl/claim/{course_id}")
async def submit_rpl(
    course_id: int,
    request: Request,
    prior_title: str = Form(...),
    prior_provider: str = Form(None),
    completion_date: str = Form(None),
    statement: str = Form(None),
    file: UploadFile = File(None),
    csrf_token: str = Form(default=""),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    evidence_path = None
    if file and file.filename:
        ext = file.filename.rsplit(".", 1)[-1] if "." in file.filename else ""
        content = await file.read()
        if len(content) > MAX_UPLOAD_MB * 1024 * 1024:
            raise HTTPException(413, f"File exceeds maximum size of {MAX_UPLOAD_MB}MB")
        mime = magic.from_buffer(content, mime=True)
        if ext not in ALLOWED_MIME or mime != ALLOWED_MIME[ext]:
            raise HTTPException(400, "File type not permitted")
        filename = f"rpl_{uuid.uuid4()}.{ext}"
        evidence_path = os.path.join(UPLOAD_DIR, filename)
        os.makedirs(UPLOAD_DIR, exist_ok=True)
        with open(evidence_path, "wb") as f:
            f.write(content)

    claim = RplClaim(
        user_id=user.id, course_id=course_id, prior_title=prior_title,
        prior_provider=prior_provider, statement=statement,
        completion_date=date.fromisoformat(completion_date) if completion_date else None,
        evidence_path=evidence_path,
    )
    db.add(claim)
    db.commit()

    create_notification(db, user.id, "rpl", f"RPL claim submitted for {prior_title}")
    flash(request, "RPL claim submitted", "success")
    return RedirectResponse(url="/learner/training-record", status_code=302)


@router.get("/rpl/review", response_class=HTMLResponse)
def rpl_review_queue(request: Request, user: User = Depends(require_role("superadmin", "trainer")), db: Session = Depends(get_db)):
    claims = db.query(RplClaim).filter(RplClaim.status == "pending").order_by(RplClaim.submitted_at).all()
    return templates.TemplateResponse("v2/rpl_review.html", {"request": request, "user": user, "claims": claims})


@router.post("/rpl/review/{claim_id}")
def review_rpl(
    claim_id: int,
    request: Request,
    status: str = Form(...),
    reviewer_notes: str = Form(None),
    csrf_token: str = Form(default=""),
    db: Session = Depends(get_db),
    user: User = Depends(require_role("superadmin", "trainer")),
):
    if status not in VALID_RPL_STATUSES:
        flash(request, f"Invalid status: {status}", "error")
        return RedirectResponse(url="/rpl/review", status_code=302)
    claim = db.query(RplClaim).filter(RplClaim.id == claim_id).first()
    if not claim:
        raise HTTPException(status_code=404)
    claim.status = status
    claim.reviewer_notes = reviewer_notes
    claim.reviewed_by = user.id
    claim.reviewed_at = datetime.utcnow()
    db.commit()

    if status == "approved":
        # Mark course as completed
        cohort = db.query(Cohort).filter(
            Cohort.course_id == claim.course_id, Cohort.is_active == True
        ).first()
        if cohort:
            enrol = db.query(Enrolment).filter(
                Enrolment.user_id == claim.user_id, Enrolment.cohort_id == cohort.id
            ).first()
            if not enrol:
                enrol = Enrolment(user_id=claim.user_id, cohort_id=cohort.id, enrolment_source="rpl")
                db.add(enrol)
                db.flush()
            enrol.status = "completed"
            enrol.completion_date = datetime.utcnow()
            enrol.retention_review_date = (datetime.utcnow() + timedelta(days=365*DATA_RETENTION_YEARS)).date()

    create_notification(db, claim.user_id, "rpl", f"RPL claim was {status}")
    log = AuditLog(user_id=user.id, action="review_rpl", target_type="rpl_claim", target_id=claim_id, notes=f"Status: {status}")
    db.add(log)
    db.commit()
    flash(request, "RPL claim reviewed", "success")
    return RedirectResponse(url="/rpl/review", status_code=302)


# ─── Improvement 7: GDPR Retention ─────────────────────────────────

@router.get("/admin/retention", response_class=HTMLResponse)
def retention_review(request: Request, user: User = Depends(require_role("superadmin")), db: Session = Depends(get_db)):
    flagged = db.query(Enrolment).filter(Enrolment.retention_status == "flagged").order_by(Enrolment.retention_review_date).all()
    logs = db.query(RetentionLog).order_by(RetentionLog.actioned_at.desc()).limit(50).all()
    return templates.TemplateResponse("v2/retention_review.html", {"request": request, "user": user, "flagged": flagged, "logs": logs})


@router.post("/admin/retention/anonymise/{enrolment_id}")
def anonymise_record(enrolment_id: int, request: Request, db: Session = Depends(get_db), user: User = Depends(require_role("superadmin"))):
    enrol = db.query(Enrolment).filter(Enrolment.id == enrolment_id).first()
    if not enrol:
        raise HTTPException(status_code=404)
    learner = enrol.user
    if learner:
        learner.full_name = "[Anonymised]"
        learner.email = f"anon_{learner.id}@anonymised.plp"
        learner.phone = None
        learner.organisation = None
        learner.username = f"anon_{learner.id}"
        learner.job_title = None
        learner.is_active = False
        learner.token_version += 1
        from models.audit import AuditLog
        db.query(AuditLog).filter(AuditLog.user_id == learner.id).update({"notes": "[anonymised]"})
        from models.certificate import Certificate
        db.query(Certificate).filter(Certificate.user_id == learner.id).update({"revoked": True, "revoked_reason": "GDPR anonymisation"})
        from models.training_record import TrainingRecord
        db.query(TrainingRecord).filter(TrainingRecord.user_id == learner.id).delete()
        from models.rpl import RplClaim
        db.query(RplClaim).filter(RplClaim.user_id == learner.id).update({"prior_title": "[anonymised]", "statement": None, "evidence_path": None})
    enrol.retention_status = "anonymised"
    db.commit()
    log = RetentionLog(user_id=learner.id if learner else None, action="anonymised", actioned_by=user.id, notes=f"Enrolment {enrolment_id} anonymised")
    db.add(log)
    db.commit()
    flash(request, "Record anonymised", "success")
    return RedirectResponse(url="/admin/retention", status_code=302)


@router.post("/admin/retention/extend/{enrolment_id}")
def extend_retention(enrolment_id: int, request: Request, years: int = Form(1), csrf_token: str = Form(default=""), db: Session = Depends(get_db), user: User = Depends(require_role("superadmin"))):
    enrol = db.query(Enrolment).filter(Enrolment.id == enrolment_id).first()
    if not enrol:
        raise HTTPException(status_code=404)
    if enrol.retention_review_date:
        enrol.retention_review_date = enrol.retention_review_date + timedelta(days=365 * years)
    enrol.retention_status = "active"
    db.commit()
    log = RetentionLog(user_id=enrol.user_id, action="extended", actioned_by=user.id, notes=f"Retention extended by {years} year(s)")
    db.add(log)
    db.commit()
    flash(request, "Retention extended", "success")
    return RedirectResponse(url="/admin/retention", status_code=302)


# ─── Improvement 8: Report Subscriptions ───────────────────────────

@router.get("/reports/subscriptions", response_class=HTMLResponse)
def list_subscriptions(request: Request, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    subs = db.query(ReportSubscription).order_by(ReportSubscription.created_at.desc()).all()
    return templates.TemplateResponse("v2/report_subscriptions.html", {"request": request, "user": user, "subscriptions": subs})


@router.post("/reports/subscriptions/create")
def create_subscription(
    request: Request,
    report_id: int = Form(...),
    recipient_emails: str = Form(...),
    frequency: str = Form("weekly"),
    day_of_week: int = Form(None),
    day_of_month: int = Form(None),
    send_time: str = Form("08:00"),
    csrf_token: str = Form(default=""),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    emails = [e.strip() for e in recipient_emails.split(",") if e.strip()]
    from datetime import time
    sub = ReportSubscription(
        report_id=report_id, created_by=user.id,
        recipient_emails=emails, frequency=frequency,
        day_of_week=day_of_week, day_of_month=day_of_month,
        send_time=time.fromisoformat(send_time) if send_time else None,
    )
    db.add(sub)
    db.commit()
    flash(request, "Report subscription created", "success")
    return RedirectResponse(url="/reports/subscriptions", status_code=302)


@router.post("/reports/subscriptions/{sub_id}/toggle")
def toggle_subscription(sub_id: int, request: Request, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    sub = db.query(ReportSubscription).filter(ReportSubscription.id == sub_id).first()
    if sub:
        sub.is_active = not sub.is_active
        db.commit()
    flash(request, "Report subscription toggled", "success")
    return RedirectResponse(url="/reports/subscriptions", status_code=302)


@router.post("/reports/subscriptions/{sub_id}/delete")
def delete_subscription(sub_id: int, request: Request, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    db.query(ReportSubscription).filter(ReportSubscription.id == sub_id).delete()
    db.commit()
    flash(request, "Report subscription deleted", "success")
    return RedirectResponse(url="/reports/subscriptions", status_code=302)
