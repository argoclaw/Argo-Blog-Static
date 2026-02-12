#!/usr/bin/env python3
"""
Record analyzed video metadata + summary to the YT Viewer data store.
Usage: 
  python3 record_video.py <video_id> <title> <channel> <duration> [view_count] [like_count] [insights_count] [--summary <json_file>]
  
Or pipe summary JSON via stdin:
  echo '{"tldr": "...", "ideas": [...]}' | python3 record_video.py <video_id> <title> <channel> <duration> --summary -
"""

import json
import sys
import time
import argparse
from pathlib import Path

DATA_FILE = Path("/home/opc/.openclaw/workspace/yt-viewer/data/videos.json")

# Required fields for a valid summary
REQUIRED_SUMMARY_FIELDS = {"tldr", "ideas", "insights"}

def validate_summary(summary: dict, video_id: str) -> dict:
    """
    Validate and normalize summary structure.
    Handles common issues like nested summary objects and missing fields.
    Returns normalized summary or raises ValueError.
    """
    if not isinstance(summary, dict):
        raise ValueError(f"Summary must be a dict, got {type(summary).__name__}")
    
    # Handle nested summary (子代理有时会把整个JSON存进summary字段)
    if "summary" in summary and isinstance(summary["summary"], dict):
        inner = summary["summary"]
        # Check if inner has the actual content
        if any(field in inner for field in REQUIRED_SUMMARY_FIELDS):
            # Flatten: merge inner summary into outer, preserving metadata
            metadata_fields = {"status", "video_id", "title", "channel", "duration", "views", "likes"}
            result = {k: v for k, v in summary.items() if k in metadata_fields}
            result.update(inner)
            summary = result
            print(f"[WARN] Flattened nested summary structure for {video_id}", file=sys.stderr)
    
    # Check required fields
    missing = REQUIRED_SUMMARY_FIELDS - set(summary.keys())
    if missing:
        raise ValueError(f"Summary missing required fields: {missing}")
    
    # Validate field types
    if not isinstance(summary.get("tldr"), str) or not summary["tldr"].strip():
        raise ValueError("tldr must be a non-empty string")
    
    if not isinstance(summary.get("ideas"), list):
        raise ValueError("ideas must be a list")
    
    if not isinstance(summary.get("insights"), list):
        raise ValueError("insights must be a list")
    
    # Ensure videoId is set
    summary["videoId"] = video_id
    
    return summary

def main():
    parser = argparse.ArgumentParser(description='Record video to YT Viewer')
    parser.add_argument('video_id', help='YouTube video ID')
    parser.add_argument('title', help='Video title')
    parser.add_argument('channel', help='Channel name')
    parser.add_argument('duration', type=int, help='Duration in seconds')
    parser.add_argument('view_count', type=int, nargs='?', default=0)
    parser.add_argument('like_count', type=int, nargs='?', default=0)
    parser.add_argument('insights_count', type=int, nargs='?', default=0)
    parser.add_argument('--summary', '-s', help='Summary JSON file or - for stdin')
    parser.add_argument('--thumbnail', '-t', help='Thumbnail URL')
    parser.add_argument('--source-url', help='Original source URL (for non-YouTube videos)')
    
    args = parser.parse_args()
    
    # Load existing data
    if DATA_FILE.exists():
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
    else:
        data = {"videos": [], "updated_at": None}
    
    # Load summary if provided
    summary = None
    if args.summary:
        try:
            if args.summary == '-':
                raw_summary = json.load(sys.stdin)
            else:
                with open(args.summary, 'r', encoding='utf-8') as f:
                    raw_summary = json.load(f)
            
            if raw_summary:
                summary = validate_summary(raw_summary, args.video_id)
                print(f"Summary validated: tldr={len(summary['tldr'])} chars, "
                      f"ideas={len(summary['ideas'])}, insights={len(summary['insights'])}")
        except json.JSONDecodeError as e:
            print(f"ERROR: Invalid JSON in summary file: {e}", file=sys.stderr)
            sys.exit(1)
        except ValueError as e:
            print(f"ERROR: Summary validation failed: {e}", file=sys.stderr)
            sys.exit(1)
    
    # Build video entry
    video_entry = {
        "id": args.video_id,
        "title": args.title,
        "channel": args.channel,
        "duration": args.duration,
        "view_count": args.view_count,
        "like_count": args.like_count,
        "insights_count": args.insights_count,
        "analyzed_at": int(time.time() * 1000)
    }
    
    if args.thumbnail:
        video_entry["thumbnail"] = args.thumbnail
    
    if args.source_url:
        video_entry["source_url"] = args.source_url
    
    if summary:
        video_entry["summary"] = summary
    
    # Check if video already exists
    existing_idx = None
    for i, v in enumerate(data["videos"]):
        if v["id"] == args.video_id:
            existing_idx = i
            break
    
    if existing_idx is not None:
        # Update existing entry, preserve summary if not provided
        if not summary and "summary" in data["videos"][existing_idx]:
            video_entry["summary"] = data["videos"][existing_idx]["summary"]
        data["videos"][existing_idx] = video_entry
        print(f"Updated existing record for {args.video_id}")
    else:
        data["videos"].append(video_entry)
        print(f"Added new record for {args.video_id}")
    
    data["updated_at"] = int(time.time() * 1000)
    
    # Save data
    DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"Data saved to {DATA_FILE}")

if __name__ == "__main__":
    main()
