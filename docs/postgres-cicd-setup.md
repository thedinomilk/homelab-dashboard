# PostgreSQL Database CI/CD Setup with Portainer

This guide explains how to set up PostgreSQL using Portainer with a proper CI/CD pipeline.

## Prerequisites

1. A GitHub repository for your homelab infrastructure
2. A Portainer instance running on your homelab (http://192.168.86.40:9000)
3. GitHub Actions enabled on your repository

## Setting Up GitHub Secrets

You'll need to add the following secrets to your GitHub repository:

1. `PORTAINER_URL` - The URL of your Portainer instance (e.g., http://192.168.86.40:9000)
2. `PORTAINER_API_KEY` - An API key generated from Portainer
3. `POSTGRES_USER` - Database username (e.g., postgres)
4. `POSTGRES_PASSWORD` - A secure password for your database
5. `POSTGRES_DB` - Database name (e.g., homelab)
6. `SSH_PRIVATE_KEY` - SSH private key for accessing your server

### How to Generate a Portainer API Key

1. Log in to your Portainer instance
2. Click on your username in the bottom-left corner
3. Select "Account Settings"
4. In the "Access tokens" section, click "Add access token"
5. Give it a name like "GitHub Actions"
6. Set an appropriate expiry time (or none for permanent access)
7. Click "Add access token" and copy the generated token

## How It Works

The CI/CD pipeline works as follows:

1. When you push changes to `docker-compose.portainer-postgres.yml` in the main branch, the GitHub Action triggers
2. The action creates an environment file with your database credentials
3. It then connects to your Portainer instance using the API key
4. It checks if a PostgreSQL stack already exists:
   - If it doesn't exist, it creates a new stack
   - If it exists, it updates the existing stack
5. The changes are applied to your Portainer deployment

## Initial Deployment

For the initial deployment:

1. Push the repository with the workflow and docker-compose file
2. Go to GitHub Actions in your repository
3. Run the "Deploy PostgreSQL Database" workflow manually using the "workflow_dispatch" event

## Testing the Connection

After deployment, you can test the connection to your PostgreSQL database:

```bash
psql postgresql://postgres:your_password@192.168.86.40:5432/homelab
```

## Using with Your Application

Update your application's environment variables to use the PostgreSQL database:

```
DATABASE_URL=postgresql://postgres:your_password@192.168.86.40:5432/homelab
```

Add this to your GitHub Secrets for the main application deployment as well.