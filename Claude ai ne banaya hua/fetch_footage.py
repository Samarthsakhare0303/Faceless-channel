"""
fetch_footage.py
────────────────
Download free stock video clips from Pexels API.
✅ Free: 200 req/hr, 20,000 req/month — no payment needed.
   Get your free API key at: https://www.pexels.com/api/

The downloader picks HD (1280p or 1920p) landscape clips.
Falls back to any available quality if HD isn't found.
"""

import os
import time
import requests
from typing import List

PEXELS_API_KEY = os.environ.get("PEXELS_API_KEY", "")
FOOTAGE_DIR = "output/footage"


def _get_best_file(video_files: list) -> dict | None:
    """Pick the best quality video file from Pexels response (prefer 1080p/720p)."""
    preferred_widths = [1920, 1280, 960]
    for width in preferred_widths:
        match = next((f for f in video_files if f.get("width") == width), None)
        if match:
            return match
    # Fall back to largest available
    return sorted(video_files, key=lambda f: f.get("width", 0), reverse=True)[0] if video_files else None


def _download_clip(url: str, dest_path: str) -> bool:
    """Download a single video clip with retry logic."""
    for attempt in range(3):
        try:
            resp = requests.get(url, stream=True, timeout=90)
            resp.raise_for_status()
            with open(dest_path, "wb") as f:
                for chunk in resp.iter_content(chunk_size=16384):
                    f.write(chunk)
            return True
        except Exception as e:
            print(f"  ⚠️  Download attempt {attempt+1}/3 failed: {e}")
            time.sleep(2)
    return False


def fetch_pexels_videos(keywords: List[str], target_duration: float, max_clips: int = 12) -> List[str]:
    """
    Search Pexels for videos matching each keyword and download them.

    Args:
        keywords:        List of search terms (e.g. ["space galaxy", "rocket launch"])
        target_duration: Total seconds of footage needed (we fetch slightly more)
        max_clips:       Hard cap on number of clips to download

    Returns:
        List of local file paths to downloaded clips.
    """
    if not PEXELS_API_KEY:
        raise ValueError(
            "❌ PEXELS_API_KEY is not set!\n"
            "   1. Get a free key at https://www.pexels.com/api/\n"
            "   2. Add it to GitHub Secrets as PEXELS_API_KEY"
        )

    os.makedirs(FOOTAGE_DIR, exist_ok=True)
    headers = {"Authorization": PEXELS_API_KEY}
    downloaded: List[str] = []

    for keyword in keywords:
        if len(downloaded) >= max_clips:
            break

        print(f"  🔍 Searching Pexels: '{keyword}'")
        try:
            resp = requests.get(
                "https://api.pexels.com/videos/search",
                headers=headers,
                params={
                    "query": keyword,
                    "per_page": 5,
                    "orientation": "landscape",
                    "size": "medium",         # medium = 4–10 min clips
                },
                timeout=15,
            )
            resp.raise_for_status()
        except Exception as e:
            print(f"  ⚠️  Pexels API error for '{keyword}': {e}")
            continue

        videos = resp.json().get("videos", [])
        if not videos:
            print(f"  ⚠️  No results for '{keyword}'")
            continue

        for video in videos:
            if len(downloaded) >= max_clips:
                break

            video_files = video.get("video_files", [])
            # Only landscape MP4s
            mp4_files = [f for f in video_files if f.get("file_type") == "video/mp4"]
            best = _get_best_file(mp4_files)
            if not best:
                continue

            clip_path = os.path.join(FOOTAGE_DIR, f"clip_{len(downloaded):03d}.mp4")
            print(f"  ⬇️  Downloading clip {len(downloaded)+1}: {best.get('width')}x{best.get('height')} — {keyword}")

            if _download_clip(best["link"], clip_path):
                downloaded.append(clip_path)
                print(f"  ✅  Saved: {clip_path}")
            else:
                print(f"  ❌  Failed to download clip for '{keyword}'")

        # Pexels rate limit safety: 200 req/hr → ~1 req per 18s is safe
        time.sleep(1)

    print(f"\n📦 Total clips downloaded: {len(downloaded)}")
    return downloaded


if __name__ == "__main__":
    # Quick test
    clips = fetch_pexels_videos(["space galaxy", "earth from space"], target_duration=60)
    print(clips)
