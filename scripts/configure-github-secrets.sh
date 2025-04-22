#!/bin/bash

# This script helps configure all necessary GitHub secrets for deployment

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

# Function to set a GitHub secret
set_secret() {
    local name=$1
    local prompt=$2
    local default_value=$3
    
    echo -e "${YELLOW}$prompt${NC}"
    read -r value
    
    # Use default if empty
    if [ -z "$value" ]; then
        value="$default_value"
        echo "Using default value."
    fi
    
    echo "$value" | gh secret set "$name"
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}Secret '$name' set successfully.${NC}"
    else
        echo -e "${RED}Failed to set secret '$name'. Make sure gh CLI is installed and you're authenticated.${NC}"
        exit 1
    fi
}

# Check if GitHub CLI is installed
if ! command -v gh &> /dev/null; then
    echo -e "${RED}GitHub CLI (gh) is not installed.${NC}"
    echo "Please install it first: https://cli.github.com/manual/installation"
    exit 1
fi

# Check if logged in to GitHub
if ! gh auth status &> /dev/null; then
    echo -e "${RED}You're not logged in to GitHub CLI.${NC}"
    echo "Please login first with: gh auth login"
    exit 1
fi

echo -e "${GREEN}=========================================${NC}"
echo -e "${GREEN}  GitHub Secrets Configuration Helper     ${NC}"
echo -e "${GREEN}=========================================${NC}"
echo ""
echo "This script will help you set up all the necessary GitHub secrets for deployment."
echo ""

echo "Homelab Configuration"
echo "===================="
set_secret "HOMELAB_HOST" "Enter your homelab server IP or hostname (e.g., 192.168.86.40):" ""
set_secret "HOMELAB_USER" "Enter your SSH username:" "$USER"

echo ""
echo "SSH Key Configuration"
echo "===================="
echo -e "${YELLOW}Enter the path to your SSH private key file:${NC}"
read -r ssh_key_path

# Default to ~/.ssh/id_rsa if empty
if [ -z "$ssh_key_path" ]; then
    ssh_key_path="$HOME/.ssh/id_rsa"
    echo "Using default path: $ssh_key_path"
fi

# Check if file exists
if [ ! -f "$ssh_key_path" ]; then
    echo -e "${RED}SSH key file not found at $ssh_key_path${NC}"
    exit 1
fi

# Set SSH private key
cat "$ssh_key_path" | gh secret set SSH_PRIVATE_KEY
if [ $? -eq 0 ]; then
    echo -e "${GREEN}Secret 'SSH_PRIVATE_KEY' set successfully.${NC}"
else
    echo -e "${RED}Failed to set SSH private key.${NC}"
    exit 1
fi

echo ""
echo "Portainer Configuration"
echo "======================"
set_secret "PORTAINER_URL" "Enter your Portainer URL (e.g., http://192.168.86.40:9000):" "http://192.168.86.40:9000"
set_secret "PORTAINER_API_KEY" "Enter your Portainer API key (generate from user settings):" ""

echo ""
echo "Proxmox Configuration"
echo "===================="
set_secret "PROXMOX_HOST" "Enter your Proxmox host (e.g., 192.168.86.100):" "192.168.86.100"
set_secret "PROXMOX_USER" "Enter your Proxmox username (e.g., root@pam):" "root@pam"
set_secret "PROXMOX_TOKEN_NAME" "Enter your Proxmox API token name:" ""
set_secret "PROXMOX_TOKEN_VALUE" "Enter your Proxmox API token value:" ""

echo ""
echo "Docker Configuration"
echo "==================="
set_secret "DOCKER_HOST" "Enter your Docker host (e.g., 192.168.86.40):" "192.168.86.40"
set_secret "DOCKER_PORT" "Enter your Docker port (default: 2375):" "2375"

echo ""
echo "Database Configuration"
echo "====================="
db_default="postgresql://postgres:postgres@192.168.86.40:5432/homelab"
set_secret "DATABASE_URL" "Enter your PostgreSQL connection string:" "$db_default"

echo ""
echo "Flask Configuration"
echo "=================="
# Generate random secret keys
secret_key=$(LC_ALL=C tr -dc 'A-Za-z0-9!#$%&()*+,-./:;<=>?@[\]^_`{|}~' </dev/urandom | head -c 32)
session_secret=$(LC_ALL=C tr -dc 'A-Za-z0-9!#$%&()*+,-./:;<=>?@[\]^_`{|}~' </dev/urandom | head -c 32)

set_secret "SECRET_KEY" "Enter your Flask secret key (or press Enter for random):" "$secret_key"
set_secret "SESSION_SECRET" "Enter your Flask session secret key (or press Enter for random):" "$session_secret"

echo ""
echo "GitHub Configuration (Optional)"
echo "=============================="
echo "Do you want to set up GitHub API integration? (y/n)"
read -r setup_github
if [[ "$setup_github" =~ ^[Yy] ]]; then
    set_secret "GITHUB_TOKEN" "Enter your GitHub personal access token:" ""
fi

echo ""
echo -e "${GREEN}Configuration complete! Your GitHub Secrets have been set up.${NC}"
echo "You can now push to your repository or manually trigger the workflow to deploy."
echo ""
echo "To manually trigger the workflow:"
echo "1. Go to your repository on GitHub"
echo "2. Click on 'Actions'"
echo "3. Select the 'Deploy to Homelab' workflow"
echo "4. Click 'Run workflow'"