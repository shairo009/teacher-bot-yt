import os
import asyncio
import json
from pathlib import Path
from jinja2 import Template


class RenderEngine:
    def __init__(self, template_path="templates/lesson_dark.html", frames_dir="temp_frames"):
        self.template_path = Path(template_path)
        self.frames_dir = Path(frames_dir)
        self.frames_dir.mkdir(parents=True, exist_ok=True)

        # Read template
        with open(self.template_path, 'r', encoding='utf-8') as f:
            self.template_content = f.read()

    def prepare_lesson_data(self, topic):
        """Convert topic text into lines for rendering."""
        lines = []
        
        if 'lines' in topic and isinstance(topic['lines'], list):
            lines = topic['lines']
        else:
            topic_text = topic['topic']
            # Split topic text into lines (max 5 words per line for visual appeal)
            words = topic_text.split()
            current_line = []
            for word in words:
                current_line.append(word)
                if len(current_line) >= 5 or len(' '.join(current_line)) > 40:
                    lines.append(' '.join(current_line))
                    current_line = []
            if current_line:
                lines.append(' '.join(current_line))

        # Ensure minimum 5 lines, maximum 8 lines for dark theme
        while len(lines) < 3:
            lines.append("") 
        lines = lines[:8]

        level = topic.get('level', 'Basic')
        topic_name = topic.get('topic', 'Math Lesson').split(':')[0]

        return {
            'level_label': level,
            'topic_label': topic_name,
            'lines': lines,
            'image_url': Path(topic.get('image')).absolute().as_uri() if topic.get('image') else "None"
        }

    async def render_lesson(self, topic):
        """Render HTML and capture frames using Playwright."""
        try:
            from playwright.async_api import async_playwright
        except ImportError:
            print("Playwright not installed. Install with: pip install playwright && playwright install chromium")
            return []

        lesson_data = self.prepare_lesson_data(topic)
        lines_json = json.dumps(lesson_data['lines'])

        # Render HTML with Jinja2
        template = Template(self.template_content)
        html_content = template.render(
            LINES_JSON=lines_json,
            IMAGE_URL=lesson_data['image_url'],
            LEVEL_LABEL=lesson_data['level_label'],
            TOPIC_LABEL=lesson_data['topic_label']
        )

        # Save HTML
        html_path = "temp_lesson.html"
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(html_content)

        frame_paths = []
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch()
                page = await browser.new_page(viewport={"width": 1080, "height": 1920})

                # Load HTML file
                await page.goto(f"file://{os.path.abspath(html_path)}")
                await asyncio.sleep(2)  # Wait for page to fully load

                # Capture frames at intervals
                # First capture empty state
                await page.screenshot(path=str(self.frames_dir / "frame_000.png"))
                frame_paths.append(str(self.frames_dir / "frame_000.png"))

                # Capture frames as lines appear (based on animation timing)
                # Total lines * 2 seconds delay + buffer
                total_lines = len(lesson_data['lines'])
                capture_times = [0.5]  # Initial frame

                # Capture each line appearance (matches new typing delay)
                for i in range(total_lines):
                    capture_times.append(3.0 + i * 3.0)

                for idx, delay in enumerate(capture_times):
                    frame_num = str(idx + 1).zfill(3)
                    path = self.frames_dir / f"frame_{frame_num}.png"
                    await page.screenshot(path=str(path))
                    frame_paths.append(str(path))

                    if idx < len(capture_times) - 1:
                        # Wait for next line to appear
                        await asyncio.sleep(3.0)

                await browser.close()

        except Exception as e:
            print(f"Render error: {e}")
            # Fallback: just capture one frame
            try:
                from playwright.sync_api import sync_playwright
                with sync_playwright() as p:
                    browser = p.chromium.launch()
                    page = browser.new_page(viewport={"width": 1080, "height": 1920})
                    page.goto(f"file://{os.path.abspath(html_path)}")
                    page.wait_for_timeout(2000)
                    page.screenshot(path=str(self.frames_dir / "frame_000.png"))
                    browser.close()
                    frame_paths = [str(self.frames_dir / "frame_000.png")]
            except:
                pass

        # Clean up HTML
        if os.path.exists(html_path):
            os.remove(html_path)

        print(f"Rendered {len(frame_paths)} frames")
        return frame_paths

    def render_simple(self, topic, num_frames=18):
        """Fallback render without Playwright - generates simple frames."""
        lesson_data = self.prepare_lesson_data(topic)
        lines = lesson_data['lines']
        frame_paths = []

        try:
            from PIL import Image, ImageDraw, ImageFont
            import math

            for frame_idx in range(num_frames):
                img = Image.new('RGB', (1080, 1920), color='white')
                draw = ImageDraw.Draw(img)

                # Draw class badge
                class_label = lesson_data.get('class_label', f"Class {topic.get('class', '1')}")
                chapter_label = lesson_data.get('chapter_label', f"Chapter {topic.get('chapter', '1')}")
                
                draw.rounded_rectangle([(60, 40), (200, 90)], radius=15, fill='#1a1a1a')
                draw.text((90, 55), class_label, fill='white')

                # Draw chapter
                draw.text((800, 55), chapter_label, fill='#888')

                # Draw pencil icon
                draw.polygon([(950, 1700), (1000, 1750), (930, 1800)], fill='#FFD700')

                # Calculate visible lines (pencil draws them)
                visible_lines = min(frame_idx // 2, len(lines))
                y_pos = 300

                for line_idx in range(visible_lines):
                    line_text = lines[line_idx] if line_idx < len(lines) else ""
                    # Simple text rendering
                    draw.text((150, y_pos), line_text, fill='#1a1a1a')
                    y_pos += 100

                # Save frame
                frame_path = self.frames_dir / f"frame_{str(frame_idx).zfill(3)}.png"
                img.save(frame_path)
                frame_paths.append(str(frame_path))

            print(f"Generated {len(frame_paths)} simple frames")

        except ImportError:
            print("PIL not available for simple render")

        return frame_paths


if __name__ == "__main__":
    engine = RenderEngine()
    test_topic = {
        'class': 6,
        'chapter': 'Chapter 1: Knowing Our Numbers',
        'topic': 'What is a number? Numbers are used to count objects. We use digits 0 to 9 to form numbers. For example, 25 means two tens and five ones.'
    }
    frames = engine.render_simple(test_topic)
    print(f"Test render: {len(frames)} frames created")