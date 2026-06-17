from fastapi import APIRouter, Request, Depends, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import func
from database import get_db
from models.user import User
from models.course import Course, Module
from models.cohort import Cohort, Enrolment
from models.assessment import Assessment, Question, AnswerOption, QuestionBank
from models.submission import Submission, Answer
from services.auth_service import get_current_user, require_role
from services.notification_service import send_result_notification, create_notification
from services.audit_service import log_action
from services.flash import flash
from datetime import datetime
import json

router = APIRouter(prefix="/assessments", tags=["assessments"])
from template_utils import templates


def check_and_complete_enrolment(db: Session, enrolment):
    course_id = enrolment.cohort.course_id
    all_assessments = db.query(Assessment).filter(Assessment.course_id == course_id, Assessment.is_published == True).count()
    if all_assessments == 0:
        from services.progress_service import get_learner_progress
        progress = get_learner_progress(db, enrolment.user_id, course_id)
        if progress and progress["total_modules"] > 0 and progress["progress_pct"] == 100:
            enrolment.final_score = 100.0
            enrolment.status = "completed"
            db.commit()
            from services.certificate_service import generate_certificate
            from models.certificate import Certificate
            existing = db.query(Certificate).filter(
                Certificate.user_id == enrolment.user_id,
                Certificate.course_id == course_id,
                Certificate.revoked == False,
            ).first()
            if not existing:
                cert = generate_certificate(db, enrolment)
                from services.notification_service import send_certificate_notification
                send_certificate_notification(db, enrolment.user_id, enrolment.cohort.course.title, cert.certificate_number)
        return
    passed_assessments = db.query(func.count(Submission.id)).join(Assessment).filter(
        Assessment.course_id == course_id,
        Submission.user_id == enrolment.user_id,
        Submission.passed == True,
        Submission.status == "released",
    ).scalar() or 0
    if passed_assessments >= all_assessments:
        avg = db.query(func.avg(Submission.score)).join(Assessment).filter(
            Assessment.course_id == course_id,
            Submission.user_id == enrolment.user_id,
            Submission.passed == True,
            Submission.status == "released",
        ).scalar()
        enrolment.final_score = round(avg, 1) if avg else 0
        enrolment.status = "completed"
        db.commit()
        from services.certificate_service import generate_certificate
        from models.certificate import Certificate
        existing = db.query(Certificate).filter(
            Certificate.user_id == enrolment.user_id,
            Certificate.course_id == course_id,
            Certificate.revoked == False,
        ).first()
        if not existing:
            cert = generate_certificate(db, enrolment)
            from services.notification_service import send_certificate_notification
            send_certificate_notification(db, enrolment.user_id, enrolment.cohort.course.title, cert.certificate_number)


@router.get("", response_class=HTMLResponse, name="assessments.list")
def list_assessments(request: Request, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if user.role == "superadmin":
        assessments = db.query(Assessment).order_by(Assessment.created_at.desc()).all()
    elif user.role == "trainer":
        from models.cohort import Cohort
        course_ids = db.query(Cohort.course_id).filter(Cohort.trainer_id == user.id).distinct()
        assessments = db.query(Assessment).filter(Assessment.course_id.in_(course_ids)).all()
    else:
        assessments = db.query(Assessment).filter(Assessment.is_published == True).all()
    return templates.TemplateResponse("shared/assessments.html", {"request": request, "user": user, "assessments": assessments})


@router.get("/create", response_class=HTMLResponse, name="assessments.create")
def create_assessment_page(request: Request, course_id: int = None, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if user.role == "superadmin":
        courses = db.query(Course).all()
    else:
        courses = db.query(Course).filter(
            (Course.created_by == user.id) | (Course.is_published == True)
        ).all()
    preselected_course_id = course_id
    modules = []
    if preselected_course_id:
        modules = db.query(Module).filter(Module.course_id == preselected_course_id).order_by(Module.order_index).all()
    course_pass_marks = {c.id: c.pass_mark for c in courses}
    return templates.TemplateResponse("shared/assessment_form.html", {
        "request": request, "user": user, "assessment": None, "courses": courses,
        "preselected_course_id": preselected_course_id, "modules": modules,
        "course_pass_marks": course_pass_marks,
    })


@router.post("/create", name="assessments.create_submit")
def create_assessment(
    request: Request,
    course_id: int = Form(...),
    module_id: int = Form(None),
    title: str = Form(...),
    type: str = Form("mcq"),
    max_attempts: int = Form(1),
    pass_mark: float = Form(None),
    time_limit_mins: int = Form(None),
    randomise_questions: str = Form("false"),
    randomise_options: str = Form("false"),
    release_results_immediately: str = Form("false"),
    csrf_token: str = Form(default=""),
    db: Session = Depends(get_db),
    user: User = Depends(require_role("superadmin", "trainer")),
):
    rq = randomise_questions == "true"
    ro = randomise_options == "true"
    rri = release_results_immediately == "true"
    if type in ("written", "short_answer"):
        rri = False
    assessment = Assessment(
        course_id=course_id,
        module_id=module_id,
        title=title,
        type=type,
        max_attempts=max_attempts,
        pass_mark=pass_mark,
        time_limit_mins=time_limit_mins,
        randomise_questions=rq,
        randomise_options=ro,
        release_results_immediately=rri,
    )
    db.add(assessment)
    db.commit()
    flash(request, "Assessment created", "success")
    return RedirectResponse(url=f"/assessments/{assessment.id}", status_code=302)


@router.get("/marking", response_class=HTMLResponse, name="marking.queue")
def marking_queue(request: Request, assessment_id: int = None, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    base = db.query(Submission).filter(Submission.status == "submitted")
    if assessment_id:
        base = base.filter(Submission.assessment_id == assessment_id)
    if user.role == "superadmin":
        submissions = base.order_by(Submission.submitted_at).all()
    elif user.role == "trainer":
        from models.cohort import Cohort
        course_ids = db.query(Cohort.course_id).filter(Cohort.trainer_id == user.id).distinct()
        submissions = base.join(Submission.assessment).filter(
            Assessment.course_id.in_(course_ids),
        ).order_by(Submission.submitted_at).all()
    else:
        submissions = []
    return templates.TemplateResponse("shared/marking_queue.html", {"request": request, "user": user, "submissions": submissions, "assessment_id": assessment_id})


@router.get("/marking/{submission_id}", response_class=HTMLResponse, name="marking.mark")
def mark_submission_page(request: Request, submission_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    submission = db.query(Submission).filter(Submission.id == submission_id).first()
    if not submission:
        raise HTTPException(status_code=404)
    assessment = submission.assessment
    questions = db.query(Question).filter(Question.assessment_id == assessment.id).order_by(Question.order_index).all()
    answers = db.query(Answer).filter(Answer.submission_id == submission_id).all()
    return templates.TemplateResponse("shared/marking_form.html", {
        "request": request, "user": user, "submission": submission,
        "assessment": assessment, "questions": questions, "answers": answers,
    })


@router.post("/marking/{submission_id}", name="marking.submit")
async def mark_submission(
    submission_id: int,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_role("superadmin", "trainer")),
):
    submission = db.query(Submission).filter(Submission.id == submission_id).first()
    if not submission:
        raise HTTPException(status_code=404)

    form = await request.form()
    form_data = dict(form)
    assessment = submission.assessment
    total_marks = 0
    awarded_marks = 0

    for key, value in form_data.items():
        if key.startswith("marks_"):
            q_id = int(key.split("_")[1])
            answer = db.query(Answer).filter(
                Answer.submission_id == submission_id, Answer.question_id == q_id
            ).first()
            if answer:
                answer.marks_awarded = float(value) if value else 0
                awarded_marks += float(value) if value else 0
            question = db.query(Question).filter(Question.id == q_id).first()
            if question:
                total_marks += question.marks

        elif key.startswith("feedback_"):
            q_id = int(key.split("_")[1])
            answer = db.query(Answer).filter(
                Answer.submission_id == submission_id, Answer.question_id == q_id
            ).first()
            if answer:
                answer.marker_feedback = value

    feedback = form_data.get("overall_feedback", "")
    score = round((awarded_marks / total_marks * 100), 1) if total_marks > 0 else 0
    pass_mark = assessment.pass_mark or assessment.course.pass_mark if assessment.course else 55
    passed = score >= pass_mark

    malpractice_flag = form_data.get("malpractice_flag") == "1"
    malpractice_notes = form_data.get("malpractice_notes", "")
    submission.malpractice_flag = malpractice_flag
    submission.malpractice_notes = malpractice_notes

    submission.score = score
    submission.passed = passed
    submission.feedback = feedback
    submission.status = "released"
    submission.marked_at = datetime.utcnow()
    submission.marked_by = user.id
    db.commit()

    log_action(db, user.id, "mark_submission", "submission", submission_id, f"Marked submission for assessment {assessment.title}: score={score}%, passed={passed}")
    if malpractice_flag:
        log_action(db, user.id, "malpractice_flag", "submission", submission_id,
                   f"Malpractice flagged for submission #{submission_id} ({assessment.title}): {malpractice_notes[:200]}")
    send_result_notification(db, submission.user_id, assessment.title, score, passed)
    if assessment.course_id and submission.user_id:
        enrol = db.query(Enrolment).join(Cohort).filter(
            Enrolment.user_id == submission.user_id,
            Cohort.course_id == assessment.course_id,
            Enrolment.status.in_(["enrolled", "in_progress"]),
        ).first()
        if enrol:
            check_and_complete_enrolment(db, enrol)
    flash(request, "Submission marked", "success")
    return RedirectResponse(url="/assessments/marking", status_code=302)


@router.get("/{assessment_id}", response_class=HTMLResponse, name="assessments.view")
def view_assessment(
    request: Request, assessment_id: int,
    course_code_tag: str = None, syllabus_area_tag: str = None,
    user: User = Depends(get_current_user), db: Session = Depends(get_db),
):
    assessment = db.query(Assessment).filter(Assessment.id == assessment_id).first()
    if not assessment:
        raise HTTPException(status_code=404)
    questions = db.query(Question).filter(Question.assessment_id == assessment_id).order_by(Question.order_index).all()
    submissions = db.query(Submission).filter(Submission.assessment_id == assessment_id).order_by(Submission.submitted_at.desc()).limit(20).all()
    bank_questions = None
    if request.query_params.get("import_filter"):
        query = db.query(QuestionBank).filter(QuestionBank.is_active == True)
        if course_code_tag:
            query = query.filter(QuestionBank.course_code_tag.ilike(f"%{course_code_tag}%"))
        if syllabus_area_tag:
            query = query.filter(QuestionBank.syllabus_area_tag.ilike(f"%{syllabus_area_tag}%"))
        bank_questions = query.order_by(QuestionBank.created_at.desc()).all()
    return templates.TemplateResponse("shared/assessment_view.html", {
        "request": request, "user": user, "assessment": assessment,
        "questions": questions, "submissions": submissions,
        "bank_questions": bank_questions,
    })


@router.get("/{assessment_id}/edit", response_class=HTMLResponse, name="assessments.edit")
def edit_assessment_get(request: Request, assessment_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    assessment = db.query(Assessment).filter(Assessment.id == assessment_id).first()
    if not assessment:
        raise HTTPException(status_code=404)
    return templates.TemplateResponse("shared/assessment_view.html", {
        "request": request, "user": user, "assessment": assessment,
        "questions": db.query(Question).filter(Question.assessment_id == assessment_id).order_by(Question.order_index).all(),
        "submissions": [],
    })

@router.post("/{assessment_id}/edit", name="assessments.edit_submit")
def edit_assessment_post(
    request: Request,
    assessment_id: int,
    title: str = Form(...),
    type: str = Form("mcq"),
    pass_mark: float = Form(None),
    max_attempts: int = Form(1),
    time_limit_mins: int = Form(None),
    is_published: bool = Form(False),
    randomise_questions: str = Form("false"),
    randomise_options: str = Form("false"),
    release_results_immediately: str = Form("false"),
    csrf_token: str = Form(default=""),
    db: Session = Depends(get_db),
    user: User = Depends(require_role("superadmin", "trainer")),
):
    assessment = db.query(Assessment).filter(Assessment.id == assessment_id).first()
    if assessment:
        assessment.title = title
        assessment.type = type
        assessment.pass_mark = pass_mark
        assessment.max_attempts = max_attempts
        assessment.time_limit_mins = time_limit_mins
        assessment.is_published = is_published
        assessment.randomise_questions = randomise_questions == "true"
        assessment.randomise_options = randomise_options == "true"
        if type in ("written", "short_answer"):
            assessment.release_results_immediately = False
        else:
            assessment.release_results_immediately = release_results_immediately == "true"
        db.commit()
        flash(request, "Assessment updated", "success")
    return RedirectResponse(url=f"/assessments/{assessment_id}", status_code=302)


@router.get("/{assessment_id}/delete-confirm", response_class=HTMLResponse, name="assessments.delete_confirm")
def delete_confirm(request: Request, assessment_id: int, db: Session = Depends(get_db), user: User = Depends(require_role("superadmin", "trainer"))):
    assessment = db.query(Assessment).filter(Assessment.id == assessment_id).first()
    if not assessment:
        raise HTTPException(status_code=404)
    sub_count = db.query(Submission).filter(Submission.assessment_id == assessment_id).count()
    return templates.TemplateResponse("shared/assessment_delete_confirm.html", {
        "request": request, "user": user, "assessment": assessment, "sub_count": sub_count,
    })


@router.post("/{assessment_id}/delete", name="assessments.delete")
def delete_assessment(request: Request, assessment_id: int, db: Session = Depends(get_db), user: User = Depends(require_role("superadmin", "trainer"))):
    assessment = db.query(Assessment).filter(Assessment.id == assessment_id).first()
    if not assessment:
        raise HTTPException(status_code=404)
    sub_count = db.query(Submission).filter(Submission.assessment_id == assessment_id).count()
    if sub_count > 0 and request.query_params.get("confirm") != "1":
        return RedirectResponse(url=f"/assessments/{assessment_id}/delete-confirm", status_code=302)
    db.delete(assessment)
    db.commit()
    flash(request, "Assessment deleted", "success")
    return RedirectResponse(url="/assessments", status_code=302)


@router.post("/{assessment_id}/questions/add", name="assessments.add_question")
def add_question(
    assessment_id: int,
    request: Request,
    question_text: str = Form(...),
    question_type: str = Form("mcq"),
    marks: float = Form(1.0),
    option_a: str = Form(None),
    option_b: str = Form(None),
    option_c: str = Form(None),
    option_d: str = Form(None),
    correct_answer: str = Form(None),
    csrf_token: str = Form(default=""),
    db: Session = Depends(get_db),
    user: User = Depends(require_role("superadmin", "trainer")),
):
    assessment = db.query(Assessment).filter(Assessment.id == assessment_id).first()
    if not assessment:
        raise HTTPException(status_code=404)

    count = db.query(Question).filter(Question.assessment_id == assessment_id).count()
    question = Question(
        assessment_id=assessment_id,
        question_text=question_text,
        question_type=question_type,
        marks=marks,
        order_index=count + 1,
    )
    db.add(question)
    db.flush()

    if question_type == "mcq":
        options = [
            ("A", option_a),
            ("B", option_b),
            ("C", option_c),
            ("D", option_d),
        ]
        for label, text in options:
            if text:
                is_correct = (label == correct_answer)
                opt = AnswerOption(question_id=question.id, option_text=text, is_correct=is_correct)
                db.add(opt)
    db.commit()
    flash(request, "Question added", "success")
    return RedirectResponse(url=f"/assessments/{assessment_id}", status_code=302)


@router.post("/{assessment_id}/import-from-bank", name="assessments.import_from_bank")
def import_from_bank(
    assessment_id: int,
    request: Request,
    question_ids: list[int] = Form(...),
    csrf_token: str = Form(default=""),
    db: Session = Depends(get_db),
    user: User = Depends(require_role("superadmin", "trainer")),
):
    assessment = db.query(Assessment).filter(Assessment.id == assessment_id).first()
    if not assessment:
        raise HTTPException(status_code=404)
    count = db.query(Question).filter(Question.assessment_id == assessment_id).count()
    bank_questions = db.query(QuestionBank).filter(QuestionBank.id.in_(question_ids)).all()
    imported = 0
    for bq in bank_questions:
        question = Question(
            assessment_id=assessment_id,
            question_text=bq.question_text,
            question_type=bq.question_type,
            marks=bq.marks,
            syllabus_area_tag=bq.syllabus_area_tag,
            order_index=count + imported + 1,
        )
        db.add(question)
        db.flush()
        if bq.bank_options:
            for opt in bq.bank_options:
                ao = AnswerOption(
                    question_id=question.id,
                    option_text=opt.option_text,
                    is_correct=opt.is_correct,
                )
                db.add(ao)
        imported += 1
    db.commit()
    flash(request, f"Imported {imported} question(s) from bank", "success")
    return RedirectResponse(url=f"/assessments/{assessment_id}", status_code=302)


@router.post("/questions/{question_id}/edit", name="assessments.edit_question")
def edit_question(
    question_id: int,
    request: Request,
    question_text: str = Form(...),
    question_type: str = Form("mcq"),
    marks: float = Form(1.0),
    order_index: int = Form(0),
    syllabus_area_tag: str = Form(None),
    option_a: str = Form(None),
    option_b: str = Form(None),
    option_c: str = Form(None),
    option_d: str = Form(None),
    correct_answer: str = Form(None),
    csrf_token: str = Form(default=""),
    db: Session = Depends(get_db),
    user: User = Depends(require_role("superadmin", "trainer")),
):
    question = db.query(Question).filter(Question.id == question_id).first()
    if not question:
        raise HTTPException(status_code=404)
    question.question_text = question_text
    question.question_type = question_type
    question.marks = marks
    question.order_index = order_index
    question.syllabus_area_tag = syllabus_area_tag
    db.commit()

    if question_type == "mcq":
        # Remove existing options and recreate
        existing = db.query(AnswerOption).filter(AnswerOption.question_id == question.id).all()
        for opt in existing:
            db.delete(opt)
        labels = ["A", "B", "C", "D"]
        texts = [option_a, option_b, option_c, option_d]
        for label, text in zip(labels, texts):
            if text:
                opt = AnswerOption(question_id=question.id, option_text=text, is_correct=(label == correct_answer))
                db.add(opt)
        db.commit()

    assessment_id = question.assessment_id
    flash(request, "Question updated", "success")
    return RedirectResponse(url=f"/assessments/{assessment_id}", status_code=302)


@router.post("/questions/{question_id}/delete", name="assessments.delete_question")
def delete_question(request: Request, question_id: int, db: Session = Depends(get_db), user: User = Depends(require_role("superadmin", "trainer"))):
    question = db.query(Question).filter(Question.id == question_id).first()
    if question:
        assessment_id = question.assessment_id
        db.delete(question)
        db.commit()
        flash(request, "Question deleted", "success")
        return RedirectResponse(url=f"/assessments/{assessment_id}", status_code=302)
    flash(request, "Question not found", "error")
    return RedirectResponse(url="/assessments", status_code=302)


@router.get("/{assessment_id}/take", response_class=HTMLResponse, name="assessments.take")
def take_assessment(request: Request, assessment_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    assessment = db.query(Assessment).filter(Assessment.id == assessment_id, Assessment.is_published == True).first()
    if not assessment:
        raise HTTPException(status_code=404)

    if user.role == "learner":
        from models.cohort import Cohort, Enrolment
        enrolled = db.query(Enrolment).join(Cohort).filter(Enrolment.user_id==user.id, Cohort.course_id==assessment.course_id, Enrolment.status.in_(["enrolled","in_progress","completed"])).first()
        if not enrolled:
            raise HTTPException(status_code=403, detail="Not enrolled in this course")

    attempt_count = db.query(Submission).filter(
        Submission.user_id == user.id, Submission.assessment_id == assessment_id
    ).count()
    if attempt_count >= assessment.max_attempts:
        return templates.TemplateResponse("shared/assessment_take.html", {
            "request": request, "user": user, "assessment": assessment,
            "error": "Maximum attempts reached",
        })

    questions = db.query(Question).filter(Question.assessment_id == assessment_id).order_by(Question.order_index).all()
    import random
    if assessment.randomise_questions:
        questions = list(questions)
        random.shuffle(questions)
    question_data = []
    for q in questions:
        opts = list(q.answer_options) if assessment.randomise_options else list(q.answer_options)
        if assessment.randomise_options:
            random.shuffle(opts)
        question_data.append({"question": q, "options": opts})
    return templates.TemplateResponse("shared/assessment_take.html", {
        "request": request, "user": user, "assessment": assessment,
        "question_data": question_data, "error": None,
    })


@router.post("/{assessment_id}/submit", name="assessments.submit")
async def submit_assessment(
    assessment_id: int,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    form = await request.form()
    assessment = db.query(Assessment).filter(Assessment.id == assessment_id).first()
    if not assessment:
        raise HTTPException(status_code=404)

    if user.role == "learner":
        from models.cohort import Cohort, Enrolment
        enrolled = db.query(Enrolment).join(Cohort).filter(Enrolment.user_id==user.id, Cohort.course_id==assessment.course_id, Enrolment.status.in_(["enrolled","in_progress","completed"])).first()
        if not enrolled:
            raise HTTPException(status_code=403, detail="Not enrolled in this course")

    form_data = dict(form)
    questions = db.query(Question).filter(Question.assessment_id == assessment_id).order_by(Question.order_index).all()

    attempt_number = db.query(Submission).filter(
        Submission.user_id == user.id, Submission.assessment_id == assessment_id
    ).count() + 1

    submission = Submission(
        user_id=user.id,
        assessment_id=assessment_id,
        attempt_number=attempt_number,
        status="submitted",
    )
    db.add(submission)
    db.flush()

    total_marks = 0
    awarded_marks = 0

    for q in questions:
        answer_key = f"q_{q.id}"
        selected = form_data.get(answer_key)

        if q.question_type == "mcq" and selected:
            try:
                selected_id = int(selected)
                option = db.query(AnswerOption).filter(AnswerOption.id == selected_id).first()
                is_correct = option and option.is_correct
                if is_correct:
                    awarded_marks += q.marks
                total_marks += q.marks
                marks_awarded = q.marks if is_correct else 0
            except (ValueError, TypeError):
                total_marks += q.marks
                marks_awarded = 0

            answer = Answer(
                submission_id=submission.id,
                question_id=q.id,
                selected_option_id=int(selected) if selected else None,
                marks_awarded=marks_awarded,
            )
        else:
            total_marks += q.marks
            marks_awarded = 0 if q.question_type == "mcq" else None
            answer = Answer(
                submission_id=submission.id,
                question_id=q.id,
                answer_text=selected,
                marks_awarded=marks_awarded,
            )
        db.add(answer)

    if assessment.type == "mcq":
        score = round((awarded_marks / total_marks * 100), 1) if total_marks > 0 else 0
        pass_mark = assessment.pass_mark or (assessment.course.pass_mark if assessment.course else None) or 55
        passed = score >= pass_mark
        submission.score = score
        submission.passed = passed
        submission.status = "released" if assessment.release_results_immediately else "submitted"

        if assessment.release_results_immediately:
            try:
                send_result_notification(db, user.id, assessment.title, score, passed)
            except Exception:
                pass

    submission.submitted_at = datetime.utcnow()
    db.commit()

    if assessment.course_id and assessment.type == "mcq" and assessment.release_results_immediately:
        try:
            enrol = db.query(Enrolment).join(Cohort).filter(
                Enrolment.user_id == user.id,
                Cohort.course_id == assessment.course_id,
                Enrolment.status.in_(["enrolled", "in_progress"]),
            ).first()
            if enrol:
                check_and_complete_enrolment(db, enrol)
        except Exception:
            db.rollback()

    log_action(db, user.id, "submit_assessment", "submission", submission.id, f"Submitted assessment {assessment.title} ({assessment_id})")
    flash(request, "Assessment submitted", "success")
    return RedirectResponse(url=f"/assessments/{assessment_id}/result/{submission.id}", status_code=302)


@router.get("/{assessment_id}/result/{submission_id}", response_class=HTMLResponse, name="assessments.view_result")
def view_result(request: Request, assessment_id: int, submission_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    submission = db.query(Submission).filter(Submission.id == submission_id, Submission.user_id == user.id).first()
    if not submission:
        raise HTTPException(status_code=404)
    assessment = db.query(Assessment).filter(Assessment.id == assessment_id).first()
    questions = db.query(Question).filter(Question.assessment_id == assessment_id).order_by(Question.order_index).all()
    answers = db.query(Answer).filter(Answer.submission_id == submission_id).all()
    answer_map = {a.question_id: a for a in answers}
    unscored_exists = any(a.marks_awarded is None for a in answers)
    partial_awarded = sum(a.marks_awarded for a in answers if a.marks_awarded is not None)
    partial_total = sum(q.marks for q in questions)
    partial_score = round((partial_awarded / partial_total * 100), 1) if partial_total > 0 else 0
    return templates.TemplateResponse("shared/assessment_result.html", {
        "request": request, "user": user, "assessment": assessment,
        "submission": submission, "questions": questions, "answers": answer_map,
        "unscored_exists": unscored_exists, "partial_score": partial_score,
    })



