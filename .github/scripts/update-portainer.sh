#!/bin/bash
set -e

# This script updates a Portainer stack with the latest code using a local docker-compose.yml
# Usage: ./update-portainer.sh PORTAINER_URL PORTAINER_API_KEY STACK_NAME

# Arguments
PORTAINER_URL="$1"
PORTAINER_API_KEY="$2"
STACK_NAME="$3"

# Check if all required arguments are provided
if [ -z "$PORTAINER_URL" ] || [ -z "$PORTAINER_API_KEY" ] || [ -z "$STACK_NAME" ]; then
    echo "Error: Missing required arguments"
    echo "Usage: ./update-portainer.sh PORTAINER_URL PORTAINER_API_KEY STACK_NAME"
    exit 1
fi

echo "Updating Portainer stack: $STACK_NAME"

# Create a temporary directory for working files
TMP_DIR=$(mktemp -d)
TMP_COMPOSE_FILE="$TMP_DIR/docker-compose.yml"
TMP_JSON_FILE="$TMP_DIR/stack-request.json"

# Use the local docker-compose.yml file
echo "Using local docker-compose.yml file..."
cp docker-compose.portainer.yml "$TMP_COMPOSE_FILE"

if [ ! -f "$TMP_COMPOSE_FILE" ]; then
    echo "Error: docker-compose.portainer.yml not found"
    exit 1
fi

# Find the stack ID
echo "Getting stack ID..."
STACK_ID=$(curl -s -H "X-API-Key: $PORTAINER_API_KEY" "$PORTAINER_URL/api/stacks" | jq -r ".[] | select(.Name == \"$STACK_NAME\") | .Id")

if [ -z "$STACK_ID" ]; then
    echo "Stack not found. Creating new stack..."
    
    # Create JSON request body for creating a new stack
    jq -n --arg name "$STACK_NAME" --arg content "$(cat $TMP_COMPOSE_FILE)" \
        '{name: $name, stackFileContent: $content, env: []}' > "$TMP_JSON_FILE"
    
    # Create new stack
    curl -X POST \
        -H "X-API-Key: $PORTAINER_API_KEY" \
        -H "Content-Type: application/json" \
        -d @"$TMP_JSON_FILE" \
        "$PORTAINER_URL/api/stacks"
        
    echo "Stack created successfully!"
else
    echo "Updating existing stack (ID: $STACK_ID)..."
    
    # Get environment variables
    ENV_VARS=$(curl -s -H "X-API-Key: $PORTAINER_API_KEY" "$PORTAINER_URL/api/stacks/$STACK_ID" | jq -c '.Env')
    
    # Create JSON request body for updating the stack
    jq -n --arg content "$(cat $TMP_COMPOSE_FILE)" --argjson env "$ENV_VARS" \
        '{stackFileContent: $content, env: $env, prune: false}' > "$TMP_JSON_FILE"
    
    # Update stack
    curl -X PUT \
        -H "X-API-Key: $PORTAINER_API_KEY" \
        -H "Content-Type: application/json" \
        -d @"$TMP_JSON_FILE" \
        "$PORTAINER_URL/api/stacks/$STACK_ID/file"
        
    echo "Stack updated successfully!"
    
    # Redeploy stack
    echo "Redeploying stack..."
    curl -X POST \
        -H "X-API-Key: $PORTAINER_API_KEY" \
        "$PORTAINER_URL/api/stacks/$STACK_ID/start"
        
    echo "Stack redeployed successfully!"
fi

# Clean up temporary files
rm -rf "$TMP_DIR"

echo "Portainer stack update completed!"