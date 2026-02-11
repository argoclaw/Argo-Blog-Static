#!/usr/bin/env python3
"""Generate viz_data for videos that don't have it yet."""

import json
import re
from pathlib import Path

DATA_FILE = Path("/home/opc/.openclaw/workspace/yt-viewer/data/videos.json")

def extract_keywords(text):
    """Extract potential keywords from text."""
    # Simple keyword extraction - words > 2 chars, exclude common words
    stop_words = {'的', '是', '在', '和', '了', '与', '对', '被', '将', '从', '到', 'the', 'and', 'to', 'of', 'a', 'is', 'in', 'for', 'on', 'that', 'this'}
    words = re.findall(r'[\u4e00-\u9fff]+|[a-zA-Z]{3,}', text)
    return [w for w in words if w.lower() not in stop_words][:5]

def generate_mindmap(summary):
    """Generate mindmap structure from summary."""
    ideas = summary.get('ideas', [])
    insights = summary.get('insights', [])
    takeaway = summary.get('takeaway', '')
    tldr = summary.get('tldr', '')
    
    # Group ideas into clusters (simple: first 3, middle 3, last 3)
    idea_texts = [i['text'] if isinstance(i, dict) else i for i in ideas]
    
    children = []
    
    if len(idea_texts) >= 3:
        # Split into themes
        third = len(idea_texts) // 3
        children.append({
            "label": "核心观点",
            "children": idea_texts[:third][:3]
        })
        children.append({
            "label": "关键论据",
            "children": idea_texts[third:2*third][:3]
        })
        children.append({
            "label": "延伸思考",
            "children": idea_texts[2*third:][:3]
        })
    
    if insights:
        children.append({
            "label": "深度洞察",
            "children": insights[:3]
        })
    
    if takeaway:
        children.append({
            "label": "核心结论",
            "children": [takeaway]
        })
    
    # Extract root from tldr
    root = tldr[:30] + "..." if len(tldr) > 30 else tldr if tldr else "视频总结"
    
    return {"root": root, "children": children}

def extract_stats(summary):
    """Extract numeric stats from facts and ideas."""
    stats = []
    facts = summary.get('facts', [])
    ideas = summary.get('ideas', [])
    
    all_text = facts + [i['text'] if isinstance(i, dict) else i for i in ideas]
    
    # Find patterns like "X万", "X%", "$X", "X年" etc
    patterns = [
        (r'(\d+(?:\.\d+)?)\s*万', '万'),
        (r'(\d+(?:\.\d+)?)\s*亿', '亿'),
        (r'(\d+(?:\.\d+)?)\s*%', '%'),
        (r'\$(\d+(?:\.\d+)?[KMB]?)', '$'),
        (r'(\d+(?:-\d+)?)\s*年', '年'),
        (r'(\d+(?:\.\d+)?)\s*倍', '倍'),
    ]
    
    seen = set()
    for text in all_text:
        for pattern, suffix in patterns:
            matches = re.findall(pattern, text)
            for m in matches:
                val = f"{m}{suffix}" if suffix != '$' else f"${m}"
                if val not in seen and len(stats) < 6:
                    # Try to extract context
                    context = text[:20].strip()
                    stats.append({"value": val, "label": context})
                    seen.add(val)
    
    return stats[:6]

def detect_comparison(summary):
    """Detect if content has comparison structure."""
    ideas = summary.get('ideas', [])
    all_text = ' '.join([i['text'] if isinstance(i, dict) else i for i in ideas])
    
    comparison_keywords = ['vs', 'VS', '对比', '相比', '优势', '劣势', '传统', '新型', '地面', '太空', '之前', '之后']
    return any(kw in all_text for kw in comparison_keywords)

def generate_viz_data(summary):
    """Generate complete viz_data for a summary."""
    viz_data = {}
    suggested_viz = []
    
    # Always generate mindmap
    mindmap = generate_mindmap(summary)
    if mindmap['children']:
        viz_data['mindmap'] = mindmap
    
    # Extract stats
    stats = extract_stats(summary)
    if stats:
        viz_data['stats'] = stats
        suggested_viz.append('stats')
    
    # Check for comparison
    if detect_comparison(summary):
        suggested_viz.append('comparison')
    
    return viz_data, suggested_viz

def main():
    with open(DATA_FILE, 'r') as f:
        data = json.load(f)
    
    updated = 0
    for video in data['videos']:
        summary = video.get('summary', {})
        
        # Skip if already has viz_data
        if summary.get('viz_data'):
            continue
        
        # Skip if no summary content
        if not summary.get('ideas') and not summary.get('insights'):
            continue
        
        viz_data, suggested_viz = generate_viz_data(summary)
        
        if viz_data:
            video['summary']['viz_data'] = viz_data
            if suggested_viz:
                video['summary']['suggested_viz'] = suggested_viz
            updated += 1
            print(f"✓ {video['id']} | {video.get('title', 'Unknown')[:40]}")
    
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ Updated {updated} videos")

if __name__ == '__main__':
    main()
