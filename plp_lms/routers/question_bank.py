from fastapi import APIRouter, Request, Depends, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from database import get_db
from models.user import User
from models.assessment import QuestionBank, QuestionBankOption
from services.auth_service import get_current_user, require_role
from services.flash import flash
from sqlalchemy import func

router = APIRouter(prefix="/question-bank", tags=["question-bank"])
from template_utils import templates


@router.get("", response_class=HTMLResponse, name="question_bank.list")
def list_questions(
    request: Request,
    course_code_tag: str = None,
    syllabus_area_tag: str = None,
    db: Session = Depends(get_db),
    user: User = Depends(require_role("superadmin", "trainer")),
):
    query = db.query(QuestionBank).filter(QuestionBank.is_active == True)
    if course_code_tag:
        query = query.filter(QuestionBank.course_code_tag.ilike(f"%{course_code_tag}%"))
    if syllabus_area_tag:
        query = query.filter(QuestionBank.syllabus_area_tag.ilike(f"%{syllabus_area_tag}%"))
    questions = query.order_by(QuestionBank.created_at.desc()).all()
    course_tags = [r[0] for r in db.query(QuestionBank.course_code_tag).filter(QuestionBank.course_code_tag.isnot(None), QuestionBank.is_active == True).distinct().order_by(QuestionBank.course_code_tag).all()]
    syllabus_tags = [r[0] for r in db.query(QuestionBank.syllabus_area_tag).filter(QuestionBank.syllabus_area_tag.isnot(None), QuestionBank.is_active == True).distinct().order_by(QuestionBank.syllabus_area_tag).all()]
    return templates.TemplateResponse("shared/question_bank.html", {
        "request": request, "user": user, "questions": questions,
        "course_code_tag": course_code_tag, "syllabus_area_tag": syllabus_area_tag,
        "course_tags": course_tags, "syllabus_tags": syllabus_tags,
    })


@router.post("/create", name="question_bank.create")
def create_question(
    request: Request,
    question_text: str = Form(...),
    question_type: str = Form("mcq"),
    marks: float = Form(1.0),
    course_code_tag: str = Form(None),
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
    question = QuestionBank(
        question_text=question_text,
        question_type=question_type,
        marks=marks,
        course_code_tag=course_code_tag or None,
        syllabus_area_tag=syllabus_area_tag or None,
        created_by=user.id,
    )
    db.add(question)
    db.flush()

    if question_type == "mcq":
        options = [("A", option_a), ("B", option_b), ("C", option_c), ("D", option_d)]
        for label, text in options:
            if text:
                opt = QuestionBankOption(
                    bank_question_id=question.id,
                    option_text=text,
                    is_correct=(label == correct_answer),
                    option_label=label,
                )
                db.add(opt)
    db.commit()
    flash(request, "Question added to bank", "success")
    return RedirectResponse(url="/question-bank", status_code=302)


@router.post("/{qid}/edit", name="question_bank.edit")
def edit_question(
    qid: int,
    request: Request,
    question_text: str = Form(...),
    question_type: str = Form("mcq"),
    marks: float = Form(1.0),
    course_code_tag: str = Form(None),
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
    question = db.query(QuestionBank).filter(QuestionBank.id == qid).first()
    if not question:
        raise HTTPException(status_code=404)
    question.question_text = question_text
    question.question_type = question_type
    question.marks = marks
    question.course_code_tag = course_code_tag or None
    question.syllabus_area_tag = syllabus_area_tag or None

    if question_type == "mcq":
        db.query(QuestionBankOption).filter(QuestionBankOption.bank_question_id == qid).delete()
        options = [("A", option_a), ("B", option_b), ("C", option_c), ("D", option_d)]
        for label, text in options:
            if text:
                opt = QuestionBankOption(
                    bank_question_id=qid, option_text=text,
                    is_correct=(label == correct_answer), option_label=label,
                )
                db.add(opt)
    db.commit()
    flash(request, "Question updated", "success")
    return RedirectResponse(url="/question-bank", status_code=302)


@router.post("/{qid}/delete", name="question_bank.delete")
def delete_question(
    qid: int,
    request: Request,
    csrf_token: str = Form(default=""),
    db: Session = Depends(get_db),
    user: User = Depends(require_role("superadmin", "trainer")),
):
    question = db.query(QuestionBank).filter(QuestionBank.id == qid).first()
    if not question:
        raise HTTPException(status_code=404)
    question.is_active = False
    db.commit()
    flash(request, "Question removed from bank", "success")
    return RedirectResponse(url="/question-bank", status_code=302)
