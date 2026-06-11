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

def draw_glow_circle(img, cx, cy, r, color_rgb, opacity=50):
    """Draw soft glow mesh circle."""
    overlay = Image.new('RGBA', img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    for i in range(r, 0, -4):
        alpha = int(opacity * (1 - i / r) ** 2)
        if alpha > 0:
            draw.ellipse([(cx - i, cy - i), (cx + i, cy + i)], fill=color_rgb + (alpha,))
    img.alpha_composite(overlay)

def draw_glassy_card(draw, img, x0, y0, x1, y1, border_color=(255, 255, 255, 50), fill_color=(255, 255, 255, 12), radius=30):
    overlay = Image.new('RGBA', img.size, (0, 0, 0, 0))
    ol_draw = ImageDraw.Draw(overlay)
    ol_draw.rounded_rectangle([(x0, y0), (x1, y1)], radius=radius, fill=fill_color, outline=border_color, width=2)
    img.alpha_composite(overlay)

def draw_left_aligned_text(draw, text, x, y, font, color, max_width=840):
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
    current_y = y
    for line in lines:
        draw.text((x, current_y), line, fill=color, font=font)
        current_y += line_h + 12

def draw_react_option_card(draw, img, x0, y0, x1, y1, letter, text, state, font_text, font_letter, font_pill, radius=24):
    """Draws a card mimicking the React web app options styling exactly."""
    # Premium Soft Box Shadow (stacked layers)
    for offset in range(1, 6):
        alpha = int(15 * (1 - offset / 6))
        draw.rounded_rectangle([(x0, y0 + offset), (x1, y1 + offset)], radius=radius, fill=(15, 23, 42, alpha))
        
    if state == 'normal':
        card_fill = (255, 255, 255, 190)  # bg-white/75 feel
        card_border = (255, 255, 255, 255)
        circle_fill = hex_to_rgb("#F1EEF8")
        circle_text = hex_to_rgb("#5C6BC0")
        pill_fill = hex_to_rgb("#F0EFF7")
        pill_text = hex_to_rgb("#9E9DB0")
        pill_label = "CHUNEIN"
        text_color = hex_to_rgb("#1E293B")
    elif state == 'correct':
        card_fill = hex_to_rgb("#E2F5EE")  # bg-[#E2F5EE]
        card_border = hex_to_rgb("#4CD3A2")
        circle_fill = hex_to_rgb("#00BFA5")
        circle_text = (255, 255, 255)
        pill_fill = hex_to_rgb("#00BFA5")
        pill_text = (255, 255, 255)
        pill_label = "SAHI JAVAB ✔"
        text_color = hex_to_rgb("#065F46")
    elif state == 'incorrect':
        card_fill = hex_to_rgb("#FDF0F1")  # bg-[#FDF0F1]
        card_border = hex_to_rgb("#FF6584")
        circle_fill = hex_to_rgb("#FF4066")
        circle_text = (255, 255, 255)
        pill_fill = hex_to_rgb("#FF4066")
        pill_text = (255, 255, 255)
        pill_label = "GALAT JAVAB ❌"
        text_color = hex_to_rgb("#991B1B")
    elif state == 'dimmed':
        card_fill = (255, 255, 255, 50)  # bg-white/20 with opacity
        card_border = (255, 255, 255, 30)
        circle_fill = (241, 238, 248, 50)
        circle_text = (92, 107, 192, 50)
        pill_fill = (240, 239, 247, 50)
        pill_text = (158, 157, 176, 50)
        pill_label = "CHUNEIN"
        text_color = (30, 41, 59, 50)

    # Draw Card Face
    draw.rounded_rectangle([(x0, y0), (x1, y1)], radius=radius, fill=card_fill, outline=card_border, width=2)
    
    # Draw Circle Indicator (Left)
    circle_cx, circle_cy = x0 + 60, y0 + 72
    draw.ellipse([(circle_cx - 28, circle_cy - 28), (circle_cx + 28, circle_cy + 28)], fill=circle_fill)
    draw.text((circle_cx, circle_cy), letter, fill=circle_text, font=font_letter, anchor='mm')
    
    # Draw Option Text (Right, top-aligned)
    draw.text((x0 + 120, y0 + 44), text, fill=text_color, font=font_text, anchor='lm')
    
    # Draw Pill Action Button (Bottom)
    pill_x0 = x0 + 120
    pill_y0 = y0 + 82
    pill_w = draw.textbbox((0, 0), pill_label, font=font_pill)[2] - draw.textbbox((0, 0), pill_label, font=font_pill)[0] + 32
    pill_h = 34
    draw.rounded_rectangle([(pill_x0, pill_y0), (pill_x0 + pill_w, pill_y0 + pill_h)], radius=10, fill=pill_fill)
    draw.text((pill_x0 + pill_w // 2, pill_y0 + pill_h // 2), pill_label, fill=pill_text, font=font_pill, anchor='mm')

def draw_explanation_card(draw, img, x0, y0, x1, y1, text, font_title, font_body, radius=22):
    """Draws the Maitripurn Jankari drawer at the bottom."""
    # Box Shadow
    for offset in range(1, 5):
        draw.rounded_rectangle([(x0, y0 + offset), (x1, y1 + offset)], radius=radius, fill=(15, 23, 42, 10))
    
    # Soft white glassmorphic base (bg-white/85)
    draw_glassy_card(draw, img, x0, y0, x1, y1, fill_color=(255, 255, 255, 220), border_color=(255, 255, 255, 150), radius=radius)
    
    # Title
    draw.text((x0 + 30, y0 + 35), "Maitripurn Jankari 💡", fill=hex_to_rgb("#1E293B"), font=font_title, anchor='lm')
    
    # Body text
    draw_left_aligned_text(draw, text, x0 + 30, y0 + 65, font_body, hex_to_rgb("#475569"), max_width=(x1 - x0 - 60))

def draw_next_button(draw, x0, y0, x1, y1, text, font, radius=16):
    """Draws next button."""
    # Shadow
    draw.rounded_rectangle([(x0, y0 + 4), (x1, y1 + 4)], radius=radius, fill=(123, 31, 162, 40))
    # Face
    draw.rounded_rectangle([(x0, y0), (x1, y1)], radius=radius, fill=hex_to_rgb("#9333EA"))
    # Text
    draw.text((x0 + (x1 - x0) // 2, y0 + (y1 - y0) // 2), text, fill=(255, 255, 255), font=font, anchor='mm')

def get_audio_duration(file_path):
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
    import edge_tts
    temp_dir = PROJECT_ROOT / "temp_audio"
    temp_dir.mkdir(exist_ok=True)
    output_path = temp_dir / filename
    communicate = edge_tts.Communicate(text, 'hi-IN-MadhurNeural')
    await communicate.save(str(output_path))
    return output_path

def render_quiz_frames(data, n_question, n_countdown, n_reveal):
    temp_frames_dir = PROJECT_ROOT / "temp_frames"
    temp_frames_dir.mkdir(exist_ok=True)
    
    for f in temp_frames_dir.glob("frame_*.png"):
        try:
            os.remove(f)
        except:
            pass

    total_frames = n_question + n_countdown + n_reveal
    print(f"Rendering {total_frames} frames in replica web app design...")
    
    # Soft Pastel backgrounds
    bg_start = "#E5DDF5"  # Soft Lavender background
    bg_end = "#E5DDF5"
    glow_purple = (216, 180, 254)  # Purple-300 blur
    glow_pink = (244, 143, 177)    # Pink-300 blur
    
    font_hud_title = get_font(26, bold=True)
    font_hud_score = get_font(22, bold=True)
    font_hud_val = get_font(24, bold=True)
    
    font_quest_badge = get_font(20, bold=True)
    font_question = get_font(38, bold=True)
    
    font_opt_text = get_font(32, bold=True)
    font_opt_letter = get_font(24, bold=True)
    font_opt_pill = get_font(18, bold=True)
    
    font_timer = get_font(36, bold=True)
    font_exp_title = get_font(24, bold=True)
    font_exp_body = get_font(22, bold=False)
    font_next = get_font(20, bold=True)
    
    frame_paths = []
    
    for frame_idx in range(total_frames):
        img = Image.new('RGBA', (WIDTH, HEIGHT))
        draw = ImageDraw.Draw(img)
        
        # 1. Base Lavender Background
        draw_gradient_vertical(draw, 0, 0, WIDTH, HEIGHT, bg_start, bg_end)
        
        # 2. Soft Pastel Blur Nodes (No grid lines to match React same-to-same)
        draw_glow_circle(img, -50, -50, 350, glow_purple, opacity=50)
        draw_glow_circle(img, WIDTH + 50, HEIGHT + 50, 450, glow_pink, opacity=40)
        
        # 3. Top Status Bar
        # Purple Dot & Title (Left)
        draw.ellipse([(90 - 10, 100 - 10), (90 + 10, 100 + 10)], fill=hex_to_rgb("#BA68C8"))
        draw.text((120, 100), "LUCENT GK VISHES", fill=hex_to_rgb("#8E24AA"), font=font_hud_title, anchor='lm')
        
        # Score Badge (Right)
        score_x0, score_y0, score_x1, score_y1 = WIDTH - 240, 70, WIDTH - 80, 130
        draw.rounded_rectangle([(score_x0, score_y0), (score_x1, score_y1)], radius=12, fill=(255, 255, 255, 130), outline=(226, 232, 240, 255), width=1)
        draw.text((score_x0 + 40, score_y0 + 30), "SCORE:", fill=hex_to_rgb("#94A3B8"), font=font_hud_score, anchor='mm')
        
        score_val = "10" if frame_idx >= (n_question + n_countdown) else "0"
        draw.text((score_x1 - 40, score_y0 + 30), score_val, fill=hex_to_rgb("#4F46E5"), font=font_hud_val, anchor='mm')
        
        # 4. Question Card (Deep gradient-to-br card)
        y0_q, y1_q = 180, 460
        # Background shadow
        for offset in range(1, 8):
            draw.rounded_rectangle([(60, y0_q + offset), (WIDTH - 60, y1_q + offset)], radius=28, fill=(15, 23, 42, int(20 * (1 - offset/8))))
            
        # Card body
        draw_gradient_vertical(draw, 60, y0_q, WIDTH - 60, y1_q, "#4A154B", "#3F0E40")
        draw.rounded_rectangle([(60, y0_q), (WIDTH - 60, y1_q)], radius=28, fill=None, outline=hex_to_rgb("#521c54"), width=2)
        
        # Pink glow circle inside question card
        draw_glow_circle(img, WIDTH - 60, y0_q, 150, (236, 72, 153), opacity=25)
        
        # Lucent Badge
        draw.rounded_rectangle([(100, 215), (290, 255)], radius=12, fill=(236, 72, 153, 50), outline=hex_to_rgb("#EC4899"), width=1)
        draw.text((195, 235), "LUCENT PRASHNO", fill=hex_to_rgb("#FDA4AF"), font=font_quest_badge, anchor='mm')
        
        # Question text
        draw_left_aligned_text(draw, f'"{data["question"]}"', 100, 280, font_question, (255, 255, 255), max_width=880)
        
        # 5. Options Section (4 Options Cards)
        opt_y_starts = [510, 680, 850, 1020]
        opt_h = 145
        letters = ["A", "B", "C", "D"]
        
        is_q_phase = frame_idx < n_question
        is_c_phase = (frame_idx >= n_question) and (frame_idx < n_question + n_countdown)
        
        for i, opt in enumerate(data["options"]):
            y0 = opt_y_starts[i]
            y1 = y0 + opt_h
            
            # Determine card state
            state = 'normal'
            if not (is_q_phase or is_c_phase):
                if i == data["correct"]:
                    state = 'correct'
                elif i == data["wrong_selected"]:
                    state = 'incorrect'
                else:
                    state = 'dimmed'
                    
            draw_react_option_card(draw, img, 80, y0, WIDTH - 80, y1, letters[i], opt, state, font_opt_text, font_opt_letter, font_opt_pill, radius=24)
            
        # 6. Timer Section (Clean Lavender Progress Orb)
        timer_cx, timer_cy = WIDTH // 2, 1245
        timer_radius = 45
        
        # Base shadow
        draw.ellipse([(timer_cx - timer_radius, timer_cy - timer_radius + 4), (timer_cx + timer_radius, timer_cy + timer_radius + 4)], fill=(15, 23, 42, 30))
        # Orb face
        draw.ellipse([(timer_cx - timer_radius, timer_cy - timer_radius), (timer_cx + timer_radius, timer_cy + timer_radius)], fill=hex_to_rgb("#F1EEF8"), outline=(255, 255, 255, 255), width=3)
        
        if is_q_phase:
            draw.text((timer_cx, timer_cy), "05", fill=hex_to_rgb("#5C6BC0"), font=font_timer, anchor='mm')
        elif is_c_phase:
            progress = (frame_idx - n_question) / n_countdown
            angle = 360 * (1 - progress)
            
            overlay = Image.new('RGBA', img.size, (0, 0, 0, 0))
            ol_draw = ImageDraw.Draw(overlay)
            ol_draw.arc([(timer_cx - timer_radius, timer_cy - timer_radius), (timer_cx + timer_radius, timer_cy + timer_radius)], start=-90, end=-90 + angle, fill=hex_to_rgb("#8E24AA"), width=5)
            img.alpha_composite(overlay)
            
            seconds_left = 5 - int((frame_idx - n_question) / 30)
            draw.text((timer_cx, timer_cy), f"0{max(1, seconds_left)}", fill=hex_to_rgb("#8E24AA"), font=font_timer, anchor='mm')
        else:
            # Green Checkmark on orb
            draw.ellipse([(timer_cx - timer_radius, timer_cy - timer_radius), (timer_cx + timer_radius, timer_cy + timer_radius)], fill=hex_to_rgb("#00BFA5"), outline=(255, 255, 255, 255), width=3)
            draw.text((timer_cx, timer_cy), "✓", fill=(255, 255, 255), font=font_timer, anchor='mm')
            
        # 7. Maitripurn Jankari (Explanation Card) & Next Button (Fade/slide in during reveal)
        if not (is_q_phase or is_c_phase):
            # Explanation card
            draw_explanation_card(draw, img, 80, 1330, WIDTH - 80, 1590, data["explanation"], font_exp_title, font_exp_body, radius=22)
            # Next trigger button
            draw_next_button(draw, WIDTH - 360, 1630, WIDTH - 80, 1710, "Agla Sawaal ➡️", font_next, radius=15)
            
        # Save frame
        frame_path = temp_frames_dir / f"frame_{str(frame_idx).zfill(3)}.png"
        img.save(frame_path)
        frame_paths.append(str(frame_path))
        
    return frame_paths

def compose_quiz_video(frame_paths, audio_path):
    outputs_dir = PROJECT_ROOT / "outputs"
    outputs_dir.mkdir(exist_ok=True)
    output_video_path = outputs_dir / "quiz_single.mp4"
    
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
    # Load first question from the provided React dataset
    quiz_data = {
        "question": "Bharat ke Sanvidhan (Constitution) ka Janak kisse mana jata hai?",
        "options": ["Dr. B. R. Ambedkar", "Dr. Rajendra Prasad", "Jawaharlal Nehru", "Sardar Vallabhbhai Patel"],
        "correct": 0,
        "wrong_selected": 1, # Dr. Rajendra Prasad selected incorrectly for dramatic effect
        "explanation": "Dr. Bhimrao Ramji Ambedkar ko Bhartiya Sanvidhan ki Drafting Committee ka chairman hone ke nate Sanvidhan ka Janak mana jata hai.",
        "q_narration": "क्या आप जानते हैं भारत के संविधान का जनक किसे माना जाता है? आपके विकल्प हैं: ए, डॉक्टर बी आर अंबेडकर, बी, डॉक्टर राजेंद्र प्रसाद, सी, जवाहरलाल नेहरू, या डी, सरदार वल्लभभाई पटेल। आपका समय शुरू होता है अब!",
        "r_narration": "समय समाप्त! सही जवाब है ए, डॉक्टर बी आर अंबेडकर। डॉक्टर भीमराव रामजी अंबेडकर को भारतीय संविधान की ड्राफ्टिंग कमेटी का चेयरमैन होने के नाते संविधान का जनक माना जाता है। क्या आपका जवाब सही था? कमेंट में बताएं!"
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
