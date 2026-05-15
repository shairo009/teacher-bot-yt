import os
import asyncio


class AudioEngine:
    def __init__(self, output_dir="temp_audio"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.voice = "hi-IN-MadhurNeural"  # Female Hindi voice

    async def generate_audio(self, text, output_path):
        """Generate audio using Edge-TTS (free, female Hindi)."""
        try:
            import edge_tts
        except ImportError:
            print("Installing edge-tts...")
            os.system("pip install edge-tts -q")
            import edge_tts

        try:
            communicate = edge_tts.Communicate(text, self.voice)
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

        # Split into parts for better timing
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
        # Remove special characters that might cause issues
        text = text.replace('`', '').replace('|', ' ')
        text = text.replace('\\n', ' ').replace('\n', ' ')
        # Limit text length for API
        if len(text) > 5000:
            text = text[:5000]
        return text


from pathlib import Path

if __name__ == "__main__":
    async def test():
        engine = AudioEngine()
        topic = {
            'class': 6,
            'chapter': 'Chapter 1: Knowing Our Numbers',
            'topic': 'What is a number? Numbers are used to count objects. We use digits 0 to 9 to form numbers.'
        }
        audios = await engine.generate_lesson_audio(topic, topic['topic'])
        print(f"Generated {len(audios)} audio files")
        for a in audios:
            print(f"  - {a}")

    asyncio.run(test())