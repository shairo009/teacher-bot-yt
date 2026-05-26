import os
import subprocess
import shutil
from pathlib import Path


class VideoEngine:
    def __init__(self, frames_dir="temp_frames", audio_dir="temp_audio", output_dir="outputs"):
        self.frames_dir = Path(frames_dir)
        self.audio_dir = Path(audio_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.has_ffmpeg = shutil.which('ffmpeg') is not None
        self.has_moviepy = False
        try:
            from moviepy.editor import ImageClip
            self.has_moviepy = True
        except ImportError:
            pass

    def compose_video(self, frame_paths, audio_paths, output_name="lesson.mp4",
                       frame_duration=None):
        """Compose video from frames and audio. Uses MoviePy if available, else ffmpeg."""
        if not frame_paths:
            print("No frames to compose")
            return None

        # Filter to existing frames only
        existing_frames = [f for f in frame_paths if os.path.exists(f)]
        if not existing_frames:
            print("No frame files found")
            return None

        # Filter to existing audio only
        existing_audio = [f for f in (audio_paths or []) if os.path.exists(f)]

        if self.has_moviepy:
            return self._compose_moviepy(existing_frames, existing_audio, output_name, frame_duration)
        elif self.has_ffmpeg:
            return self._compose_ffmpeg(existing_frames, existing_audio, output_name)
        else:
            print("Neither MoviePy nor ffmpeg available")
            return None

    def _compose_moviepy(self, frame_paths, audio_paths, output_name, frame_duration):
        """Compose using MoviePy."""
        try:
            from moviepy.editor import (ImageClip, AudioFileClip,
                                        concatenate_videoclips, concatenate_audioclips)
        except ImportError:
            print("MoviePy import failed, falling back to ffmpeg")
            return self._compose_ffmpeg(frame_paths, audio_paths, output_name)

        output_path = self.output_dir / output_name

        try:
            # Calculate total audio duration
            total_audio_duration = 0
            for audio_path in audio_paths:
                try:
                    ac = AudioFileClip(audio_path)
                    total_audio_duration += ac.duration
                    ac.close()
                except:
                    pass

            # Determine frame duration
            if frame_duration is None:
                if total_audio_duration > 0 and len(frame_paths) > 0:
                    frame_duration = total_audio_duration / len(frame_paths)
                else:
                    frame_duration = 0.5
            frame_duration = max(0.3, min(frame_duration, 3.0))

            # Create clips
            clips = []
            for frame_path in frame_paths:
                clip = ImageClip(frame_path).set_duration(frame_duration)
                clips.append(clip)

            if not clips:
                return None

            video = concatenate_videoclips(clips, method="compose")

            # Add audio
            if audio_paths:
                audio_clips = [AudioFileClip(a) for a in audio_paths]
                if audio_clips:
                    combined_audio = concatenate_audioclips(audio_clips)
                    video = video.set_audio(combined_audio)
                    if video.duration < combined_audio.duration:
                        video = video.set_duration(combined_audio.duration)

            video.write_videofile(
                str(output_path), fps=30, codec='libx264',
                audio_codec='aac', preset='fast',
                verbose=False, logger=None
            )
            video.close()

            if os.path.exists(output_path):
                print(f"Video created (MoviePy): {output_path}")
                return str(output_path)

        except Exception as e:
            print(f"MoviePy error: {e}, falling back to ffmpeg")
            return self._compose_ffmpeg(frame_paths, audio_paths, output_name)

        return None

    def _compose_ffmpeg(self, frame_paths, audio_paths, output_name):
        """Compose using ffmpeg (no MoviePy needed)."""
        output_path = str(self.output_dir / output_name)

        # Get absolute paths
        abs_frames = [os.path.abspath(f) for f in frame_paths]
        abs_audio = [os.path.abspath(a) for a in audio_paths] if audio_paths else []

        # Create concat file for frames
        list_file = os.path.abspath(os.path.join(str(self.output_dir), "frames.txt"))
        with open(list_file, 'w') as f:
            for frame in abs_frames:
                f.write(f"file '{frame}'\n")
                f.write("duration 0.5\n")
            f.write(f"file '{abs_frames[-1]}'\n")

        # Get total audio duration for video length
        audio_duration = 10  # default
        if abs_audio:
            try:
                probe = subprocess.run(
                    ['ffprobe', '-v', 'error', '-show_entries', 'format=duration',
                     '-of', 'default=noprint_wrappers=1:nokey=1', abs_audio[0]],
                    capture_output=True, text=True
                )
                if probe.returncode == 0:
                    audio_duration = float(probe.stdout.strip())
            except:
                pass

        # Step 1: Create video from frames
        temp_video = os.path.abspath(os.path.join(str(self.output_dir), "temp_video.mp4"))
        result = subprocess.run([
            'ffmpeg', '-y',
            '-f', 'concat', '-safe', '0',
            '-i', list_file,
            '-vf', 'scale=1080:1920,fps=30',
            '-c:v', 'libx264', '-preset', 'fast',
            '-pix_fmt', 'yuv420p',
            '-t', str(audio_duration),
            temp_video
        ], capture_output=True, text=True)

        if os.path.exists(list_file):
            os.remove(list_file)

        if result.returncode != 0:
            print(f"ffmpeg video failed: {result.stderr[-200:]}")
            return None

        # Step 2: Merge audio if available
        if abs_audio:
            # Concat audio files first
            audio_list = os.path.abspath(os.path.join(str(self.output_dir), "audio.txt"))
            with open(audio_list, 'w') as f:
                for a in abs_audio:
                    f.write(f"file '{a}'\n")

            temp_audio = os.path.abspath(os.path.join(str(self.output_dir), "temp_audio_concat.mp3"))
            subprocess.run([
                'ffmpeg', '-y', '-f', 'concat', '-safe', '0',
                '-i', audio_list, '-c', 'copy', temp_audio
            ], capture_output=True, text=True)

            if os.path.exists(audio_list):
                os.remove(audio_list)

            # Merge video + audio
            if os.path.exists(temp_audio):
                result = subprocess.run([
                    'ffmpeg', '-y',
                    '-i', temp_video,
                    '-i', temp_audio,
                    '-c:v', 'copy', '-c:a', 'aac',
                    '-shortest',
                    output_path
                ], capture_output=True, text=True)

                os.remove(temp_audio)
                if os.path.exists(temp_video):
                    os.remove(temp_video)

                if result.returncode == 0 and os.path.exists(output_path):
                    print(f"Video created (ffmpeg): {output_path}")
                    return output_path

        # No audio - just rename temp
        if os.path.exists(temp_video):
            os.rename(temp_video, output_path)
            print(f"Video created (ffmpeg, no audio): {output_path}")
            return output_path

        return None

        return None

    def create_simple_video(self, frame_paths, output_name="lesson.mp4"):
        """Simple video from frames only (no audio)."""
        output_path = self.output_dir / output_name
        self.output_dir.mkdir(parents=True, exist_ok=True)

        if not frame_paths:
            return None

        try:
            import subprocess
            import glob as globmod

            # Use absolute paths for ffmpeg
            abs_frames = [os.path.abspath(f) for f in sorted(frame_paths)]

            # Check which frames actually exist
            existing = [f for f in abs_frames if os.path.exists(f)]
            if not existing:
                print("No frame files found")
                return None

            # Create file list with absolute paths
            list_file = os.path.abspath(os.path.join(str(self.output_dir), "frames.txt"))
            with open(list_file, 'w') as f:
                for frame in existing:
                    f.write(f"file '{frame}'\n")
                    f.write(f"duration 0.5\n")
                # Last frame needs no duration (ffmpeg convention)
                f.write(f"file '{existing[-1]}'\n")

            result = subprocess.run([
                'ffmpeg', '-y',
                '-f', 'concat', '-safe', '0',
                '-i', list_file,
                '-vf', 'scale=1080:1920,fps=30',
                '-c:v', 'libx264',
                '-preset', 'fast',
                '-pix_fmt', 'yuv420p',
                str(output_path)
            ], capture_output=True, text=True)

            # Clean up
            if os.path.exists(list_file):
                os.remove(list_file)

            if result.returncode == 0 and os.path.exists(output_path):
                print(f"Simple video created: {output_path}")
                return str(output_path)
            else:
                print(f"ffmpeg failed (code {result.returncode}): {result.stderr[-200:]}")

        except Exception as e:
            print(f"Simple video error: {e}")

        return None


if __name__ == "__main__":
    engine = VideoEngine()
    test_frames = list(Path("temp_frames").glob("*.png"))[:18]
    video = engine.create_simple_video([str(f) for f in test_frames])
    print(f"Test video: {video}")