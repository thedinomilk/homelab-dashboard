document.addEventListener('DOMContentLoaded', function() {
    // DOM elements
    const newRequestBtn = document.getElementById('newRequestBtn');
    const requestModal = new bootstrap.Modal(document.getElementById('requestModal'));
    const requestForm = document.getElementById('requestForm');
    const requestId = document.getElementById('requestId');
    const saveRequestBtn = document.getElementById('saveRequestBtn');
    const deleteRequestBtn = document.getElementById('deleteRequestBtn');
    const adminFields = document.getElementById('adminFields');

    // Event listeners
    newRequestBtn.addEventListener('click', showNewRequestForm);
    saveRequestBtn.addEventListener('click', saveRequest);
    deleteRequestBtn.addEventListener('click', deleteRequest);
    
    // Add event listeners to view buttons
    document.querySelectorAll('.view-request').forEach(button => {
        button.addEventListener('click', function() {
            const id = this.getAttribute('data-id');
            loadRequestDetails(id);
        });
    });

    // Functions
    function showNewRequestForm() {
        // Reset the form
        requestForm.reset();
        requestId.value = '';
        
        // Hide admin fields
        adminFields.classList.add('d-none');
        
        // Update UI
        document.getElementById('requestModalLabel').textContent = 'New Media Request';
        saveRequestBtn.textContent = 'Submit Request';
        deleteRequestBtn.classList.add('d-none');
        
        // Show the modal
        requestModal.show();
    }
    
    function loadRequestDetails(id) {
        fetch(`/api/media-requests/${id}`)
            .then(response => {
                if (!response.ok) {
                    throw new Error('Network response was not ok');
                }
                return response.json();
            })
            .then(data => {
                displayRequestDetails(data);
            })
            .catch(error => {
                console.error('Error loading request details:', error);
                showToast('Error loading request details', 'error');
            });
    }
    
    function displayRequestDetails(request) {
        const statusBadge = getStatusBadge(request.status);
        const typeBadge = getTypeBadge(request.media_type);
        
        // Format dates
        const createdDate = new Date(request.created_at).toLocaleDateString();
        const updatedDate = new Date(request.updated_at).toLocaleDateString();
        
        // Build HTML for details panel
        const detailsHtml = `
            <div class="card-header bg-primary text-white">
                <h5 class="mb-0">${request.title}</h5>
            </div>
            <div class="card-body">
                <div class="d-flex justify-content-between mb-3">
                    <div>${typeBadge}</div>
                    <div>${statusBadge}</div>
                </div>
                
                <h6>Description</h6>
                <p>${request.description || 'No description provided'}</p>
                
                <div class="row mt-3">
                    <div class="col-md-6">
                        <p class="mb-1"><strong>Requester:</strong></p>
                        <p>${request.requester_name || 'Anonymous'}</p>
                    </div>
                    <div class="col-md-6">
                        <p class="mb-1"><strong>Requested:</strong></p>
                        <p>${createdDate}</p>
                    </div>
                </div>
                
                ${request.notes ? `
                <div class="mt-3">
                    <h6>Admin Notes</h6>
                    <p>${request.notes}</p>
                </div>
                ` : ''}
                
                <div class="mt-4">
                    <button class="btn btn-primary btn-sm edit-request-btn" data-id="${request.id}">
                        <i class="fas fa-edit me-1"></i> Edit
                    </button>
                </div>
            </div>
        `;
        
        // Update the details panel
        document.getElementById('requestDetails').innerHTML = detailsHtml;
        
        // Add event listener to edit button
        document.querySelector('.edit-request-btn').addEventListener('click', function() {
            editRequest(request.id);
        });
    }
    
    function editRequest(id) {
        fetch(`/api/media-requests/${id}`)
            .then(response => {
                if (!response.ok) {
                    throw new Error('Network response was not ok');
                }
                return response.json();
            })
            .then(data => {
                // Populate the form
                requestId.value = data.id;
                document.getElementById('title').value = data.title;
                document.getElementById('mediaType').value = data.media_type;
                document.getElementById('description').value = data.description || '';
                document.getElementById('requesterName').value = data.requester_name || '';
                
                // Populate admin fields
                document.getElementById('status').value = data.status;
                document.getElementById('notes').value = data.notes || '';
                
                // Show admin fields
                adminFields.classList.remove('d-none');
                
                // Update UI
                document.getElementById('requestModalLabel').textContent = 'Edit Media Request';
                saveRequestBtn.textContent = 'Update Request';
                deleteRequestBtn.classList.remove('d-none');
                
                // Show the modal
                requestModal.show();
            })
            .catch(error => {
                console.error('Error loading request for edit:', error);
                showToast('Error loading request details', 'error');
            });
    }
    
    function saveRequest() {
        // Validate the form
        if (!requestForm.checkValidity()) {
            requestForm.reportValidity();
            return;
        }
        
        // Build request data
        const data = {
            title: document.getElementById('title').value,
            media_type: document.getElementById('mediaType').value,
            description: document.getElementById('description').value,
            requester_name: document.getElementById('requesterName').value
        };
        
        // Include admin fields if visible
        if (!adminFields.classList.contains('d-none')) {
            data.status = document.getElementById('status').value;
            data.notes = document.getElementById('notes').value;
        }
        
        // Determine if this is a create or update
        const id = requestId.value;
        const url = id ? `/api/media-requests/${id}` : '/api/media-requests';
        const method = id ? 'PUT' : 'POST';
        
        // Send the request
        fetch(url, {
            method: method,
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(data),
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(result => {
            // Close the modal
            requestModal.hide();
            
            // Show success message
            const message = id ? 'Request updated successfully' : 'Request submitted successfully';
            showToast(message, 'success');
            
            // Reload the page to show updated data
            setTimeout(() => {
                window.location.reload();
            }, 1000);
        })
        .catch(error => {
            console.error('Error saving request:', error);
            showToast('Error saving request', 'error');
        });
    }
    
    function deleteRequest() {
        const id = requestId.value;
        if (!id) return;
        
        if (!confirm('Are you sure you want to delete this request?')) {
            return;
        }
        
        fetch(`/api/media-requests/${id}`, {
            method: 'DELETE',
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(result => {
            // Close the modal
            requestModal.hide();
            
            // Show success message
            showToast('Request deleted successfully', 'success');
            
            // Reload the page to show updated data
            setTimeout(() => {
                window.location.reload();
            }, 1000);
        })
        .catch(error => {
            console.error('Error deleting request:', error);
            showToast('Error deleting request', 'error');
        });
    }
    
    // Helper functions
    function getStatusBadge(status) {
        const badgeClass = {
            'Pending': 'bg-warning',
            'Approved': 'bg-success',
            'Downloading': 'bg-info',
            'Completed': 'bg-primary',
            'Rejected': 'bg-danger'
        }[status] || 'bg-secondary';
        
        return `<span class="badge ${badgeClass}">${status}</span>`;
    }
    
    function getTypeBadge(type) {
        const badgeClass = {
            'movie': 'bg-info',
            'tv_show': 'bg-success',
            'audiobook': 'bg-warning'
        }[type] || 'bg-secondary';
        
        const label = {
            'movie': 'Movie',
            'tv_show': 'TV Show',
            'audiobook': 'Audiobook'
        }[type] || type;
        
        return `<span class="badge ${badgeClass}">${label}</span>`;
    }
    
    function showToast(message, type = 'info') {
        // Create toast container if it doesn't exist
        let toastContainer = document.querySelector('.toast-container');
        if (!toastContainer) {
            toastContainer = document.createElement('div');
            toastContainer.className = 'toast-container position-fixed bottom-0 end-0 p-3';
            document.body.appendChild(toastContainer);
        }
        
        // Create toast element
        const toastId = 'toast-' + Date.now();
        const bgClass = type === 'error' ? 'bg-danger' : 
                        type === 'success' ? 'bg-success' : 
                        'bg-info';
        
        const toastHtml = `
            <div id="${toastId}" class="toast" role="alert" aria-live="assertive" aria-atomic="true">
                <div class="toast-header ${bgClass} text-white">
                    <strong class="me-auto">Notification</strong>
                    <button type="button" class="btn-close btn-close-white" data-bs-dismiss="toast" aria-label="Close"></button>
                </div>
                <div class="toast-body">
                    ${message}
                </div>
            </div>
        `;
        
        // Add toast to container
        toastContainer.innerHTML += toastHtml;
        
        // Initialize and show the toast
        const toastElement = document.getElementById(toastId);
        const toast = new bootstrap.Toast(toastElement, { autohide: true, delay: 5000 });
        toast.show();
        
        // Remove toast after it's hidden
        toastElement.addEventListener('hidden.bs.toast', function() {
            toastElement.remove();
        });
    }
});