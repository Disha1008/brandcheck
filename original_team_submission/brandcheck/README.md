# BrandCheck – Backend (Disha)

FastAPI + PostgreSQL. Tables are created and FreshSip demo data is seeded automatically on first start.

## Setup (Windows PowerShell shown; use `source venv/bin/activate` on Mac/Linux)
1. Install Python 3.11+ and PostgreSQL. Remember the postgres password you set.
2. Create the database:  `psql -U postgres -c "CREATE DATABASE brandcheck;"`
3. ```
   cd backend
   python -m venv venv
   venv\Scripts\activate
   pip install -r requirements.txt
   copy .env.example .env      # then edit DATABASE_URL password + SECRET_KEY
   uvicorn main:app --reload
   ```
4. Open http://127.0.0.1:8000/docs

## Demo logins
| Role     | Email                 | Password     |
|----------|-----------------------|--------------|
| creator  | creator@freshsip.com  | creator123   |
| reviewer | reviewer@freshsip.com | reviewer123  |
| admin    | admin@freshsip.com    | admin123     |

In Swagger: call `POST /auth/login`, copy `access_token`, click **Authorize**, paste it.

## Endpoints
| Endpoint | Who | Purpose |
|---|---|---|
| POST /auth/login, GET /auth/me | all | login, current user |
| GET/POST /guidelines, /facts, /terms (DELETE /x/{id}) | read: all, write: admin | brand source material |
| POST /drafts, GET /drafts, GET/PUT /drafts/{id} | creator | save drafts |
| POST /drafts/{id}/check | creator | run checker, returns findings |
| GET /drafts/{id}/findings | all | results |
| PATCH /drafts/{id}/findings/{fid} | creator | `{"action":"accept"/"reject"/"edit"}` |
| POST /drafts/{id}/submit | creator | send to reviewer |
| POST /drafts/{id}/review | reviewer | `{"decision":"approve"/"request_changes","comment":"..."}` |
| GET/POST /drafts/{id}/comments | all | comments |
| GET /drafts/{id}/history | all | revision history |
| GET /insights/summary | reviewer/admin | recurring issues, unclear rules |

Status flow: `draft → checked → submitted → approved | changes_requested → (edit) draft`

## For Pritha (AI engine)
`backend/ai_engine/checker.py` → `check_content(text, guidelines, approved_facts, terms)` returns a list of dicts with:
`sentence, start_char, end_char, issue_type, severity, explanation, source_type, source_id, source_quote, suggestion, evidence_status`.
Keep `validate_findings()` as the last step: no valid source, no finding.

## Known prototype shortcuts
- Tables via `create_all` (no migrations). Demo users seeded; change secrets before real deployment.
- Re-checking a draft replaces its old findings.
