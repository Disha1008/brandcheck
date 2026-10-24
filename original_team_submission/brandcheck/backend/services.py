from sqlalchemy.orm import Session
from models import Draft, RevisionHistory, User


def log(db: Session, draft: Draft, user: User, action: str, details: dict | None = None, snapshot: bool = False):
    db.add(RevisionHistory(
        draft_id=draft.id, user_id=user.id, user_name=user.name, action=action,
        details=details, version=draft.version,
        content_snapshot=draft.content if snapshot else None,
    ))
