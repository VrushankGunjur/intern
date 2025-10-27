FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY agent.py .
COPY email_sender.py .

# Create volume mount point for persistent data
VOLUME ["/app/data"]

# Set environment variable to use data directory
ENV IDEAS_HISTORY_FILE=/app/data/ideas_history.json

# Run the agent
CMD ["python", "-u", "agent.py"]
