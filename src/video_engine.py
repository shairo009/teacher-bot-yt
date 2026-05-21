import os
from pathlib import Path


class VideoEngine:
    def __init__(self, frames_dir="temp_frames", audio_dir="temp_audio", output_dir="outputs"):
        self.frames_dir = Path(frames_dir)
        self.audio_dir = Path(audio_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def compose_video(self, frame_paths, audio_paths, output_name="lesson.mp4"):
        """Compose video from frames or direct video, and audio using MoviePy."""
        try:
            from moviepy.editor import (ImageClip, AudioFileClip, VideoFileClip,
                                        concatenate_videoclips, concatenate_audioclips)
        except ImportError:
            print("MoviePy not installed. Installing...")
            os.system("pip install moviepy -q")
            from moviepy.editor import (ImageClip, AudioFileClip, VideoFileClip,
                                        concatenate_videoclips, concatenate_audioclips)

        if not frame_paths:
            print("No frames/videos to compose")
            return None

        output_path = self.output_dir / output_name
        is_direct_video = len(frame_paths) == 1 and frame_paths[0].endswith(".mp4")

        try:
            if is_direct_video:
                print(f"🎬 Loading direct video clip (stripping pre-existing audio): {frame_paths[0]}")
                video = VideoFileClip(frame_paths[0]).without_audio()
            else:
                clips = []
                # Create image clips from frames
                for frame_path in frame_paths:
                    if os.path.exists(frame_path):
                        clip = ImageClip(frame_path).set_duration(0.5)  # 0.5s per frame
                        clips.append(clip)

                if not clips:
                    print("No valid frame clips created")
                    return None

                # Concatenate frames
                video = concatenate_videoclips(clips, method="compose")

            # Add audio if available
            if audio_paths:
                audio_clips = []
                for audio_path in audio_paths:
                    if os.path.exists(audio_path):
                        audio_clips.append(AudioFileClip(audio_path))

                if audio_clips:
                    combined_audio = concatenate_audioclips(audio_clips)
                    
                    # Match silent video/audio duration dynamically and smoothly first
                    if video.duration < combined_audio.duration:
                        # Loop silent video smoothly to match audio duration
                        repeats = int(combined_audio.duration / video.duration) + 1
                        video = concatenate_videoclips([video] * repeats)
                        video = video.subclip(0, combined_audio.duration)
                    elif combined_audio.duration < video.duration:
                        # Trim silent video to match audio
                        video = video.subclip(0, combined_audio.duration)

                    # Bind the combined audio exactly once to the final looped/trimmed silent video
                    video = video.set_audio(combined_audio)

            # Write video
            video.write_videofile(
                str(output_path),
                fps=30,
                codec='libx264',
                audio_codec='aac',
                preset='fast',
                verbose=False,
                logger=None
            )

            video.close()

            if os.path.exists(output_path):
                print(f"Video created: {output_path}")
                return str(output_path)

        except Exception as e:
            print(f"Video composition error: {e}")

            # Fallback: just copy first frame as video
            try:
                import subprocess
                first_frame = frame_paths[0] if frame_paths else None
                if first_frame and os.path.exists(first_frame):
                    result = subprocess.run([
                        'ffmpeg', '-y',
                        '-loop', '1', '-i', first_frame,
                        '-c:v', 'libx264', '-t', '10',
                        '-pix_fmt', 'yuv420p',
                        '-vf', 'scale=1080:1920',
                        str(output_path)
                    ], capture_output=True, text=True)
                    if result.returncode == 0:
                        print(f"Fallback video created: {output_path}")
                        return str(output_path)
            except:
                pass

        return None

    def create_simple_video(self, frame_paths, output_name="lesson.mp4"):
        """Simple video from frames only (no audio)."""
        output_path = self.output_dir / output_name
        self.output_dir.mkdir(parents=True, exist_ok=True)

        if not frame_paths:
            return None

        try:
            import subprocess

            # Create file list for ffmpeg
            list_file = self.output_dir / "frames.txt"
            with open(list_file, 'w') as f:
                for frame in sorted(frame_paths):
                    f.write(f"file '{frame}'\n")
                    f.write(f"duration 0.5\n")

            # Last frame needs no duration (ffmpeg convention)
            with open(list_file, 'a') as f:
                last = sorted(frame_paths)[-1]
                f.write(f"file '{last}'\n")

            result = subprocess.run([
                'ffmpeg', '-y',
                '-f', 'concat', '-safe', '0',
                '-i', str(list_file),
                '-vf', 'scale=1080:1920,fps=30',
                '-c:v', 'libx264',
                '-preset', 'fast',
                '-pix_fmt', 'yuv420p',
                str(output_path)
            ], capture_output=True, text=True)

            list_file.unlink()

            if result.returncode == 0 and os.path.exists(output_path):
                print(f"Simple video created: {output_path}")
                return str(output_path)

        except Exception as e:
            print(f"Simple video error: {e}")

        return None


if __name__ == "__main__":
    engine = VideoEngine()
    test_frames = list(Path("temp_frames").glob("*.png"))[:18]
    video = engine.create_simple_video([str(f) for f in test_frames])
    print(f"Test video: {video}")