import os
import json
import subprocess
from pathlib import Path

PROJECT_ROOT = Path("C:/Users/1001s/teacher-bot-temp")
python_exe = "C:/Users/1001s/AppData/Local/Programs/Python/Python312/python.exe"

def main():
    questions_path = PROJECT_ROOT / "data/lucent_questions.json"
    if not questions_path.exists():
        print("Error: lucent_questions.json not found. Run generate_lucent_database.py first!")
        return

    with open(questions_path, 'r', encoding='utf-8') as f:
        questions = json.load(f)

    print("=" * 60)
    print(f"  Starting Lucent Polity GK Shorts Series ({len(questions)} videos)")
    print("=" * 60)

    for q in questions:
        q_id = q["id"]
        output_video = PROJECT_ROOT / f"outputs/quiz_polity_q{q_id}.mp4"
        
        if output_video.exists():
            print(f"\n[Skip] Video for Question ID {q_id} already exists at {output_video.name}")
            continue

        print(f"\n[Start] Generating Video for Question ID {q_id}...")
        print(f"        Topic: {q['topic']}")
        print(f"        Question: {q['question_hi']}")
        
        cmd = [
            python_exe,
            str(PROJECT_ROOT / "scratch/html_quiz.py"),
            "--question-id", str(q_id)
        ]
        
        # Run synchronously to prevent CPU overload
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0 and output_video.exists():
            print(f"✅ [Success] Generated video: {output_video.name}")
        else:
            print(f"❌ [Error] Failed to generate video for ID {q_id}!")
            print(result.stderr)
            break

    print("\n" + "=" * 60)
    print("  Lucent Series Generation Complete! 🎉")
    print("=" * 60)

if __name__ == "__main__":
    main()
