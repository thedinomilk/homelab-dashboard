#!/bin/bash
set -e

# This script tests your GitHub workflow locally
# It simulates the GitHub Actions environment but uses .env.local for secrets

echo "Homelab Dashboard - GitHub Workflow Test"
echo "========================================"
echo "This script will test your GitHub workflow locally."
echo "Make sure you have .env.local file with your secrets."
echo ""

# Check if .env.local exists
if [ ! -f ".env.local" ]; then
    echo "Error: .env.local file not found."
    echo "Please create a .env.local file with your secrets."
    echo "You can use .env.template as a template."
    exit 1
fi

# Load variables from .env.local
echo "Loading variables from .env.local..."
set -a
source .env.local
set +a

# Create temporary .env file
echo "Creating temporary .env file for deployment..."
cp .env.local .env.deploy

# Check for SSH key
SSH_KEY_PATH=""
if [ -f "$HOME/.ssh/id_rsa" ]; then
    SSH_KEY_PATH="$HOME/.ssh/id_rsa"
    echo "Using SSH key from $SSH_KEY_PATH"
else
    echo "No SSH key found at $HOME/.ssh/id_rsa"
    read -p "Enter path to your SSH private key: " SSH_KEY_PATH
    if [ ! -f "$SSH_KEY_PATH" ]; then
        echo "Error: SSH key not found at $SSH_KEY_PATH"
        exit 1
    fi
fi

# Check for required variables
REQUIRED_VARS=("HOMELAB_HOST" "HOMELAB_USER" "PROXMOX_HOST" "PROXMOX_USER" 
               "PROXMOX_TOKEN_NAME" "PROXMOX_TOKEN_VALUE" "DOCKER_HOST" "DOCKER_PORT")

for var in "${REQUIRED_VARS[@]}"; do
    if [ -z "${!var}" ]; then
        echo "Error: Required variable $var is not set in .env.local"
        exit 1
    fi
done

echo "All required variables are set."

# Test SSH connection
echo "Testing SSH connection to $HOMELAB_USER@$HOMELAB_HOST..."
if ! ssh -i "$SSH_KEY_PATH" -o BatchMode=yes -o ConnectTimeout=5 "$HOMELAB_USER@$HOMELAB_HOST" echo "SSH connection successful"; then
    echo "Error: SSH connection failed."
    echo "Make sure your SSH key is valid and the server is reachable."
    exit 1
fi

# Create deployment directory on homelab server
echo "Creating deployment directory on homelab server..."
ssh -i "$SSH_KEY_PATH" "$HOMELAB_USER@$HOMELAB_HOST" "mkdir -p ~/homelab-dashboard"

# Copy .env file to homelab server
echo "Copying .env file to homelab server..."
scp -i "$SSH_KEY_PATH" .env.deploy "$HOMELAB_USER@$HOMELAB_HOST:~/homelab-dashboard/.env"

# Test Portainer connection if webhook or API credentials are provided
if [ ! -z "$PORTAINER_WEBHOOK_URL" ]; then
    echo "Testing Portainer webhook..."
    echo "Note: This will trigger an actual update of your stack."
    read -p "Do you want to continue? (y/n): " TRIGGER_WEBHOOK
    if [[ "$TRIGGER_WEBHOOK" =~ ^[Yy] ]]; then
        echo "Triggering Portainer webhook..."
        curl -s -X POST "$PORTAINER_WEBHOOK_URL"
        echo "Webhook triggered."
    else
        echo "Webhook test skipped."
    fi
elif [ ! -z "$PORTAINER_URL" ] && [ ! -z "$PORTAINER_USERNAME" ] && [ ! -z "$PORTAINER_PASSWORD" ]; then
    echo "Testing Portainer API connection..."
    echo "Logging in to Portainer..."
    AUTH_RESPONSE=$(curl -s -X POST "${PORTAINER_URL}/api/auth" \
      -H "Content-Type: application/json" \
      -d "{\"username\":\"${PORTAINER_USERNAME}\",\"password\":\"${PORTAINER_PASSWORD}\"}")

    JWT=$(echo ${AUTH_RESPONSE} | grep -o '"jwt":"[^"]*' | cut -d'"' -f4)

    if [ -z "${JWT}" ]; then
      echo "Failed to get authentication token from Portainer."
      echo "Response: ${AUTH_RESPONSE}"
      exit 1
    fi

    echo "Successfully authenticated with Portainer."
    echo "API connection is working correctly."
else
    echo "No Portainer webhook URL or API credentials provided in .env.local."
    echo "Skipping Portainer connection test."
fi

echo ""
echo "Test completed successfully!"
echo "Your GitHub workflow should work with the configured secrets."
echo ""
echo "Next steps:"
echo "1. Add the secrets to your GitHub repository"
echo "2. Push your changes to trigger the GitHub workflow"
echo "3. Check that the deployment worked correctly"
echo ""
echo "Cleaning up..."
rm .env.deploy

exit 0