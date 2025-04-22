#!/bin/bash
# Create a static .env file for testing purposes
# This file will be executed by GitHub Actions

cat <<EOT > .env
PROXMOX_HOST=192.168.86.100
PROXMOX_USER=root@pam
PROXMOX_TOKEN_NAME=github-actions
PROXMOX_TOKEN_VALUE=dummy-value

DOCKER_HOST=192.168.86.40
DOCKER_PORT=2375

DATABASE_URL=postgresql://postgres:postgres@192.168.86.40:5432/homelab

GITHUB_TOKEN=dummy-github-token

FLASK_ENV=production
SECRET_KEY=dummy-secret-key
SESSION_SECRET=dummy-session-secret
EOT

echo "Static .env file created for testing purposes."