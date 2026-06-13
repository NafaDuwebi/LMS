from sqlalchemy.orm import Session, joinedload
from models.course import Course, Module, Material
from models.cohort import Enrolment
from models.submission import Submission
from models.assessment import Assessment
from models.cohort import AttendanceRecord


def get_learner_progress(db: Session, user_id: int, course_id: int):
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        return None

    modules = db.query(Module).options(
        joinedload(Module.materials),
        joinedload(Module.assessments),
    ).filter(
        Module.course_id == course_id, Module.is_published == True
    ).order_by(Module.order_index).all()

    total_modules = len(modules)
    completed_modules = 0
    module_statuses = []

    for mod in modules:
        submissions = db.query(Submission).filter(
            Submission.user_id == user_id,
            Submission.assessment_id.in_([a.id for a in mod.assessments]),
            Submission.passed == True,
        ).count()

        is_completed = False
        if not mod.assessments and mod.materials:
            is_completed = True
        elif mod.assessments and submissions >= len(mod.assessments):
            is_completed = True

        if is_completed:
            completed_modules += 1

        module_statuses.append({
            "module": mod,
            "materials": mod.materials,
            "assessments": mod.assessments,
            "material_count": len(mod.materials),
            "assessment_count": len(mod.assessments),
            "passed_assessments": submissions,
            "is_completed": is_completed,
        })

    progress_pct = round((completed_modules / total_modules * 100)) if total_modules > 0 else 0

    return {
        "course": course,
        "total_modules": total_modules,
        "completed_modules": completed_modules,
        "progress_pct": progress_pct,
        "module_statuses": module_statuses,
    }


def get_cohort_progress_summary(db: Session, cohort_id: int):
    from models.cohort import Cohort, Enrolment

    cohort = db.query(Cohort).filter(Cohort.id == cohort_id).first()
    if not cohort:
        return None

    enrolments = db.query(Enrolment).filter(
        Enrolment.cohort_id == cohort_id,
        Enrolment.status.in_(["enrolled", "in_progress", "completed"]),
    ).all()

    total = len(enrolments)
    completed = sum(1 for e in enrolments if e.status == "completed")
    in_progress = sum(1 for e in enrolments if e.status == "in_progress")
    withdrawn = sum(1 for e in enrolments if e.status == "withdrawn")
    scores = [e.final_score for e in enrolments if e.final_score is not None]
    avg_score = round(sum(scores) / len(scores), 1) if scores else 0
    pass_rate = round(sum(1 for s in scores if s >= (cohort.course.pass_mark if cohort.course else 55)) / len(scores) * 100, 1) if scores else 0

    return {
        "cohort": cohort,
        "total": total,
        "completed": completed,
        "in_progress": in_progress,
        "withdrawn": withdrawn,
        "avg_score": avg_score,
        "pass_rate": pass_rate,
    }
