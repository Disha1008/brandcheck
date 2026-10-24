from datetime import datetime
from typing import Literal, Optional
from pydantic import BaseModel, ConfigDict


class ORM(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class LoginIn(BaseModel):
    email: str
    password: str


class UserOut(ORM):
    id: int
    name: str
    email: str
    role: str
    org_id: int


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


class GuidelineIn(BaseModel):
    code: str
    title: str
    content: str
    rule_type: Literal["banned_term", "claim_policy", "tone"]
    keywords: list[str] = []
    fact_category: Optional[str] = None


class GuidelineOut(GuidelineIn, ORM):
    id: int


class FactIn(BaseModel):
    code: str
    statement: str
    category: str = "general"


class FactOut(FactIn, ORM):
    id: int


class TermIn(BaseModel):
    code: str
    approved_term: str
    banned_variants: list[str] = []
    note: Optional[str] = None


class TermOut(TermIn, ORM):
    id: int


class DraftIn(BaseModel):
    title: str
    content: str


class DraftUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None


class DraftOut(ORM):
    id: int
    title: str
    content: str
    status: str
    version: int
    creator_id: int
    created_at: datetime
    updated_at: datetime


class FindingOut(ORM):
    id: int
    draft_id: int
    sentence: str
    start_char: int
    end_char: int
    issue_type: str
    severity: str
    explanation: str
    source_type: str
    source_id: str
    source_quote: str
    suggestion: Optional[str]
    evidence_status: str
    status: str
    edited_text: Optional[str]
    reject_reason: Optional[str]


class FindingAction(BaseModel):
    action: Literal["accept", "reject", "edit"]
    edited_text: Optional[str] = None
    reason: Optional[str] = None


class CommentIn(BaseModel):
    body: str


class CommentOut(ORM):
    id: int
    draft_id: int
    user_id: int
    user_name: str
    body: str
    created_at: datetime


class ReviewIn(BaseModel):
    decision: Literal["approve", "request_changes"]
    comment: Optional[str] = None


class ReviewOut(ORM):
    id: int
    draft_id: int
    reviewer_id: int
    decision: str
    comment: Optional[str]
    created_at: datetime


class HistoryOut(ORM):
    id: int
    draft_id: int
    user_name: str
    action: str
    details: Optional[dict]
    content_snapshot: Optional[str]
    version: int
    created_at: datetime
