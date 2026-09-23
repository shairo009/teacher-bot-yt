# 🤖 AI Handover & Continuity Architecture (AI_HANDOFF.md)

> **FOR ANY INCOMING AI / AGENT / LLM:**  
> This file is your single source of truth. If the previous AI ran out of credits or context window, read this document to pick up work immediately without losing progress, without breaking existing systems, and without reverting to 3D.

---

## 🎯 1. Project Vision & Identity

This repository generates high-performing **YouTube Shorts** featuring:
1. **2D Interactive Bio-Kinematic Creatures**: Animals that track a moving cyber cursor using realistic inverse kinematics (IK), spine vertebrae chains, anatomical joints, and species-specific traits.
2. **Interactive Telemetry Canvas**: Realtime HUD (`TARGET [X, Y]`, `DIST`, `ROT`, `IK SOLVER 60 FPS`, laser trajectory, and rotating reticles).
3. **macOS One Dark Pro IDE Code Window**: Clean syntax-highlighted JavaScript code that types and scrolls in real-time, matching the creature's mechanics.

### ⛔ Critical Constraint: ABSOLUTELY NO 3D
- **Do NOT introduce 3D renderers, ellipsoids, or mesh approximations.** 
- 3D was previously tested and failed; the channel's viral brand identity is built entirely on **2D Organic Procedural Canvas Animation** with coding aesthetics.

---

## 📍 2. Current System State & Progress

- **Last Published Short**: Animal #330 (`DUGONG`) — [Watch on YouTube](https://youtu.be/2y6NRKBM3vE)
- **YouTube Upload Privacy**: Strictly **PUBLIC** by default (Never set to private).
- **Core Engine Files**:
  - `src/animal_short_generator.py`: Pipeline runner (Research -> Render -> Audio -> FFmpeg -> Upload).
  - `src/generative_dragon_engine.py`: Canvas HUD, laser guides, reticle, and macOS IDE code window.
  - `src/bio_bone_renderer.py`: Anatomical skeleton, muscle, skin, and kinematics for 680+ animal species.
  - `.github/workflows/generate.yml`: Automated daily runner on GitHub Actions.
- **State Ledgers (DO NOT DELETE)**:
  - `data/animal_progress.json`: Tracks next species index.
  - `data/animal_history.json`: Rolling history of uploaded species, visual diffs, and URLs.
  - `data/used_animals.json`: Base-noun deduplication ledger (guarantees zero duplicate animals).

---

## 🚀 3. How to Make Animals "100x Better" (Quality Roadmap)

When improving the visual quality of animal models, make your enhancements directly in **`src/bio_bone_renderer.py`** and **`src/generative_dragon_engine.py`**:

### A. Anatomical Realism (In `src/bio_bone_renderer.py`)
1. **Dynamic Spine Curvature**:
   - Ensure the spine segments bend organically with variable stiffness (neck flexible, torso rigid, tail whip-like).
2. **Multi-Layered Shading & Organic Textures**:
   - Use 3-tone shading: Base dark tone -> Mid-body muscle tone -> Highlight dorsal ridge.
   - Add species micro-details (e.g., tiger/zebra stripe patterns, cheetah spots, reptile scales, insect wing veins, bird feather vanes).
3. **Advanced Limb Inverse Kinematics**:
   - 2-bone or 3-bone IK with realistic joint constraints (knees bend backward for ungulates/quadrupeds, forward for primates/frogs).
   - Dynamic foot planting: paws/hooves flatten slightly on weight-bearing contact.
4. **Secondary Motion & Easing**:
   - Ears flick, tails lag behind body motion with wave physics, and whiskers/antennae tremble subtly.
   - Breathing/chest expansion cycle using `math.sin(sim_time * 3)`.

### B. Canvas & Visual Effects (In `src/generative_dragon_engine.py`)
1. **Organic Drop Shadow**:
   - Render a soft, semi-transparent contact shadow under the creature's body and feet onto the dark canvas grid.
2. **Fluid Particle Trails**:
   - Cursor ember trails and subtle creature dust/water bubbles depending on whether the animal is terrestrial, aerial, or aquatic.
3. **Live Telemetry Fidelity**:
   - Ensure HUD badges, laser dash lines, and rotating cyber brackets remain crisp and never overlap with creature silhouettes.

---

## 🛠️ 4. Quick Testing & Verification Commands

Before committing any changes, run these quick commands to ensure zero errors:

```bash
# 1. Syntax check all python source files
python -m compileall src

# 2. Test video generation without uploading (Dry Run)
python src/animal_short_generator.py --dry-run

# 3. Test a specific animal index (e.g. index 5)
python src/animal_short_generator.py --dry-run --animal-id 5

# 4. Check git status to ensure no stray files
git status
```

---

## 🔄 5. Continuity Checklist for Incoming AI

When you start your session:
1. [ ] Run `git status` and `git pull origin main` to sync with the latest state.
2. [ ] Read `data/animal_progress.json` to see the next animal queued.
3. [ ] Check `src/bio_bone_renderer.py` to see the specific renderer for that animal's class/morphology.
4. [ ] Enhance and refine the model with anatomical precision.
5. [ ] Run `python -m compileall src` to guarantee clean execution.
6. [ ] Commit with clear, descriptive messages and push:
   ```bash
   git add -A
   git commit -m "Enhance <animal> procedural kinematics and anatomy"
   git pull --rebase origin main
   git push origin main
   ```
7. [ ] Ensure GitHub Actions (`.github/workflows/generate.yml`) runs green and uploads as **Public**.
