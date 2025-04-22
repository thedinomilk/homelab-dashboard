#!/bin/bash
set -e

# This script helps create a Portainer stack for the homelab dashboard
# It requires the Portainer CLI to be installed

# Default values
DEFAULT_STACK_NAME="homelab-dashboard"
DEFAULT_PORTAINER_URL="http://localhost:9000"
DEFAULT_COMPOSE_FILE="docker-compose.portainer.yml"

# Welcome message
echo "Homelab Dashboard - Portainer Stack Creator"
echo "==========================================="
echo "This script will help you set up a Portainer stack for your homelab dashboard."
echo ""

# Prompt for Portainer URL
read -p "Enter your Portainer URL [$DEFAULT_PORTAINER_URL]: " PORTAINER_URL
PORTAINER_URL=${PORTAINER_URL:-$DEFAULT_PORTAINER_URL}

# Prompt for Portainer credentials
read -p "Enter your Portainer username [admin]: " PORTAINER_USERNAME
PORTAINER_USERNAME=${PORTAINER_USERNAME:-admin}
read -sp "Enter your Portainer password: " PORTAINER_PASSWORD
echo ""

# Prompt for stack name
read -p "Enter the stack name [$DEFAULT_STACK_NAME]: " STACK_NAME
STACK_NAME=${STACK_NAME:-$DEFAULT_STACK_NAME}

# Prompt for compose file
read -p "Enter the compose file to use [$DEFAULT_COMPOSE_FILE]: " COMPOSE_FILE
COMPOSE_FILE=${COMPOSE_FILE:-$DEFAULT_COMPOSE_FILE}

# Verify the compose file exists
if [ ! -f "$COMPOSE_FILE" ]; then
    echo "Error: Compose file $COMPOSE_FILE not found."
    exit 1
fi

# Check if .env file exists
if [ ! -f ".env" ]; then
    if [ -f ".env.template" ]; then
        echo "No .env file found, but .env.template exists."
        read -p "Would you like to create a .env file from the template? (y/n): " CREATE_ENV
        if [[ "$CREATE_ENV" =~ ^[Yy] ]]; then
            cp .env.template .env
            echo "Created .env file from template. Please edit it with your actual values."
            exit 0
        fi
    fi
    echo "Warning: No .env file found. Environment variables will not be included."
fi

# Login to Portainer API
echo "Logging in to Portainer..."
AUTH_RESPONSE=$(curl -s -X POST "${PORTAINER_URL}/api/auth" \
  -H "Content-Type: application/json" \
  -d "{\"username\":\"${PORTAINER_USERNAME}\",\"password\":\"${PORTAINER_PASSWORD}\"}")

JWT=$(echo ${AUTH_RESPONSE} | grep -o '"jwt":"[^"]*' | cut -d'"' -f4)

if [ -z "${JWT}" ]; then
  echo "Failed to get authentication token from Portainer."
  echo "Response: ${AUTH_RESPONSE}"
  exit 1
fi

echo "Successfully authenticated with Portainer."

# Get endpoints
echo "Getting endpoints..."
ENDPOINTS_RESPONSE=$(curl -s -X GET "${PORTAINER_URL}/api/endpoints" \
  -H "Authorization: Bearer ${JWT}")

ENDPOINT_ID=$(echo ${ENDPOINTS_RESPONSE} | grep -o '"Id":[0-9]*' | head -1 | cut -d':' -f2)

if [ -z "${ENDPOINT_ID}" ]; then
  echo "Failed to get endpoint ID."
  echo "Response: ${ENDPOINTS_RESPONSE}"
  exit 1
fi

echo "Using endpoint ID: ${ENDPOINT_ID}"

# Check if stack already exists
echo "Checking if stack already exists..."
STACKS_RESPONSE=$(curl -s -X GET "${PORTAINER_URL}/api/stacks" \
  -H "Authorization: Bearer ${JWT}")

STACK_ID=$(echo ${STACKS_RESPONSE} | grep -o "\"Name\":\"${STACK_NAME}\"[^}]*" | grep -o '"Id":[0-9]*' | cut -d':' -f2)

if [ ! -z "${STACK_ID}" ]; then
  echo "Stack '${STACK_NAME}' already exists with ID: ${STACK_ID}"
  read -p "Would you like to update the existing stack? (y/n): " UPDATE_STACK
  if [[ ! "$UPDATE_STACK" =~ ^[Yy] ]]; then
    echo "Aborting. No changes made."
    exit 0
  fi
fi

# Build environment variables array for stack
ENV_ARRAY="[]"
if [ -f ".env" ]; then
  echo "Reading environment variables from .env file..."
  ENV_VARS=$(cat .env | grep -v "^#" | grep "=")
  
  # Create JSON array for env variables
  ENV_ARRAY="["
  while IFS= read -r line; do
    if [[ ! -z "$line" ]]; then
      key=$(echo "$line" | cut -d= -f1)
      value=$(echo "$line" | cut -d= -f2-)
      ENV_ARRAY+="{ \"name\": \"$key\", \"value\": \"$value\" },"
    fi
  done <<< "$ENV_VARS"
  # Remove trailing comma and close array
  ENV_ARRAY=${ENV_ARRAY%,}
  ENV_ARRAY+="]"
fi

# Read the compose file content
COMPOSE_CONTENT=$(cat "$COMPOSE_FILE")

if [ ! -z "${STACK_ID}" ]; then
  # Update existing stack
  echo "Updating stack ${STACK_NAME}..."
  UPDATE_RESPONSE=$(curl -s -X PUT "${PORTAINER_URL}/api/stacks/${STACK_ID}?endpointId=${ENDPOINT_ID}" \
    -H "Authorization: Bearer ${JWT}" \
    -H "Content-Type: application/json" \
    -d "{
      \"stackFileContent\": $(jq -Rs . <<< "$COMPOSE_CONTENT"),
      \"env\": ${ENV_ARRAY},
      \"prune\": true
    }")
  
  if echo "${UPDATE_RESPONSE}" | grep -q "ResourceControl"; then
    echo "Stack ${STACK_NAME} updated successfully!"
  else
    echo "Failed to update stack."
    echo "Response: ${UPDATE_RESPONSE}"
    exit 1
  fi
else
  # Create new stack
  echo "Creating new stack ${STACK_NAME}..."
  CREATE_RESPONSE=$(curl -s -X POST "${PORTAINER_URL}/api/stacks?type=1&method=string&endpointId=${ENDPOINT_ID}" \
    -H "Authorization: Bearer ${JWT}" \
    -H "Content-Type: application/json" \
    -d "{
      \"name\": \"${STACK_NAME}\",
      \"stackFileContent\": $(jq -Rs . <<< "$COMPOSE_CONTENT"),
      \"env\": ${ENV_ARRAY}
    }")
  
  if echo "${CREATE_RESPONSE}" | grep -q "ResourceControl"; then
    echo "Stack ${STACK_NAME} created successfully!"
  else
    echo "Failed to create stack."
    echo "Response: ${CREATE_RESPONSE}"
    exit 1
  fi
fi

echo ""
echo "Stack setup complete! You can now access your homelab dashboard."
echo "If you're using the default settings, it should be available at:"
echo "http://your-server-ip:5000"
echo ""
echo "Don't forget to manage your GitHub Actions secrets for automated deployments!"