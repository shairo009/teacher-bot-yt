import os
import sys
import asyncio
import json
from pathlib import Path
from datetime import datetime

# Import our modules
from src.pdf_downloader import PDFDownloader
from src.pdf_extractor import PDFExtractor
from src.topic_manager import TopicManager
from src.render_engine import RenderEngine
from src.audio_engine import AudioEngine
from src.video_engine import VideoEngine


class TeacherBot:
    def __init__(self, dry_run=False, force_redownload=False):
        self.dry_run = dry_run
        self.force_redownload = force_redownload

        # Components
        self.pdf_downloader = PDFDownloader()
        self.pdf_extractor = PDFExtractor()
        self.topic_manager = TopicManager()
        self.render_engine = RenderEngine()
        self.audio_engine = AudioEngine()
        self.video_engine = VideoEngine()

        self.uploader = None  # Lazy load

    def setup_uploader(self):
        if self.uploader is None:
            try:
                from src.uploader import YouTubeUploader
                self.uploader = YouTubeUploader()
            except Exception as e:
                print(f"Warning: YouTube uploader not available: {e}")

    async def initialize(self):
        """Download PDFs and build topic index if needed."""
        print("=" * 60)
        print("  Teacher Bot YT - NCERT Video Creator")
        print("=" * 60)

        # Check if we need to download PDFs
        pdf_files = self.pdf_downloader.get_available_pdfs()

        if not pdf_files or self.force_redownload:
            print("\n[1/4] Downloading NCERT books...")
            downloaded, failed = self.pdf_downloader.download_all_books()
            pdf_files = self.pdf_downloader.get_available_pdfs()
            print(f"Downloaded {len(downloaded)} books")
            if failed:
                print(f"Failed: {len(failed)}")
        else:
            print(f"\n[1/4] Found {len(pdf_files)} existing PDFs")

        # Extract topics from PDFs
        print("\n[2/4] Extracting topics from books...")
        all_content = self.pdf_extractor.extract_all(pdf_files)

        if not all_content:
            print("ERROR: No content extracted from PDFs!")
            return False

        # Build and save topic index
        print("\n[3/4] Building topic index...")
        index = self.topic_manager.load_index(all_content)

        if not index:
            print("ERROR: No topics found in books!")
            return False

        # Save index for reference
        with open("data/topics_index.json", 'w', encoding='utf-8') as f:
            json.dump({'total_topics': len(index), 'topics': index}, f, ensure_ascii=False, indent=2)

        print(f"Indexed {len(index)} topics")

        return True

    async def create_video(self):
        """Create a video for the current topic."""
        print("\n[4/4] Creating video...")

        # Get current topic
        topic = self.topic_manager.get_current_topic()

        if not topic:
            print("All topics completed! 🎉")
            return True

        # Display current topic info
        print(f"\n📚 Current: Class {topic['class']} | {topic['chapter']}")
        print(f"   Topic: {topic['topic'][:80]}...")

        # Create temp directories
        os.makedirs("temp_frames", exist_ok=True)
        os.makedirs("temp_audio", exist_ok=True)

        # Render frames
        print("   Rendering frames...")
        frames = await self.render_engine.render_lesson(topic)

        if not frames:
            # Fallback to simple render
            print("   Using simple render...")
            frames = self.render_engine.render_simple(topic)

        if not frames:
            print("ERROR: Could not render frames!")
            return False

        print(f"   Created {len(frames)} frames")

        # Generate audio
        print("   Generating audio...")
        audios = await self.audio_engine.generate_lesson_audio(topic, topic['topic'])

        if not audios:
            print("WARNING: No audio generated, video will be silent")
            audios = []

        print(f"   Created {len(audios)} audio parts")

        # Compose video
        print("   Composing video...")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_name = f"lesson_class{topic['class']}_{timestamp}.mp4"

        video_path = self.video_engine.compose_video(frames, audios, output_name)

        if not video_path:
            # Try simple video
            video_path = self.video_engine.create_simple_video(frames, output_name)

        if not video_path:
            print("ERROR: Could not create video!")
            return False

        print(f"   Video: {video_path}")

        # Upload if not dry run
        if not self.dry_run:
            self.setup_uploader()
            if self.uploader:
                print("\n   Uploading to YouTube...")
                video_id = self.uploader.upload_video(
                    video_path,
                    title=f"Class {topic['class']} - {topic['chapter']} | NCERT Hindi",
                    description=f"NCERT Math Lesson\nClass {topic['class']}\nChapter: {topic['chapter']}\n\n#ncert #math #class{topic['class']} #education #hindi"
                )
                print(f"   Uploaded! Video ID: {video_id}")
            else:
                print("   ⚠️ YouTube upload not configured")
        else:
            print(f"\n   ✅ Dry run complete! Video saved: {video_path}")

        # Mark topic as completed
        self.topic_manager.mark_completed(topic['id'])

        # Cleanup
        self.cleanup()

        return True

    def cleanup(self):
        """Clean up temporary files."""
        import shutil
        for dir_path in ["temp_frames", "temp_audio"]:
            if os.path.exists(dir_path):
                try:
                    shutil.rmtree(dir_path)
                except:
                    pass

        if os.path.exists("temp_lesson.html"):
            os.remove("temp_lesson.html")

        if os.path.exists("temp_audio"):
            os.makedirs("temp_audio", exist_ok=True)

        print("\n🧹 Cleanup done")


async def main():
    dry_run = "--dry-run" in sys.argv or "-d" in sys.argv
    force_redownload = "--force" in sys.argv or "-f" in sys.argv

    bot = TeacherBot(dry_run=dry_run, force_redownload=force_redownload)

    # Initialize (download PDFs, build index)
    if not await bot.initialize():
        print("\n❌ Initialization failed!")
        sys.exit(1)

    # Create video for current topic
    if not await bot.create_video():
        print("\n❌ Video creation failed!")
        sys.exit(1)

    print("\n✅ Teacher Bot completed successfully!")


if __name__ == "__main__":
    asyncio.run(main())