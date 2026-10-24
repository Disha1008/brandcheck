# BrandCheck functional test plan

Record actual outcomes and environment before submission. Do not report pass rates until tests have been run.

| ID | Test | Expected result |
|---|---|---|
| T01 | Login with each demo account | Correct role and workspace loaded |
| T02 | Wrong password | Clear login error; no token stored |
| T03 | Creator creates and saves draft | Draft persists after reload |
| T04 | Import valid UTF-8 .txt | Content becomes a new draft |
| T05 | Import valid .docx | Paragraph text becomes a new draft |
| T06 | Import unsupported or >2 MB file | API rejects it with a readable error |
| T07 | Trigger a banned term | Finding cites the exact guideline text and code |
| T08 | Trigger incorrect terminology | Finding identifies preferred term and offers a replacement |
| T09 | Trigger a health/claim keyword with no exact approved support | High-severity verification warning; no invented correction |
| T10 | Apply a correction to repeated sentence content | Only the checked span changes; other findings become stale |
| T11 | Try to apply a stale finding | API refuses and asks for a new check |
| T12 | Dismiss a finding without a reason | API rejects the action |
| T13 | Submit before checking | API refuses submission |
| T14 | Submit with unresolved findings | UI asks for explicit confirmation; reviewer still decides |
| T15 | Reviewer requests changes without comment | UI/API refuses |
| T16 | Reviewer approves a submitted draft | Status changes to Approved and history records action |
| T17 | Creator attempts to edit submitted/approved draft | API refuses edit |
| T18 | Non-admin adds/deletes brand sources/assets | API returns permission error |
| T19 | Add source URL and expiry date to fact | Metadata persists and displays |
| T20 | Upload approved PNG/JPEG/WebP | Asset metadata and file persist |
| T21 | Check exact same image | Exact file match is reported |
| T22 | Check unrelated image | Not-in-library warning is reported without asserting it is off-brand |
| T23 | Upload malformed image or >5 MB | API rejects it |
| T24 | Check a sentence over 28 words | Low-severity readability suggestion cites the stored readability guideline |
| T25 | Check comments/history/insights | Stored comments and revision actions display; insight counts match saved findings |
| T26 | Enable optional contextual AI with valid test key | Contextual findings are source-validated; API failure does not break deterministic checks |

## Test data

Use the fictional FreshSip seed data or deliberately synthetic text. Do not test with private client material. Keep sample text and expected findings labelled so judges can reproduce them.
