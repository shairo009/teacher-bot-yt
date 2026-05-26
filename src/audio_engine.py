import os
import asyncio
import tempfile
from pathlib import Path


class AudioEngine:
    def __init__(self, output_dir="temp_audio"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.voice = "hi-IN-MadhurNeural"  # Female Hindi voice
        self.available = False

        # Check if edge-tts is available
        try:
            import edge_tts
            self.edge_tts = edge_tts
            self.available = True
        except ImportError:
            self.edge_tts = None

    async def generate_audio(self, text, output_path):
        """Generate audio using Edge-TTS (free, female Hindi)."""
        if not self.available:
            print("Edge-TTS not available - will create text file instead")
            with open(output_path.replace('.mp3', '.txt'), 'w') as f:
                f.write(text)
            return False

        try:
            communicate = self.edge_tts.Communicate(text, self.voice)
            await communicate.save(output_path)
            return os.path.exists(output_path)
        except Exception as e:
            print(f"Edge-TTS failed: {e}")
            return False

    async def generate_lesson_audio(self, topic, lesson_text):
        """Generate full lesson audio from topic content."""
        os.makedirs(self.output_dir, exist_ok=True)

        # Clean and prepare text
        clean_text = self._prepare_text(lesson_text)

        # Split into parts
        intro = f"नमस्ते! आज हम सीखेंगे: {topic.get('chapter', 'Lesson')}"
        main = clean_text
        outro = "अभ्यास करें। धन्यवाद!"

        audio_parts = []

        # Generate intro
        intro_path = self.output_dir / "intro.mp3"
        if await self.generate_audio(intro, str(intro_path)):
            audio_parts.append(str(intro_path))

        # Generate main content
        main_path = self.output_dir / "main.mp3"
        if await self.generate_audio(main, str(main_path)):
            audio_parts.append(str(main_path))

        # Generate outro
        outro_path = self.output_dir / "outro.mp3"
        if await self.generate_audio(outro, str(outro_path)):
            audio_parts.append(str(outro_path))

        return audio_parts

    def _prepare_text(self, text):
        """Clean Hindi text for TTS."""
        text = text.replace('`', '').replace('|', ' ')
        text = text.replace('\\n', ' ').replace('\n', ' ')
        if len(text) > 5000:
            text = text[:5000]
        return text

    def generate_sync(self, topic, lesson_text):
        """Synchronous wrapper for audio generation."""
        try:
            loop = asyncio.get_event_loop()
        except:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        return loop.run_until_complete(self.generate_lesson_audio(topic, lesson_text))


if __name__ == "__main__":
    async def test():
        engine = AudioEngine()
        topic = {
            'class': 6,
            'chapter': 'Chapter 1: Knowing Our Numbers',
            'topic': 'What is a number? Numbers are used to count objects.'
        }
        audios = await engine.generate_lesson_audio(topic, topic['topic'])
        print(f"Generated {len(audios)} audio files")

    asyncio.run(test())