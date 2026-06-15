import os
import sys
import json
import asyncio
import argparse
import subprocess
import random
from pathlib import Path
from datetime import datetime, timezone

PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.append(str(PROJECT_ROOT))

# Canvas size for 4K Shorts (Portrait)
WIDTH = 2160
HEIGHT = 3840
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
    """Generate audio using edge-tts, then convert to uncompressed WAV to prevent compression delays/drift."""
    import edge_tts
    temp_dir = PROJECT_ROOT / "temp_audio"
    temp_dir.mkdir(exist_ok=True)
    
    # edge-tts generates MP3 format
    mp3_filename = filename.replace(".wav", ".mp3")
    mp3_path = temp_dir / mp3_filename
    
    communicate = edge_tts.Communicate(text, 'hi-IN-MadhurNeural', rate='+14%')
    await communicate.save(str(mp3_path))
    
    # Target WAV path
    wav_filename = filename.replace(".mp3", ".wav")
    wav_path = temp_dir / wav_filename
    
    # Convert MP3 to standard PCM 16-bit 24kHz mono WAV
    cmd = [
        'ffmpeg', '-y',
        '-i', str(mp3_path),
        '-acodec', 'pcm_s16le',
        '-ar', '24000',
        '-ac', '1',
        str(wav_path)
    ]
    subprocess.run(cmd, capture_output=True)
    
    # Clean up intermediate MP3
    if mp3_path.exists():
        try:
            os.remove(mp3_path)
        except:
            pass
            
    return wav_path

def pad_trim_audio(input_path, target_duration, output_path):
    """Pad or trim an audio file to the exact target duration in seconds using FFmpeg."""
    cmd = [
        'ffmpeg', '-y',
        '-i', str(input_path),
        '-filter_complex', f'apad=whole_len={int(target_duration * 24000)}',
        '-t', f'{target_duration:.6f}',
        '-c:a', 'pcm_s16le',
        '-ar', '24000',
        '-ac', '1',
        str(output_path)
    ]
    subprocess.run(cmd, capture_output=True)
    return output_path

def generate_tick_sound(output_path, duration=5.0):
    """Generate TikTok-style tick-tock countdown beeps using FFmpeg.
    5 sharp tick beeps mixed with a low suspense drone in WAV format.
    Ticks occur at 1s, 2s, 3s, 4s (880Hz, 80ms) and 4.9s (1000Hz, 100ms) to align with number changes."""
    # Build inputs: 1 drone + 5 tick beeps
    inputs_args = ['-f', 'lavfi', '-i', f'sine=frequency=120:duration={duration}']
    
    # 4 standard ticks at 1.0s, 2.0s, 3.0s, 4.0s
    for i in range(1, 5):
        t_ms = i * 1000
        inputs_args += [
            '-f', 'lavfi', '-i',
            f'sine=frequency=880:duration=0.08,adelay={t_ms}|{t_ms}'
        ]
        
    # Final tick at 4.9s (duration 0.1s, 1000Hz)
    inputs_args += [
        '-f', 'lavfi', '-i',
        f'sine=frequency=1000:duration=0.1,adelay=4900|4900'
    ]
    
    mix_inputs = ''.join(f'[{j}:a]' for j in range(6))
    filter_complex = f'{mix_inputs}amix=inputs=6:normalize=0,volume=2.5[outa]'
    cmd = ['ffmpeg', '-y'] + inputs_args + [
        '-filter_complex', filter_complex,
        '-map', '[outa]',
        '-t', str(duration),
        '-c:a', 'pcm_s16le',
        str(output_path)
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        subprocess.run([
            'ffmpeg', '-y', '-f', 'lavfi', '-i', 'anullsrc=r=24000:cl=mono',
            '-t', str(duration), '-c:a', 'pcm_s16le', str(output_path)
        ], capture_output=True)
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
        browser = await p.chromium.launch(
            headless=True,
            args=[
                '--enable-font-antialiasing',
                '--force-color-profile=srgb',
            ]
        )
        page = await browser.new_page(
            viewport={"width": WIDTH, "height": HEIGHT},
            device_scale_factor=1.0
        )
        
        # Log browser console messages and errors to help with debugging
        page.on("console", lambda msg: print(f"[Browser Console] {msg.text}"))
        page.on("pageerror", lambda err: print(f"[Browser Error] {err}"))
        
        await page.goto(file_url)
        try:
            await page.evaluate("document.fonts.ready")
        except:
            pass
        await page.wait_for_timeout(1500)
        
        # Initialize theme FIRST to avoid black screen
        await page.evaluate("window.randomizeTheme();")
        await page.evaluate("document.body.style.opacity = '1';")
        await page.wait_for_timeout(500)
        
        for frame_idx in range(total_frames):
            timings_json = "null"
            if frame_idx < n_q:
                phase = 'question'
                progress = frame_idx / FPS
                timings_json = json.dumps(timings)
            elif frame_idx < (n_q + n_c):
                phase = 'countdown'
                progress = (frame_idx - n_q) / n_c
            elif frame_idx < (n_q + n_c + n_r):
                phase = 'reveal'
                progress = (frame_idx - n_q - n_c) / n_r
            elif frame_idx < (n_q + n_c + n_r + n_e0):
                phase = 'explain0'
                progress = (frame_idx - n_q - n_c - n_r) / n_e0
            elif frame_idx < (n_q + n_c + n_r + n_e0 + n_e1):
                phase = 'explain1'
                progress = (frame_idx - n_q - n_c - n_r - n_e0) / n_e1
            elif frame_idx < (n_q + n_c + n_r + n_e0 + n_e1 + n_e2):
                phase = 'explain2'
                progress = (frame_idx - n_q - n_c - n_r - n_e0 - n_e1) / n_e2
            else:
                phase = 'explain3'
                progress = (frame_idx - n_q - n_c - n_r - n_e0 - n_e1 - n_e2) / n_e3
                
            await page.evaluate(f"window.setQuizState('{phase}', {progress}, {timings_json})")
            
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
        '-vf', 'fps=30',
        '-c:v', 'libx264',
        '-preset', 'slow',
        '-crf', '15',
        '-c:a', 'aac',
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
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true", help="Skip YouTube upload")
    parser.add_argument("--question-id", type=int, default=None, help="Force a specific question ID")
    args = parser.parse_args()

    # Load questions
    questions_path = PROJECT_ROOT / "data/lucent_questions.json"
    if not questions_path.exists():
        print(f"Error: Database not found at {questions_path}!")
        return

    with open(questions_path, 'r', encoding='utf-8') as f:
        questions = json.load(f)

    # Load progress
    progress_path = PROJECT_ROOT / "data/lucent_progress.json"
    current_id = 1
    if progress_path.exists():
        try:
            with open(progress_path, 'r', encoding='utf-8') as f:
                progress = json.load(f)
                current_id = progress.get("current_id", 1)
        except:
            pass

    # Use forced ID if provided
    if args.question_id is not None:
        current_id = args.question_id

    # Find matching question
    question_data = next((q for q in questions if q["id"] == current_id), None)
    if not question_data:
        print(f"All questions generated! ({current_id} is out of bounds)")
        return

    print(f"\n============================================================")
    print(f"  Teacher Bot - Lucent GK Shorts Series (QID: {question_data['id']})")
    print(f"============================================================")
    print(f"Topic: {question_data['topic']}")
    print(f"Question: {question_data['question_hi']}")

    # Render dynamic HTML
    from jinja2 import Template
    template_path = PROJECT_ROOT / "templates/quiz_shorts_template.html"
    output_html_path = PROJECT_ROOT / "templates/quiz_shorts.html"

    with open(template_path, 'r', encoding='utf-8') as f:
        template_str = f.read()

    template = Template(template_str)
    rendered_html = template.render(
        q_id=question_data["id"],
        subject_hi=question_data.get("subject_hi", question_data["subject"]),
        chapter_hi=question_data.get("chapter_hi", question_data["chapter"]),
        topic_hi=question_data.get("topic_hi", question_data["topic"]),
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

    # Set up structures
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
    q_intro_audio = await generate_tts(q_segments["intro"], "q_intro.wav")
    # Use question_hi directly, remove any "aapke vikalp hain" text from narration
    clean_question = question_data["question_hi"].rstrip("।").rstrip("?")
    q_question_audio = await generate_tts(f"{clean_question}? दिए गए विकल्पों में से अपना जवाब कमेंट में बताइए।", "q_question.wav")
    
    t_delay = 0.25

    # Generate Countdown Tick Sound + Silence Audios (Need silence early for dummy assignments)
    print("Generating tick-tock countdown sound...")
    tick_audio = temp_dir / "tick_tock.wav"
    generate_tick_sound(tick_audio, duration=5.0)

    opt_silence = temp_dir / "opt_silence.wav"
    subprocess.run([
        'ffmpeg', '-y', '-f', 'lavfi', '-i', 'anullsrc=r=24000:cl=mono',
        '-t', str(t_delay), '-c:a', 'pcm_s16le', str(opt_silence)
    ], capture_output=True)

    # Use tiny silence for options and outro instead of generating TTS
    q_opt0_audio = opt_silence
    q_opt1_audio = opt_silence
    q_opt2_audio = opt_silence
    q_opt3_audio = opt_silence
    q_outro_audio = opt_silence

    r_audio = await generate_tts(quiz_data["r_narration"], "reveal.wav")
    e0_audio = await generate_tts(quiz_data["e0_narration"], "explain0.wav")
    e1_audio = await generate_tts(quiz_data["e1_narration"], "explain1.wav")
    e2_audio = await generate_tts(quiz_data["e2_narration"], "explain2.wav")
    e3_audio = await generate_tts(quiz_data["e3_narration"], "explain3.wav")
    
    # 3. Measure Durations
    t_intro = get_audio_duration(q_intro_audio)
    t_question = get_audio_duration(q_question_audio)
    t_opt0 = get_audio_duration(q_opt0_audio)
    t_opt1 = get_audio_duration(q_opt1_audio)
    t_opt2 = get_audio_duration(q_opt2_audio)
    t_opt3 = get_audio_duration(q_opt3_audio)
    t_outro = get_audio_duration(q_outro_audio)

    t_delay = 0.25
    t_c = 5.0
    t_r = get_audio_duration(r_audio)
    t_e0 = get_audio_duration(e0_audio)
    t_e1 = get_audio_duration(e1_audio)
    t_e2 = get_audio_duration(e2_audio)
    t_e3 = get_audio_duration(e3_audio)
    
    # Calculate pre-countdown natural duration
    t_q_natural = t_intro + t_delay + t_question + t_delay + t_opt0 + t_delay + t_opt1 + t_delay + t_opt2 + t_delay + t_opt3 + t_delay + t_outro
    
    # 5. Frame counts aligned exactly to FPS
    n_q = int(round(t_q_natural * FPS))
    n_c = int(round(t_c * FPS))
    n_r = int(round(t_r * FPS))
    n_e0 = int(round(t_e0 * FPS))
    n_e1 = int(round(t_e1 * FPS))
    n_e2 = int(round(t_e2 * FPS))
    n_e3 = int(round(t_e3 * FPS))
    
    # Target durations aligned to 30 FPS
    t_q_target = n_q / FPS
    t_c_target = n_c / FPS
    t_r_target = n_r / FPS
    t_e0_target = n_e0 / FPS
    t_e1_target = n_e1 / FPS
    t_e2_target = n_e2 / FPS
    t_e3_target = n_e3 / FPS
    
    # Pre-countdown alignment: adjust duration of the last silence delay (index 11)
    t_other = t_intro + t_delay + t_question + t_delay + t_opt0 + t_delay + t_opt1 + t_delay + t_opt2 + t_delay + t_opt3 + t_outro
    t_last_silence = max(0.01, t_q_target - t_other)
    
    # Generate custom last silence
    last_silence = temp_dir / "last_silence.wav"
    subprocess.run([
        'ffmpeg', '-y', '-f', 'lavfi', '-i', 'anullsrc=r=24000:cl=mono',
        '-t', f'{t_last_silence:.6f}', '-c:a', 'pcm_s16le', str(last_silence)
    ], capture_output=True)
    
    # Pad and trim post-countdown voiceovers to exact 30 FPS boundary
    r_audio_padded = temp_dir / "reveal_padded.wav"
    pad_trim_audio(r_audio, t_r_target, r_audio_padded)
    
    e0_audio_padded = temp_dir / "explain0_padded.wav"
    pad_trim_audio(e0_audio, t_e0_target, e0_audio_padded)
    
    e1_audio_padded = temp_dir / "explain1_padded.wav"
    pad_trim_audio(e1_audio, t_e1_target, e1_audio_padded)
    
    e2_audio_padded = temp_dir / "explain2_padded.wav"
    pad_trim_audio(e2_audio, t_e2_target, e2_audio_padded)
    
    e3_audio_padded = temp_dir / "explain3_padded.wav"
    pad_trim_audio(e3_audio, t_e3_target, e3_audio_padded)
    
    timings = {
        "start_intro": 0.0,
        "end_intro": t_intro,
        "start_question": t_intro + t_delay,
        "end_question": t_intro + t_delay + t_question,
        "start_opt0": t_intro + t_delay + t_question + t_delay,
        "end_opt0": t_intro + t_delay + t_question + t_delay + t_opt0,
        "start_opt1": t_intro + t_delay + t_question + t_delay + t_opt0 + t_delay,
        "end_opt1": t_intro + t_delay + t_question + t_delay + t_opt0 + t_delay + t_opt1,
        "start_opt2": t_intro + t_delay + t_question + t_delay + t_opt0 + t_delay + t_opt1 + t_delay,
        "end_opt2": t_intro + t_delay + t_question + t_delay + t_opt0 + t_delay + t_opt1 + t_delay + t_opt2,
        "start_opt3": t_intro + t_delay + t_question + t_delay + t_opt0 + t_delay + t_opt1 + t_delay + t_opt2 + t_delay,
        "end_opt3": t_intro + t_delay + t_question + t_delay + t_opt0 + t_delay + t_opt1 + t_delay + t_opt2 + t_delay + t_opt3,
        "start_outro": t_intro + t_delay + t_question + t_delay + t_opt0 + t_delay + t_opt1 + t_delay + t_opt2 + t_delay + t_opt3 + t_delay,
        "end_outro": t_q_target
    }
    
    total_audio_time = t_q_target + t_c_target + t_r_target + t_e0_target + t_e1_target + t_e2_target + t_e3_target
    
    # 4. Merge Audios (countdown uses tick_audio - TikTok style!)
    print("Concatenating all 19 audio segments...")
    merged_audio = temp_dir / "quiz_final.wav"
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
        '-i', str(last_silence),      # 11 (Aligned silence)
        '-i', str(q_outro_audio),     # 12
        '-i', str(tick_audio),        # 13 (Ticks aligned to number changes)
        '-i', str(r_audio_padded),    # 14
        '-i', str(e0_audio_padded),   # 15
        '-i', str(e1_audio_padded),   # 16
        '-i', str(e2_audio_padded),   # 17
        '-i', str(e3_audio_padded),   # 18
        '-filter_complex', '[0:a][1:a][2:a][3:a][4:a][5:a][6:a][7:a][8:a][9:a][10:a][11:a][12:a][13:a][14:a][15:a][16:a][17:a][18:a]concat=n=19:v=0:a=1[outa]',
        '-map', '[outa]',
        str(merged_audio)
    ]
    subprocess.run(cmd_merge, capture_output=True)
    
    # 6. Render Frames
    frame_paths = await render_html_frames(quiz_data, n_q, n_c, n_r, n_e0, n_e1, n_e2, n_e3, timings)
    
    # 7. Compose Video
    video_path = compose_quiz_video(frame_paths, merged_audio, question_data["id"])
    
    # Cleanup temp files
    for frame in frame_paths:
        try: os.remove(frame)
        except: pass
    for audio in [q_intro_audio, q_question_audio, q_opt0_audio, q_opt1_audio,
                  q_opt2_audio, q_opt3_audio, q_outro_audio, r_audio,
                  tick_audio, opt_silence, e0_audio, e1_audio, e2_audio, e3_audio,
                  last_silence, r_audio_padded, e0_audio_padded, e1_audio_padded,
                  e2_audio_padded, e3_audio_padded]:
        try: os.remove(audio)
        except: pass

    if not video_path or not video_path.exists():
        print("Error: Video file was not created!")
        return

    # 8. Upload to YouTube (if not dry run and credentials exist)
    token_json = PROJECT_ROOT / "token.json"
    video_uploaded = False
    
    if not args.dry_run and token_json.exists():
        print("\nUploading to YouTube...")
        try:
            from src.uploader import YouTubeUploader
            uploader = YouTubeUploader()
            
            # Generate SEO optimized metadata
            chapter_num = question_data['chapter'].split(':')[0].replace('CHAPTER', '').strip()
            title = f"Lucent GK Quiz: {question_data['question_hi'][:45]}... | #shorts #gk #lucentgk"
            
            description = f"""📚 Lucent सामान्य ज्ञान Series - Indian Polity (भारतीय राजव्यवस्था)

❓ प्रश्न:
{question_data['question_hi']}

🔤 विकल्प:
A. {question_data['opt0_hi']}
B. {question_data['opt1_hi']}
C. {question_data['opt2_hi']}
D. {question_data['opt3_hi']}

💬 सही उत्तर कमेंट में बताइए!

📖 Chapter: {question_data['chapter']}
📌 Topic: {question_data['topic']}

#shorts #gk #lucentgk #gkinhindi #politygk #constitution #exam #upsc #ssc #railway
"""
            tags = ["lucent gk", "polity gk", "gk shorts", "indian constitution", "gk in hindi", "ssc gk", "upsc polity"]
            
            metadata = {
                "title": title,
                "description": description,
                "tags": tags
            }
            
            # Upload video (CategoryId '27' is Education)
            video_id = uploader.upload_video(
                video_path=str(video_path),
                metadata=metadata,
                schedule=False # Upload as public immediately
            )
            
            if video_id:
                print(f"✅ Upload successful! Video ID: {video_id}")
                video_uploaded = True
                
        except Exception as e:
            print(f"❌ YouTube Upload failed: {e}")
    else:
        print("\n[Skip] YouTube upload skipped (dry-run or token.json missing)")

    # 9. Update progress and history
    if video_path and video_path.exists() and (args.dry_run or token_json.exists()):
        # Save progress increment
        with open(progress_path, 'w', encoding='utf-8') as f:
            json.dump({"current_id": question_data["id"] + 1}, f, ensure_ascii=False, indent=2)
            
        # Update history
        history_path = PROJECT_ROOT / "data/video_history.json"
        history = []
        if history_path.exists():
            try:
                with open(history_path, 'r', encoding='utf-8') as f:
                    history = json.load(f)
            except:
                pass
                
        history.append({
            "id": question_data["id"],
            "topic": question_data["topic"],
            "question": question_data["question_hi"],
            "video_file": video_path.name,
            "uploaded": video_uploaded,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
        
        with open(history_path, 'w', encoding='utf-8') as f:
            json.dump(history, f, ensure_ascii=False, indent=2)

        print(f"Progress updated! Next question ID: {question_data['id'] + 1}")

        # Clean up local video file if running locally to save disk space
        if os.environ.get("GITHUB_ACTIONS") != "true":
            try:
                if video_path.exists():
                    os.remove(video_path)
                    print(f"Cleaned up local video file to save disk space: {video_path}")
            except Exception as e:
                print(f"Could not delete local video file: {e}")

if __name__ == "__main__":
    asyncio.run(main())
