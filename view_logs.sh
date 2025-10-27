#!/bin/bash

# View agent logs
# Usage:
#   ./view_logs.sh           - View all logs
#   ./view_logs.sh tail      - Follow live logs
#   ./view_logs.sh rejected  - Show only rejected ideas
#   ./view_logs.sh found     - Show only found ideas

case "$1" in
    tail)
        echo "[LOGS] Streaming live logs (Ctrl+C to stop)..."
        tail -f agent.log 2>/dev/null || echo "[WARN] Log file not found. Agent has not started logging yet."
        ;;
    rejected)
        echo "=== REJECTED IDEAS ==="
        grep "\[REJECTED\]" agent.log 2>/dev/null || echo "[INFO] No rejected ideas logged yet."
        ;;
    found)
        echo "=== FOUND IDEAS ==="
        grep "\[APPROVED\]" agent.log 2>/dev/null || echo "[INFO] No promising ideas found yet."
        ;;
    *)
        echo "=== AGENT LOGS ==="
        cat agent.log 2>/dev/null || echo "[WARN] Log file not found. Agent has not started yet."
        ;;
esac
