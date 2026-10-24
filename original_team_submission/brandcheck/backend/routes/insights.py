from collections import Counter
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from auth import require_roles
from database import get_db
from models import Finding, Draft, User

router = APIRouter(prefix="/insights", tags=["insights"])


@router.get("/summary")
def summary(user: User = Depends(require_roles("reviewer", "admin")), db: Session = Depends(get_db)):
    """Recurring issues + rules creators often reject (possibly unclear guidelines)."""
    rows = (db.query(Finding).join(Draft, Finding.draft_id == Draft.id)
            .filter(Draft.org_id == user.org_id).all())
    by_type = Counter(r.issue_type for r in rows)
    per_source = Counter(r.source_id for r in rows)
    rejected = Counter(r.source_id for r in rows if r.status == "rejected")
    unclear = [{"source_id": s, "flags": n, "rejected": rejected[s], "reject_rate": round(rejected[s] / n, 2)}
               for s, n in per_source.items() if n >= 3 and rejected[s] / n >= 0.5]
    return {"total_findings": len(rows), "by_issue_type": dict(by_type),
            "per_source": dict(per_source), "possibly_unclear_guidelines": unclear}
