from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from auth import get_current_user, require_roles
from database import get_db
from models import Draft, Finding, Comment, Review, Guideline, ApprovedFact, Term, User
from schemas import (DraftIn, DraftUpdate, DraftOut, FindingOut, FindingAction, CommentIn,
                     CommentOut, ReviewIn, ReviewOut, HistoryOut)
from services import log
from ai_engine import check_content

router = APIRouter(prefix="/drafts", tags=["drafts"])


def get_draft(db: Session, user: User, draft_id: int) -> Draft:
    d = db.query(Draft).filter_by(id=draft_id, org_id=user.org_id).first()
    if not d:
        raise HTTPException(404, "Draft not found")
    if user.role == "creator" and d.creator_id != user.id:
        raise HTTPException(403, "You can only access your own drafts")
    return d


def own_editable(draft: Draft, user: User):
    if draft.creator_id != user.id:
        raise HTTPException(403, "Only the creator can do this")
    if draft.status in ("submitted", "approved"):
        raise HTTPException(409, f"Draft is '{draft.status}' and cannot be changed")


@router.post("", response_model=DraftOut, status_code=201)
def create_draft(data: DraftIn, user: User = Depends(require_roles("creator", "admin")), db: Session = Depends(get_db)):
    d = Draft(org_id=user.org_id, creator_id=user.id, title=data.title, content=data.content)
    db.add(d); db.flush()
    log(db, d, user, "draft_created", snapshot=True)
    db.commit(); db.refresh(d)
    return d


@router.get("", response_model=list[DraftOut])
def list_drafts(status: str | None = None, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    q = db.query(Draft).filter_by(org_id=user.org_id)
    if user.role == "creator":
        q = q.filter_by(creator_id=user.id)
    if status:
        q = q.filter_by(status=status)
    return q.order_by(Draft.updated_at.desc()).all()


@router.get("/{draft_id}", response_model=DraftOut)
def read_draft(draft_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return get_draft(db, user, draft_id)


@router.put("/{draft_id}", response_model=DraftOut)
def update_draft(draft_id: int, data: DraftUpdate, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    d = get_draft(db, user, draft_id)
    own_editable(d, user)
    if data.title is not None:
        d.title = data.title
    if data.content is not None and data.content != d.content:
        d.content = data.content
        d.version += 1
        d.status = "draft"
        db.query(Finding).filter_by(draft_id=d.id).delete()  # old findings are stale now
        log(db, d, user, "content_updated", snapshot=True)
    db.commit(); db.refresh(d)
    return d


@router.post("/{draft_id}/check", response_model=list[FindingOut])
def run_check(draft_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    d = get_draft(db, user, draft_id)
    own_editable(d, user)
    org = user.org_id
    guidelines = [dict(code=g.code, title=g.title, content=g.content, rule_type=g.rule_type,
                       keywords=g.keywords or [], fact_category=g.fact_category)
                  for g in db.query(Guideline).filter_by(org_id=org)]
    facts = [dict(code=f.code, statement=f.statement, category=f.category)
             for f in db.query(ApprovedFact).filter_by(org_id=org)]
    terms = [dict(code=t.code, approved_term=t.approved_term, banned_variants=t.banned_variants or [], note=t.note)
             for t in db.query(Term).filter_by(org_id=org)]

    results = check_content(d.content, guidelines, facts, terms)

    db.query(Finding).filter_by(draft_id=d.id).delete()
    for r in results:
        db.add(Finding(draft_id=d.id, **{k: r.get(k) for k in (
            "sentence", "start_char", "end_char", "issue_type", "severity", "explanation",
            "source_type", "source_id", "source_quote", "suggestion", "evidence_status")}))
    d.status = "checked"
    log(db, d, user, "check_run", {"findings": len(results)})
    db.commit()
    return db.query(Finding).filter_by(draft_id=d.id).order_by(Finding.start_char).all()


@router.get("/{draft_id}/findings", response_model=list[FindingOut])
def get_findings(draft_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    d = get_draft(db, user, draft_id)
    return db.query(Finding).filter_by(draft_id=d.id).order_by(Finding.start_char).all()


@router.patch("/{draft_id}/findings/{finding_id}", response_model=FindingOut)
def act_on_finding(draft_id: int, finding_id: int, data: FindingAction,
                   user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    d = get_draft(db, user, draft_id)
    own_editable(d, user)
    f = db.query(Finding).filter_by(id=finding_id, draft_id=d.id).first()
    if not f:
        raise HTTPException(404, "Finding not found")

    replacement = None
    if data.action == "accept":
        if not f.suggestion:
            raise HTTPException(400, "No suggestion to accept. Edit or reject instead.")
        replacement, f.status = f.suggestion, "accepted"
    elif data.action == "edit":
        if not data.edited_text:
            raise HTTPException(400, "edited_text is required")
        replacement, f.status, f.edited_text = data.edited_text, "edited", data.edited_text
    else:
        f.status, f.reject_reason = "rejected", data.reason

    if replacement is not None and f.sentence in d.content:
        d.content = d.content.replace(f.sentence, replacement, 1)
        d.version += 1
        f.sentence = replacement
    log(db, d, user, f"finding_{f.status}", {"finding_id": f.id, "source_id": f.source_id,
                                             "reason": data.reason}, snapshot=replacement is not None)
    db.commit(); db.refresh(f)
    return f


@router.post("/{draft_id}/submit", response_model=DraftOut)
def submit(draft_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    d = get_draft(db, user, draft_id)
    own_editable(d, user)
    if d.status != "checked":
        raise HTTPException(409, "Run the content check before submitting")
    open_count = db.query(Finding).filter_by(draft_id=d.id, status="open").count()
    d.status = "submitted"
    log(db, d, user, "submitted", {"unresolved_findings": open_count}, snapshot=True)
    db.commit(); db.refresh(d)
    return d


@router.post("/{draft_id}/review", response_model=ReviewOut)
def review(draft_id: int, data: ReviewIn, user: User = Depends(require_roles("reviewer", "admin")),
           db: Session = Depends(get_db)):
    d = get_draft(db, user, draft_id)
    if d.status != "submitted":
        raise HTTPException(409, "Draft is not waiting for review")
    if data.decision == "request_changes" and not (data.comment or "").strip():
        raise HTTPException(400, "A comment is required when requesting changes")
    r = Review(draft_id=d.id, reviewer_id=user.id, decision=data.decision, comment=data.comment)
    db.add(r)
    if data.comment:
        db.add(Comment(draft_id=d.id, user_id=user.id, user_name=user.name, body=data.comment))
    d.status = "approved" if data.decision == "approve" else "changes_requested"
    log(db, d, user, "approved" if data.decision == "approve" else "changes_requested", {"comment": data.comment})
    db.commit(); db.refresh(r)
    return r


@router.post("/{draft_id}/comments", response_model=CommentOut, status_code=201)
def add_comment(draft_id: int, data: CommentIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    d = get_draft(db, user, draft_id)
    c = Comment(draft_id=d.id, user_id=user.id, user_name=user.name, body=data.body)
    db.add(c)
    log(db, d, user, "comment_added", {"body": data.body})
    db.commit(); db.refresh(c)
    return c


@router.get("/{draft_id}/comments", response_model=list[CommentOut])
def list_comments(draft_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return get_draft(db, user, draft_id).comments


@router.get("/{draft_id}/history", response_model=list[HistoryOut])
def history(draft_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return get_draft(db, user, draft_id).history
