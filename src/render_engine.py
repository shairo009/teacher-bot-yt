import os
import asyncio
import json
from pathlib import Path


class RenderEngine:
    def __init__(self, template_path="templates/lesson_template.html",
                 frames_dir="temp_frames", use_math_effects=True):
        self.template_path = Path(template_path)
        self.frames_dir = Path(frames_dir)
        self.frames_dir.mkdir(parents=True, exist_ok=True)
        self.use_math_effects = use_math_effects

        # Read template
        try:
            with open(self.template_path, 'r', encoding='utf-8') as f:
                self.template_content = f.read()
        except:
            self.template_content = None

    def prepare_lesson_data(self, topic):
        """Convert topic text into lines for rendering."""
        topic_text = topic['topic']
        lines = []

        # Split topic text into lines (max 5 words per line)
        words = topic_text.split()
        current_line = []
        for word in words:
            current_line.append(word)
            if len(current_line) >= 5 or len(' '.join(current_line)) > 40:
                lines.append(' '.join(current_line))
                current_line = []
        if current_line:
            lines.append(' '.join(current_line))

        # Ensure minimum 5 lines, maximum 12 lines
        while len(lines) < 5:
            lines.append("")
        lines = lines[:12]

        class_num = topic.get('class', 6)
        chapter = topic.get('chapter', 'Chapter 1')

        return {
            'class_label': f"Class {class_num}",
            'chapter_label': chapter,
            'lines': lines
        }

    def render_simple(self, topic, num_frames=18):
        """Generate simple frames using PIL (no Playwright needed)."""
        from PIL import Image, ImageDraw

        lesson_data = self.prepare_lesson_data(topic)
        lines = lesson_data['lines']
        frame_paths = []

        try:
            for frame_idx in range(num_frames):
                img = Image.new('RGB', (1080, 1920), color='white')
                draw = ImageDraw.Draw(img)

                # Draw class badge (top left)
                draw.rounded_rectangle([(60, 40), (220, 95)], radius=15, fill='#2d2d2d')
                draw.text((85, 55), lesson_data['class_label'], fill='white')

                # Draw chapter (top right)
                draw.text((780, 55), lesson_data['chapter_label'], fill='#666')

                # Calculate visible lines (pencil effect)
                visible_count = min(frame_idx // 2 + 1, len(lines))
                y_pos = 300

                for line_idx in range(visible_count):
                    if line_idx < len(lines):
                        line_text = lines[line_idx]
                        # Draw text
                        draw.text((150, y_pos), line_text, fill='#1a1a1a')
                        y_pos += 100

                # Draw pencil icon (bottom right)
                pencil_x, pencil_y = 900, 1600
                draw.polygon([
                    (pencil_x, pencil_y),
                    (pencil_x + 60, pencil_y + 40),
                    (pencil_x - 30, pencil_y + 80)
                ], fill='#FFD700')

                # Save frame
                frame_path = self.frames_dir / f"frame_{str(frame_idx).zfill(3)}.png"
                img.save(frame_path)
                frame_paths.append(str(frame_path))

            print(f"Generated {len(frame_paths)} frames")

        except ImportError:
            print("PIL not available - using text-based fallback")
            return self.render_text_only(topic)

        return frame_paths

    def render_text_only(self, topic, num_frames=18):
        """Fallback: generate text frames without PIL."""
        lesson_data = self.prepare_lesson_data(topic)
        lines = lesson_data['lines']
        frame_paths = []

        for frame_idx in range(num_frames):
            # Create a simple text file with frame info
            visible_count = min(frame_idx // 2 + 1, len(lines))
            content = f"{lesson_data['class_label']} | {lesson_data['chapter_label']}\n\n"
            for i in range(visible_count):
                if i < len(lines):
                    content += f"{i+1}. {lines[i]}\n"

            frame_path = self.frames_dir / f"frame_{str(frame_idx).zfill(3)}.txt"
            with open(frame_path, 'w') as f:
                f.write(content)
            frame_paths.append(str(frame_path))

        print(f"Generated {len(frame_paths)} text frames (fallback mode)")
        return frame_paths

    def render_with_math_effects(self, topic, num_frames=30):
        """Generate visually rich math frames with 2D effects."""
        try:
            from src.math_effects import auto_detect_and_generate
            frames = auto_detect_and_generate(topic, str(self.frames_dir))
            if frames:
                print(f"Generated {len(frames)} math visual frames")
                return frames
        except ImportError:
            print("math_effects not available, falling back to simple render")
        except Exception as e:
            print(f"Math effects error: {e}, falling back to simple render")

        return self.render_simple(topic, num_frames=18)

    def render_with_llm(self, topic):
        """Generate visuals using LLM + PIL (best quality).
        Returns (frames, narrations) tuple or (None, None).
        """
        try:
            from src.visual_generator import generate_visual
            frames, narrations = generate_visual(topic, str(self.frames_dir))
            if frames:
                print(f"Generated {len(frames)} LLM visual frames")
                return frames, narrations
        except ImportError:
            print("visual_generator not available, falling back to math_effects")
        except Exception as e:
            print(f"LLM visual error: {e}, falling back to math_effects")
        return None, None

    async def render_lesson(self, topic):
        """Async wrapper - tries LLM first, then math effects, then simple.
        Returns (frames, narrations) tuple.
        narrations is a list of Hindi strings synced with frames (empty list for non-LLM fallbacks).
        """
        # Priority 1: LLM-powered visuals (topic-specific, with narration)
        frames, narrations = self.render_with_llm(topic)
        if frames:
            return frames, narrations

        # Priority 2: Math effects (keyword-based, no narration)
        if self.use_math_effects:
            frames = self.render_with_math_effects(topic)
            if frames:
                return frames, []

        # Priority 3: Simple text frames (no narration)
        return self.render_simple(topic), []


if __name__ == "__main__":
    engine = RenderEngine()
    test_topic = {
        'class': 6,
        'chapter': 'Chapter 1: Knowing Our Numbers',
        'topic': 'What is a number? Numbers are used to count objects. We use digits 0 to 9 to form numbers. For example, 25 means two tens and five ones.'
    }
    frames = engine.render_simple(test_topic)
    print(f"Test render: {len(frames)} frames created")