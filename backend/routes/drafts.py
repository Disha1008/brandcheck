from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from auth import get_current_user, require_roles
from database import get_db
from models import Draft, Finding, Comment, Review, Guideline, ApprovedFact, Term, User
from schemas import (DraftIn, DraftUpdate, DraftOut, FindingOut, FindingAction, CommentIn,
                     CommentOut, ReviewIn, ReviewOut, HistoryOut)
from services import log
from io import BytesIO
from docx import Document
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




@router.post("/import", response_model=DraftOut, status_code=201)
async def import_document(file: UploadFile = File(...), user: User = Depends(require_roles("creator", "admin")),
                         db: Session = Depends(get_db)):
    """Import a UTF-8 .txt or text-only .docx document as a draft."""
    name = (file.filename or "").lower()
    if not (name.endswith(".txt") or name.endswith(".docx")):
        raise HTTPException(415, "Supported formats are .txt and .docx")
    raw = await file.read()
    if len(raw) > 2_000_000:
        raise HTTPException(413, "File must be 2 MB or smaller")
    try:
        if name.endswith(".txt"):
            content = raw.decode("utf-8-sig")
        else:
            document = Document(BytesIO(raw))
            content = "\n\n".join(p.text for p in document.paragraphs if p.text.strip())
    except Exception:
        raise HTTPException(400, "Could not read this document. Try saving it as UTF-8 .txt or a valid .docx file.")
    if not content.strip():
        raise HTTPException(400, "The document contains no readable text")
    title = (file.filename or "Imported draft")[:200]
    d = Draft(org_id=user.org_id, creator_id=user.id, title=title, content=content)
    db.add(d); db.flush(); log(db, d, user, "document_imported", {"filename":file.filename}, snapshot=True)
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
    facts = [dict(code=f.code, statement=f.statement, category=f.category,
                   expires_at=f.expires_at.isoformat() if f.expires_at else None,
                   source_url=f.source_url, verified_at=f.verified_at.isoformat() if f.verified_at else None)
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
            raise HTTPException(400, "No suggestion is available. Edit or dismiss this finding instead.")
        replacement, f.status = f.suggestion, "accepted"
    elif data.action == "edit":
        if not (data.edited_text or "").strip():
            raise HTTPException(400, "edited_text is required")
        replacement, f.status, f.edited_text = data.edited_text, "edited", data.edited_text
    else:
        if not (data.reason or "").strip():
            raise HTTPException(400, "Please provide a short reason for dismissing this finding")
        f.status, f.reject_reason = "rejected", data.reason.strip()

    if replacement is not None:
        # Only replace the exact checked span. Never replace the first matching sentence
        # elsewhere in a document, and refuse to apply stale suggestions.
        current = d.content[f.start_char:f.end_char]
        if current != f.sentence:
            raise HTTPException(409, "This finding is out of date. Run the check again before applying a correction.")
        d.content = d.content[:f.start_char] + replacement + d.content[f.end_char:]
        d.version += 1
        d.status = "draft"
        log(db, d, user, f"finding_{f.status}", {"finding_id": f.id, "source_id": f.source_id}, snapshot=True)
        # Other findings were based on the old text. Mark them stale instead of allowing
        # the user to apply an old suggestion to changed content.
        for other in db.query(Finding).filter(Finding.draft_id == d.id, Finding.id != f.id, Finding.status == "open").all():
            other.status = "stale"
    else:
        log(db, d, user, f"finding_{f.status}", {"finding_id": f.id, "source_id": f.source_id,
                                                   "reason": data.reason})
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
    log(db, d, user, "submitted", {"unresolved_findings": open_count, "creator_acknowledged_unresolved": open_count > 0}, snapshot=True)
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
