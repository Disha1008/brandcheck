"""Fictional FreshSip demo data + demo users."""
from sqlalchemy.orm import Session
from auth import hash_password
from models import Organization, User, Guideline, ApprovedFact, Term


def seed(db: Session):
    if db.query(Organization).first():
        return
    org = Organization(name="FreshSip (demo)")
    db.add(org)
    db.flush()
    db.add_all([
        User(org_id=org.id, name="Admin Namrata", email="admin@freshsip.com", role="admin", password_hash=hash_password("admin123")),
        User(org_id=org.id, name="Creator Mansi", email="creator@freshsip.com", role="creator", password_hash=hash_password("creator123")),
        User(org_id=org.id, name="Reviewer Disha", email="reviewer@freshsip.com", role="reviewer", password_hash=hash_password("reviewer123")),
    ])
    db.add_all([
        Guideline(org_id=org.id, code="G-001", title="Health claims need approved proof",
                  content="Health claims need approved proof. Never say a product cures, heals, treats or prevents an illness.",
                  rule_type="claim_policy", fact_category="health",
                  keywords=["cures", "cure", "heals", "treats", "prevents", "clinically proven", "miracle", "detox"]),
        Guideline(org_id=org.id, code="G-002", title="Banned words",
                  content="Never describe FreshSip as cheap, artificial or chemical-free.",
                  rule_type="banned_term", keywords=["cheap", "artificial", "chemical-free"]),
        Guideline(org_id=org.id, code="G-003", title="Do not name competitors",
                  content="Do not mention competitor brands in any FreshSip content.",
                  rule_type="banned_term", keywords=["JuiceCo"]),
        Guideline(org_id=org.id, code="G-004", title="Keep content readable",
                  content="Use clear, readable language. Break up unusually long sentences and avoid unnecessary all-caps wording. This is a readability aid, not a full accessibility audit.",
                  rule_type="accessibility", keywords=[]),
    ])
    db.add_all([
        ApprovedFact(org_id=org.id, code="F-001", category="health", statement="FreshSip is packed with vitamin C to support your day."),
        ApprovedFact(org_id=org.id, code="F-002", category="product", statement="FreshSip Orange is made from 100% pressed oranges with no added sugar."),
        ApprovedFact(org_id=org.id, code="F-003", category="product", statement="FreshSip Orange comes in a 300 ml recyclable bottle."),
    ])
    db.add_all([
        Term(org_id=org.id, code="T-001", approved_term="FreshSip", banned_variants=["Fresh Sip", "Freshsip", "Fresh-Sip", "FreshSIP"],
             note="The product name is always written as 'FreshSip' (one word, capital S)."),
    ])
    db.commit()
