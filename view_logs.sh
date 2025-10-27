#!/bin/bash

# View agent logs
# Usage:
#   ./view_logs.sh           - View all logs
#   ./view_logs.sh tail      - Follow live logs
#   ./view_logs.sh rejected  - Show only rejected ideas
#   ./view_logs.sh found     - Show only found ideas

case "$1" in
    tail)
        echo "Following live logs (Ctrl+C to stop)..."
        tail -f agent.log 2>/dev/null || echo "No log file yet. Agent hasn't started logging."
        ;;
    rejected)
        echo "=== REJECTED IDEAS ==="
        grep "REJECTED:" agent.log 2>/dev/null || echo "No rejections logged yet."
        ;;
    found)
        echo "=== FOUND IDEAS ==="
        grep "FOUND PROMISING IDEA:" agent.log 2>/dev/null || echo "No promising ideas found yet."
        ;;
    *)
        echo "=== AGENT LOGS ==="
        cat agent.log 2>/dev/null || echo "No log file yet. Agent hasn't started."
        ;;
esac
