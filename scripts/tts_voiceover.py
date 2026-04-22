"""
tts_voiceover.py
────────────────
Generate voiceover audio using Microsoft Edge TTS.
✅ Completely free — no API key, no account needed.
✅ 300+ natural-sounding voices across 50+ languages.

Popular English voices:
  en-US-AriaNeural      → Warm female (great for general content)
  en-US-GuyNeural       → Deep male (great for serious/news content)
  en-US-JennyNeural     → Friendly female
  en-GB-SoniaNeural     → British female
  en-AU-NatashaNeural   → Australian female
  en-IN-NeerjaNeural    → Indian female

Run `edge-tts --list-voices` for the full list.
"""

import asyncio
import os
import edge_tts


async def _speak(text: str, voice: str, output_path: str) -> None:
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(output_path)


def generate_voiceover(
    text: str,
    voice: str = "en-US-AriaNeural",
    output_path: str = "output/voiceover.mp3",
) -> str:
    """
    Generate voiceover MP3 from text.
    Returns the path to the generated file.
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    asyncio.run(_speak(text, voice, output_path))

    size_kb = os.path.getsize(output_path) / 1024
    print(f"✅ Voiceover generated: {output_path} ({size_kb:.0f} KB) | voice: {voice}")
    return output_path


if __name__ == "__main__":
    # Quick test
    generate_voiceover(
        "Welcome to our channel. Today we are going to explore ten amazing facts "
        "about the universe that will completely change how you see the world.",
        voice="en-US-AriaNeural",
        output_path="output/test_voiceover.mp3",
    )
