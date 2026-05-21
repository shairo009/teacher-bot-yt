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
from src.llm_engine import LLMEngine


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
        self.llm_engine = LLMEngine()

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
        print("  Teacher Bot YT - Premium Formula Book Presenter")
        print("=" * 60)

        # 0. Check if index already exists to skip slow extraction/building step
        index_path = Path("data/topics_index.json")
        if index_path.exists() and not self.force_redownload:
            try:
                with open(index_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    index = data.get('topics', [])
                    if index:
                        self.topic_manager.index = index
                        print(f"Loaded existing topic index with {len(index)} topics from data/topics_index.json")
                        return True
            except Exception as e:
                print(f"Warning: Could not load existing index: {e}")

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
        print("\n[3/4] Building topic index from curriculum...")
        index = self.topic_manager.build_from_curriculum()

        if not index:
            print("Falling back to PDF extraction...")
            index = self.topic_manager.load_index(all_content)

        if not index:
            print("ERROR: No topics found!")
            return False

        # Save index for reference
        with open("data/topics_index.json", 'w', encoding='utf-8') as f:
            json.dump({'total_topics': len(index), 'topics': index}, f, ensure_ascii=False, indent=2)

        print(f"Indexed {len(index)} topics")

        return True

    async def create_video(self):
        """Create a video for the current topic."""
        print("\n[4/4] Creating video...")

        # 0. Check if we should prioritize the premium Formula Book JSON (default behavior for monetization)
        formula_book_path = Path("data/formula_book.json")
        topic = None
        
        # Load from formula book if it exists
        if formula_book_path.exists():
            try:
                with open(formula_book_path, 'r', encoding='utf-8') as f:
                    book_data = json.load(f)
                    formulas = book_data.get("formulas", [])
                    if formulas:
                        idx = self.topic_manager.progress.get("formula_idx", 0)
                        if idx >= len(formulas):
                            idx = 0
                            self.topic_manager.progress["formula_idx"] = 0
                            self.topic_manager._save_progress()
                        
                        topic = formulas[idx]
                        print(f"\n📚 Premium Formula Book Active! Loaded: {topic['formula_title']}")
                        print(f"   Formula: {topic['formula_text']}")
            except Exception as e:
                print(f"Warning: Could not load formula book: {e}")

        # Fallback to general topic manager if formula book is empty/failed
        if not topic:
            topic = self.topic_manager.get_current_topic()

        if not topic:
            print("All topics completed! 🎉")
            return True

        # Process script and parameters
        if 'formula_title' in topic and 'intro_script' in topic:
            # Already pre-designed in formula book! Skip LLM explanation
            print("   ✨ Curated formula metadata found, skipping LLM engine call...")
            topic['lines'] = [topic['formula_title'], topic['formula_text']]
            topic['script'] = topic.get('narration_script', "")
        else:
            # AI reads the raw PDF text and explains it
            print("   🤖 AI is studying the book...")
            explanation = self.llm_engine.explain_topic(topic['topic'], class_num=topic['class'])
            topic['lines'] = explanation['screen_bullet_points']
            topic['script'] = explanation['narration_script']
            # Copy split scripts
            for k, v in explanation.items():
                topic[k] = v

        # Create temp directories
        os.makedirs("temp_frames", exist_ok=True)
        os.makedirs("temp_audio", exist_ok=True)

        # Generate audio parts
        print("   🎙️ Generating split step-based audio...")
        audios = await self.audio_engine.generate_lesson_audio(topic)

        if not audios:
            print("WARNING: No audio generated, video will be silent")
            audios = []

        print(f"   Created {len(audios)} audio parts")

        # Extract audio durations dynamically
        audio_durations = {}
        if audios:
            try:
                from moviepy.editor import AudioFileClip
                for audio_path in audios:
                    name = Path(audio_path).stem  # 'intro', 'step1', 'step2', 'step3', 'outro'
                    clip = AudioFileClip(audio_path)
                    audio_durations[name] = clip.duration
                    clip.close()
                print(f"   Dynamic Audio durations: {audio_durations}")
            except Exception as e:
                print(f"   Error reading audio durations: {e}")

        # Render frames with exact audio timing
        print("   Rendering frames with dynamic sync...")
        frames = await self.render_engine.render_lesson(topic, audio_durations)

        if not frames:
            # Fallback to simple render
            print("   Using simple render...")
            frames = self.render_engine.render_simple(topic)

        if not frames:
            print("ERROR: Could not render frames!")
            return False

        print(f"   Created {len(frames)} frames")

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
                
                # Only delete the video after successful upload
                self.cleanup(video_path)
            else:
                print("   ⚠️ YouTube upload not configured")
        else:
            print(f"\n   ✅ Dry run complete! Video saved: {video_path}")

        # Mark topic as completed (and increment formula index if from formula book)
        if 'formula_title' in topic and formula_book_path.exists():
            self.topic_manager.progress["formula_idx"] = self.topic_manager.progress.get("formula_idx", 0) + 1
            self.topic_manager._save_progress()
            print(f"Formula book topic completed. Next index: {self.topic_manager.progress['formula_idx']}")
        else:
            self.topic_manager.mark_completed(topic['id'])

        return True

    def cleanup(self, video_path=None):
        """Clean up video file after upload, keep other files."""
        if video_path and os.path.exists(video_path):
            try:
                os.remove(video_path)
                print(f"\n🧹 Deleted uploaded video: {video_path}")
            except Exception as e:
                print(f"Could not delete video: {e}")


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