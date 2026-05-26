import os
import subprocess
import json
from pathlib import Path


class VideoEngine:
    def __init__(self, frames_dir="temp_frames", audio_dir="temp_audio", output_dir="outputs"):
        self.frames_dir = Path(frames_dir)
        self.audio_dir = Path(audio_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

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
        return 3.0  # fallback 3 seconds

    def compose_video(self, frame_paths, audio_paths, output_name="lesson.mp4",
                       frames_per_step=5):
        """Compose video with proper frame-audio sync.

        Strategy:
        - frames are grouped: [step0_frame0..step0_frameN, step1_frame0..step1_frameN, ...]
        - audio is: [intro, step0_narration, step1_narration, ..., outro]
        - intro plays during step0's frames
        - step_i narration plays during step_i's frames
        - outro plays during last step's frames
        - each frame within a step shows for (step_audio_duration / frames_per_step)
        """
        existing_frames = [f for f in (frame_paths or []) if os.path.exists(f)]
        existing_audio = [f for f in (audio_paths or []) if os.path.exists(f)]

        if not existing_frames:
            print("No frames to compose")
            return None

        output_path = str(self.output_dir / output_name)

        # Calculate per-step audio durations
        # audio layout: [intro, step_0, step_1, ..., step_N, outro]
        # frame layout: [step0_f0...step0_fN, step1_f0...step1_fN, ...]
        num_frames = len(existing_frames)
        num_audio = len(existing_audio)

        if num_audio == 0:
            return self._compose_frames_only(existing_frames, output_path)

        # Get duration for each audio clip
        audio_durations = [self._get_audio_duration(a) for a in existing_audio]

        # Map audio to frame groups
        # If we have N steps with frames_per_step each = N*frames_per_step frames
        # Audio: intro + N step clips + outro = N+2 clips
        num_steps = num_frames // frames_per_step if frames_per_step > 0 else 1

        # Build per-frame durations
        frame_durations = []
        audio_idx = 0

        for step_i in range(num_steps):
            # Which audio clip plays during this step's frames?
            # intro(step0), step0(step0), step1(step1), ..., outro(last_step)
            if step_i == 0:
                # First step: use intro audio (idx 0) if available
                clip_duration = audio_durations[0] if num_audio > 0 else 3.0
            elif step_i < num_audio - 1:
                # Middle steps: use step_i audio
                clip_duration = audio_durations[step_i] if step_i < num_audio else 3.0
            else:
                # Last step: use outro audio if available
                clip_duration = audio_durations[-1] if num_audio > 1 else 3.0

            per_frame = max(0.5, clip_duration / frames_per_step)
            for _ in range(frames_per_step):
                frame_durations.append(per_frame)

        # Handle leftover frames (if num_frames not divisible by frames_per_step)
        leftover = num_frames - len(frame_durations)
        for _ in range(leftover):
            frame_durations.append(1.0)

        # Step 1: Create ffmpeg concat file with per-frame durations
        concat_file = str(self.output_dir / "concat.txt")
        with open(concat_file, 'w') as f:
            for i, frame in enumerate(existing_frames):
                dur = frame_durations[i] if i < len(frame_durations) else 1.0
                f.write(f"file '{os.path.abspath(frame)}'\n")
                f.write(f"duration {dur:.2f}\n")
            # Last frame (ffmpeg requirement)
            f.write(f"file '{os.path.abspath(existing_frames[-1])}'\n")

        # Step 2: Concat audio files
        audio_concat = str(self.output_dir / "audio_concat.txt")
        with open(audio_concat, 'w') as f:
            for a in existing_audio:
                f.write(f"file '{os.path.abspath(a)}'\n")

        temp_audio = str(self.output_dir / "temp_audio.mp3")
        result = subprocess.run([
            'ffmpeg', '-y', '-f', 'concat', '-safe', '0',
            '-i', audio_concat, '-c', 'copy', temp_audio
        ], capture_output=True, text=True, timeout=60)

        has_audio = result.returncode == 0 and os.path.exists(temp_audio)

        # Step 3: Create video from frames
        temp_video = str(self.output_dir / "temp_video.mp4")
        result = subprocess.run([
            'ffmpeg', '-y',
            '-f', 'concat', '-safe', '0',
            '-i', concat_file,
            '-vf', 'scale=1080:1920,fps=30',
            '-c:v', 'libx264', '-preset', 'fast',
            '-pix_fmt', 'yuv420p',
            temp_video
        ], capture_output=True, text=True, timeout=120)

        # Cleanup concat file
        if os.path.exists(concat_file):
            os.remove(concat_file)
        if os.path.exists(audio_concat):
            os.remove(audio_concat)

        if result.returncode != 0:
            print(f"ffmpeg video failed: {result.stderr[-200:]}")
            return None

        # Step 4: Merge video + audio
        if has_audio:
            result = subprocess.run([
                'ffmpeg', '-y',
                '-i', temp_video,
                '-i', temp_audio,
                '-c:v', 'copy', '-c:a', 'aac',
                '-shortest',
                output_path
            ], capture_output=True, text=True, timeout=60)

            os.remove(temp_audio)
            if os.path.exists(temp_video):
                os.remove(temp_video)

            if result.returncode == 0 and os.path.exists(output_path):
                print(f"Video created (synced): {output_path}")
                return output_path
        else:
            # No audio, just rename
            if os.path.exists(temp_video):
                os.rename(temp_video, output_path)
                print(f"Video created (no audio): {output_path}")
                return output_path

        return None

    def _compose_frames_only(self, frame_paths, output_path):
        """Create video from frames only (no audio)."""
        concat_file = str(self.output_dir / "concat.txt")
        with open(concat_file, 'w') as f:
            for frame in frame_paths:
                f.write(f"file '{os.path.abspath(frame)}'\n")
                f.write("duration 1.0\n")
            f.write(f"file '{os.path.abspath(frame_paths[-1])}'\n")

        result = subprocess.run([
            'ffmpeg', '-y',
            '-f', 'concat', '-safe', '0',
            '-i', concat_file,
            '-vf', 'scale=1080:1920,fps=30',
            '-c:v', 'libx264', '-preset', 'fast',
            '-pix_fmt', 'yuv420p',
            output_path
        ], capture_output=True, text=True, timeout=120)

        if os.path.exists(concat_file):
            os.remove(concat_file)

        if result.returncode == 0 and os.path.exists(output_path):
            print(f"Video created (frames only): {output_path}")
            return output_path
        return None
