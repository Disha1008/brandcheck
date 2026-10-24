"""Deterministic rule checks (Pritha owns this folder).
Each function takes ONE sentence and returns a list of raw finding dicts.
Every finding must name a source_id + source_quote; the checker validates them."""
import re


def _word(pattern: str, flags=0):
    return re.compile(rf"(?<!\w){re.escape(pattern)}(?!\w)", flags)


def term_source_text(t: dict) -> str:
    return t.get("note") or f"Always write the name as '{t['approved_term']}'."


def banned_term_findings(sentence, guidelines):
    out = []
    for g in guidelines:
        if g["rule_type"] != "banned_term":
            continue
        for kw in g.get("keywords") or []:
            if _word(kw, re.IGNORECASE).search(sentence):
                out.append({
                    "issue_type": "banned_term", "severity": "medium",
                    "explanation": f"'{kw}' is not allowed in brand content ({g['title']}).",
                    "source_type": "guideline", "source_id": g["code"],
                    "source_quote": g["content"], "suggestion": None,
                    "evidence_status": "confirmed",
                })
    return out


def term_findings(sentence, terms):
    out = []
    for t in terms:
        for variant in t.get("banned_variants") or []:
            m = _word(variant).search(sentence)  # case-sensitive on purpose
            if m:
                text = term_source_text(t)
                out.append({
                    "issue_type": "product_name", "severity": "low",
                    "explanation": f"'{variant}' is an incorrect form. The approved term is '{t['approved_term']}'.",
                    "source_type": "term", "source_id": t["code"],
                    "source_quote": text,
                    "suggestion": sentence[:m.start()] + t["approved_term"] + sentence[m.end():],
                    "evidence_status": "confirmed",
                })
    return out


def tone_findings(sentence, guidelines):
    """Transparent keyword-based tone checks configured by an admin.
    For tone guidelines, keywords are phrases that should be reviewed, not proof of a violation."""
    out = []
    for g in guidelines:
        if g["rule_type"] != "tone":
            continue
        for kw in g.get("keywords") or []:
            if _word(kw, re.IGNORECASE).search(sentence):
                out.append({
                    "issue_type": "tone", "severity": "low",
                    "explanation": f"This wording may conflict with the tone guidance '{g['title']}'. Review the rule before changing it.",
                    "source_type": "guideline", "source_id": g["code"],
                    "source_quote": g["content"], "suggestion": None,
                    "evidence_status": "confirmed",
                })
    return out


def accessibility_findings(sentence, guidelines):
    out = []
    rule = next((g for g in guidelines if g.get("rule_type") == "accessibility"), None)
    if not rule:
        return out
    words = re.findall(r"\b[\w'-]+\b", sentence)
    all_caps = len(re.findall(r"[A-Z]", sentence)) >= 8 and len(re.findall(r"[a-z]", sentence)) <= 2
    if len(words) > 28:
        out.append({
            "issue_type": "readability", "severity": "low",
            "explanation": f"This sentence has {len(words)} words. Consider splitting it to make the content easier to scan; this is a readability heuristic, not a full accessibility assessment.",
            "source_type": "guideline", "source_id": rule["code"], "source_quote": rule["content"],
            "suggestion": None, "evidence_status": "confirmed",
        })
    if all_caps:
        out.append({
            "issue_type": "readability", "severity": "low",
            "explanation": "This sentence uses unusually heavy all-caps wording, which can be harder to read. Review whether normal capitalization would work.",
            "source_type": "guideline", "source_id": rule["code"], "source_quote": rule["content"],
            "suggestion": None, "evidence_status": "confirmed",
        })
    return out


def claim_findings(sentence, guidelines, facts):
    """Conservative claim policy check. A matching keyword is not proof that a
    whole claim is supported; unsupported claims are sent for human verification."""
    out = []
    for g in guidelines:
        if g["rule_type"] != "claim_policy":
            continue
        for kw in g.get("keywords") or []:
            if not _word(kw, re.IGNORECASE).search(sentence):
                continue
            # A keyword appearing in a fact is not sufficient evidence for the whole
            # claim. Only skip if the full sentence itself is contained in an approved
            # fact, a deliberately conservative exact-match check.
            from datetime import date
            active_facts = [f for f in facts if not f.get("expires_at") or f["expires_at"] >= date.today().isoformat()]
            expired_facts = [f for f in facts if f.get("expires_at") and f["expires_at"] < date.today().isoformat()]
            exact_supported = any(sentence.strip().rstrip(".!?").casefold() in
                                  f["statement"].strip().rstrip(".!?").casefold() for f in active_facts)
            if exact_supported:
                break
            relevant_expired = next((f for f in expired_facts if f.get("category") == (g.get("fact_category") or "health")), None)
            if relevant_expired:
                out.append({
                    "issue_type": "outdated_fact", "severity": "high",
                    "explanation": f"A related approved fact ({relevant_expired['code']}) expired on {relevant_expired['expires_at']}. It must be re-verified before it can support this claim.",
                    "source_type": "fact", "source_id": relevant_expired["code"],
                    "source_quote": relevant_expired["statement"], "suggestion": None,
                    "evidence_status": "not_enough_evidence",
                })
                break
            out.append({
                "issue_type": "unsupported_claim", "severity": "high",
                "explanation": (f"This sentence contains the claim trigger '{kw}'. The available approved facts "
                                "do not establish that the complete claim is supported. Verify it before publication."),
                "source_type": "guideline", "source_id": g["code"],
                "source_quote": g["content"], "suggestion": None,
                "evidence_status": "not_enough_evidence",
            })
            break
    return out
