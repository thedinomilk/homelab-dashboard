# Setting Up PostgreSQL with Portainer and CI/CD

This guide will walk you through setting up a PostgreSQL database for your homelab dashboard using Portainer and GitHub Actions for CI/CD.

## Prerequisites

1. Portainer running on your Docker host (http://192.168.86.40:9000)
2. GitHub repository with GitHub Actions enabled
3. SSH access to your Docker host

## Step 1: Set Up GitHub Secrets

You'll need to add these secrets to your GitHub repository:

1. Go to your GitHub repository
2. Click on "Settings" > "Secrets and variables" > "Actions"
3. Add the following secrets:

| Secret Name | Description | Example Value |
|-------------|-------------|---------------|
| `PORTAINER_URL` | URL of your Portainer instance | `http://192.168.86.40:9000` |
| `PORTAINER_API_KEY` | API key from Portainer | (Generated from Portainer) |
| `POSTGRES_USER` | Database username | `postgres` |
| `POSTGRES_PASSWORD` | Database password | `secure_password` |
| `POSTGRES_DB` | Database name | `homelab` |
| `SSH_PRIVATE_KEY` | SSH key to access your server | (Your private SSH key) |

## Step 2: Generate a Portainer API Key

1. Log in to your Portainer instance
2. Click on your username in the bottom-left corner
3. Select "Account Settings"
4. In the "Access tokens" section, click "Add access token"
5. Give it a name (e.g., "GitHub Actions")
6. Set an appropriate expiry time (or leave blank for no expiry)
7. Click "Add access token" and copy the generated token
8. Add this token as the `PORTAINER_API_KEY` secret in GitHub

## Step 3: Run the PostgreSQL Deployment Workflow

Once you've set up the secrets:

1. Go to your GitHub repository's "Actions" tab
2. Find the "Deploy PostgreSQL Database" workflow
3. Click "Run workflow" on the main branch
4. This will deploy PostgreSQL to your Portainer instance

## Step 4: Verify the Deployment

After the workflow runs:

1. Log in to your Portainer instance
2. Go to "Stacks" in the left sidebar
3. You should see a "homelab-postgres" stack
4. Click on it to view details and ensure it's running

## Step 5: Get the Database URL

Your PostgreSQL database will be accessible at:

```
postgresql://postgres:your_password@192.168.86.40:5432/homelab
```

Where:
- `postgres` is the username you set in GitHub Secrets
- `your_password` is the password you set in GitHub Secrets
- `192.168.86.40` is your Docker host IP
- `homelab` is the database name you set in GitHub Secrets

## Step 6: Configure Your Application

1. Add the database URL to your application's GitHub Secrets as `DATABASE_URL`
2. Your application will use this secret during deployment

## Step 7: Making Changes to the PostgreSQL Configuration

If you need to make changes to the PostgreSQL configuration:

1. Edit the `docker-compose.portainer-postgres.yml` file
2. Commit and push the changes to your main branch
3. The GitHub Action will automatically update the Portainer stack

## Troubleshooting

If you encounter issues:

1. Check the GitHub Actions logs for error messages
2. Verify that your Portainer API key has the correct permissions
3. Ensure your Docker host is accessible from GitHub Actions
4. Check the Portainer stack logs for any PostgreSQL startup issues

## Advanced Configuration

You can customize your PostgreSQL deployment by modifying:

- Environment variables in `docker-compose.portainer-postgres.yml`
- Volume configurations for data persistence
- Network settings
- PostgreSQL configuration parameters