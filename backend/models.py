from datetime import datetime, timezone, date
from sqlalchemy import String, Text, Integer, ForeignKey, DateTime, JSON, Date
from sqlalchemy.orm import Mapped, mapped_column, relationship
from database import Base


def now():
    return datetime.now(timezone.utc)


class Organization(Base):
    __tablename__ = "organizations"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200))


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    org_id: Mapped[int] = mapped_column(ForeignKey("organizations.id"))
    name: Mapped[str] = mapped_column(String(120))
    email: Mapped[str] = mapped_column(String(200), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(300))
    role: Mapped[str] = mapped_column(String(20))  # creator | reviewer | admin


class Guideline(Base):
    __tablename__ = "guidelines"
    id: Mapped[int] = mapped_column(primary_key=True)
    org_id: Mapped[int] = mapped_column(ForeignKey("organizations.id"), index=True)
    code: Mapped[str] = mapped_column(String(30))            # e.g. G-001 (the citable source ID)
    title: Mapped[str] = mapped_column(String(200))
    content: Mapped[str] = mapped_column(Text)               # the exact passage that gets cited
    rule_type: Mapped[str] = mapped_column(String(30))       # banned_term | claim_policy | tone
    keywords: Mapped[list] = mapped_column(JSON, default=list)
    fact_category: Mapped[str | None] = mapped_column(String(50), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class ApprovedFact(Base):
    __tablename__ = "approved_facts"
    id: Mapped[int] = mapped_column(primary_key=True)
    org_id: Mapped[int] = mapped_column(ForeignKey("organizations.id"), index=True)
    code: Mapped[str] = mapped_column(String(30))            # e.g. F-001
    statement: Mapped[str] = mapped_column(Text)
    category: Mapped[str] = mapped_column(String(50), default="general")
    source_url: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    verified_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    expires_at: Mapped[date | None] = mapped_column(Date, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class Term(Base):
    __tablename__ = "terms"
    id: Mapped[int] = mapped_column(primary_key=True)
    org_id: Mapped[int] = mapped_column(ForeignKey("organizations.id"), index=True)
    code: Mapped[str] = mapped_column(String(30))            # e.g. T-001
    approved_term: Mapped[str] = mapped_column(String(200))
    banned_variants: Mapped[list] = mapped_column(JSON, default=list)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)


class Draft(Base):
    __tablename__ = "drafts"
    id: Mapped[int] = mapped_column(primary_key=True)
    org_id: Mapped[int] = mapped_column(ForeignKey("organizations.id"), index=True)
    creator_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    title: Mapped[str] = mapped_column(String(200))
    content: Mapped[str] = mapped_column(Text)
    # draft | checked | submitted | approved | changes_requested
    status: Mapped[str] = mapped_column(String(30), default="draft")
    version: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now, onupdate=now)

    findings = relationship("Finding", cascade="all, delete-orphan", order_by="Finding.start_char")
    comments = relationship("Comment", cascade="all, delete-orphan", order_by="Comment.created_at")
    history = relationship("RevisionHistory", cascade="all, delete-orphan", order_by="RevisionHistory.created_at")


class Finding(Base):
    __tablename__ = "findings"
    id: Mapped[int] = mapped_column(primary_key=True)
    draft_id: Mapped[int] = mapped_column(ForeignKey("drafts.id"), index=True)
    sentence: Mapped[str] = mapped_column(Text)
    start_char: Mapped[int] = mapped_column(Integer, default=0)
    end_char: Mapped[int] = mapped_column(Integer, default=0)
    issue_type: Mapped[str] = mapped_column(String(40))      # unsupported_claim | banned_term | product_name | ...
    severity: Mapped[str] = mapped_column(String(10), default="medium")
    explanation: Mapped[str] = mapped_column(Text)
    source_type: Mapped[str] = mapped_column(String(20))     # guideline | fact | term
    source_id: Mapped[str] = mapped_column(String(30))
    source_quote: Mapped[str] = mapped_column(Text)
    suggestion: Mapped[str | None] = mapped_column(Text, nullable=True)
    evidence_status: Mapped[str] = mapped_column(String(30), default="confirmed")  # confirmed | not_enough_evidence
    status: Mapped[str] = mapped_column(String(20), default="open")  # open | accepted | rejected | edited
    edited_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    reject_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class Comment(Base):
    __tablename__ = "comments"
    id: Mapped[int] = mapped_column(primary_key=True)
    draft_id: Mapped[int] = mapped_column(ForeignKey("drafts.id"), index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    user_name: Mapped[str] = mapped_column(String(120))
    body: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class Review(Base):
    __tablename__ = "reviews"
    id: Mapped[int] = mapped_column(primary_key=True)
    draft_id: Mapped[int] = mapped_column(ForeignKey("drafts.id"), index=True)
    reviewer_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    decision: Mapped[str] = mapped_column(String(30))        # approve | request_changes
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class RevisionHistory(Base):
    __tablename__ = "revision_history"
    id: Mapped[int] = mapped_column(primary_key=True)
    draft_id: Mapped[int] = mapped_column(ForeignKey("drafts.id"), index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    user_name: Mapped[str] = mapped_column(String(120))
    action: Mapped[str] = mapped_column(String(40))
    details: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    content_snapshot: Mapped[str | None] = mapped_column(Text, nullable=True)
    version: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class BrandAsset(Base):
    __tablename__ = "brand_assets"
    id: Mapped[int] = mapped_column(primary_key=True)
    org_id: Mapped[int] = mapped_column(ForeignKey("organizations.id"), index=True)
    uploaded_by: Mapped[int] = mapped_column(ForeignKey("users.id"))
    name: Mapped[str] = mapped_column(String(200))
    storage_name: Mapped[str] = mapped_column(String(300), unique=True)
    media_type: Mapped[str] = mapped_column(String(100))
    sha256: Mapped[str] = mapped_column(String(64), index=True)
    width: Mapped[int] = mapped_column(Integer)
    height: Mapped[int] = mapped_column(Integer)
    average_color: Mapped[str] = mapped_column(String(7))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class BrandColor(Base):
    __tablename__ = "brand_colors"
    id: Mapped[int] = mapped_column(primary_key=True)
    org_id: Mapped[int] = mapped_column(ForeignKey("organizations.id"), index=True)
    name: Mapped[str] = mapped_column(String(100))
    hex_color: Mapped[str] = mapped_column(String(7))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
