document.addEventListener('DOMContentLoaded', function() {
    // Initialize dashboard components
    checkProxmoxStatus();
    checkDockerStatus();
    checkStorageStatus();
    loadResourceUsage();
    loadNodeList();
    loadDockerContainerSummary();
    loadStorageSummary();
    
    // Set up refresh timer (every 60 seconds)
    setInterval(function() {
        checkProxmoxStatus();
        checkDockerStatus();
        checkStorageStatus();
        loadResourceUsage();
        loadNodeList();
        loadDockerContainerSummary();
        loadStorageSummary();
    }, 60000);
});

// Check status of Proxmox connection
function checkProxmoxStatus() {
    const statusIndicator = document.getElementById('proxmox-status-indicator');
    const statusText = document.getElementById('proxmox-status-text');
    
    fetch('/api/proxmox/nodes')
        .then(response => {
            if (!response.ok) {
                return response.json().then(err => { throw new Error(err.error || 'Failed to connect'); });
            }
            return response.json();
        })
        .then(data => {
            statusIndicator.className = 'status-indicator status-success';
            statusText.textContent = `Connected (${data.length} nodes)`;
            statusText.className = 'mt-3 text-success';
        })
        .catch(error => {
            statusIndicator.className = 'status-indicator status-error';
            statusText.textContent = 'Connection Error';
            statusText.className = 'mt-3 text-danger';
            console.error('Proxmox connection error:', error);
        });
}

// Check status of Docker connection
function checkDockerStatus() {
    const statusIndicator = document.getElementById('docker-status-indicator');
    const statusText = document.getElementById('docker-status-text');
    
    fetch('/api/docker/containers')
        .then(response => {
            if (!response.ok) {
                return response.json().then(err => { throw new Error(err.error || 'Failed to connect'); });
            }
            return response.json();
        })
        .then(data => {
            statusIndicator.className = 'status-indicator status-success';
            statusText.textContent = `Connected (${data.length} containers)`;
            statusText.className = 'mt-3 text-success';
        })
        .catch(error => {
            statusIndicator.className = 'status-indicator status-error';
            statusText.textContent = 'Connection Error';
            statusText.className = 'mt-3 text-danger';
            console.error('Docker connection error:', error);
        });
}

// Check status of Storage
function checkStorageStatus() {
    const statusIndicator = document.getElementById('storage-status-indicator');
    const statusText = document.getElementById('storage-status-text');
    
    fetch('/api/storage/info')
        .then(response => {
            if (!response.ok) {
                return response.json().then(err => { throw new Error(err.error || 'Failed to connect'); });
            }
            return response.json();
        })
        .then(data => {
            statusIndicator.className = 'status-indicator status-success';
            statusText.textContent = `Connected (${data.length} mounts)`;
            statusText.className = 'mt-3 text-success';
        })
        .catch(error => {
            statusIndicator.className = 'status-indicator status-error';
            statusText.textContent = 'Connection Error';
            statusText.className = 'mt-3 text-danger';
            console.error('Storage connection error:', error);
        });
}

// Load resource usage chart
function loadResourceUsage() {
    // Try to get resources from Proxmox
    fetch('/api/proxmox/resources')
        .then(response => {
            if (!response.ok) {
                throw new Error('Failed to fetch resource data');
            }
            return response.json();
        })
        .then(data => {
            // Process data for chart
            const resources = processResourceData(data);
            updateResourceChart(resources);
        })
        .catch(error => {
            console.error('Error loading resource data:', error);
            // Show demo/placeholder data
            const placeholderData = {
                cpuUsage: 35,
                memoryUsage: 48,
                diskUsage: 72
            };
            updateResourceChart(placeholderData);
        });
}

// Process resource data from Proxmox for chart display
function processResourceData(data) {
    // Initialize counters
    let cpuTotal = 0;
    let cpuUsed = 0;
    let memTotal = 0;
    let memUsed = 0;
    let diskTotal = 0;
    let diskUsed = 0;
    
    // Process node resources
    const nodes = data.filter(item => item.type === 'node');
    nodes.forEach(node => {
        // CPU
        if (node.maxcpu) {
            cpuTotal += node.maxcpu;
        }
        if (node.cpu) {
            cpuUsed += node.cpu * (node.maxcpu || 1);
        }
        
        // Memory
        if (node.maxmem) {
            memTotal += node.maxmem;
        }
        if (node.mem) {
            memUsed += node.mem;
        }
    });
    
    // Process storage resources
    const storages = data.filter(item => item.type === 'storage');
    storages.forEach(storage => {
        if (storage.maxdisk) {
            diskTotal += storage.maxdisk;
        }
        if (storage.disk) {
            diskUsed += storage.disk;
        }
    });
    
    // Calculate percentages
    const cpuUsage = cpuTotal > 0 ? Math.round((cpuUsed / cpuTotal) * 100) : 0;
    const memoryUsage = memTotal > 0 ? Math.round((memUsed / memTotal) * 100) : 0;
    const diskUsage = diskTotal > 0 ? Math.round((diskUsed / diskTotal) * 100) : 0;
    
    return {
        cpuUsage,
        memoryUsage,
        diskUsage
    };
}

// Create or update the resource chart
let resourceChart;
function updateResourceChart(resources) {
    const ctx = document.getElementById('resourceChart').getContext('2d');
    
    const data = {
        labels: ['CPU', 'Memory', 'Disk'],
        datasets: [{
            label: 'Usage (%)',
            data: [
                resources.cpuUsage,
                resources.memoryUsage,
                resources.diskUsage
            ],
            backgroundColor: [
                'rgba(54, 162, 235, 0.6)',
                'rgba(255, 99, 132, 0.6)',
                'rgba(255, 206, 86, 0.6)'
            ],
            borderColor: [
                'rgba(54, 162, 235, 1)',
                'rgba(255, 99, 132, 1)',
                'rgba(255, 206, 86, 1)'
            ],
            borderWidth: 1
        }]
    };
    
    const options = {
        responsive: true,
        scales: {
            y: {
                beginAtZero: true,
                max: 100,
                ticks: {
                    callback: function(value) {
                        return value + '%';
                    }
                }
            }
        },
        plugins: {
            legend: {
                display: false
            },
            tooltip: {
                callbacks: {
                    label: function(context) {
                        return context.raw + '% usage';
                    }
                }
            }
        }
    };
    
    // Destroy existing chart if it exists
    if (resourceChart) {
        resourceChart.destroy();
    }
    
    // Create new chart
    resourceChart = new Chart(ctx, {
        type: 'bar',
        data: data,
        options: options
    });
}

// Load node list
function loadNodeList() {
    const nodeList = document.getElementById('node-list');
    
    fetch('/api/proxmox/nodes')
        .then(response => {
            if (!response.ok) {
                throw new Error('Failed to fetch node data');
            }
            return response.json();
        })
        .then(data => {
            let html = '';
            
            if (data.length === 0) {
                html = `
                    <div class="list-group-item text-center">
                        <p class="mb-0">No nodes found</p>
                        <small class="text-muted">Check Proxmox connection settings</small>
                    </div>
                `;
            } else {
                data.forEach(node => {
                    let statusClass = 'success';
                    let statusText = 'Online';
                    
                    if (node.status !== 'online') {
                        statusClass = 'danger';
                        statusText = node.status || 'Offline';
                    }
                    
                    html += `
                        <div class="list-group-item">
                            <div class="d-flex justify-content-between align-items-center">
                                <h6 class="mb-0">${node.node}</h6>
                                <span class="badge bg-${statusClass}">${statusText}</span>
                            </div>
                            <small class="text-muted">
                                CPU: ${node.cpu ? (node.cpu * 100).toFixed(1) + '%' : 'N/A'} | 
                                Memory: ${node.mem && node.maxmem ? formatBytes(node.mem) + ' / ' + formatBytes(node.maxmem) : 'N/A'}
                            </small>
                        </div>
                    `;
                });
            }
            
            nodeList.innerHTML = html;
        })
        .catch(error => {
            console.error('Error loading node list:', error);
            nodeList.innerHTML = `
                <div class="list-group-item text-center text-danger">
                    <i class="fas fa-exclamation-circle mb-2"></i>
                    <p class="mb-0">Error loading nodes</p>
                    <small>${error.message}</small>
                </div>
            `;
        });
}

// Load Docker container summary
function loadDockerContainerSummary() {
    const containerSummary = document.getElementById('docker-container-summary');
    
    fetch('/api/docker/containers')
        .then(response => {
            if (!response.ok) {
                throw new Error('Failed to fetch container data');
            }
            return response.json();
        })
        .then(data => {
            let html = '';
            
            if (data.length === 0) {
                html = `
                    <div class="list-group-item text-center">
                        <p class="mb-0">No containers found</p>
                        <small class="text-muted">No Docker containers are running</small>
                    </div>
                `;
            } else {
                // Limit to 5 containers for the summary
                const containers = data.slice(0, 5);
                
                containers.forEach(container => {
                    const status = container.Status || '';
                    let statusClass = 'secondary';
                    
                    if (status.includes('Up')) {
                        statusClass = 'success';
                    } else if (status.includes('Exited')) {
                        statusClass = 'danger';
                    }
                    
                    html += `
                        <div class="list-group-item">
                            <div class="d-flex justify-content-between align-items-center">
                                <h6 class="mb-0">${container.Name}</h6>
                                <span class="badge bg-${statusClass}">${status}</span>
                            </div>
                            <small class="text-muted">
                                ${container.Image.split(':')[0]}
                                ${container.PortsFormatted.length > 0 ? ' | Ports: ' + container.PortsFormatted.join(', ') : ''}
                            </small>
                        </div>
                    `;
                });
            }
            
            containerSummary.innerHTML = html;
        })
        .catch(error => {
            console.error('Error loading container summary:', error);
            containerSummary.innerHTML = `
                <div class="list-group-item text-center text-danger">
                    <i class="fas fa-exclamation-circle mb-2"></i>
                    <p class="mb-0">Error loading containers</p>
                    <small>${error.message}</small>
                </div>
            `;
        });
}

// Load storage summary and chart
let storageChart;
function loadStorageSummary() {
    fetch('/api/storage/info')
        .then(response => {
            if (!response.ok) {
                throw new Error('Failed to fetch storage data');
            }
            return response.json();
        })
        .then(data => {
            updateStorageChart(data);
        })
        .catch(error => {
            console.error('Error loading storage summary:', error);
            // Create placeholder chart
            updateStorageChart([]);
        });
}

// Update storage doughnut chart
function updateStorageChart(storageData) {
    const ctx = document.getElementById('storageChart').getContext('2d');
    
    // Prepare chart data
    let labels = [];
    let used = [];
    let free = [];
    let backgroundColors = [];
    
    if (storageData.length === 0) {
        // Placeholder data
        labels = ['No Storage Data'];
        used = [0];
        free = [100];
        backgroundColors = ['rgba(200, 200, 200, 0.6)'];
    } else {
        // Process real data
        const colorPool = [
            'rgba(54, 162, 235, 0.6)',
            'rgba(255, 99, 132, 0.6)',
            'rgba(255, 206, 86, 0.6)',
            'rgba(75, 192, 192, 0.6)',
            'rgba(153, 102, 255, 0.6)',
            'rgba(255, 159, 64, 0.6)'
        ];
        
        storageData.forEach((item, index) => {
            if (item.exists && !item.error) {
                labels.push(item.path);
                used.push(item.used_gb);
                free.push(item.free_gb);
                backgroundColors.push(colorPool[index % colorPool.length]);
            }
        });
    }
    
    const data = {
        labels: labels,
        datasets: [{
            label: 'Used (GB)',
            data: used,
            backgroundColor: backgroundColors,
            borderWidth: 1
        }, {
            label: 'Free (GB)',
            data: free,
            backgroundColor: backgroundColors.map(color => color.replace('0.6', '0.3')),
            borderWidth: 1
        }]
    };
    
    const options = {
        responsive: true,
        plugins: {
            legend: {
                position: 'right',
                labels: {
                    boxWidth: 12
                }
            },
            tooltip: {
                callbacks: {
                    label: function(context) {
                        const datasetLabel = context.dataset.label || '';
                        return datasetLabel + ': ' + context.raw + ' GB';
                    }
                }
            }
        }
    };
    
    // Destroy existing chart if it exists
    if (storageChart) {
        storageChart.destroy();
    }
    
    // Create new chart
    storageChart = new Chart(ctx, {
        type: 'doughnut',
        data: data,
        options: options
    });
}

// Format bytes to human-readable format
function formatBytes(bytes, decimals = 2) {
    if (bytes === 0) return '0 Bytes';
    
    const k = 1024;
    const dm = decimals < 0 ? 0 : decimals;
    const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB', 'PB', 'EB', 'ZB', 'YB'];
    
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    
    return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i];
}
