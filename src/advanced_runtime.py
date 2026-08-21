"""Advanced runtime wrapper with clean phone-first rendering."""
from __future__ import annotations
import asyncio, hashlib, json, re
from pathlib import Path

from src import pro_quality_pipeline
from src.advanced_director import director_brief, prompt_suffix
from src.quality_auditor import audit_video
from src.clean_short_layout import clean_frame
from src.llm_router import call_llm as routed_call_llm

ROOT = Path(__file__).resolve().parent.parent
HISTORY = ROOT / "data" / "video_history.json"
MEMORY = ROOT / "data" / "creative_memory.json"


def _puzzle_number(prompt: str) -> int:
    m = re.search(r"PUZZLE #(\d+)", prompt or "")
    return int(m.group(1)) if m else 1


def _load_memory():
    try:
        return json.loads(MEMORY.read_text(encoding="utf-8"))
    except Exception:
        return {"fingerprints": [], "variants": {}, "topics": {}}


def _save_memory(data):
    MEMORY.parent.mkdir(parents=True, exist_ok=True)
    MEMORY.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def install_advanced():
    # Lock the final runtime to the intended 2-minute format: 9 scenes x ~13.33s.
    pro_quality_pipeline.MIN_STEP_SECONDS = 13.333333
    base = pro_quality_pipeline.install()
    original_prompt = base.build_llm_prompt

    # Replace the old provider chain with the current free-model router.
    base.call_llm = routed_call_llm
    original_call = base.call_llm
    original_compose = base.compose_video

    # Final phone-first pass: remove non-essential game UI text after rendering.
    original_render = pro_quality_pipeline.VariantPuzzleEngine.render_frame
    original_thumb = pro_quality_pipeline.VariantPuzzleEngine.render_thumbnail

    def clean_render(self, scene, step_idx, step_progress, global_frame, total_steps):
        frame = original_render(self, scene, step_idx, step_progress, global_frame, total_steps)
        return clean_frame(frame, scene)

    def clean_thumbnail(self, scene):
        frame = original_thumb(self, scene)
        return clean_frame(frame, scene)

    pro_quality_pipeline.VariantPuzzleEngine.render_frame = clean_render
    pro_quality_pipeline.VariantPuzzleEngine.render_thumbnail = clean_thumbnail

    def build_prompt(topic, game_mechanic, game_tag, puzzle_num):
        p = original_prompt(topic, game_mechanic, game_tag, puzzle_num)
        brief = director_brief(int(puzzle_num), HISTORY)
        memory = _load_memory()
        recent = list(memory.get("variants", {}).keys())[-20:]
        anti_repeat = (
            "Avoid these recent creative signatures: " + ", ".join(recent)
            if recent else "No recent signatures; maximize novelty."
        )
        return p + prompt_suffix(brief) + "\nANTI-REPEAT RULE: " + anti_repeat + "\n"

    async def call_llm(prompt, api_key):
        # The router is synchronous; run it in a worker so the async pipeline stays responsive.
        scene = await asyncio.to_thread(original_call, prompt, api_key)
        n = _puzzle_number(prompt)
        scene["director"] = director_brief(n, HISTORY)
        scene["puzzle_num"] = n
        narr = list(scene.get("narration") or [])
        scene["narration"] = [str(x).strip() for x in narr[:base.N_STEPS]]
        return scene

    def compose_video(frames, audio_paths, durations, output_path):
        result = original_compose(frames, audio_paths, durations, output_path)
        if not result:
            return result
        report_path = Path(output_path).with_name("quality_report.json")
        report = audit_video(result, report_path)
        if not report.get("passed"):
            raise RuntimeError("Advanced QA gate failed: " + "; ".join(report.get("errors", [])))
        return result

    base.build_llm_prompt = build_prompt
    base.call_llm = call_llm
    base.compose_video = compose_video
    return base


def _record_creative_memory(scene: dict, output_path: str):
    memory = _load_memory()
    variant = str(scene.get("visual_variant", "unknown"))
    topic = str(scene.get("topic", scene.get("title", "unknown")))
    fp = hashlib.sha256((topic + "|" + variant).lower().encode()).hexdigest()[:16]
    memory.setdefault("fingerprints", []).append(fp)
    memory.setdefault("variants", {})[variant] = memory.get("variants", {}).get(variant, 0) + 1
    memory.setdefault("topics", {})[topic] = {"variant": variant, "output": str(output_path)}
    memory["fingerprints"] = memory["fingerprints"][-1000:]
    _save_memory(memory)


if __name__ == "__main__":
    base = install_advanced()
    asyncio.run(base.main())
