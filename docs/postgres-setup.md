# PostgreSQL Database Setup

This document explains how to set up the PostgreSQL database for the homelab dashboard.

## Option 1: Using Docker Compose (Recommended)

1. Copy the `docker-compose.postgres.yml` file to your Docker host:
   ```bash
   scp docker-compose.postgres.yml dinomilk@192.168.86.40:~/
   ```

2. SSH into your Docker host:
   ```bash
   ssh dinomilk@192.168.86.40
   ```

3. Start the PostgreSQL container:
   ```bash
   docker-compose -f docker-compose.postgres.yml up -d
   ```

4. Verify the container is running:
   ```bash
   docker ps | grep homelab-postgres
   ```

5. The database will be accessible at:
   ```
   postgresql://postgres:postgres@192.168.86.40:5432/homelab
   ```

## Option 2: Deploying with Portainer

1. Go to your Portainer instance at http://192.168.86.40:9000
2. Navigate to Stacks
3. Click "Add Stack"
4. Name it "homelab-postgres"
5. Copy the contents of `docker-compose.postgres.yml` into the web editor
6. Deploy the stack

## Changing Default Credentials

If you wish to change the default credentials (recommended for production), modify the environment variables in the docker-compose file:

```yaml
environment:
  POSTGRES_USER: your_secure_username
  POSTGRES_PASSWORD: your_secure_password
  POSTGRES_DB: homelab
```

Then update your DATABASE_URL accordingly:
```
postgresql://your_secure_username:your_secure_password@192.168.86.40:5432/homelab
```

## Connecting to the Database

You can connect to your PostgreSQL database using tools like pgAdmin, DBeaver, or the command line:

```bash
docker exec -it homelab-postgres psql -U postgres -d homelab
```