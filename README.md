# Teacher Bot YT — procedural animal Shorts

Offline Python + NumPy + Pillow + FFmpeg animal-video generation with optional YouTube publishing. Run on a Linux workstation or GitHub Actions runner. This needs filesystem access and subprocesses and is **not a Cloudflare application**.

## Verified status — 2026-09-22

- 1080x1920 vertical H.264/AAC MP4 at 30 FPS; default duration 25 seconds.
- Actual analytical 3D for all **687 catalogue entries across 43 morphology profiles**, composited into the existing 2D poster. Five exact species retain dedicated rigs; others use metadata-driven family rigs. Geometry is stylized and primitive-based, **not photorealistic or 687 independently validated anatomical models**.
- History-aware scene planning, checksummed event journal, isolated preview history and per-reservation output directories.
- Imported baseline independently verified: **99 offline tests PASS**. Includes finite geometry for all 687 entries, visible animation across 43 morphology profiles, workflow checks and real local-git checkpoint tests; YouTube uploads are mocked.
- Current continuation is validating consecutive unused-species MP4s on one isolated preview ledger. See `AI_HANDOFF.md` for current results; older Tiger/Turtle previews were not included in the uploaded source archive.
- Production `data/` must remain untouched; byte-for-byte comparison against the input ZIP is required before delivery.
- No YouTube uploads, workflow triggers, paid media generation, credential use or production deployment performed.

## Setup and safe first run

Use Python 3.11+ and FFmpeg/ffprobe on PATH. From **this folder**, not the outer Hono development wrapper:

```bash
python -m pip install -r requirements.txt
OPENBLAS_NUM_THREADS=1 python -m unittest discover -s tests -v
OPENBLAS_NUM_THREADS=1 python src/animal_short_generator.py --animal-id 306 --renderer 3d --quality standard --duration 3 --dry-run --no-research --history-dir tmp/my-preview --max-unique-retries 1
OPENBLAS_NUM_THREADS=1 python src/animal_short_generator.py --animal-id 401 --renderer 3d --quality standard --duration 3 --dry-run --no-research --history-dir tmp/my-preview --max-unique-retries 1
```

The Animal Shorts preview needs no API key, never researches online and synthesizes audio locally. Full requirements include dependencies for legacy scripts, optional production research, YouTube publishing and PyYAML for workflow tests. Legacy paths may access the network even in preview.

Run previews sequentially using the **same** `--history-dir`; do not clear it between animals. Rerunning against existing preview history may reject the requested plan; rejection is not permission to reset production history. A new preview directory is an isolated test sandbox, never evidence of production eligibility.

### Renderer coverage

Dedicated rigs (preserved unchanged):

| Catalogue ID | Species |
|---|---|
| 0 | African Lion |
| 1 | Tiger |
| 104 | Green Sea Turtle |
| 122 | Leopard Gecko |
| 465 | Mexican Redknee Tarantula |

Other catalogue entries use reusable morphology-driven families: mammals, birds, fish, rays, seahorses, marine mammals, reptiles, amphibians, insects, arachnids, crustaceans, cephalopods and jellyfish. Proportions, colours and appendages come from catalogue metadata. Explicit morphology takes precedence over broad class; unknown explicit morphology fails closed in strict `3d` mode. Exact names, not a shared family name, select the five dedicated rigs.

`auto` chooses supported 3D and otherwise legacy 2D. `3d` requires an exact dedicated species or supported morphology/class metadata; `2d` explicitly retains the legacy renderer. Current catalogue indexes are 0–686. This does not invent arbitrary new species from free-form prompts or certify anatomical accuracy.

**Production constraints:** all five dedicated-rig base nouns are already used, but unused generic-rig species exist (for example 306 Pacific Seahorse, 401 Monarch Butterfly, 604 Indian Greater One Horned Rhino). Unused status alone is NOT publishing eligibility: production references, history, semantic/visual gates and upload safeguards still apply. Never delete history, rename a used animal or lower visual thresholds. Keep publishing disabled until visual diversity and recognizability are reviewed.

## CLI entry points

No public web/API endpoints or production URLs exist for this bot. Main entry: `python src/animal_short_generator.py`.

| Parameter | Behavior |
|---|---|
| `--dry-run` | Render/audit locally without research, upload or production-state changes |
| `--animal-id N` | Select a catalogue ID without overriding production duplicate bans |
| `--renderer auto\|2d\|3d` | Default `auto`; `3d` requires a dedicated species or supported morphology metadata |
| `--quality draft\|standard\|high` | Internal 3D resolution; default `standard`; final canvas unchanged |
| `--duration SECONDS` | Positive finite duration up to 180; default 25 |
| `--no-research` | Disable optional research; **alone this does not disable publishing** |
| `--history-dir PATH` | Isolated preview ledger only; cannot overlap production `data/` |
| `--max-unique-retries N` | Default 48; use 1 for small smoke tests |
| `--similarity-threshold VALUE` | Semantic threshold, default 0.78; permanent base bans and visual gates remain |

No arguments means a **production attempt**, not preview. CLI descriptions and examples now label this explicitly. The workflow publishing opt-ins do not guard direct CLI use.

## Outputs and data model

Each reservation writes:

```text
tmp/reel_<animal-id>_<reservation-id>/
  <species>_short.mp4
  generation_manifest.json
  quality_report.json
  audio.wav
  frames/frame_0000.jpg ...
```

Manifest: plan, content fingerprint, encoded-file SHA-256, three perceptual hashes decoded from the MP4, preview flag and audit report. Audits check encoding and sampled frames; they do not certify biological accuracy or visual quality.

Permanent state:

- `data/animal_encyclopedia.json`: catalogue and rendering descriptors.
- `data/used_animals.json`: permanently uploaded names, normalized and base-noun deduplicated.
- `data/animal_history.json`, `animal_progress.json`: confirmed uploads and progress.
- `data/recent_frames/`, `last_uploaded_frame.jpg`: rolling visual reference buffer.
- `data/unique_animal_history.jsonl`: authoritative checksummed append-only journal.
- `data/unique_animal_history.json`: derived readable snapshot.
- `data/unique_animal_history.initialized`: durable journal head detecting rollback/truncation.

The three production ledger files do not exist in the untouched input; they are created on first production reservation. Back them up together. Preview ledger is `tmp/unique-preview-history/`; locks serialize cooperating local processes. Storage uses files and git checkpoints, not D1/KV/R2.

## Safety gates and recovery

1. Permanent base-noun bans include prefixed variants.
2. Planner rejects reused seeds, duplicate content, repeated animal/action/scene combinations, cosmetic changes and high semantic similarity.
3. Production visual gates require mean pixel difference at least 20% and dHash distance greater than 10. Previews skip only the legacy production-reference check, not their own ledger checks.
4. Encoded video must pass canvas/duration/stream checks, full decode and sampled-frame checks before completion.
5. Lifecycle: `reserved -> completed -> publishing -> published`; `reserved -> failed` also allowed. Failed plans retain semantic barriers. Incomplete/uncertain publishes are not automatically retried.
6. CI pushes durable publish intent before contacting YouTube; checkpoint failure blocks upload. File SHA-256 is rechecked after that checkpoint.
7. Missing/blank upload confirmation exits with code 1, leaving `publishing` intact. Legacy uploaded state advances only after confirmation.

After timeout/interruption, manually inspect the channel and journal. The remote may already have accepted the video. **Do not delete the record or rerun that animal.** Automated reconciliation is not implemented. If published state and legacy files disagree, reconcile from trusted records before resuming.

Corrupt state or a missing initialized journal blocks generation. Restore trusted backups, not an empty list. Checksums detect accidental corruption, not malicious rewriting. Rolling back all ledger files together requires an independent backup to detect.

## GitHub Actions

For a standalone bot repository, place this folder's **contents at the repository root**, including `.github/`, on branch `main`. Nested workflows do not run from the outer development wrapper.

### Animal Shorts (`generate.yml`)

- Manual preview defaults to true, without YouTube credentials.
- Publishing requires repository variable `ENABLE_ANIMAL_PUBLISH=true` and valid `TOKEN_JSON`/`CLIENT_SECRETS_JSON` secrets. Keep opt-in unset until production eligibility and recovery are reviewed.
- Main must permit workflow writes. Git identity and `UNIQUE_HISTORY_GIT=1` enable durable checkpoints; rejected pushes fail closed.
- Concurrency serializes Animal Shorts jobs; regressions run before generation.
- Schedule `17 2,7,12,17,21 * * *` UTC (five times daily) is skipped unless publishing is enabled. Schedules do not guarantee precise delivery time.
- Seven-day artifacts include MP4s, manifests, audit reports and ledger files, never credentials or full frame sequences.

### Legacy Real Draw (`generate_real_draw.yml`)

Now preview-default with its own opt-in `ENABLE_REAL_DRAW_PUBLISH=true`. Preview does not receive YouTube secrets. Boolean-safe progress conditions, main checkout/full history, rebase before push and pre-generation regressions are configured.

**Keep this publishing opt-in unset.** Workflow hardening does not fix the legacy generator: it may advance progress on missing upload confirmation, reset exhausted subjects, fail open on corrupt history, reuse output folders, and lacks the Animal Shorts durable-publishing/audit protections. Its preview fetches public web photos and is **not offline**. No Real Draw video was generated here. Review source-image licenses before publication.

`main.py`, `generate_code_reel.py` and OAuth utilities remain for compatibility; they are not covered by Animal Shorts guarantees. OAuth utilities may modify credentials or trigger external services; do not run them as tests.

### Validation scope

Seven inherited workflow tests parse both YAML files, check explicit safety expressions, run `bash -n`, and execute generation shell blocks with an argv recorder instead of the real generator. Hostile input stays a literal argument; preview flags are verified. These tests do not evaluate all GitHub expression semantics or establish repository permissions. **Real GitHub Actions and YouTube authorization remain unverified.**

## Delivery artifacts

The delivery package is assembled after validation from this source tree and selected `preview_artifacts/` evidence. `AI_HANDOFF.md` lists the actual current videos and validation outcomes. Evidence ledgers are not automatically used by the default CLI. Never copy them into production `data/`.

Delivery excludes credentials, caches, full generated frame sequences, raw WAV files and the outer Hono template. `AI_HANDOFF.md` records the exact continuation checkpoint. Local outputs remain under `tmp/` and are excluded from git.

## Remaining work

1. Review unused generic-rig species for anatomy/recognizability and refine species-specific features where reusable family geometry is insufficient.
2. Review diversity against real production references without weakening safeguards.
3. Improve intersecting primitive joints and ground integration; use properly licensed detailed rigs and an offline Blender/PBR pipeline if photorealism is required.
4. Build a reviewed reconciliation tool for uncertain uploads/partially updated legacy state.
5. Test GitHub Actions in a preview-only standalone repository; separately harden legacy generator internals before enabling Real Draw publishing.

Update `AI_HANDOFF.md` after meaningful changes and before ending a continuation.
