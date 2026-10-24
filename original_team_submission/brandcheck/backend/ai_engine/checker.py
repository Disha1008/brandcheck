"""Main entry point for Disha's backend:
    check_content(text, guidelines, approved_facts, terms) -> list[dict]

Pritha: replace/extend the body (e.g. add LLM judgement) but keep the signature,
the returned keys, and the final validate_findings() step."""
import re
from .rules import banned_term_findings, term_findings, claim_findings, term_source_text

SENTENCE_RE = re.compile(r"[^.!?\n]+[.!?]*")


def split_sentences(text: str):
    for m in SENTENCE_RE.finditer(text):
        s = m.group().strip()
        if s:
            start = m.start() + (len(m.group()) - len(m.group().lstrip()))
            yield s, start, start + len(s)


def validate_findings(findings, guidelines, facts, terms):
    """No source, no flag: drop any finding whose source id does not exist
    or whose quoted passage is not really inside that source."""
    sources = {("guideline", g["code"]): g["content"] for g in guidelines}
    sources.update({("fact", f["code"]): f["statement"] for f in facts})
    sources.update({("term", t["code"]): term_source_text(t) for t in terms})
    valid = []
    for f in findings:
        text = sources.get((f.get("source_type"), f.get("source_id")))
        quote = (f.get("source_quote") or "").strip().lower()
        if text and quote and quote in text.lower():
            valid.append(f)
    return valid


def check_content(text, guidelines, approved_facts, terms=None):
    terms = terms or []
    raw = []
    for sentence, start, end in split_sentences(text):
        found = (banned_term_findings(sentence, guidelines)
                 + term_findings(sentence, terms)
                 + claim_findings(sentence, guidelines, approved_facts))
        for f in found:
            f.update({"sentence": sentence, "start_char": start, "end_char": end})
        raw.extend(found)
    return validate_findings(raw, guidelines, approved_facts, terms)
