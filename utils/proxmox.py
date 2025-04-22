import requests
import logging
import json
import os
from urllib3.exceptions import InsecureRequestWarning
import urllib3

# Suppress only the single warning from urllib3 needed.
urllib3.disable_warnings(InsecureRequestWarning)

def get_proxmox_connection(settings=None):
    """
    Establish a connection to the Proxmox API using hardcoded values
    
    Args:
        settings: Ignored - maintained for backward compatibility
        
    Returns:
        tuple: (base_url, headers, verify_ssl)
    """
    # Hardcoded Proxmox credentials
    proxmox_host = os.environ.get("PROXMOX_HOST")
    proxmox_user = os.environ.get("PROXMOX_USER")
    proxmox_token_name = os.environ.get("PROXMOX_TOKEN_NAME")
    proxmox_token_value = os.environ.get("PROXMOX_TOKEN_VALUE")
    
    # Check for development mode
    development_mode = os.environ.get("DEVELOPMENT_MODE", "false").lower() == "true"
    
    # Format the base URL
    if not proxmox_host:
        if development_mode:
            logging.warning("Development mode enabled - using mock Proxmox host")
            proxmox_host = "localhost"
            proxmox_user = "dev@pam"
            proxmox_token_name = "dev-token"
            proxmox_token_value = "dev-value"
        else:
            raise ValueError("Proxmox host not configured")
        
    base_url = proxmox_host
    if not base_url.startswith('http'):
        base_url = f"https://{base_url}"
    if not base_url.endswith('/api2/json'):
        if not base_url.endswith('/'):
            base_url = f"{base_url}/"
        base_url = f"{base_url}api2/json"
    
    # API token format is USER@REALM!TOKENNAME=TOKENVALUE
    token_id = f"{proxmox_user}!{proxmox_token_name}"
    
    # Set up API headers
    headers = {
        'Authorization': f'PVEAPIToken={token_id}={proxmox_token_value}'
    }
    
    # For now, disable SSL verification (not recommended for production)
    verify_ssl = False
    
    return (base_url, headers, verify_ssl)

def get_nodes(settings):
    """
    Get a list of Proxmox nodes
    
    Args:
        settings: UserSettings object with Proxmox credentials
        
    Returns:
        list: List of node objects
    """
    # Check for development mode
    development_mode = os.environ.get("DEVELOPMENT_MODE", "false").lower() == "true"
    
    if development_mode:
        logging.warning("Development mode enabled - returning mock Proxmox nodes")
        # Return mock data for development
        return [
            {"node": "proxmox-1", "status": "online", "cpu": 0.1, "maxcpu": 8, "mem": 2048, "maxmem": 16384, "uptime": 1234567},
            {"node": "proxmox-2", "status": "online", "cpu": 0.2, "maxcpu": 8, "mem": 4096, "maxmem": 32768, "uptime": 7654321}
        ]
    
    # Normal production mode
    base_url, headers, verify_ssl = get_proxmox_connection(settings)
    
    try:
        response = requests.get(
            f"{base_url}/nodes",
            headers=headers,
            verify=verify_ssl
        )
        response.raise_for_status()
        
        data = response.json()
        return data.get('data', [])
        
    except requests.exceptions.RequestException as e:
        logging.error(f"Error connecting to Proxmox API: {str(e)}")
        raise Exception(f"Error connecting to Proxmox: {str(e)}")

def get_resources(settings, resource_type=None):
    """
    Get resources from Proxmox
    
    Args:
        settings: UserSettings object with Proxmox credentials
        resource_type: Optional type filter (qemu, storage, node)
        
    Returns:
        list: List of resources
    """
    # Check for development mode
    development_mode = os.environ.get("DEVELOPMENT_MODE", "false").lower() == "true"
    
    if development_mode:
        logging.warning(f"Development mode enabled - returning mock Proxmox resources for type: {resource_type}")
        # Return mock data for development
        if resource_type == "vm":
            return [
                {"type": "qemu", "node": "proxmox-1", "id": "qemu/100", "name": "web-server", "status": "running", "cpu": 1, "maxcpu": 2, "mem": 2048, "maxmem": 4096},
                {"type": "qemu", "node": "proxmox-2", "id": "qemu/101", "name": "db-server", "status": "running", "cpu": 2, "maxcpu": 4, "mem": 4096, "maxmem": 8192}
            ]
        elif resource_type == "lxc":
            return [
                {"type": "lxc", "node": "proxmox-1", "id": "lxc/200", "name": "docker-host", "status": "running", "cpu": 1, "maxcpu": 2, "mem": 1024, "maxmem": 2048},
                {"type": "lxc", "node": "proxmox-2", "id": "lxc/201", "name": "media-server", "status": "running", "cpu": 2, "maxcpu": 4, "mem": 2048, "maxmem": 4096}
            ]
        elif resource_type == "storage":
            return [
                {"type": "storage", "node": "proxmox-1", "storage": "local", "total": 1000000000, "used": 500000000, "avail": 500000000},
                {"type": "storage", "node": "proxmox-2", "storage": "zfs-pool", "total": 5000000000, "used": 1000000000, "avail": 4000000000}
            ]
        else:
            # Generic resource list
            return [
                {"type": "node", "node": "proxmox-1", "status": "online", "cpu": 0.1, "mem": 0.3, "disk": 0.5},
                {"type": "node", "node": "proxmox-2", "status": "online", "cpu": 0.2, "mem": 0.4, "disk": 0.6},
                {"type": "qemu", "node": "proxmox-1", "id": "qemu/100", "name": "web-server", "status": "running"},
                {"type": "qemu", "node": "proxmox-2", "id": "qemu/101", "name": "db-server", "status": "running"},
                {"type": "lxc", "node": "proxmox-1", "id": "lxc/200", "name": "docker-host", "status": "running"},
                {"type": "lxc", "node": "proxmox-2", "id": "lxc/201", "name": "media-server", "status": "running"}
            ]
    
    # Normal production mode
    base_url, headers, verify_ssl = get_proxmox_connection(settings)
    
    url = f"{base_url}/cluster/resources"
    if resource_type:
        url += f"?type={resource_type}"
    
    try:
        response = requests.get(
            url,
            headers=headers,
            verify=verify_ssl
        )
        response.raise_for_status()
        
        data = response.json()
        return data.get('data', [])
        
    except requests.exceptions.RequestException as e:
        logging.error(f"Error getting Proxmox resources: {str(e)}")
        raise Exception(f"Error getting Proxmox resources: {str(e)}")

def get_vms(settings, node=None):
    """
    Get list of VMs on a node or all nodes
    
    Args:
        settings: UserSettings object with Proxmox credentials
        node: Optional node name to filter
        
    Returns:
        list: List of VM objects
    """
    resources = get_resources(settings, "vm")
    
    if node:
        return [vm for vm in resources if vm.get('node') == node]
    return resources

def get_containers(settings, node=None):
    """
    Get list of LXC containers
    
    Args:
        settings: UserSettings object with Proxmox credentials
        node: Optional node name to filter
        
    Returns:
        list: List of container objects
    """
    resources = get_resources(settings, "lxc")
    
    if node:
        return [container for container in resources if container.get('node') == node]
    return resources

def get_node_status(settings, node):
    """
    Get detailed status of a specific node
    
    Args:
        settings: UserSettings object with Proxmox credentials
        node: Node name
        
    Returns:
        dict: Node status details
    """
    base_url, headers, verify_ssl = get_proxmox_connection(settings)
    
    try:
        response = requests.get(
            f"{base_url}/nodes/{node}/status",
            headers=headers,
            verify=verify_ssl
        )
        response.raise_for_status()
        
        data = response.json()
        return data.get('data', {})
        
    except requests.exceptions.RequestException as e:
        logging.error(f"Error getting node status: {str(e)}")
        raise Exception(f"Error getting node status: {str(e)}")

def get_node_storage(settings, node):
    """
    Get storage status on a specific node
    
    Args:
        settings: UserSettings object with Proxmox credentials
        node: Node name
        
    Returns:
        list: List of storage details
    """
    base_url, headers, verify_ssl = get_proxmox_connection(settings)
    
    try:
        response = requests.get(
            f"{base_url}/nodes/{node}/storage",
            headers=headers,
            verify=verify_ssl
        )
        response.raise_for_status()
        
        data = response.json()
        return data.get('data', [])
        
    except requests.exceptions.RequestException as e:
        logging.error(f"Error getting storage status: {str(e)}")
        raise Exception(f"Error getting storage status: {str(e)}")
