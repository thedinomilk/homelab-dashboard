#!/bin/bash
set -e

# Logging helper
log() {
  echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1"
}

# Directory where the application is deployed
DEPLOY_DIR="/opt/homelab-dashboard"

# Create deployment directory if it doesn't exist
if [ ! -d "$DEPLOY_DIR" ]; then
  log "Creating deployment directory at $DEPLOY_DIR"
  mkdir -p "$DEPLOY_DIR"
  cd "$DEPLOY_DIR"
  git clone https://github.com/thedinomilk/homelab-dashboard.git .
else
  log "Pulling latest changes from GitHub"
  cd "$DEPLOY_DIR"
  git pull
fi

# Make sure we have the latest dependencies
log "Checking for docker and docker-compose"
if ! command -v docker &> /dev/null; then
  log "ERROR: Docker is not installed. Please install Docker first."
  exit 1
fi

if ! command -v docker-compose &> /dev/null; then
  log "ERROR: Docker Compose is not installed. Please install Docker Compose first."
  exit 1
fi

# Deploy with Docker Compose
log "Deploying the application with Docker Compose"
docker-compose down || true
docker-compose build --no-cache
docker-compose up -d

log "Deployment completed successfully!"
log "Your application is now running at http://$(hostname -I | awk '{print $1}'):5000"