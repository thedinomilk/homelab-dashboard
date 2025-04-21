document.addEventListener('DOMContentLoaded', function() {
    // Load the docker containers
    loadContainers();
    
    // Set up refresh button
    document.getElementById('refresh-containers').addEventListener('click', function() {
        loadContainers();
    });
    
    // Set up container action confirmation
    setupContainerActionModal();
    
    // Load container resources
    loadContainerResources();
    
    // Set up periodic refresh (every 30 seconds)
    setInterval(function() {
        loadContainers();
        loadContainerResources();
    }, 30000);
});

// Load containers list from API
function loadContainers() {
    const containersTable = document.getElementById('containers-table');
    const containersWrapper = document.getElementById('containers-table-wrapper');
    const loadingDiv = document.getElementById('containers-list').querySelector('.text-center');
    const noContainersMessage = document.getElementById('no-containers-message');
    const connectionError = document.getElementById('connection-error');
    
    // Show loading, hide other elements
    loadingDiv.style.display = 'block';
    containersWrapper.style.display = 'none';
    noContainersMessage.style.display = 'none';
    connectionError.style.display = 'none';
    
    fetch('/api/docker/containers')
        .then(response => {
            if (!response.ok) {
                throw new Error('Failed to fetch containers');
            }
            return response.json();
        })
        .then(data => {
            // Update container stats
            updateContainerStats(data);
            
            if (data.length === 0) {
                // No containers found
                loadingDiv.style.display = 'none';
                noContainersMessage.style.display = 'block';
                return;
            }
            
            // Create table rows for containers
            let tableHtml = '';
            
            data.forEach(container => {
                const containerId = container.Id;
                const name = container.Name;
                const image = container.Image;
                const status = container.Status;
                const created = container.CreatedFormatted || 'Unknown';
                const ports = container.PortsFormatted.join(', ') || 'None';
                const statusClass = container.StatusClass || 'secondary';
                
                // Determine which action buttons to show based on status
                let actionButtons = '';
                
                if (status.includes('Up')) {
                    actionButtons = `
                        <button class="btn btn-sm btn-outline-warning container-action" data-action="restart" data-id="${containerId}" data-name="${name}">
                            <i class="fas fa-sync-alt"></i>
                        </button>
                        <button class="btn btn-sm btn-outline-danger container-action" data-action="stop" data-id="${containerId}" data-name="${name}">
                            <i class="fas fa-stop"></i>
                        </button>
                    `;
                } else {
                    actionButtons = `
                        <button class="btn btn-sm btn-outline-success container-action" data-action="start" data-id="${containerId}" data-name="${name}">
                            <i class="fas fa-play"></i>
                        </button>
                    `;
                }
                
                tableHtml += `
                    <tr>
                        <td>${name}</td>
                        <td>${image}</td>
                        <td><span class="badge bg-${statusClass}">${status}</span></td>
                        <td>${created}</td>
                        <td>${ports}</td>
                        <td>
                            <div class="btn-group" role="group">
                                ${actionButtons}
                            </div>
                        </td>
                    </tr>
                `;
            });
            
            containersTable.innerHTML = tableHtml;
            
            // Add event listeners to action buttons
            document.querySelectorAll('.container-action').forEach(button => {
                button.addEventListener('click', handleContainerAction);
            });
            
            // Hide loading, show table
            loadingDiv.style.display = 'none';
            containersWrapper.style.display = 'block';
        })
        .catch(error => {
            console.error('Error loading containers:', error);
            loadingDiv.style.display = 'none';
            connectionError.style.display = 'block';
            connectionError.textContent = `Connection error: ${error.message}`;
        });
}

// Update container statistics display
function updateContainerStats(containers) {
    const runningCount = document.getElementById('running-count');
    const stoppedCount = document.getElementById('stopped-count');
    const pausedCount = document.getElementById('paused-count');
    const totalCount = document.getElementById('total-count');
    
    let running = 0;
    let stopped = 0;
    let paused = 0;
    
    containers.forEach(container => {
        const status = container.Status.toLowerCase();
        if (status.includes('up')) {
            running++;
        } else if (status.includes('paused')) {
            paused++;
        } else {
            stopped++;
        }
    });
    
    runningCount.textContent = running;
    stoppedCount.textContent = stopped;
    pausedCount.textContent = paused;
    totalCount.textContent = containers.length;
}

// Set up container action confirmation modal
function setupContainerActionModal() {
    const modal = new bootstrap.Modal(document.getElementById('containerActionModal'));
    const confirmBtn = document.getElementById('confirmActionBtn');
    
    confirmBtn.addEventListener('click', function() {
        const action = this.dataset.action;
        const containerId = this.dataset.containerId;
        
        performContainerAction(action, containerId);
        modal.hide();
    });
}

// Handle container action button click
function handleContainerAction(event) {
    const button = event.currentTarget;
    const action = button.dataset.action;
    const containerId = button.dataset.id;
    const containerName = button.dataset.name;
    
    // Update modal content
    const modalTitle = document.getElementById('containerActionModalLabel');
    const modalMessage = document.getElementById('containerActionMessage');
    const confirmBtn = document.getElementById('confirmActionBtn');
    
    let actionTitle, actionMessage, actionButtonClass;
    
    switch (action) {
        case 'start':
            actionTitle = 'Start Container';
            actionMessage = `Are you sure you want to start container "${containerName}"?`;
            actionButtonClass = 'btn-success';
            break;
        case 'stop':
            actionTitle = 'Stop Container';
            actionMessage = `Are you sure you want to stop container "${containerName}"?`;
            actionButtonClass = 'btn-danger';
            break;
        case 'restart':
            actionTitle = 'Restart Container';
            actionMessage = `Are you sure you want to restart container "${containerName}"?`;
            actionButtonClass = 'btn-warning';
            break;
    }
    
    modalTitle.textContent = actionTitle;
    modalMessage.textContent = actionMessage;
    confirmBtn.className = `btn ${actionButtonClass}`;
    confirmBtn.textContent = 'Confirm ' + action.charAt(0).toUpperCase() + action.slice(1);
    
    // Store action data
    confirmBtn.dataset.action = action;
    confirmBtn.dataset.containerId = containerId;
    
    // Show modal
    const modal = new bootstrap.Modal(document.getElementById('containerActionModal'));
    modal.show();
}

// Perform container action (start, stop, restart)
function performContainerAction(action, containerId) {
    // Show processing indicator on button
    const actionButtons = document.querySelectorAll(`.container-action[data-id="${containerId}"]`);
    actionButtons.forEach(button => {
        button.disabled = true;
        const icon = button.querySelector('i');
        const originalClass = icon.className;
        icon.className = 'fas fa-spinner fa-spin';
        
        // Store original class for restoration
        button.dataset.originalIcon = originalClass;
    });
    
    // Call API to perform action
    fetch(`/api/docker/container/${containerId}/${action}`, {
        method: 'POST'
    })
    .then(response => {
        if (!response.ok) {
            return response.json().then(err => { throw new Error(err.error || `Failed to ${action} container`); });
        }
        return response.json();
    })
    .then(result => {
        // Success message
        const message = `Container ${action}ed successfully`;
        showToast(message, 'success');
        
        // Reload containers after a short delay
        setTimeout(() => {
            loadContainers();
        }, 1000);
    })
    .catch(error => {
        console.error(`Error ${action}ing container:`, error);
        
        // Restore action buttons
        actionButtons.forEach(button => {
            button.disabled = false;
            const icon = button.querySelector('i');
            icon.className = button.dataset.originalIcon;
        });
        
        // Show error message
        showToast(`Error: ${error.message}`, 'danger');
    });
}

// Load container resource charts
let resourcesChart;
function loadContainerResources() {
    const resourcesLoading = document.getElementById('container-resources-loading');
    const resourcesDiv = document.getElementById('container-resources');
    const resourcesError = document.getElementById('resources-error');
    
    resourcesLoading.style.display = 'block';
    resourcesDiv.style.display = 'none';
    resourcesError.style.display = 'none';
    
    // First get container list
    fetch('/api/docker/containers')
        .then(response => {
            if (!response.ok) {
                throw new Error('Failed to fetch containers');
            }
            return response.json();
        })
        .then(containers => {
            // Filter for running containers only
            const runningContainers = containers.filter(container => 
                container.Status.toLowerCase().includes('up')
            );
            
            if (runningContainers.length === 0) {
                throw new Error('No running containers to show resource usage for');
            }
            
            // Create placeholder data for the chart
            // In a real implementation, you would fetch actual stats for each container
            const resourceData = {
                labels: runningContainers.map(container => container.Name),
                cpuData: runningContainers.map(() => Math.random() * 30),
                memoryData: runningContainers.map(() => Math.random() * 50)
            };
            
            updateResourcesChart(resourceData);
            
            resourcesLoading.style.display = 'none';
            resourcesDiv.style.display = 'block';
        })
        .catch(error => {
            console.error('Error loading container resources:', error);
            resourcesLoading.style.display = 'none';
            resourcesError.style.display = 'block';
            resourcesError.textContent = `Cannot load container resources: ${error.message}`;
        });
}

// Update container resources chart
function updateResourcesChart(data) {
    const ctx = document.getElementById('containerResourcesChart').getContext('2d');
    
    // Destroy existing chart if it exists
    if (resourcesChart) {
        resourcesChart.destroy();
    }
    
    resourcesChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: data.labels,
            datasets: [
                {
                    label: 'CPU Usage (%)',
                    data: data.cpuData,
                    backgroundColor: 'rgba(54, 162, 235, 0.6)',
                    borderColor: 'rgba(54, 162, 235, 1)',
                    borderWidth: 1
                },
                {
                    label: 'Memory Usage (%)',
                    data: data.memoryData,
                    backgroundColor: 'rgba(255, 99, 132, 0.6)',
                    borderColor: 'rgba(255, 99, 132, 1)',
                    borderWidth: 1
                }
            ]
        },
        options: {
            responsive: true,
            scales: {
                y: {
                    beginAtZero: true,
                    max: 100,
                    title: {
                        display: true,
                        text: 'Usage (%)'
                    }
                }
            },
            plugins: {
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return context.dataset.label + ': ' + context.raw.toFixed(1) + '%';
                        }
                    }
                }
            }
        }
    });
}

// Show a toast message
function showToast(message, type = 'info') {
    // Create toast container if it doesn't exist
    let toastContainer = document.querySelector('.toast-container');
    if (!toastContainer) {
        toastContainer = document.createElement('div');
        toastContainer.className = 'toast-container position-fixed bottom-0 end-0 p-3';
        document.body.appendChild(toastContainer);
    }
    
    // Create toast element
    const toastElement = document.createElement('div');
    toastElement.className = `toast align-items-center text-white bg-${type} border-0`;
    toastElement.setAttribute('role', 'alert');
    toastElement.setAttribute('aria-live', 'assertive');
    toastElement.setAttribute('aria-atomic', 'true');
    
    toastElement.innerHTML = `
        <div class="d-flex">
            <div class="toast-body">
                ${message}
            </div>
            <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
        </div>
    `;
    
    toastContainer.appendChild(toastElement);
    
    // Initialize and show the toast
    const toast = new bootstrap.Toast(toastElement, {
        autohide: true,
        delay: 3000
    });
    toast.show();
    
    // Remove toast after it's hidden
    toastElement.addEventListener('hidden.bs.toast', function() {
        toastElement.remove();
    });
}
