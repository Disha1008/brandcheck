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


def claim_findings(sentence, guidelines, facts):
    out = []
    for g in guidelines:
        if g["rule_type"] != "claim_policy":
            continue
        for kw in g.get("keywords") or []:
            if not _word(kw, re.IGNORECASE).search(sentence):
                continue
            # Supported only if an approved fact itself contains that claim wording
            if any(_word(kw, re.IGNORECASE).search(f["statement"]) for f in facts):
                break
            category = g.get("fact_category") or "health"
            candidates = [f for f in facts if f.get("category") == category]
            if candidates:
                fact = candidates[0]
                out.append({
                    "issue_type": "unsupported_claim", "severity": "high",
                    "explanation": (f"'{kw}' makes a claim that no approved fact supports. "
                                    f"{g['title']}. Consider an approved statement instead."),
                    "source_type": "guideline", "source_id": g["code"],
                    "source_quote": g["content"], "suggestion": fact["statement"],
                    "evidence_status": "confirmed",
                })
            else:
                out.append({
                    "issue_type": "unsupported_claim", "severity": "high",
                    "explanation": (f"'{kw}' makes a claim that no approved fact supports. "
                                    "Not enough evidence to propose a correction; a human must decide."),
                    "source_type": "guideline", "source_id": g["code"],
                    "source_quote": g["content"], "suggestion": None,
                    "evidence_status": "not_enough_evidence",
                })
            break
    return out
