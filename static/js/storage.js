document.addEventListener('DOMContentLoaded', function() {
    // Initialize storage components
    loadStorageOverview();
    loadStorageDetails();
    loadZFSPools();
    initializeStorageTrends();
    
    // Setup refresh buttons
    document.getElementById('refresh-storage').addEventListener('click', function() {
        loadStorageOverview();
        loadStorageDetails();
    });
    
    document.getElementById('refresh-zpools').addEventListener('click', function() {
        loadZFSPools();
    });
    
    // Setup ZFS pool deletion modal
    const deletePoolModal = new bootstrap.Modal(document.getElementById('deletePoolModal'));
    let poolToDelete = '';
    
    // Event delegation for delete pool buttons (will be added dynamically)
    document.addEventListener('click', function(event) {
        if (event.target.classList.contains('delete-pool-btn') || 
            event.target.closest('.delete-pool-btn')) {
            const button = event.target.classList.contains('delete-pool-btn') ? 
                          event.target : 
                          event.target.closest('.delete-pool-btn');
            poolToDelete = button.dataset.pool;
            
            // Update modal content with pool name
            document.getElementById('pool-name-to-delete').textContent = poolToDelete;
            
            // Show modal
            deletePoolModal.show();
        }
    });
    
    // Confirm delete button
    document.getElementById('confirm-delete-pool').addEventListener('click', function() {
        if (poolToDelete) {
            deleteZFSPool(poolToDelete);
            deletePoolModal.hide();
        }
    });
    
    // Auto refresh every 2 minutes
    setInterval(function() {
        loadStorageOverview();
        loadStorageDetails();
        loadZFSPools();
    }, 120000);
});

// Storage overview - main storage summary
let storageDonutChart;
function loadStorageOverview() {
    const loadingDiv = document.getElementById('storage-overview-loading');
    const storageOverview = document.getElementById('storage-overview');
    const storageError = document.getElementById('storage-error');
    
    // Show loading state
    loadingDiv.style.display = 'block';
    storageOverview.style.display = 'none';
    storageError.style.display = 'none';
    
    fetch('/api/storage/info')
        .then(response => {
            if (!response.ok) {
                return response.json().then(err => { throw new Error(err.error || 'Failed to load storage information'); });
            }
            return response.json();
        })
        .then(data => {
            if (data.length === 0) {
                throw new Error('No storage paths configured or accessible');
            }
            
            // Update summary table
            updateStorageSummaryTable(data);
            
            // Update donut chart
            updateStorageDonutChart(data);
            
            // Hide loading, show content
            loadingDiv.style.display = 'none';
            storageOverview.style.display = 'block';
        })
        .catch(error => {
            console.error('Error loading storage overview:', error);
            storageError.textContent = `Error: ${error.message}`;
            storageError.style.display = 'block';
            loadingDiv.style.display = 'none';
        });
}

// Update storage summary table
function updateStorageSummaryTable(storageData) {
    const table = document.getElementById('storage-summary-table').querySelector('tbody');
    let html = '';
    
    storageData.forEach(storage => {
        if (storage.exists && !storage.error) {
            const usagePercent = storage.percent_used;
            let usageClass = 'success';
            
            if (usagePercent > 85) {
                usageClass = 'danger';
            } else if (usagePercent > 70) {
                usageClass = 'warning';
            }
            
            html += `
                <tr>
                    <td>${storage.path}</td>
                    <td>${storage.total_gb} GB</td>
                    <td>${storage.used_gb} GB</td>
                    <td>${storage.free_gb} GB</td>
                    <td>
                        <div class="d-flex align-items-center">
                            <div class="progress flex-grow-1 me-2" style="height: 6px;">
                                <div class="progress-bar bg-${usageClass}" role="progressbar" 
                                     style="width: ${usagePercent}%;" 
                                     aria-valuenow="${usagePercent}" 
                                     aria-valuemin="0" 
                                     aria-valuemax="100">
                                </div>
                            </div>
                            <span>${usagePercent}%</span>
                        </div>
                    </td>
                </tr>
            `;
        } else {
            // Display error for this storage path
            html += `
                <tr class="table-danger">
                    <td>${storage.path}</td>
                    <td colspan="4">
                        <i class="fas fa-exclamation-triangle me-1"></i>
                        ${storage.error || 'Path not accessible'}
                    </td>
                </tr>
            `;
        }
    });
    
    table.innerHTML = html;
}

// Update storage donut chart
function updateStorageDonutChart(storageData) {
    const ctx = document.getElementById('storageDonutChart').getContext('2d');
    
    // Prepare data for chart
    const labels = [];
    const usedData = [];
    const freeData = [];
    const backgroundColors = [
        'rgba(54, 162, 235, 0.8)',
        'rgba(255, 99, 132, 0.8)',
        'rgba(255, 206, 86, 0.8)',
        'rgba(75, 192, 192, 0.8)',
        'rgba(153, 102, 255, 0.8)',
        'rgba(255, 159, 64, 0.8)'
    ];
    
    // Process storage data
    storageData.forEach((storage, index) => {
        if (storage.exists && !storage.error) {
            labels.push(storage.path);
            usedData.push(storage.used_gb);
            freeData.push(storage.free_gb);
        }
    });
    
    // If no valid storage, add placeholder
    if (labels.length === 0) {
        labels.push('No storage data');
        usedData.push(0);
        freeData.push(100);
    }
    
    // Destroy existing chart if it exists
    if (storageDonutChart) {
        storageDonutChart.destroy();
    }
    
    // Create new chart
    storageDonutChart = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: labels,
            datasets: [{
                label: 'Used Space (GB)',
                data: usedData,
                backgroundColor: backgroundColors,
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            cutout: '65%',
            plugins: {
                legend: {
                    position: 'right',
                    labels: {
                        boxWidth: 12,
                        font: {
                            size: 11
                        }
                    }
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const total = usedData[context.dataIndex] + freeData[context.dataIndex];
                            const percentage = Math.round((usedData[context.dataIndex] / total) * 100);
                            return `${context.label}: ${usedData[context.dataIndex]} GB (${percentage}%) used of ${total} GB`;
                        }
                    }
                }
            }
        }
    });
}

// Load detailed storage information
function loadStorageDetails() {
    const loadingDiv = document.getElementById('storage-details-loading');
    const storageDetails = document.getElementById('storage-details');
    
    // Show loading state
    loadingDiv.style.display = 'block';
    storageDetails.style.display = 'none';
    
    fetch('/api/storage/info')
        .then(response => {
            if (!response.ok) {
                return response.json().then(err => { throw new Error(err.error || 'Failed to load storage details'); });
            }
            return response.json();
        })
        .then(data => {
            const storageCards = document.getElementById('storage-cards');
            let html = '';
            
            if (data.length === 0) {
                html = `
                    <div class="col-12">
                        <div class="alert alert-info">
                            <i class="fas fa-info-circle me-2"></i>
                            No storage paths configured. Please add storage paths in settings.
                        </div>
                    </div>
                `;
            } else {
                data.forEach(storage => {
                    if (storage.exists && !storage.error) {
                        // Calculate usage class based on percentage
                        const usagePercent = storage.percent_used;
                        let usageClass = 'success';
                        let usageIcon = 'check-circle';
                        
                        if (usagePercent > 85) {
                            usageClass = 'danger';
                            usageIcon = 'exclamation-circle';
                        } else if (usagePercent > 70) {
                            usageClass = 'warning';
                            usageIcon = 'exclamation-triangle';
                        }
                        
                        html += `
                            <div class="col-md-6 mb-4">
                                <div class="card h-100">
                                    <div class="card-header bg-dark">
                                        <div class="d-flex justify-content-between align-items-center">
                                            <span><i class="fas fa-hdd me-2"></i> ${storage.path}</span>
                                            <span class="badge bg-${usageClass}">
                                                <i class="fas fa-${usageIcon} me-1"></i>
                                                ${usagePercent}% Used
                                            </span>
                                        </div>
                                    </div>
                                    <div class="card-body">
                                        <div class="mb-3">
                                            <div class="progress" style="height: 10px;">
                                                <div class="progress-bar bg-${usageClass}" role="progressbar" 
                                                     style="width: ${usagePercent}%;" 
                                                     aria-valuenow="${usagePercent}" 
                                                     aria-valuemin="0" 
                                                     aria-valuemax="100">
                                                </div>
                                            </div>
                                        </div>
                                        <div class="row mb-2">
                                            <div class="col-4 text-center border-end">
                                                <div class="mb-1 text-muted small">Total</div>
                                                <div class="fw-bold">${storage.total_gb} GB</div>
                                            </div>
                                            <div class="col-4 text-center border-end">
                                                <div class="mb-1 text-muted small">Used</div>
                                                <div class="fw-bold text-${usageClass}">${storage.used_gb} GB</div>
                                            </div>
                                            <div class="col-4 text-center">
                                                <div class="mb-1 text-muted small">Free</div>
                                                <div class="fw-bold">${storage.free_gb} GB</div>
                                            </div>
                                        </div>
                                        <div class="mt-3">
                                            <small class="text-muted">
                                                <i class="fas fa-info-circle me-1"></i>
                                                Filesystem: ${storage.filesystem || 'Unknown'}
                                            </small>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        `;
                    } else {
                        // Error card for inaccessible storage
                        html += `
                            <div class="col-md-6 mb-4">
                                <div class="card h-100 border-danger">
                                    <div class="card-header bg-danger text-white">
                                        <i class="fas fa-exclamation-triangle me-2"></i>
                                        ${storage.path}
                                    </div>
                                    <div class="card-body">
                                        <div class="alert alert-danger mb-0">
                                            ${storage.error || 'Storage path is not accessible'}
                                        </div>
                                    </div>
                                </div>
                            </div>
                        `;
                    }
                });
            }
            
            storageCards.innerHTML = html;
            
            // Hide loading, show content
            loadingDiv.style.display = 'none';
            storageDetails.style.display = 'block';
        })
        .catch(error => {
            console.error('Error loading storage details:', error);
            
            // Show error message
            document.getElementById('storage-cards').innerHTML = `
                <div class="col-12">
                    <div class="alert alert-danger">
                        <i class="fas fa-exclamation-circle me-2"></i>
                        Error loading storage details: ${error.message}
                    </div>
                </div>
            `;
            
            loadingDiv.style.display = 'none';
            storageDetails.style.display = 'block';
        });
}

// Initialize storage trends chart with placeholder data
// In a real implementation, you would fetch historical data from a database
// Load ZFS pools
function loadZFSPools() {
    const loadingDiv = document.getElementById('zpools-loading');
    const zpoolsContent = document.getElementById('zpools-content');
    const zpoolsError = document.getElementById('zpools-error');
    const noZpools = document.getElementById('no-zpools');
    
    // Show loading state
    loadingDiv.style.display = 'block';
    zpoolsContent.style.display = 'none';
    zpoolsError.style.display = 'none';
    
    fetch('/api/storage/zpool/list')
        .then(response => {
            if (!response.ok) {
                return response.json().then(err => { throw new Error(err.error || 'Failed to load ZFS pool information'); });
            }
            return response.json();
        })
        .then(data => {
            // Hide loading state
            loadingDiv.style.display = 'none';
            zpoolsContent.style.display = 'block';
            
            if (!data.success) {
                throw new Error(data.message || 'Failed to retrieve ZFS pool information');
            }
            
            const poolsTable = document.getElementById('zpools-table').querySelector('tbody');
            
            if (!data.pools || data.pools.length === 0) {
                poolsTable.innerHTML = '';
                noZpools.style.display = 'block';
                return;
            }
            
            noZpools.style.display = 'none';
            
            // Update the table with pool information
            let html = '';
            data.pools.forEach(pool => {
                // Determine health status color
                let healthClass = 'success';
                if (pool.health !== 'ONLINE') {
                    healthClass = pool.health === 'DEGRADED' ? 'warning' : 'danger';
                }
                
                html += `
                    <tr>
                        <td>${pool.name}</td>
                        <td>${pool.size}</td>
                        <td>${pool.allocated}</td>
                        <td>${pool.free}</td>
                        <td><span class="badge bg-${healthClass}">${pool.health}</span></td>
                        <td>
                            <button class="btn btn-sm btn-danger delete-pool-btn" data-pool="${pool.name}">
                                <i class="fas fa-trash-alt me-1"></i> Delete
                            </button>
                        </td>
                    </tr>
                `;
            });
            
            poolsTable.innerHTML = html;
        })
        .catch(error => {
            console.error('Error loading ZFS pools:', error);
            zpoolsError.textContent = `Error: ${error.message}`;
            zpoolsError.style.display = 'block';
            loadingDiv.style.display = 'none';
        });
}

// Delete a ZFS pool
function deleteZFSPool(poolName) {
    // Show a toast notification that deletion is in progress
    showToast(`Deleting ZFS pool "${poolName}"...`, 'info');
    
    fetch(`/api/storage/zpool/delete/${poolName}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        }
    })
    .then(response => {
        if (!response.ok) {
            return response.json().then(err => { throw new Error(err.error || 'Failed to delete ZFS pool'); });
        }
        return response.json();
    })
    .then(data => {
        if (data.success) {
            showToast(data.message, 'success');
            // Refresh the ZFS pools list
            loadZFSPools();
        } else {
            showToast(`Error: ${data.message}`, 'danger');
        }
    })
    .catch(error => {
        console.error('Error deleting ZFS pool:', error);
        showToast(`Error: ${error.message}`, 'danger');
    });
}

// Helper function to display toast notifications
function showToast(message, type = 'info') {
    const toastContainer = document.querySelector('.toast-container');
    
    // Create toast container if it doesn't exist
    if (!toastContainer) {
        const container = document.createElement('div');
        container.className = 'toast-container position-fixed bottom-0 end-0 p-3';
        document.body.appendChild(container);
    }
    
    // Create toast element
    const toastEl = document.createElement('div');
    toastEl.className = `toast align-items-center text-white bg-${type} border-0`;
    toastEl.setAttribute('role', 'alert');
    toastEl.setAttribute('aria-live', 'assertive');
    toastEl.setAttribute('aria-atomic', 'true');
    
    // Create toast content
    toastEl.innerHTML = `
        <div class="d-flex">
            <div class="toast-body">
                ${message}
            </div>
            <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
        </div>
    `;
    
    // Add toast to container
    const container = document.querySelector('.toast-container');
    container.appendChild(toastEl);
    
    // Initialize and show toast
    const toast = new bootstrap.Toast(toastEl, { autohide: true, delay: 5000 });
    toast.show();
    
    // Remove toast element after it's hidden
    toastEl.addEventListener('hidden.bs.toast', function() {
        toastEl.remove();
    });
}

let storageTrendsChart;
function initializeStorageTrends() {
    const ctx = document.getElementById('storageTrendsChart').getContext('2d');
    
    // Generate some placeholder timestamps (last 7 days)
    const timestamps = [];
    const now = new Date();
    for (let i = 6; i >= 0; i--) {
        const date = new Date(now);
        date.setDate(date.getDate() - i);
        timestamps.push(date.toISOString().split('T')[0]);
    }
    
    // Empty datasets - would be populated with actual data in a real implementation
    const datasets = [];
    
    // Create a note that this is placeholder data
    const chartText = {
        id: 'chartText',
        beforeDraw(chart) {
            const ctx = chart.ctx;
            ctx.save();
            ctx.fillStyle = 'rgba(255, 255, 255, 0.7)';
            ctx.textAlign = 'center';
            ctx.textBaseline = 'middle';
            ctx.font = '14px Arial';
            ctx.fillText('Data collection in progress...', chart.width / 2, chart.height / 2);
            ctx.restore();
        }
    };
    
    // Destroy existing chart if it exists
    if (storageTrendsChart) {
        storageTrendsChart.destroy();
    }
    
    // Create new chart
    storageTrendsChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: timestamps,
            datasets: datasets
        },
        options: {
            responsive: true,
            scales: {
                y: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: 'Storage Used (GB)'
                    }
                }
            },
            plugins: {
                title: {
                    display: true,
                    text: 'Storage Usage Trends'
                },
                tooltip: {
                    mode: 'index',
                    intersect: false
                }
            }
        },
        plugins: [chartText]
    });
}
