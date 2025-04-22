#!/bin/bash
# This script installs the webhook listener as a systemd service

set -e

# Default values
USERNAME=$(whoami)
WEBHOOK_SECRET=${WEBHOOK_SECRET:-"generate_a_strong_secret"}
WEBHOOK_PORT=${WEBHOOK_PORT:-8555}
REPO_PATH=${REPO_PATH:-"$HOME/homelab-dashboard"}
GITHUB_REPO=${GITHUB_REPO:-"thedinomilk/homelab-dashboard"}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    --username)
      USERNAME="$2"
      shift 2
      ;;
    --webhook-secret)
      WEBHOOK_SECRET="$2"
      shift 2
      ;;
    --webhook-port)
      WEBHOOK_PORT="$2"
      shift 2
      ;;
    --repo-path)
      REPO_PATH="$2"
      shift 2
      ;;
    --github-repo)
      GITHUB_REPO="$2"
      shift 2
      ;;
    --help)
      echo "Usage: $0 [options]"
      echo "Options:"
      echo "  --username USERNAME        Username to run the service as (default: current user)"
      echo "  --webhook-secret SECRET    Secret token for webhook verification (default: generate_a_strong_secret)"
      echo "  --webhook-port PORT        Port to listen on (default: 8555)"
      echo "  --repo-path PATH           Path to the repository (default: ~/homelab-dashboard)"
      echo "  --github-repo REPO         GitHub repository name (default: thedinomilk/homelab-dashboard)"
      echo "  --help                     Show this help message"
      exit 0
      ;;
    *)
      echo "Unknown option: $1"
      exit 1
      ;;
  esac
done

echo "Installing GitHub webhook listener..."
echo "Username: $USERNAME"
echo "Webhook port: $WEBHOOK_PORT"
echo "Repository path: $REPO_PATH"
echo "GitHub repository: $GITHUB_REPO"

# Create the service file
SERVICE_FILE=/tmp/webhook-listener.service
cat > $SERVICE_FILE << EOF
[Unit]
Description=GitHub Webhook Listener for Homelab Dashboard
After=network.target

[Service]
Type=simple
User=$USERNAME
Group=$USERNAME
WorkingDirectory=$REPO_PATH
ExecStart=/usr/bin/python3 $REPO_PATH/scripts/webhook-listener.py
Restart=always
RestartSec=10
Environment=WEBHOOK_SECRET=$WEBHOOK_SECRET
Environment=WEBHOOK_PORT=$WEBHOOK_PORT
Environment=REPO_PATH=$REPO_PATH
Environment=GITHUB_REPO=$GITHUB_REPO

[Install]
WantedBy=multi-user.target
EOF

# Ensure the log file exists and has proper permissions
sudo touch /var/log/webhook-listener.log
sudo chown $USERNAME:$USERNAME /var/log/webhook-listener.log

# Install the service
echo "Installing systemd service..."
sudo mv $SERVICE_FILE /etc/systemd/system/webhook-listener.service
sudo systemctl daemon-reload
sudo systemctl enable webhook-listener.service
sudo systemctl start webhook-listener.service

echo "Done! The webhook listener is now running on port $WEBHOOK_PORT"
echo "Make sure to configure your GitHub webhook with these settings:"
echo "  Payload URL: http://your-homelab-ip:$WEBHOOK_PORT/webhook"
echo "  Content type: application/json"
echo "  Secret: $WEBHOOK_SECRET"
echo "  Events: Just the push event"
echo ""
echo "To check the status of the service, run:"
echo "  sudo systemctl status webhook-listener.service"
echo ""
echo "To view logs, run:"
echo "  sudo journalctl -u webhook-listener.service -f"
echo "  or"
echo "  tail -f /var/log/webhook-listener.log"