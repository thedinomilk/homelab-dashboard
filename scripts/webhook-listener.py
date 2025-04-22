#!/usr/bin/env python3
"""
GitHub Webhook Listener for Homelab Dashboard

This service listens for GitHub webhook events and pulls the latest code
to deploy it to the homelab environment. It's designed to run on the
homelab server itself, eliminating the need for direct inbound connections
from GitHub Actions to the homelab.

Usage:
    python webhook-listener.py

Environment variables:
    WEBHOOK_SECRET: Secret token configured in GitHub webhook (required)
    WEBHOOK_PORT: Port to listen on (default: 8555)
    REPO_PATH: Path to the repository (default: ~/homelab-dashboard)
    GITHUB_REPO: GitHub repository name (default: thedinomilk/homelab-dashboard)

GitHub Webhook Configuration:
    1. Go to your GitHub repo -> Settings -> Webhooks -> Add webhook
    2. Payload URL: http://your-homelab-ip:8555/webhook
    3. Content type: application/json
    4. Secret: Same as WEBHOOK_SECRET env var
    5. Events: Just the push event
"""

import hashlib
import hmac
import json
import logging
import os
import subprocess
import sys
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('/var/log/webhook-listener.log'),
    ]
)
logger = logging.getLogger('webhook-listener')

# Configuration from environment variables
WEBHOOK_SECRET = os.environ.get('WEBHOOK_SECRET')
WEBHOOK_PORT = int(os.environ.get('WEBHOOK_PORT', 8555))
REPO_PATH = os.environ.get('REPO_PATH', os.path.expanduser('~/homelab-dashboard'))
GITHUB_REPO = os.environ.get('GITHUB_REPO', 'thedinomilk/homelab-dashboard')

class WebhookHandler(BaseHTTPRequestHandler):
    def _send_response(self, status_code, message):
        self.send_response(status_code)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps({'message': message}).encode())

    def do_GET(self):
        if self.path == '/health':
            self._send_response(200, 'Webhook listener is healthy')
        else:
            self._send_response(404, 'Not found')

    def do_POST(self):
        if self.path != '/webhook':
            self._send_response(404, 'Not found')
            return

        # Verify GitHub signature
        if WEBHOOK_SECRET:
            signature = self.headers.get('X-Hub-Signature-256')
            if not signature:
                logger.error("No signature header found")
                self._send_response(403, 'No signature provided')
                return

            # Get request body
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)

            # Verify signature
            expected_signature = 'sha256=' + hmac.new(
                WEBHOOK_SECRET.encode(),
                post_data,
                hashlib.sha256
            ).hexdigest()

            if not hmac.compare_digest(signature, expected_signature):
                logger.error("Signature verification failed")
                self._send_response(403, 'Invalid signature')
                return
        else:
            logger.warning("No webhook secret configured - skipping signature verification")
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)

        # Parse the JSON payload
        try:
            payload = json.loads(post_data.decode('utf-8'))
        except json.JSONDecodeError:
            logger.error("Invalid JSON payload")
            self._send_response(400, 'Invalid JSON payload')
            return

        # Check if this is a push event for the main branch
        try:
            ref = payload.get('ref', '')
            repo_name = payload.get('repository', {}).get('full_name', '')
            
            if ref != 'refs/heads/main' or repo_name != GITHUB_REPO:
                logger.info(f"Ignoring event: {ref} for {repo_name}")
                self._send_response(200, 'Event ignored')
                return
                
            logger.info(f"Processing push event to {ref} for {repo_name}")
            self._deploy_update()
            self._send_response(200, 'Deployment initiated')
            
        except Exception as e:
            logger.error(f"Error processing webhook: {str(e)}")
            self._send_response(500, f'Error: {str(e)}')

    def _deploy_update(self):
        """Pull the latest code and restart services"""
        try:
            # Change to the repository directory
            repo_dir = Path(REPO_PATH).expanduser().resolve()
            if not repo_dir.exists():
                logger.info(f"Cloning repository to {repo_dir}")
                repo_dir.parent.mkdir(parents=True, exist_ok=True)
                subprocess.run(
                    ['git', 'clone', f'https://github.com/{GITHUB_REPO}.git', str(repo_dir)],
                    check=True
                )
            
            # Pull the latest changes
            logger.info(f"Pulling latest changes in {repo_dir}")
            subprocess.run(['git', 'fetch', 'origin'], cwd=str(repo_dir), check=True)
            subprocess.run(['git', 'reset', '--hard', 'origin/main'], cwd=str(repo_dir), check=True)
            
            # Deploy with Docker Compose
            logger.info("Deploying with Docker Compose")
            subprocess.run(['docker-compose', 'up', '-d', '--build'], cwd=str(repo_dir), check=True)
            
            logger.info("Deployment completed successfully")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Deployment failed: {e}")
            return False

def run_server():
    """Run the webhook listener server"""
    if not WEBHOOK_SECRET:
        logger.warning("WEBHOOK_SECRET environment variable not set. Webhook verification will be disabled.")
    
    server_address = ('0.0.0.0', WEBHOOK_PORT)
    httpd = HTTPServer(server_address, WebhookHandler)
    logger.info(f"Starting webhook listener on port {WEBHOOK_PORT}")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        logger.info("Stopping webhook listener")
        httpd.server_close()

if __name__ == '__main__':
    run_server()