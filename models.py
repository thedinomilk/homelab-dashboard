from app import db
from datetime import datetime

class UserSettings(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    proxmox_host = db.Column(db.String(255), nullable=True)
    proxmox_user = db.Column(db.String(255), nullable=True)
    proxmox_token_name = db.Column(db.String(255), nullable=True)
    proxmox_token_value = db.Column(db.String(255), nullable=True)
    docker_host = db.Column(db.String(255), nullable=True)
    docker_port = db.Column(db.Integer, default=2375)
    storage_paths = db.Column(db.Text, nullable=True)  # JSON string of storage paths

class DocuEntry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    content = db.Column(db.Text, nullable=False)
    tags = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class ScriptEntry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)
    script_content = db.Column(db.Text, nullable=False)
    script_type = db.Column(db.String(50), nullable=False, default='bash')  # bash, python, etc.
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
