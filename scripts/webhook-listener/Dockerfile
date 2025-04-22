FROM python:3.9-slim

WORKDIR /app

# Install git and required packages
RUN apt-get update && \
    apt-get install -y git docker.io curl && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Copy the webhook listener script
COPY webhook-listener.py /app/

# Make the script executable
RUN chmod +x /app/webhook-listener.py

# Expose the webhook port
EXPOSE 8555

# Default environment variables (override these when running the container)
ENV WEBHOOK_SECRET="change_this_to_your_secret"
ENV WEBHOOK_PORT=8555
ENV REPO_PATH="/app/repo"
ENV GITHUB_REPO="thedinomilk/homelab-dashboard"

# Create directory for the repository
RUN mkdir -p /app/repo

# Run the webhook listener
CMD ["python", "/app/webhook-listener.py"]