import os
import sys
import json
import math
import asyncio
import subprocess
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
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

def hex_to_rgb(hex_color):
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

def get_font(size, bold=False):
    font_paths = [
        str(PROJECT_ROOT / 'assets/fonts/Montserrat-Bold.ttf'),
        'C:/Windows/Fonts/arialbd.ttf' if bold else 'C:/Windows/Fonts/arial.ttf',
        'C:/Windows/Fonts/segoeuib.ttf' if bold else 'C:/Windows/Fonts/segoeui.ttf',
    ]
    for path in font_paths:
        try:
            return ImageFont.truetype(path, size)
        except:
            continue
    return ImageFont.load_default()

def draw_gradient_vertical(draw, x0, y0, x1, y1, color_start, color_end):
    r1, g1, b1 = hex_to_rgb(color_start)
    r2, g2, b2 = hex_to_rgb(color_end)
    height = y1 - y0
    for y in range(y0, y1):
        ratio = (y - y0) / height
        r = int(r1 + (r2 - r1) * ratio)
        g = int(g1 + (g2 - g1) * ratio)
        b = int(b1 + (b2 - b1) * ratio)
        draw.line([(x0, y), (x1, y)], fill=(r, g, b))

def draw_glow_circle(img, cx, cy, r, color_rgb):
    """Draw soft glow mesh circle."""
    overlay = Image.new('RGBA', img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    for i in range(r, 0, -4):
        alpha = int(35 * (1 - i / r) ** 2)
        if alpha > 0:
            draw.ellipse([(cx - i, cy - i), (cx + i, cy + i)], fill=color_rgb + (alpha,))
    img.alpha_composite(overlay)

def draw_glassy_card(draw, img, x0, y0, x1, y1, border_color=(255, 255, 255, 50), fill_color=(255, 255, 255, 12), radius=30):
    overlay = Image.new('RGBA', img.size, (0, 0, 0, 0))
    ol_draw = ImageDraw.Draw(overlay)
    ol_draw.rounded_rectangle([(x0, y0), (x1, y1)], radius=radius, fill=fill_color, outline=border_color, width=2)
    img.alpha_composite(overlay)

def draw_text_inside_card(draw, text, cx, cy, font, color, max_width=800):
    words = text.split()
    lines = []
    current = []
    for word in words:
        candidate = ' '.join(current + [word])
        bbox = draw.textbbox((0, 0), candidate, font=font)
        if current and bbox[2] - bbox[0] > max_width:
            lines.append(' '.join(current))
            current = [word]
        else:
            current.append(word)
    if current:
        lines.append(' '.join(current))
    
    line_h = draw.textbbox((0,0), "Ag", font=font)[3] - draw.textbbox((0,0), "Ag", font=font)[1]
    total_h = len(lines) * line_h + (len(lines) - 1) * 12
    start_y = cy - total_h // 2
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=font)
        tw = bbox[2] - bbox[0]
        tx = cx - tw // 2
        draw.text((tx, start_y), line, fill=color, font=font)
        start_y += line_h + 12

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
    """Generate audio using edge-tts."""
    import edge_tts
    temp_dir = PROJECT_ROOT / "temp_audio"
    temp_dir.mkdir(exist_ok=True)
    output_path = temp_dir / filename
    communicate = edge_tts.Communicate(text, 'hi-IN-MadhurNeural')
    await communicate.save(str(output_path))
    return output_path

def render_quiz_frames(data, n_question, n_countdown, n_reveal):
    """Render frames synced exactly with the calculated audio phase durations."""
    temp_frames_dir = PROJECT_ROOT / "temp_frames"
    temp_frames_dir.mkdir(exist_ok=True)
    
    for f in temp_frames_dir.glob("frame_*.png"):
        try:
            os.remove(f)
        except:
            pass

    total_frames = n_question + n_countdown + n_reveal
    print(f"Rendering {total_frames} frames (Q: {n_question}, C: {n_countdown}, R: {n_reveal})...")
    
    # Elegant Color Palette
    bg_start = "#090A0F"  # Rich Dark Gray-Blue
    bg_end = "#131525"    # Midnight Indigo
    glow_cyan = (6, 182, 212)
    glow_purple = (139, 92, 246)
    
    font_question = get_font(44, bold=True)
    font_option = get_font(36, bold=True)
    font_timer = get_font(60, bold=True)
    font_footer = get_font(28, bold=True)
    
    frame_paths = []
    
    for frame_idx in range(total_frames):
        img = Image.new('RGBA', (WIDTH, HEIGHT))
        draw = ImageDraw.Draw(img)
        
        # 1. Base Gradient Background
        draw_gradient_vertical(draw, 0, 0, WIDTH, HEIGHT, bg_start, bg_end)
        
        # 2. Draw Soft Mesh Glows (Depth Effect)
        draw_glow_circle(img, WIDTH - 100, 300, 350, glow_cyan)
        draw_glow_circle(img, 100, 1500, 450, glow_purple)
        
        # 3. Question Card (Shifted higher, premium design)
        draw_glassy_card(draw, img, 60, 120, WIDTH - 60, 440, radius=25)
        draw_text_inside_card(draw, data["question"], WIDTH // 2, 280, font_question, (255, 255, 255, 245), max_width=880)
        
        # 4. Timer Section
        timer_cx, timer_cy = WIDTH // 2, 580
        timer_radius = 65
        
        is_q_phase = frame_idx < n_question
        is_c_phase = (frame_idx >= n_question) and (frame_idx < n_question + n_countdown)
        
        # Draw Timer
        if is_q_phase:
            # Question is being read, timer is static at 5
            draw_glassy_card(draw, img, timer_cx - 55, timer_cy - 55, timer_cx + 55, timer_cy + 55, radius=55, fill_color=(255, 255, 255, 10), border_color=(255, 255, 255, 30))
            draw.ellipse([(timer_cx - timer_radius, timer_cy - timer_radius), (timer_cx + timer_radius, timer_cy + timer_radius)], outline=(245, 158, 11, 240), width=6)
            draw.text((timer_cx, timer_cy), "5", fill=(245, 158, 11, 240), font=font_timer, anchor='mm')
        elif is_c_phase:
            # Countdown is active (5 seconds)
            progress = (frame_idx - n_question) / n_countdown
            angle = 360 * (1 - progress)
            
            draw_glassy_card(draw, img, timer_cx - 55, timer_cy - 55, timer_cx + 55, timer_cy + 55, radius=55, fill_color=(255, 255, 255, 10), border_color=(255, 255, 255, 30))
            draw.ellipse([(timer_cx - timer_radius, timer_cy - timer_radius), (timer_cx + timer_radius, timer_cy + timer_radius)], outline=(255, 255, 255, 20), width=6)
            
            overlay = Image.new('RGBA', img.size, (0, 0, 0, 0))
            ol_draw = ImageDraw.Draw(overlay)
            ol_draw.arc([(timer_cx - timer_radius, timer_cy - timer_radius), (timer_cx + timer_radius, timer_cy + timer_radius)], start=-90, end=-90 + angle, fill=(245, 158, 11, 255), width=8)
            img.alpha_composite(overlay)
            
            seconds_left = 5 - int((frame_idx - n_question) / 30)
            draw.text((timer_cx, timer_cy), str(max(1, seconds_left)), fill=(245, 158, 11, 240), font=font_timer, anchor='mm')
        else:
            # Reveal Phase
            draw.ellipse([(timer_cx - timer_radius, timer_cy - timer_radius), (timer_cx + timer_radius, timer_cy + timer_radius)], fill=(16, 185, 129, 30), outline=(16, 185, 129, 255), width=6)
            draw.text((timer_cx, timer_cy), "✓", fill=(16, 185, 129, 255), font=font_timer, anchor='mm')
            
        # 5. Options Section
        opt_y_starts = [740, 880, 1020, 1160]
        opt_h = 100
        
        for i, opt in enumerate(data["options"]):
            y0 = opt_y_starts[i]
            y1 = y0 + opt_h
            
            card_fill = (255, 255, 255, 10)
            card_border = (255, 255, 255, 30)
            text_color = (255, 255, 255, 220)
            
            # If in Reveal Phase
            if not (is_q_phase or is_c_phase):
                if i == data["correct"]:
                    card_fill = (16, 185, 129, 50)
                    card_border = (16, 185, 129, 255)
                    text_color = (16, 185, 129, 255)
                    
                    # Renders indicator badge on correct card
                    draw.rounded_rectangle([(WIDTH - 280, y0 + 20), (WIDTH - 120, y1 - 20)], radius=10, fill=(16, 185, 129, 100))
                    draw.text((WIDTH - 200, y0 + opt_h // 2), "CORRECT", fill=(255, 255, 255), font=get_font(20, bold=True), anchor='mm')
                else:
                    text_color = (255, 255, 255, 70)
                    card_fill = (0, 0, 0, 50)
                    card_border = (255, 255, 255, 10)
                    
            draw_glassy_card(draw, img, 120, y0, WIDTH - 120, y1, fill_color=card_fill, border_color=card_border, radius=18)
            draw.text((160, y0 + opt_h // 2), f"{chr(65+i)}) {opt}", fill=text_color, font=font_option, anchor='lm')
            
        # 6. Bottom Call to Action Card
        draw_glassy_card(draw, img, 120, 1450, WIDTH - 120, 1600, fill_color=(139, 92, 246, 15), border_color=(245, 158, 11, 70), radius=22)
        draw.text((WIDTH // 2, 1495), "COMMENT YOUR SCORE!", fill=(255, 255, 255, 230), font=font_footer, anchor='mm')
        draw.text((WIDTH // 2, 1550), "Like & Share to challenge your friends!", fill=(255, 255, 255, 150), font=get_font(24), anchor='mm')
        
        # Save frame
        frame_path = temp_frames_dir / f"frame_{str(frame_idx).zfill(3)}.png"
        img.save(frame_path)
        frame_paths.append(str(frame_path))
        
    return frame_paths

def compose_quiz_video(frame_paths, audio_path):
    """Compile frames and audio into final video using FFmpeg."""
    outputs_dir = PROJECT_ROOT / "outputs"
    outputs_dir.mkdir(exist_ok=True)
    output_video_path = outputs_dir / "quiz_single.mp4"
    
    # Concat file for ffmpeg
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
    # Quiz Data
    quiz_data = {
        "question": "Which site is famous for prehistoric rock paintings?",
        "options": ["Harappa", "Bhimbetka", "Lothal", "Dholavira"],
        "correct": 1,
        "q_narration": "क्या आप इस सवाल का जवाब जानते हैं? सवाल है: कौन सा स्थल प्रागैतिहासिक शैल चित्रों के लिए प्रसिद्ध है? आपका समय शुरू होता है अब!",
        "r_narration": "समय समाप्त! सही जवाब है बी, भीमबेटका! क्या आपका जवाब सही था? कमेंट में बताएं और दोस्तों को शेयर करें!"
    }
    
    temp_dir = PROJECT_ROOT / "temp_audio"
    temp_dir.mkdir(exist_ok=True)
    
    # 1. Generate Voiceovers
    print("\nGenerating Audio Voiceovers...")
    q_audio = await generate_tts(quiz_data["q_narration"], "question.mp3")
    r_audio = await generate_tts(quiz_data["r_narration"], "reveal.mp3")
    
    # 2. Generate Silence Audio for the 5s countdown
    print("Generating 5s silence audio track...")
    silence_audio = temp_dir / "silence.mp3"
    cmd_silence = [
        'ffmpeg', '-y',
        '-f', 'lavfi', '-i', 'anullsrc=r=24000:cl=mono',
        '-t', '5.0',
        '-c:a', 'libmp3lame',
        str(silence_audio)
    ]
    subprocess.run(cmd_silence, capture_output=True)
    
    # 3. Measure Durations
    t_q = get_audio_duration(q_audio)
    t_c = 5.0  # exactly 5 seconds
    t_r = get_audio_duration(r_audio)
    
    print(f"Durations measured -> Q: {t_q}s, Countdown: {t_c}s, Reveal: {t_r}s")
    
    # 4. Merge Audios
    print("Concatenating audio segments...")
    merged_audio = temp_dir / "quiz_final.mp3"
    cmd_merge = [
        'ffmpeg', '-y',
        '-i', str(q_audio),
        '-i', str(silence_audio),
        '-i', str(r_audio),
        '-filter_complex', '[0:a][1:a][2:a]concat=n=3:v=0:a=1[outa]',
        '-map', '[outa]',
        str(merged_audio)
    ]
    subprocess.run(cmd_merge, capture_output=True)
    
    # 5. Calculate Frame counts
    n_q = int(t_q * FPS)
    n_c = int(t_c * FPS)
    n_r = int(t_r * FPS)
    
    # 6. Render Frames
    print("\nRendering video frames...")
    frame_paths = render_quiz_frames(quiz_data, n_q, n_c, n_r)
    
    # 7. Compose Video
    print("\nComposing final MP4 video...")
    video_path = compose_quiz_video(frame_paths, merged_audio)
    
    # Cleanup temp frames
    print("\nCleaning up temporary files...")
    for frame in frame_paths:
        try:
            os.remove(frame)
        except:
            pass
    try:
        os.remove(q_audio)
        os.remove(r_audio)
        os.remove(silence_audio)
    except:
        pass
            
    print(f"\nDone! Final video is available at: {video_path}")

if __name__ == "__main__":
    asyncio.run(main())
