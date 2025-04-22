# Containerized GitHub Webhook Listener

This directory contains everything needed to run the webhook listener as a Docker container.

## Overview

The webhook listener is a simple service that:
1. Listens for webhook events from GitHub
2. Validates the events using a shared secret
3. Pulls the latest code from your repository
4. Deploys it using Docker Compose

## Advantages of Containerized Deployment

- **Isolation**: The webhook listener runs in its own container
- **Dependency management**: All dependencies are contained in the image
- **Easy updates**: Just rebuild the container to update the listener
- **Easy monitoring**: Use standard Docker tools to monitor the container
- **Easy deployment**: Uses Docker Compose for simple deployment

## Setup Instructions

1. **Edit the docker-compose.yml file**:
   
   Update the `WEBHOOK_SECRET` with a strong, random value. This will be used to verify that webhook requests are coming from GitHub.
   
   ```yaml
   environment:
     - WEBHOOK_SECRET=your_strong_random_secret
   ```

2. **Build and start the container**:

   ```bash
   cd scripts/webhook-listener
   docker-compose up -d
   ```

3. **Configure the GitHub webhook**:

   a. Go to your GitHub repository
   b. Click Settings -> Webhooks -> Add webhook
   c. Configure the webhook:
      - Payload URL: `http://your-homelab-ip:8555/webhook`
      - Content type: `application/json`
      - Secret: The same secret you used in the docker-compose.yml file
      - Events: Just the push event
   d. Click "Add webhook"

4. **Test the webhook**:

   Make a small change to your repository and push it to GitHub. The webhook listener should receive the event and deploy the changes.

## Troubleshooting

### View Container Logs

To see the webhook listener logs:

```bash
docker logs homelab-webhook-listener
```

### Check Container Status

To check if the container is running:

```bash
docker ps | grep homelab-webhook-listener
```

### Restart the Container

To restart the webhook listener:

```bash
docker-compose restart webhook-listener
```

### Test the Webhook Manually

You can test if the webhook endpoint is accessible:

```bash
curl http://localhost:8555/health
```

Should return: `{"message": "Webhook listener is healthy"}`

## Security Considerations

- The webhook secret is used to verify that requests come from GitHub
- The container needs access to the Docker socket to deploy services
- Consider using a reverse proxy with HTTPS for production use
- Only expose the webhook port to GitHub's IP ranges if possible