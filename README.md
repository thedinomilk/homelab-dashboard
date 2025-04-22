# Homelab Dashboard

A comprehensive homelab management platform designed to simplify infrastructure monitoring, storage management, and container orchestration across multiple services.

## Features

- Proxmox resource monitoring
- Docker container management
- ZFS storage array tracking
- SSH/SFTP file transfer capabilities
- Cross-platform system administration tools
- Media request system for content downloads

## Deployment Instructions

### Prerequisites

- Docker and Docker Compose installed on your homelab server
- Git installed on your homelab server
- A server with at least 1GB RAM and 10GB free disk space

### Option 1: Portainer Deployment (Recommended)

If you're already using Portainer to manage Docker containers:

1. In Portainer, go to "Stacks" in the left menu
2. Click "Add stack"
3. Give it a name like "homelab-dashboard"
4. For "Build method" select "Git repository"
5. For "Repository URL" enter: `https://github.com/thedinomilk/homelab-dashboard.git`
6. For "Repository reference" enter: `main`
7. For "Compose path" enter: `docker-compose.yml`
   - Or use `docker-compose.portainer.yml` if you want to use an existing database
8. Set environment variables:
   - `DATABASE_URL`: Your PostgreSQL connection string (if using external database)
   - `SESSION_SECRET`: A secure random string for session security
9. Click "Deploy the stack"
10. Access the application at `http://your-server-ip:5000`

### Option 2: Automatic Deployment

1. SSH into your homelab server
2. Download the deployment script:
   ```bash
   curl -o deploy.sh https://raw.githubusercontent.com/thedinomilk/homelab-dashboard/main/update.sh
   chmod +x deploy.sh
   ```
3. Run the deployment script:
   ```bash
   ./deploy.sh
   ```
4. Access the application at `http://your-server-ip:5000`

### Option 3: GitHub Actions Automated Deployment (Recommended)

This method uses GitHub Secrets and GitHub Actions to securely manage credentials and automate deployment to your Portainer stack. 

> **Note:** If you haven't created a Portainer stack yet, follow the detailed guide at [docs/portainer-stack-setup.md](docs/portainer-stack-setup.md).

1. Fork or clone this repository to your own GitHub account

2. **Option A: Use the Configuration Helper Script (Recommended)**
   
   ```bash
   # Clone your repo
   git clone https://github.com/yourusername/homelab-dashboard.git
   cd homelab-dashboard
   
   # Run the configuration script
   ./scripts/configure-github-secrets.sh
   ```
   
   The script will guide you through setting up all necessary GitHub Secrets.

3. **Option B: Manual Setup**
   
   Go to your repository's Settings > Secrets and variables > Actions
   Manually add the following repository secrets:

   **Required Secrets:**
   - `SSH_PRIVATE_KEY`: Your private SSH key for accessing the homelab server
   - `HOMELAB_HOST`: IP or hostname of your homelab server
   - `HOMELAB_USER`: Username for SSH access to your server
   - `PROXMOX_HOST`: IP/hostname of your Proxmox server
   - `PROXMOX_USER`: Proxmox username (usually in format user@pam)
   - `PROXMOX_TOKEN_NAME`: API token name for Proxmox
   - `PROXMOX_TOKEN_VALUE`: API token value for Proxmox
   - `DOCKER_HOST`: IP/hostname of your Docker host
   - `DOCKER_PORT`: Port for Docker API (usually 2375)
   - `SECRET_KEY`: Flask application secret key
   - `SESSION_SECRET`: Flask session secret
   - `DATABASE_URL`: PostgreSQL database connection string

   **Optional Portainer Integration:**
   - `PORTAINER_URL`: URL to your Portainer instance
   - `PORTAINER_USERNAME`: Portainer admin username
   - `PORTAINER_PASSWORD`: Portainer admin password
   - `STACK_NAME`: Name of your stack in Portainer
   
   **Alternative Portainer Integration:**
   - `PORTAINER_WEBHOOK_URL`: Webhook URL for your Portainer stack

4. Push to the main branch or manually trigger the "Deploy to Homelab" workflow
5. The GitHub Action will:
   - Create a secure .env file with your credentials
   - Copy it to your homelab server
   - Update your Portainer stack with the latest code

6. Access the application at `http://your-server-ip:5000`

### Option 4: Manual Deployment

1. SSH into your homelab server
2. Create a deployment directory:
   ```bash
   mkdir -p /opt/homelab-dashboard
   cd /opt/homelab-dashboard
   ```
3. Clone the repository:
   ```bash
   git clone https://github.com/thedinomilk/homelab-dashboard.git .
   ```
4. Create a `.env` file with your configuration (see below)
5. Deploy with Docker Compose:
   ```bash
   docker-compose up -d
   ```
6. Access the application at `http://your-server-ip:5000`

### Setup Automated Updates (Optional)

To automatically update the application with the latest code from GitHub:

1. Add a cron job to periodically run the update script:
   ```bash
   crontab -e
   ```
2. Add the following line to check for updates every hour:
   ```
   0 * * * * /opt/homelab-dashboard/update.sh >> /opt/homelab-dashboard/update.log 2>&1
   ```

## Configuration

### Environment Variables

#### Required Variables
- `DATABASE_URL`: PostgreSQL connection string
- `SESSION_SECRET`: Secret key for session management
- `PROXMOX_HOST`: Hostname or IP address of your Proxmox server
- `PROXMOX_USER`: Username for Proxmox API access
- `PROXMOX_TOKEN_NAME`: API token name for Proxmox
- `PROXMOX_TOKEN_VALUE`: API token value for Proxmox
- `DOCKER_HOST`: Hostname or IP address of your Docker server
- `DOCKER_PORT`: Port for Docker API access (typically 2375)
- `GITHUB_TOKEN`: GitHub personal access token (if using GitHub integration)

#### Using .env File

You can create a `.env` file in the root directory with these variables:

```
# Proxmox configuration
PROXMOX_HOST=your_proxmox_ip
PROXMOX_USER=your_proxmox_username
PROXMOX_TOKEN_NAME=your_proxmox_token_name
PROXMOX_TOKEN_VALUE=your_proxmox_token_value

# Docker configuration
DOCKER_HOST=your_docker_host_ip
DOCKER_PORT=2375

# GitHub configuration
GITHUB_TOKEN=your_github_token

# Flask configuration
FLASK_ENV=production
SECRET_KEY=your_random_secret_key
```

When deploying in Portainer, make sure to:
1. Upload the `.env` file to your server
2. Update your stack configuration to use this file with `env_file: .env`

## Setting Up GitHub Secrets

For using GitHub Actions deployment, you need to set up these secrets in your GitHub repository:

### Method 1: Using the Helper Script (Recommended)

1. Clone your repository:
   ```bash
   git clone https://github.com/yourusername/homelab-dashboard.git
   cd homelab-dashboard
   ```

2. Make the helper script executable:
   ```bash
   chmod +x scripts/configure-github-secrets.sh
   ```

3. Run the helper script:
   ```bash
   ./scripts/configure-github-secrets.sh
   ```

4. Follow the prompts to set up your secrets.

### Method 2: Manual Configuration

1. Go to your GitHub repository on GitHub.com
2. Click on "Settings" tab
3. In the left sidebar, click on "Secrets and variables" then "Actions"
4. Click on "New repository secret" to add each of the following secrets:

| Secret Name | Description | Example |
|-------------|-------------|---------|
| `SSH_PRIVATE_KEY` | Your private SSH key for server access | Contents of `~/.ssh/id_rsa` |
| `HOMELAB_HOST` | Hostname or IP of your homelab server | `192.168.1.100` |
| `HOMELAB_USER` | Username for SSH access to your server | `username` |
| `PROXMOX_HOST` | Hostname or IP of your Proxmox server | `192.168.1.10` |
| `PROXMOX_USER` | Proxmox API username | `user@pam` |
| `PROXMOX_TOKEN_NAME` | Proxmox API token name | `github-deploy` |
| `PROXMOX_TOKEN_VALUE` | Proxmox API token value | `xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx` |
| `DOCKER_HOST` | Hostname or IP of your Docker server | `192.168.1.20` |
| `DOCKER_PORT` | Port for Docker API access | `2375` |
| `SECRET_KEY` | Flask secret key | Random string |
| `SESSION_SECRET` | Flask session secret key | Random string |
| `DATABASE_URL` | PostgreSQL database URL | `postgresql://user:pass@host:5432/db` |
| `PORTAINER_URL` | URL to your Portainer instance | `http://192.168.1.20:9000` |
| `PORTAINER_USERNAME` | Portainer admin username | `admin` |
| `PORTAINER_PASSWORD` | Portainer admin password | Your password |
| `STACK_NAME` | Name of your Portainer stack | `homelab-dashboard` |
| `PORTAINER_WEBHOOK_URL` | Webhook URL for stack updates | `http://192.168.1.20:9000/api/webhooks/...` |
| `GITHUB_TOKEN_ENV` | GitHub API token | `ghp_...` |

## License

This project is licensed under the MIT License - see the LICENSE file for details.
