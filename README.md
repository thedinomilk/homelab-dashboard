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

### Option 3: Manual Deployment

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
4. Deploy with Docker Compose:
   ```bash
   docker-compose up -d
   ```
5. Access the application at `http://your-server-ip:5000`

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

- `DATABASE_URL`: PostgreSQL connection string
- `SESSION_SECRET`: Secret key for session management

## License

This project is licensed under the MIT License - see the LICENSE file for details.# This file intentionally modified to trigger a refresh
