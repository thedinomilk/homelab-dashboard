import requests
import logging
import json
from urllib3.exceptions import InsecureRequestWarning
import urllib3

# Suppress only the single warning from urllib3 needed.
urllib3.disable_warnings(InsecureRequestWarning)

def get_proxmox_connection(settings):
    """
    Establish a connection to the Proxmox API
    
    Args:
        settings: UserSettings object with Proxmox credentials
        
    Returns:
        tuple: (base_url, headers, verify_ssl)
    """
    if not settings.proxmox_host:
        raise ValueError("Proxmox host not configured")
        
    if not settings.proxmox_token_name or not settings.proxmox_token_value:
        raise ValueError("Proxmox API token not configured")
    
    # Format the base URL
    base_url = settings.proxmox_host
    if not base_url.startswith('http'):
        base_url = f"https://{base_url}"
    if not base_url.endswith('/api2/json'):
        if not base_url.endswith('/'):
            base_url += '/'
        base_url += 'api2/json'
    
    # API token format is USER@REALM!TOKENNAME=TOKENVALUE
    token_id = f"{settings.proxmox_user}!{settings.proxmox_token_name}"
    
    # Set up API headers
    headers = {
        'Authorization': f'PVEAPIToken={token_id}={settings.proxmox_token_value}'
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
