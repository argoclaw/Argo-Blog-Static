#!/usr/bin/env python3
"""
Import historical videos from yt-summarizer cache to YT Viewer.
Fetches metadata from YouTube and adds to videos.json.
"""

import json
import subprocess
import os
import time
from pathlib import Path

CACHE_DIR = Path("/home/opc/.openclaw/workspace/skills/yt-summarizer/cache")
TRANSCRIPT_DIR = CACHE_DIR / "transcript"
DATA_FILE = Path("/home/opc/.openclaw/workspace/yt-viewer/data/videos.json")
COOKIES = "/home/opc/.openclaw/workspace/skills/yt-summarizer/cookies/youtube.txt"

def get_video_metadata(video_id):
    """Fetch video metadata from YouTube using yt-dlp"""
    try:
        result = subprocess.run(
            ["yt-dlp", "--cookies", COOKIES, "-j", f"https://youtu.be/{video_id}"],
            capture_output=True,
            text=True,
            timeout=30
        )
        if result.returncode == 0:
            data = json.loads(result.stdout)
            return {
                "title": data.get("title", "Unknown"),
                "channel": data.get("channel", data.get("uploader", "Unknown")),
                "duration": data.get("duration", 0),
                "view_count": data.get("view_count", 0),
                "like_count": data.get("like_count", 0)
            }
    except Exception as e:
        print(f"  Error fetching {video_id}: {e}")
    return None

def main():
    # Load existing data
    if DATA_FILE.exists():
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
    else:
        data = {"videos": [], "updated_at": None}
    
    existing_ids = {v["id"] for v in data["videos"]}
    
    # Find all video IDs in transcript cache
    video_ids = []
    for item in TRANSCRIPT_DIR.iterdir():
        if item.is_dir() and item.name != ".gitkeep" and len(item.name) == 11:
            # Check if has transcript.txt
            if (item / "transcript.txt").exists():
                video_ids.append(item.name)
    
    print(f"Found {len(video_ids)} videos in cache")
    print(f"Already in database: {len(existing_ids)}")
    
    new_videos = [vid for vid in video_ids if vid not in existing_ids]
    print(f"New videos to import: {len(new_videos)}")
    
    for i, video_id in enumerate(new_videos):
        print(f"\n[{i+1}/{len(new_videos)}] Processing {video_id}...")
        
        metadata = get_video_metadata(video_id)
        if not metadata:
            print(f"  Skipping - couldn't fetch metadata")
            continue
        
        # Get file modification time as analyzed_at
        transcript_file = TRANSCRIPT_DIR / video_id / "transcript.txt"
        mtime = transcript_file.stat().st_mtime * 1000
        
        video_entry = {
            "id": video_id,
            "title": metadata["title"],
            "channel": metadata["channel"],
            "duration": metadata["duration"],
            "view_count": metadata["view_count"],
            "like_count": metadata["like_count"],
            "insights_count": 0,
            "analyzed_at": int(mtime)
        }
        
        data["videos"].append(video_entry)
        print(f"  Added: {metadata['title'][:50]}...")
        
        # Rate limit
        time.sleep(1)
    
    data["updated_at"] = int(time.time() * 1000)
    
    # Save
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"\nDone! Total videos in database: {len(data['videos'])}")

if __name__ == "__main__":
    main()
