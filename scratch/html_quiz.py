import os
import sys
import json
import math
import asyncio
import subprocess
from pathlib import Path
from dotenv import load_dotenv

# Add project root to sys.path
PROJECT_ROOT = Path("C:/Users/1001s/teacher-bot-temp")
sys.path.append(str(PROJECT_ROOT))

# Load environment variables
load_dotenv(PROJECT_ROOT / ".env", override=True)

# Canvas size for Shorts (Portrait)
WIDTH = 1080
HEIGHT = 1920
FPS = 30

def get_audio_duration(file_path):
    """Query exact duration of audio using ffprobe."""
    cmd = [
        'ffprobe', '-v', 'error',
        '-show_entries', 'format=duration',
        '-of', 'default=noprint_wrappers=1:nokey=1',
        str(file_path)
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode == 0:
        return float(result.stdout.strip())
    return 3.0

async def generate_tts(text, filename):
    """Generate audio using edge-tts with standard rate boost (+14%)."""
    import edge_tts
    temp_dir = PROJECT_ROOT / "temp_audio"
    temp_dir.mkdir(exist_ok=True)
    output_path = temp_dir / filename
    communicate = edge_tts.Communicate(text, 'hi-IN-MadhurNeural', rate='+14%')
    await communicate.save(str(output_path))
    return output_path

async def render_html_frames(data, n_q, n_c, n_r, n_e0, n_e1, n_e2, n_e3, timings):
    """Render frames by taking screenshots of the HTML file using Playwright."""
    from playwright.async_api import async_playwright
    
    temp_frames_dir = PROJECT_ROOT / "temp_frames"
    temp_frames_dir.mkdir(exist_ok=True)
    
    # Clean up old frames
    for f in temp_frames_dir.glob("frame_*.png"):
        try:
            os.remove(f)
        except:
            pass

    total_frames = n_q + n_c + n_r + n_e0 + n_e1 + n_e2 + n_e3
    print(f"Rendering {total_frames} frames using Playwright Chromium...")
    
    html_path = PROJECT_ROOT / "templates/quiz_shorts.html"
    file_url = f"file:///{os.path.abspath(html_path).replace(os.sep, '/')}"
    
    frame_paths = []
    
    async with async_playwright() as p:
        # Launch headless Chromium
        browser = await p.chromium.launch(headless=True)
        # Create page with exactly 1080x1920 viewport
        page = await browser.new_page(viewport={"width": WIDTH, "height": HEIGHT})
        
        # Open local HTML template
        await page.goto(file_url)
        # Wait for page to fully load (fonts, CSS)
        await page.wait_for_timeout(1000)
        
        for frame_idx in range(total_frames):
            timings_json = "null"
            if frame_idx < n_q:
                # 1. Question reading phase
                phase = 'question'
                progress = frame_idx / FPS
                timings_json = json.dumps(timings)
            elif frame_idx < (n_q + n_c):
                # 2. Countdown phase
                phase = 'countdown'
                progress = (frame_idx - n_q) / n_c
            elif frame_idx < (n_q + n_c + n_r):
                # 3. Reveal correct answer phase
                phase = 'reveal'
                progress = (frame_idx - n_q - n_c) / n_r
            elif frame_idx < (n_q + n_c + n_r + n_e0):
                # 4. Explain Option A
                phase = 'explain0'
                progress = (frame_idx - n_q - n_c - n_r) / n_e0
            elif frame_idx < (n_q + n_c + n_r + n_e0 + n_e1):
                # 5. Explain Option B
                phase = 'explain1'
                progress = (frame_idx - n_q - n_c - n_r - n_e0) / n_e1
            elif frame_idx < (n_q + n_c + n_r + n_e0 + n_e1 + n_e2):
                # 6. Explain Option C
                phase = 'explain2'
                progress = (frame_idx - n_q - n_c - n_r - n_e0 - n_e1) / n_e2
            else:
                # 7. Explain Option D
                phase = 'explain3'
                progress = (frame_idx - n_q - n_c - n_r - n_e0 - n_e1 - n_e2) / n_e3
                
            # Invoke the global JS state controller inside the page
            await page.evaluate(f"window.setQuizState('{phase}', {progress}, {timings_json})")
            
            # Take a screenshot of the frame
            frame_path = temp_frames_dir / f"frame_{str(frame_idx).zfill(3)}.png"
            await page.screenshot(path=str(frame_path), type='png')
            frame_paths.append(str(frame_path))
            
            if frame_idx % 100 == 0:
                print(f"Rendered {frame_idx}/{total_frames} frames...")
                
        await browser.close()
        
    return frame_paths

def compose_quiz_video(frame_paths, audio_path, question_id):
    """Compile frames and audio into final video using FFmpeg."""
    outputs_dir = PROJECT_ROOT / "outputs"
    outputs_dir.mkdir(exist_ok=True)
    output_video_path = outputs_dir / f"quiz_polity_q{question_id}.mp4"
    
    concat_file = outputs_dir / "quiz_concat.txt"
    frame_dur = 1.0 / FPS
    
    with open(concat_file, 'w') as f:
        for frame in frame_paths:
            f.write(f"file '{os.path.abspath(frame)}'\n")
            f.write(f"duration {frame_dur:.6f}\n")
        f.write(f"file '{os.path.abspath(frame_paths[-1])}'\n")
 
    print("Composing video with FFmpeg...")
    if output_video_path.exists():
        os.remove(output_video_path)
        
    cmd = [
        'ffmpeg', '-y',
        '-f', 'concat', '-safe', '0',
        '-i', str(concat_file),
        '-i', str(audio_path),
        '-vf', 'scale=1080:1920,fps=30',
        '-c:v', 'libx264',
        '-preset', 'fast',
        '-pix_fmt', 'yuv420p',
        '-shortest',
        str(output_video_path)
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    if concat_file.exists():
        os.remove(concat_file)
        
    if result.returncode == 0 and output_video_path.exists():
        print(f"Success! Video created at: {output_video_path}")
        return output_video_path
    else:
        print(f"FFmpeg failed: {result.stderr}")
        return None

async def main():
    import argparse
    from jinja2 import Template

    parser = argparse.ArgumentParser()
    parser.add_argument("--question-id", type=int, default=1, help="ID of the question from lucent_questions.json")
    args, unknown = parser.parse_known_args()

    # Load questions from database
    questions_path = PROJECT_ROOT / "data/lucent_questions.json"
    if not questions_path.exists():
        print(f"Error: Database not found at {questions_path}!")
        return

    with open(questions_path, 'r', encoding='utf-8') as f:
        questions = json.load(f)

    # Find the question with matching ID
    question_data = next((q for q in questions if q["id"] == args.question_id), None)
    if not question_data:
        print(f"Error: Question ID {args.question_id} not found in database! Defaulting to ID 1.")
        question_data = questions[0]

    print(f"\n--- Running Question ID {question_data['id']} ---")
    print(f"Subject: {question_data['subject']}")
    print(f"Chapter: {question_data['chapter']}")
    print(f"Topic: {question_data['topic']}")
    print(f"Question (HI): {question_data['question_hi']}")

    # Render templates/quiz_shorts_template.html to templates/quiz_shorts.html
    template_path = PROJECT_ROOT / "templates/quiz_shorts_template.html"
    output_html_path = PROJECT_ROOT / "templates/quiz_shorts.html"

    with open(template_path, 'r', encoding='utf-8') as f:
        template_str = f.read()

    template = Template(template_str)
    rendered_html = template.render(
        subject=question_data["subject"],
        chapter=question_data["chapter"],
        topic=question_data["topic"],
        question_hi=question_data["question_hi"],
        question_en=question_data["question_en"],
        opt0_en=question_data["opt0_en"],
        opt0_hi=question_data["opt0_hi"],
        opt1_en=question_data["opt1_en"],
        opt1_hi=question_data["opt1_hi"],
        opt2_en=question_data["opt2_en"],
        opt2_hi=question_data["opt2_hi"],
        opt3_en=question_data["opt3_en"],
        opt3_hi=question_data["opt3_hi"],
        exp0=question_data["exp0"],
        exp1=question_data["exp1"],
        exp2=question_data["exp2"],
        exp3=question_data["exp3"],
        correct_idx=question_data["correct_idx"]
    )

    with open(output_html_path, 'w', encoding='utf-8') as f:
        f.write(rendered_html)

    # Map database fields to script structures
    quiz_data = {
        "question": question_data["question_en"],
        "options": [
            question_data["opt0_en"],
            question_data["opt1_en"],
            question_data["opt2_en"],
            question_data["opt3_en"]
        ],
        "correct": question_data["correct_idx"],
        "explanation": question_data[f"exp{question_data['correct_idx']}"],
        "r_narration": question_data["narration"]["r_narration"],
        "e0_narration": question_data["narration"]["e0_narration"],
        "e1_narration": question_data["narration"]["e1_narration"],
        "e2_narration": question_data["narration"]["e2_narration"],
        "e3_narration": question_data["narration"]["e3_narration"]
    }

    q_segments = {
        "intro": question_data["narration"]["q_intro"],
        "question": question_data["narration"]["q_question"],
        "opt0": question_data["narration"]["opt0"],
        "opt1": question_data["narration"]["opt1"],
        "opt2": question_data["narration"]["opt2"],
        "opt3": question_data["narration"]["opt3"],
        "outro": question_data["narration"]["q_outro"]
    }

    temp_dir = PROJECT_ROOT / "temp_audio"
    temp_dir.mkdir(exist_ok=True)
    
    # 1. Generate Voiceovers
    print("\nGenerating Audio Voiceovers...")
    q_intro_audio = await generate_tts(q_segments["intro"], "q_intro.mp3")
    q_question_audio = await generate_tts(q_segments["question"], "q_question.mp3")
    q_opt0_audio = await generate_tts(q_segments["opt0"], "q_opt0.mp3")
    q_opt1_audio = await generate_tts(q_segments["opt1"], "q_opt1.mp3")
    q_opt2_audio = await generate_tts(q_segments["opt2"], "q_opt2.mp3")
    q_opt3_audio = await generate_tts(q_segments["opt3"], "q_opt3.mp3")
    q_outro_audio = await generate_tts(q_segments["outro"], "q_outro.mp3")

    r_audio = await generate_tts(quiz_data["r_narration"], "reveal.mp3")
    e0_audio = await generate_tts(quiz_data["e0_narration"], "explain0.mp3")
    e1_audio = await generate_tts(quiz_data["e1_narration"], "explain1.mp3")
    e2_audio = await generate_tts(quiz_data["e2_narration"], "explain2.mp3")
    e3_audio = await generate_tts(quiz_data["e3_narration"], "explain3.mp3")
    
    # 2. Generate Silence Audios (5s countdown and 0.25s delay silence)
    print("Generating silence audio tracks...")
    silence_audio = temp_dir / "silence.mp3"
    cmd_silence = [
        'ffmpeg', '-y',
        '-f', 'lavfi', '-i', 'anullsrc=r=24000:cl=mono',
        '-t', '5.0',
        '-c:a', 'libmp3lame',
        str(silence_audio)
    ]
    subprocess.run(cmd_silence, capture_output=True)

    opt_silence = temp_dir / "opt_silence.mp3"
    cmd_opt_silence = [
        'ffmpeg', '-y',
        '-f', 'lavfi', '-i', 'anullsrc=r=24000:cl=mono',
        '-t', '0.25',
        '-c:a', 'libmp3lame',
        str(opt_silence)
    ]
    subprocess.run(cmd_opt_silence, capture_output=True)
    
    # 3. Measure Durations
    t_intro = get_audio_duration(q_intro_audio)
    t_question = get_audio_duration(q_question_audio)
    t_opt0 = get_audio_duration(q_opt0_audio)
    t_opt1 = get_audio_duration(q_opt1_audio)
    t_opt2 = get_audio_duration(q_opt2_audio)
    t_opt3 = get_audio_duration(q_opt3_audio)
    t_outro = get_audio_duration(q_outro_audio)

    t_delay = 0.25  # 250ms delay between option segments
    t_c = 5.0  # exactly 5 seconds countdown
    t_r = get_audio_duration(r_audio)
    t_e0 = get_audio_duration(e0_audio)
    t_e1 = get_audio_duration(e1_audio)
    t_e2 = get_audio_duration(e2_audio)
    t_e3 = get_audio_duration(e3_audio)
    
    # Build cumulative timings timeline including delays
    start_intro = 0.0
    end_intro = t_intro
    
    start_question = end_intro + t_delay
    end_question = start_question + t_question
    
    start_opt0 = end_question + t_delay
    end_opt0 = start_opt0 + t_opt0
    
    start_opt1 = end_opt0 + t_delay
    end_opt1 = start_opt1 + t_opt1
    
    start_opt2 = end_opt1 + t_delay
    end_opt2 = start_opt2 + t_opt2
    
    start_opt3 = end_opt2 + t_delay
    end_opt3 = start_opt3 + t_opt3
    
    start_outro = end_opt3 + t_delay
    end_outro = start_outro + t_outro

    timings = {
        "start_intro": start_intro,
        "end_intro": end_intro,
        "start_question": start_question,
        "end_question": end_question,
        "start_opt0": start_opt0,
        "end_opt0": end_opt0,
        "start_opt1": start_opt1,
        "end_opt1": end_opt1,
        "start_opt2": start_opt2,
        "end_opt2": end_opt2,
        "start_opt3": start_opt3,
        "end_opt3": end_opt3,
        "start_outro": start_outro,
        "end_outro": end_outro
    }
    
    t_q = end_outro
    
    print(f"Durations measured:")
    print(f" - Intro: {t_intro}s")
    print(f" - Question text: {t_question}s")
    print(f" - Option A: {t_opt0}s")
    print(f" - Option B: {t_opt1}s")
    print(f" - Option C: {t_opt2}s")
    print(f" - Option D: {t_opt3}s")
    print(f" - Outro: {t_outro}s")
    print(f" - Question Phase Total (t_q): {t_q}s")
    print(f" - Countdown: {t_c}s")
    print(f" - Reveal: {t_r}s")
    print(f" - Explain A: {t_e0}s")
    print(f" - Explain B: {t_e1}s")
    print(f" - Explain C: {t_e2}s")
    print(f" - Explain D: {t_e3}s")
    
    total_audio_time = t_q + t_c + t_r + t_e0 + t_e1 + t_e2 + t_e3
    print(f"Total Video Duration: {total_audio_time:.2f}s")
    
    # 4. Merge Audios (19 audio segments concatenated)
    print("Concatenating all 19 audio segments...")
    merged_audio = temp_dir / "quiz_final.mp3"
    cmd_merge = [
        'ffmpeg', '-y',
        '-i', str(q_intro_audio),     # 0
        '-i', str(opt_silence),       # 1
        '-i', str(q_question_audio),  # 2
        '-i', str(opt_silence),       # 3
        '-i', str(q_opt0_audio),      # 4
        '-i', str(opt_silence),       # 5
        '-i', str(q_opt1_audio),      # 6
        '-i', str(opt_silence),       # 7
        '-i', str(q_opt2_audio),      # 8
        '-i', str(opt_silence),       # 9
        '-i', str(q_opt3_audio),      # 10
        '-i', str(opt_silence),       # 11
        '-i', str(q_outro_audio),     # 12
        '-i', str(silence_audio),     # 13
        '-i', str(r_audio),           # 14
        '-i', str(e0_audio),          # 15
        '-i', str(e1_audio),          # 16
        '-i', str(e2_audio),          # 17
        '-i', str(e3_audio),          # 18
        '-filter_complex', '[0:a][1:a][2:a][3:a][4:a][5:a][6:a][7:a][8:a][9:a][10:a][11:a][12:a][13:a][14:a][15:a][16:a][17:a][18:a]concat=n=19:v=0:a=1[outa]',
        '-map', '[outa]',
        str(merged_audio)
    ]
    subprocess.run(cmd_merge, capture_output=True)
    
    # 5. Calculate Frame counts
    n_q = int(t_q * FPS)
    n_c = int(t_c * FPS)
    n_r = int(t_r * FPS)
    n_e0 = int(t_e0 * FPS)
    n_e1 = int(t_e1 * FPS)
    n_e2 = int(t_e2 * FPS)
    n_e3 = int(t_e3 * FPS)
    
    # 6. Render Frames using Playwright Chromium
    print("\nRendering video frames via Playwright...")
    frame_paths = await render_html_frames(quiz_data, n_q, n_c, n_r, n_e0, n_e1, n_e2, n_e3, timings)
    
    # 7. Compose Video
    print("\nComposing final MP4 video...")
    video_path = compose_quiz_video(frame_paths, merged_audio, question_data["id"])
    
    # Cleanup temp frames & audios
    print("\nCleaning up temporary files...")
    for frame in frame_paths:
        try:
            os.remove(frame)
        except:
            pass
    try:
        os.remove(q_intro_audio)
        os.remove(q_question_audio)
        os.remove(q_opt0_audio)
        os.remove(q_opt1_audio)
        os.remove(q_opt2_audio)
        os.remove(q_opt3_audio)
        os.remove(q_outro_audio)
        os.remove(r_audio)
        os.remove(silence_audio)
        os.remove(opt_silence)
        os.remove(e0_audio)
        os.remove(e1_audio)
        os.remove(e2_audio)
        os.remove(e3_audio)
    except:
        pass
            
    print(f"\nDone! Final video is available at: {video_path}")

if __name__ == "__main__":
    asyncio.run(main())
