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

    async def render_lesson(self, topic, audio_durations=None):
        """Render HTML and capture frames using Playwright, fallback to Manim animation if configured/supported."""
        # 1. Try to generate Math3D aesthetic Manim graphs/animations if topic contains graph indicators
        manim_rendered = await self._try_render_manim(topic, audio_durations)
        if manim_rendered:
            return manim_rendered

        # 2. Regular HTML render
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

    async def _try_render_manim(self, topic, audio_durations=None):
        """Helper to render dynamic dark-theme mathematical/geometrical visualizations using Manim library."""
        try:
            import manim
            from manim import (
                ThreeDScene, ThreeDAxes, Create, Write, WHITE, PINK, GREEN, RED, BLUE, GOLD, ORANGE,
                FadeIn, FadeOut, Text, UP, DOWN, LEFT, RIGHT, OUT, config, DEGREES, Sphere, Cone, Cylinder, Torus, Circle, Line, VGroup,
                RoundedRectangle, ReplacementTransform, Polygon
            )
            import numpy as np
            
            # Setup Manim config for portrait short videos (1080 x 1920)
            config.pixel_width = 1080
            config.pixel_height = 1920
            config.frame_width = 9.0
            config.frame_height = 16.0
            config.background_color = "#000000"  # Pure black background to merge seamlessly with mobile screens

            # Extract formula details from topic
            formula_title = topic.get('formula_title', 'Mathematical Model')
            formula_text = topic.get('formula_text', 'y = f(x)')
            
            # Step parameters
            step1_symbol = topic.get('step1_symbol', 'x')
            step1_desc = topic.get('step1_desc', 'First Parameter')
            step2_symbol = topic.get('step2_symbol', 'y')
            step2_desc = topic.get('step2_desc', 'Second Parameter')
            step3_symbol = topic.get('step3_symbol', formula_text)
            step3_desc = topic.get('step3_desc', 'Assembled Relation')
            
            math_type = topic.get('math_type', 'axes_3d').lower()

            # Dynamic time calculation based on actual audio durations
            if audio_durations is None:
                audio_durations = {}
            
            intro_dur = audio_durations.get('intro', 5.0)
            s1_dur = audio_durations.get('step1', 5.0)
            s2_dur = audio_durations.get('step2', 5.0)
            s3_dur = audio_durations.get('step3', 5.0)
            outro_dur = audio_durations.get('outro', 5.0)

            print(f"    🎥 [Manim Setup] Synchronizing scene timing with durations: Intro={intro_dur}s, S1={s1_dur}s, S2={s2_dur}s, S3={s3_dur}s, Outro={outro_dur}s")

            # Distribute intro time: write title and create axes
            intro_anim_title = min(1.2, intro_dur * 0.4)
            intro_anim_axes = min(1.5, intro_dur * 0.4)
            intro_wait = max(0.01, intro_dur - (intro_anim_title + intro_anim_axes + 0.1))

            # Step 1 timing
            s1_anim = min(1.5, s1_dur * 0.4)
            s1_wait = max(0.01, s1_dur - s1_anim)
            
            # Step 2 timing
            s2_anim = min(1.5, s2_dur * 0.4)
            s2_wait = max(0.01, s2_dur - s2_anim)
            
            # Step 3 timing
            s3_anim = min(2.0, s3_dur * 0.4)
            s3_wait = max(0.01, s3_dur - s3_anim)

            # Build temporary scene class using ThreeDScene for gorgeous 3D perspective
            class DynamicMath3DScene(ThreeDScene):
                def construct(self):
                    UR, UL, DL, DR = UP + RIGHT, UP + LEFT, DOWN + LEFT, DOWN + RIGHT
                    # Helper for wrapping presentation subtitles nicely in the card
                    def wrap_text(text, max_chars=40):
                        words = text.split()
                        lines = []
                        current_line = []
                        current_length = 0
                        for word in words:
                            if current_length + len(word) + 1 > max_chars:
                                lines.append(" ".join(current_line))
                                current_line = [word]
                                current_length = len(word)
                            else:
                                current_line.append(word)
                                current_length += len(word) + 1
                        if current_line:
                            lines.append(" ".join(current_line))
                        return "\n".join(lines)

                    # 1. Overlay Bottom Glassmorphic HUD card
                    hud_card = RoundedRectangle(
                        corner_radius=0.25,
                        width=8.2,
                        height=4.4,
                        color="#45A29E",       # Sleek glowing border
                        fill_color="#0B0C10",   # Translucent dark body
                        fill_opacity=0.9,
                        stroke_width=2.5
                    ).shift(DOWN * 5.5)
                    self.add_fixed_in_frame_mobjects(hud_card)

                    # Header Pill showing title & formula equation
                    header_str = f"{formula_title} • {formula_text}"
                    header_display = Text(header_str, font_size=28, color="#66FCF1", font="Segoe UI").move_to([0, -3.6, 0])
                    self.add_fixed_in_frame_mobjects(header_display)
                    
                    self.play(FadeIn(hud_card), Write(header_display), run_time=intro_anim_title)
                    self.wait(0.1)

                    is_trig_identity = "trig" in formula_title.lower() or "sin" in formula_text.lower() or "cos" in formula_text.lower() or math_type == "parametric_surface"

                    # 2. Setup 3D camera orientation (phi=75 deg, theta=-45 deg)
                    if not is_trig_identity:
                        self.set_camera_orientation(phi=75 * DEGREES, theta=-45 * DEGREES)
                        self.camera.frame_center.move_to(np.array([0, 0, 0]))

                    # 3. Create Axes
                    if is_trig_identity:
                        axes = ThreeDAxes(
                            x_range=[-2.5, 2.5, 1],
                            y_range=[-2.5, 2.5, 1],
                            z_range=[-1, 1, 1],
                            x_length=6.8,
                            y_length=6.8,
                            z_length=0.1,
                            axis_config={"color": "#45A29E", "stroke_width": 2}
                        )
                        
                        circle_radius = np.linalg.norm(axes.c2p(2.0, 0, 0) - axes.c2p(0, 0, 0))
                        circle = Circle(radius=circle_radius, color="#45A29E", stroke_width=3).move_to(axes.c2p(0, 0, 0))
                        radius_label = Text("r = 1", font_size=24, color="#45A29E", font="Segoe UI").next_to(circle, UR, buff=-0.5)
                        
                        self.play(Create(axes), Create(circle), Write(radius_label), run_time=intro_anim_axes)
                    else:
                        axes = ThreeDAxes(
                            x_range=[-3, 3, 1],
                            y_range=[-3, 3, 1],
                            z_range=[-3, 3, 1],
                            x_length=5.2,
                            y_length=5.2,
                            z_length=5.2,
                            axis_config={"color": "#45A29E", "stroke_width": 2}
                        )
                        self.play(Create(axes), run_time=intro_anim_axes)

                    # Display Intro Live Script Subtitles
                    intro_sub = wrap_text(topic.get('intro_script', ''))
                    intro_sub_text = Text(intro_sub, font_size=25, color=WHITE, line_spacing=1.3, font="Segoe UI").move_to([0, -5.4, 0])
                    self.add_fixed_in_frame_mobjects(intro_sub_text)
                    self.play(Write(intro_sub_text), run_time=1.0)
                    self.wait(max(0.01, intro_wait - 1.0))
                    self.play(FadeOut(intro_sub_text), run_time=0.2)

                    # Determine 3D visualization shapes and math components
                    is_cylinder = "cylinder" in math_type
                    is_sphere = ("sphere" in math_type or "inside" in formula_text.lower() or "outside" in formula_text.lower() or "boundary" in formula_text.lower()) and not is_trig_identity
                    is_cone = "cone" in math_type
                    is_torus = "torus" in math_type
                    is_spiral = "spiral" in math_type or "helix" in math_type or "successor" in formula_title.lower()
                    is_pythagoras = ("pythagoras" in formula_title.lower() or "pythagoras" in formula_text.lower() or math_type == "axes_3d") and not is_trig_identity

                    # Step 1: Draw coordinate component 1 and display Step 1 live subtitles
                    s1_sub = wrap_text(topic.get('step1_script', ''))
                    s1_sub_text = Text(s1_sub, font_size=25, color=WHITE, line_spacing=1.3, font="Segoe UI").move_to([0, -5.4, 0])
                    self.add_fixed_in_frame_mobjects(s1_sub_text)

                    if is_trig_identity:
                        theta_val = 40 * DEGREES
                        origin = axes.c2p(0, 0, 0)
                        cos_line = Line(
                            start=origin,
                            end=axes.c2p(np.cos(theta_val)*2, 0, 0),
                            color="#FF007F",
                            stroke_width=6
                        )
                        cos_label = Text("cos θ", color="#FF007F", font_size=22, font="Segoe UI").next_to(cos_line.get_center(), DOWN, buff=0.1)
                        vector1 = cos_line
                        self.play(Create(cos_line), Write(cos_label), Write(s1_sub_text), run_time=s1_anim)
                    elif is_pythagoras:
                        vertices_triangle = [axes.c2p(0, 0, 0), axes.c2p(2, 0, 0), axes.c2p(0, 1.5, 0)]
                        triangle = Polygon(*vertices_triangle, color=WHITE, stroke_width=3.0).set_style(fill_opacity=0.1, fill_color=WHITE)
                        
                        vertices_a = [axes.c2p(0, 0, 0), axes.c2p(2, 0, 0), axes.c2p(2, -2, 0), axes.c2p(0, -2, 0)]
                        square_a = Polygon(*vertices_a, color="#FF007F", stroke_width=4.0).set_style(fill_opacity=0.25, fill_color="#FF007F")
                        
                        vector1 = square_a
                        self.play(Create(triangle), Create(vector1), Write(s1_sub_text), run_time=s1_anim)
                    elif is_cylinder:
                        # Height axis representing first parameter (7 ticks for height 7)
                        vector1_line = Line(start=axes.c2p(0, 0, -1.05), end=axes.c2p(0, 0, 1.05), color="#FF007F", stroke_width=6.0)
                        ticks1 = VGroup()
                        z_vals = np.linspace(-1.05, 1.05, 7)
                        for z in z_vals:
                            tick = Line(
                                start=axes.c2p(-0.15, 0, z),
                                end=axes.c2p(0.15, 0, z),
                                color="#FF007F",
                                stroke_width=3.5
                            )
                            ticks1.add(tick)
                        vector1 = VGroup(vector1_line, ticks1)
                        self.play(Create(vector1), Write(s1_sub_text), run_time=s1_anim)
                    elif is_sphere:
                        # Flat circle representing spatial bounds/radius or cosine base
                        vector1 = Circle(radius=1.8, color="#FF007F", stroke_width=6.0).move_to(axes.c2p(0, 0, 0))
                        self.play(Create(vector1), Write(s1_sub_text), run_time=s1_anim)
                    elif is_cone:
                        # Height axis h
                        vector1 = Line(start=axes.c2p(0, 0, -1.25), end=axes.c2p(0, 0, 1.25), color="#FF007F", stroke_width=6.0)
                        self.play(Create(vector1), Write(s1_sub_text), run_time=s1_anim)
                    elif is_torus:
                        # Major radius circle
                        vector1 = Circle(radius=1.6, color="#FF007F", stroke_width=6.0).move_to(axes.c2p(0, 0, 0))
                        self.play(Create(vector1), Write(s1_sub_text), run_time=s1_anim)
                    else:
                        vector1 = Line(start=axes.get_center(), end=axes.get_center() + UP * 2.2, color="#FF007F", stroke_width=6.0)
                        self.play(Create(vector1), Write(s1_sub_text), run_time=s1_anim)
                    self.wait(s1_wait)
                    self.play(FadeOut(s1_sub_text), run_time=0.2)

                    # Step 2: Draw coordinate component 2 and display Step 2 live subtitles
                    s2_sub = wrap_text(topic.get('step2_script', ''))
                    s2_sub_text = Text(s2_sub, font_size=25, color=WHITE, line_spacing=1.3, font="Segoe UI").move_to([0, -5.4, 0])
                    self.add_fixed_in_frame_mobjects(s2_sub_text)

                    if is_trig_identity:
                        sin_line = Line(
                            start=axes.c2p(np.cos(theta_val)*2, 0, 0),
                            end=axes.c2p(np.cos(theta_val)*2, np.sin(theta_val)*2, 0),
                            color="#FFD700",
                            stroke_width=6
                        )
                        sin_label = Text("sin θ", color="#FFD700", font_size=22, font="Segoe UI").next_to(sin_line.get_center(), RIGHT, buff=0.1)
                        vector2 = VGroup(sin_line, sin_label)
                    elif is_pythagoras:
                        vertices_b = [axes.c2p(0, 0, 0), axes.c2p(0, 1.5, 0), axes.c2p(-1.5, 1.5, 0), axes.c2p(-1.5, 0, 0)]
                        square_b = Polygon(*vertices_b, color="#FFD700", stroke_width=4.0).set_style(fill_opacity=0.25, fill_color="#FFD700")
                        
                        vector2 = square_b
                    elif is_cylinder:
                        # Horizontal base circle and radius line with 5 ticks (representing base radius 5)
                        vector2_circle = Circle(radius=1.5, color="#FFD700", stroke_width=4.0).move_to(axes.c2p(0, 0, -1.05))
                        vector2_radius = Line(start=axes.c2p(0, 0, -1.05), end=axes.c2p(1.5, 0, -1.05), color="#FFD700", stroke_width=6.0)
                        ticks2 = VGroup()
                        x_vals = np.linspace(0, 1.5, 5)
                        for x in x_vals:
                            tick = Line(
                                start=axes.c2p(x, -0.15, -1.05),
                                end=axes.c2p(x, 0.15, -1.05),
                                color="#FFD700",
                                stroke_width=3.5
                            )
                            ticks2.add(tick)
                        vector2 = VGroup(vector2_circle, vector2_radius, ticks2)
                    elif is_sphere:
                        # Vector pointer representing point distance d or sine perpendicular
                        vector2 = Line(start=axes.c2p(0, 0, 0), end=axes.c2p(1.2, 1.2, 0), color="#FFD700", stroke_width=6.0)
                    elif is_cone:
                        # Flat base circle
                        vector2 = Circle(radius=1.5, color="#FFD700", stroke_width=6.0).move_to(axes.c2p(0, 0, -1.25))
                    elif is_torus:
                        # Minor radius circle at the edge
                        vector2 = Circle(radius=0.5, color="#FFD700", stroke_width=5.0).move_to(axes.c2p(1.6, 0, 0)).rotate(90 * DEGREES, axis=UP)
                    else:
                        vector2 = Line(start=axes.get_center(), end=axes.get_center() + RIGHT * 1.5, color="#FFD700", stroke_width=6.0)

                    self.play(
                        Create(vector2),
                        Write(s2_sub_text),
                        run_time=s2_anim
                    )
                    self.wait(s2_wait)
                    self.play(FadeOut(s2_sub_text), run_time=0.2)

                    # Step 3: Expand / Morph / Assemble into final shape & display complete formula & Step 3 live subtitles
                    s3_sub = wrap_text(topic.get('step3_script', ''))
                    s3_sub_text = Text(s3_sub, font_size=25, color=WHITE, line_spacing=1.3, font="Segoe UI").move_to([0, -5.4, 0])
                    self.add_fixed_in_frame_mobjects(s3_sub_text)

                    if is_trig_identity:
                        hypotenuse = Line(
                            start=origin, 
                            end=axes.c2p(np.cos(theta_val)*2, np.sin(theta_val)*2, 0),
                            color=WHITE,
                            stroke_width=5
                        )
                        hyp_label = Text("1", color=WHITE, font_size=24, font="Segoe UI").next_to(hypotenuse.get_center(), UL, buff=0.1)
                        
                        from manim import Angle
                        angle = Angle(
                            Line(origin, origin + RIGHT * 2),
                            hypotenuse,
                            radius=0.5,
                            color="#66FCF1"
                        )
                        angle_label = Text("θ", color="#66FCF1", font_size=22, font="Segoe UI").next_to(angle.get_center(), UR, buff=0.05)

                        pythagoras_eq = Text(
                            "(Base)² + (Perp)² = (Hyp)²",
                            font_size=26,
                            color=WHITE,
                            font="Segoe UI"
                        ).move_to([0, -1.6, 0])
                        
                        final_eq = Text(
                            "(cos θ)² + (sin θ)² = 1²",
                            font_size=26,
                            color=WHITE,
                            font="Segoe UI"
                        ).move_to([0, -1.6, 0])
                        
                        beautiful_final = Text(
                            "sin²θ + cos²θ = 1",
                            font_size=32,
                            color="#66FCF1",
                            font="Segoe UI"
                        ).move_to([0, -1.6, 0])
                        
                        from manim import SurroundingRectangle
                        box = SurroundingRectangle(beautiful_final, color="#66FCF1", buff=0.15)

                        # Timing split for 4 stages inside s3_dur
                        s3_stage = s3_dur / 5.0
                        self.play(Create(hypotenuse), Write(hyp_label), Create(angle), Write(angle_label), Write(s3_sub_text), run_time=s3_stage)
                        self.wait(0.3)
                        self.play(Write(pythagoras_eq), run_time=s3_stage)
                        self.wait(0.3)
                        self.play(ReplacementTransform(pythagoras_eq, final_eq), run_time=s3_stage)
                        self.wait(0.3)
                        self.play(ReplacementTransform(final_eq, beautiful_final), Create(box), run_time=s3_stage)
                        
                        s3_rem = max(0.01, s3_dur - (s3_stage * 4 + 0.9))
                        self.wait(s3_rem)
                        self.play(FadeOut(s3_sub_text), run_time=0.2)
                    else:
                        if is_pythagoras:
                            vertices_c = [axes.c2p(2, 0, 0), axes.c2p(0, 1.5, 0), axes.c2p(1.5, 3.5, 0), axes.c2p(3.5, 2, 0)]
                            square_c = Polygon(*vertices_c, color="#66FCF1", stroke_width=4.0).set_style(fill_opacity=0.25, fill_color="#66FCF1")
                            
                            shape = square_c
                        elif is_cylinder:
                            shape = Cylinder(radius=1.5, height=2.1, color=BLUE)
                            shape.set_style(fill_opacity=0.25, stroke_color="#007FFF", stroke_width=2.5)
                        elif is_sphere:
                            shape = Sphere(radius=1.8, color=PINK, resolution=(20, 20))
                            shape.set_style(fill_opacity=0.25, stroke_color="#FF007F", stroke_width=2.5)
                        elif is_cone:
                            shape = Cone(base_radius=1.5, height=2.5, color=ORANGE, direction=UP)
                            shape.set_style(fill_opacity=0.25, stroke_color="#FF5E00", stroke_width=2.5)
                        elif is_torus:
                            shape = Torus(major_radius=1.6, minor_radius=0.5, color=GOLD)
                            shape.set_style(fill_opacity=0.25, stroke_color="#FFD700", stroke_width=2.5)
                        elif is_spiral:
                            from manim import ParametricFunction
                            shape = ParametricFunction(
                                lambda t: axes.c2p(
                                    1.5 * np.cos(t),
                                    1.5 * np.sin(t),
                                    t / 4.0 - 1.0
                                ),
                                t_range=[-3*np.pi, 3*np.pi],
                                color="#C5A3FF",
                                stroke_width=6
                            )
                        elif "surface" in math_type or "trig" in formula_title.lower() or "sin" in formula_text.lower():
                            # Make parametric circle curve in 3D for Trigonometry Unit Circle Identity
                            from manim import ParametricFunction
                            shape = ParametricFunction(
                                lambda t: axes.c2p(
                                    1.8 * np.cos(t),
                                    1.8 * np.sin(t),
                                    0.0
                                ),
                                t_range=[0, 2*np.pi],
                                color="#66FCF1",
                                stroke_width=6
                            )
                        else:
                            shape = Circle(radius=1.6, color="#66FCF1", stroke_width=3.5).rotate(45 * DEGREES, axis=RIGHT)

                        if not is_pythagoras:
                            shape.move_to(axes.get_center())

                        self.play(
                             ReplacementTransform(VGroup(vector1, vector2), shape),
                             Write(s3_sub_text),
                             run_time=s3_anim
                        )
                        self.wait(s3_wait)
                        self.play(FadeOut(s3_sub_text), run_time=0.2)

                    # 4. Outro: Rotating Z/X in-place over outro duration + Outro Live Subtitles
                    outro_sub = wrap_text(topic.get('outro_script', ''))
                    outro_sub_text = Text(outro_sub, font_size=25, color=WHITE, line_spacing=1.3, font="Segoe UI").move_to([0, -5.4, 0])
                    self.add_fixed_in_frame_mobjects(outro_sub_text)

                    # Smooth, centered rotation in 3D around axes center
                    if is_trig_identity:
                        from manim import ValueTracker, always_redraw, Angle
                        theta_tracker = ValueTracker(40 * DEGREES)
                        
                        dynamic_cos_line = always_redraw(lambda: Line(
                            start=origin,
                            end=axes.c2p(np.cos(theta_tracker.get_value())*2, 0, 0),
                            color="#FF007F",
                            stroke_width=6
                        ))
                        dynamic_cos_label = always_redraw(lambda: Text(
                            "cos θ", color="#FF007F", font_size=22, font="Segoe UI"
                        ).next_to(dynamic_cos_line.get_center(), DOWN if np.sin(theta_tracker.get_value()) >= 0 else UP, buff=0.1))
                        
                        dynamic_sin_line = always_redraw(lambda: Line(
                            start=axes.c2p(np.cos(theta_tracker.get_value())*2, 0, 0),
                            end=axes.c2p(np.cos(theta_tracker.get_value())*2, np.sin(theta_tracker.get_value())*2, 0),
                            color="#FFD700",
                            stroke_width=6
                        ))
                        dynamic_sin_label = always_redraw(lambda: Text(
                            "sin θ", color="#FFD700", font_size=22, font="Segoe UI"
                        ).next_to(dynamic_sin_line.get_center(), RIGHT if np.cos(theta_tracker.get_value()) >= 0 else LEFT, buff=0.1))
                        
                        dynamic_hypotenuse = always_redraw(lambda: Line(
                            start=origin, 
                            end=axes.c2p(np.cos(theta_tracker.get_value())*2, np.sin(theta_tracker.get_value())*2, 0),
                            color=WHITE,
                            stroke_width=5
                        ))
                        dynamic_hyp_label = always_redraw(lambda: Text(
                            "1", color=WHITE, font_size=24, font="Segoe UI"
                        ).next_to(dynamic_hypotenuse.get_center(), UL if np.sin(theta_tracker.get_value()) >= 0 else DR, buff=0.1))

                        dynamic_angle = always_redraw(lambda: Angle(
                            Line(origin, origin + RIGHT * 2),
                            dynamic_hypotenuse,
                            radius=0.5,
                            color="#66FCF1"
                        ))
                        dynamic_angle_label = always_redraw(lambda: Text(
                            "θ", color="#66FCF1", font_size=22, font="Segoe UI"
                        ).next_to(dynamic_angle.get_center(), UR if np.sin(theta_tracker.get_value()) >= 0 else DL, buff=0.05))

                        self.add(dynamic_cos_line, dynamic_cos_label, dynamic_sin_line, dynamic_sin_label, dynamic_hypotenuse, dynamic_hyp_label, dynamic_angle, dynamic_angle_label)
                        self.remove(cos_line, cos_label, sin_line, sin_label, hypotenuse, hyp_label, angle, angle_label)

                        self.play(
                            Write(outro_sub_text),
                            theta_tracker.animate.set_value(40 * DEGREES + 2 * np.pi),
                            run_time=outro_dur,
                            rate_func=lambda t: t
                        )
                        # Graceful fade out
                        self.play(
                            FadeOut(dynamic_cos_line),
                            FadeOut(dynamic_cos_label),
                            FadeOut(dynamic_sin_line),
                            FadeOut(dynamic_sin_label),
                            FadeOut(dynamic_hypotenuse),
                            FadeOut(dynamic_hyp_label),
                            FadeOut(dynamic_angle),
                            FadeOut(dynamic_angle_label),
                            FadeOut(beautiful_final),
                            FadeOut(box),
                            FadeOut(outro_sub_text),
                            run_time=0.8
                        )
                    elif is_pythagoras:
                        rotation_group = VGroup(triangle, shape)
                        self.play(
                            Write(outro_sub_text),
                            rotation_group.animate.rotate(120 * DEGREES, axis=[0.3, 0.6, 1.0]),
                            run_time=outro_dur * 0.5
                        )
                        self.play(
                            rotation_group.animate.rotate(120 * DEGREES, axis=[0.3, 0.6, 1.0]),
                            run_time=outro_dur * 0.5
                        )
                    else:
                        self.play(
                            Write(outro_sub_text),
                            shape.animate.rotate(120 * DEGREES, axis=[0.3, 0.6, 1.0]),
                            run_time=outro_dur * 0.5
                        )
                        self.play(
                            shape.animate.rotate(120 * DEGREES, axis=[0.3, 0.6, 1.0]),
                            run_time=outro_dur * 0.5
                        )

            print("    🎥 [Manim] Rendering premium 3D mathematical formula animation...")
            
            # Setup temporary output paths
            temp_media_dir = Path("temp_media")
            
            # Proactively clear temp_media directory to prevent stale/duplicate outputs
            if temp_media_dir.exists():
                for old_mp4 in temp_media_dir.glob("**/*.mp4"):
                    try:
                        old_mp4.unlink()
                    except:
                        pass
                        
            config.media_dir = str(temp_media_dir)
            config.video_dir = str(temp_media_dir)
            
            # Run Manim Scene construction
            scene = DynamicMath3DScene()
            scene.render()

            # Find generated video frames or video output
            video_output = [f for f in temp_media_dir.glob("**/*.mp4") if f.name != "manim_rendered.mp4"]
            if video_output:
                out_mp4 = video_output[0]
                import shutil
                stable_mp4_path = temp_media_dir / "manim_rendered.mp4"
                shutil.copy2(str(out_mp4), str(stable_mp4_path))
                print(f"    ✅ [Manim] Direct smooth video generated at: {stable_mp4_path}")
                return [str(stable_mp4_path)]

        except Exception as e:
            print(f"    ⚠️ [Manim] 3D render error, falling back to Playwright: {e}")
        
        return []

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