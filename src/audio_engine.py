import os
import asyncio
import random
from pathlib import Path


class AudioEngine:
    def __init__(self, output_dir="temp_audio"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # ElevenLabs config — human-like Hindi voice
        self.elevenlabs_key = os.environ.get('ELEVENLABS_API_KEY', '')
        self.elevenlabs_voice_id = '21m00Tcm4TlvDq8ikWAM'  # Rachel (natural female)
        self.elevenlabs_url = 'https://api.elevenlabs.io/v1/text-to-speech'

        # edge-tts fallback
        self.edge_voice = 'hi-IN-SwaraNeural'
        self.edge_voice_male = 'hi-IN-MadhurNeural'

        # Track which engine we're using
        self._engine = None

    def _detect_engine(self):
        """Detect available TTS engine at runtime."""
        if self._engine is not None:
            return self._engine

        if self.elevenlabs_key:
            self._engine = 'elevenlabs'
            print("  TTS Engine: ElevenLabs (human-like voice)")
        else:
            self._engine = 'edge-tts'
            print("  TTS Engine: edge-tts (fallback)")
        return self._engine

    async def _tts_elevenlabs(self, text, output_path):
        """Generate TTS using ElevenLabs API (human-like voice)."""
        import requests

        headers = {
            'Accept': 'audio/mpeg',
            'xi-api-key': self.elevenlabs_key,
            'Content-Type': 'application/json',
        }
        data = {
            'text': text,
            'model_id': 'eleven_multilingual_v2',
            'voice_settings': {
                'stability': 0.5,
                'similarity_boost': 0.75,
                'style': 0.4,
                'use_speaker_boost': True
            }
        }
        try:
            url = f"{self.elevenlabs_url}/{self.elevenlabs_voice_id}"
            response = requests.post(url, json=data, headers=headers, timeout=30)
            if response.status_code == 200:
                with open(output_path, 'wb') as f:
                    f.write(response.content)
                return os.path.exists(output_path) and os.path.getsize(output_path) > 100
            else:
                print(f"  ElevenLabs error {response.status_code}: {response.text[:200]}")
                return False
        except Exception as e:
            print(f"  ElevenLabs error: {e}")
            return False

    async def _tts_edge(self, text, output_path):
        """Generate TTS using edge-tts (free fallback)."""
        import edge_tts

        try:
            communicate = edge_tts.Communicate(text, self.edge_voice)
            await communicate.save(output_path)
            return os.path.exists(output_path) and os.path.getsize(output_path) > 100
        except Exception as e:
            print(f"  edge-tts error: {e}")
            return False

    async def _tts(self, text, output_path):
        """Generate TTS with ElevenLabs first, edge-tts fallback."""
        engine = self._detect_engine()

        if engine == 'elevenlabs':
            success = await self._tts_elevenlabs(text, output_path)
            if success:
                return True
            print("  ElevenLabs failed, falling back to edge-tts...")
            return await self._tts_edge(text, output_path)
        else:
            return await self._tts_edge(text, output_path)

    async def generate_step_audio(self, narrations):
        """Generate one TTS clip per narration line (synced with visual steps).
        narrations: list of Hindi strings, one per step.
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
        """Fallback: generate audio from topic data when narrations are unavailable.
        Builds a proper Hindi teaching script from topic + subtopics.
        """
        os.makedirs(self.output_dir, exist_ok=True)

        topic_name = topic.get('topic', lesson_text or 'Lesson')
        subtopics = topic.get('subtopics', [])
        chapter = topic.get('chapter', 'Chapter')
        class_num = topic.get('class', 6)

        audio_parts = []

        # Random intro — so every video sounds different
        intro_variants = [
            f"नमस्ते बच्चों! आज हम \"{topic_name}\" सीखेंगे। यह कक्षा {class_num} का {chapter} है। ध्यान से देखो!",
            f"हेलो बच्चों! तैयार हो? आज का टॉपिक है \"{topic_name}\"। बहुत मज़ेदार है, चलो शुरू करते हैं!",
            f"बच्चों, आज हम \"{topic_name}\" सीखेंगे। कक्षा {class_num} के लिए बहुत ज़रूरी है। ध्यान दो!",
            f"आज का lesson है \"{topic_name}\"! बहुत आसान है, बस मेरे साथ चलो!",
            f"तैयार हो जाओ! \"{topic_name}\" शुरू करते हैं। बहुत interesting है!",
        ]
        intro = random.choice(intro_variants)
        intro_path = str(self.output_dir / "intro.mp3")
        if await self._tts(intro, intro_path):
            audio_parts.append(intro_path)

        # Random connectors for subtopic steps
        connectors = [
            "अब समझते हैं:", "चलो अब देखते हैं:", "अगला topic है:",
            "अब बात करते हैं:", "इसके बाद देखो:", "अब आता है:",
        ]

        # Generate teaching narrations from subtopics
        if subtopics:
            for i, sub in enumerate(subtopics[:5]):
                connector = random.choice(connectors)
                step_text = f"{connector} {sub}। {self._subtopic_hint(sub)}"
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
            f"बहुत अच्छे! \"{topic_name}\" समझ आ गया होगा। अभ्यास ज़रूर करो। धन्यवाद!",
            f"वाह बच्चों! \"{topic_name}\" बहुत अच्छे से सीखा। अब खुद practice करो!",
            f"शाबाश! \"{topic_name}\" हो गया। रोज़ अभ्यास करोगे तो master बन जाओगे!",
            f"great job! \"{topic_name}\" आ गया। homework मत भूलना! अगले lesson में मिलते हैं!",
        ]
        outro = random.choice(outro_variants)
        outro_path = str(self.output_dir / "outro.mp3")
        if await self._tts(outro, outro_path):
            audio_parts.append(outro_path)

        return audio_parts

    @staticmethod
    def _subtopic_hint(sub):
        """Generate a short Hindi teaching hint for a subtopic."""
        sub_lower = sub.lower()
        if any(k in sub_lower for k in ['example', 'problem', 'practice']):
            return "उदाहरण देखो और खुद कोशिश करो।"
        if any(k in sub_lower for k in ['definition', 'what is', 'basics', 'introduction']):
            return "पहले बेसिक समझो, फिर आगे बढ़ेंगे।"
        if any(k in sub_lower for k in ['property', 'properties', 'rule']):
            return "इसके नियम याद रखो, बहुत ज़रूरी हैं।"
        if any(k in sub_lower for k in ['formula', 'equation']):
            return "यह फ़ॉर्मूला याद रखो।"
        return "ध्यान से देखो, बहुत आसान है।"

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
        "चलो तीन और दो को जोड़ते हैं। तीन गेंदें लो, फिर दो और गेंदें मिलाओ।",
        "कुल पाँच गेंदें हो गईं। तीन प्लस दो बराबर पाँच।",
    ]
    audios = await engine.generate_step_audio(narrations)
    print(f"Generated {len(audios)} audio files: {audios}")

if __name__ == "__main__":
    asyncio.run(_test())
