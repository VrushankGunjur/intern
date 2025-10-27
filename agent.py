#!/usr/bin/env python3
"""
Autonomous Startup Idea Generation Agent

Continuously generates, researches, and evaluates startup ideas using Claude API.
Sends promising venture-backable ideas via email.
"""

import os
import json
import time
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Dict
import anthropic
from dotenv import load_dotenv
from email_sender import send_startup_idea_email

# Load environment variables
load_dotenv()

# Configuration
ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY')
IDEAS_HISTORY_FILE = Path(os.getenv('IDEAS_HISTORY_FILE', 'ideas_history.json'))
LOG_FILE = Path('agent.log')
MODEL = "claude-haiku-4-5-20251001"  # Haiku 4.5 supports web search, much cheaper
MAX_WEB_SEARCHES = 5  # 5 web searches for cost efficiency while catching major competitors


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
        self.explored_ideas = self.load_history()

    def load_history(self) -> List[str]:
        """Load previously explored idea topics from JSON file."""
        if IDEAS_HISTORY_FILE.exists():
            try:
                with open(IDEAS_HISTORY_FILE, 'r') as f:
                    data = json.load(f)
                    return data.get('explored_ideas', [])
            except Exception as e:
                print(f"[WARN] Could not load history file: {e}")
                return []
        return []

    def save_history(self):
        """Save explored ideas to JSON file."""
        try:
            with open(IDEAS_HISTORY_FILE, 'w') as f:
                json.dump({
                    'explored_ideas': self.explored_ideas,
                    'last_updated': datetime.now().isoformat()
                }, f, indent=2)
        except Exception as e:
            print(f"[WARN] Could not save history: {e}")

    def generate_and_evaluate_idea(self) -> Dict | None:
        """
        Generate a startup idea, research it thoroughly, and evaluate if it's venture-backable.

        Returns:
            Dict with idea details if promising, None otherwise
        """
        print(f"\n{'='*70}")
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] [GENERATE] Generating new startup idea")
        print(f"[HISTORY] Explored ideas count: {len(self.explored_ideas)}")
        print(f"{'='*70}\n")

        # Create the system prompt
        system_prompt = """You are an expert startup analyst and venture capitalist with deep knowledge of:
- Emerging technologies and market trends
- Competitive landscape analysis
- Market sizing and TAM estimation
- Customer development and ICP definition
- Venture capital criteria for fundability

IMPORTANT: Focus on ideas suited for 22-year-old CS grad founders with:
- Strong software engineering skills (distributed systems, ML/AI, backend infrastructure)
- Quantitative/analytical background (can build data-intensive products)
- Technical depth but limited industry connections or sales experience
- Ability to build v1 without raising significant capital
- Preference for developer tools, infrastructure, data/AI products, or technical B2B SaaS

Your goal is to generate ONE truly promising, venture-backable startup idea by:
1. Researching current trends, emerging technologies, and market gaps
2. Conducting competitive analysis
3. Estimating market size (TAM/SAM/SOM)
4. Defining the ideal customer profile
5. Articulating the value proposition and core problem

Be rigorous and critical. Only propose ideas that meet these criteria:
- TAM of $1B+ (or clear path to it)
- Clear, urgent customer pain point
- Defensible competitive moat (technical complexity, network effects, data, etc.)
- Realistic go-to-market strategy (ideally bottom-up, developer-led, or product-led)
- Can be built by technical founders without deep industry connections
- Timing is right (why now?)"""

        # Create the user prompt with history
        history_str = "\n".join([f"- {idea}" for idea in self.explored_ideas[-50:]])  # Last 50 to keep prompt manageable

        user_prompt = f"""Generate ONE new venture-backable startup idea.

IMPORTANT: Avoid ideas similar to these already explored:
{history_str if self.explored_ideas else "(No ideas explored yet - this is your first!)"}

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
                return None

            print(f"[APPROVED] Venture-backable idea identified: {result['title']}")

            # Add keywords to explored ideas
            keywords = result.get('keywords', [])
            self.explored_ideas.extend(keywords)
            self.explored_ideas.append(result['title'])
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
        """Main loop: continuously generate ideas and send emails for promising ones."""
        print("[AGENT] Startup Idea Agent initializing...")
        print(f"[CONFIG] Email recipient: {os.getenv('RECIPIENT_EMAIL', 'team@heysanctum.com')}")
        print(f"[CONFIG] Model: {MODEL}")
        print(f"[CONFIG] Max web searches per idea: {MAX_WEB_SEARCHES}")
        print("\n" + "="*70 + "\n")

        iteration = 0
        while True:
            iteration += 1
            print(f"\n[ITERATION] Starting iteration {iteration}")

            try:
                # Generate and evaluate idea
                idea = self.generate_and_evaluate_idea()

                if idea:
                    # Send email
                    print(f"\n[EMAIL] Sending email for: {idea['title']}")

                    email_success = send_startup_idea_email({
                        'title': idea['title'],
                        'core_problem': idea['core_problem'],
                        'value_proposition': idea['value_proposition'],
                        'market_size': idea['market_size'],
                        'icp': idea['icp'],
                        'justification': idea['justification'],
                        'competitive_landscape': idea.get('competitive_landscape', 'N/A'),
                        'citations': idea.get('citations', [])
                    })

                    if email_success:
                        print(f"[SUCCESS] Email sent successfully")
                    else:
                        print(f"[WARN] Email failed to send (idea saved to history)")

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

    if not os.getenv('GMAIL_USER') or not os.getenv('GMAIL_APP_PASSWORD'):
        print("[ERROR] Gmail credentials not set (GMAIL_USER, GMAIL_APP_PASSWORD)")
        exit(1)

    # Start the agent
    agent = StartupIdeaAgent()
    agent.run()
