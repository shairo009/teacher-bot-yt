import asyncio
import edge_tts
from pathlib import Path

async def inspect_stream():
    q_narration = "क्या आप जानते हैं"
    communicate = edge_tts.Communicate(q_narration, 'hi-IN-MadhurNeural')
    async for chunk in communicate.stream():
        print("Chunk:", chunk)

if __name__ == "__main__":
    asyncio.run(inspect_stream())
