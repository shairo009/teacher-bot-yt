import os
import sys
import json
import time
import shutil
import subprocess
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
OUTPUTS_DIR = BASE_DIR / "outputs"
TEMPLATES_DIR = BASE_DIR / "templates"
DOWNLOADS_DIR = Path("C:/Users/1001s/Downloads")

TOPICS_FILE = DATA_DIR / "code_reel_topics.json"
PROGRESS_FILE = DATA_DIR / "code_reel_progress.json"

def load_progress():
    if PROGRESS_FILE.exists():
        try:
            with open(PROGRESS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {"completed_ids": [], "current_idx": 0}

def save_progress(progress):
    PROGRESS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(PROGRESS_FILE, "w", encoding="utf-8") as f:
        json.dump(progress, f, indent=2)

def get_next_topic():
    if not TOPICS_FILE.exists():
        raise FileNotFoundError("Topics file not found!")
    with open(TOPICS_FILE, "r", encoding="utf-8") as f:
        catalog = json.load(f)

    topics = catalog.get("topics", [])
    progress = load_progress()
    completed = set(progress.get("completed_ids", []))

    for topic in topics:
        if topic["id"] not in completed:
            return topic
    return None

def generate_reel_video(topic=None, duration_seconds=60):
    if not topic:
        topic = get_next_topic()

    if not topic:
        print("🎉 All 500 Unique Code Reel Topics Completed!")
        return None

    print(f"🎬 Generating 1-Minute Full HD (1080x1920) Code Reel #{topic['id']}: {topic['title']}...")

    # Format Code Lines as JSON
    code_lines_json = json.dumps(topic["code_lines"])
    glow_color = topic["color_theme"][0] if len(topic["color_theme"]) > 0 else "#38BDF8"

    # Load Template
    tmpl_path = TEMPLATES_DIR / "code_reel_template.html"
    with open(tmpl_path, "r", encoding="utf-8") as f:
        html = f.read()

    # Replace Template Tokens
    html = html.replace("{{TITLE}}", topic["title"])
    html = html.replace("{{BADGE}}", topic["badge"])
    html = html.replace("{{FILE_NAME}}", topic["file_name"])
    html = html.replace("{{VISUAL_TYPE}}", topic["visual_type"])
    html = html.replace("{{GLOW_COLOR}}", glow_color)
    html = html.replace("{{CODE_LINES_JSON}}", code_lines_json)

    render_html = BASE_DIR / "render_temp.html"
    with open(render_html, "w", encoding="utf-8") as f:
        f.write(html)

    # Node rendering script for 1-minute 60s video (1800 frames at 30fps)
    node_render_js = BASE_DIR / "render_runner.js"
    js_code = f"""
const fs = require('fs');
const path = require('path');
const {{ execSync }} = require('child_process');
const puppeteer = require('puppeteer');

function getChromePath() {{
  const paths = [
    'C:\\\\Program Files\\\\Google\\\\Chrome\\\\Application\\\\chrome.exe',
    'C:\\\\Program Files (x86)\\\\Google\\\\Chrome\\\\Application\\\\chrome.exe'
  ];
  for (const p of paths) {{ if (fs.existsSync(p)) return p; }}
  return null;
}}

async function render() {{
  const framesDir = path.join(__dirname, 'frames');
  if (!fs.existsSync(framesDir)) fs.mkdirSync(framesDir);
  else {{
    for (const f of fs.readdirSync(framesDir)) fs.unlinkSync(path.join(framesDir, f));
  }}

  const chromePath = getChromePath();
  const launchOpts = {{ headless: 'new', args: ['--no-sandbox'] }};
  if (chromePath) launchOpts.executablePath = chromePath;

  const browser = await puppeteer.launch(launchOpts);
  const page = await browser.newPage();
  await page.setViewport({{ width: 540, height: 960, deviceScaleFactor: 2 }});

  const htmlPath = 'file:///' + path.join(__dirname, 'render_temp.html').replace(/\\\\/g, '/');
  await page.goto(htmlPath, {{ waitUntil: 'networkidle0' }});

  const totalFrames = {duration_seconds * 30};
  console.log(`📸 Capturing ${{totalFrames}} frames for 1-Minute Full HD Video...`);

  for (let i = 1; i <= totalFrames; i++) {{
    const num = String(i).padStart(5, '0');
    await page.screenshot({{ path: path.join(framesDir, `frame_${{num}}.png`), clip: {{ x: 0, y: 0, width: 540, height: 960 }} }});
    await new Promise(r => setTimeout(r, 16));
    if (i % 300 === 0) {{
      console.log(` Rendered ${{i / 30}}s / {duration_seconds}s...`);
    }}
  }}

  await browser.close();

  const outMp4 = path.join(__dirname, 'outputs', 'hd_code_reel_{topic['id']}.mp4');
  const ffmpegCmd = `ffmpeg -y -framerate 30 -i "${{path.join(framesDir, 'frame_%05d.png')}}" -c:v libx264 -preset medium -crf 18 -pix_fmt yuv420p "${{outMp4}}"`;
  console.log('🎥 Compiling 1-Minute HD Reel Video with FFmpeg...');
  execSync(ffmpegCmd, {{ stdio: 'inherit' }});

  const downloadMp4 = path.join('C:\\\\Users\\\\1001s\\\\Downloads', 'hd_code_reel_{topic['id']}.mp4');
  fs.copyFileSync(outMp4, downloadMp4);
  console.log(`✅ 1-MINUTE HD REEL GENERATED: ${{outMp4}}`);
}}

render().catch(err => {{ console.error(err); process.exit(1); }});
"""
    with open(node_render_js, "w", encoding="utf-8") as f:
        f.write(js_code)

    OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
    subprocess.run(["node", str(node_render_js)], check=True)

    # Update Progress Tracking
    progress = load_progress()
    progress["completed_ids"].append(topic["id"])
    progress["current_idx"] = len(progress["completed_ids"])
    save_progress(progress)

    final_video = OUTPUTS_DIR / f"hd_code_reel_{topic['id']}.mp4"
    download_video = DOWNLOADS_DIR / f"hd_code_reel_{topic['id']}.mp4"
    return final_video, download_video

if __name__ == "__main__":
    generate_reel_video()
