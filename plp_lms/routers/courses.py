import magic
from fastapi import APIRouter, Request, Depends, Form, UploadFile, File, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, FileResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from database import get_db
from models.user import User
from models.course import Course, LearningOutcome, Module, Material
from models.assessment import Assessment
from models.enrolment_request import EnrolmentRequest
from models.material_view import MaterialView
from models.cohort import Cohort, Enrolment
from services.auth_service import get_current_user, require_role
from services.notification_service import create_notification
from services.audit_service import log_action
from services.flash import flash
import os
import uuid
from config import UPLOAD_DIR, MAX_UPLOAD_MB

router = APIRouter(prefix="/courses", tags=["courses"])
from template_utils import templates

ALLOWED_MIME = {"pdf":"application/pdf","docx":"application/vnd.openxmlformats-officedocument.wordprocessingml.document","pptx":"application/vnd.openxmlformats-officedocument.presentationml.presentation","mp4":"video/mp4","png":"image/png","jpg":"image/jpeg"}


def _can_access_material(db: Session, user: User, material: Material) -> bool:
    """Return True if the user is allowed to view/download this material.
    Admins and trainers always have access.
    Learners must be actively enrolled in a cohort for the material's course.
    """
    if user.role in ("superadmin", "trainer"):
        return True
    course_id = material.module.course_id
    enrolled = (
        db.query(Enrolment)
        .join(Cohort, Cohort.id == Enrolment.cohort_id)
        .filter(
            Enrolment.user_id == user.id,
            Cohort.course_id == course_id,
            Enrolment.status.in_(["enrolled", "completed"]),
        )
        .first()
    )
    return enrolled is not None


def course_context(request, user, db):
    return {"request": request, "user": user}


@router.get("", response_class=HTMLResponse, name="courses.index")
def list_courses(request: Request, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if user.role == "superadmin":
        courses = db.query(Course).order_by(Course.created_at.desc()).all()
    elif user.role == "trainer":
        created = db.query(Course).filter(Course.created_by == user.id).all()
        assigned = db.query(Course).join(Cohort).filter(Cohort.trainer_id == user.id).all()
        seen = set()
        courses = []
        for c in created + assigned:
            if c.id not in seen:
                seen.add(c.id)
                courses.append(c)
    else:
        courses = db.query(Course).filter(Course.is_published == True).all()
    return templates.TemplateResponse("shared/courses.html", {**course_context(request, user, db), "courses": courses})


@router.get("/catalogue", response_class=HTMLResponse, name="courses.catalogue")
def course_catalogue(request: Request, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    courses = db.query(Course).filter(Course.is_published == True).order_by(Course.title).all()
    return templates.TemplateResponse("catalogue.html", {
        "request": request, "user": user, "courses": courses,
        "success": request.query_params.get("success"), "error": request.query_params.get("error"),
    })


@router.post("/{course_id}/request-enrolment", name="courses.request_enrolment")
def request_enrolment(
    request: Request, course_id: int, csrf_token: str = Form(default=""),
    db: Session = Depends(get_db), user: User = Depends(get_current_user),
):
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        flash(request, "Course not found", "error")
        return RedirectResponse(url="/courses/catalogue", status_code=302)
    existing = db.query(EnrolmentRequest).filter(
        EnrolmentRequest.user_id == user.id,
        EnrolmentRequest.course_id == course_id,
        EnrolmentRequest.status == "pending",
    ).first()
    if existing:
        flash(request, "You already have a pending request for this course", "error")
        return RedirectResponse(url="/courses/catalogue", status_code=302)
    req = EnrolmentRequest(user_id=user.id, course_id=course_id)
    db.add(req)
    db.commit()
    admins = db.query(User).filter(User.role == "superadmin", User.is_active == True).all()
    for a in admins:
        create_notification(db, a.id, "enrolment_request", f"New enrolment request from {user.full_name}", f"{user.full_name} requested enrolment in {course.title}.", action_url="/admin/enrolment-requests")
    flash(request, "Enrolment request submitted", "success")
    return RedirectResponse(url="/courses/catalogue", status_code=302)


@router.get("/create", response_class=HTMLResponse, name="courses.create")
def create_course_page(request: Request, user: User = Depends(get_current_user)):
    return templates.TemplateResponse("shared/course_form.html", {**course_context(request, user, db=None), "course": None})


@router.post("/create", name="courses.create_submit")
def create_course(
    request: Request,
    course_code: str = Form(...),
    title: str = Form(...),
    awarding_body: str = Form(None),
    level: str = Form(None),
    description: str = Form(None),
    pass_mark: float = Form(55.0),
    assessment_type: str = Form("mixed"),
    delivery_mode: str = Form("blended"),
    duration_hours: int = Form(None),
    cert_validity_years: int = Form(0),
    credit_value: int = Form(None),
    csrf_token: str = Form(default=""),
    db: Session = Depends(get_db),
    user: User = Depends(require_role("superadmin", "trainer")),
):
    course = Course(
        course_code=course_code,
        title=title,
        awarding_body=awarding_body,
        level=level,
        description=description,
        pass_mark=pass_mark,
        assessment_type=assessment_type,
        delivery_mode=delivery_mode,
        duration_hours=duration_hours,
        cert_validity_years=cert_validity_years,
        credit_value=credit_value,
        created_by=user.id,
        is_published=False,
        status="draft",
    )
    db.add(course)
    db.commit()
    log_action(db, user.id, "create_course", "course", course.id, f"Created course {course_code}: {title}")
    flash(request, "Course created", "success")
    return RedirectResponse(url=f"/courses/{course.id}", status_code=302)


@router.post("/{course_id}/submit-review", name="courses.submit_review")
def submit_for_review(course_id: int, request: Request, csrf_token: str = Form(default=""), db: Session = Depends(get_db), user: User = Depends(require_role("trainer", "superadmin"))):
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404)
    course.status = "in_review"
    db.commit()
    log_action(db, user.id, "submit_review", "course", course.id, f"Course {course.course_code} submitted for review")
    flash(request, "Course submitted for review", "success")
    return RedirectResponse(url=f"/courses/{course.id}", status_code=302)


@router.post("/{course_id}/publish", name="courses.publish")
def publish_course(course_id: int, request: Request, csrf_token: str = Form(default=""), db: Session = Depends(get_db), user: User = Depends(require_role("superadmin"))):
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404)
    course.status = "published"
    course.is_published = True
    db.commit()
    log_action(db, user.id, "publish_course", "course", course.id, f"Course {course.course_code} published")
    flash(request, "Course published", "success")
    return RedirectResponse(url=f"/courses/{course.id}", status_code=302)


@router.post("/{course_id}/unpublish", name="courses.unpublish")
def unpublish_course(course_id: int, request: Request, csrf_token: str = Form(default=""), db: Session = Depends(get_db), user: User = Depends(require_role("superadmin"))):
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404)
    course.status = "draft"
    course.is_published = False
    db.commit()
    log_action(db, user.id, "unpublish_course", "course", course.id, f"Course {course.course_code} unpublished")
    flash(request, "Course unpublished", "success")
    return RedirectResponse(url=f"/courses/{course.id}", status_code=302)


@router.get("/{course_id}", response_class=HTMLResponse, name="courses.view")
def view_course(request: Request, course_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    from models.assessment import Assessment
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404)
    modules = db.query(Module).filter(Module.course_id == course_id).order_by(Module.order_index).all()
    outcomes = db.query(LearningOutcome).filter(LearningOutcome.course_id == course_id).order_by(LearningOutcome.order_index).all()
    assessments = db.query(Assessment).filter(Assessment.course_id == course_id).order_by(Assessment.created_at.desc()).all()
    return templates.TemplateResponse("shared/course_view.html", {
        **course_context(request, user, db), "course": course, "modules": modules, "outcomes": outcomes,
        "assessments": assessments,
    })


@router.get("/{course_id}/edit", response_class=HTMLResponse, name="courses.edit")
def edit_course_page(request: Request, course_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404)
    return templates.TemplateResponse("shared/course_form.html", {**course_context(request, user, db), "course": course})


@router.post("/{course_id}/edit", name="courses.edit_submit")
def edit_course(
    request: Request,
    course_id: int,
    course_code: str = Form(...),
    title: str = Form(...),
    awarding_body: str = Form(None),
    level: str = Form(None),
    description: str = Form(None),
    pass_mark: float = Form(55.0),
    assessment_type: str = Form("mixed"),
    delivery_mode: str = Form("blended"),
    duration_hours: int = Form(None),
    cert_validity_years: int = Form(0),
    credit_value: int = Form(None),
    is_published: bool = Form(False),
    csrf_token: str = Form(default=""),
    db: Session = Depends(get_db),
    user: User = Depends(require_role("superadmin", "trainer")),
):
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404)
    course.course_code = course_code
    course.title = title
    course.awarding_body = awarding_body
    course.level = level
    course.description = description
    course.pass_mark = pass_mark
    course.assessment_type = assessment_type
    course.delivery_mode = delivery_mode
    course.duration_hours = duration_hours
    course.cert_validity_years = cert_validity_years
    course.credit_value = credit_value
    course.is_published = is_published
    db.commit()
    log_action(db, user.id, "edit_course", "course", course.id, f"Edited course {course_code}: {title}")
    flash(request, "Course updated", "success")
    return RedirectResponse(url=f"/courses/{course.id}", status_code=302)


@router.post("/{course_id}/delete", name="courses.delete")
def delete_course(request: Request, course_id: int, db: Session = Depends(get_db), user: User = Depends(require_role("superadmin"))):
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        flash(request, "Course not found", "error")
        return RedirectResponse(url="/courses", status_code=302)
    log_action(db, user.id, "delete_course", "course", course_id, f"Deleted course {course.course_code}: {course.title}")
    db.delete(course)
    db.commit()
    flash(request, "Course deleted", "success")
    return RedirectResponse(url="/courses", status_code=302)


@router.post("/{course_id}/outcomes/add", name="courses.add_outcome")
def add_outcome(
    course_id: int,
    request: Request,
    outcome_text: str = Form(...),
    syllabus_area: str = Form(None),
    csrf_token: str = Form(default=""),
    db: Session = Depends(get_db),
    user: User = Depends(require_role("superadmin", "trainer")),
):
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404)
    count = db.query(LearningOutcome).filter(LearningOutcome.course_id == course_id).count()
    outcome = LearningOutcome(course_id=course_id, outcome_text=outcome_text, syllabus_area=syllabus_area, order_index=count + 1)
    db.add(outcome)
    db.commit()
    flash(request, "Learning outcome added", "success")
    return RedirectResponse(url=f"/courses/{course_id}", status_code=302)


@router.post("/outcomes/{outcome_id}/delete", name="courses.delete_outcome")
def delete_outcome(request: Request, outcome_id: int, db: Session = Depends(get_db), user: User = Depends(require_role("superadmin", "trainer"))):
    outcome = db.query(LearningOutcome).filter(LearningOutcome.id == outcome_id).first()
    if not outcome:
        flash(request, "Learning outcome not found", "error")
        return RedirectResponse(url="/courses", status_code=302)
    course_id = outcome.course_id
    db.delete(outcome)
    db.commit()
    flash(request, "Learning outcome deleted", "success")
    return RedirectResponse(url=f"/courses/{course_id}", status_code=302)


# ---- Module Management ----

@router.get("/{course_id}/modules/create", response_class=HTMLResponse, name="modules.create")
def create_module_page(request: Request, course_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    course = db.query(Course).filter(Course.id == course_id).first()
    return templates.TemplateResponse("shared/module_form.html", {**course_context(request, user, db), "course": course, "module": None})


@router.post("/{course_id}/modules/create", name="modules.create_submit")
def create_module(
    request: Request,
    course_id: int,
    title: str = Form(...),
    description: str = Form(None),
    delivery_mode: str = Form("online"),
    csrf_token: str = Form(default=""),
    db: Session = Depends(get_db),
    user: User = Depends(require_role("superadmin", "trainer")),
):
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404)
    count = db.query(Module).filter(Module.course_id == course_id).count()
    module = Module(course_id=course_id, title=title, description=description, delivery_mode=delivery_mode, order_index=count + 1)
    db.add(module)
    db.commit()
    flash(request, "Module created", "success")
    return RedirectResponse(url=f"/courses/{course_id}", status_code=302)


@router.get("/modules/{module_id}/edit", response_class=HTMLResponse, name="modules.edit")
def edit_module_page(request: Request, module_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    module = db.query(Module).filter(Module.id == module_id).first()
    if not module:
        raise HTTPException(status_code=404)
    return templates.TemplateResponse("shared/module_form.html", {**course_context(request, user, db), "course": module.course, "module": module})


@router.post("/modules/{module_id}/edit", name="modules.edit_submit")
def edit_module(
    request: Request,
    module_id: int,
    title: str = Form(...),
    description: str = Form(None),
    delivery_mode: str = Form("online"),
    is_published: bool = Form(False),
    csrf_token: str = Form(default=""),
    db: Session = Depends(get_db),
    user: User = Depends(require_role("superadmin", "trainer")),
):
    module = db.query(Module).filter(Module.id == module_id).first()
    if not module:
        flash(request, "Module not found", "error")
        return RedirectResponse(url="/courses", status_code=302)
    module.title = title
    module.description = description
    module.delivery_mode = delivery_mode
    module.is_published = is_published
    db.commit()
    flash(request, "Module updated", "success")
    return RedirectResponse(url=f"/courses/{module.course_id}", status_code=302)


@router.post("/modules/{module_id}/delete", name="modules.delete")
def delete_module(request: Request, module_id: int, db: Session = Depends(get_db), user: User = Depends(require_role("superadmin", "trainer"))):
    module = db.query(Module).filter(Module.id == module_id).first()
    if not module:
        flash(request, "Module not found", "error")
        return RedirectResponse(url="/courses", status_code=302)
    course_id = module.course_id
    db.delete(module)
    db.commit()
    flash(request, "Module deleted", "success")
    return RedirectResponse(url=f"/courses/{course_id}", status_code=302)


@router.post("/modules/{module_id}/reorder", name="modules.reorder")
def reorder_modules(module_id: int, request: Request, direction: str = Form("up"), csrf_token: str = Form(default=""), db: Session = Depends(get_db), user: User = Depends(require_role("superadmin", "trainer"))):
    module = db.query(Module).filter(Module.id == module_id).first()
    if not module:
        raise HTTPException(status_code=404)

    course_id = module.course_id
    modules = db.query(Module).filter(Module.course_id == course_id).order_by(Module.order_index).all()
    idx = None
    for i, m in enumerate(modules):
        if m.id == module_id:
            idx = i
            break

    if idx is not None:
        if direction == "up" and idx > 0:
            modules[idx].order_index, modules[idx - 1].order_index = modules[idx - 1].order_index, modules[idx].order_index
        elif direction == "down" and idx < len(modules) - 1:
            modules[idx].order_index, modules[idx + 1].order_index = modules[idx + 1].order_index, modules[idx].order_index

    for i, m in enumerate(modules):
        m.order_index = i + 1
    db.commit()
    flash(request, "Module order updated", "success")
    return RedirectResponse(url=f"/courses/{course_id}", status_code=302)


# ---- Material Management ----

@router.get("/modules/{module_id}/materials/create", response_class=HTMLResponse, name="materials.create")
def create_material_page(request: Request, module_id: int, db: Session = Depends(get_db), user: User = Depends(require_role("superadmin", "trainer"))):
    module = db.query(Module).filter(Module.id == module_id).first()
    if not module:
        raise HTTPException(status_code=404, detail="Module not found")
    return templates.TemplateResponse("shared/material_form.html", {**course_context(request, user, db), "module": module})


@router.post("/modules/{module_id}/materials/create", name="materials.create_submit")
async def create_material(
    request: Request,
    module_id: int,
    title: str = Form(...),
    file_type: str = Form("pdf"),
    url: str = Form(None),
    file: UploadFile = File(None),
    csrf_token: str = Form(default=""),
    db: Session = Depends(get_db),
    user: User = Depends(require_role("superadmin", "trainer")),
):
    module = db.query(Module).filter(Module.id == module_id).first()
    if not module:
        raise HTTPException(status_code=404)

    file_path = None
    file_size = None
    if file and file.filename:
        ext = file.filename.rsplit(".", 1)[-1] if "." in file.filename else ""
        filename = f"{uuid.uuid4()}.{ext}"
        file_path = os.path.join(UPLOAD_DIR, filename)
        content = await file.read()
        if len(content) > MAX_UPLOAD_MB * 1024 * 1024:
            raise HTTPException(413, f"File exceeds maximum size of {MAX_UPLOAD_MB}MB")
        mime = magic.from_buffer(content, mime=True)
        if ext not in ALLOWED_MIME or mime != ALLOWED_MIME[ext]:
            raise HTTPException(400, "File type not permitted")
        file_size = len(content) // 1024
        os.makedirs(UPLOAD_DIR, exist_ok=True)
        with open(file_path, "wb") as f:
            f.write(content)

    material = Material(
        module_id=module_id,
        title=title,
        file_type=file_type,
        file_path=file_path,
        file_size_kb=file_size,
        url=url or None,
        uploaded_by=user.id,
    )
    db.add(material)
    db.commit()

    flash(request, "Material uploaded", "success")
    return RedirectResponse(url=f"/courses/{module.course_id}", status_code=302)


@router.post("/materials/{material_id}/delete", name="materials.delete")
def delete_material(request: Request, material_id: int, db: Session = Depends(get_db), user: User = Depends(require_role("superadmin", "trainer"))):
    material = db.query(Material).filter(Material.id == material_id).first()
    if not material:
        flash(request, "Material not found", "error")
        return RedirectResponse(url="/courses", status_code=302)
    if material.file_path and os.path.exists(material.file_path):
        os.remove(material.file_path)
    course_id = material.module.course_id
    db.delete(material)
    db.commit()
    flash(request, "Material deleted", "success")
    return RedirectResponse(url=f"/courses/{course_id}", status_code=302)


@router.get("/materials/{material_id}/view", name="materials.view")
def view_material(material_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    material = db.query(Material).filter(Material.id == material_id).first()
    if not material or not material.file_path:
        raise HTTPException(status_code=404)
    if not _can_access_material(db, user, material):
        raise HTTPException(status_code=403, detail="You are not enrolled in this course")
    from config import UPLOAD_DIR
    safe_filename = os.path.basename(material.file_path)
    full_path = os.path.join(UPLOAD_DIR, safe_filename)
    real = os.path.realpath(full_path)
    upload_real = os.path.realpath(UPLOAD_DIR)
    if not real.startswith(upload_real):
        raise HTTPException(status_code=403)
    if not os.path.exists(full_path):
        raise HTTPException(status_code=404)
    return FileResponse(full_path, media_type="application/pdf", headers={"Content-Disposition": "inline"})


@router.get("/materials/{material_id}/download", name="materials.download")
def download_material(material_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    material = db.query(Material).filter(Material.id == material_id).first()
    if not material or not material.file_path:
        raise HTTPException(status_code=404)
    if not _can_access_material(db, user, material):
        raise HTTPException(status_code=403, detail="You are not enrolled in this course")
    from config import UPLOAD_DIR
    safe_filename = os.path.basename(material.file_path)
    full_path = os.path.join(UPLOAD_DIR, safe_filename)
    real = os.path.realpath(full_path)
    upload_real = os.path.realpath(UPLOAD_DIR)
    if not real.startswith(upload_real):
        raise HTTPException(status_code=403)
    if not os.path.exists(full_path):
        raise HTTPException(status_code=404)
    download_name = f"{material.title}{os.path.splitext(safe_filename)[1]}"
    view = MaterialView(user_id=user.id, material_id=material_id)
    db.add(view)
    db.commit()
    return FileResponse(full_path, media_type='application/octet-stream', filename=download_name)


@router.post("/materials/{material_id}/viewed", name="materials.viewed")
def record_material_view(material_id: int, view_duration_seconds: int = Form(0), csrf_token: str = Form(default=""), db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    material = db.query(Material).filter(Material.id == material_id).first()
    if not material:
        raise HTTPException(status_code=404)
    view = MaterialView(user_id=user.id, material_id=material_id, view_duration_seconds=view_duration_seconds)
    db.add(view)
    db.commit()
    return JSONResponse({"ok": True})
