# Autonomous Startup Idea Agent

An AI-powered agent that continuously generates, researches, and evaluates venture-backable startup ideas, saving the most promising ones as text files.

## Features

- **Autonomous Research**: Uses Claude API with web search to research trends, markets, and competition in real-time
- **Rigorous Evaluation**: Only saves ideas that meet venture capital criteria (TAM $1B+, clear moat, timing, etc.)
- **Continuous Operation**: Runs 24/7 in Docker, generating ideas around the clock
- **Enhanced Memory System**: Tracks both approved and rejected ideas with reasons, compressing learnings to improve future evaluations
- **Smart Deduplication**: Avoids repetition by learning from both successes and failures
- **Organized Storage**: Saves each approved idea as a timestamped text file in the ideas/ directory

## How It Works

1. **Generate**: Claude researches current trends and generates a startup idea
2. **Research**: Performs web searches to validate market size, competition, and timing
3. **Evaluate**: Applies VC criteria to determine if the idea is truly venture-backable
4. **Learn**: Tracks rejected ideas with reasons and compresses learnings when history grows large
5. **Save**: If approved, saves a detailed text file to ideas/ with justification, TAM, ICP, and competitive analysis
6. **Loop**: Continues immediately to the next iteration, learning from past successes and failures

## Prerequisites

- Docker and Docker Compose (optional, for containerized deployment)
- Anthropic API key (Claude)
- Python 3.11+ (if running locally)

## Setup

### 1. Clone/Download this repository

### 2. Set up environment variables

```bash
# Copy the example file
cp .env.example .env

# Edit .env with your credentials
nano .env
```

Fill in your API key:

```env
ANTHROPIC_API_KEY=sk-ant-...
```

### 3. Create data directory (for Docker deployment)

```bash
mkdir -p data
```

The ideas will be saved to the `ideas/` directory (automatically created on first run).

## Running the Agent

### Using Docker Compose (Recommended)

```bash
# Build and start the agent
docker-compose up -d

# View logs
docker-compose logs -f

# Stop the agent
docker-compose down
```

### Using Docker directly

```bash
# Build the image
docker build -t startup-agent .

# Run the container
docker run -d \
  --name startup-agent \
  --env-file .env \
  -v $(pwd)/data:/app/data \
  startup-agent

# View logs
docker logs -f startup-agent

# Stop the container
docker stop startup-agent
```

### Running locally (for testing)

```bash
# Install dependencies
pip install -r requirements.txt

# Run the agent
python agent.py
```

## Viewing Generated Ideas

All approved ideas are saved as text files in the `ideas/` directory:

```bash
# List all generated ideas
ls -lh ideas/

# View a specific idea
cat ideas/20251027_123456_AI_Governance_Platform.txt

# Monitor new ideas in real-time
watch -n 5 'ls -lh ideas/ | tail -10'
```

## Configuration

### Adjusting Research Depth

Edit `agent.py` line 28 to change the number of web searches per idea:

```python
MAX_WEB_SEARCHES = 10  # Increase for deeper research, decrease for faster generation
```

### Adjusting Learning Compression

Edit `agent.py` line 29 to change when rejected ideas get compressed into learnings:

```python
COMPRESSION_THRESHOLD = 100  # Number of rejected ideas before compression runs
```

### Modifying Evaluation Criteria

Edit the system prompt in `agent.py` to adjust what makes an idea "venture-backable."

## Monitoring

### View real-time logs

```bash
docker-compose logs -f
```

### Check idea history

```bash
cat data/ideas_history.json
```

### Restart the agent

```bash
docker-compose restart
```

## Troubleshooting

### "ANTHROPIC_API_KEY not set" error

- Ensure your `.env` file exists in the project root
- Check that `ANTHROPIC_API_KEY` is set correctly
- Verify the API key is active at https://console.anthropic.com/

### "Anthropic API error"

- Verify your `ANTHROPIC_API_KEY` is correct
- Check your API usage limits at https://console.anthropic.com/
- Web search costs $10 per 1,000 searches plus token costs

### No ideas being saved

- Check logs: `docker-compose logs -f` or `cat agent.log`
- The agent is highly selective - it may take several cycles before approving an idea
- Check the `ideas/` directory for newly saved files
- Review rejected ideas in `ideas_history.json` to see what's being filtered out

### Container keeps restarting

- Check logs: `docker logs startup-idea-agent`
- Verify all environment variables are set
- Ensure the `data` directory exists and is writable
- Ensure the `ideas` directory can be created

## Cost Estimation

### Claude API Costs

- Web search: $10 per 1,000 searches
- Tokens: ~$3 per million input tokens, ~$15 per million output tokens
- Estimated: $0.50-2.00 per idea (depending on research depth)

With 30-60 ideas per day, expect roughly $15-60/day in API costs.

## Architecture

```
agent.py              # Main agent loop and idea generation
├─ generate_and_evaluate_idea()  # Core logic with web search
├─ load_history()     # Load approved/rejected ideas and learnings
├─ save_history()     # Persist history with timestamps
├─ save_idea_to_file()  # Save approved ideas as text files
└─ compress_learnings()  # Compress rejected ideas into insights

ideas_history.json    # Enhanced history tracking (auto-generated)
├─ approved_ideas[]   # Titles and keywords of approved ideas
├─ rejected_ideas[]   # Rejected ideas with reasons and timestamps
├─ compressed_learnings  # AI-generated insights from rejections
└─ last_updated       # Timestamp of last update

ideas/                # Directory with approved idea files (auto-created)
└─ YYYYMMDD_HHMMSS_Idea_Title.txt  # Timestamped idea files
```

## Memory System

The agent now features an enhanced memory system that learns from both successes and failures:

- **Approved Ideas**: Tracked by title and keywords to avoid repetition
- **Rejected Ideas**: Stored with detailed reasons (market issues, competition, TAM concerns, etc.)
- **Compressed Learnings**: When rejected ideas exceed the threshold (default: 100), Claude automatically summarizes common rejection patterns into actionable insights
- **Context Integration**: Both recent history and compressed learnings are included in prompts to improve future evaluations

## Customization Ideas

- Add Slack/Discord notifications when new ideas are saved
- Parse text files into a database for analysis and visualization
- Build a web dashboard to browse and filter saved ideas
- Integrate with Airtable or Notion for idea management
- Add semantic similarity checking using embeddings
- Filter by specific industries or technologies
- Add email notifications (using email_sender.py as a starting point)
- Export ideas to PDF with better formatting

## License

MIT

## Support

For issues or questions, contact team@heysanctum.com
