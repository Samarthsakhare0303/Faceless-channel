"""
add_captions.py
───────────────
Generate captions from audio using OpenAI Whisper (tiny model, runs free on CPU)
and burn them into video using FFmpeg.

✅ Completely free — Whisper is open source, runs on GitHub Actions CPU.
✅ Accurate enough for YouTube-quality captions.
✅ Captions are styled: white text, black outline, bottom-center.
"""

import os
import subprocess
from faster_whisper import WhisperModel


def _seconds_to_srt_time(seconds: float) -> str:
    """Convert float seconds → SRT timestamp format (HH:MM:SS,mmm)."""
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    ms = int((seconds % 1) * 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def transcribe_and_generate_srt(
    audio_path: str,
    srt_path: str = "output/voiceover.srt",
    model_size: str = "tiny",
) -> str:
    """
    Transcribe audio with Whisper and write an SRT subtitle file.

    Args:
        audio_path: Path to MP3/WAV audio file
        srt_path:   Where to save the SRT file
        model_size: 'tiny' (fastest, ~75 MB), 'base', 'small', 'medium'

    Returns:
        Path to the generated SRT file.
    """
    print(f"🧠 Loading Whisper model: {model_size} (CPU mode)...")
    model = WhisperModel(model_size, device="cpu", compute_type="int8")

    print(f"🎤 Transcribing: {audio_path}")
    segments, info = model.transcribe(
        audio_path,
        beam_size=5,
        language="en",       # set to None for auto-detect
        condition_on_previous_text=True,
    )
    print(f"   Detected language: {info.language} ({info.language_probability:.0%})")

    os.makedirs(os.path.dirname(srt_path), exist_ok=True)

    srt_lines = []
    for i, seg in enumerate(segments, 1):
        start = _seconds_to_srt_time(seg.start)
        end   = _seconds_to_srt_time(seg.end)
        text  = seg.text.strip()
        srt_lines.append(f"{i}\n{start} --> {end}\n{text}\n")

    with open(srt_path, "w", encoding="utf-8") as f:
        f.write("\n".join(srt_lines))

    print(f"✅ SRT captions saved: {srt_path} ({len(srt_lines)} segments)")
    return srt_path


def burn_captions(
    video_path: str,
    srt_path: str,
    output_path: str = "output/final_video.mp4",
) -> str:
    """
    Burn SRT captions into video using FFmpeg's subtitles filter.
    Style: white text, black outline, 18pt Arial, bottom-center.

    Args:
        video_path:  Input video (no captions)
        srt_path:    SRT subtitle file
        output_path: Where to save captioned video

    Returns:
        Path to the output video.
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # FFmpeg subtitles filter style
    style = (
        "FontName=Open Sans,"
        "FontSize=18,"
        "PrimaryColour=&H00FFFFFF,"   # white text
        "OutlineColour=&H00000000,"   # black outline
        "BackColour=&H80000000,"      # semi-transparent background
        "Outline=2,"
        "Shadow=1,"
        "Alignment=2,"                # bottom center
        "MarginV=40"                  # margin from bottom
    )

    # Escape the SRT path for FFmpeg filter (handle colons on Windows paths)
    srt_escaped = os.path.abspath(srt_path).replace("\\", "/").replace(":", "\\:")

    cmd = [
        "ffmpeg", "-y",
        "-i", video_path,
        "-vf", f"subtitles={srt_escaped}:force_style='{style}'",
        "-c:v", "libx264", "-preset", "fast", "-crf", "22",
        "-c:a", "copy",
        "-movflags", "+faststart",
        output_path,
    ]

    print(f"🔥 Burning captions: {video_path} → {output_path}")
    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        print(f"❌ FFmpeg caption error:\n{result.stderr[-2000:]}")
        # If caption burning fails, just copy the video without captions
        print("⚠️  Falling back: copying video without burned captions...")
        subprocess.run(["cp", video_path, output_path], check=True)
    else:
        size_mb = os.path.getsize(output_path) / 1024 / 1024
        print(f"✅ Final video with captions: {output_path} ({size_mb:.1f} MB)")

    return output_path
