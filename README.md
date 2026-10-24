BrandCheck — Explainable AI Brand Governance
	
Live demo	LIVE_URL_HERE (free hosting: the first load can take up to ~60 s, and data created by visitors may reset when the server sleeps)
Demo logins	creator@freshsip.com / creator123 · reviewer@freshsip.com / reviewer123 · admin@freshsip.com / admin123
Team	FOUR MINDS, Thakur College of Engineering and Technology
Event	Inkloom AI problem statement, Round 2: The Build
More	DEPLOY.md to deploy your own copy · tests/ for the smoke test and labelled evaluation

BrandCheck helps a team check content against its own approved guidelines, terminology, factual sources and visual assets before publication. It is a human-in-the-loop review workspace: the app flags issues and offers suggestions, while people control edits and approval.

The exact uploaded team ZIP is preserved under original_team_submission/. The active project keeps the original FastAPI/SQLAlchemy architecture and existing features, with targeted reliability improvements, and adds a React + Vite frontend, a default SQLite setup, safer correction handling, .txt/.docx import, optional contextual AI review, approved visual asset comparison, readability heuristics, fact source/expiry metadata, and Round 2 testing/research materials.

What works in this prototype
Login with creator, reviewer and admin demo roles.
Create, edit, import, search and filter drafts.
Rule checks for banned terms, preferred terminology, configured claim policies, tone keywords and basic readability heuristics.
Findings cite the exact stored guideline, approved fact or terminology source. Unsupported claims are marked for verification instead of being labelled false or automatically rewritten.
Human-controlled Accept / Edit / Dismiss actions. Applying a suggestion replaces only the checked text span; other findings become stale and must be checked again.
Submit for review, reviewer approval or change request, comments, revision snapshots and status tracking.
Admin management for guidelines, approved facts, terminology and approved visual assets.
Source URL, verification timestamp and optional expiry date for approved facts.
Visual governance: approved image/logo library, exact-file and approximate thumbnail-hash comparisons, configurable brand-color palette comparison, alt-text quality checks, and WCAG AA text/background contrast calculation. Similarity and average-color checks are only signals, not proof of brand compliance.
Insights into finding categories and sources whose warnings are often dismissed.
Optional OpenAI-compatible contextual tone/messaging review when an API key is explicitly configured. By default, checks run locally without an external AI API.
.txt and .docx draft import. Image upload supports PNG, JPEG and WebP, max 5 MB.
Quick start (Windows)

Requirements: Python 3.11+ and Node.js 20+.

1. Start the backend

Open PowerShell in the project folder:

powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
Copy-Item .env.example .env
uvicorn main:app --reload

SQLite is the default, so PostgreSQL is not required for the demo. The database file backend/brandcheck.db is created on first start. The API is at http://127.0.0.1:8000; interactive API docs are at http://127.0.0.1:8000/docs.

If PowerShell blocks activation, use Set-ExecutionPolicy -Scope Process Bypass in that terminal, or run .venv\Scripts\python.exe -m pip install -r requirements.txt and .venv\Scripts\python.exe -m uvicorn main:app --reload without activating.

2. Start the frontend in a second terminal

From the project folder:

powershell
cd frontend
npm install
npm run dev

Open http://127.0.0.1:5173.

If your backend runs at a different address, create frontend/.env with VITE_API_URL=http://127.0.0.1:8000 and restart Vite.

Demo logins
Role	Email	Password
Creator	creator@freshsip.com	creator123
Reviewer	reviewer@freshsip.com	reviewer123
Admin	admin@freshsip.com	admin123

The demo brand FreshSip and all example product facts are fictional. Use them for demonstration only.

Optional contextual AI

The app does not call an external AI service by default. To enable contextual tone/messaging checks, add your provider's key to backend/.env:

env
OPENAI_API_KEY=your_key_here
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_MODEL=gpt-4o-mini

This optional mode sends the draft text and relevant brand sources to the configured OpenAI-compatible API. Do not use confidential material unless your team has permission and has reviewed the provider's terms/privacy settings. Never commit .env. If the key is absent or the request fails, deterministic checks still run. A model's output is still a suggestion and requires human review.

Round 1 commitments: what Round 2 delivers (baseline)
Evidence-linked findings and uncertainty: every saved finding must cite an existing source ID and an exact source quote. Unsupported claims are shown as needing verification rather than asserted to be false.
Recurring-issues dashboard and unclear-guideline flags: reviewer/admin insights aggregate issue types and highlight sources that meet the current repeated-dismissal threshold. The threshold is a heuristic, not proof that a guideline is wrong.
Accessibility and visual checks: a quick check evaluates entered alt text and WCAG AA contrast for chosen foreground/background colors; the approved asset library checks exact/similar image files and compares average image color against an admin-configured palette. These are intentionally limited checks, not a full automated WCAG, OCR or logo-recognition system.
Review workflow
Sign in as creator and create a draft or import .txt / .docx.
Run Check content. Findings show severity, explanation, source ID, source quote and optional correction.
Accept a suggestion, edit the replacement, or dismiss with a reason. Applying a change invalidates other findings from the old version; run the check again.
Submit the checked draft. The UI warns if findings remain open.
Sign in as reviewer and open Review queue. Add a comment and approve or request changes.
Sign back in as creator to revise, save, re-check and resubmit if changes were requested.
Sign in as admin to manage guidelines, approved facts, terminology and approved visual assets.
Round 3 roadmap (our three committed improvements)
Semantic evidence verification: retrieval plus model judgement, still validated against real source IDs and exact quotes, to catch the paraphrased and numeric claims the rules miss. Reported as precision/recall against the current rules on a larger labelled set.
Guideline-health analytics and audit reporting: per-rule history of flagged / accepted / dismissed / overruled, suggested clearer wording for admins to approve, trends, and exportable audit reports.
Real image and accessibility compliance: OCR on images, contrast measured on actual pixels, logo detection against approved logos, and pixel-level palette checks.
Measured results (run it yourself: python tests/labelled_eval.py)

A small team-written labelled set of 20 FreshSip sentences (not representative of real-world content): 11 true positives, 0 false flags, 4 missed issues -> precision 1.00, recall 0.73. The misses are paraphrased or numeric claims such as "eliminates colds overnight", "helps prevent the flu", and an upper-case brand name. This is the known weakness of keyword/rule matching and is the reason semantic verification is our first Round 3 improvement. The checker is strict by design: it flags only what a stored source supports.

Known limitations
The default checker is deterministic and rule-based, not a general-purpose semantic fact verifier. Contextual AI review is optional and depends on a configured API provider/key.
Fact expiry is metadata and expired facts are not treated as supporting evidence by the claim checker. This prototype does not crawl source URLs to re-verify facts automatically.
Visual checks compare image file hashes and simple thumbnail hashes. They are not a complete logo detector, OCR system, color-palette validator or design-quality judge.
Readability checks use simple sentence-length and all-caps heuristics. The separate accessibility quick check evaluates user-entered alt text and selected text/background colors; it does not inspect text embedded inside uploaded images or automatically determine whether alt text describes an image correctly.
Local SQLite and local file storage are for a hackathon demo. Production deployment needs migrations, stronger secrets, backups, HTTPS, rate limiting, access review, retention controls and deployment-specific file storage.
The backend uses create_all for a fresh demo database; it is not a production migration strategy. If you change the data models after creating a local DB, back up the DB and recreate the demo DB or add proper migrations.
User research, interviews, accuracy rates and time-saved claims must be reported from actual evidence. The included research documents are templates/plans, not fabricated results.
Project structure
text
brandcheck/
  backend/       FastAPI API, database models, rule checker, optional AI, image asset endpoints
  frontend/      React + Vite web app
  docs/          Architecture, test plan, demo script and Round 2 checklist
  research/      Survey/interview log and analysis template
  tests/         Backend smoke tests
Responsible use, tools and disclosure
AI in the product: none by default. All checks in the live demo are deterministic rules. The optional contextual review only runs if an operator sets an API key.
AI in development: AI coding assistants (Claude by Anthropic, and similar tools) were used to help write and review parts of the code, tests and documentation. The team set the scope and design, ran the product and tested it.
Original scaffold: the first team backend is preserved unchanged in original_team_submission/; the active project extends it.
Data: all brand data (FreshSip) is fictional. Do not enter confidential content.
Libraries and services: React, Vite, FastAPI, Uvicorn, SQLAlchemy, Pydantic, PyJWT, python-docx, Pillow, httpx; hosted with Docker on Render.
Contributions: individual work is visible in the commit history.