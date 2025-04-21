import json
import os
import shutil
import logging
import subprocess

def manage_zpool(action, pool_name):
    """
    Manage ZFS pool operations
    
    Args:
        action: Operation to perform (delete, create, etc.)
        pool_name: Name of the ZFS pool
        
    Returns:
        dict: Result of the operation
    """
    try:
        if action == 'delete':
            # First, check if pool exists
            check_cmd = ['zpool', 'list', pool_name]
            check_result = subprocess.run(
                check_cmd, 
                capture_output=True, 
                text=True
            )
            
            if check_result.returncode != 0:
                return {
                    'success': False,
                    'message': f"ZFS pool '{pool_name}' does not exist or is not accessible"
                }
                
            # Execute pool deletion (force destruction)
            cmd = ['zpool', 'destroy', '-f', pool_name]
            result = subprocess.run(
                cmd, 
                capture_output=True, 
                text=True
            )
            
            if result.returncode == 0:
                return {
                    'success': True,
                    'message': f"ZFS pool '{pool_name}' has been successfully deleted"
                }
            else:
                return {
                    'success': False,
                    'message': f"Failed to delete ZFS pool: {result.stderr.strip()}"
                }
                
        elif action == 'list':
            # List all ZFS pools
            cmd = ['zpool', 'list', '-H']
            result = subprocess.run(
                cmd, 
                capture_output=True, 
                text=True
            )
            
            if result.returncode == 0:
                pools = []
                for line in result.stdout.strip().split('\n'):
                    if line:
                        parts = line.split('\t')
                        if len(parts) >= 5:
                            pools.append({
                                'name': parts[0],
                                'size': parts[1],
                                'allocated': parts[2],
                                'free': parts[3],
                                'health': parts[4],
                            })
                return {
                    'success': True,
                    'pools': pools
                }
            else:
                return {
                    'success': False,
                    'message': f"Failed to list ZFS pools: {result.stderr.strip()}"
                }
        else:
            return {
                'success': False,
                'message': f"Unsupported action: {action}"
            }
    except Exception as e:
        logging.error(f"Error in manage_zpool: {str(e)}")
        return {
            'success': False,
            'message': f"Error: {str(e)}"
        }

def get_storage_info(settings):
    """
    Get storage usage information for configured paths
    
    Args:
        settings: UserSettings object with storage paths
        
    Returns:
        list: List of storage mount points with usage data
    """
    try:
        # Parse storage paths from settings
        storage_paths = []
        if settings.storage_paths:
            try:
                storage_paths = json.loads(settings.storage_paths)
            except json.JSONDecodeError:
                logging.error("Failed to parse storage paths JSON")
                storage_paths = []
        
        if not storage_paths:
            raise ValueError("No storage paths configured")
        
        storage_info = []
        
        for path in storage_paths:
            if not os.path.exists(path):
                logging.warning(f"Storage path does not exist: {path}")
                storage_info.append({
                    'path': path,
                    'exists': False,
                    'error': 'Path does not exist'
                })
                continue
            
            # Get disk usage stats
            try:
                total, used, free = shutil.disk_usage(path)
                
                # Get filesystem type - try to use df command
                fs_type = "Unknown"
                mount_point = path
                try:
                    df_output = subprocess.run(
                        ['df', '-T', path], 
                        capture_output=True, 
                        text=True, 
                        timeout=5
                    )
                    if df_output.returncode == 0:
                        # Parse df output (skip header)
                        lines = df_output.stdout.strip().split('\n')
                        if len(lines) > 1:
                            parts = lines[1].split()
                            if len(parts) >= 7:
                                fs_type = parts[1]
                                mount_point = parts[6]
                except (subprocess.SubprocessError, IndexError) as e:
                    logging.warning(f"Could not determine filesystem type: {e}")
                
                storage_info.append({
                    'path': path,
                    'exists': True,
                    'mount_point': mount_point,
                    'total': total,
                    'used': used,
                    'free': free,
                    'total_gb': round(total / (1024**3), 2),
                    'used_gb': round(used / (1024**3), 2),
                    'free_gb': round(free / (1024**3), 2),
                    'percent_used': round((used / total) * 100, 1),
                    'filesystem': fs_type
                })
            except Exception as e:
                logging.error(f"Error getting disk usage for {path}: {str(e)}")
                storage_info.append({
                    'path': path,
                    'exists': True,
                    'error': str(e)
                })
        
        return storage_info
    
    except Exception as e:
        logging.error(f"Error in get_storage_info: {str(e)}")
        raise Exception(f"Error getting storage information: {str(e)}")

def get_storage_details(path):
    """
    Get detailed information about a storage path
    
    Args:
        path: The path to examine
        
    Returns:
        dict: Detailed storage information
    """
    if not os.path.exists(path):
        return {
            'path': path,
            'exists': False,
            'error': 'Path does not exist'
        }
    
    try:
        stats = os.stat(path)
        
        # Get largest directories (limited to avoid long operations)
        largest_dirs = []
        try:
            if os.path.isdir(path):
                dirs = [(d, os.path.join(path, d)) for d in os.listdir(path) if os.path.isdir(os.path.join(path, d))]
                dir_sizes = []
                
                for name, dirpath in dirs:
                    try:
                        # Use du command for faster directory size calculation
                        du_output = subprocess.run(
                            ['du', '-s', dirpath], 
                            capture_output=True, 
                            text=True, 
                            timeout=10
                        )
                        if du_output.returncode == 0:
                            size_kb = int(du_output.stdout.strip().split()[0])
                            dir_sizes.append({
                                'name': name,
                                'path': dirpath,
                                'size': size_kb * 1024,  # Convert KB to bytes
                                'size_gb': round(size_kb / (1024**2), 2)  # Convert KB to GB
                            })
                    except Exception as e:
                        logging.warning(f"Error measuring directory {name}: {str(e)}")
                        
                # Sort by size (largest first) and take top 5
                largest_dirs = sorted(dir_sizes, key=lambda x: x['size'], reverse=True)[:5]
        except Exception as e:
            logging.warning(f"Error getting directory sizes: {str(e)}")
        
        return {
            'path': path,
            'exists': True,
            'permissions': oct(stats.st_mode)[-3:],
            'owner': stats.st_uid,
            'group': stats.st_gid,
            'size': stats.st_size,
            'last_modified': stats.st_mtime,
            'largest_dirs': largest_dirs
        }
    
    except Exception as e:
        logging.error(f"Error getting storage details for {path}: {str(e)}")
        return {
            'path': path,
            'exists': True,
            'error': str(e)
        }
