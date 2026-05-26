import os
import requests
from pathlib import Path


class AudioEngine:
    def __init__(self, output_dir="temp_audio"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # ElevenLabs config (Adam voice, Hindi multilingual)
        self.api_key = os.environ.get('ELEVENLABS_API_KEY', '')
        self.voice_id = 'pNInz6obpgDQGcFmaJgB'  # Adam
        self.model_id = 'eleven_multilingual_v2'  # Hindi support
        self.available = bool(self.api_key)

    def _tts(self, text, output_path):
        """Generate TTS audio using ElevenLabs API (synchronous)."""
        if not self.available:
            print("  ElevenLabs API key not set")
            return False

        resp = requests.post(
            f'https://api.elevenlabs.io/v1/text-to-speech/{self.voice_id}',
            headers={
                'xi-api-key': self.api_key,
                'Content-Type': 'application/json',
            },
            json={
                'text': text,
                'model_id': self.model_id,
                'voice_settings': {'stability': 0.5, 'similarity_boost': 0.75}
            },
            timeout=30
        )

        if resp.status_code == 200:
            with open(output_path, 'wb') as f:
                f.write(resp.content)
            return True
        else:
            print(f"  ElevenLabs error {resp.status_code}: {resp.text[:100]}")
            return False

    def generate_step_audio(self, narrations):
        """Generate one TTS clip per narration line (synced with visual steps).
        narrations: list of Hindi strings, one per step.
        Returns: list of audio file paths (mp3), one per step.
        """
        os.makedirs(self.output_dir, exist_ok=True)
        audio_parts = []

        # Intro
        intro_path = str(self.output_dir / "step_intro.mp3")
        if self._tts("नमस्ते बच्चों! आज हम एक नया टॉपिक सीखेंगे।", intro_path):
            audio_parts.append(intro_path)

        # Per-step narration
        for i, text in enumerate(narrations):
            if not text.strip():
                continue
            step_path = str(self.output_dir / f"step_{i:03d}.mp3")
            if self._tts(text, step_path):
                audio_parts.append(step_path)

        # Outro
        outro_path = str(self.output_dir / "step_outro.mp3")
        if self._tts("अभ्यास ज़रूर करें। धन्यवाद!", outro_path):
            audio_parts.append(outro_path)

        return audio_parts

    def generate_lesson_audio(self, topic, lesson_text):
        """Fallback: generate audio from raw topic text."""
        os.makedirs(self.output_dir, exist_ok=True)
        clean_text = self._prepare_text(lesson_text)

        intro = f"नमस्ते! आज हम सीखेंगे: {topic.get('chapter', 'Lesson')}"
        outro = "अभ्यास करें। धन्यवाद!"

        audio_parts = []

        intro_path = str(self.output_dir / "intro.mp3")
        if self._tts(intro, intro_path):
            audio_parts.append(intro_path)

        main_path = str(self.output_dir / "main.mp3")
        if self._tts(clean_text, main_path):
            audio_parts.append(main_path)

        outro_path = str(self.output_dir / "outro.mp3")
        if self._tts(outro, outro_path):
            audio_parts.append(outro_path)

        return audio_parts

    def _prepare_text(self, text):
        """Clean text for TTS."""
        text = text.replace('`', '').replace('|', ' ')
        text = text.replace('\\n', ' ').replace('\n', ' ')
        if len(text) > 5000:
            text = text[:5000]
        return text


if __name__ == "__main__":
    engine = AudioEngine()
    narrations = [
        "चलो तीन और दो को जोड़ते हैं। तीन गेंदें लो, फिर दो और गेंदें मिलाओ।",
        "कुल पाँच गेंदें हो गईं। तीन प्लस दो बराबर पाँच।",
    ]
    audios = engine.generate_step_audio(narrations)
    print(f"Generated {len(audios)} audio files: {audios}")
