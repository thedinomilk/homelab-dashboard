# Deployment Guide for Homelab Dashboard

This guide explains how to deploy the Homelab Dashboard application to your server using GitHub Actions and Portainer.

## Prerequisites

1. A GitHub repository with this code pushed to it
2. A Docker host with Portainer installed (e.g., http://192.168.86.40:9000)
3. PostgreSQL database already set up (see `docs/postgres-cicd-setup.md`)
4. SSH access to your Docker host

## Setting Up GitHub Secrets

You need to set up the following secrets in your GitHub repository:

1. Go to your GitHub repository
2. Click on "Settings" > "Secrets and variables" > "Actions"
3. Add the following secrets:

### Homelab Configuration
- `HOMELAB_HOST`: Your server's IP address or hostname (e.g., 192.168.86.40)
- `HOMELAB_USER`: Your SSH username (e.g., dinomilk)
- `SSH_PRIVATE_KEY`: Your SSH private key for accessing the server

### Portainer Configuration
- `PORTAINER_URL`: URL of your Portainer instance (e.g., http://192.168.86.40:9000)
- `PORTAINER_API_KEY`: API key from Portainer (generate from user settings)

### Proxmox Configuration
- `PROXMOX_HOST`: Your Proxmox host address (e.g., 192.168.86.100)
- `PROXMOX_USER`: Your Proxmox username (e.g., root@pam)
- `PROXMOX_TOKEN_NAME`: Name of your Proxmox API token
- `PROXMOX_TOKEN_VALUE`: Value of your Proxmox API token

### Docker Configuration
- `DOCKER_HOST`: Your Docker host address (e.g., 192.168.86.40)
- `DOCKER_PORT`: Docker API port (usually 2375)

### Database Configuration
- `DATABASE_URL`: PostgreSQL connection URL (e.g., postgresql://postgres:password@192.168.86.40:5432/homelab)

### Flask Configuration
- `SECRET_KEY`: A random string for Flask's secret key
- `SESSION_SECRET`: A random string for session encryption

### Optional Configuration
- `GITHUB_TOKEN`: GitHub personal access token for GitHub API integration

## Deploying the Application

Once you've set up all the secrets, you can deploy the application using GitHub Actions:

### Method 1: Automatic Deployment

The application will automatically deploy whenever you push to the main branch.

### Method 2: Manual Deployment

1. Go to your GitHub repository
2. Click on "Actions"
3. Select the "Deploy to Homelab" workflow
4. Click "Run workflow" and choose the main branch
5. Click "Run workflow" to start the deployment

## Checking Deployment Status

1. Go to the Actions tab in your GitHub repository
2. Click on the latest "Deploy to Homelab" workflow run
3. Check the logs to see if the deployment was successful

## Accessing the Application

After deployment, you can access the application at:

```
http://YOUR_SERVER_IP:5000
```

For example: http://192.168.86.40:5000

## Troubleshooting

### Issues with SSH Connection
- Ensure your SSH private key is correctly formatted
- Verify that your SSH user has permission to access the server

### Issues with Portainer
- Verify that your Portainer API key has not expired
- Check that your Portainer URL is accessible from GitHub Actions

### Issues with the Application
- Check the container logs in Portainer
- Ensure all environment variables are correctly set
- Verify that the PostgreSQL database is accessible