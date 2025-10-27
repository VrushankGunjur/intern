# Autonomous Startup Idea Agent

An AI-powered agent that continuously generates, researches, and evaluates venture-backable startup ideas, sending the most promising ones via email.

## Features

- **Autonomous Research**: Uses Claude API with web search to research trends, markets, and competition in real-time
- **Rigorous Evaluation**: Only sends ideas that meet venture capital criteria (TAM $1B+, clear moat, timing, etc.)
- **Continuous Operation**: Runs 24/7 in Docker, generating ideas around the clock
- **Smart Deduplication**: Tracks explored ideas to avoid repetition
- **Beautiful Email Reports**: Sends formatted emails with market size, ICP, value prop, and competitive analysis

## How It Works

1. **Generate**: Claude researches current trends and generates a startup idea
2. **Research**: Performs web searches to validate market size, competition, and timing
3. **Evaluate**: Applies VC criteria to determine if the idea is truly venture-backable
4. **Report**: If promising, sends a detailed email with justification, TAM, ICP, and more
5. **Loop**: Pauses briefly, then repeats continuously

## Prerequisites

- Docker and Docker Compose
- Anthropic API key (Claude)
- Gmail/Google Workspace account with your heysanctum.com domain

## Setup

### 1. Clone/Download this repository

### 2. Configure Gmail App Password

Since you're using Gmail/Google Workspace with your heysanctum.com domain:

1. Go to [Google App Passwords](https://myaccount.google.com/apppasswords)
2. Sign in with your @heysanctum.com account
3. Create a new app password for "Mail"
4. Copy the 16-character password (remove spaces)

### 3. Set up environment variables

```bash
# Copy the example file
cp .env.example .env

# Edit .env with your credentials
nano .env
```

Fill in your credentials:

```env
ANTHROPIC_API_KEY=sk-ant-...
GMAIL_USER=your_email@heysanctum.com
GMAIL_APP_PASSWORD=your16charpassword
RECIPIENT_EMAIL=team@heysanctum.com
```

### 4. Create data directory

```bash
mkdir -p data
```

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

## Testing Email Functionality

Before running the full agent, test that emails work:

```bash
python email_sender.py
```

This will send a test email to verify your Gmail configuration.

## Configuration

### Adjusting Research Depth

Edit `agent.py` line 26 to change the number of web searches per idea:

```python
MAX_WEB_SEARCHES = 10  # Increase for deeper research, decrease for faster generation
```

### Changing Pause Duration

Edit `agent.py` line 226 to adjust the pause between idea generation cycles:

```python
pause_seconds = 150  # Currently 2.5 minutes
```

### Modifying Evaluation Criteria

Edit the system prompt in `agent.py` starting at line 68 to adjust what makes an idea "venture-backable."

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

### "Gmail credentials not set" error

- Ensure your `.env` file exists and has the correct values
- Check that `GMAIL_USER` and `GMAIL_APP_PASSWORD` are set
- Verify you're using an App Password, not your regular Gmail password

### "Anthropic API error"

- Verify your `ANTHROPIC_API_KEY` is correct
- Check your API usage limits at https://console.anthropic.com/
- Web search costs $10 per 1,000 searches plus token costs

### No emails being sent

- Check logs: `docker-compose logs -f`
- The agent is highly selective - it may take several cycles before finding a truly promising idea
- Test email functionality: `python email_sender.py`

### Container keeps restarting

- Check logs: `docker logs startup-idea-agent`
- Verify all environment variables are set
- Ensure the `data` directory exists and is writable

## Cost Estimation

### Claude API Costs

- Web search: $10 per 1,000 searches
- Tokens: ~$3 per million input tokens, ~$15 per million output tokens
- Estimated: $0.50-2.00 per idea (depending on research depth)

With 30-60 ideas per day, expect roughly $15-60/day in API costs.

## Architecture

```
agent.py              # Main agent loop and idea generation
├─ generate_and_evaluate_idea()  # Core logic
├─ load_history()     # Deduplication
└─ save_history()     # Persistence

email_sender.py       # Email formatting and sending
└─ send_startup_idea_email()

ideas_history.json    # Tracked ideas (auto-generated)
```

## Customization Ideas

- Add Slack notifications instead of/in addition to email
- Store full reports in a database for analysis
- Add a web dashboard to view ideas
- Integrate with Airtable or Notion for idea management
- Add more sophisticated deduplication (embeddings, semantic similarity)
- Filter by specific industries or technologies

## License

MIT

## Support

For issues or questions, contact team@heysanctum.com
