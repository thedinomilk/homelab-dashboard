#!/bin/bash
set -e

# This script updates a Portainer stack with the latest code
# Usage: ./update-portainer.sh PORTAINER_URL PORTAINER_API_KEY STACK_NAME SSH_CONNECTION REMOTE_PATH

# Arguments
PORTAINER_URL="$1"
PORTAINER_API_KEY="$2"
STACK_NAME="$3"
SSH_CONNECTION="$4"
REMOTE_PATH="$5"

# Check if all required arguments are provided
if [ -z "$PORTAINER_URL" ] || [ -z "$PORTAINER_API_KEY" ] || [ -z "$STACK_NAME" ] || [ -z "$SSH_CONNECTION" ] || [ -z "$REMOTE_PATH" ]; then
    echo "Error: Missing required arguments"
    echo "Usage: ./update-portainer.sh PORTAINER_URL PORTAINER_API_KEY STACK_NAME SSH_CONNECTION REMOTE_PATH"
    exit 1
fi

echo "Updating Portainer stack: $STACK_NAME"

# Find the stack ID
echo "Getting stack ID..."
STACK_ID=$(curl -s -H "X-API-Key: $PORTAINER_API_KEY" "$PORTAINER_URL/api/stacks" | jq -r ".[] | select(.Name == \"$STACK_NAME\") | .Id")

if [ -z "$STACK_ID" ]; then
    echo "Stack not found. Creating new stack..."
    
    # Get docker-compose content from remote server - with safer handling
    echo "Getting docker-compose content from remote server..."
    COMPOSE_CONTENT=$(ssh $SSH_CONNECTION "cat $REMOTE_PATH/docker-compose.yml" | awk '{printf "%s\\n", $0}' | sed 's/"/\\"/g')
    
    # Create new stack
    curl -X POST \
        -H "X-API-Key: $PORTAINER_API_KEY" \
        -H "Content-Type: application/json" \
        -d "{\"name\": \"$STACK_NAME\", \"stackFileContent\": \"$COMPOSE_CONTENT\", \"env\": []}" \
        "$PORTAINER_URL/api/stacks"
        
    echo "Stack created successfully!"
else
    echo "Updating existing stack (ID: $STACK_ID)..."
    
    # Get environment variables
    ENV_VARS=$(curl -s -H "X-API-Key: $PORTAINER_API_KEY" "$PORTAINER_URL/api/stacks/$STACK_ID" | jq -c '.Env')
    
    # Get docker-compose content from remote server - with safer handling
    echo "Getting docker-compose content from remote server..."
    COMPOSE_CONTENT=$(ssh $SSH_CONNECTION "cat $REMOTE_PATH/docker-compose.yml" | awk '{printf "%s\\n", $0}' | sed 's/"/\\"/g')
    
    # Update stack
    curl -X PUT \
        -H "X-API-Key: $PORTAINER_API_KEY" \
        -H "Content-Type: application/json" \
        -d "{\"stackFileContent\": \"$COMPOSE_CONTENT\", \"env\": $ENV_VARS, \"prune\": false}" \
        "$PORTAINER_URL/api/stacks/$STACK_ID/file"
        
    echo "Stack updated successfully!"
    
    # Redeploy stack
    echo "Redeploying stack..."
    curl -X POST \
        -H "X-API-Key: $PORTAINER_API_KEY" \
        "$PORTAINER_URL/api/stacks/$STACK_ID/start"
        
    echo "Stack redeployed successfully!"
fi

echo "Portainer stack update completed!"