#!/bin/bash

# Setup PostgreSQL database for the homelab dashboard

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

# Default values
DOCKER_HOST="192.168.86.40"
POSTGRES_USER="postgres"
POSTGRES_PASSWORD="postgres"
POSTGRES_DB="homelab"
POSTGRES_PORT="5432"

# Print header
echo -e "${GREEN}=========================================${NC}"
echo -e "${GREEN}  PostgreSQL Setup for Homelab Dashboard ${NC}"
echo -e "${GREEN}=========================================${NC}"

# Check if docker-compose.postgres.yml exists
if [ ! -f "docker-compose.postgres.yml" ]; then
    echo -e "${RED}Error: docker-compose.postgres.yml not found${NC}"
    echo -e "${YELLOW}Make sure you run this script from the project root directory${NC}"
    exit 1
fi

# Ask for deployment method
echo -e "\n${YELLOW}How would you like to deploy PostgreSQL?${NC}"
echo "1) SSH to remote server and deploy with Docker Compose"
echo "2) Manual deployment (I'll set it up myself)"
read -p "Enter your choice (1-2): " DEPLOY_CHOICE

if [ "$DEPLOY_CHOICE" == "1" ]; then
    # Get SSH details
    read -p "Enter SSH username for $DOCKER_HOST [dinomilk]: " SSH_USER
    SSH_USER=${SSH_USER:-dinomilk}

    # Copy docker-compose file
    echo -e "\n${YELLOW}Copying docker-compose.postgres.yml to $SSH_USER@$DOCKER_HOST...${NC}"
    scp docker-compose.postgres.yml $SSH_USER@$DOCKER_HOST:~/
    
    if [ $? -ne 0 ]; then
        echo -e "${RED}Failed to copy file${NC}"
        exit 1
    fi
    
    # Deploy with SSH
    echo -e "\n${YELLOW}Deploying PostgreSQL on $DOCKER_HOST...${NC}"
    ssh $SSH_USER@$DOCKER_HOST "docker-compose -f docker-compose.postgres.yml up -d"
    
    if [ $? -ne 0 ]; then
        echo -e "${RED}Failed to deploy PostgreSQL${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}PostgreSQL deployed successfully!${NC}"
else
    echo -e "\n${YELLOW}Manual deployment selected.${NC}"
    echo -e "Please follow the instructions in docs/postgres-setup.md to set up PostgreSQL."
fi

# Generate DATABASE_URL
DATABASE_URL="postgresql://$POSTGRES_USER:$POSTGRES_PASSWORD@$DOCKER_HOST:$POSTGRES_PORT/$POSTGRES_DB"

# Set GitHub Secret
echo -e "\n${YELLOW}Would you like to set the DATABASE_URL as a GitHub secret?${NC}"
read -p "Enter y/n: " SET_SECRET

if [ "$SET_SECRET" == "y" ] || [ "$SET_SECRET" == "Y" ]; then
    echo -e "\n${YELLOW}Setting GitHub secret DATABASE_URL...${NC}"
    echo "$DATABASE_URL" | gh secret set DATABASE_URL
    
    if [ $? -ne 0 ]; then
        echo -e "${RED}Failed to set GitHub secret${NC}"
        echo -e "${YELLOW}You may need to set it manually:${NC}"
        echo "gh secret set DATABASE_URL '$DATABASE_URL'"
    else
        echo -e "${GREEN}GitHub secret set successfully!${NC}"
    fi
fi

# Final info
echo -e "\n${GREEN}=========================================${NC}"
echo -e "${GREEN}  PostgreSQL Setup Complete  ${NC}"
echo -e "${GREEN}=========================================${NC}"
echo -e "${YELLOW}Database URL:${NC} $DATABASE_URL"
echo -e "${YELLOW}To test the connection, run:${NC}"
echo "psql '$DATABASE_URL'"

# Make this script executable with: chmod +x scripts/setup-postgres.sh