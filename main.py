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

        # 0. Check if we have curriculum_master.json to build/load the master index directly
        curriculum_path = Path("curriculum_master.json")
        index_path = Path("data/topics_index.json")
        
        if curriculum_path.exists():
            print("\n[Direct Load] Found curriculum_master.json! Building master index...")
            index = self.topic_manager.build_from_curriculum()
            if index:
                # Save index for reference
                os.makedirs("data", exist_ok=True)
                with open(index_path, 'w', encoding='utf-8') as f:
                    json.dump({'total_topics': len(index), 'topics': index}, f, ensure_ascii=False, indent=2)
                print(f"✅ Loaded and saved master index with {len(index)} progressive topics (Class 1 to PhD Level)!")
                return True

        # Fallback to loading existing topic index
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

        # Load current topic from master curriculum index
        topic = self.topic_manager.get_current_topic()

        if not topic:
            print("All topics completed! 🎉")
            return True

        # Process script and parameters via LLM
        print("   🤖 AI is studying the topic...")
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
                    title=f"{topic['level']} - {topic['chapter']}",
                    description=f"Math Lesson\nLevel: {topic['level']}\nChapter: {topic['chapter']}\nTopic: {topic['topic']}\n\n#math #education #{topic['level'].lower().replace(' ', '')}"
                )
                print(f"   Uploaded! Video ID: {video_id}")
                
                # Only delete the video after successful upload
                self.cleanup(video_path)
            else:
                print("   ⚠️ YouTube upload not configured")
        else:
            print(f"\n   ✅ Dry run complete! Video saved: {video_path}")

        # Mark topic as completed
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
    
    # Parse batch size: e.g. --batch 5
    batch_size = 5
    for idx, arg in enumerate(sys.argv):
        if arg == "--batch" and idx + 1 < len(sys.argv):
            try:
                batch_size = int(sys.argv[idx + 1])
            except ValueError:
                pass

    bot = TeacherBot(dry_run=dry_run, force_redownload=force_redownload)

    # Initialize (download/load curriculum and index)
    if not await bot.initialize():
        print("\n❌ Initialization failed!")
        sys.exit(1)

    print(f"\n🚀 Running video generation batch: {batch_size} videos to create sequentially...\n")

    successful_videos = 0
    for i in range(batch_size):
        print(f"\n🎬 === Video {i+1}/{batch_size} ===")
        try:
            if await bot.create_video():
                successful_videos += 1
            else:
                print(f"❌ Failed to create video {i+1}!")
                break
        except Exception as e:
            print(f"❌ Exception in video {i+1}: {e}")
            break

    print(f"\n✅ Batch run complete! {successful_videos}/{batch_size} videos created successfully.")


if __name__ == "__main__":
    asyncio.run(main())