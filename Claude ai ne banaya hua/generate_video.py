"""
generate_video.py
─────────────────
Main orchestrator for the faceless YouTube channel video pipeline.

Flow:
  1. Generate script with Groq (free LLaMA) — or use topic as-is
  2. Generate voiceover with Edge TTS (free)
  3. Fetch stock footage from Pexels (free)
  4. Assemble: footage + voiceover → raw video
  5. Generate captions with Whisper tiny (free, CPU)
  6. Burn captions → final_video.mp4
"""

import os
import sys
import json
import re
import subprocess
import time
from pathlib import Path

# Make sure scripts/ is in path
sys.path.insert(0, str(Path(__file__).parent))

from tts_voiceover import generate_voiceover
from fetch_footage import fetch_pexels_videos
from add_captions import transcribe_and_generate_srt, burn_captions


# ─── Script Generation ────────────────────────────────────────────────────────

GROQ_SYSTEM_PROMPT = """You are an expert YouTube script writer for a faceless channel.
Write a natural, engaging script that takes 90–120 seconds to read aloud.
Rules:
- Conversational tone, like you're talking to a friend
- No stage directions, no [PAUSE], no emojis
- No "Hey guys" or "smash that like button" — just pure content
- Start with a hook sentence that grabs attention immediately
- Pure spoken text only — what the narrator says word for word"""


def generate_script(topic: str) -> str:
    groq_key = os.environ.get("GROQ_API_KEY", "")

    if not groq_key:
        print("ℹ️  No GROQ_API_KEY found — using topic/text directly as script")
        return topic

    print("🤖 Generating script with Groq (llama-3.1-8b-instant)...")

    import requests

    for attempt in range(3):
        try:
            resp = requests.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {groq_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": "llama-3.3-70b-versatile",   # free tier model
                    "messages": [
                        {"role": "system", "content": GROQ_SYSTEM_PROMPT},
                        {"role": "user", "content": f"Write a faceless YouTube video script about: {topic}"},
                    ],
                    "max_tokens": 700,
                    "temperature": 0.75,
                },
                timeout=30,
            )
            resp.raise_for_status()
            script = resp.json()["choices"][0]["message"]["content"].strip()
            print(f"✅ Script generated ({len(script.split())} words)")
            return script

        except Exception as e:
            print(f"⚠️  Groq attempt {attempt+1}/3 failed: {e}")
            if attempt < 2:
                time.sleep(3)

    print("⚠️  Groq failed — falling back to topic as script")
    return topic


# ─── Keyword Extraction ────────────────────────────────────────────────────────

TOPIC_FOOTAGE_MAP = {
    "space":       ["space galaxy stars", "milky way nebula", "astronaut rocket", "earth orbit nasa"],
    "money":       ["money success business", "stock market finance", "luxury lifestyle wealth", "entrepreneur office"],
    "health":      ["healthy food nutrition", "exercise fitness gym", "meditation yoga calm", "doctor healthcare"],
    "history":     ["ancient ruins historical", "medieval castle", "old city architecture", "museum artifact"],
    "technology":  ["technology innovation future", "coding computer programming", "artificial intelligence robot", "data center server"],
    "nature":      ["nature landscape forest", "ocean waves beach", "mountain sunrise hiking", "wildlife animals"],
    "food":        ["cooking kitchen chef", "restaurant dining food", "fresh ingredients market", "gourmet meal"],
    "travel":      ["travel destination city", "airport plane flight", "beach vacation resort", "backpacking adventure"],
    "psychology":  ["people thinking minds", "human behavior emotion", "brain neuroscience", "therapy wellness mental"],
    "science":     ["laboratory research science", "experiment discovery chemistry", "biology microscope cells", "physics quantum"],
    "motivation":  ["success achievement goals", "sunrise morning inspiration", "running sports determination", "team collaboration"],
    "animals":     ["wildlife safari nature", "ocean marine sea life", "birds flying nature", "cute animals pets"],
    "ai":          ["artificial intelligence technology", "robot future automation", "data computing digital", "neural network"],
    "finance":     ["stock market trading", "cryptocurrency bitcoin", "investment portfolio", "financial planning wealth"],
}


def extract_footage_keywords(script: str, extra_keywords: str = "") -> list:
    keywords = []

    # User-provided keywords take priority
    if extra_keywords:
        keywords.extend([k.strip() for k in extra_keywords.split(",") if k.strip()])

    # Match script against topic map
    script_lower = script.lower()
    for topic_key, footage_list in TOPIC_FOOTAGE_MAP.items():
        if topic_key in script_lower:
            keywords.extend(footage_list[:2])

    # Extract specific nouns from script as fallback keywords
    nouns = re.findall(r'\b[A-Za-z]{6,}\b', script)
    unique_nouns = list(dict.fromkeys([w.lower() for w in nouns]))
    # Pick every 3rd word to get a varied sample
    keywords.extend(unique_nouns[::3][:4])

    # Deduplicate while keeping order
    seen = set()
    unique_keywords = []
    for k in keywords:
        if k not in seen:
            seen.add(k)
            unique_keywords.append(k)

    # Always have at least some fallback
    if not unique_keywords:
        unique_keywords = ["inspiring nature landscape", "city life urban", "technology future", "people success"]

    final = unique_keywords[:8]
    print(f"🔍 Footage keywords: {final}")
    return final


# ─── Video Assembly ────────────────────────────────────────────────────────────

def get_duration(file_path: str) -> float:
    """Get media file duration in seconds using ffprobe."""
    result = subprocess.run(
        ["ffprobe", "-v", "quiet", "-print_format", "json", "-show_format", file_path],
        capture_output=True, text=True
    )
    data = json.loads(result.stdout)
    return float(data["format"]["duration"])


def assemble_video(clips: list, audio_path: str, audio_duration: float) -> str:
    """
    Assemble footage clips looped to match audio duration, then mix with voiceover.
    Output: 1920×1080 H.264, AAC audio, YouTube-ready.
    """
    os.makedirs("output", exist_ok=True)
    concat_path = "output/concat.txt"

    # Build concat list — loop clips until we have enough footage
    total_footage = 0.0
    clip_idx = 0
    with open(concat_path, "w") as f:
        while total_footage < audio_duration + 10:  # +10s buffer
            clip = clips[clip_idx % len(clips)]
            abs_path = os.path.abspath(clip)
            f.write(f"file '{abs_path}'\n")
            try:
                clip_dur = get_duration(abs_path)
            except Exception:
                clip_dur = 5.0
            total_footage += clip_dur
            clip_idx += 1

    assembled = "output/assembled.mp4"
    print("🔧 Assembling footage + voiceover...")

    cmd = [
        "ffmpeg", "-y",
        "-f", "concat", "-safe", "0", "-i", concat_path,
        "-i", audio_path,
        "-map", "0:v:0",
        "-map", "1:a:0",
        # Video: normalize to 1920×1080, 30fps
        "-vf", (
            "scale=1920:1080:force_original_aspect_ratio=increase,"
            "crop=1920:1080,"
            "setsar=1,"
            "fps=30"
        ),
        "-c:v", "libx264", "-preset", "fast", "-crf", "23",
        "-c:a", "aac", "-b:a", "128k",
        "-t", str(audio_duration),
        "-movflags", "+faststart",
        assembled,
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"❌ Assembly error:\n{result.stderr[-2000:]}")
        raise RuntimeError("Video assembly failed")

    print(f"✅ Assembled: {assembled}")
    return assembled


# ─── Main Pipeline ─────────────────────────────────────────────────────────────

def main():
    print("=" * 55)
    print("🎬  FACELESS YOUTUBE VIDEO GENERATOR")
    print("    100% Free Stack: Groq + EdgeTTS + Pexels + Whisper")
    print("=" * 55)

    topic    = os.environ.get("TOPIC", "10 Shocking Facts About the Human Brain")
    voice    = os.environ.get("VOICE", "en-US-AriaNeural")
    keywords = os.environ.get("KEYWORDS", "")

    os.makedirs("output", exist_ok=True)

    # Step 1: Script
    print(f"\n📝 STEP 1/5 — Script generation")
    print(f"   Topic: {topic}")
    script = generate_script(topic)

    with open("output/script.txt", "w", encoding="utf-8") as f:
        f.write(script)
    print(f"   Saved: output/script.txt ({len(script.split())} words)")

    # Step 2: Voiceover
    print(f"\n🎙️  STEP 2/5 — Voiceover generation (voice: {voice})")
    audio_path = "output/voiceover.mp3"
    generate_voiceover(script, voice, audio_path)

    audio_duration = get_duration(audio_path)
    print(f"   Audio duration: {audio_duration:.1f}s")

    # Step 3: Stock footage
    print(f"\n🎥  STEP 3/5 — Fetching stock footage from Pexels")
    footage_keywords = extract_footage_keywords(script, keywords)
    clips = fetch_pexels_videos(footage_keywords, audio_duration)

    if not clips:
        print("❌ No footage downloaded. Verify PEXELS_API_KEY secret is set correctly.")
        sys.exit(1)

    # Step 4: Assemble
    print(f"\n🔧  STEP 4/5 — Assembling video")
    assembled_path = assemble_video(clips, audio_path, audio_duration)

    # Step 5: Captions
    print(f"\n📝  STEP 5/5 — Generating & burning captions (Whisper tiny)")
    srt_path = transcribe_and_generate_srt(audio_path)
    final_path = "output/final_video.mp4"
    burn_captions(assembled_path, srt_path, final_path)

    # Summary
    size_mb = os.path.getsize(final_path) / 1024 / 1024
    duration = get_duration(final_path)

    print("\n" + "=" * 55)
    print("✅  VIDEO COMPLETE!")
    print(f"   📁 File:     output/final_video.mp4")
    print(f"   📏 Size:     {size_mb:.1f} MB")
    print(f"   ⏱️  Duration: {duration:.1f}s ({duration/60:.1f} min)")
    print(f"   📝 Script:   output/script.txt")
    print(f"   💬 Captions: output/voiceover.srt")
    print("=" * 55)


if __name__ == "__main__":
    main()
