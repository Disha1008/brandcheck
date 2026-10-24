# BrandCheck architecture

## Request flow

React/Vite UI → FastAPI routes → role checks/JWT → SQLAlchemy → SQLite (default demo) or configured PostgreSQL.

Content checks combine deterministic Python rules with optional contextual review through an OpenAI-compatible chat-completions endpoint. The external call is disabled unless `OPENAI_API_KEY` is configured. All findings pass a source validator that requires a valid source ID and an exact quote from stored brand material.

## Main data models

- Organization: demo workspace boundary.
- User: creator, reviewer or admin role.
- Guideline: approved rule with source code and exact text.
- ApprovedFact: statement, category, source URL, verification time and optional expiry date.
- Term: approved term and incorrect variants.
- Draft: content, status and version.
- Finding: severity, source evidence, suggested correction and human action state.
- Comment / Review / RevisionHistory: collaboration and audit trail.
- BrandAsset: approved image metadata, SHA-256, dimensions and average color; original image is stored in backend/uploads/assets.

## Safety decisions

- Corrections only replace the exact span checked. A stale span returns an error rather than silently changing a different occurrence.
- Other open findings become stale after content changes.
- Unsupported claims are not presented as definitively false. Missing evidence leads to human verification.
- Dismissal requires a reason. Reviewers can approve or request changes; the system does not publish content.
- Uploaded text documents are limited to 2 MB; image files are limited to 5 MB and PNG/JPEG/WebP.
- Image similarity is approximate and is explicitly described as a signal, not a compliance verdict.

## Known boundaries

The demo uses `create_all` rather than migrations, local file storage and a simple demo organization. Contextual review is optional. There is no automatic source crawling, full semantic entailment engine, OCR, logo detection, color palette comparison, publishing integration or production deployment hardening.
