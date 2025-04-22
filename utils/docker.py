import requests
import logging
import json
import os
from datetime import datetime

def get_docker_url(settings=None):
    """
    Build the Docker API URL using hardcoded values
    
    Args:
        settings: Ignored - maintained for backward compatibility
        
    Returns:
        str: Docker API base URL
    """
    # Hardcoded Docker credentials
    docker_host = os.environ.get("DOCKER_HOST")
    docker_port = int(os.environ.get("DOCKER_PORT", 2375))
    
    # Check for development mode
    development_mode = os.environ.get("DEVELOPMENT_MODE", "false").lower() == "true"
    
    # Format Docker URL
    if not docker_host:
        if development_mode:
            logging.warning("Development mode enabled - using mock Docker host")
            docker_host = "localhost"
        else:
            raise ValueError("Docker host not configured")
        
    base_url = docker_host
    if base_url.startswith('tcp://'):
        base_url = base_url.replace('tcp://', 'http://')
    
    if not base_url.startswith('http'):
        base_url = f"http://{base_url}"
    
    # Add port if not in URL
    if ':' not in base_url.split('//')[-1]:
        base_url = f"{base_url}:{docker_port}"
    
    return base_url

def get_containers(settings, all_containers=True):
    """
    Get list of Docker containers
    
    Args:
        settings: UserSettings object with Docker config
        all_containers: Whether to include stopped containers
        
    Returns:
        list: List of container objects
    """
    # Check for development mode
    development_mode = os.environ.get("DEVELOPMENT_MODE", "false").lower() == "true"
    
    if development_mode:
        logging.warning("Development mode enabled - returning mock Docker containers")
        # Return mock container data for development
        now = datetime.now().timestamp()
        
        mock_containers = [
            {
                "Id": "container1",
                "Names": ["/media-server"],
                "Name": "media-server",
                "Image": "linuxserver/plex:latest",
                "Created": now - 86400,  # 1 day ago
                "CreatedFormatted": datetime.fromtimestamp(now - 86400).strftime('%Y-%m-%d %H:%M:%S'),
                "Status": "Up 1 day",
                "StatusClass": "success",
                "Ports": [{"PrivatePort": 32400, "PublicPort": 32400, "Type": "tcp"}],
                "PortsFormatted": ["32400:32400/tcp"]
            },
            {
                "Id": "container2",
                "Names": ["/transmission"],
                "Name": "transmission",
                "Image": "linuxserver/transmission:latest",
                "Created": now - 172800,  # 2 days ago
                "CreatedFormatted": datetime.fromtimestamp(now - 172800).strftime('%Y-%m-%d %H:%M:%S'),
                "Status": "Up 2 days",
                "StatusClass": "success",
                "Ports": [{"PrivatePort": 9091, "PublicPort": 9091, "Type": "tcp"}],
                "PortsFormatted": ["9091:9091/tcp"]
            },
            {
                "Id": "container3",
                "Names": ["/portainer"],
                "Name": "portainer",
                "Image": "portainer/portainer-ce:latest",
                "Created": now - 604800,  # 7 days ago
                "CreatedFormatted": datetime.fromtimestamp(now - 604800).strftime('%Y-%m-%d %H:%M:%S'),
                "Status": "Up 7 days",
                "StatusClass": "success",
                "Ports": [{"PrivatePort": 9000, "PublicPort": 9000, "Type": "tcp"}],
                "PortsFormatted": ["9000:9000/tcp"]
            },
            {
                "Id": "container4",
                "Names": ["/database"],
                "Name": "database",
                "Image": "postgres:14",
                "Created": now - 259200,  # 3 days ago
                "CreatedFormatted": datetime.fromtimestamp(now - 259200).strftime('%Y-%m-%d %H:%M:%S'),
                "Status": "Exited (0) 1 hour ago",
                "StatusClass": "danger",
                "Ports": [{"PrivatePort": 5432, "PublicPort": 5432, "Type": "tcp"}],
                "PortsFormatted": ["5432:5432/tcp"]
            }
        ]
        
        # Only return running containers if all_containers is False
        if not all_containers:
            return [c for c in mock_containers if 'up' in c['Status'].lower()]
        return mock_containers
    
    # Normal production mode
    base_url = get_docker_url(settings)
    
    try:
        response = requests.get(
            f"{base_url}/containers/json?all={'true' if all_containers else 'false'}",
            timeout=5
        )
        response.raise_for_status()
        
        containers = response.json()
        
        # Format container data
        for container in containers:
            # Convert created timestamp to readable date
            created = container.get('Created', 0)
            container['CreatedFormatted'] = datetime.fromtimestamp(created).strftime('%Y-%m-%d %H:%M:%S')
            
            # Format port mappings
            container['PortsFormatted'] = []
            for port in container.get('Ports', []):
                if 'PublicPort' in port and 'PrivatePort' in port:
                    container['PortsFormatted'].append(
                        f"{port.get('PublicPort', '')}:{port.get('PrivatePort', '')}/{port.get('Type', 'tcp')}"
                    )
            
            # Extract name without leading slash
            container['Names'] = [name.lstrip('/') for name in container.get('Names', [])]
            
            # Get first name as primary name
            if container['Names']:
                container['Name'] = container['Names'][0]
            else:
                container['Name'] = 'Unnamed'
                
            # Format status
            status = container.get('Status', '').lower()
            if 'up' in status:
                container['StatusClass'] = 'success'
            elif 'exited' in status:
                container['StatusClass'] = 'danger'
            elif 'paused' in status:
                container['StatusClass'] = 'warning'
            else:
                container['StatusClass'] = 'secondary'
        
        return containers
        
    except requests.exceptions.RequestException as e:
        logging.error(f"Error connecting to Docker API: {str(e)}")
        raise Exception(f"Error connecting to Docker: {str(e)}")

def start_container(settings, container_id):
    """
    Start a Docker container
    
    Args:
        settings: UserSettings object with Docker config
        container_id: Container ID to start
        
    Returns:
        bool: Success status
    """
    base_url = get_docker_url(settings)
    
    try:
        response = requests.post(
            f"{base_url}/containers/{container_id}/start",
            timeout=10
        )
        response.raise_for_status()
        return True
        
    except requests.exceptions.RequestException as e:
        logging.error(f"Error starting container: {str(e)}")
        raise Exception(f"Error starting container: {str(e)}")

def stop_container(settings, container_id):
    """
    Stop a Docker container
    
    Args:
        settings: UserSettings object with Docker config
        container_id: Container ID to stop
        
    Returns:
        bool: Success status
    """
    base_url = get_docker_url(settings)
    
    try:
        response = requests.post(
            f"{base_url}/containers/{container_id}/stop",
            timeout=30  # Longer timeout for stop operation
        )
        response.raise_for_status()
        return True
        
    except requests.exceptions.RequestException as e:
        logging.error(f"Error stopping container: {str(e)}")
        raise Exception(f"Error stopping container: {str(e)}")

def restart_container(settings, container_id):
    """
    Restart a Docker container
    
    Args:
        settings: UserSettings object with Docker config
        container_id: Container ID to restart
        
    Returns:
        bool: Success status
    """
    base_url = get_docker_url(settings)
    
    try:
        response = requests.post(
            f"{base_url}/containers/{container_id}/restart",
            timeout=30  # Longer timeout for restart operation
        )
        response.raise_for_status()
        return True
        
    except requests.exceptions.RequestException as e:
        logging.error(f"Error restarting container: {str(e)}")
        raise Exception(f"Error restarting container: {str(e)}")

def get_container_stats(settings, container_id):
    """
    Get container runtime statistics
    
    Args:
        settings: UserSettings object with Docker config
        container_id: Container ID to get stats for
        
    Returns:
        dict: Container statistics
    """
    base_url = get_docker_url(settings)
    
    try:
        # Get one-time stats snapshot
        response = requests.get(
            f"{base_url}/containers/{container_id}/stats?stream=false",
            timeout=5
        )
        response.raise_for_status()
        
        stats = response.json()
        
        # Calculate CPU percentage
        cpu_delta = stats.get('cpu_stats', {}).get('cpu_usage', {}).get('total_usage', 0) - \
                   stats.get('precpu_stats', {}).get('cpu_usage', {}).get('total_usage', 0)
        
        system_delta = stats.get('cpu_stats', {}).get('system_cpu_usage', 0) - \
                       stats.get('precpu_stats', {}).get('system_cpu_usage', 0)
        
        cpu_percent = 0
        if system_delta > 0 and cpu_delta > 0:
            num_cpus = len(stats.get('cpu_stats', {}).get('cpu_usage', {}).get('percpu_usage', []))
            if num_cpus == 0:
                num_cpus = 1
            cpu_percent = (cpu_delta / system_delta) * num_cpus * 100
        
        # Calculate memory usage
        memory_usage = stats.get('memory_stats', {}).get('usage', 0)
        memory_limit = stats.get('memory_stats', {}).get('limit', 1)
        memory_percent = (memory_usage / memory_limit) * 100
        
        return {
            'id': container_id,
            'cpu_percent': round(cpu_percent, 2),
            'memory_percent': round(memory_percent, 2),
            'memory_usage': memory_usage,
            'memory_limit': memory_limit,
            'networks': stats.get('networks', {})
        }
        
    except requests.exceptions.RequestException as e:
        logging.error(f"Error getting container stats: {str(e)}")
        raise Exception(f"Error getting container stats: {str(e)}")
