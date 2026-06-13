from database import init_db, SessionLocal
from models.user import User
from models.course import Course, LearningOutcome, Module, Material
from models.cohort import Cohort, Enrolment, AttendanceRecord
from models.assessment import Assessment, Question, AnswerOption
from models.submission import Submission, Answer
from services.auth_service import hash_password
from datetime import datetime, date, timedelta
import random


def seed():
    init_db()
    db = SessionLocal()

    existing = db.query(User).filter(User.email == "admin@plprojects.co.uk").first()
    if existing:
        print("Seed data already exists. Skipping.")
        return

    # Users
    admin = User(
        username="admin", email="admin@plprojects.co.uk",
        password_hash=hash_password("Admin1234!"), role="superadmin",
        full_name="System Administrator", organisation="PL Projects Ltd",
        force_password_change=True, gdpr_consent_date=datetime.utcnow(),
    )
    trainer = User(
        username="trainer", email="trainer@plprojects.co.uk",
        password_hash=hash_password("Trainer1234!"), role="trainer",
        full_name="Sarah Trainer", organisation="PL Projects Ltd",
        gdpr_consent_date=datetime.utcnow(),
    )
    observer = User(
        username="observer", email="observer@plprojects.co.uk",
        password_hash=hash_password("Observer1234!"), role="observer",
        full_name="Mike Observer", organisation="PL Projects Ltd",
        gdpr_consent_date=datetime.utcnow(),
    )
    assessor = User(
        username="assessor", email="assessor@plprojects.co.uk",
        password_hash=hash_password("Assessor1234!"), role="external_assessor",
        full_name="Claire Assessor", organisation="PL Projects Ltd",
        gdpr_consent_date=datetime.utcnow(),
    )
    learner1 = User(
        username="learner1", email="learner1@example.com",
        password_hash=hash_password("Learner1234!"), role="learner",
        full_name="Alice Johnson", organisation="ABC Corp",
        gdpr_consent_date=datetime.utcnow(),
    )
    learner2 = User(
        username="learner2", email="learner2@example.com",
        password_hash=hash_password("Learner1234!"), role="learner",
        full_name="Bob Smith", organisation="XYZ Ltd",
        gdpr_consent_date=datetime.utcnow(),
    )
    db.add_all([admin, trainer, observer, assessor, learner1, learner2])
    db.flush()

    # Course templates
    courses_data = [
        {"code": "PFQ", "title": "APM Project Fundamentals Qualification", "body": "APM", "level": "Foundation",
         "desc": "The APM Project Fundamentals Qualification (PFQ) is the introductory qualification for project management.",
         "pass": 55.0, "assessment": "mixed", "mode": "blended", "hours": 24, "cert_years": 0, "credit": 5},
        {"code": "PMQ", "title": "APM Project Management Qualification", "body": "APM", "level": "Practitioner",
         "desc": "The APM Project Management Qualification (PMQ) is a knowledge-based qualification for project managers.",
         "pass": 55.0, "assessment": "mixed", "mode": "blended", "hours": 48, "cert_years": 0, "credit": 10},
        {"code": "RISK-L1", "title": "Risk Management Level 1", "body": "IRM / in-house", "level": "Introductory",
         "desc": "Introduction to risk management principles and practices.",
         "pass": 60.0, "assessment": "mcq", "mode": "online", "hours": 12, "cert_years": 2, "credit": 3},
        {"code": "RISK-L2", "title": "Risk Management Level 2", "body": "IRM / in-house", "level": "Practitioner",
         "desc": "Advanced risk management for project practitioners.",
         "pass": 60.0, "assessment": "mixed", "mode": "online", "hours": 24, "cert_years": 2, "credit": 6},
        {"code": "CiTiB", "title": "Construction Industry Training Board Awareness", "body": "CITB", "level": "Industry",
         "desc": "CITB Health and Safety Awareness for the construction industry.",
         "pass": 70.0, "assessment": "mcq", "mode": "classroom", "hours": 8, "cert_years": 5, "credit": 2},
    ]

    courses = []
    for cd in courses_data:
        c = Course(
            course_code=cd["code"], title=cd["title"], awarding_body=cd["body"],
            level=cd["level"], description=cd["desc"], pass_mark=cd["pass"],
            assessment_type=cd["assessment"], delivery_mode=cd["mode"],
            duration_hours=cd["hours"], cert_validity_years=cd["cert_years"],
            credit_value=cd["credit"], is_published=True, created_by=admin.id,
        )
        db.add(c)
        db.flush()
        courses.append(c)

        # Learning outcomes
        outcomes = [
            f"Understand key {cd['code']} concepts",
            f"Apply {cd['code']} methodologies",
            f"Evaluate {cd['code']} case studies",
            f"Demonstrate {cd['code']} best practices",
        ]
        for i, ot in enumerate(outcomes):
            lo = LearningOutcome(course_id=c.id, outcome_text=ot, syllabus_area=cd["code"], order_index=i + 1)
            db.add(lo)

    # PFQ modules
    pfq = courses[0]
    modules_data = [
        {"title": "Introduction to Project Management", "mode": "online"},
        {"title": "Project Lifecycle and Processes", "mode": "online"},
        {"title": "Planning and Scheduling", "mode": "blended"},
    ]

    for i, md in enumerate(modules_data):
        mod = Module(course_id=pfq.id, title=md["title"], description=f"Module covering {md['title']}",
                     order_index=i + 1, delivery_mode=md["mode"])
        db.add(mod)
        db.flush()

        if i < 2:
            mat = Material(module_id=mod.id, title=f"{md['title']} Slides", file_type="pdf",
                           file_path=f"sample_{md['title'].lower().replace(' ', '_')}.pdf",
                           file_size_kb=random.randint(200, 2000), uploaded_by=trainer.id)
            db.add(mat)

    # PFQ assessment with MCQ questions
    pfq_assessment = Assessment(
        course_id=pfq.id, title="PFQ Sample Test", type="mcq",
        max_attempts=2, pass_mark=55.0, time_limit_mins=30,
        is_published=True, release_results_immediately=True,
    )
    db.add(pfq_assessment)
    db.flush()

    questions_data = [
        ("What is a project?", "A temporary endeavour to create a unique product or service", "Ongoing operations", "A routine task", "A department function", "A"),
        ("What does WBS stand for?", "Work Breakdown Structure", "Work Based Schedule", "Work Balance System", "Weekly Briefing Session", "A"),
        ("What is the triple constraint?", "Time, Cost, Quality", "Time, Cost, Scope", "Scope, Quality, Risk", "Time, Risk, Quality", "B"),
        ("What is a risk?", "An uncertain event that may affect objectives", "A guaranteed problem", "A project task", "A team member", "A"),
        ("What is the critical path?", "The longest sequence of dependent activities", "The shortest path", "The easiest tasks", "The project budget", "A"),
    ]

    for i, (qt, opt_a, opt_b, opt_c, opt_d, correct) in enumerate(questions_data):
        q = Question(assessment_id=pfq_assessment.id, question_text=qt, question_type="mcq", marks=1.0, order_index=i + 1)
        db.add(q)
        db.flush()

        for label, text in [("A", opt_a), ("B", opt_b), ("C", opt_c), ("D", opt_d)]:
            opt = AnswerOption(question_id=q.id, option_text=text, is_correct=(label == correct))
            db.add(opt)

    # Cohort
    pfq_cohort = Cohort(
        name="PFQ Cohort 2026-A", course_id=pfq.id, trainer_id=trainer.id,
        start_date=date(2026, 1, 15), end_date=date(2026, 3, 15),
        max_learners=20, enrolment_token="PFQ2026A", is_active=True,
        delivery_mode="blended", venue="PLP London Office",
    )
    db.add(pfq_cohort)
    db.flush()

    # Enrolments
    for learner in [learner1, learner2]:
        en = Enrolment(user_id=learner.id, cohort_id=pfq_cohort.id, status="in_progress", enrolment_source="seed")
        db.add(en)
        db.flush()

        # Sample attendance
        for days_ago in [5, 4, 3]:
            att = AttendanceRecord(
                enrolment_id=en.id, cohort_id=pfq_cohort.id,
                session_date=date.today() - timedelta(days=days_ago),
                attended=True, recorded_by=trainer.id,
            )
            db.add(att)

    # --- Written assessment for trainer marking flow ---
    written_assessment = Assessment(
        course_id=pfq.id, title="PFQ Written Assignment", type="written",
        max_attempts=2, pass_mark=55.0, time_limit_mins=60,
        is_published=True, release_results_immediately=False,
    )
    db.add(written_assessment)
    db.flush()

    written_questions = [
        "Describe the key stages of a project lifecycle.",
        "Explain how a Work Breakdown Structure is created and used.",
        "Identify three common project risks and describe mitigation strategies.",
    ]
    for i, qt in enumerate(written_questions):
        q = Question(
            assessment_id=written_assessment.id, question_text=qt,
            question_type="written", marks=10.0, order_index=i + 1,
        )
        db.add(q)
    db.flush()

    # --- Learner submissions for PFQ Sample Test (MCQ, auto-graded) ---
    mcq = pfq_assessment
    mcq_questions = db.query(Question).filter(Question.assessment_id == mcq.id).order_by(Question.order_index).all()
    mcq_options = {}
    for q in mcq_questions:
        mcq_options[q.id] = db.query(AnswerOption).filter(AnswerOption.question_id == q.id).all()

    # learner1: 3/5 correct
    sub1 = Submission(
        user_id=learner1.id, assessment_id=mcq.id, attempt_number=1,
        status="released", score=60.0, passed=True,
        submitted_at=datetime.utcnow() - timedelta(hours=2),
    )
    db.add(sub1)
    db.flush()
    learner1_correct = [0, 1, 3]  # question indices (0-based) that learner1 gets right
    for idx, q in enumerate(mcq_questions):
        correct_opt = [o for o in mcq_options[q.id] if o.is_correct][0]
        wrong_opt = [o for o in mcq_options[q.id] if not o.is_correct][0]
        chosen = correct_opt if idx in learner1_correct else wrong_opt
        db.add(Answer(
            submission_id=sub1.id, question_id=q.id,
            selected_option_id=chosen.id,
            marks_awarded=q.marks if idx in learner1_correct else 0,
        ))
    db.flush()

    # learner2: 4/5 correct
    sub2 = Submission(
        user_id=learner2.id, assessment_id=mcq.id, attempt_number=1,
        status="released", score=80.0, passed=True,
        submitted_at=datetime.utcnow() - timedelta(hours=1),
    )
    db.add(sub2)
    db.flush()
    learner2_wrong = [2]  # gets question index 2 wrong
    for idx, q in enumerate(mcq_questions):
        correct_opt = [o for o in mcq_options[q.id] if o.is_correct][0]
        wrong_opt = [o for o in mcq_options[q.id] if not o.is_correct][0]
        chosen = wrong_opt if idx in learner2_wrong else correct_opt
        db.add(Answer(
            submission_id=sub2.id, question_id=q.id,
            selected_option_id=chosen.id,
            marks_awarded=0 if idx in learner2_wrong else q.marks,
        ))
    db.flush()

    # --- Learner submission for written assessment (pending trainer marking) ---
    written_qs = db.query(Question).filter(Question.assessment_id == written_assessment.id).order_by(Question.order_index).all()
    sub3 = Submission(
        user_id=learner1.id, assessment_id=written_assessment.id, attempt_number=1,
        status="submitted",
        submitted_at=datetime.utcnow() - timedelta(minutes=30),
    )
    db.add(sub3)
    db.flush()
    written_answers = [
        "The key stages are: initiation, planning, execution, monitoring & control, and closure. Initiation defines the project, planning sets the roadmap, execution delivers the work, monitoring tracks progress, and closure finalises everything.",
        "A WBS is a hierarchical decomposition of the work to be performed. It breaks deliverables down into smaller, manageable components. It's used to estimate costs, assign responsibilities, and track progress at each level.",
        "1. Scope creep - mitigated by clear change control process. 2. Resource unavailability - mitigated by resource planning and cross-training. 3. Technical failure - mitigated by prototyping and regular testing.",
    ]
    for q, ans_text in zip(written_qs, written_answers):
        db.add(Answer(
            submission_id=sub3.id, question_id=q.id, answer_text=ans_text,
        ))
    db.flush()

    db.commit()
    print("Seed data created successfully!")
    print("Admin: admin@plprojects.co.uk / Admin1234!")
    print("Trainer: trainer@plprojects.co.uk / Trainer1234!")
    print("Observer: observer@plprojects.co.uk / Observer1234!")
    print("External Assessor: assessor@plprojects.co.uk / Assessor1234!")
    print("Learners: learner1@example.com / Learner1234! and learner2@example.com / Learner1234!")
    print("Cohort token: PFQ2026A")


if __name__ == "__main__":
    seed()
