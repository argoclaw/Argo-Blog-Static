#!/usr/bin/env python3
"""
Parse existing summary files and add to videos.json
"""

import json
import re
from pathlib import Path

DATA_FILE = Path("/home/opc/.openclaw/workspace/yt-viewer/data/videos.json")
SUMMARY_DIR = Path("/home/opc/.openclaw/workspace/skills/yt-summarizer/cache/summary")

def parse_markdown_summary(content, video_id):
    """Parse markdown summary into structured JSON"""
    summary = {"videoId": video_id}
    
    # Extract SUMMARY/TLDR
    tldr_match = re.search(r'(?:^|\n)(?:>?\s*\*?\*?SUMMARY\*?\*?|# SUMMARY)\s*\n+>?\s*(.+?)(?=\n\n|\n#)', content, re.IGNORECASE | re.DOTALL)
    if tldr_match:
        summary["tldr"] = tldr_match.group(1).strip().strip('>')
    
    # Extract IDEAS
    ideas_match = re.search(r'#\s*(?:💡\s*)?IDEAS[:\s]*\n+([\s\S]+?)(?=\n#|\Z)', content, re.IGNORECASE)
    if ideas_match:
        ideas = []
        for line in ideas_match.group(1).strip().split('\n'):
            line = line.strip()
            if line.startswith(('-', '*', '•')):
                text = re.sub(r'^[-*•]\s*', '', line)
                # Extract timestamp
                ts_match = re.search(r'\[\[?(\d+):(\d+)\]?\]', text)
                if ts_match:
                    mins, secs = int(ts_match.group(1)), int(ts_match.group(2))
                    timestamp = mins * 60 + secs
                    text = re.sub(r'\s*\[\[?\d+:\d+\]?\]\([^)]+\)', '', text).strip()
                    ideas.append({"text": text, "timestamp": timestamp})
                else:
                    ideas.append({"text": text, "timestamp": None})
        summary["ideas"] = ideas[:15]  # Limit to 15
    
    # Extract INSIGHTS
    insights_match = re.search(r'#\s*(?:🧠\s*)?INSIGHTS[:\s]*\n+([\s\S]+?)(?=\n#|\Z)', content, re.IGNORECASE)
    if insights_match:
        insights = []
        for line in insights_match.group(1).strip().split('\n'):
            line = line.strip()
            if line.startswith(('-', '*', '•')):
                text = re.sub(r'^[-*•]\s*', '', line)
                text = re.sub(r'\s*\[\[?\d+:\d+\]?\]\([^)]+\)', '', text).strip()
                if text:
                    insights.append(text)
        summary["insights"] = insights[:10]
    
    # Extract QUOTES
    quotes_match = re.search(r'#\s*(?:🗣️\s*)?QUOTES[:\s]*\n+([\s\S]+?)(?=\n#|\Z)', content, re.IGNORECASE)
    if quotes_match:
        quotes = []
        for line in quotes_match.group(1).strip().split('\n'):
            line = line.strip()
            if line.startswith(('-', '*', '•')):
                text = re.sub(r'^[-*•]\s*', '', line)
                # Clean up quotes
                text = re.sub(r'\s*-\s*Speaker.*$', '', text)
                text = re.sub(r'\s*\[\d+:\d+\].*$', '', text)
                text = text.strip('"\'')
                if text:
                    quotes.append(text)
        summary["quotes"] = quotes[:5]
    
    # Extract FACTS
    facts_match = re.search(r'#\s*(?:🧪\s*)?FACTS[:\s]*\n+([\s\S]+?)(?=\n#|\Z)', content, re.IGNORECASE)
    if facts_match:
        facts = []
        for line in facts_match.group(1).strip().split('\n'):
            line = line.strip()
            if line.startswith(('-', '*', '•')):
                text = re.sub(r'^[-*•]\s*', '', line).strip()
                if text:
                    facts.append(text)
        summary["facts"] = facts[:8]
    
    # Extract TAKEAWAY
    takeaway_match = re.search(r'#\s*(?:🚀\s*)?(?:ONE[- ]SENTENCE\s*)?TAKEAWAY[:\s]*\n+(.+?)(?=\n#|\n\n|\Z)', content, re.IGNORECASE)
    if takeaway_match:
        summary["takeaway"] = takeaway_match.group(1).strip()
    
    return summary

def main():
    # Load existing data
    with open(DATA_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Map video IDs to indices
    video_map = {v["id"]: i for i, v in enumerate(data["videos"])}
    
    updated = 0
    
    # Process summary files
    for item in SUMMARY_DIR.iterdir():
        video_id = None
        content = None
        
        if item.is_file() and item.suffix == '.md':
            # Extract video ID from filename
            video_id = item.stem.split('_')[0]
            content = item.read_text(encoding='utf-8')
        elif item.is_dir():
            video_id = item.name
            summary_file = item / 'summary.txt'
            if summary_file.exists():
                content = summary_file.read_text(encoding='utf-8')
        
        if video_id and content and video_id in video_map:
            idx = video_map[video_id]
            if "summary" not in data["videos"][idx] or not data["videos"][idx]["summary"]:
                summary = parse_markdown_summary(content, video_id)
                if summary.get("ideas") or summary.get("insights"):
                    data["videos"][idx]["summary"] = summary
                    data["videos"][idx]["insights_count"] = len(summary.get("ideas", []))
                    print(f"✅ Added summary for {video_id}: {data['videos'][idx]['title'][:40]}...")
                    updated += 1
    
    # Save
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"\nDone! Updated {updated} videos with summaries.")

if __name__ == "__main__":
    main()
