# Webhook-Based Deployment Guide

This guide explains how to set up webhook-based deployments for your homelab dashboard, which eliminates the need for direct connections from GitHub to your homelab.

## How It Works

Instead of using GitHub Actions to push changes to your homelab (which requires your homelab to be accessible from the internet), this approach uses a webhook listener that runs directly on your homelab server.

The process works as follows:

1. You push code to your GitHub repository
2. GitHub sends a webhook notification to your homelab server
3. Your webhook listener receives the notification and verifies it's authentic
4. The listener pulls the latest code from GitHub and deploys it using Docker Compose

This approach has several advantages:
- No inbound SSH connections from GitHub to your homelab
- No need to expose your homelab to the internet (except for the webhook port)
- Simpler setup with fewer potential failure points
- More secure as it doesn't require SSH keys in GitHub secrets

## Installation

### Prerequisites

- A Linux server running systemd
- Python 3.6 or higher
- Git installed
- Docker and Docker Compose installed
- Your server must be accessible on the configured webhook port (default: 8555)

### Setup Steps

1. **Clone this repository to your homelab server:**

   ```bash
   git clone https://github.com/thedinomilk/homelab-dashboard.git ~/homelab-dashboard
   cd ~/homelab-dashboard
   ```

2. **Install the webhook listener service:**

   ```bash
   bash scripts/install-webhook-listener.sh --webhook-secret "your_strong_secret_here"
   ```

   You can customize the installation with additional options:
   ```bash
   bash scripts/install-webhook-listener.sh \
     --username your_username \
     --webhook-secret your_strong_secret \
     --webhook-port 8555 \
     --repo-path /path/to/repo \
     --github-repo thedinomilk/homelab-dashboard
   ```

3. **Configure the GitHub webhook:**

   a. Go to your GitHub repository
   b. Click Settings -> Webhooks -> Add webhook
   c. Configure the webhook:
      - Payload URL: `http://your-homelab-ip:8555/webhook`
      - Content type: `application/json`
      - Secret: The same secret you used when installing the service
      - Events: Just the push event
   d. Click "Add webhook"

4. **Test the webhook:**

   a. Make a simple change to your repository and push it to GitHub
   b. GitHub will send a webhook to your server
   c. Your server will pull the latest changes and deploy them

## Troubleshooting

### Checking Service Status

To check if the webhook listener is running:

```bash
sudo systemctl status webhook-listener.service
```

### Viewing Logs

To view the logs:

```bash
# System logs
sudo journalctl -u webhook-listener.service -f

# Application logs
tail -f /var/log/webhook-listener.log
```

### Testing Locally

You can test the webhook handler locally by sending a simulated webhook payload:

```bash
curl -X POST http://localhost:8555/webhook \
  -H "Content-Type: application/json" \
  -H "X-Hub-Signature-256: sha256=YOUR_SIGNATURE" \
  -d '{"ref": "refs/heads/main", "repository": {"full_name": "thedinomilk/homelab-dashboard"}}'
```

### Common Issues

1. **Webhook verification fails**
   - Ensure the secret in GitHub matches the `WEBHOOK_SECRET` in your service configuration.

2. **Service can't pull from GitHub**
   - Ensure your server has internet access and can reach GitHub.
   - If your repository is private, you may need to configure Git credentials.

3. **Port not accessible**
   - Make sure the webhook port (default: 8555) is accessible from GitHub's servers.
   - Check your firewall settings to allow incoming connections on this port.

## Security Considerations

- Use a strong, random secret for webhook verification
- Consider putting the webhook listener behind a reverse proxy with HTTPS
- If possible, restrict the source IP addresses that can access your webhook endpoint
- Regularly update the webhook listener code to address any security vulnerabilities