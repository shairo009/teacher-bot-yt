import sys
import argparse
from pathlib import Path

sys.path.append(str(Path(__file__).parent / "src"))
from code_reel_generator import generate_reel_video, load_progress

def main():
    parser = argparse.ArgumentParser(description="500+ Unique Code Reel Generator Engine")
    parser.add_argument("--count", type=int, default=1, help="Number of unique videos to generate")
    args = parser.parse_args()

    print("==================================================")
    print("🎬 TEACHER BOT - 500+ UNIQUE CODE REEL GENERATOR ENGINE")
    print("==================================================")

    progress = load_progress()
    completed_count = len(progress.get("completed_ids", []))
    print(f"📊 Completed Unique Videos: {completed_count} / 500")

    for i in range(args.count):
        print(f"\n🎥 Generating Video {i+1} of {args.count}...")
        result = generate_reel_video()
        if not result:
            print("Finished all available topics!")
            break
        print(f"✨ Created Video Reel: {result[0]}")
        print(f"📥 Saved to Downloads: {result[1]}")

if __name__ == "__main__":
    main()
