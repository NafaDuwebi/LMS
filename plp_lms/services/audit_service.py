from sqlalchemy.orm import Session
from models.audit import AuditLog


def log_action(db: Session, user_id: int, action: str, target_type: str = None, target_id: int = None, notes: str = ""):
    log = AuditLog(
        user_id=user_id,
        action=action,
        target_type=target_type,
        target_id=target_id,
        notes=notes,
    )
    db.add(log)
    db.flush()
    return log
