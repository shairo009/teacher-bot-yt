## CURRENT TASK — Shorts / policy / reliability audit (2026-09-23)
- User requested direct fixes, no routine questions, and live handoff updates. This checkpoint supersedes ALL historical NEXT ACTION sections below.
- Source: finalteacher-bot-yt-final-continuation.zip; original archive untouched. Working copy: /home/user/webapp/teacher-bot-yt-main.
- Scope: offline Python/FFmpeg bot audit, regression tests, current official YouTube guidance, fixed-source delivery. Not a Cloudflare application.
- Initial confirmed findings: uploader ignores made_for_kids, formats IST as UTC for scheduling, invents recording dates, installs dependencies at import, defaults uploads to public; technical auditor has no 180-second maximum. These require fixes and tests.
- Four supplied MP4s are only 3-second previews, not complete published Shorts; viral performance cannot be predicted from these or guaranteed by code.
- Safety: no uploads, OAuth, workflow triggers or external media-generation calls; production histories must remain unchanged.
- Baseline independently verified: 103 tests PASS in 19.047s (Python unittest). No credentials/network generation used.
- Official sources checked on 2026-09-23: YouTube help 15424877 (Shorts), 1311392 (monetization), 14328491 (synthetic disclosure), 9528076 (audience), 2801973 (spam). IMPORTANT: current Shorts help announces a Content ID change effective 2026-09-24; do not copy the old over-60-second automatic-block rule as timeless guidance.
- Implemented, pending regression: uploader private-first; explicit audience/disclosure booleans; media+metadata-bound editorial review for public/unlisted/scheduled releases; proper UTC scheduling; no invented recording dates/timestamps, no import-time pip, no automatic OAuth browser. Metadata validation before authentication.
- Implemented, pending regression: quality gate now checks <=180 seconds, sample aspect/rotation and audio duration; default minimum is 1 second (63 was a legacy product setting, not YouTube policy).
- Implemented, pending visual QA: mobile-sized three-beat model explanations replace scrolling pseudo-code; pixel-measured long titles; morphology-specific explanations for selected families; truthful Python labels in 2D as well as 3D. This does NOT eliminate channel-level repetitive-content risk.
- NEXT: quarantine unlicensed legacy Real Draw publishing and fix its preview failure/path handling; remove automatic high-frequency schedule; add regression coverage, run full-length offline preview, update README and package. Do not reset any histories.

## Historical: Autonomous continuation progress — final package completed (2026-09-22)
- Completed the four requested continuation previews: **306, 401, 604, 339**. All four passed the local 3-second quality/decode gate and were visually inspected via contact sheets.
- Full regression suite: **103 tests, RC 0, PASS**. `python -m compileall -q src tests`: PASS.
- Production-state comparison against the input archive: all pre-existing production `data/` files are byte-for-byte unchanged; only the intentionally updated `data/ai_resume_state.json` checkpoint differs.
- Final deliverable built as `/mnt/data/teacher-bot-yt-final-continuation.zip`, ZIP integrity verified with `unzip -t`. It contains source plus approved preview MP4s, quality reports and contact sheets, while excluding credentials, caches, locks, raw frame sequences and temporary reel directories.
- No YouTube upload, GitHub workflow trigger, OAuth credential, or external generation API was used.
- **NEXT ACTION for any future AI:** read this handoff and `data/ai_resume_state.json`; the continuation preview checkpoint is complete. Do not rerun completed preview work unless a regression is observed. If development resumes, choose a new explicit task and create a new isolated preview ledger.

# 🚨 NEXT AI — AUTONOMOUS CONTINUATION MODE

**User instruction (authoritative): do not ask routine continuation questions. Start the remaining work immediately from the latest checkpoint.**

## No-question rule
- Read this file, `AGENTS.md`, and `data/ai_resume_state.json` first.
- Execute `NEXT ACTION` directly.
- Do not ask for the old preview-history upload.
- If the old preview ledger is missing, create a NEW isolated ledger such as `tmp/continuation-auto-preview` and record it as a new ledger. Do not pretend it is the lost ledger.
- Do not spend the session asking for routine approvals that are already covered by the safe offline testing rules.
- Continue all non-blocked offline work automatically and update this handoff after every meaningful step.

## Recovery checkpoint — 2026-09-22
- The prior package had 103 PASS regression coverage but the old `tmp/continuation-7-preview` ledger and retained pre-fix Seahorse artifacts were not present in the archive.
- The user has now explicitly pre-approved starting a **new isolated preview history** if the old ledger is unavailable, so no user question is required.
- Production `data/` state, credentials, upload history, OAuth, remote triggers, and external generation APIs remain protected and must not be changed during preview/testing.

## NEXT ACTION — EXECUTE WITHOUT ASKING
1. Use the existing 103-test regression baseline as the starting point.
2. Create or reuse a clearly named NEW preview ledger, preferably `tmp/continuation-auto-preview`, because the old ledger is unavailable in this archive.
3. Render catalogue IDs **306 → 401 → 604 → 339** sequentially through that same new ledger.
4. For each result, inspect the MP4 and run the quality/FFmpeg decode checks.
5. Verify production `data/` files remain unchanged.
6. Record exact results after each meaningful step in this file and `data/ai_resume_state.json`.
7. Package the source + approved previews only after the checks pass, excluding credentials, caches, and frame sequences.
8. If one animal cannot be rendered, diagnose/fix it and continue automatically; do not stop to ask the user.

Suggested safe commands:
```bash
OPENBLAS_NUM_THREADS=1 python src/animal_short_generator.py --animal-id 306 --renderer 3d --quality standard --duration 3 --dry-run --no-research --history-dir tmp/continuation-auto-preview --max-unique-retries 1
OPENBLAS_NUM_THREADS=1 python src/animal_short_generator.py --animal-id 401 --renderer 3d --quality standard --duration 3 --dry-run --no-research --history-dir tmp/continuation-auto-preview --max-unique-retries 1
OPENBLAS_NUM_THREADS=1 python src/animal_short_generator.py --animal-id 604 --renderer 3d --quality standard --duration 3 --dry-run --no-research --history-dir tmp/continuation-auto-preview --max-unique-retries 1
OPENBLAS_NUM_THREADS=1 python src/animal_short_generator.py --animal-id 339 --renderer 3d --quality standard --duration 3 --dry-run --no-research --history-dir tmp/continuation-auto-preview --max-unique-retries 1
```

## Hard safety rules
- Never clear/reset a history to make an animal pass.
- Never lower uniqueness or visual-quality thresholds.
- Never upload to YouTube, trigger GitHub Actions, use OAuth/credentials, or call paid/external generation APIs during preview/testing.
- Never delete a retained diagnostic merely to make tests pass.
- Update `AI_HANDOFF.md` after every meaningful render/test and before the session/credits end.

### Current checkpoint (inherited; recovery checkpoint above takes precedence)
- Current archive lineage: **eighth continuation package**.
- The previous AI completed the habitat-planner repair for Pacific Seahorse and recorded **103 PASS**.
- The previous diagnostic seahorse render is intentionally retained in `tmp/continuation-7-preview`; **do not delete it just to make tests pass**.
- Production history/state, credentials, workflow triggers, and uploads must remain untouched during this continuation.

### NEXT ACTION — EXECUTE THESE IN ORDER
Use the **same preview history ledger** for every render:
`tmp/continuation-7-preview`

1. Render the corrected Pacific Seahorse (catalogue ID **306**) through the same ledger.
2. Then render unused catalogue ID **401**.
3. Then render unused catalogue ID **604**.
4. Then render unused catalogue ID **339**.
5. For each result: inspect the MP4, run the quality audit/FFmpeg decode checks, and record the exact result in this file.
6. Verify the preview work did not modify production `data/` state.
7. Only after the above is complete, package the source + approved previews while excluding caches, credentials, and generated frame sequences.

Suggested safe command shape (run from this `teacher-bot-yt-main` folder):
```bash
OPENBLAS_NUM_THREADS=1 python src/animal_short_generator.py --animal-id 306 --renderer 3d --quality standard --duration 3 --dry-run --no-research --history-dir tmp/continuation-7-preview --max-unique-retries 1
OPENBLAS_NUM_THREADS=1 python src/animal_short_generator.py --animal-id 401 --renderer 3d --quality standard --duration 3 --dry-run --no-research --history-dir tmp/continuation-7-preview --max-unique-retries 1
OPENBLAS_NUM_THREADS=1 python src/animal_short_generator.py --animal-id 604 --renderer 3d --quality standard --duration 3 --dry-run --no-research --history-dir tmp/continuation-7-preview --max-unique-retries 1
OPENBLAS_NUM_THREADS=1 python src/animal_short_generator.py --animal-id 339 --renderer 3d --quality standard --duration 3 --dry-run --no-research --history-dir tmp/continuation-7-preview --max-unique-retries 1
```

### Hard rules for the next AI
- **Do not** clear or reset the preview ledger to make a requested animal pass.
- **Do not** lower uniqueness thresholds or bypass semantic/visual/history barriers.
- **Do not** upload to YouTube, trigger GitHub Actions, use OAuth/credentials, or make paid/external generation API calls during testing.
- **Do not** erase the retained pre-fix Pacific Seahorse record.
- Update `AI_HANDOFF.md` **after each meaningful render/test** and before the session/credits end.
- When finished, replace the `NEXT ACTION` section with the new exact next action so the following AI can continue without guessing.

### Resume protocol
1. Read this section.
2. Read `AGENTS.md`.
3. Inspect the current `NEXT ACTION` only; do not redo older checkpoints unless a current test proves they regressed.
4. Execute the next action.
5. Record exact commands, outputs, files changed, and the next action here before stopping.


# Live AI handoff — READ THIS FIRST

## Active continuation — seventh uploaded archive, 2026-09-22
- Input: `/home/user/uploaded_files/7genspark-653c0fec-cdaa-40b1-bd2e-035f9f6937b2-main.zip`, untouched.
- Restored 80 nested files to `/home/user/webapp/teacher-bot-yt-main/`; outer Hono source untouched.
- Independently ran baseline: `OPENBLAS_NUM_THREADS=1 python -m unittest discover -s tests -v` -> **99 PASS in 10.565s**. The 12 generic-rig repairs/tests already exist in this input, not newly implemented here.
- Workflow already has updated 687-catalog guidance; README is still five-species-only and must be corrected.
- README corrected to distinguish five dedicated rigs from 687 supported generic catalogue entries; CLI/workflow already had the correct generic-3D guidance.
- Found and fixed a real planner bug: substring `horse` sent PACIFIC SEAHORSE to `farm`. In `src/unique_animal_generation_skill.py`, explicit aquatic class now wins over misleading fragments; farm/cat overrides require appropriate class and complete name words. No uniqueness thresholds or journal schema changed.
- Added four HabitatProfileTests, covering aquatic catalogue entries, seahorse/cowfish/lionfish, terrestrial name collisions, retained domestic overrides and unchanged history barriers. Full suite -> **103 PASS in 18.334s**.
- Initial pre-fix diagnostic preview: `tmp/reel_0306_704b372eb901487c59fb501d6b8c67c5/pacific_seahorse_short.mp4` (audit passed but semantically wrong farm habitat). Its completed record is RETAINED in `tmp/continuation-7-preview`; do not erase it to make the corrected preview pass.
- NEXT: render corrected 306, then unused 401, 604 and 339 sequentially through that SAME ledger, inspect/audit and package. No uploads, credentials, workflow triggers or production-state changes allowed.

## Previous repair checkpoint — 2026-09-22
- Input: `/home/user/uploaded_files/OGteacher-bot-yt-generic-687-animals-updated.zip`; original left untouched.
- Editable project: `/home/user/webapp/teacher-bot-yt-main/` (older workspace paths below are historical).
- Baseline: `OPENBLAS_NUM_THREADS=1 python -m unittest discover -s tests -v` -> 87 PASS, 6.140s, Python 3.13.14. FFmpeg available.
- Inspection found generic-renderer coverage gaps not exercised by the inherited five-rig tests: cephalopod/jellyfish profiles fall through to four-legged mammal geometry; several families have no articulated animation; README/workflow still describe five-species-only support.
- Implemented `src/animal_3d_renderer.py` repair: explicit morphology-first dispatch, separate cephalopod/jellyfish anatomy, dedicated rig selection by exact name (not `turtle`/`spider` collisions), animated generic families, marine flukes/fins, decapod legs/claws, elephant trunk/tusks, rhino midline horns, articulated terrestrial legs and bounded nested catalog proportions. Unknown explicit morphology now fails closed.
- Added 12 `GenericRendererTests` in the existing test file: all 687 entries build finite positive orthonormal geometry, all 43 morphology families render/animate, appendage counts and regression coverage for dispatch, metadata, determinism and invalid motion time.
- Verification after repair: `OPENBLAS_NUM_THREADS=1 python -m unittest discover -s tests -v` -> 99 PASS, 8.785s. These are structural/render tests, NOT an anatomical-realism certification.
- NEXT: synchronize CLI/workflow/README guidance; render consecutive unused species through ONE preview ledger, inspect visual output and audit MP4s. Preserve all production state and duplicate/visual gates.
- No upload, OAuth, workflow trigger or external generation API used. This is an offline Python/FFmpeg project, not a Cloudflare web app.

## User requirement (Hinglish)
"Problem dekho aur solve karo. Existing 2D environment mein realistic 3D animals banao. Original se alag jagah edit karo. Ek alag file live update karo taaki credits khatam hone par next AI wahi se kaam start kar sake. Next AI bhi apne credits khatam hone se pehle file update karta rahe."

## Mandatory continuation protocol for EVERY next AI
1. Read this file and AGENTS.md before changing anything.
2. Work only in the edited project, never overwrite the original uploaded ZIP.
3. Update this file AFTER EACH meaningful change/test, not only at the end. Before credits/context/time run out, save current state, exact errors, commands, files changed and the NEXT action here.
4. Never claim a test passed if not run. Distinguish procedural 3D from photorealism.
5. Never upload videos, trigger workflows, use OAuth tokens or modify upload history during testing. Use --dry-run --no-research.
6. Commit tested milestones. Do not commit credentials, caches or generated frame sequences.
7. This is checkpoint-based live documentation, not a background service that keeps running after the session ends.

## Locations
- Current original input: /home/user/uploaded_files/5genspark-5019d8db-c465-4604-9558-c21ab78c5ecd-main.zip (untouched).
- Restored only the nested workspace into /home/user/webapp; the outer Hono template was not overwritten.
- Isolated editable project: /home/user/webapp/workspace/teacher-bot-yt-main/.
- Outer /home/user/webapp contains the platform Hono template and git repository; it is NOT the Python bot.
- Once downloaded/extracted, run all commands from the folder containing this file.

## Architecture and constraints
Python + Pillow + FFmpeg offline video generation; scheduled GitHub Actions and optional YouTube API upload. NOT a deployable Cloudflare runtime: requires filesystem and subprocesses. Existing renderer is Pillow 2D, not JavaScript/WebGL despite on-screen labels. 687 catalog entries do not imply 687 authentic rigs. No paid media-generation services authorized or used.

## Current checkpoint: fifth continuation complete (2026-09-22)
- Restored 80 nested project files only; outer Hono template and input ZIP untouched.
- Baseline: `OPENBLAS_NUM_THREADS=1 python -m unittest discover -s tests -v`: 80 PASS in 6.584s. Real local-git tests included; YouTube remains mocked.
- README already describes the 80-test milestone; earlier instructions calling it stale are historical. Prior generated MP4s and preview ledger are not included in the input archive, so recreate Tiger then Turtle using one fresh isolated preview ledger.
- COMPLETED: actual Tiger/Turtle previews on one ledger, 87 passing tests, workflow preview hardening, production-state byte comparison, updated documentation and delivery ZIP. Details at the final milestone below.
- NEXT IMPLEMENTATION: add unused species-specific rigs and review visual quality/diversity, or separately harden legacy Real Draw internals. Do not repeat the completed verification milestone unless source changes require it.

## Historical checkpoint: initial 28 offline tests PASS
- Ran `python -m unittest discover -s tests -v`: 28 tests passed in 1.677 seconds.
- Tests use temporary state and mocked uploader/encoder; these are NOT end-to-end MP4 tests.
- NumPy, Pillow, unittest/pytest and FFmpeg are available in this sandbox.
- Follow-up inspection found malformed JSON registries still fail open and uploader tags still falsely describe JavaScript. Fix and extend tests before rendering previews.
- NEXT: strict state validation, truthful upload metadata, short dry-run MP4 and workflow/docs completion.

### Original issues addressed by the imported implementation
Verified by previous code inspection:
- Upload failure/missing credentials still marks animals used and mutates progress/history/buffer.
- Final selection fallback bypasses base-noun duplicate guard.
- Explicit --animal-id only warns on duplicates and allows upload.
- get_used_base_nouns ignores permanent used_animals registry.
- Candidate dHash uses cropped viewport; stored dHash uses full poster (incomparable).
- Visual verification exceptions fail open (accept candidate).
- Reused frame directories can leave stale frames in shorter reruns.
- Zero-distance IK divides by zero; duration is not validated.
- README says 8.8s wildlife photos; actual generator renders 25s procedural anatomy.
- Workflow animal ID help is incorrect (0 is African Lion, 1 Tiger).

## Implementation plan
1. Correct these safety/correctness issues and add offline regression tests.
2. Add isolated NumPy CPU 3D renderer with actual camera-space depth/ray intersections, materials, lighting and animation; composite into existing 2D layout. Explicit species support and explicit legacy fallback, no generic dog pretending to be every animal.
3. Add CLI renderer/quality controls and safe preview workflow. Keep external assets/photoreal rig work clearly marked as future work.
4. Run tests, render review images and short MP4, package edited project and update this file with exact outcomes.

## Implemented checkpoint
- Added src/animal_3d_renderer.py: actual XYZ analytical ellipsoids, orthographic ray casting, depth buffer, normals, lighting, material patterns, soft approximate contact shadows, deterministic articulated motion and camera yaw.
- Five EXACT species supported: TIGER (ID 1), AFRICAN LION (ID 0), GREEN SEA TURTLE (ID 104), MEXICAN REDKNEE TARANTULA (ID 465), LEOPARD GECKO (ID 122). Other species are explicitly legacy 2D in auto mode; strict 3d refuses unsupported species.
- Integrated into existing 2D grid/code-card layout in generative_dragon_engine.py; corrected false 60 FPS/Vanilla JS labels. 3D code panel is a labelled pipeline sketch, not executable sample code.
- Added CLI --renderer auto|2d|3d and --quality draft|standard|high. Added NumPy requirement.
- Addressed upload-state, duplicate fallback, viewport hash scope, fail-open visual checks, stale frames, duration and explicit ID validation, zero-distance IK.
- Compilation passed. Five-species contact sheet rendered in tmp/review/animals_3d_contact_sheet.png.
- Independent visual review: clean framing/no clipping; clearly procedural/toy-like, NOT photorealistic. Current limitations include simplified anatomy, segmented mane/limbs and synthetic patterns. Do not market this as photorealism. Detailed licensed rigged assets plus Blender/PBR rendering would be the next realism milestone.
- NEXT: run regression tests, short dry-run videos, inspect full poster layout; update docs/workflow and package.

## Continuation checkpoint: safety regression milestone
- Strict JSON reads now distinguish absent first-run state from corrupt/unreadable state; registry and progress/history shape validation block unsafe retries. Registry names are normalized on read.
- dHash accepts only 16 hexadecimal characters. Malformed hashes fail closed.
- Upload titles/descriptions/tags now describe Python procedural rendering in both modes; no JavaScript tags for generated 3D videos.
- FFmpeg encoder limited to two threads to avoid unbounded CPU/memory on shared runners.
- Added 10 regression tests: `python -m unittest discover -s tests -v` PASS, 38 tests in 1.581s. `python -m compileall -q src tests` PASS.
- Changed: src/animal_short_generator.py, src/animal_researcher.py, src/animal_3d_renderer.py, tests/test_animal_pipeline.py.
- NEXT: generate five-species contact sheet/full poster and short CLI MP4 with `--dry-run --no-research`; compare every data file against ZIP bytes afterward. No real uploads performed.

## Continuation checkpoint: actual preview and state verification
- Rendered high-quality layers and full 1080x1920 posters for all five species in `tmp/review/`.
- Ran `OPENBLAS_NUM_THREADS=1 python src/animal_short_generator.py --animal-id 1 --renderer 3d --quality standard --duration 3 --dry-run --no-research` successfully.
- `tmp/reel_0001/tiger_short.mp4`: ffprobe reports H.264, 1080x1920, 30/1 FPS, 90 frames, AAC, exactly 3.000 seconds. Full `ffmpeg -v error -i ... -f null -` decode passed.
- Compared every original `data/` file against uploaded ZIP bytes: all 13 unchanged.
- Visual review: five species recognizable, long tarantula heading fits, no layout clipping. Primitive/toy-like anatomy remains. No claim of photorealism or seamless looping. Review model gave contradictory leg counts between sheet and poster; code explicitly constructs eight tarantula legs plus two pedipalps, with viewpoint occlusion. Approximate shadows and overlapping primitives remain limitations, not a validated biological simulation.
- IMPORTANT REAL-DATA BLOCKER: all five supported base nouns are already used. Current pixel-difference scores versus recent buffer: Tiger 3.99%, Lion 4.27%, Turtle 3.84%, Tarantula 1.58%, Gecko 4.33% (required >=20%). Hamming distances 20-24 pass, but pixel policy does not. Strict 3D cannot currently select an uploadable supported animal. Explicit dry-run IDs work; NEVER clear history or lower guards to fake success. Next production milestone needs unused authentic species rigs and a separately reviewed diversity metric/background strategy.
- Workflow updated locally with manual preview default true, renderer/quality/duration inputs, correct IDs, tests before render, no research or credentials in dry-run, boolean-safe save condition. Existing schedule remains enabled in source; it was NOT triggered here. GitHub validation pending.
- NEXT: validate workflow syntax/commands locally, correct README, package previews + source (exclude caches/frames/credentials), commit and supply links.

## 2026-09-22 unique generation checkpoint (in progress)
- New input: `/home/user/uploaded_files/2genspark-92ec0500-83dc-4b4d-910f-cf93f78c2174-main.zip`, left untouched. Restored nested project at the same editable location above.
- Read entire handoff and AGENTS, generation, renderer, history, quality auditor, uploader and both workflows. Baseline `python -m unittest discover -s tests -v`: 38 PASS (2.035s).
- Implementing reusable `src/unique_animal_generation_skill.py`, durable history + publish-intent, history-aware selection, real renderer controls and offline regression/simulation coverage. Existing base-noun bans and pixel/dHash thresholds must NOT be weakened.
- Important distinction: this is a filesystem/FFmpeg Python bot, NOT Cloudflare. No external upload/research/paid generation authorized for tests.
- NEXT: implement and test; this checkpoint is NOT a completion claim.

## 2026-09-22 continuation from third archive: baseline inspected
- Current input: `/home/user/uploaded_files/3genspark-f87ed0a1-01b0-4f0f-89fe-4150172f2bb4-main.zip`, untouched. Restored only nested workspace; outer Hono template untouched.
- Actual imported baseline: 38 tests run, 33 PASS, 4 errors and 1 failure (4.569s). Prior checkpoint's 38 PASS predates the unfinished uniqueness integration.
- Old mocked encoder tests now reach the real MP4 auditor; expected upload-state snapshots incorrectly include the new intentional reservation ledger. Must update mocks while adding real audit regressions, not bypass the quality gate.
- Found additional gaps: preview history can target production data, concurrent runs share output folders, CI omits required UNIQUE_HISTORY_GIT and early git identity, and new journal/planner have no regression coverage.
- NEXT: harden isolated preview/publish safety, journal validation and per-run output isolation; test interrupted/uncertain uploads and corrupt history. Then actual offline MP4, README/workflow corrections and deliver archive.

## 2026-09-22 continuation from fourth archive: current checkpoint
- Input: `/home/user/uploaded_files/4genspark-2c168e6d-26ee-46f8-9f1e-8eef17003233-main.zip`, untouched. Restored nested workspace only.
- Baseline `OPENBLAS_NUM_THREADS=1 python -m unittest discover -s tests -v`: all 73 tests PASS (4.548s). The previous handoff was stale: preview isolation, journal schema/transition validation, per-reservation outputs, opt-in publishing and CI checkpoints are already implemented in this archive.
- Do NOT repeat those fixes or claim they were added during this continuation.
- Next: exercise the real encoded-video path, add focused regressions for any remaining safety gaps, correct the stale README, validate CI locally, package source and preview. No uploads/workflows/credentials will be used.

### Fourth-archive safety and render milestone
- Added `UploadUnconfirmedError`: missing/blank upload confirmation now exits CLI with code 1, retains the publishing barrier and leaves legacy uploaded state untouched. Previously it returned success despite an unknown remote result.
- Recheck the audited output SHA-256 after the durable publishing checkpoint; changed video bytes cannot be uploaded.
- Added seven regressions including four REAL local-git integration tests (temporary bare remote only): push of publishing intent, rejected push, unrelated staged-file refusal, and successful rebase over an unrelated remote commit.
- `OPENBLAS_NUM_THREADS=1 python -m unittest discover -s tests -v`: 80 PASS (4.596s). `python -m compileall -q src tests`: PASS.
- Expanded `.gitignore` to exclude credential variants, local lock files/caches/logs and delivery archives; permanent JSON/JSONL history remains tracked.
- Actual preview succeeded with `OPENBLAS_NUM_THREADS=1 python src/animal_short_generator.py --animal-id 1 --renderer 3d --quality standard --duration 3 --dry-run --no-research --max-unique-retries 1`.
- Output: `tmp/reel_0001_a670e45520d555adba92471012ae5e4e/tiger_short.mp4`, 549951 bytes. Real quality report PASS: 1080x1920, 30 FPS, 3.000s, full decode passed, three decoded hashes, zero blank/near-black frames. Preview history isolated in `tmp/unique-preview-history/`.
- Next: second species preview through same ledger, visual review, workflow validation and production-state byte comparison; rewrite stale README and deliver archive.

## Fifth-archive verified milestone (2026-09-22)
- Recreated actual Tiger and Green Sea Turtle previews sequentially against ONE `tmp/unique-preview-history/` ledger, not two clean histories. Both records are `completed`, not `published`.
- Commands (run Tiger first, then Turtle): `OPENBLAS_NUM_THREADS=1 python src/animal_short_generator.py --animal-id ID --renderer 3d --quality standard --duration 3 --dry-run --no-research --max-unique-retries 1`, where ID is 1 then 104.
- Tiger: `tmp/reel_0001_d7b79daff60a391f7a5a8d8e1b969cf1/tiger_short.mp4`, 553146 bytes.
- Turtle: `tmp/reel_0104_f684dd440e2058a3de42207287cf6d7d/green_sea_turtle_short.mp4`, 683192 bytes.
- Both actual MP4 audits PASS: H.264 1080x1920, 30 FPS, 90 video frames, 3.000 seconds, AAC audio, full decode success, three sampled hashes, zero sampled blank/near-black frames. Independently rechecked manifest SHA-256 and full FFmpeg decode. This is NOT a biological-accuracy or production-diversity certification.
- All 13 original `data/` files compare byte-for-byte equal to the fifth input ZIP; no new production state files exist.
- Added seven WorkflowTests to the existing test file; added PyYAML to requirements. These parse both workflow YAML files, check preview/secret gates, main checkout, rebase-before-push, durable checkpoint configuration, run `bash -n`, and execute generation shell blocks with a fake argv recorder to verify literal hostile input and preview flags. No actual workflow, installer, uploader or remote service is run by these tests.
- Hardened legacy Real Draw workflow: preview defaults true, `ENABLE_REAL_DRAW_PUBLISH=true` required for production, no YouTube secrets in preview, boolean-safe progress condition, main checkout/full fetch, rebase before push, regressions before generation. This does NOT fix legacy generator internals: missing confirmation can still advance its history, corrupted history fails open, exhausted subjects reset, no durable publish intent, no encoded-video audit. Keep its production opt-in UNSET pending a separate hardening pass. Its preview still fetches public web reference photos (unlike offline Animal Shorts).
- Corrected misleading Animal Shorts CLI description and examples: procedural/stylized, not realistic; `--no-research` alone is explicitly labelled production.
- `OPENBLAS_NUM_THREADS=1 python -m unittest discover -s tests -v`: 87 PASS in 4.756s. `python -m compileall -q src tests`: PASS.
- External video review agrees species are recognizable and clearly primitive/stylized, with visible overlapping joints and weak ground integration. Reviewer outputs disagree on camera speed/background/shadows; do not promote those subjective claims into verified defects. No photorealism or seamless-loop claim. Midpoint JPEGs and paired sheet are in `tmp/review/`.
- Delivery: updated nested and outer READMEs. Built and CRC-verified `tmp/teacher_bot_yt_updated_2026-09-22.zip` with 92 files: 80 source files and 12 selected preview evidence files. ZIP root is `teacher-bot-yt-main/`; evidence is under `preview_artifacts/` and its ledger is not used by default. No secrets, raw WAVs, frame sequences, locks, Python caches or outer Hono template are packaged. The source milestone is committed on `main`.
- Future implementation: add an unused authentic species rig; do not rerun old completed safety work or weaken production history/visual gates. Current previews remain stylized, and strict 3D publishing is still blocked by the existing permanent base-noun history.

## Tools checked
Python has Pillow, NumPy, PyYAML and pytest; FFmpeg available at /usr/bin/ffmpeg. No secrets or YouTube services used. Blender/bpy was absent in prior continuations and was not installed here.

## 2026-09-22 API-free generic animal renderer milestone
- User requirement: do not hard-limit the bot to the five hand-authored 3D rigs; the bot should render new animal species without requiring a paid/external generation API.
- Added a morphology-driven procedural fallback to `src/animal_3d_renderer.py`. Existing five species keep their dedicated anatomy rigs; all encyclopedia morphologies/classes now use reusable offline 3D primitives when no dedicated rig exists.
- The current `data/animal_encyclopedia.json` contains 687 species entries. `supports_species()` now accepts all 687 entries based on their morphology/class metadata; no API/network call is required by the renderer.
- Generic families include terrestrial quadrupeds, birds, reptiles/amphibians, serpents, fish/aquatic animals, marine mammals, rays, seahorses, insects, arachnids, crustaceans and cephalopods. Species-specific metadata drives proportions, palette and appendages; this is procedural/stylized geometry, not photorealistic scanned anatomy.
- `render_animal_layer()` now passes species metadata into the rig builder, so the existing Animal Shorts pipeline automatically uses the generic 3D renderer for catalog animals that do not have a dedicated rig.
- Verification: 687/687 catalog entries report 3D support; representative species across feline, giraffe, rhino, elephant, lizard, bird, fish, beetle, bear and small-mammal morphologies rendered successfully at draft quality; existing regression suite remains 87 PASS / 65 subtests.
- `random` was added only for deterministic species-seeded variation; there is no external API dependency.
- Limitation: this expands the renderer to the existing 687-species encyclopedia. It does not invent arbitrary scientifically new species from an unconstrained language prompt, and generic models remain stylized. The permanent no-repeat/history/quality gates remain unchanged.
- NEXT: render several sequential unused species through the actual unique ledger and inspect the generated MP4s; then package the updated source. Do not weaken duplicate/history/visual gates.

## 2026-09-22 current delivery checkpoint — handoff updated after API-free 687-species work
- This checkpoint supersedes the package handoff note above for the current source archive.
- User goal: the bot must not be hard-limited to the five dedicated animal rigs; it should be able to render unused animals from the existing 687-species encyclopedia without a paid/external generation API.
- Implemented generic morphology-driven 3D fallback remains enabled in `src/animal_3d_renderer.py`. The five dedicated rigs are preserved; unsupported dedicated species fall back to reusable procedural body/appendage families driven by encyclopedia morphology/class metadata.
- Verified `data/animal_encyclopedia.json` contains exactly 687 species entries.
- Re-ran the full regression suite after packaging work: `OPENBLAS_NUM_THREADS=1 python -m unittest discover -s tests -v` -> **87 tests, OK, 5.522s**.
- No YouTube upload, OAuth, GitHub workflow trigger, external AI generation API, or credentialed network operation was used for this verification.
- Important limitation remains: generic animals are procedural/stylized 3D, not photorealistic scanned/rigged assets, and the 687-entry catalog is finite. The renderer does not invent arbitrary scientifically new species outside the catalog from free-form prompts.
- Important production constraint remains: permanent history/duplicate/visual quality gates must NOT be weakened. The current generic fallback expansion does not by itself certify production diversity or authorize duplicate uploads.
- NEXT: run several consecutive unused catalog species through the actual unique ledger, inspect their MP4s and diversity decisions, then repackage only after those checks. Record exact commands/results here before any subsequent handoff.
