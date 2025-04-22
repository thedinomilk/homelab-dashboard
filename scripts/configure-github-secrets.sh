#!/bin/bash

# Script to help configure GitHub Secrets for homelab-dashboard
# Requires the GitHub CLI (gh) to be installed and authenticated

echo "Homelab Dashboard - GitHub Secrets Configuration Helper"
echo "====================================================="
echo "This script will help you set up GitHub Secrets for deployment."
echo "You need to have the GitHub CLI (gh) installed and authenticated."
echo ""

# Check if gh CLI is installed
if ! command -v gh &> /dev/null; then
    echo "Error: GitHub CLI (gh) is not installed."
    echo "Please install it from: https://cli.github.com/"
    exit 1
fi

# Check if authenticated
if ! gh auth status &> /dev/null; then
    echo "Error: You are not authenticated with GitHub CLI."
    echo "Please run 'gh auth login' first."
    exit 1
fi

# Get repository
current_repo=$(gh repo view --json nameWithOwner -q .nameWithOwner 2>/dev/null)
if [ -z "$current_repo" ]; then
    echo "Enter your GitHub repository name (e.g., username/homelab-dashboard):"
    read repo_name
else
    echo "Using current repository: $current_repo"
    repo_name=$current_repo
fi

echo ""
echo "Setting up secrets for repository: $repo_name"
echo ""

# Helper function to set a secret
set_secret() {
    local name=$1
    local prompt=$2
    local default=$3
    local is_file=${4:-false}

    echo "$prompt"
    if [ -n "$default" ]; then
        echo -n "[$default]: "
    fi
    
    # For non-file inputs, read directly
    if [ "$is_file" = false ]; then
        read -r value
        if [ -z "$value" ] && [ -n "$default" ]; then
            value=$default
        fi
        
        if [ -n "$value" ]; then
            echo "Setting secret: $name"
            echo -n "$value" | gh secret set "$name" -R "$repo_name"
            echo "✓ Secret $name set successfully."
        fi
    else
        # For file inputs, read the file path and then set the secret from the file
        read -r file_path
        if [ -z "$file_path" ] && [ -n "$default" ]; then
            file_path=$default
        fi
        
        if [ -n "$file_path" ]; then
            if [ -f "$file_path" ]; then
                echo "Setting secret: $name from file $file_path"
                gh secret set "$name" -R "$repo_name" < "$file_path"
                echo "✓ Secret $name set successfully from file."
            else
                echo "Error: File $file_path not found."
            fi
        fi
    fi
    
    echo ""
}

echo "SSH Access Configuration"
echo "========================"
set_secret "SSH_PRIVATE_KEY" "Enter the path to your SSH private key file:" "$HOME/.ssh/id_rsa" true
set_secret "HOMELAB_HOST" "Enter your homelab server IP or hostname:" ""
set_secret "HOMELAB_USER" "Enter your homelab server username:" "$USER"

echo "Proxmox Configuration"
echo "====================="
set_secret "PROXMOX_HOST" "Enter your Proxmox host (IP or hostname):" ""
set_secret "PROXMOX_USER" "Enter your Proxmox username (usually user@pam):" ""
set_secret "PROXMOX_TOKEN_NAME" "Enter your Proxmox API token name:" ""
set_secret "PROXMOX_TOKEN_VALUE" "Enter your Proxmox API token value:" ""

echo "Docker Configuration"
echo "===================="
set_secret "DOCKER_HOST" "Enter your Docker host (IP or hostname):" ""
set_secret "DOCKER_PORT" "Enter your Docker port:" "2375"

echo "Portainer Configuration (Optional)"
echo "================================="
echo "Do you want to set up Portainer integration? (y/n)"
read -r setup_portainer
if [[ "$setup_portainer" =~ ^[Yy] ]]; then
    echo "Portainer API Access (Option 1)"
    set_secret "PORTAINER_URL" "Enter your Portainer URL (e.g., http://localhost:9000):" ""
    set_secret "PORTAINER_USERNAME" "Enter your Portainer username:" "admin"
    set_secret "PORTAINER_PASSWORD" "Enter your Portainer password:" ""
    set_secret "STACK_NAME" "Enter your Portainer stack name:" "homelab-dashboard"
    
    echo "Portainer Webhook (Option 2)"
    set_secret "PORTAINER_WEBHOOK_URL" "Enter your Portainer webhook URL (leave empty if not using):" ""
fi

echo "Flask Configuration"
echo "=================="
# Generate a random secret key
random_key=$(LC_ALL=C tr -dc 'A-Za-z0-9!#$%&()*+,-./:;<=>?@[\]^_`{|}~' </dev/urandom | head -c 32)
set_secret "SECRET_KEY" "Enter your Flask secret key (or press Enter for random):" "$random_key"

# Generate another random key for sessions
random_session=$(LC_ALL=C tr -dc 'A-Za-z0-9!#$%&()*+,-./:;<=>?@[\]^_`{|}~' </dev/urandom | head -c 32)
set_secret "SESSION_SECRET" "Enter your Flask session secret key (or press Enter for random):" "$random_session"

set_secret "DATABASE_URL" "Enter your PostgreSQL database URL:" "postgresql://user:password@localhost:5432/homelab"

echo "GitHub Configuration (Optional)"
echo "=============================="
echo "Do you want to set up GitHub API integration? (y/n)"
read -r setup_github
if [[ "$setup_github" =~ ^[Yy] ]]; then
    set_secret "GITHUB_TOKEN_ENV" "Enter your GitHub personal access token:" ""
fi

echo ""
echo "Configuration complete! Your GitHub Secrets have been set up."
echo "You can now push to your repository or manually trigger the workflow to deploy."
echo ""
echo "To manually trigger the workflow:"
echo "1. Go to your repository on GitHub"
echo "2. Click on 'Actions'"
echo "3. Select the 'Deploy to Homelab' workflow"
echo "4. Click 'Run workflow'"
echo ""