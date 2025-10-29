#!/usr/bin/env python3
"""
Autonomous Startup Idea Generation Agent

Continuously generates, researches, and evaluates startup ideas using Claude API.
Saves promising venture-backable ideas as text files in the ideas/ directory.
"""

import os
import json
import time
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional
import anthropic
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY')
IDEAS_HISTORY_FILE = Path(os.getenv('IDEAS_HISTORY_FILE', 'ideas_history.json'))
IDEAS_DIR = Path('ideas')
LOG_FILE = Path('agent.log')
MODEL = "claude-sonnet-4-5-20250929"  # Sonnet 4.5 for better analysis
MAX_WEB_SEARCHES = 5  # 5 web searches for cost efficiency while catching major competitors
COMPRESSION_THRESHOLD = 100  # Compress learnings when history exceeds this many items


class Logger:
    """Simple logger that writes to both stdout and a file."""
    def __init__(self, log_file: Path):
        self.log_file = log_file
        self.file = open(log_file, 'a', buffering=1)  # Line buffered

    def log(self, message: str):
        """Write message to both stdout and log file."""
        print(message)
        self.file.write(f"{message}\n")
        self.file.flush()

    def close(self):
        self.file.close()


# Create global logger
logger = Logger(LOG_FILE)


class StartupIdeaAgent:
    """Autonomous agent that generates and researches startup ideas."""

    def __init__(self):
        self.client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
        self.history = self.load_history()
        # Ensure ideas directory exists
        IDEAS_DIR.mkdir(exist_ok=True)

    def load_history(self) -> Dict:
        """Load history with approved ideas, rejected ideas, and compressed learnings."""
        if IDEAS_HISTORY_FILE.exists():
            try:
                with open(IDEAS_HISTORY_FILE, 'r') as f:
                    data = json.load(f)
                    # Support legacy format
                    if 'explored_ideas' in data and not isinstance(data.get('explored_ideas'), list):
                        return data
                    # Legacy format: convert to new structure
                    if 'explored_ideas' in data and isinstance(data.get('explored_ideas'), list):
                        return {
                            'approved_ideas': data['explored_ideas'],
                            'rejected_ideas': [],
                            'compressed_learnings': '',
                            'last_updated': data.get('last_updated', datetime.now().isoformat())
                        }
                    return data
            except Exception as e:
                print(f"[WARN] Could not load history file: {e}")
                return {'approved_ideas': [], 'rejected_ideas': [], 'compressed_learnings': '', 'last_updated': datetime.now().isoformat()}
        return {'approved_ideas': [], 'rejected_ideas': [], 'compressed_learnings': '', 'last_updated': datetime.now().isoformat()}

    def save_history(self):
        """Save history with approved ideas, rejected ideas, and compressed learnings."""
        try:
            self.history['last_updated'] = datetime.now().isoformat()
            with open(IDEAS_HISTORY_FILE, 'w') as f:
                json.dump(self.history, f, indent=2)
        except Exception as e:
            print(f"[WARN] Could not save history: {e}")

    def save_idea_to_file(self, idea: Dict) -> Path:
        """Save an approved idea to a text file in the ideas/ directory."""
        try:
            # Create filename from timestamp and sanitized title
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            sanitized_title = "".join(c if c.isalnum() or c in (' ', '-', '_') else '' for c in idea['title'])
            sanitized_title = sanitized_title.replace(' ', '_')[:50]  # Limit length
            filename = f"{timestamp}_{sanitized_title}.txt"
            filepath = IDEAS_DIR / filename

            # Format the idea content
            content = f"""{'='*70}
STARTUP IDEA: {idea['title']}
Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
{'='*70}

CORE PROBLEM
{'-'*70}
{idea['core_problem']}

VALUE PROPOSITION
{'-'*70}
{idea['value_proposition']}

MARKET SIZE
{'-'*70}
{idea['market_size']}

IDEAL CUSTOMER PROFILE (ICP)
{'-'*70}
{idea['icp']}

JUSTIFICATION
{'-'*70}
{idea['justification']}

COMPETITIVE LANDSCAPE
{'-'*70}
{idea.get('competitive_landscape', 'N/A')}

SOURCES & CITATIONS
{'-'*70}
"""
            # Add citations if available
            if idea.get('citations'):
                for i, citation in enumerate(idea['citations'], 1):
                    content += f"{i}. {citation}\n"
            else:
                content += "No citations available.\n"

            content += f"\n{'='*70}\n"

            # Write to file
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)

            print(f"[FILE] Idea saved to: {filepath}")
            return filepath
        except Exception as e:
            print(f"[ERROR] Failed to save idea to file: {e}")
            return None

    def compress_learnings(self):
        """Compress rejected ideas into key learnings when history gets too large."""
        rejected_count = len(self.history.get('rejected_ideas', []))

        if rejected_count < COMPRESSION_THRESHOLD:
            return  # Not enough data to compress yet

        print(f"\n[COMPRESSION] Compressing {rejected_count} rejected ideas into learnings...")

        try:
            # Prepare rejected ideas for summarization
            rejected_summary = "\n".join([
                f"- {idea['title']}: {idea['reason']}"
                for idea in self.history['rejected_ideas'][-COMPRESSION_THRESHOLD:]
            ])

            # Use Claude to summarize learnings
            response = self.client.messages.create(
                model=MODEL,
                max_tokens=2000,
                temperature=0.3,
                messages=[{
                    "role": "user",
                    "content": f"""Analyze these rejected startup ideas and extract key learnings about what makes ideas non-venture-backable.

Rejected ideas and reasons:
{rejected_summary}

Provide a concise summary (3-5 bullet points) of the most common rejection patterns and key lessons learned. Focus on:
- Market/competition issues
- Lack of defensibility
- TAM concerns
- Timing problems
- Other systematic issues

Keep it under 500 words."""
                }]
            )

            compressed = response.content[0].text.strip()

            # Update compressed learnings
            if self.history.get('compressed_learnings'):
                self.history['compressed_learnings'] += f"\n\n--- Compression from {datetime.now().strftime('%Y-%m-%d')} ---\n{compressed}"
            else:
                self.history['compressed_learnings'] = compressed

            # Keep only the most recent rejected ideas
            self.history['rejected_ideas'] = self.history['rejected_ideas'][-50:]

            self.save_history()
            print(f"[COMPRESSION] Learnings compressed successfully")

        except Exception as e:
            print(f"[ERROR] Failed to compress learnings: {e}")

    def generate_and_evaluate_idea(self) -> Dict | None:
        """
        Generate a startup idea, research it thoroughly, and evaluate if it's venture-backable.

        Returns:
            Dict with idea details if promising, None otherwise
        """
        print(f"\n{'='*70}")
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] [GENERATE] Generating new startup idea")
        approved_count = len(self.history.get('approved_ideas', []))
        rejected_count = len(self.history.get('rejected_ideas', []))
        print(f"[HISTORY] Approved: {approved_count}, Rejected: {rejected_count}")
        print(f"{'='*70}\n")

        # Create the system prompt
        system_prompt = """You are an expert startup analyst and venture capitalist with deep knowledge of:
- Emerging technologies and market trends
- Competitive landscape analysis
- Market sizing and TAM estimation
- Customer development and ICP definition
- Venture capital criteria for fundability

Your goal is to generate ONE truly promising, venture-backable startup idea by:
1. Researching current trends, emerging technologies, and market gaps
2. Conducting competitive analysis
3. Estimating market size (TAM/SAM/SOM)
4. Defining the ideal customer profile
5. Articulating the value proposition and core problem

Be rigorous and critical. Only propose ideas that meet these criteria:
- TAM of $1B+ (or clear path to it)
- Clear, urgent customer pain point
- Defensible competitive moat (technical complexity, network effects, data, stickiness etc.)
- Realistic go-to-market strategy (ideally bottom-up, developer-led, or product-led)
- Timing is right (why now?)"""

        # Create the user prompt with history and learnings
        approved_ideas = self.history.get('approved_ideas', [])
        history_str = "\n".join([f"- {idea}" for idea in approved_ideas[-50:]])  # Last 50 to keep prompt manageable

        compressed_learnings = self.history.get('compressed_learnings', '')
        learnings_section = f"""

KEY LEARNINGS FROM PAST REJECTIONS:
{compressed_learnings}

These learnings should inform your evaluation criteria.""" if compressed_learnings else ""

        user_prompt = f"""Generate ONE new venture-backable startup idea.

IMPORTANT: Avoid ideas similar to these already explored:
{history_str if approved_ideas else "(No ideas explored yet - this is your first!)"}
{learnings_section}

Process:
1. Use web search to research:
   - Current tech/business trends and emerging opportunities
   - Recent news, research papers, and industry developments
   - Market size data and growth rates

2. Synthesize findings to identify a compelling opportunity

3. CRITICAL: Thoroughly research the competitive landscape with MULTIPLE searches:
   - Search for direct competitors: "[idea category] startups"
   - Search for recent funding: "[idea category] funding 2024 2025"
   - Search YC companies: "Y Combinator [idea category]"
   - Search for alternatives: "best [idea category] tools"
   - Look for both established players AND early-stage startups
   - If you find 5+ well-funded competitors, strongly consider rejecting

4. Deeply analyze:
   - Core problem and why it matters
   - Target customer (ICP) and their pain
   - Value proposition and unique approach that differentiates from ALL competitors found
   - Market size (TAM/SAM/SOM with sources)
   - Complete list of competitors with their funding/stage
   - Why now? (timing/trends making this viable)
   - Go-to-market strategy
   - Defensibility: What moat do you have that competitors lack?

5. Make a decision: Is this truly venture-backable?
   - TAM: $1B+ potential?
   - Pain: Is it urgent and critical?
   - Competition: Not too crowded? Clear differentiation?
   - Defensibility: Clear moat that's hard to replicate?
   - Timing: Why is now the right time?

If YES, respond with this EXACT JSON format:
{{
  "venture_backable": true,
  "title": "Brief, compelling name (5-8 words max)",
  "core_problem": "2-3 sentences on the problem",
  "value_proposition": "2-3 sentences on your solution and unique approach",
  "market_size": "TAM/SAM/SOM with numbers and sources",
  "icp": "Detailed ideal customer description",
  "justification": "Why this is venture-backable (timing, market, defensibility, team opportunity)",
  "competitive_landscape": "List ALL competitors found (established + startups), their funding/stage, and your clear differentiation",
  "keywords": ["keyword1", "keyword2", "keyword3"]
}}

If NO (not venture-backable), respond:
{{
  "venture_backable": false,
  "idea": "Brief title or description of the rejected idea",
  "reason": "Detailed explanation of why not venture-backable"
}}

Remember: Be critical and selective. Most ideas should be rejected. Only the truly exceptional ones should pass."""

        try:
            # Make API call with web search tool enabled
            message = self.client.messages.create(
                model=MODEL,
                max_tokens=16000,
                temperature=1.0,  # Higher temperature for creativity
                tools=[{
                    "type": "web_search_20250305",
                    "name": "web_search",
                    "max_uses": MAX_WEB_SEARCHES
                }],
                messages=[{
                    "role": "user",
                    "content": user_prompt
                }],
                system=system_prompt
            )

            # Extract the response and citations
            response_text = ""
            citations = []

            for block in message.content:
                if block.type == "text":
                    response_text += block.text

            # Extract citations if available (from web search results)
            if hasattr(message, 'citations') and message.citations:
                citations = [{"url": c.url, "title": c.title} for c in message.citations]

            print(f"[API] Response received from Claude")
            print(f"[USAGE] Tokens: {message.usage.input_tokens} input, {message.usage.output_tokens} output")
            if citations:
                print(f"[RESEARCH] Citations found: {len(citations)}")

            # Parse JSON response
            # Find JSON in the response (it might be wrapped in markdown code blocks)
            json_start = response_text.find('{')
            json_end = response_text.rfind('}') + 1

            if json_start == -1 or json_end == 0:
                print("[WARN] No JSON found in response")
                return None

            json_str = response_text[json_start:json_end]
            result = json.loads(json_str)

            if not result.get('venture_backable', False):
                idea_title = result.get('idea', 'Unknown idea')
                reason = result.get('reason', 'No reason provided')
                print(f"[REJECTED] {idea_title}: {reason}")

                # Track rejected idea with reason
                self.history.setdefault('rejected_ideas', []).append({
                    'title': idea_title,
                    'reason': reason,
                    'timestamp': datetime.now().isoformat()
                })
                self.save_history()

                # Check if we should compress learnings
                self.compress_learnings()

                return None

            print(f"[APPROVED] Venture-backable idea identified: {result['title']}")

            # Add keywords and title to approved ideas
            keywords = result.get('keywords', [])
            approved_list = self.history.setdefault('approved_ideas', [])
            approved_list.extend(keywords)
            approved_list.append(result['title'])
            self.save_history()

            # Add citations to result
            result['citations'] = citations

            return result

        except anthropic.APIError as e:
            print(f"[ERROR] Anthropic API error: {e}")
            return None
        except json.JSONDecodeError as e:
            print(f"[ERROR] Failed to parse JSON response: {e}")
            print(f"[DEBUG] Response text: {response_text[:500]}...")
            return None
        except Exception as e:
            print(f"[ERROR] Unexpected error: {e}")
            return None

    def run(self):
        """Main loop: continuously generate ideas and save promising ones to files."""
        print("[AGENT] Startup Idea Agent initializing...")
        print(f"[CONFIG] Ideas directory: {IDEAS_DIR.absolute()}")
        print(f"[CONFIG] Model: {MODEL}")
        print(f"[CONFIG] Max web searches per idea: {MAX_WEB_SEARCHES}")
        print(f"[CONFIG] Compression threshold: {COMPRESSION_THRESHOLD} rejected ideas")
        print("\n" + "="*70 + "\n")

        iteration = 0
        while True:
            iteration += 1
            print(f"\n[ITERATION] Starting iteration {iteration}")

            try:
                # Generate and evaluate idea
                idea = self.generate_and_evaluate_idea()

                if idea:
                    # Save idea to file
                    print(f"\n[SAVE] Saving idea to file: {idea['title']}")

                    filepath = self.save_idea_to_file(idea)

                    if filepath:
                        print(f"[SUCCESS] Idea saved successfully to {filepath}")
                    else:
                        print(f"[WARN] Failed to save idea to file (but saved to history)")

                # Continue immediately to next iteration
                print(f"\n[AGENT] Proceeding to next iteration...")

            except KeyboardInterrupt:
                print("\n\n[SHUTDOWN] Agent stopped by user")
                break
            except Exception as e:
                print(f"\n[ERROR] Unexpected error in main loop: {e}")
                print("[RETRY] Waiting 5 minutes before retrying...")
                time.sleep(300)


if __name__ == "__main__":
    # Verify required environment variables
    if not ANTHROPIC_API_KEY:
        print("[ERROR] ANTHROPIC_API_KEY not set")
        exit(1)

    # Start the agent
    agent = StartupIdeaAgent()
    agent.run()
