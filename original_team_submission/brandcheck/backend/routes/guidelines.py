from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from auth import get_current_user, require_roles
from database import get_db
from models import Guideline, ApprovedFact, Term, User
from schemas import GuidelineIn, GuidelineOut, FactIn, FactOut, TermIn, TermOut

router = APIRouter(tags=["brand material"])


def _add(db, model, user, data, label):
    if db.query(model).filter_by(org_id=user.org_id, code=data.code).first():
        raise HTTPException(409, f"{label} code '{data.code}' already exists")
    obj = model(org_id=user.org_id, **data.model_dump())
    db.add(obj); db.commit(); db.refresh(obj)
    return obj


def _delete(db, model, user, item_id):
    obj = db.query(model).filter_by(id=item_id, org_id=user.org_id).first()
    if not obj:
        raise HTTPException(404, "Not found")
    db.delete(obj); db.commit()
    return {"deleted": item_id}


# ---- Guidelines ----
@router.get("/guidelines", response_model=list[GuidelineOut])
def list_guidelines(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return db.query(Guideline).filter_by(org_id=user.org_id).order_by(Guideline.code).all()


@router.post("/guidelines", response_model=GuidelineOut, status_code=201)
def add_guideline(data: GuidelineIn, user: User = Depends(require_roles("admin")), db: Session = Depends(get_db)):
    return _add(db, Guideline, user, data, "Guideline")


@router.delete("/guidelines/{item_id}")
def delete_guideline(item_id: int, user: User = Depends(require_roles("admin")), db: Session = Depends(get_db)):
    return _delete(db, Guideline, user, item_id)


# ---- Approved facts ----
@router.get("/facts", response_model=list[FactOut])
def list_facts(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return db.query(ApprovedFact).filter_by(org_id=user.org_id).order_by(ApprovedFact.code).all()


@router.post("/facts", response_model=FactOut, status_code=201)
def add_fact(data: FactIn, user: User = Depends(require_roles("admin")), db: Session = Depends(get_db)):
    return _add(db, ApprovedFact, user, data, "Fact")


@router.delete("/facts/{item_id}")
def delete_fact(item_id: int, user: User = Depends(require_roles("admin")), db: Session = Depends(get_db)):
    return _delete(db, ApprovedFact, user, item_id)


# ---- Terminology ----
@router.get("/terms", response_model=list[TermOut])
def list_terms(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return db.query(Term).filter_by(org_id=user.org_id).order_by(Term.code).all()


@router.post("/terms", response_model=TermOut, status_code=201)
def add_term(data: TermIn, user: User = Depends(require_roles("admin")), db: Session = Depends(get_db)):
    return _add(db, Term, user, data, "Term")


@router.delete("/terms/{item_id}")
def delete_term(item_id: int, user: User = Depends(require_roles("admin")), db: Session = Depends(get_db)):
    return _delete(db, Term, user, item_id)
