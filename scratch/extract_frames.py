import os
import subprocess
from pathlib import Path

PROJECT_ROOT = Path("C:/Users/1001s/teacher-bot-temp")

def extract_frame(time_seconds, label):
    output_path = PROJECT_ROOT / f"outputs/preview_{label}.png"
    if output_path.exists():
        os.remove(output_path)
    
    cmd = [
        'ffmpeg', '-y',
        '-ss', str(time_seconds),
        '-i', str(PROJECT_ROOT / "outputs/quiz_single.mp4"),
        '-vframes', '1',
        '-q:v', '2',
        str(output_path)
    ]
    subprocess.run(cmd, capture_output=True)
    if output_path.exists():
        print(f"Extracted frame at {time_seconds}s to {output_path.name}")
    else:
        print(f"Failed to extract frame at {time_seconds}s")

def main():
    # New Video duration: 57.87s
    # Q: 0.0s to 22.944s
    #   Intro: 0.0s - 2.64s
    #   Question: 2.64s - 8.64s
    #   Option A: 8.64s - 12.216s
    #   Option B: 12.216s - 14.952s
    #   Option C: 14.952s - 17.448s
    #   Option D: 17.448s - 20.568s
    #   Outro: 20.568s - 22.944s
    # Countdown: 22.944s to 27.944s
    # Reveal: 27.944s to 32.096s
    # Explain A: 32.096s to 38.384s
    # Explain B: 38.384s to 45.344s
    # Explain C: 45.344s to 52.64s
    # Explain D: 52.64s to 57.872s
    
    print("Extracting key preview frames from quiz_single.mp4...")
    extract_frame(1.0, "intro")            # 1.0s: Intro (Normal question, flat options)
    extract_frame(5.0, "question_zoom")    # 5.0s: Question should be zoomed in
    extract_frame(10.5, "option_a_zoom")   # 10.5s: Option A should be zoomed
    extract_frame(14.0, "option_b_zoom")   # 14.0s: Option B should be zoomed
    extract_frame(17.0, "option_c_zoom")   # 17.0s: Option C should be zoomed
    extract_frame(20.0, "option_d_zoom")   # 20.0s: Option D should be zoomed
    extract_frame(27.0, "countdown")       # 27.0s: Countdown phase (Timer orb ring active)
    extract_frame(31.0, "reveal")          # 31.0s: Answer reveal phase (Solid green border, zoomed correct)
    extract_frame(36.0, "explain_a")       # 36.0s: Explain A zoomed, Card A active
    extract_frame(43.0, "explain_b")       # 43.0s: Explain B zoomed, Card A flat, Card B active
    extract_frame(50.0, "explain_c")       # 50.0s: Explain C zoomed, Cards A & B flat, Card C active
    extract_frame(56.0, "explain_d")       # 56.0s: Explain D zoomed, Cards A, B, C flat, Card D active
    print("Done!")

if __name__ == "__main__":
    main()
