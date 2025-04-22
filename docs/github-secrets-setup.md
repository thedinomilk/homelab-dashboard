# GitHub Secrets Setup for Homelab Dashboard

This document provides instructions on how to set up GitHub Secrets for your Homelab Dashboard deployment. GitHub Secrets are used to store sensitive information such as API keys, passwords, and connection strings, which can then be securely used in GitHub Actions workflows without exposing them in your codebase.

## Why Use GitHub Secrets?

GitHub Secrets provide several advantages for your homelab deployment:

1. **Centralized Secret Management**: Store all your sensitive configuration in one secure location
2. **Separation of Code and Configuration**: Keep your code repository clean without sensitive data
3. **Automated Deployments**: Enable secure CI/CD pipelines that can deploy to your homelab
4. **Version Independence**: Update configuration without changing code
5. **Role-Based Access**: Only repository admins can manage secrets

## Required Secrets

The following secrets are required for the deployment workflow:

### SSH Access
- `SSH_PRIVATE_KEY`: Your private SSH key for accessing the homelab server
- `HOMELAB_HOST`: The IP address or hostname of your homelab server
- `HOMELAB_USER`: The username for SSH access to your homelab server

### Proxmox Configuration
- `PROXMOX_HOST`: Your Proxmox host (IP or hostname)
- `PROXMOX_USER`: Your Proxmox username (usually in format user@pam)
- `PROXMOX_TOKEN_NAME`: Your Proxmox API token name
- `PROXMOX_TOKEN_VALUE`: Your Proxmox API token value

### Docker Configuration
- `DOCKER_HOST`: Your Docker host (IP or hostname)
- `DOCKER_PORT`: Your Docker port (usually 2375 for unencrypted or 2376 for TLS)

### Portainer Configuration (Optional)
Either use API access:
- `PORTAINER_URL`: Your Portainer URL (e.g., http://localhost:9000)
- `PORTAINER_USERNAME`: Your Portainer username
- `PORTAINER_PASSWORD`: Your Portainer password
- `STACK_NAME`: Your Portainer stack name (default: homelab-dashboard)

Or use webhook:
- `PORTAINER_WEBHOOK_URL`: Your Portainer webhook URL

### Flask Configuration
- `SECRET_KEY`: A random secret key for Flask
- `SESSION_SECRET`: A random secret key for Flask sessions
- `DATABASE_URL`: PostgreSQL database URL

### GitHub Configuration (Optional)
- `GITHUB_TOKEN_ENV`: GitHub personal access token (note: this is different from the built-in GITHUB_TOKEN)

## Setting Up Secrets

You can set up GitHub Secrets in one of the following ways:

### Option 1: Using the GitHub Web Interface

1. Go to your repository on GitHub
2. Click on "Settings" tab
3. In the left sidebar, click on "Secrets and variables" > "Actions"
4. Click on "New repository secret"
5. Enter the name and value of the secret
6. Click "Add secret"
7. Repeat for each secret

### Option 2: Using the GitHub CLI

You can use the GitHub CLI to set up secrets from the command line:

```bash
gh secret set SSH_PRIVATE_KEY < ~/.ssh/id_rsa
gh secret set HOMELAB_HOST --body "192.168.1.100"
# Repeat for other secrets
```

### Option 3: Using the Helper Script

For your convenience, a helper script is provided in the repository:

```bash
# Make the script executable
chmod +x scripts/configure-github-secrets.sh

# Run the script
./scripts/configure-github-secrets.sh
```

The script will:
1. Check if you have the GitHub CLI installed and authenticated
2. Guide you through setting up each required secret
3. Automatically generate random values for secrets like SECRET_KEY if desired

## Testing Your Configuration

You can test your configuration locally before committing to GitHub:

```bash
# Make the script executable
chmod +x scripts/test-github-workflow.sh

# Create a local environment file with your secrets
cp .env.template .env.local
# Edit .env.local with your values

# Run the test script
./scripts/test-github-workflow.sh
```

This script will simulate the GitHub Actions workflow without actually triggering the GitHub CI/CD pipeline, allowing you to verify your configuration works correctly.

## Syncing Secrets Between Replit and GitHub

To ensure that your application uses the same configuration in both Replit and GitHub environments:

1. In Replit, set up the secrets using the Replit Secrets management interface
2. In GitHub, set up the same secrets using one of the methods above
3. Make sure the secret names are identical in both environments
4. Your application code should reference these environment variables directly

For example, in your Python code:

```python
import os

proxmox_host = os.environ.get('PROXMOX_HOST')
proxmox_user = os.environ.get('PROXMOX_USER')
```

This approach ensures that your application will work correctly in both environments without code changes.

## Troubleshooting

If you encounter issues with your GitHub Secrets:

1. Check that all required secrets are defined
2. Verify that secret names match exactly between GitHub and your code
3. For SSH keys, ensure the key is the complete private key including the BEGIN and END lines
4. For URLs, make sure they include the protocol (http:// or https://)
5. Check the GitHub Actions workflow run logs for more detailed error messages

## Security Best Practices

1. Use different tokens with minimal permissions for different environments
2. Regularly rotate secrets and tokens
3. Never commit sensitive information directly in your codebase
4. Use secrets for all sensitive information, even in development
5. Consider using dedicated deployment keys instead of your personal SSH key