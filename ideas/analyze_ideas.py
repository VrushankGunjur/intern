#!/usr/bin/env python3
"""
Startup Ideas Analysis Script

Analyzes 162 startup ideas, clusters them by theme, identifies duplicates,
scores them on key dimensions, and outputs structured data for strategic review.
"""

import os
import sys
import json
import re
from pathlib import Path
from typing import List, Dict, Optional
import anthropic
from dotenv import load_dotenv

# Load environment variables
load_dotenv(dotenv_path='../.env')

# Configuration
ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY')
IDEAS_DIR = Path('.')
OUTPUT_FILE = Path('analysis.json')
MODEL = "claude-sonnet-4-5-20250929"  # Use Sonnet for better analysis


def parse_idea_file(filepath: Path) -> Dict:
    """Parse a startup idea file into structured data."""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # Extract the title from the first line after ===
    title_match = re.search(r'STARTUP IDEA: (.+)', content)
    title = title_match.group(1).strip() if title_match else filepath.stem

    # Extract sections using regex
    def extract_section(section_name: str) -> str:
        pattern = rf'{section_name}\s*\n-+\s*\n(.*?)(?=\n[A-Z\s]+\n-+|\n=+|$)'
        match = re.search(pattern, content, re.DOTALL)
        return match.group(1).strip() if match else ""

    return {
        'filename': filepath.name,
        'title': title,
        'core_problem': extract_section('CORE PROBLEM'),
        'value_proposition': extract_section('VALUE PROPOSITION'),
        'market_size': extract_section('MARKET SIZE'),
        'icp': extract_section('IDEAL CUSTOMER PROFILE'),
        'justification': extract_section('JUSTIFICATION'),
        'competitive_landscape': extract_section('COMPETITIVE LANDSCAPE'),
    }


def load_all_ideas() -> List[Dict]:
    """Load and parse all idea files."""
    print("[LOADING] Scanning for idea files...", flush=True)
    sys.stdout.flush()
    idea_files = sorted(IDEAS_DIR.glob('2025*.txt'))

    ideas = []
    for filepath in idea_files:
        try:
            idea = parse_idea_file(filepath)
            ideas.append(idea)
        except Exception as e:
            print(f"[WARN] Failed to parse {filepath.name}: {e}")

    print(f"[LOADED] {len(ideas)} ideas loaded successfully", flush=True)
    sys.stdout.flush()
    return ideas


def analyze_ideas_batch(client: anthropic.Anthropic, ideas: List[Dict], batch_num: int, total_batches: int) -> Dict:
    """Use Claude to analyze a batch of ideas: cluster, score, identify duplicates."""
    print(f"\n[ANALYZING] Batch {batch_num}/{total_batches} ({len(ideas)} ideas)...", flush=True)
    sys.stdout.flush()

    # Prepare ideas summary for Claude
    ideas_summary = ""
    for idx, idea in enumerate(ideas, 1):
        ideas_summary += f"\n## IDEA {idx}: {idea['title']}\n"
        ideas_summary += f"PROBLEM: {idea['core_problem'][:300]}...\n"
        ideas_summary += f"VALUE: {idea['value_proposition'][:300]}...\n"
        ideas_summary += f"TAM: {idea['market_size'][:200]}...\n"
        ideas_summary += f"COMPETITION: {idea['competitive_landscape'][:300]}...\n"

    prompt = f"""Analyze these startup ideas and provide structured analysis.

{ideas_summary}

Provide your analysis in this EXACT JSON format:
{{
  "themes": [
    {{
      "name": "Theme name",
      "description": "What this theme is about",
      "idea_indices": [1, 3, 5],
      "promise_score": 7,
      "saturation": "low/medium/high",
      "key_insight": "Why this theme matters or concerns"
    }}
  ],
  "duplicates": [
    {{
      "group": [1, 5, 12],
      "reason": "Why these are duplicates/overlapping"
    }}
  ],
  "scores": [
    {{
      "idea_index": 1,
      "market_timing": 8,
      "defensibility": 7,
      "tam_quality": 9,
      "execution_difficulty": 6,
      "total_score": 30,
      "unique_angle": "What makes this different",
      "concerns": "Key risks or weaknesses"
    }}
  ]
}}

Scoring criteria (1-10):
- market_timing: Is now the right time? Is urgency high?
- defensibility: How strong is the moat? Hard to replicate?
- tam_quality: Is TAM real and achievable? Good unit economics?
- execution_difficulty: Can technical founders build this? (lower = easier = better)

Be critical. Don't inflate scores. Average should be 5-6."""

    try:
        response = client.messages.create(
            model=MODEL,
            max_tokens=16000,
            temperature=0.3,
            messages=[{"role": "user", "content": prompt}]
        )

        response_text = response.content[0].text

        # Extract JSON
        json_start = response_text.find('{')
        json_end = response_text.rfind('}') + 1
        json_str = response_text[json_start:json_end]

        result = json.loads(json_str)
        print(f"[SUCCESS] Batch {batch_num} analyzed successfully", flush=True)
        sys.stdout.flush()
        return result

    except Exception as e:
        print(f"[ERROR] Failed to analyze batch {batch_num}: {e}", flush=True)
        sys.stdout.flush()
        return {"themes": [], "duplicates": [], "scores": []}


def merge_batch_results(batch_results: List[Dict], batch_size: int) -> Dict:
    """Merge results from multiple batches, adjusting indices."""
    merged = {
        "themes": [],
        "duplicates": [],
        "scores": []
    }

    for batch_num, result in enumerate(batch_results):
        offset = batch_num * batch_size

        # Adjust theme indices
        for theme in result.get("themes", []):
            theme["idea_indices"] = [idx + offset for idx in theme["idea_indices"]]
            merged["themes"].append(theme)

        # Adjust duplicate indices
        for dup_group in result.get("duplicates", []):
            dup_group["group"] = [idx + offset for idx in dup_group["group"]]
            merged["duplicates"].append(dup_group)

        # Adjust score indices
        for score in result.get("scores", []):
            score["idea_index"] = score["idea_index"] + offset
            merged["scores"].append(score)

    return merged


def consolidate_themes(themes: List[Dict]) -> List[Dict]:
    """Use Claude to consolidate overlapping themes from batches."""
    print("\n[CONSOLIDATING] Merging themes from batches...")
    # For now, just return as-is; could add LLM-based consolidation if needed
    return themes


def main():
    """Main analysis pipeline."""
    print("="*70, flush=True)
    print("STARTUP IDEAS ANALYSIS", flush=True)
    print("="*70, flush=True)
    sys.stdout.flush()

    # Verify API key
    if not ANTHROPIC_API_KEY:
        print("[ERROR] ANTHROPIC_API_KEY not found in ../.env", flush=True)
        sys.stdout.flush()
        return

    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    # Load all ideas
    ideas = load_all_ideas()

    if not ideas:
        print("[ERROR] No ideas found to analyze", flush=True)
        sys.stdout.flush()
        return

    # Process in batches (Claude context limits)
    BATCH_SIZE = 20
    batches = [ideas[i:i + BATCH_SIZE] for i in range(0, len(ideas), BATCH_SIZE)]
    total_batches = len(batches)

    print(f"\n[BATCHING] Processing {len(ideas)} ideas in {total_batches} batches of {BATCH_SIZE}")

    batch_results = []
    for batch_num, batch in enumerate(batches, 1):
        result = analyze_ideas_batch(client, batch, batch_num, total_batches)
        batch_results.append(result)

    # Merge results
    print("\n[MERGING] Combining batch results...")
    merged_results = merge_batch_results(batch_results, BATCH_SIZE)

    # Consolidate themes
    consolidated_themes = consolidate_themes(merged_results["themes"])

    # Build final output
    output = {
        "total_ideas": len(ideas),
        "ideas": ideas,
        "themes": consolidated_themes,
        "duplicates": merged_results["duplicates"],
        "scores": merged_results["scores"],
        "top_ideas": sorted(
            merged_results["scores"],
            key=lambda x: x.get("total_score", 0),
            reverse=True
        )[:20]
    }

    # Save to JSON
    print(f"\n[SAVING] Writing analysis to {OUTPUT_FILE}...")
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2)

    print(f"\n[COMPLETE] Analysis saved to {OUTPUT_FILE}")
    print(f"[STATS] {len(consolidated_themes)} themes identified")
    print(f"[STATS] {len(merged_results['duplicates'])} duplicate groups found")
    print(f"[STATS] {len(merged_results['scores'])} ideas scored")

    # Print top 5 ideas
    print("\n" + "="*70)
    print("TOP 5 IDEAS BY SCORE:")
    print("="*70)
    for i, score in enumerate(output["top_ideas"][:5], 1):
        idea_idx = score["idea_index"]
        idea = ideas[idea_idx]
        print(f"\n{i}. {idea['title']}")
        print(f"   Score: {score['total_score']}/40 (Timing:{score['market_timing']}, "
              f"Defensibility:{score['defensibility']}, TAM:{score['tam_quality']}, "
              f"Difficulty:{score['execution_difficulty']})")
        print(f"   Unique: {score.get('unique_angle', 'N/A')}")


if __name__ == "__main__":
    main()
