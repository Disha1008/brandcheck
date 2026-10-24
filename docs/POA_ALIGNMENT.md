# Round 1 POA → current prototype mapping

The three named improvements in the FOUR MINDS Round 1 Plan are preserved as explicit work items.

| POA commitment | Current implementation | Honest boundary |
|---|---|---|
| 1. Every finding cites a source; show “not enough evidence” when evidence is missing | `validate_findings()` verifies that the source ID exists and the exact quote occurs in the stored source. Claim warnings can use `not_enough_evidence`; corrections are not invented for those cases. | Deterministic checks are not a general-purpose semantic fact-verification system. Optional LLM findings are also source-validated. |
| 2. Recurring-issues dashboard and possibly unclear guideline flags | `/insights/summary` aggregates finding types and flags source IDs with at least 3 findings and a dismissal rate of at least 50%. | The thresholds are heuristics; they do not prove a guideline is wrong. More user data is required. |
| 3. Accessibility and visual checks: alt text, text contrast, logo and color rules | Accessibility quick check evaluates whether alt text is missing/generic/long and calculates WCAG AA contrast ratio for selected text/background colors. Admins can configure a brand color palette and approved asset library; uploads are checked for exact-file and approximate image/color similarity. | Alt text is entered by the user and is not semantically verified. Image checks do not perform OCR, logo localization, pixel-level palette analysis or a full WCAG audit. |

## Other Round 2 core commitments

- Login and creator/reviewer/admin roles.
- Guideline, approved fact, terminology and visual asset management.
- Draft creation and `.txt`/`.docx` import.
- Text review with cited findings and suggested corrections.
- Human-controlled accept/edit/dismiss with stale finding protection.
- Comments, submit/review/approve/request-changes workflow and revision history.
- Insights, installation instructions, architecture explanation, dependency/service disclosure and smoke-test script.
- Research log template and a preliminary survey summary based only on the two responses reported by the team on 24 October 2026.

## Round 2 submission items outside the code

A judge-accessible repository/deployed link, actual screenshots, the real survey/interview results, labelled test outcomes, and the team contribution statement still need to be prepared by the team. They are not fabricated or represented as completed in this ZIP. Confirm the event's official build-window rules and disclose reused scaffold/AI-assisted work as required.
