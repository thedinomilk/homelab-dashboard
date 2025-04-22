#!/bin/bash
set -e

# This script updates a Portainer stack with the latest code and configuration

# Required variables (should be set as GitHub secrets)
PORTAINER_URL="${PORTAINER_URL}"
PORTAINER_USERNAME="${PORTAINER_USERNAME}"
PORTAINER_PASSWORD="${PORTAINER_PASSWORD}"
STACK_NAME="${STACK_NAME:-homelab-dashboard}"
ENV_FILE_PATH="${ENV_FILE_PATH:-/home/${HOMELAB_USER}/homelab-dashboard/.env}"

# Login to Portainer and get auth token
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

# Get endpoints (usually 1 for local)
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

# Get stack ID
echo "Getting stack ID for ${STACK_NAME}..."
STACKS_RESPONSE=$(curl -s -X GET "${PORTAINER_URL}/api/stacks" \
  -H "Authorization: Bearer ${JWT}")

STACK_ID=$(echo ${STACKS_RESPONSE} | grep -o "\"Name\":\"${STACK_NAME}\"[^}]*" | grep -o '"Id":[0-9]*' | cut -d':' -f2)

if [ -z "${STACK_ID}" ]; then
  echo "Failed to find stack named '${STACK_NAME}'."
  echo "Please ensure the stack exists in Portainer."
  exit 1
fi

echo "Found stack ID: ${STACK_ID}"

# Get stack details
echo "Getting stack details..."
STACK_DETAILS=$(curl -s -X GET "${PORTAINER_URL}/api/stacks/${STACK_ID}" \
  -H "Authorization: Bearer ${JWT}")

# Extract information needed for update
ENVIRONMENT_VARS=$(curl -s -X GET "${PORTAINER_URL}/api/stacks/${STACK_ID}/env" \
  -H "Authorization: Bearer ${JWT}")

# Update the stack with the pull option
echo "Updating stack ${STACK_NAME}..."
UPDATE_RESPONSE=$(curl -s -X PUT "${PORTAINER_URL}/api/stacks/${STACK_ID}?endpointId=${ENDPOINT_ID}" \
  -H "Authorization: Bearer ${JWT}" \
  -H "Content-Type: application/json" \
  -d "{
    \"prune\": true,
    \"pullImage\": true,
    \"env\": ${ENVIRONMENT_VARS}
  }")

if echo "${UPDATE_RESPONSE}" | grep -q "ResourceControl"; then
  echo "Stack ${STACK_NAME} updated successfully!"
else
  echo "Failed to update stack."
  echo "Response: ${UPDATE_RESPONSE}"
  exit 1
fi

# Verify the env file exists
echo "Checking if .env file exists at ${ENV_FILE_PATH}..."
if ssh ${HOMELAB_USER}@${HOMELAB_HOST} "[ -f ${ENV_FILE_PATH} ]"; then
  echo ".env file found at ${ENV_FILE_PATH}"
else
  echo "Warning: .env file not found at ${ENV_FILE_PATH}"
  echo "Ensure the .env file was copied correctly during deployment."
fi

echo "Deployment completed successfully!"