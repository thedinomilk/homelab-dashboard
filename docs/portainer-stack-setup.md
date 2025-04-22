# Setting Up a Portainer Stack for Homelab Dashboard

This guide will walk you through creating a stack in your existing Portainer installation for the Homelab Dashboard application.

## Prerequisites
- Portainer installed and running on your homelab
- Access to the Portainer web interface
- GitHub repository for your homelab dashboard

## Steps to Create a Portainer Stack

### 1. Log in to Portainer Web Interface
- Open your web browser and navigate to your Portainer instance (e.g., http://your-server-ip:9000)
- Log in with your Portainer credentials

### 2. Access Stacks
- In the left sidebar, click on "Stacks"
- Click the "Add stack" button

### 3. Configure Stack Using Git Repository
- For **Name**, enter: `homelab-dashboard`
- For **Build method**, select: `Git repository`
- For **Repository URL**, enter: `https://github.com/yourusername/homelab-dashboard.git`
- For **Repository reference**, enter: `main` (or your preferred branch)
- For **Compose path**, enter: `docker-compose.portainer.yml`

### 4. Set Environment Variables
- In the **Environment variables** section, click "Add environment variable" to add each of the following:
  - `PROXMOX_HOST` = your Proxmox host IP
  - `PROXMOX_USER` = your Proxmox username
  - `PROXMOX_TOKEN_NAME` = your Proxmox token name
  - `PROXMOX_TOKEN_VALUE` = your Proxmox token value
  - `DOCKER_HOST` = your Docker host IP
  - `DOCKER_PORT` = your Docker port (usually 2375)
  - `SECRET_KEY` = a random secure string
  - `SESSION_SECRET` = another random secure string
  - `DATABASE_URL` = your PostgreSQL connection string
  - `GITHUB_TOKEN` = your GitHub token (if using GitHub integration)

### 5. Deploy the Stack
- Click the "Deploy the stack" button
- Wait for the deployment to complete

### 6. Get Stack Webhook URL (For GitHub Actions)
- After the stack is deployed, click on the stack name
- Look for the "Webhooks" section
- Click "Add webhook"
- Enter a name like "github-actions-deploy"
- Click "Create webhook"
- Copy the generated webhook URL - you'll need this for your GitHub Secrets

### 7. Access Your Dashboard
- Once deployed, your homelab dashboard will be accessible at: http://your-server-ip:5000

## Setting Up Automatic Updates

To enable automatic updates using GitHub Actions:

1. Add the webhook URL you copied to your GitHub repository as a secret named `PORTAINER_WEBHOOK_URL`
2. When you push changes to your GitHub repository, the GitHub Action will trigger this webhook
3. Portainer will automatically pull the latest changes and redeploy your stack

## Additional Configuration

You can further customize your deployment by:
- Modifying the docker-compose.portainer.yml file to add more services
- Adding volume mappings for persistent data
- Setting up a reverse proxy to add HTTPS support
- Configuring auto-restart policies for your containers