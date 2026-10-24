"""Optional OpenAI-compatible contextual review. Disabled unless explicitly configured.
No content leaves the local app unless OPENAI_API_KEY is set by the operator.
"""
import json, os
import httpx


def llm_findings(text, guidelines, facts, terms):
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key:
        return []
    base = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1").rstrip("/")
    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    source_list = []
    for g in guidelines:
        source_list.append({"source_type":"guideline","source_id":g["code"],"quote":g["content"],"title":g["title"],"type":g["rule_type"]})
    from datetime import date
    for f in facts:
        if f.get("expires_at") and f["expires_at"] < date.today().isoformat():
            continue
        source_list.append({"source_type":"fact","source_id":f["code"],"quote":f["statement"],"title":"Approved fact"})
    for t in terms:
        source_list.append({"source_type":"term","source_id":t["code"],"quote":t.get("note") or f"Always write the name as '{t['approved_term']}'.","title":"Approved terminology"})
    if not source_list:
        return []
    prompt = {
      "task":"Review content against the supplied brand sources. Focus on tone, messaging, unsupported claims and contradictions. Do not do generic proofreading.",
      "rules":["Use only the supplied sources.","Do not claim a statement is false merely because evidence is missing.","Every finding must cite one exact source_id and quote copied verbatim from that source.","If no source supports a concern, omit it.","Do not invent replacement facts.","Suggested correction must preserve the author's intent; use null if uncertain."],
      "output_schema":{"findings":[{"sentence":"exact sentence from content","issue_type":"tone|messaging|unsupported_claim|fact_conflict","severity":"low|medium|high","explanation":"plain language","source_type":"guideline|fact|term","source_id":"exact id","source_quote":"exact quote from source","suggestion":"string or null","evidence_status":"confirmed|not_enough_evidence"}]},
      "sources":source_list,"content":text
    }
    try:
        response = httpx.post(base + "/chat/completions", headers={"Authorization":f"Bearer {api_key}"},
            json={"model":model,"temperature":0,"response_format":{"type":"json_object"},
                  "messages":[{"role":"system","content":"You are a conservative brand-governance reviewer. Return valid JSON only."},
                              {"role":"user","content":json.dumps(prompt, ensure_ascii=False)}]}, timeout=25)
        response.raise_for_status()
        payload = response.json()["choices"][0]["message"]["content"]
        data = json.loads(payload)
        allowed = {"tone","messaging","unsupported_claim","fact_conflict"}
        result=[]
        for item in data.get("findings", []):
            sentence = item.get("sentence", "")
            if not sentence or sentence not in text or item.get("issue_type") not in allowed:
                continue
            if item.get("source_type") not in ("guideline","fact","term"):
                continue
            item["start_char"] = text.find(sentence)
            item["end_char"] = item["start_char"] + len(sentence)
            result.append(item)
        return result
    except Exception:
        # A network/model failure must not prevent the deterministic checker from working.
        return []
