import os
import sys
import shutil
import asyncio
import json
from pathlib import Path
from datetime import datetime

# Import our modules
from src.pdf_downloader import PDFDownloader
from src.pdf_extractor import PDFExtractor
from src.topic_manager import TopicManager


class TeacherBot:
    def __init__(self, dry_run=False, force_redownload=False):
        self.dry_run = dry_run
        self.force_redownload = force_redownload

        # Components
        self.pdf_downloader = PDFDownloader()
        self.pdf_extractor = PDFExtractor()
        self.topic_manager = TopicManager()

        # Optional components (loaded later)
        self.render_engine = None
        self.audio_engine = None
        self.video_engine = None
        self.uploader = None

    def _init_optional_components(self):
        """Initialize optional components that may not be installed."""
        try:
            from src.render_engine import RenderEngine
            self.render_engine = RenderEngine()
            print("  ✓ RenderEngine loaded")
        except Exception as e:
            print(f"  ✗ RenderEngine not available: {e}")

        try:
            from src.audio_engine import AudioEngine
            self.audio_engine = AudioEngine()
            print("  ✓ AudioEngine loaded")
        except Exception as e:
            print(f"  ✗ AudioEngine not available: {e}")

        try:
            from src.video_engine import VideoEngine
            self.video_engine = VideoEngine()
            print("  ✓ VideoEngine loaded")
        except Exception as e:
            print(f"  ✗ VideoEngine not available: {e}")

    def setup_uploader(self):
        if self.uploader is None:
            try:
                from src.uploader import YouTubeUploader
                self.uploader = YouTubeUploader()
                print("  ✓ YouTube uploader loaded")
            except Exception as e:
                print(f"  ✗ YouTube uploader not available: {e}")

    async def initialize(self):
        """Load curriculum and build topic index."""
        print("=" * 60)
        print("  Teacher Bot YT - NCERT Video Creator")
        print("=" * 60)

        # Load curriculum as "books"
        print("\n[1/4] Loading curriculum...")
        books = self.pdf_downloader.get_available_books()
        print(f"  Found {len(books)} curriculum items (chapters)")

        # Extract content
        print("\n[2/4] Extracting content...")
        all_content = self.pdf_extractor.extract_all()
        print(f"  Extracted {len(all_content)} classes")

        # Build index
        print("\n[3/4] Building topic index...")
        index = self.topic_manager.load_index(all_content)
        print(f"  Indexed {len(index)} topics")

        # Save index
        os.makedirs("data", exist_ok=True)
        with open("data/topics_index.json", 'w', encoding='utf-8') as f:
            json.dump({'total_topics': len(index), 'topics': index}, f, ensure_ascii=False, indent=2)

        # Init optional components
        print("\n[4/4] Loading components...")
        self._init_optional_components()

        return True

    async def create_video(self):
        """Create a video for the current topic."""
        print("\n" + "=" * 60)
        print("  Creating Video...")
        print("=" * 60)

        # Get current topic
        topic = self.topic_manager.get_current_topic()

        if not topic:
            print("All topics completed! 🎉")
            return True

        print(f"\n📚 Current: Class {topic['class']} | {topic['chapter']}")
        print(f"   Topic: {topic['topic']}")
        print()

        # Create temp directories
        os.makedirs("temp_frames", exist_ok=True)
        os.makedirs("temp_audio", exist_ok=True)
        os.makedirs("outputs", exist_ok=True)

        video_created = False

        # Try to render frames (now returns frames + narrations)
        if self.render_engine:
            print("  Rendering frames...")
            try:
                frames, narrations = await self.render_engine.render_lesson(topic)
                print(f"    Created {len(frames)} frames, {len(narrations)} narration lines")

                # Generate audio from LLM narrations (visual-synced)
                audios = []
                if self.audio_engine:
                    print("  Generating audio...")
                    try:
                        if narrations:
                            # Per-step audio: each visual gets its own TTS clip
                            audios = self.audio_engine.generate_step_audio(narrations)
                        else:
                            # Fallback: raw topic text (boring, but works)
                            audios = self.audio_engine.generate_lesson_audio(topic, topic['topic'])
                        print(f"    Created {len(audios)} audio files")
                    except Exception as e:
                        print(f"    Audio generation failed: {e}")

                # Try to compose video
                if self.video_engine and frames:
                    print("  Composing video...")
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    output_name = f"lesson_class{topic['class']}_{timestamp}.mp4"
                    video_path = self.video_engine.compose_video(frames, audios, output_name, frames_per_step=5)

                    if video_path:
                        print(f"    ✅ Video: {video_path}")
                        video_created = True
                    else:
                        print("    ⚠️ Could not compose video")
                        # Save frame info as fallback
                        with open(f"outputs/lesson_info.json", 'w') as f:
                            json.dump({
                                'topic': topic,
                                'frames_count': len(frames),
                                'audios_count': len(audios)
                            }, f, indent=2)
            except Exception as e:
                print(f"  Rendering failed: {e}")
        else:
            print("  ⚠️ RenderEngine not available")
            print("  Topic data saved for manual processing")

        # Show what we have
        print("\n  📊 Status:")
        print(f"     - Topic: {topic['topic']}")
        print(f"     - Class: {topic['class']}")
        print(f"     - Chapter: {topic['chapter']}")
        print(f"     - Video created: {'Yes' if video_created else 'No (needs dependencies)'}")

        # Upload if not dry run and video was created
        if not self.dry_run and video_created:
            self.setup_uploader()
            if self.uploader:
                print("\n  Uploading to YouTube...")
                video_id = self.uploader.upload_video(
                    video_path,
                    title=f"Class {topic['class']} - {topic['chapter']} | NCERT Hindi",
                    description=f"NCERT Math Lesson\nClass {topic['class']}\nChapter: {topic['chapter']}\n\n#ncert #math #class{topic['class']} #education #hindi"
                )
                if video_id:
                    print(f"  ✅ Uploaded! Video ID: {video_id}")
        elif self.dry_run:
            print("\n  ✅ Dry run complete!")

        # Log to video history
        self._log_video_history(topic, video_created, video_path if video_created else None)

        # Mark topic as completed
        self.topic_manager.mark_completed(topic.get('id', 0))

        # Cleanup temp files after everything is done
        self._cleanup_temp()

        return True

    def _log_video_history(self, topic, video_created, video_path=None):
        """Append video generation record to history log."""
        history_file = Path("data/video_history.json")
        history = []
        if history_file.exists():
            try:
                with open(history_file, 'r') as f:
                    history = json.load(f)
            except Exception:
                history = []

        entry = {
            "timestamp": datetime.now().isoformat(),
            "class": topic.get('class'),
            "chapter": topic.get('chapter'),
            "topic": topic.get('topic'),
            "topic_id": topic.get('id'),
            "video_created": video_created,
            "video_file": Path(video_path).name if video_path else None
        }
        history.append(entry)

        with open(history_file, 'w') as f:
            json.dump(history, f, indent=2, ensure_ascii=False)
        print(f"  📝 History logged ({len(history)} total videos)")

    def _cleanup_temp(self):
        """Remove temp files after video generation."""
        cleaned = 0
        for d in ["temp_frames", "temp_audio"]:
            if os.path.exists(d):
                shutil.rmtree(d)
                cleaned += 1

        # Remove stale outputs but keep the latest video
        if os.path.exists("outputs"):
            videos = sorted(Path("outputs").glob("*.mp4"), key=lambda p: p.stat().st_mtime)
            for v in videos[:-1]:  # keep only the latest
                v.unlink()
                cleaned += 1
            # Remove non-video files
            for f in Path("outputs").iterdir():
                if f.suffix != ".mp4":
                    f.unlink()
                    cleaned += 1

        # Remove rebuilt index from disk (regenerated each run, don't need to persist)
        if os.path.exists("data/topics_index.json"):
            os.remove("data/topics_index.json")
            cleaned += 1

        print(f"  🧹 Cleanup done ({cleaned} items removed)")

    def show_progress(self):
        """Show current progress."""
        stats = self.topic_manager.get_progress_stats()
        print("\n" + "=" * 60)
        print("  Progress Report")
        print("=" * 60)
        print(f"  Total topics: {stats['total_topics']}")
        print(f"  Completed: {stats['completed']}")
        print(f"  Remaining: {stats['remaining']}")
        print(f"  Progress: {stats['percentage']}%")

        topic = self.topic_manager.get_current_topic()
        if topic:
            print(f"\n  Next topic: Class {topic['class']} | {topic['chapter']}")
            print(f"  Subtopic: {topic['topic']}")


async def main():
    dry_run = "--dry-run" in sys.argv or "-d" in sys.argv
    force_redownload = "--force" in sys.argv or "-f" in sys.argv
    show_progress = "--progress" in sys.argv or "-p" in sys.argv

    bot = TeacherBot(dry_run=dry_run, force_redownload=force_redownload)

    # Initialize
    if not await bot.initialize():
        print("\n❌ Initialization failed!")
        sys.exit(1)

    if show_progress:
        bot.show_progress()
        return

    # Create video
    if not await bot.create_video():
        print("\n❌ Video creation failed!")
        sys.exit(1)

    print("\n✅ Teacher Bot completed!")


if __name__ == "__main__":
    asyncio.run(main())