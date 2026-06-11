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
COUNTDOWN_SECONDS = 5
REVEAL_SECONDS = 1.5
TOTAL_FRAMES = int((COUNTDOWN_SECONDS + REVEAL_SECONDS) * FPS)  # 195 frames

# Helper functions
def hex_to_rgb(hex_color):
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

def get_font(size, bold=False):
    font_paths = [
        str(PROJECT_ROOT / 'assets/fonts/Montserrat-Bold.ttf') if bold else str(PROJECT_ROOT / 'assets/fonts/Montserrat-Regular.ttf'),
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
    total_h = len(lines) * line_h + (len(lines) - 1) * 15
    start_y = cy - total_h // 2
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=font)
        tw = bbox[2] - bbox[0]
        tx = cx - tw // 2
        draw.text((tx, start_y), line, fill=color, font=font)
        start_y += line_h + 15

async def get_would_you_rather_question():
    """Fetch a high-quality, engaging 'Would You Rather' question from LLM."""
    from src.visual_generator import _call_api
    
    prompt = """You are a viral content creator for YouTube Shorts. Generate a highly engaging 'Would You Rather' decision question.
Make it extremely choice-inducing, controversial, or fun (e.g. superpowers, survival situations, life decisions).

Return ONLY valid JSON (no markdown, no explanations) in this exact format:
{
  "question": "Would you rather...",
  "option_a": "Always know when someone is lying to you",
  "option_b": "Always get away with any lie you tell",
  "percentage_a": 54,
  "percentage_b": 46,
  "narration": "Would you rather always know when someone is lying to you, OR, always get away with any lie you tell? Make your choice!"
}
"""
    model = os.environ.get('OPENAI_MODEL', 'mimo-v2.5-free')
    try:
        print(f"Calling LLM ({model}) for a viral question...")
        content = _call_api(
            messages=[
                {"role": "system", "content": "You are a creative viral scriptwriter. Return only valid JSON."},
                {"role": "user", "content": prompt}
            ],
            model=model, temperature=0.8
        )
        if content:
            # Clean up markdown code blocks if present
            if content.startswith('```'):
                content = content.split('\n', 1)[1] if '\n' in content else content[3:]
            if content.endswith('```'):
                content = content[:-3]
            content = content.strip()
            if content.startswith('json'):
                content = content[4:].strip()
                
            return json.loads(content)
    except Exception as e:
        print(f"Failed to get question from LLM: {e}")
    
    # Fallback question
    return {
        "question": "Would you rather...",
        "option_a": "Have the power to fly but only at walking speed",
        "option_b": "Have the power to run at 100 mph but only on all fours",
        "percentage_a": 58,
        "percentage_b": 42,
        "narration": "Would you rather have the power to fly, but only at walking speed? OR, have the power to run at 100 miles per hour, but only on all fours? Make your choice!"
    }

async def generate_narration_audio(text):
    """Generate high-quality TTS audio file."""
    import edge_tts
    temp_dir = PROJECT_ROOT / "temp_audio"
    temp_dir.mkdir(exist_ok=True)
    output_path = temp_dir / "wyr_narration.mp3"
    
    # Use GuyNeural (male) for bold, high-energy gaming questions
    communicate = edge_tts.Communicate(text, 'en-US-GuyNeural')
    await communicate.save(str(output_path))
    return output_path

def render_frames(data):
    """Render all frames for the Shorts video using Pillow."""
    temp_frames_dir = PROJECT_ROOT / "temp_frames"
    temp_frames_dir.mkdir(exist_ok=True)
    
    # Clear existing frames
    for f in temp_frames_dir.glob("frame_*.png"):
        try:
            os.remove(f)
        except:
            pass

    print(f"Rendering {TOTAL_FRAMES} frames...")
    
    # Colors
    color_red_start = "#450A0A" # Dark red
    color_red_end = "#991B1B"   # Vibrant red
    color_blue_start = "#1E3A8A" # Vibrant blue
    color_blue_end = "#0F172A"  # Dark blue
    
    font_question = get_font(52, bold=True)
    font_option = get_font(42, bold=True)
    font_percentage = get_font(120, bold=True)
    font_timer = get_font(60, bold=True)
    font_winner = get_font(28, bold=True)
    
    frame_paths = []
    
    # Determine winner
    winner_a = data["percentage_a"] >= data["percentage_b"]
    
    for frame_idx in range(TOTAL_FRAMES):
        # Base image
        img = Image.new('RGBA', (WIDTH, HEIGHT))
        draw = ImageDraw.Draw(img)
        
        # 1. Draw split screens with vertical gradients
        # Top half (Option A)
        draw_gradient_vertical(draw, 0, 0, WIDTH, HEIGHT // 2, color_red_start, color_red_end)
        # Bottom half (Option B)
        draw_gradient_vertical(draw, 0, HEIGHT // 2, WIDTH, HEIGHT, color_blue_start, color_blue_end)
        
        # 2. Draw glassy cards for options
        # Top card
        draw_glassy_card(draw, img, 80, 240, WIDTH - 80, HEIGHT // 2 - 120)
        # Bottom card
        draw_glassy_card(draw, img, 80, HEIGHT // 2 + 120, WIDTH - 80, HEIGHT - 240)
        
        # 3. Draw question text at the top
        draw_glassy_card(draw, img, 150, 40, WIDTH - 150, 150, fill_color=(0, 0, 0, 120), border_color=(255, 255, 255, 40), radius=20)
        draw.text((WIDTH // 2, 95), data["question"].upper(), fill=(255, 255, 255, 240), font=get_font(38, bold=True), anchor='mm')
        
        # 4. Handle countdown vs reveal phases
        is_reveal = frame_idx >= (COUNTDOWN_SECONDS * FPS)
        
        if not is_reveal:
            # COUNTDOWN PHASE
            # Draw Option A text
            draw_text_inside_card(draw, data["option_a"], WIDTH // 2, (240 + HEIGHT // 2 - 120) // 2, font_option, (255, 255, 255, 245))
            # Draw Option B text
            draw_text_inside_card(draw, data["option_b"], WIDTH // 2, (HEIGHT // 2 + 120 + HEIGHT - 240) // 2, font_option, (255, 255, 255, 245))
            
            # Central Timer Hub
            cy = HEIGHT // 2
            # Separator bar
            draw.line([(0, cy), (WIDTH, cy)], fill=(255, 255, 255, 40), width=4)
            # Timer outer glow circle
            draw.ellipse([(WIDTH // 2 - 95, cy - 95), (WIDTH // 2 + 95, cy + 95)], fill=(11, 15, 25, 255), outline=(255, 255, 255, 40), width=3)
            
            # Circular loading bar
            elapsed_seconds = frame_idx / FPS
            remaining_seconds = max(0, COUNTDOWN_SECONDS - elapsed_seconds)
            progress = remaining_seconds / COUNTDOWN_SECONDS
            
            # Draw arc
            angle = int(360 * progress)
            draw.arc([(WIDTH // 2 - 90, cy - 90), (WIDTH // 2 + 90, cy + 90)], start=-90, end=-90 + angle, fill=(251, 191, 36), width=8)
            
            # Text inside timer
            timer_text = str(int(math.ceil(remaining_seconds)))
            draw.text((WIDTH // 2, cy), timer_text, fill=(255, 255, 255, 255), font=font_timer, anchor='mm')
            
        else:
            # REVEAL PHASE (Percentages)
            # Top card content
            ty_a = (240 + HEIGHT // 2 - 120) // 2
            draw.text((WIDTH // 2, ty_a - 110), data["option_a"][:40] + ("..." if len(data["option_a"]) > 40 else ""), fill=(255, 255, 255, 180), font=get_font(26), anchor='mm')
            draw.text((WIDTH // 2, ty_a + 20), f"{data['percentage_a']}%", fill=(244, 63, 94, 255), font=font_percentage, anchor='mm') # Neon Red
            
            # Bottom card content
            ty_b = (HEIGHT // 2 + 120 + HEIGHT - 240) // 2
            draw.text((WIDTH // 2, ty_b - 110), data["option_b"][:40] + ("..." if len(data["option_b"]) > 40 else ""), fill=(255, 255, 255, 180), font=get_font(26), anchor='mm')
            draw.text((WIDTH // 2, ty_b + 20), f"{data['percentage_b']}%", fill=(14, 165, 233, 255), font=font_percentage, anchor='mm') # Neon Blue
            
            # Draw Winner Badge
            if winner_a:
                # Winner A Badge
                draw.rounded_rectangle([(WIDTH // 2 - 160, ty_a + 105), (WIDTH // 2 + 160, ty_a + 155)], radius=12, fill=(251, 191, 36, 230))
                draw.text((WIDTH // 2, ty_a + 130), "MOST CHOSEN ★", fill=(17, 24, 39), font=font_winner, anchor='mm')
            else:
                # Winner B Badge
                draw.rounded_rectangle([(WIDTH // 2 - 160, ty_b + 105), (WIDTH // 2 + 160, ty_b + 155)], radius=12, fill=(251, 191, 36, 230))
                draw.text((WIDTH // 2, ty_b + 130), "MOST CHOSEN ★", fill=(17, 24, 39), font=font_winner, anchor='mm')
            
            # Central VS Hub
            cy = HEIGHT // 2
            draw.line([(0, cy), (WIDTH, cy)], fill=(255, 255, 255, 60), width=4)
            draw.ellipse([(WIDTH // 2 - 95, cy - 95), (WIDTH // 2 + 95, cy + 95)], fill=(11, 15, 25, 255), outline=(251, 191, 36, 255), width=4)
            draw.text((WIDTH // 2, cy), "VS", fill=(251, 191, 36), font=font_timer, anchor='mm')

        # Save frame
        frame_path = temp_frames_dir / f"frame_{str(frame_idx).zfill(3)}.png"
        img.save(frame_path)
        frame_paths.append(str(frame_path))
        
    return frame_paths

def compose_would_you_rather_video(frame_paths, audio_path):
    """Compile frames and audio into final video using FFmpeg."""
    outputs_dir = PROJECT_ROOT / "outputs"
    outputs_dir.mkdir(exist_ok=True)
    output_video_path = outputs_dir / "would_you_rather.mp4"
    
    # Concat file for ffmpeg
    concat_file = outputs_dir / "wyr_concat.txt"
    
    # We want countdown frames to take exactly COUNTDOWN_SECONDS, and reveal frames to take REVEAL_SECONDS.
    # Total duration = 6.5s
    # Each frame dur = total_dur / total_frames
    frame_dur = 1.0 / FPS
    
    with open(concat_file, 'w') as f:
        for frame in frame_paths:
            f.write(f"file '{os.path.abspath(frame)}'\n")
            f.write(f"duration {frame_dur:.6f}\n")
        # Repeat last frame
        f.write(f"file '{os.path.abspath(frame_paths[-1])}'\n")

    print("Composing video with FFmpeg...")
    # Clean output if it exists
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
        '-shortest', # truncate to shortest stream (matching the audio duration)
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
    # 1. Fetch Question
    wyr_data = await get_would_you_rather_question()
    print("\nWYR Question Data:")
    print(json.dumps(wyr_data, indent=2))
    
    # 2. Generate Audio Narration
    print("\nGenerating Audio Narration...")
    audio_path = await generate_narration_audio(wyr_data["narration"])
    print(f"Audio generated at: {audio_path}")
    
    # 3. Render Video Frames
    print("\nRendering frames...")
    frame_paths = render_frames(wyr_data)
    
    # 4. Compose Video
    print("\nComposing final MP4 video...")
    video_path = compose_would_you_rather_video(frame_paths, audio_path)
    
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
