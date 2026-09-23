# AUTO-RESUME MODE — DO NOT ASK THE USER FOR ROUTINE CONTINUATION DECISIONS

This project is intentionally configured so a new AI session can continue the current checkpoint without spending credits asking the user questions.

## Mandatory behavior
1. Read `AI_HANDOFF.md`, then `AGENTS.md`, then `data/ai_resume_state.json`.
2. Execute the current `NEXT ACTION` directly.
3. Do not ask the user for permission for routine offline preview/testing/package decisions already covered by the handoff.
4. Do not ask the user to upload the old preview ledger just because it is missing.
5. If the referenced preview ledger is missing, create a NEW clearly named isolated preview ledger (for example `tmp/continuation-auto-preview`) and record that it is a new ledger. Never falsely call it a continuation of a lost ledger.
6. Continue safe offline work automatically: render, test, audit, document, and package.
7. If a step is impossible because of a genuinely missing required input, do not burn the session on a question. Record the exact blocker in `AI_HANDOFF.md`, choose the safest non-blocked next action, and continue with everything else that can be completed.
8. Never change production state, upload to YouTube, trigger remote workflows, use credentials, or call paid/external generation APIs during preview/testing unless the handoff explicitly authorizes it.
9. Before credits/context/time run out, update `AI_HANDOFF.md` and `data/ai_resume_state.json` with the exact completed step and next action.

## User pre-approval recorded for this checkpoint
The user has explicitly instructed the AI to continue from the previous AI's stopping point without asking again. A new isolated preview history is pre-approved when the old preview history is unavailable.
