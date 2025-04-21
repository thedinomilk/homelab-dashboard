import os
import json
import requests
from flask import Flask, render_template, jsonify, request, redirect, url_for
from dotenv import load_dotenv
from models import db, UserSettings, ProxmoxAnalysis, Recommendation, ImplementationPlan

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Configure database
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Initialize the database
db.init_app(app)

# Create all tables
with app.app_context():
    db.create_all()

class ProxmoxData:
    def __init__(self, data=None):
        self.data = data or {}
        
    def load_from_file(self, filepath):
        try:
            with open(filepath, 'r') as f:
                self.data = json.load(f)
            return True
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"Error loading data: {e}")
            return False
    
    def analyze_resource_utilization(self):
        """Analyze resource utilization across nodes, VMs, and containers"""
        analysis = {
            'cpu': {'total': 0, 'used': 0, 'percent': 0},
            'memory': {'total': 0, 'used': 0, 'percent': 0},
            'storage': {'total': 0, 'used': 0, 'percent': 0},
            'vms': {'total': 0, 'running': 0},
            'containers': {'total': 0, 'running': 0},
            'recommendations': []
        }
        
        # Node analysis
        if 'node_status' in self.data:
            node = self.data.get('node_status', {})
            if node:
                # CPU
                if 'cpu' in node:
                    cpu_usage = node['cpu'] * 100
                    analysis['cpu']['used'] = cpu_usage
                    analysis['cpu']['total'] = 100
                    analysis['cpu']['percent'] = cpu_usage
                    
                    if cpu_usage > 80:
                        analysis['recommendations'].append("CPU usage is high (>80%). Consider redistributing workloads or adding resources.")
                    elif cpu_usage < 20:
                        analysis['recommendations'].append("CPU usage is very low (<20%). Consider consolidating workloads to improve efficiency.")
                
                # Memory
                if 'memory' in node:
                    mem = node['memory']
                    total_gb = mem.get('total', 0) / 1024**3
                    used_gb = mem.get('used', 0) / 1024**3
                    mem_percent = (used_gb / total_gb * 100) if total_gb > 0 else 0
                    
                    analysis['memory']['total'] = round(total_gb, 2)
                    analysis['memory']['used'] = round(used_gb, 2)
                    analysis['memory']['percent'] = round(mem_percent, 2)
                    
                    if mem_percent > 85:
                        analysis['recommendations'].append("Memory usage is high (>85%). Consider adding more RAM or optimizing memory-intensive services.")
                    elif mem_percent < 30:
                        analysis['recommendations'].append("Memory usage is low (<30%). You may be able to run more services or reduce allocated memory.")
        
        # Storage analysis
        if 'storage' in self.data:
            storage_list = self.data.get('storage', [])
            total_storage = 0
            used_storage = 0
            
            for storage in storage_list:
                total_storage += storage.get('total', 0)
                used_storage += storage.get('used', 0)
            
            total_storage_gb = total_storage / 1024**3
            used_storage_gb = used_storage / 1024**3
            storage_percent = (used_storage_gb / total_storage_gb * 100) if total_storage_gb > 0 else 0
            
            analysis['storage']['total'] = round(total_storage_gb, 2)
            analysis['storage']['used'] = round(used_storage_gb, 2)
            analysis['storage']['percent'] = round(storage_percent, 2)
            
            if storage_percent > 85:
                analysis['recommendations'].append("Storage usage is high (>85%). Consider expanding storage or cleaning up unused data.")
            
            # Storage type analysis
            storage_types = set(s.get('type', '') for s in storage_list)
            if 'zfspool' not in storage_types and len(storage_list) > 1:
                analysis['recommendations'].append("Consider implementing ZFS for better data protection and storage efficiency.")
        
        # VM analysis
        if 'vms' in self.data:
            vms = self.data.get('vms', [])
            analysis['vms']['total'] = len(vms)
            analysis['vms']['running'] = sum(1 for vm in vms if vm.get('status') == 'running')
            
            # Check for overprovisioning
            total_allocated_cores = sum(vm.get('cpus', 0) for vm in vms if vm.get('status') == 'running')
            if 'node_status' in self.data and 'cpuinfo' in self.data['node_status']:
                physical_cores = self.data['node_status']['cpuinfo'].get('cpus', 0)
                if physical_cores > 0 and total_allocated_cores > physical_cores * 2:
                    analysis['recommendations'].append(f"CPU overprovisioning is high ({total_allocated_cores} vCPUs on {physical_cores} physical cores). Monitor for CPU contention.")
        
        # Container analysis
        if 'containers' in self.data:
            containers = self.data.get('containers', [])
            analysis['containers']['total'] = len(containers)
            analysis['containers']['running'] = sum(1 for c in containers if c.get('status') == 'running')
            
            # Compare efficiency of VMs vs Containers
            if analysis['vms']['total'] > 0 and analysis['containers']['total'] > 0:
                analysis['recommendations'].append("Consider converting more workloads to containers for better resource efficiency when appropriate.")
        
        return analysis
    
    def generate_architecture_recommendations(self):
        """Generate architectural recommendations based on the Proxmox setup"""
        recommendations = {
            'infrastructure': [],
            'virtualization': [],
            'storage': [],
            'networking': [],
            'services': [],
        }
        
        # Infrastructure recommendations
        nodes = self.data.get('nodes', [])
        if len(nodes) == 1:
            recommendations['infrastructure'].append("Current setup is a single node. Consider adding a second node for high availability if running critical services.")
        
        # Check for hardware capabilities
        if 'node_status' in self.data:
            if 'cpuinfo' in self.data['node_status']:
                cpu_info = self.data['node_status']['cpuinfo']
                cpu_flags = cpu_info.get('flags', '').split()
                
                # Check for virtualization extensions
                if 'vmx' in cpu_flags or 'svm' in cpu_flags:
                    recommendations['virtualization'].append("CPU supports hardware virtualization. Ensure VT-d/IOMMU is enabled in BIOS for PCI passthrough.")
                
                # Check processor generation
                cpu_model = cpu_info.get('model', '').lower()
                if 'intel' in cpu_model and any(gen in cpu_model for gen in ['3rd', '4th', '5th']):
                    recommendations['infrastructure'].append("You're running an older generation Intel CPU. Consider upgrading for better power efficiency and performance if running many VMs.")
        
        # Virtualization strategy
        vms = self.data.get('vms', [])
        containers = self.data.get('containers', [])
        
        if len(vms) > 0 and len(containers) == 0:
            recommendations['virtualization'].append("Consider using LXC containers for lightweight services like DHCP, DNS, or monitoring tools.")
        
        # Storage recommendations
        storage_list = self.data.get('storage', [])
        storage_types = [s.get('type') for s in storage_list]
        
        if 'dir' in storage_types and len(storage_list) > 1:
            recommendations['storage'].append("You're using directory storage. Consider migrating to ZFS, LVM, or Ceph for better performance and data protection.")
        
        if len(storage_list) > 2:
            recommendations['storage'].append("Multiple storage pools detected. Consider implementing tiered storage with SSD for VM disks and HDD for media/backups.")
        
        # Network recommendations
        if 'node_status' in self.data and 'network' in self.data['node_status']:
            network_interfaces = self.data['node_status'].get('network', {})
            if len(network_interfaces) == 1:
                recommendations['networking'].append("Single network interface detected. Consider adding a second NIC for dedicated VM traffic or storage network.")
            
            # VLAN recommendations
            has_vlans = any('.' in iface for iface in network_interfaces.keys())
            if not has_vlans and len(vms) > 3:
                recommendations['networking'].append("No VLANs detected. Consider implementing network segmentation with VLANs for better security and traffic management.")
        
        # Service recommendations based on current VMs
        vm_names = [vm.get('name', '').lower() for vm in vms]
        container_names = [c.get('name', '').lower() for c in containers]
        all_service_names = vm_names + container_names
        
        # Check for common services
        if not any('storage' in name or 'nas' in name for name in all_service_names):
            recommendations['services'].append("Consider running a NAS solution like TrueNAS or Synology for centralized storage management.")
        
        if not any('monitor' in name or 'grafana' in name or 'prometheus' in name for name in all_service_names):
            recommendations['services'].append("No monitoring solution detected. Consider implementing Grafana/Prometheus for comprehensive monitoring.")
        
        if not any('backup' in name for name in all_service_names):
            recommendations['services'].append("No dedicated backup solution detected. Consider implementing Proxmox Backup Server or another backup solution.")
        
        return recommendations

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/upload', methods=['POST'])
def upload_data():
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file part'}), 400
            
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No selected file'}), 400
            
        if file:
            # Save the file
            filepath = 'uploads/proxmox_data.json'
            os.makedirs('uploads', exist_ok=True)
            file.save(filepath)
            
            return jsonify({'success': True, 'message': 'File uploaded successfully'})
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/analyze', methods=['GET'])
def analyze_data():
    try:
        proxmox_data = ProxmoxData()
        filepath = 'uploads/proxmox_data.json'
        
        if not proxmox_data.load_from_file(filepath):
            # Try using proxmox_info.json if it exists
            filepath = 'uploads/proxmox_info.json'
            if not proxmox_data.load_from_file(filepath):
                return jsonify({'error': 'Failed to load data file'}), 404
        
        # Analyze the data
        analysis = proxmox_data.analyze_resource_utilization()
        recommendations = proxmox_data.generate_architecture_recommendations()
        
        # Save the analysis to the database
        with open(filepath, 'r') as f:
            raw_data = f.read()
            
        # Create a new analysis record
        new_analysis = ProxmoxAnalysis(
            raw_data=raw_data,
            cpu_usage=analysis['cpu']['percent'],
            memory_usage=analysis['memory']['percent'],
            storage_usage=analysis['storage']['percent'],
            vm_count=analysis['vms']['total'],
            container_count=analysis['containers']['total'],
            resource_analysis=json.dumps(analysis),
            recommendations=json.dumps(recommendations)
        )
        
        db.session.add(new_analysis)
        db.session.commit()
        
        # Add detailed recommendations
        for category, recs in recommendations.items():
            priority = 3  # Default priority
            
            # Set priority based on category (example logic)
            if category == 'infrastructure':
                priority = 1
            elif category in ['virtualization', 'storage']:
                priority = 2
            
            # Add each recommendation
            for rec_text in recs:
                recommendation = Recommendation(
                    analysis_id=new_analysis.id,
                    category=category,
                    recommendation=rec_text,
                    priority=priority
                )
                db.session.add(recommendation)
        
        db.session.commit()
        
        return jsonify({
            'analysis': analysis,
            'recommendations': recommendations,
            'analysis_id': new_analysis.id
        })
        
    except Exception as e:
        import traceback
        print(traceback.format_exc())
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    # Ensure templates directory exists
    os.makedirs('templates', exist_ok=True)
    
    # Create the HTML template if it doesn't exist
    if not os.path.exists('templates/index.html'):
        with open('templates/index.html', 'w') as f:
            f.write("""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Proxmox Homelab Architect</title>
    <link rel="stylesheet" href="https://cdn.replit.com/agent/bootstrap-agent-dark-theme.min.css">
    <style>
        body {
            padding-top: 2rem;
            padding-bottom: 2rem;
        }
        .recommendation-card {
            margin-bottom: 1rem;
        }
        .chart-container {
            position: relative;
            height: 200px;
            width: 100%;
        }
        .category-badge {
            font-size: 0.8rem;
        }
        .summary-card {
            border-left: 4px solid var(--bs-primary);
            background-color: var(--bs-dark);
        }
        .upload-area {
            border: 2px dashed var(--bs-secondary);
            border-radius: 5px;
            padding: 2rem;
            text-align: center;
            cursor: pointer;
            margin: 2rem 0;
        }
        .upload-area:hover {
            border-color: var(--bs-primary);
        }
        .resource-gauge {
            position: relative;
            height: 120px;
            margin-bottom: 1rem;
        }
        .analysis-section {
            display: none;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1 class="mb-4">Proxmox Homelab Architect</h1>
        
        <div class="row">
            <div class="col-md-8">
                <div class="card mb-4">
                    <div class="card-header">
                        <h2 class="card-title h5 mb-0">Upload Proxmox Data</h2>
                    </div>
                    <div class="card-body">
                        <p>Upload your Proxmox JSON data file to receive architecture recommendations.</p>
                        
                        <div id="uploadArea" class="upload-area">
                            <div id="uploadPrompt">
                                <i class="bi bi-cloud-upload fs-1"></i>
                                <p>Drag and drop your proxmox_info.json file here or click to browse</p>
                            </div>
                            <div id="uploadProgress" style="display:none;">
                                <div class="spinner-border text-primary" role="status">
                                    <span class="visually-hidden">Loading...</span>
                                </div>
                                <p>Uploading...</p>
                            </div>
                        </div>
                        <input type="file" id="fileInput" style="display:none;" accept=".json">
                    </div>
                </div>
                
                <div id="analysisSection" class="analysis-section">
                    <div class="card mb-4">
                        <div class="card-header">
                            <h2 class="card-title h5 mb-0">Resource Utilization</h2>
                        </div>
                        <div class="card-body">
                            <div class="row">
                                <div class="col-md-4">
                                    <div class="resource-gauge" id="cpuGauge"></div>
                                    <h5 class="text-center">CPU Usage</h5>
                                    <p class="text-center" id="cpuText">-</p>
                                </div>
                                <div class="col-md-4">
                                    <div class="resource-gauge" id="memoryGauge"></div>
                                    <h5 class="text-center">Memory Usage</h5>
                                    <p class="text-center" id="memoryText">-</p>
                                </div>
                                <div class="col-md-4">
                                    <div class="resource-gauge" id="storageGauge"></div>
                                    <h5 class="text-center">Storage Usage</h5>
                                    <p class="text-center" id="storageText">-</p>
                                </div>
                            </div>
                            
                            <div class="row mt-4">
                                <div class="col-md-6">
                                    <div class="card bg-dark">
                                        <div class="card-body">
                                            <h5 class="card-title">Virtual Machines</h5>
                                            <p class="fs-2" id="vmCount">- / -</p>
                                            <p class="text-muted">Running / Total</p>
                                        </div>
                                    </div>
                                </div>
                                <div class="col-md-6">
                                    <div class="card bg-dark">
                                        <div class="card-body">
                                            <h5 class="card-title">Containers</h5>
                                            <p class="fs-2" id="containerCount">- / -</p>
                                            <p class="text-muted">Running / Total</p>
                                        </div>
                                    </div>
                                </div>
                            </div>
                            
                            <div class="mt-4">
                                <h5>Performance Recommendations</h5>
                                <ul id="performanceRecommendations" class="list-group">
                                    <li class="list-group-item bg-dark">No recommendations available yet</li>
                                </ul>
                            </div>
                        </div>
                    </div>
                    
                    <div class="card mb-4">
                        <div class="card-header">
                            <h2 class="card-title h5 mb-0">Architecture Recommendations</h2>
                        </div>
                        <div class="card-body">
                            <div class="accordion" id="recommendationsAccordion">
                                <div class="accordion-item bg-dark">
                                    <h2 class="accordion-header">
                                        <button class="accordion-button" type="button" data-bs-toggle="collapse" data-bs-target="#infrastructureCollapse" aria-expanded="true" aria-controls="infrastructureCollapse">
                                            Infrastructure Design
                                        </button>
                                    </h2>
                                    <div id="infrastructureCollapse" class="accordion-collapse collapse show" data-bs-parent="#recommendationsAccordion">
                                        <div class="accordion-body">
                                            <ul id="infrastructureRecommendations" class="list-group">
                                                <li class="list-group-item bg-dark">No recommendations available yet</li>
                                            </ul>
                                        </div>
                                    </div>
                                </div>
                                
                                <div class="accordion-item bg-dark">
                                    <h2 class="accordion-header">
                                        <button class="accordion-button collapsed" type="button" data-bs-toggle="collapse" data-bs-target="#virtualizationCollapse" aria-expanded="false" aria-controls="virtualizationCollapse">
                                            Virtualization Strategy
                                        </button>
                                    </h2>
                                    <div id="virtualizationCollapse" class="accordion-collapse collapse" data-bs-parent="#recommendationsAccordion">
                                        <div class="accordion-body">
                                            <ul id="virtualizationRecommendations" class="list-group">
                                                <li class="list-group-item bg-dark">No recommendations available yet</li>
                                            </ul>
                                        </div>
                                    </div>
                                </div>
                                
                                <div class="accordion-item bg-dark">
                                    <h2 class="accordion-header">
                                        <button class="accordion-button collapsed" type="button" data-bs-toggle="collapse" data-bs-target="#storageCollapse" aria-expanded="false" aria-controls="storageCollapse">
                                            Storage Architecture
                                        </button>
                                    </h2>
                                    <div id="storageCollapse" class="accordion-collapse collapse" data-bs-parent="#recommendationsAccordion">
                                        <div class="accordion-body">
                                            <ul id="storageRecommendations" class="list-group">
                                                <li class="list-group-item bg-dark">No recommendations available yet</li>
                                            </ul>
                                        </div>
                                    </div>
                                </div>
                                
                                <div class="accordion-item bg-dark">
                                    <h2 class="accordion-header">
                                        <button class="accordion-button collapsed" type="button" data-bs-toggle="collapse" data-bs-target="#networkingCollapse" aria-expanded="false" aria-controls="networkingCollapse">
                                            Network Planning
                                        </button>
                                    </h2>
                                    <div id="networkingCollapse" class="accordion-collapse collapse" data-bs-parent="#recommendationsAccordion">
                                        <div class="accordion-body">
                                            <ul id="networkingRecommendations" class="list-group">
                                                <li class="list-group-item bg-dark">No recommendations available yet</li>
                                            </ul>
                                        </div>
                                    </div>
                                </div>
                                
                                <div class="accordion-item bg-dark">
                                    <h2 class="accordion-header">
                                        <button class="accordion-button collapsed" type="button" data-bs-toggle="collapse" data-bs-target="#servicesCollapse" aria-expanded="false" aria-controls="servicesCollapse">
                                            Service Deployment
                                        </button>
                                    </h2>
                                    <div id="servicesCollapse" class="accordion-collapse collapse" data-bs-parent="#recommendationsAccordion">
                                        <div class="accordion-body">
                                            <ul id="servicesRecommendations" class="list-group">
                                                <li class="list-group-item bg-dark">No recommendations available yet</li>
                                            </ul>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="col-md-4">
                <div class="card mb-4">
                    <div class="card-header">
                        <h3 class="card-title h5 mb-0">How It Works</h3>
                    </div>
                    <div class="card-body">
                        <ol>
                            <li>Set up the Proxmox agent on your container.</li>
                            <li>The agent creates a JSON file with your Proxmox data.</li>
                            <li>Upload that JSON file here.</li>
                            <li>Get personalized architecture recommendations.</li>
                        </ol>
                        
                        <div class="alert alert-info mt-3">
                            <h5>Need help?</h5>
                            <p>If you need assistance creating the agent or exporting data, ask for help!</p>
                        </div>
                    </div>
                </div>
                
                <div class="card mb-4">
                    <div class="card-header">
                        <h3 class="card-title h5 mb-0">Homelab Resources</h3>
                    </div>
                    <ul class="list-group list-group-flush">
                        <li class="list-group-item bg-dark">
                            <a href="https://www.proxmox.com/en/downloads/category/documentation-pdf" target="_blank" class="text-decoration-none">Proxmox VE Documentation</a>
                        </li>
                        <li class="list-group-item bg-dark">
                            <a href="https://pve.proxmox.com/wiki/Category:HOWTO" target="_blank" class="text-decoration-none">Proxmox HOWTOs</a>
                        </li>
                        <li class="list-group-item bg-dark">
                            <a href="https://www.reddit.com/r/homelab/" target="_blank" class="text-decoration-none">r/homelab Community</a>
                        </li>
                        <li class="list-group-item bg-dark">
                            <a href="https://forum.proxmox.com/" target="_blank" class="text-decoration-none">Proxmox Forums</a>
                        </li>
                    </ul>
                </div>
            </div>
        </div>
    </div>
    
    <!-- Import Chart.js before your script -->
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    
    <script>
        document.addEventListener('DOMContentLoaded', function() {
            // Reference DOM elements
            const uploadArea = document.getElementById('uploadArea');
            const fileInput = document.getElementById('fileInput');
            const uploadPrompt = document.getElementById('uploadPrompt');
            const uploadProgress = document.getElementById('uploadProgress');
            const analysisSection = document.getElementById('analysisSection');
            
            // Gauge charts
            let cpuGauge, memoryGauge, storageGauge;
            
            // Initialize charts
            function initializeCharts() {
                // CPU Gauge
                cpuGauge = new Chart(document.getElementById('cpuGauge'), {
                    type: 'doughnut',
                    data: {
                        datasets: [{
                            data: [0, 100],
                            backgroundColor: ['#0d6efd', '#212529']
                        }]
                    },
                    options: {
                        cutout: '70%',
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {
                            tooltip: { enabled: false },
                            legend: { display: false }
                        }
                    }
                });
                
                // Memory Gauge
                memoryGauge = new Chart(document.getElementById('memoryGauge'), {
                    type: 'doughnut',
                    data: {
                        datasets: [{
                            data: [0, 100],
                            backgroundColor: ['#198754', '#212529']
                        }]
                    },
                    options: {
                        cutout: '70%',
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {
                            tooltip: { enabled: false },
                            legend: { display: false }
                        }
                    }
                });
                
                // Storage Gauge
                storageGauge = new Chart(document.getElementById('storageGauge'), {
                    type: 'doughnut',
                    data: {
                        datasets: [{
                            data: [0, 100],
                            backgroundColor: ['#dc3545', '#212529']
                        }]
                    },
                    options: {
                        cutout: '70%',
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {
                            tooltip: { enabled: false },
                            legend: { display: false }
                        }
                    }
                });
            }
            
            // Handle file uploads
            uploadArea.addEventListener('click', () => {
                fileInput.click();
            });
            
            fileInput.addEventListener('change', handleFileUpload);
            
            uploadArea.addEventListener('dragover', (e) => {
                e.preventDefault();
                uploadArea.classList.add('border-primary');
            });
            
            uploadArea.addEventListener('dragleave', () => {
                uploadArea.classList.remove('border-primary');
            });
            
            uploadArea.addEventListener('drop', (e) => {
                e.preventDefault();
                uploadArea.classList.remove('border-primary');
                
                if (e.dataTransfer.files.length) {
                    fileInput.files = e.dataTransfer.files;
                    handleFileUpload();
                }
            });
            
            function handleFileUpload() {
                if (!fileInput.files.length) return;
                
                const file = fileInput.files[0];
                if (!file.name.endsWith('.json')) {
                    alert('Please upload a JSON file');
                    return;
                }
                
                // Show upload progress
                uploadPrompt.style.display = 'none';
                uploadProgress.style.display = 'block';
                
                const formData = new FormData();
                formData.append('file', file);
                
                fetch('/api/upload', {
                    method: 'POST',
                    body: formData
                })
                .then(response => response.json())
                .then(data => {
                    if (data.error) {
                        alert('Upload error: ' + data.error);
                        uploadPrompt.style.display = 'block';
                        uploadProgress.style.display = 'none';
                        return;
                    }
                    
                    // Initialize charts if not already done
                    if (!cpuGauge) {
                        initializeCharts();
                    }
                    
                    // Fetch analysis
                    analysisSection.style.display = 'block';
                    fetchAnalysis();
                })
                .catch(error => {
                    console.error('Error:', error);
                    alert('Upload failed. Please try again.');
                    uploadPrompt.style.display = 'block';
                    uploadProgress.style.display = 'none';
                });
            }
            
            function fetchAnalysis() {
                fetch('/api/analyze')
                .then(response => response.json())
                .then(data => {
                    // Hide progress indicator
                    uploadPrompt.style.display = 'block';
                    uploadProgress.style.display = 'none';
                    
                    if (data.error) {
                        alert('Analysis error: ' + data.error);
                        return;
                    }
                    
                    updateAnalysisUI(data.analysis, data.recommendations);
                })
                .catch(error => {
                    console.error('Error:', error);
                    alert('Analysis failed. Please try again.');
                    uploadPrompt.style.display = 'block';
                    uploadProgress.style.display = 'none';
                });
            }
            
            function updateAnalysisUI(analysis, recommendations) {
                // Update resource gauges
                updateGauge(cpuGauge, analysis.cpu.percent);
                updateGauge(memoryGauge, analysis.memory.percent);
                updateGauge(storageGauge, analysis.storage.percent);
                
                // Update text information
                document.getElementById('cpuText').textContent = `${analysis.cpu.percent.toFixed(1)}%`;
                document.getElementById('memoryText').textContent = `${analysis.memory.used}GB / ${analysis.memory.total}GB (${analysis.memory.percent.toFixed(1)}%)`;
                document.getElementById('storageText').textContent = `${analysis.storage.used}GB / ${analysis.storage.total}GB (${analysis.storage.percent.toFixed(1)}%)`;
                document.getElementById('vmCount').textContent = `${analysis.vms.running} / ${analysis.vms.total}`;
                document.getElementById('containerCount').textContent = `${analysis.containers.running} / ${analysis.containers.total}`;
                
                // Update performance recommendations
                const perfRecommendationsEl = document.getElementById('performanceRecommendations');
                perfRecommendationsEl.innerHTML = '';
                
                if (analysis.recommendations.length === 0) {
                    perfRecommendationsEl.innerHTML = '<li class="list-group-item bg-dark">No performance recommendations at this time.</li>';
                } else {
                    analysis.recommendations.forEach(rec => {
                        const li = document.createElement('li');
                        li.className = 'list-group-item bg-dark';
                        li.textContent = rec;
                        perfRecommendationsEl.appendChild(li);
                    });
                }
                
                // Update architecture recommendations
                updateRecommendationsList('infrastructureRecommendations', recommendations.infrastructure);
                updateRecommendationsList('virtualizationRecommendations', recommendations.virtualization);
                updateRecommendationsList('storageRecommendations', recommendations.storage);
                updateRecommendationsList('networkingRecommendations', recommendations.networking);
                updateRecommendationsList('servicesRecommendations', recommendations.services);
            }
            
            function updateRecommendationsList(elementId, recommendationsList) {
                const element = document.getElementById(elementId);
                element.innerHTML = '';
                
                if (!recommendationsList || recommendationsList.length === 0) {
                    element.innerHTML = '<li class="list-group-item bg-dark">No recommendations available.</li>';
                    return;
                }
                
                recommendationsList.forEach(rec => {
                    const li = document.createElement('li');
                    li.className = 'list-group-item bg-dark';
                    li.textContent = rec;
                    element.appendChild(li);
                });
            }
            
            function updateGauge(chart, value) {
                chart.data.datasets[0].data[0] = value;
                chart.data.datasets[0].data[1] = 100 - value;
                chart.update();
            }
        });
    </script>
</body>
</html>""")
    
    # Create uploads directory
    os.makedirs('uploads', exist_ok=True)
    
    # Start the app
    app.run(host='0.0.0.0', port=5000, debug=True)