import os
import asyncio
import random
from pathlib import Path


class AudioEngine:
    def __init__(self, output_dir="temp_audio"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # edge-tts voices (English)
        self.edge_voice = 'en-US-JennyNeural'       # female
        self.edge_voice_male = 'en-US-GuyNeural'     # male

    async def _tts(self, text, output_path):
        """Generate TTS using edge-tts."""
        import edge_tts

        try:
            communicate = edge_tts.Communicate(text, self.edge_voice)
            await communicate.save(output_path)
            return os.path.exists(output_path) and os.path.getsize(output_path) > 100
        except Exception as e:
            print(f"  edge-tts error: {e}")
            return False

    async def generate_step_audio(self, narrations):
        """Generate one TTS clip per narration line (synced with visual steps).
        narrations: list of English strings, one per step.
        Returns: list of audio file paths (mp3), one per step.
        """
        os.makedirs(self.output_dir, exist_ok=True)
        audio_parts = []

        for i, text in enumerate(narrations):
            if not text.strip():
                continue
            step_path = str(self.output_dir / f"step_{i:03d}.mp3")
            if await self._tts(text, step_path):
                audio_parts.append(step_path)

        return audio_parts

    async def generate_lesson_audio(self, topic, lesson_text):
        """Generate audio from topic data when narrations are unavailable.
        Builds a teaching script from topic + subtopics.
        """
        os.makedirs(self.output_dir, exist_ok=True)

        topic_name = topic.get('topic', lesson_text or 'Lesson')
        subtopics = topic.get('subtopics', [])
        chapter = topic.get('chapter', 'Chapter')
        class_num = topic.get('class', 6)

        audio_parts = []

        # Random intro — so every video sounds different
        intro_variants = [
            f"Hello kids! Today we'll learn about {topic_name}. This is from class {class_num}, {chapter}. Pay attention!",
            f"Hey kids! Ready? Today's topic is {topic_name}. It's really fun, let's get started!",
            f"Kids, today we're going to learn {topic_name}. This is very important for class {class_num}. Listen carefully!",
            f"Today's lesson is {topic_name}! It's very easy, just follow along with me!",
            f"Get ready! Let's start {topic_name}. It's going to be really interesting!",
        ]
        intro = random.choice(intro_variants)
        intro_path = str(self.output_dir / "intro.mp3")
        if await self._tts(intro, intro_path):
            audio_parts.append(intro_path)

        # Random connectors for subtopic steps
        connectors = [
            "Now let's understand:", "Let's look at:", "Next topic:",
            "Now let's talk about:", "After this, look:", "Now comes:",
        ]

        # Generate teaching narrations from subtopics
        if subtopics:
            for i, sub in enumerate(subtopics[:5]):
                connector = random.choice(connectors)
                step_text = f"{connector} {sub}. {self._subtopic_hint(sub)}"
                step_path = str(self.output_dir / f"step_{i:03d}.mp3")
                if await self._tts(step_text, step_path):
                    audio_parts.append(step_path)
        else:
            # No subtopics — teach from topic text directly
            clean_text = self._prepare_text(lesson_text or topic_name)
            main_path = str(self.output_dir / "main.mp3")
            if await self._tts(clean_text, main_path):
                audio_parts.append(main_path)

        # Random outro
        outro_variants = [
            f"Great job! You must have understood {topic_name}. Make sure to practice. Thank you!",
            f"Wow kids! You learned {topic_name} really well. Now practice it yourself!",
            f"Well done! {topic_name} is done. If you practice every day, you'll master it!",
            f"Great work! You got {topic_name}. Don't forget your homework! See you in the next lesson!",
        ]
        outro = random.choice(outro_variants)
        outro_path = str(self.output_dir / "outro.mp3")
        if await self._tts(outro, outro_path):
            audio_parts.append(outro_path)

        return audio_parts

    @staticmethod
    def _subtopic_hint(sub):
        """Generate a short English teaching hint for a subtopic."""
        sub_lower = sub.lower()
        if any(k in sub_lower for k in ['example', 'problem', 'practice']):
            return "Look at the example and try it yourself."
        if any(k in sub_lower for k in ['definition', 'what is', 'basics', 'introduction']):
            return "First understand the basics, then we'll move forward."
        if any(k in sub_lower for k in ['property', 'properties', 'rule']):
            return "Remember these rules, they're very important."
        if any(k in sub_lower for k in ['formula', 'equation']):
            return "Remember this formula."
        return "Watch carefully, it's very easy."

    def _prepare_text(self, text):
        """Clean text for TTS."""
        text = text.replace('`', '').replace('|', ' ')
        text = text.replace('\\n', ' ').replace('\n', ' ')
        if len(text) > 5000:
            text = text[:5000]
        return text


async def _test():
    engine = AudioEngine()
    narrations = [
        "Let's add three and two together. Take three balls, then add two more balls.",
        "That makes five balls in total. Three plus two equals five.",
    ]
    audios = await engine.generate_step_audio(narrations)
    print(f"Generated {len(audios)} audio files: {audios}")

if __name__ == "__main__":
    asyncio.run(_test())
