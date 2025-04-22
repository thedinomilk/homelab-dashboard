from datetime import datetime
from database import db

class UserSettings(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    proxmox_host = db.Column(db.String(255), nullable=True)
    proxmox_user = db.Column(db.String(255), nullable=True)
    proxmox_token_name = db.Column(db.String(255), nullable=True)
    proxmox_token_value = db.Column(db.String(255), nullable=True)
    docker_host = db.Column(db.String(255), nullable=True)
    docker_port = db.Column(db.Integer, default=2375)
    storage_paths = db.Column(db.Text, nullable=True)  # JSON string of storage paths
    
    # SSH settings for remote ZFS management
    ssh_host = db.Column(db.String(255), nullable=True)
    ssh_user = db.Column(db.String(255), nullable=True)
    ssh_password = db.Column(db.String(255), nullable=True)
    ssh_key_path = db.Column(db.String(255), nullable=True)
    
    def __repr__(self):
        return f'<UserSettings {self.id}>'
        
class MediaRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    media_type = db.Column(db.String(50), nullable=False)  # movie, tv_show, audiobook
    description = db.Column(db.Text, nullable=True)
    requester_name = db.Column(db.String(100), nullable=True)
    status = db.Column(db.String(50), default='Pending')  # Pending, Approved, Downloading, Completed, Rejected
    notes = db.Column(db.Text, nullable=True)  # Admin notes/comments
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<MediaRequest {self.id} - {self.title}>'

class ProxmoxAnalysis(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    analysis_date = db.Column(db.DateTime, default=datetime.utcnow)
    raw_data = db.Column(db.Text, nullable=False)  # JSON string of Proxmox data
    cpu_usage = db.Column(db.Float, nullable=True)
    memory_usage = db.Column(db.Float, nullable=True)
    storage_usage = db.Column(db.Float, nullable=True)
    vm_count = db.Column(db.Integer, nullable=True)
    container_count = db.Column(db.Integer, nullable=True)
    
    # Store analysis results
    resource_analysis = db.Column(db.Text, nullable=True)  # JSON string
    recommendations = db.Column(db.Text, nullable=True)  # JSON string
    
    def __repr__(self):
        return f'<ProxmoxAnalysis {self.id} - {self.analysis_date}>'

class Recommendation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    analysis_id = db.Column(db.Integer, db.ForeignKey('proxmox_analysis.id'), nullable=False)
    category = db.Column(db.String(50), nullable=False)  # infrastructure, virtualization, storage, network, services
    recommendation = db.Column(db.Text, nullable=False)
    priority = db.Column(db.Integer, default=3)  # 1-5, with 1 being highest priority
    implemented = db.Column(db.Boolean, default=False)
    implementation_date = db.Column(db.DateTime, nullable=True)
    
    # Relationship to parent analysis
    analysis = db.relationship('ProxmoxAnalysis', backref=db.backref('detailed_recommendations', lazy=True))
    
    def __repr__(self):
        return f'<Recommendation {self.id} - {self.category}>'

class ImplementationPlan(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)
    category = db.Column(db.String(50), nullable=False)
    steps = db.Column(db.Text, nullable=True)  # JSON array of implementation steps
    status = db.Column(db.String(20), default='Planned')  # Planned, In Progress, Completed, Abandoned
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<ImplementationPlan {self.id} - {self.title}>'

class DocuEntry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    content = db.Column(db.Text, nullable=False)
    tags = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<DocuEntry {self.id} - {self.title}>'

class ScriptEntry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)
    script_content = db.Column(db.Text, nullable=False)
    script_type = db.Column(db.String(50), default='bash')  # bash, python, etc.
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<ScriptEntry {self.id} - {self.title}>'