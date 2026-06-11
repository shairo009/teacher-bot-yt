import os
import sys
import json
import math
import random
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
ROUND_1_FRAMES = 90  # 3s for Player 1
ROUND_2_FRAMES = 90  # 3s for Player 2
RESULT_FRAMES = 60   # 2s for Winner Screen
TOTAL_FRAMES = ROUND_1_FRAMES + ROUND_2_FRAMES + RESULT_FRAMES  # 240 frames (8s)

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

def draw_glassy_card(draw, img, x0, y0, x1, y1, border_color=(255, 255, 255, 60), fill_color=(255, 255, 255, 18), radius=30):
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

def draw_dim_overlay(img, x0, y0, x1, y1, opacity=140):
    overlay = Image.new('RGBA', img.size, (0, 0, 0, 0))
    ol_draw = ImageDraw.Draw(overlay)
    ol_draw.rectangle([(x0, y0), (x1, y1)], fill=(0, 0, 0, opacity))
    img.alpha_composite(overlay)

async def get_quiz_battle_data():
    """Return specific Lucent GK questions for the battle."""
    return {
        "p1_question": "Which site is famous for prehistoric rock paintings?",
        "p1_options": ["Harappa", "Bhimbetka", "Lothal", "Dholavira"],
        "p1_correct": 1,
        "p2_question": "In which year was the Battle of Plassey fought?",
        "p2_options": ["1764", "1757", "1857", "1748"],
        "p2_correct": 1,
        "p2_wrong": 0,
        "narration": "दो प्लेयर क्विज़ बैटल! राउंड वन प्लेयर वन के लिए: कौन सा स्थल प्रागैतिहासिक शैल चित्रों के लिए प्रसिद्ध है? ... भीमबेटका बिल्कुल सही जवाब! प्लेयर वन को मिलता है एक पॉइंट। राउंड टू प्लेयर टू के लिए: प्लासी का युद्ध किस वर्ष लड़ा गया था? ... सत्रह सौ सत्तावन सही जवाब है! लेकिन प्लेयर टू ने सत्रह सौ चौंसठ चुना और मिस कर दिया! प्लेयर वन की जीत! अपने दोस्त को चैलेंज करने के लिए टैग करें!"
    }   
    # Fallback Quiz Data
    return {
        "p1_question": "What is the largest ocean on Earth?",
        "p1_options": ["Atlantic", "Indian", "Pacific"],
        "p1_correct": 2,
        "p2_question": "What is the powerhouse of the cell?",
        "p2_options": ["Nucleus", "Mitochondria", "Ribosome"],
        "p2_correct": 1,
        "p2_wrong": 0,
        "narration": "दो प्लेयर क्विज़ बैटल! राउंड वन प्लेयर वन के लिए: दुनिया का सबसे बड़ा महासागर कौन सा है? ... पैसिफिक बिल्कुल सही जवाब! प्लेयर वन को मिलता है एक पॉइंट। राउंड टू प्लेयर टू के लिए: सेल का पावरहाउस क्या है? ... माइटोकॉन्ड्रिया सही जवाब है! लेकिन प्लेयर टू ने न्यूक्लियस चुना और मिस कर दिया!  प्लेयर वन की जीत! अपने दोस्त को चैलेंज करने के लिए टैग करें!"
    }

async def generate_narration_audio(text):
    """Generate high-quality TTS audio file."""
    import edge_tts
    temp_dir = PROJECT_ROOT / "temp_audio"
    temp_dir.mkdir(exist_ok=True)
    output_path = temp_dir / "quiz_narration.mp3"
    
    # High-energy Hindi voice
    communicate = edge_tts.Communicate(text, 'hi-IN-MadhurNeural')
    await communicate.save(str(output_path))
    return output_path

def render_frames(data):
    """Render all frames for the Quiz Battle Shorts video using Pillow."""
    temp_frames_dir = PROJECT_ROOT / "temp_frames"
    temp_frames_dir.mkdir(exist_ok=True)
    
    for f in temp_frames_dir.glob("frame_*.png"):
        try:
            os.remove(f)
        except:
            pass

    print(f"Rendering {TOTAL_FRAMES} frames...")
    
    # Color Gradients
    # Player 1 (Blue)
    color_p1_start = "#0F172A" # Dark blue/black
    color_p1_end = "#1E3A8A"   # Royal navy blue
    # Player 2 (Green)
    color_p2_start = "#064E3B" # Dark forest green
    color_p2_end = "#022C22"   # Deep green/black
    
    font_header = get_font(42, bold=True)
    font_badge = get_font(28, bold=True)
    font_score = get_font(48, bold=True)
    font_question = get_font(34, bold=True)
    font_option = get_font(32, bold=True)
    font_result = get_font(90, bold=True)
    
    frame_paths = []
    
    # Split screen boundary: Top half is y=120 to y=1020, Bottom half is y=1020 to y=1920
    mid_y = 990
    
    p1_score = 0
    p2_score = 0
    
    for frame_idx in range(TOTAL_FRAMES):
        img = Image.new('RGBA', (WIDTH, HEIGHT))
        draw = ImageDraw.Draw(img)
        
        # 1. Base Gradients for Split Screen
        draw_gradient_vertical(draw, 0, 0, WIDTH, mid_y, color_p1_start, color_p1_end)
        draw_gradient_vertical(draw, 0, mid_y, WIDTH, HEIGHT, color_p2_start, color_p2_end)
        
        # 2. Draw Middle Neon Boundary Line
        draw.line([(0, mid_y), (WIDTH, mid_y)], fill=(255, 255, 255, 100), width=6)
        
        # 3. Determine Phase
        is_p1_turn = frame_idx < ROUND_1_FRAMES
        is_p2_turn = (frame_idx >= ROUND_1_FRAMES) and (frame_idx < ROUND_1_FRAMES + ROUND_2_FRAMES)
        is_result_phase = frame_idx >= (ROUND_1_FRAMES + ROUND_2_FRAMES)
        
        # 4. Scores and Badges positioning
        # Player 1 Header Bar
        draw.rounded_rectangle([(60, 40), (280, 90)], radius=12, fill=hex_to_rgb("#2563EB"))
        draw.text((170, 65), "PLAYER 1", fill=(255, 255, 255), font=font_badge, anchor='mm')
        
        # Player 2 Header Bar
        draw.rounded_rectangle([(60, mid_y + 40), (280, mid_y + 90)], radius=12, fill=hex_to_rgb("#10B981"))
        draw.text((170, mid_y + 65), "PLAYER 2", fill=(255, 255, 255), font=font_badge, anchor='mm')
        
        # Scores
        if not is_p1_turn:
            p1_score = 1 # Player 1 answered correctly
        if is_result_phase:
            p2_score = 0 # Player 2 answered wrongly
            
        draw.text((WIDTH - 120, 65), f"SCORE: {p1_score}", fill=(255, 255, 255), font=font_score, anchor='rm')
        draw.text((WIDTH - 120, mid_y + 65), f"SCORE: {p2_score}", fill=(255, 255, 255), font=font_score, anchor='rm')
        
        # 5. Draw Player 1 Area Content
        # Question Card
        draw_glassy_card(draw, img, 60, 120, WIDTH - 60, mid_y - 80)
        # Options Cards
        opt_y_starts_p1 = [350, 460, 570, 680]
        opt_h = 90
        
        # Render P1 Question
        draw_text_inside_card(draw, data["p1_question"], WIDTH // 2, 240, font_question, (255, 255, 255, 240))
        
        # Render P1 Options
        for i, opt in enumerate(data["p1_options"]):
            y0 = opt_y_starts_p1[i]
            y1 = y0 + opt_h
            
            # Determine card highlighting
            card_fill = (255, 255, 255, 12)
            card_border = (255, 255, 255, 40)
            text_color = (255, 255, 255, 220)
            
            if is_p1_turn:
                # Timer reveal in the last 1s (30 frames) of P1 round
                if frame_idx >= (ROUND_1_FRAMES - 30):
                    if i == data["p1_correct"]:
                        # Highlight correct answer in green
                        card_fill = (16, 185, 129, 60)
                        card_border = (16, 185, 129, 255)
                        text_color = (16, 185, 129, 255)
                    else:
                        # Dim other options
                        text_color = (255, 255, 255, 80)
            else:
                # After P1 round completes, keep correct option highlighted
                if i == data["p1_correct"]:
                    card_fill = (16, 185, 129, 60)
                    card_border = (16, 185, 129, 255)
                    text_color = (16, 185, 129, 255)
                else:
                    text_color = (255, 255, 255, 80)
                    
            draw_glassy_card(draw, img, 100, y0, WIDTH - 100, y1, fill_color=card_fill, border_color=card_border, radius=16)
            draw.text((140, y0 + opt_h // 2), f"{chr(65+i)}) {opt}", fill=text_color, font=font_option, anchor='lm')
            
        # P1 Timer bar
        if is_p1_turn:
            progress = frame_idx / ROUND_1_FRAMES
            draw.rounded_rectangle([(100, mid_y - 60), (WIDTH - 100, mid_y - 45)], radius=8, fill=(255, 255, 255, 30))
            draw.rounded_rectangle([(100, mid_y - 60), (100 + int((WIDTH - 200) * (1 - progress)), mid_y - 45)], radius=8, fill=hex_to_rgb("#2563EB"))
            
        # 6. Draw Player 2 Area Content
        # Question Card
        draw_glassy_card(draw, img, 60, mid_y + 120, WIDTH - 60, HEIGHT - 120)
        # Options Cards
        opt_y_starts_p2 = [mid_y + 350, mid_y + 460, mid_y + 570, mid_y + 680]
        
        # Render P2 Question
        draw_text_inside_card(draw, data["p2_question"], WIDTH // 2, mid_y + 240, font_question, (255, 255, 255, 240))
        
        # Render P2 Options
        for i, opt in enumerate(data["p2_options"]):
            y0 = opt_y_starts_p2[i]
            y1 = y0 + opt_h
            
            card_fill = (255, 255, 255, 12)
            card_border = (255, 255, 255, 40)
            text_color = (255, 255, 255, 220)
            
            if is_p2_turn:
                # Timer reveal in the last 1s (30 frames) of P2 round
                p2_frame_elapsed = frame_idx - ROUND_1_FRAMES
                if p2_frame_elapsed >= (ROUND_2_FRAMES - 30):
                    if i == data["p2_correct"]:
                        # Highlight correct answer in green
                        card_fill = (16, 185, 129, 60)
                        card_border = (16, 185, 129, 255)
                        text_color = (16, 185, 129, 255)
                    elif i == data["p2_wrong"]:
                        # Highlight player 2's wrong answer in red
                        card_fill = (239, 68, 68, 60)
                        card_border = (239, 68, 68, 255)
                        text_color = (239, 68, 68, 255)
                    else:
                        text_color = (255, 255, 255, 80)
            elif is_result_phase:
                # In result phase, show correct (green) and wrong chosen (red)
                if i == data["p2_correct"]:
                    card_fill = (16, 185, 129, 60)
                    card_border = (16, 185, 129, 255)
                    text_color = (16, 185, 129, 255)
                elif i == data["p2_wrong"]:
                    card_fill = (239, 68, 68, 60)
                    card_border = (239, 68, 68, 255)
                    text_color = (239, 68, 68, 255)
                else:
                    text_color = (255, 255, 255, 80)
                    
            draw_glassy_card(draw, img, 100, y0, WIDTH - 100, y1, fill_color=card_fill, border_color=card_border, radius=16)
            draw.text((140, y0 + opt_h // 2), f"{chr(65+i)}) {opt}", fill=text_color, font=font_option, anchor='lm')
            
        # P2 Timer bar
        if is_p2_turn:
            progress = (frame_idx - ROUND_1_FRAMES) / ROUND_2_FRAMES
            draw.rounded_rectangle([(100, HEIGHT - 100), (WIDTH - 100, HEIGHT - 85)], radius=8, fill=(255, 255, 255, 30))
            draw.rounded_rectangle([(100, HEIGHT - 100), (100 + int((WIDTH - 200) * (1 - progress)), HEIGHT - 85)], radius=8, fill=hex_to_rgb("#10B981"))
            
        # 7. Apply Dimming for Non-active Turns
        if is_p1_turn:
            draw_dim_overlay(img, 0, mid_y, WIDTH, HEIGHT, opacity=140)
        elif is_p2_turn:
            draw_dim_overlay(img, 0, 0, WIDTH, mid_y, opacity=140)
            
        # 8. Render Result Overlay Screen (Last 2s)
        if is_result_phase:
            # Full screen glassmorphic block
            draw_dim_overlay(img, 0, 0, WIDTH, HEIGHT, opacity=180)
            
            # Winner Banner Card in center
            draw_glassy_card(draw, img, 80, HEIGHT // 2 - 240, WIDTH - 80, HEIGHT // 2 + 240, border_color=(251, 191, 36, 180), fill_color=(17, 24, 39, 230), radius=35)
            
            # Text announcements
            draw.text((WIDTH // 2, HEIGHT // 2 - 120), "GAME OVER", fill=(255, 255, 255, 180), font=get_font(42), anchor='mm')
            draw.text((WIDTH // 2, HEIGHT // 2), "PLAYER 1 WINS! 👑", fill=(251, 191, 36, 255), font=font_result, anchor='mm')
            draw.text((WIDTH // 2, HEIGHT // 2 + 110), f"Final Score: {p1_score} - {p2_score}", fill=(255, 255, 255, 220), font=font_score, anchor='mm')
            
            # Subtitle challenge
            draw.rounded_rectangle([(WIDTH // 2 - 250, HEIGHT // 2 + 175), (WIDTH // 2 + 250, HEIGHT // 2 + 215)], radius=10, fill=(255, 255, 255, 25))
            draw.text((WIDTH // 2, HEIGHT // 2 + 195), "TAG A FRIEND TO BATTLE!", fill=(255, 255, 255, 240), font=get_font(24, bold=True), anchor='mm')

        # Save frame
        frame_path = temp_frames_dir / f"frame_{str(frame_idx).zfill(3)}.png"
        img.save(frame_path)
        frame_paths.append(str(frame_path))
        
    return frame_paths

def compose_quiz_battle_video(frame_paths, audio_path):
    """Compile frames and audio into final video using FFmpeg."""
    outputs_dir = PROJECT_ROOT / "outputs"
    outputs_dir.mkdir(exist_ok=True)
    output_video_path = outputs_dir / "quiz_battle.mp4"
    
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
    # 1. Fetch Quiz Data
    quiz_data = await get_quiz_battle_data()
    print("\nQuiz Battle Data:")
    print(json.dumps(quiz_data, indent=2))
    
    # 2. Generate Audio Narration
    print("\nGenerating Audio Narration...")
    audio_path = await generate_narration_audio(quiz_data["narration"])
    print(f"Audio generated at: {audio_path}")
    
    # 3. Render Video Frames
    print("\nRendering frames...")
    frame_paths = render_frames(quiz_data)
    
    # 4. Compose Video
    print("\nComposing final MP4 video...")
    video_path = compose_quiz_battle_video(frame_paths, audio_path)
    
    # Cleanup temp frames
    print("\nCleaning up temporary frame PNG files...")
    for frame in frame_paths:
        try:
            os.remove(frame)
        except:
            pass
            
    print(f"\nDone! Final video is available at: {video_path}")

if __name__ == "__main__":
    asyncio.run(main())
