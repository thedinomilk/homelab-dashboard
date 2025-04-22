import os
import logging
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
from werkzeug.middleware.proxy_fix import ProxyFix
from werkzeug.security import generate_password_hash, check_password_hash
import json
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Import database
from database import db, init_db

# Create Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Configure SQLite database (can be changed to MySQL/PostgreSQL later)
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///homelab.db")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}

# Initialize database
init_db(app)

# Create Jinja2 filters
@app.template_filter('from_json')
def from_json_filter(value):
    """Convert JSON string to Python list/dict"""
    if not value:
        return []
    try:
        return json.loads(value)
    except:
        return []

# Import utils after app initialization
from utils import proxmox, docker, storage
from models import UserSettings, DocuEntry, ScriptEntry, MediaRequest

# Initialize default settings if none exist
with app.app_context():
    if not UserSettings.query.first():
        default_settings = UserSettings(
            proxmox_host="",
            proxmox_user="",
            proxmox_token_name="",
            proxmox_token_value="",
            docker_host="",
            docker_port=2375,
            storage_paths=json.dumps(["/mnt"])
        )
        db.session.add(default_settings)
        db.session.commit()
        logging.info("Initialized default settings")

# Routes
@app.route('/')
def index():
    settings = UserSettings.query.first()
    return render_template('dashboard.html', active_page='dashboard', settings=settings)

@app.route('/dashboard')
def dashboard():
    settings = UserSettings.query.first()
    return render_template('dashboard.html', active_page='dashboard', settings=settings)

@app.route('/docker')
def docker_page():
    settings = UserSettings.query.first()
    return render_template('docker.html', active_page='docker', settings=settings)

@app.route('/storage')
def storage_page():
    settings = UserSettings.query.first()
    return render_template('storage.html', active_page='storage', settings=settings)

@app.route('/docs')
def docs_page():
    docs = DocuEntry.query.order_by(DocuEntry.title).all()
    return render_template('docs.html', active_page='docs', docs=docs)

@app.route('/scripts')
def scripts_page():
    scripts = ScriptEntry.query.order_by(ScriptEntry.title).all()
    return render_template('scripts.html', active_page='scripts', scripts=scripts)

@app.route('/settings', methods=['GET', 'POST'])
def settings_page():
    settings = UserSettings.query.first()
    
    if request.method == 'POST':
        # Update settings
        settings.proxmox_host = request.form.get('proxmox_host', '')
        settings.proxmox_user = request.form.get('proxmox_user', '')
        settings.proxmox_token_name = request.form.get('proxmox_token_name', '')
        
        # Only update token if provided (to not overwrite existing one)
        if request.form.get('proxmox_token_value'):
            settings.proxmox_token_value = request.form.get('proxmox_token_value')
            
        settings.docker_host = request.form.get('docker_host', '')
        settings.docker_port = int(request.form.get('docker_port', 2375))
        
        # Handle storage paths as a list
        storage_paths = request.form.get('storage_paths', '')
        settings.storage_paths = json.dumps(
            [path.strip() for path in storage_paths.split('\n') if path.strip()]
        )
        
        # Update SSH settings for ZFS management
        settings.ssh_host = request.form.get('ssh_host', '')
        settings.ssh_user = request.form.get('ssh_user', '')
        
        # Only update SSH password if provided
        if request.form.get('ssh_password'):
            settings.ssh_password = request.form.get('ssh_password')
            
        settings.ssh_key_path = request.form.get('ssh_key_path', '')
        
        db.session.commit()
        flash('Settings updated successfully!', 'success')
        return redirect(url_for('settings_page'))
        
    return render_template('settings.html', active_page='settings', settings=settings)

# API Routes
@app.route('/api/proxmox/nodes')
def get_proxmox_nodes():
    settings = UserSettings.query.first()
    try:
        nodes = proxmox.get_nodes(settings)
        return jsonify(nodes)
    except Exception as e:
        logging.error(f"Error getting Proxmox nodes: {str(e)}")
        # Return empty array instead of error to prevent frontend issues
        return jsonify([]), 200

@app.route('/api/proxmox/resources')
def get_proxmox_resources():
    settings = UserSettings.query.first()
    try:
        resources = proxmox.get_resources(settings)
        return jsonify(resources)
    except Exception as e:
        logging.error(f"Error getting Proxmox resources: {str(e)}")
        # Return empty array instead of error
        return jsonify([]), 200

@app.route('/api/docker/containers')
def get_docker_containers():
    settings = UserSettings.query.first()
    try:
        containers = docker.get_containers(settings)
        return jsonify(containers)
    except Exception as e:
        logging.error(f"Error getting Docker containers: {str(e)}")
        # Return empty array instead of error
        return jsonify([]), 200

@app.route('/api/docker/container/<container_id>/start', methods=['POST'])
def start_container(container_id):
    settings = UserSettings.query.first()
    try:
        result = docker.start_container(settings, container_id)
        return jsonify({"success": True, "message": "Container started"})
    except Exception as e:
        logging.error(f"Error starting container: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/docker/container/<container_id>/stop', methods=['POST'])
def stop_container(container_id):
    settings = UserSettings.query.first()
    try:
        result = docker.stop_container(settings, container_id)
        return jsonify({"success": True, "message": "Container stopped"})
    except Exception as e:
        logging.error(f"Error stopping container: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/docker/container/<container_id>/restart', methods=['POST'])
def restart_container(container_id):
    settings = UserSettings.query.first()
    try:
        result = docker.restart_container(settings, container_id)
        return jsonify({"success": True, "message": "Container restarted"})
    except Exception as e:
        logging.error(f"Error restarting container: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/storage/info')
def get_storage_info():
    settings = UserSettings.query.first()
    try:
        storage_info = storage.get_storage_info(settings)
        return jsonify(storage_info)
    except Exception as e:
        logging.error(f"Error getting storage info: {str(e)}")
        # Return empty array instead of error
        return jsonify([]), 200

@app.route('/api/storage/zpool/list')
def list_zpools():
    """List all ZFS pools"""
    try:
        settings = UserSettings.query.first()
        result = storage.manage_zpool('list', '', settings)
        return jsonify(result)
    except Exception as e:
        logging.error(f"Error listing ZFS pools: {str(e)}")
        return jsonify({"error": str(e)}), 500
        
@app.route('/api/storage/zpool/test-ssh')
def test_zpool_ssh():
    """Test SSH connection for ZFS management"""
    try:
        settings = UserSettings.query.first()
        
        # Skip test if SSH settings are not configured
        if not settings.ssh_host or not settings.ssh_user:
            return jsonify({
                "success": False,
                "message": "SSH connection not configured. Please set SSH host and username."
            }), 400
            
        # Run a simple command via SSH to test connection
        stdout, stderr, exit_code = storage.run_ssh_command(
            settings.ssh_host,
            settings.ssh_user,
            settings.ssh_password,
            settings.ssh_key_path,
            "command -v zpool || echo 'ZFS not installed'"
        )
        
        if exit_code != 0:
            return jsonify({
                "success": False,
                "message": f"SSH connection failed: {stderr}"
            })
            
        # Check if zpool command is available
        if "not installed" in stdout:
            return jsonify({
                "success": False,
                "message": "Connected to SSH, but ZFS tools are not installed on the remote system."
            })
            
        # If ZFS is installed, try to list pools to verify full functionality
        stdout, stderr, exit_code = storage.run_ssh_command(
            settings.ssh_host,
            settings.ssh_user,
            settings.ssh_password,
            settings.ssh_key_path,
            "zpool list -H"
        )
        
        if exit_code != 0:
            return jsonify({
                "success": False,
                "message": f"ZFS tools are installed, but unable to list pools: {stderr}"
            })
        
        # Count the pools
        pools = [line for line in stdout.strip().split('\n') if line.strip()]
        pool_count = len(pools)
        
        # Report success with pool count
        return jsonify({
            "success": True,
            "message": f"SSH connection successful and ZFS is working! Found {pool_count} ZFS pools."
        })
        
    except Exception as e:
        logging.error(f"Error testing SSH ZFS connection: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/storage/zpool/delete/<pool_name>', methods=['POST'])
def delete_zpool(pool_name):
    """Delete a ZFS pool"""
    try:
        settings = UserSettings.query.first()
        result = storage.manage_zpool('delete', pool_name, settings)
        return jsonify(result)
    except Exception as e:
        logging.error(f"Error deleting ZFS pool: {str(e)}")
        return jsonify({"error": str(e)}), 500
        
@app.route('/api/storage/zpool/delete-apatosaurus', methods=['POST'])
def delete_apatosaurus_zpool():
    """Dedicated endpoint to delete the 'apatosaurus' ZFS pool"""
    try:
        settings = UserSettings.query.first()
        
        # Skip if SSH settings are not configured
        if not settings.ssh_host or not settings.ssh_user:
            return jsonify({
                "success": False,
                "message": "SSH connection not configured. Please set SSH host and username."
            }), 400
        
        result = storage.manage_zpool('delete', 'apatosaurus', settings)
        return jsonify(result)
    except Exception as e:
        logging.error(f"Error deleting 'apatosaurus' ZFS pool: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/storage/transfer', methods=['POST'])
def transfer_files_to_server():
    """Transfer files from local to remote server using SFTP"""
    try:
        settings = UserSettings.query.first()
        
        # Check if SSH settings are configured
        if not settings.ssh_host or not settings.ssh_user:
            return jsonify({
                "success": False,
                "message": "SSH connection not configured. Please set SSH host and username."
            }), 400
        
        # Get parameters from request
        data = request.json
        source_path = data.get('source_path')
        destination_path = data.get('destination_path')
        
        # Validate parameters
        if not source_path or not destination_path:
            return jsonify({
                "success": False,
                "message": "Missing required parameters: source_path and/or destination_path"
            }), 400
        
        # Handle recursive flag
        recursive = data.get('recursive', True)
        
        # Use settings from database
        result = storage.transfer_files(
            source_path=source_path,
            destination_host=settings.ssh_host,
            destination_path=destination_path,
            username=settings.ssh_user,
            password=settings.ssh_password,
            key_path=settings.ssh_key_path,
            recursive=recursive
        )
        
        return jsonify(result)
    except Exception as e:
        logging.error(f"Error transferring files: {str(e)}")
        return jsonify({"error": str(e)}), 500

# Media Request Routes
@app.route('/media-requests')
def media_requests_page():
    """Page for viewing and submitting media requests"""
    requests = MediaRequest.query.order_by(MediaRequest.created_at.desc()).all()
    return render_template('media_requests.html', active_page='media-requests', requests=requests)

@app.route('/api/media-requests', methods=['GET', 'POST'])
def manage_media_requests():
    """API for managing media requests"""
    if request.method == 'POST':
        data = request.get_json()
        new_request = MediaRequest(
            title=data.get('title'),
            media_type=data.get('media_type'),
            description=data.get('description', ''),
            requester_name=data.get('requester_name', ''),
            status='Pending',
            created_at=datetime.now()
        )
        db.session.add(new_request)
        db.session.commit()
        return jsonify({"success": True, "id": new_request.id})
    else:
        requests = MediaRequest.query.all()
        return jsonify([{
            "id": req.id,
            "title": req.title,
            "media_type": req.media_type,
            "description": req.description,
            "requester_name": req.requester_name,
            "status": req.status,
            "notes": req.notes,
            "created_at": req.created_at.isoformat(),
            "updated_at": req.updated_at.isoformat()
        } for req in requests])

@app.route('/api/media-requests/<int:request_id>', methods=['GET', 'PUT', 'DELETE'])
def manage_media_request(request_id):
    """API for managing a specific media request"""
    req = MediaRequest.query.get_or_404(request_id)
    
    if request.method == 'GET':
        return jsonify({
            "id": req.id,
            "title": req.title,
            "media_type": req.media_type,
            "description": req.description,
            "requester_name": req.requester_name,
            "status": req.status,
            "notes": req.notes,
            "created_at": req.created_at.isoformat(),
            "updated_at": req.updated_at.isoformat()
        })
        
    elif request.method == 'PUT':
        data = request.get_json()
        
        # Only update fields that were provided
        if 'title' in data:
            req.title = data.get('title')
        if 'media_type' in data:
            req.media_type = data.get('media_type')
        if 'description' in data:
            req.description = data.get('description')
        if 'requester_name' in data:
            req.requester_name = data.get('requester_name')
        if 'status' in data:
            req.status = data.get('status')
        if 'notes' in data:
            req.notes = data.get('notes')
            
        db.session.commit()
        return jsonify({"success": True})
        
    elif request.method == 'DELETE':
        db.session.delete(req)
        db.session.commit()
        return jsonify({"success": True})

# Documentation APIs
@app.route('/api/docs', methods=['GET', 'POST'])
def manage_docs():
    if request.method == 'POST':
        data = request.get_json()
        new_doc = DocuEntry(
            title=data.get('title'),
            content=data.get('content'),
            tags=data.get('tags', ''),
            created_at=datetime.now()
        )
        db.session.add(new_doc)
        db.session.commit()
        return jsonify({"success": True, "id": new_doc.id})
    else:
        docs = DocuEntry.query.all()
        return jsonify([{
            "id": doc.id,
            "title": doc.title,
            "content": doc.content,
            "tags": doc.tags,
            "created_at": doc.created_at.isoformat()
        } for doc in docs])

@app.route('/api/docs/<int:doc_id>', methods=['GET', 'PUT', 'DELETE'])
def manage_doc(doc_id):
    doc = DocuEntry.query.get_or_404(doc_id)
    
    if request.method == 'GET':
        return jsonify({
            "id": doc.id,
            "title": doc.title,
            "content": doc.content,
            "tags": doc.tags,
            "created_at": doc.created_at.isoformat()
        })
        
    elif request.method == 'PUT':
        data = request.get_json()
        doc.title = data.get('title', doc.title)
        doc.content = data.get('content', doc.content)
        doc.tags = data.get('tags', doc.tags)
        db.session.commit()
        return jsonify({"success": True})
        
    elif request.method == 'DELETE':
        db.session.delete(doc)
        db.session.commit()
        return jsonify({"success": True})

# Scripts APIs
@app.route('/api/scripts', methods=['GET', 'POST'])
def manage_scripts():
    if request.method == 'POST':
        data = request.get_json()
        new_script = ScriptEntry(
            title=data.get('title'),
            description=data.get('description', ''),
            script_content=data.get('script_content'),
            script_type=data.get('script_type', 'bash'),
            created_at=datetime.now()
        )
        db.session.add(new_script)
        db.session.commit()
        return jsonify({"success": True, "id": new_script.id})
    else:
        scripts = ScriptEntry.query.all()
        return jsonify([{
            "id": script.id,
            "title": script.title,
            "description": script.description,
            "script_content": script.script_content,
            "script_type": script.script_type,
            "created_at": script.created_at.isoformat()
        } for script in scripts])

@app.route('/api/scripts/<int:script_id>', methods=['GET', 'PUT', 'DELETE'])
def manage_script(script_id):
    script = ScriptEntry.query.get_or_404(script_id)
    
    if request.method == 'GET':
        return jsonify({
            "id": script.id,
            "title": script.title,
            "description": script.description,
            "script_content": script.script_content,
            "script_type": script.script_type,
            "created_at": script.created_at.isoformat()
        })
        
    elif request.method == 'PUT':
        data = request.get_json()
        script.title = data.get('title', script.title)
        script.description = data.get('description', script.description)
        script.script_content = data.get('script_content', script.script_content)
        script.script_type = data.get('script_type', script.script_type)
        db.session.commit()
        return jsonify({"success": True})
        
    elif request.method == 'DELETE':
        db.session.delete(script)
        db.session.commit()
        return jsonify({"success": True})

# Error handlers
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def server_error(e):
    return render_template('500.html', error=str(e)), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
