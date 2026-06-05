import os
import subprocess
import json
import random
from pathlib import Path

# Project root for assets
_PROJECT_ROOT = str(Path(__file__).resolve().parent.parent)
TARGET_FPS = 30


class VideoEngine:
    def __init__(self, frames_dir="temp_frames", audio_dir="temp_audio", output_dir="outputs"):
        self.frames_dir = Path(frames_dir)
        self.audio_dir = Path(audio_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.assets_dir = Path(_PROJECT_ROOT) / 'assets'

    def _run(self, cmd, timeout=120):
        """Run ffmpeg command, return result."""
        print(f"  [ffmpeg] {' '.join(cmd[:6])}...", flush=True)
        return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)

    def _get_audio_duration(self, audio_path):
        """Get duration of an audio file in seconds using ffprobe."""
        try:
            result = subprocess.run(
                ['ffprobe', '-v', 'error', '-show_entries', 'format=duration',
                 '-of', 'default=noprint_wrappers=1:nokey=1', str(audio_path)],
                capture_output=True, text=True, timeout=10
            )
            if result.returncode == 0:
                return float(result.stdout.strip())
        except:
            pass
        return 3.0

    def compose_video(self, frame_paths, audio_paths, output_name="lesson.mp4",
                       frames_per_step=None):
        """Compose video with pro post-processing: crossfade, bg music, normalization.

        Strategy:
        - frames grouped by step, audio synced per step
        - post-processing: background music mix, audio normalization
        """
        existing_frames = [f for f in (frame_paths or []) if os.path.exists(f)]
        existing_audio = [f for f in (audio_paths or []) if os.path.exists(f)]

        if not existing_frames:
            print("No frames to compose")
            return None

        output_path = self.output_dir / output_name
        if output_path.suffix.lower() != ".mp4":
            output_path = output_path.with_suffix(".mp4")
        output_path = str(output_path)

        # Get duration for each audio clip
        num_audio = len(existing_audio)
        audio_durations = [self._get_audio_duration(a) for a in existing_audio] if num_audio else []
        frame_durations = []

        if num_audio == 0:
            # No narration available: play the rendered animation at real 30fps.
            # Stretching tiny frame groups made fallback videos look frozen.
            frame_durations = [1.0 / TARGET_FPS] * len(existing_frames)
        else:
            if frames_per_step is None:
                frames_per_step = max(1, round(len(existing_frames) / num_audio))

            # Build per-frame durations synced to audio
            for step_i in range(max(1, num_audio)):
                if step_i == 0:
                    clip_duration = audio_durations[0]
                elif step_i < num_audio - 1:
                    clip_duration = audio_durations[min(step_i, num_audio - 1)]
                else:
                    clip_duration = audio_durations[-1]

                per_frame = max(1.0 / TARGET_FPS, clip_duration / frames_per_step)
                for _ in range(frames_per_step):
                    frame_durations.append(per_frame)

        # Handle leftover frames
        leftover = len(existing_frames) - len(frame_durations)
        for _ in range(leftover):
            frame_durations.append(1.0 / TARGET_FPS)

        # Step 1: Create concat file with per-frame durations
        concat_file = str(self.output_dir / "concat.txt")
        with open(concat_file, 'w') as f:
            for i, frame in enumerate(existing_frames):
                dur = frame_durations[i] if i < len(frame_durations) else (1.0 / TARGET_FPS)
                f.write(f"file '{os.path.abspath(frame)}'\n")
                f.write(f"duration {dur:.6f}\n")
            f.write(f"file '{os.path.abspath(existing_frames[-1])}'\n")

        # Step 2: Concat audio files
        has_audio = False
        temp_audio = str(self.output_dir / "temp_audio.mp3")
        if existing_audio:
            audio_concat = str(self.output_dir / "audio_concat.txt")
            with open(audio_concat, 'w') as f:
                for a in existing_audio:
                    f.write(f"file '{os.path.abspath(a)}'\n")

            result = self._run([
                'ffmpeg', '-y', '-f', 'concat', '-safe', '0',
                '-i', audio_concat, '-c', 'copy', temp_audio
            ], timeout=60)
            has_audio = result.returncode == 0 and os.path.exists(temp_audio)
            if os.path.exists(audio_concat):
                os.remove(audio_concat)

        # Step 3: Create video from frames with smooth framerate
        temp_video = str(self.output_dir / "temp_video.mp4")
        result = self._run([
            'ffmpeg', '-y',
            '-f', 'concat', '-safe', '0',
            '-i', concat_file,
            '-vf', f'scale=1080:1920,fps={TARGET_FPS}',
            '-c:v', 'libx264', '-preset', 'fast',
            '-pix_fmt', 'yuv420p',
            temp_video
        ], timeout=180)

        if os.path.exists(concat_file):
            os.remove(concat_file)

        if result.returncode != 0:
            print(f"ffmpeg video failed: {result.stderr[-300:]}")
            return None

        # Step 4: Post-process — merge video + audio + bg music + normalize
        if has_audio:
            final_path = self._post_process(temp_video, temp_audio, output_path)
            if os.path.exists(temp_audio):
                os.remove(temp_audio)
            if os.path.exists(temp_video):
                os.remove(temp_video)
            if final_path:
                print(f"Video created: {final_path}")
                return final_path
        else:
            # No audio — just rename
            if os.path.exists(temp_video):
                os.rename(temp_video, output_path)
                print(f"Video created (no audio): {output_path}")
                return output_path

        return None

    def extract_thumbnail_frame(self, video_path, output_path=None):
        """Extract a frame at ~20% duration for thumbnail source."""
        if not os.path.exists(video_path):
            return None

        duration = self._get_audio_duration(video_path)
        seek_time = max(1.0, duration * 0.2)

        if output_path is None:
            output_path = str(self.output_dir / "thumb_source.png")

        result = subprocess.run([
            'ffmpeg', '-y',
            '-ss', str(seek_time),
            '-i', video_path,
            '-vframes', '1',
            '-vf', 'scale=1280:720',
            output_path
        ], capture_output=True, text=True, timeout=15)

        if result.returncode == 0 and os.path.exists(output_path):
            return output_path
        return None

    def _post_process(self, video_path, audio_path, output_path):
        """Post-process: mix background music, normalize audio, add intro fade."""
        bg_music = str(self.assets_dir / 'music' / 'ambient_30s.mp3')
        has_bg = os.path.exists(bg_music)

        if has_bg:
            # Mix narration + background music, normalize
            result = self._run([
                'ffmpeg', '-y',
                '-i', video_path,
                '-i', audio_path,
                '-i', bg_music,
                '-filter_complex',
                # Scale bg music volume to be subtle, loop it
                '[2:a]aloop=loop=-1:size=2e+09,volume=0.08[bg];'
                # Concat narration audio
                '[1:a]aformat=sample_rates=44100:channel_layouts=stereo[narr];'
                # Mix narration + bg music
                '[narr][bg]amix=inputs=2:duration=first:dropout_transition=2[mixed];'
                # Normalize loudness to -14 LUFS (YouTube standard)
                '[mixed]loudnorm=I=-14:TP=-1.5:LRA=11[norm]',
                '-map', '0:v', '-map', '[norm]',
                '-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k',
                '-shortest',
                output_path
            ], timeout=120)
        else:
            # No bg music — just normalize narration
            result = self._run([
                'ffmpeg', '-y',
                '-i', video_path,
                '-i', audio_path,
                '-filter_complex',
                '[1:a]loudnorm=I=-14:TP=-1.5:LRA=11[norm]',
                '-map', '0:v', '-map', '[norm]',
                '-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k',
                '-shortest',
                output_path
            ], timeout=60)

        if result.returncode == 0 and os.path.exists(output_path):
            return output_path

        # Fallback: simple merge without normalization
        print(f"  Post-process failed, trying simple merge...", flush=True)
        result = self._run([
            'ffmpeg', '-y',
            '-i', video_path,
            '-i', audio_path,
            '-c:v', 'copy', '-c:a', 'aac',
            '-shortest',
            output_path
        ], timeout=60)

        if result.returncode == 0 and os.path.exists(output_path):
            return output_path

        print(f"  All merge attempts failed: {result.stderr[-200:]}")
        return None
