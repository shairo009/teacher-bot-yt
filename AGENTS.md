# Teacher Bot YT — Agent Guidelines & Permanent Rules

## 1. Zero Duplicate Animal Policy (Base-Noun Deduplication)
- **STRICT BAN ON CLONES / VARIANTS:** Once an animal's base noun has been uploaded (e.g., `SCORPION`, `CRAB`, `SPIDER`, `MANTIS`), NO further variants with prefixes (like `VOLT`, `CYBER`, `QUANTUM`, `SOLAR`, `LASER`, `STONE`, `GIANT`) may ever be generated or uploaded.
- All candidate animal selections must pass `extract_base_noun(name) not in get_used_base_nouns()`.
- If an animal category is already in `data/used_animals.json` or `data/animal_history.json`, it is permanently blocked.

## 2. Mandatory Visual Variety & Taxonomy Rotation
- **Multi-Class Rotation:** Consecutive videos must cycle through distinct taxonomic classes:
  `aquatic -> insect -> quadruped -> cephalopod -> reptile -> arachnid -> serpent -> crustacean`
- **Unique Anatomy & Rigging:** Every animal must use its authentic biological rigging renderer (e.g., Lion mane, Giraffe neck & ossicones, Rhinoceros horns, Elephant trunk & tusks, Cobra hood, Bear coat). Do NOT fall back to a generic quadruped dog model.
- **Dynamic Themes:** Background, canvas border, and UI badges must alternate between distinct color environments (`ocean`, `savanna`, `jungle`, `volcanic`, `arctic`, `cyber`).
- **Motion Physics:** Motion dynamics must match taxonomic class (fluid glide for fish, snappy bursts for insects, scuttle for arachnids, sinuous slither for serpents).

## 3. Rolling Frame Verification Buffer
- Representative frames of uploads are stored in `data/recent_frames/` (up to 5 frames) and `data/last_uploaded_frame.jpg`.
- Before rendering/uploading, every candidate must pass:
  - Perceptual dHash Hamming distance check (> 10).
  - Minimum visual difference check (> 20%).
- If too similar to any recent frame, the candidate is discarded and the next distinct animal is selected.

## 4. Git & Workflow Push Reliability
- In `.github/workflows/generate.yml`, ensure `git pull --rebase origin main` is always executed prior to `git push origin HEAD:main` to prevent push rejection conflicts.
