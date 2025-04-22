#!/bin/bash
# Simple script to run the webhook listener directly (without systemd)

# Default values - change these as needed
WEBHOOK_SECRET="your_webhook_secret"
WEBHOOK_PORT=8555
REPO_PATH="$HOME/homelab-dashboard"
GITHUB_REPO="thedinomilk/homelab-dashboard"

# Export environment variables
export WEBHOOK_SECRET
export WEBHOOK_PORT
export REPO_PATH
export GITHUB_REPO

# Run the webhook listener
echo "Starting webhook listener on port $WEBHOOK_PORT..."
echo "Press Ctrl+C to stop"
echo ""
echo "GitHub webhook should be configured with:"
echo "  - Payload URL: http://your-homelab-ip:$WEBHOOK_PORT/webhook"
echo "  - Content type: application/json"
echo "  - Secret: $WEBHOOK_SECRET"
echo "  - Events: Just the push event"
echo ""

# Run the webhook listener script
python3 $(dirname "$0")/webhook-listener.py