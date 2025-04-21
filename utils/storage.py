import json
import os
import shutil
import logging
import subprocess
import paramiko
from paramiko import SFTPClient
from typing import Optional, Tuple, Dict, List, Any

def run_ssh_command(host: str, username: str, password: Optional[str] = None, 
                  key_path: Optional[str] = None, command: str = "") -> Tuple[str, str, int]:
    """
    Run a command over SSH
    
    Args:
        host: SSH host (IP or hostname)
        username: SSH username
        password: SSH password (optional if key_path is provided)
        key_path: Path to SSH private key (optional if password is provided)
        command: Command to run
        
    Returns:
        tuple: (stdout, stderr, return_code)
    """
    if not host or not username:
        return "", "Missing SSH host or username", -1
        
    if not command:
        return "", "No command specified", -1
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        # Connect using either password or key
        if key_path and os.path.exists(key_path):
            # Use key-based authentication
            key = paramiko.RSAKey.from_private_key_file(key_path)
            ssh.connect(host, username=username, pkey=key)
        else:
            # Use password authentication
            ssh.connect(host, username=username, password=password)
        
        # Execute command
        stdin, stdout, stderr = ssh.exec_command(command)
        exit_code = stdout.channel.recv_exit_status()
        
        # Get output
        stdout_str = stdout.read().decode('utf-8')
        stderr_str = stderr.read().decode('utf-8')
        
        return stdout_str, stderr_str, exit_code
    
    except Exception as e:
        logging.error(f"SSH error: {str(e)}")
        return "", str(e), -1
    
    finally:
        ssh.close()

def manage_zpool(action: str, pool_name: str, settings: Optional[Any] = None) -> Dict[str, Any]:
    """
    Manage ZFS pool operations
    
    Args:
        action: Operation to perform (delete, create, etc.)
        pool_name: Name of the ZFS pool
        settings: UserSettings object for SSH connection (optional)
        
    Returns:
        dict: Result of the operation
    """
    try:
        # Initialize SSH variables with defaults
        ssh_host = ""
        ssh_user = "root"
        ssh_password = None
        ssh_key_path = None
        use_ssh = False
        
        # Check if we should use SSH (settings has ssh_* attributes)
        if settings and hasattr(settings, 'ssh_host') and settings.ssh_host:
            use_ssh = True
            ssh_host = settings.ssh_host
            ssh_user = getattr(settings, 'ssh_user', 'root')
            ssh_password = getattr(settings, 'ssh_password', None) 
            ssh_key_path = getattr(settings, 'ssh_key_path', None)
        
        if action == 'delete':
            if use_ssh:
                # First, check if pool exists via SSH
                check_cmd = f"zpool list {pool_name}"
                stdout, stderr, exit_code = run_ssh_command(
                    ssh_host, ssh_user, ssh_password, ssh_key_path, check_cmd
                )
                
                if exit_code != 0:
                    return {
                        'success': False,
                        'message': f"ZFS pool '{pool_name}' does not exist or is not accessible"
                    }
                
                # Execute pool deletion via SSH
                cmd = f"zpool destroy -f {pool_name}"
                stdout, stderr, exit_code = run_ssh_command(
                    ssh_host, ssh_user, ssh_password, ssh_key_path, cmd
                )
                
                if exit_code == 0:
                    return {
                        'success': True,
                        'message': f"ZFS pool '{pool_name}' has been successfully deleted"
                    }
                else:
                    return {
                        'success': False,
                        'message': f"Failed to delete ZFS pool: {stderr.strip()}"
                    }
            else:
                # Local execution
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
            if use_ssh:
                # List all ZFS pools via SSH
                cmd = "zpool list -H"
                stdout, stderr, exit_code = run_ssh_command(
                    ssh_host, ssh_user, ssh_password, ssh_key_path, cmd
                )
                
                if exit_code == 0:
                    pools = []
                    for line in stdout.strip().split('\n'):
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
                        'message': f"Failed to list ZFS pools: {stderr.strip()}"
                    }
            else:
                # Local execution
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

def transfer_files(source_path: str, destination_host: str, destination_path: str, 
               username: str, password: Optional[str] = None, key_path: Optional[str] = None,
               recursive: bool = True) -> Dict[str, Any]:
    """
    Transfer files from local to remote server using SCP (Secure Copy Protocol)
    
    Args:
        source_path: Local path of file or directory to transfer
        destination_host: Remote hostname or IP address
        destination_path: Remote path to copy files to
        username: SSH username
        password: SSH password (optional if key_path is provided)
        key_path: Path to SSH private key (optional if password is provided)
        recursive: Whether to copy directories recursively
        
    Returns:
        dict: Result of the operation with success status and message
    """
    if not source_path or not os.path.exists(source_path):
        return {
            'success': False,
            'message': f"Source path '{source_path}' does not exist"
        }
        
    if not destination_host or not destination_path or not username:
        return {
            'success': False,
            'message': "Missing required parameters (destination_host, destination_path, or username)"
        }
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        # Connect using either password or key
        if key_path and os.path.exists(key_path):
            # Use key-based authentication
            key = paramiko.RSAKey.from_private_key_file(key_path)
            ssh.connect(destination_host, username=username, pkey=key)
        else:
            # Use password authentication
            ssh.connect(destination_host, username=username, password=password)
        
        # Create sftp client
        sftp = ssh.open_sftp()
        
        # Ensure the destination directory exists
        try:
            # Try to create all directories in the path
            if destination_path != '/':  # Skip if root directory
                destination_dirs = destination_path.split('/')
                current_path = '/'
                
                # Build path incrementally and create as needed
                for directory in destination_dirs:
                    if not directory:  # Skip empty segments from leading/trailing/consecutive slashes
                        continue
                        
                    current_path = os.path.join(current_path, directory)
                    try:
                        sftp.stat(current_path)  # Test if directory exists
                    except FileNotFoundError:
                        sftp.mkdir(current_path)  # Create if not exists
        except Exception as e:
            logging.warning(f"Error ensuring destination directory exists: {str(e)}")
            
        # Track transfer statistics
        transferred_files = 0
        total_size = 0
        failed_files = []
        
        # Handle directory or file transfer
        if os.path.isdir(source_path):
            # It's a directory - need to copy recursively if specified
            if not recursive:
                return {
                    'success': False,
                    'message': f"Source '{source_path}' is a directory, but recursive copy not enabled"
                }
                
            # Walk the directory structure and copy files
            for root, dirs, files in os.walk(source_path):
                # Create relative path
                rel_path = os.path.relpath(root, source_path)
                if rel_path == '.':
                    rel_path = ''
                    
                # Create destination directory for current path
                current_dest_path = os.path.join(destination_path, rel_path).replace('\\', '/')
                try:
                    try:
                        sftp.stat(current_dest_path)
                    except FileNotFoundError:
                        sftp.mkdir(current_dest_path)
                except Exception as e:
                    logging.warning(f"Error creating directory {current_dest_path}: {str(e)}")
                
                # Copy all files in the current directory
                for file in files:
                    local_file = os.path.join(root, file)
                    remote_file = os.path.join(current_dest_path, file).replace('\\', '/')
                    
                    try:
                        sftp.put(local_file, remote_file)
                        file_size = os.path.getsize(local_file)
                        transferred_files += 1
                        total_size += file_size
                        logging.info(f"Transferred: {local_file} → {remote_file} ({file_size} bytes)")
                    except Exception as e:
                        logging.error(f"Error transferring {local_file}: {str(e)}")
                        failed_files.append(local_file)
        else:
            # It's a single file
            try:
                # If destination is a directory, append the filename
                file_name = os.path.basename(source_path)
                if destination_path.endswith('/'):
                    remote_file = os.path.join(destination_path, file_name).replace('\\', '/')
                else:
                    remote_file = destination_path
                    
                sftp.put(source_path, remote_file)
                file_size = os.path.getsize(source_path)
                transferred_files += 1
                total_size += file_size
                logging.info(f"Transferred: {source_path} → {remote_file} ({file_size} bytes)")
            except Exception as e:
                logging.error(f"Error transferring {source_path}: {str(e)}")
                failed_files.append(source_path)
        
        summary = {
            'success': len(failed_files) == 0,
            'transferred_files': transferred_files,
            'failed_files': len(failed_files),
            'total_size_bytes': total_size,
            'total_size_mb': round(total_size / (1024 * 1024), 2)
        }
        
        if failed_files:
            summary['message'] = f"Completed with some errors. {transferred_files} files transferred, {len(failed_files)} failed."
            summary['failed_file_list'] = failed_files
        else:
            summary['message'] = f"Successfully transferred {transferred_files} files ({summary['total_size_mb']} MB)"
            
        return summary
            
    except Exception as e:
        logging.error(f"Error in file transfer: {str(e)}")
        return {
            'success': False,
            'message': f"File transfer error: {str(e)}"
        }
    finally:
        # Close SFTP connection if it was opened
        if 'sftp' in locals() and sftp:
            sftp.close()
        # Close SSH connection
        if ssh:
            ssh.close()

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
