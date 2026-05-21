import os
import asyncio
from pathlib import Path


class AudioEngine:
    def __init__(self, output_dir="temp_audio"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.voice = "hi-IN-MadhurNeural"  # Female/Male Hindi voice
        self.prefer_elevenlabs = os.environ.get("PREFER_ELEVENLABS", "false").lower() == "true"

    async def generate_audio(self, text, output_path):
        """Generate audio using edge-tts or ElevenLabs API based on configuration."""
        if self.prefer_elevenlabs:
            print("    🎙️ [Config] Prioritizing ElevenLabs API...")
            if await self._generate_elevenlabs(text, output_path):
                return True
            print("    ⚠️ ElevenLabs failed, falling back to edge-tts...")
            return await self._generate_edgetts(text, output_path)
        else:
            if await self._generate_edgetts(text, output_path):
                return True
            print("    ⚠️ edge-tts failed, falling back to ElevenLabs...")
            return await self._generate_elevenlabs(text, output_path)

    async def _generate_edgetts(self, text, output_path):
        """Generate audio using edge-tts."""
        try:
            import edge_tts
            print(f"    🎙️ Generating voice via edge-tts ({self.voice})...")
            communicate = edge_tts.Communicate(text, self.voice)
            await communicate.save(output_path)
            if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
                return True
        except Exception as e:
            print(f"    ❌ edge-tts failed: {e}")
        return False

    async def _generate_elevenlabs(self, text, output_path):
        """Generate audio using ElevenLabs API."""
        import requests
        
        url = "https://api.elevenlabs.io/v1/text-to-speech/EXAVITQu4vr4xnSDxMaL"  # Bella voice (female)
        eleven_key = os.environ.get("ELEVENLABS_API_KEY") or "1b5004d419d62f06736e976f09bf4bc1cbd44b72bd92f4cb8387aa0602bbd504"
        
        headers = {
            "Accept": "audio/mpeg",
            "Content-Type": "application/json",
            "xi-api-key": eleven_key
        }
        
        data = {
            "text": text,
            "model_id": "eleven_multilingual_v2",
            "voice_settings": {
                "stability": 0.5,
                "similarity_boost": 0.75
            }
        }

        try:
            print("    🎙️ Generating voice via ElevenLabs...")
            response = requests.post(url, json=data, headers=headers)
            
            if response.status_code == 200:
                with open(output_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=1024):
                        if chunk:
                            f.write(chunk)
                return os.path.exists(output_path)
            else:
                print(f"    ❌ ElevenLabs failed: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            print(f"    ❌ ElevenLabs Exception: {e}")
            return False

    async def generate_lesson_audio(self, topic, lesson_text=None):
        """Generate full lesson audio split by steps from topic content."""
        os.makedirs(self.output_dir, exist_ok=True)

        # Clear existing mp3 files in the directory to prevent stale/double audio mixing
        for old_file in self.output_dir.glob("*.mp3"):
            try:
                old_file.unlink()
            except:
                pass

        # Extract split scripts with robust fallbacks
        intro = self._prepare_text(topic.get('intro_script', f"Namaste dosto! Aaj hum seekhenge {topic.get('formula_title', 'ek concept')}."))
        step1 = self._prepare_text(topic.get('step1_script', f"Step 1 me screen par {topic.get('step1_desc', 'pehla step')} dekhiye."))
        step2 = self._prepare_text(topic.get('step2_script', f"Step 2 me screen par {topic.get('step2_desc', 'dusra step')} dekhiye."))
        step3 = self._prepare_text(topic.get('step3_script', f"Aur ab final assembly! Jaise hi hum mathematically combine karte hain toh {topic.get('step3_desc', 'final formula')} prove hota hai."))
        outro = self._prepare_text(topic.get('outro_script', "Aise hi aur amazing lessons ke liye, video ko like aur share zaroor karein. Dhanyawad!"))

        audio_parts = []

        # Generate intro
        intro_path = self.output_dir / "intro.mp3"
        print(f"   Generating Intro Audio: '{intro[:40]}...'")
        if await self.generate_audio(intro, str(intro_path)):
            audio_parts.append(str(intro_path))

        # Generate Step 1
        step1_path = self.output_dir / "step1.mp3"
        print(f"   Generating Step 1 Audio: '{step1[:40]}...'")
        if await self.generate_audio(step1, str(step1_path)):
            audio_parts.append(str(step1_path))

        # Generate Step 2
        step2_path = self.output_dir / "step2.mp3"
        print(f"   Generating Step 2 Audio: '{step2[:40]}...'")
        if await self.generate_audio(step2, str(step2_path)):
            audio_parts.append(str(step2_path))

        # Generate Step 3
        step3_path = self.output_dir / "step3.mp3"
        print(f"   Generating Step 3 Audio: '{step3[:40]}...'")
        if await self.generate_audio(step3, str(step3_path)):
            audio_parts.append(str(step3_path))

        # Generate Outro
        outro_path = self.output_dir / "outro.mp3"
        print(f"   Generating Outro Audio: '{outro[:40]}...'")
        if await self.generate_audio(outro, str(outro_path)):
            audio_parts.append(str(outro_path))

        return audio_parts

    def _prepare_text(self, text):
        """Clean Hinglish text for TTS."""
        if not text:
            return ""
        # Remove special characters that might cause issues
        text = text.replace('`', '').replace('|', ' ')
        text = text.replace('\\n', ' ').replace('\n', ' ')
        # Limit text length for API
        if len(text) > 2000:
            text = text[:2000]
        return text


if __name__ == "__main__":
    async def test():
        engine = AudioEngine()
        topic = {
            'formula_title': 'Unit Circle Identity',
            'intro_script': 'Namaste dosto! Aaj hum seekhenge trigonometric identities.',
            'step1_script': 'Step 1 me chaliye cos square vector ko represent karte hain.',
            'step2_script': 'Step 2 me vertical line sin square component ko represent karti hai.',
            'step3_script': 'Assembly me in dono ko plus karke unit circle prove karte hain.',
            'outro_script': 'Thanks for watching, see you again!'
        }
        audios = await engine.generate_lesson_audio(topic)
        print(f"Generated {len(audios)} audio files")
        for a in audios:
            print(f"  - {a}")

    asyncio.run(test())