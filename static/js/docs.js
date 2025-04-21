document.addEventListener('DOMContentLoaded', function() {
    // Initialize documentation page
    setupDocumentationUI();
    
    // Set up form submission
    const docForm = document.getElementById('document-form');
    docForm.addEventListener('submit', handleDocFormSubmit);
    
    // Cancel button handler
    document.getElementById('cancel-doc-btn').addEventListener('click', function() {
        resetDocForm();
        showDocPlaceholder();
    });
    
    // New document button
    document.getElementById('new-doc-btn').addEventListener('click', function() {
        resetDocForm();
        showDocForm();
    });
    
    // Attach event listeners to doc items in list
    attachDocItemListeners();
    
    // Delete confirmation setup
    document.getElementById('confirm-delete-btn').addEventListener('click', function() {
        const docId = this.getAttribute('data-doc-id');
        if (docId) {
            deleteDocument(docId);
        }
    });
});

// Set up the documentation UI
function setupDocumentationUI() {
    // Initial state - hide form, show placeholder
    document.getElementById('doc-form').style.display = 'none';
    document.getElementById('doc-view').classList.add('d-none');
    document.getElementById('doc-placeholder').style.display = 'block';
    document.getElementById('doc-actions').style.display = 'none';
}

// Attach event listeners to all document items in the list
function attachDocItemListeners() {
    const docItems = document.querySelectorAll('.doc-item');
    
    docItems.forEach(item => {
        item.addEventListener('click', function() {
            const docId = this.getAttribute('data-id');
            loadDocumentDetails(docId);
            
            // Highlight the selected item
            docItems.forEach(i => i.classList.remove('active'));
            this.classList.add('active');
        });
    });
}

// Handle document form submission
function handleDocFormSubmit(event) {
    event.preventDefault();
    
    const docId = document.getElementById('doc-id').value;
    const title = document.getElementById('doc-title').value;
    const tags = document.getElementById('doc-tags').value;
    const content = document.getElementById('doc-content').value;
    
    // Form validation
    if (!title.trim() || !content.trim()) {
        showToast('Title and content are required', 'danger');
        return;
    }
    
    const docData = {
        title: title,
        tags: tags,
        content: content
    };
    
    if (docId) {
        // Update existing document
        updateDocument(docId, docData);
    } else {
        // Create new document
        createNewDocument(docData);
    }
}

// Create a new document
function createNewDocument(docData) {
    fetch('/api/docs', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(docData)
    })
    .then(response => {
        if (!response.ok) {
            return response.json().then(err => { throw new Error(err.error || 'Failed to create document'); });
        }
        return response.json();
    })
    .then(result => {
        showToast('Document created successfully', 'success');
        
        // Reload the page to show the new document in the list
        window.location.reload();
    })
    .catch(error => {
        console.error('Error creating document:', error);
        showToast(`Error: ${error.message}`, 'danger');
    });
}

// Update an existing document
function updateDocument(docId, docData) {
    fetch(`/api/docs/${docId}`, {
        method: 'PUT',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(docData)
    })
    .then(response => {
        if (!response.ok) {
            return response.json().then(err => { throw new Error(err.error || 'Failed to update document'); });
        }
        return response.json();
    })
    .then(result => {
        showToast('Document updated successfully', 'success');
        
        // Switch to view mode and reload document
        loadDocumentDetails(docId);
    })
    .catch(error => {
        console.error('Error updating document:', error);
        showToast(`Error: ${error.message}`, 'danger');
    });
}

// Delete a document
function deleteDocument(docId) {
    fetch(`/api/docs/${docId}`, {
        method: 'DELETE'
    })
    .then(response => {
        if (!response.ok) {
            return response.json().then(err => { throw new Error(err.error || 'Failed to delete document'); });
        }
        return response.json();
    })
    .then(result => {
        showToast('Document deleted successfully', 'success');
        
        // Close the modal
        const modal = bootstrap.Modal.getInstance(document.getElementById('deleteDocModal'));
        modal.hide();
        
        // Reload the page to update the list
        window.location.reload();
    })
    .catch(error => {
        console.error('Error deleting document:', error);
        showToast(`Error: ${error.message}`, 'danger');
    });
}

// Load document details by ID
function loadDocumentDetails(docId) {
    fetch(`/api/docs/${docId}`)
        .then(response => {
            if (!response.ok) {
                return response.json().then(err => { throw new Error(err.error || 'Failed to load document'); });
            }
            return response.json();
        })
        .then(doc => {
            // Fill the view with document data
            document.getElementById('view-title').textContent = doc.title;
            
            // Process tags
            const tagsElement = document.getElementById('view-tags');
            tagsElement.innerHTML = '';
            
            if (doc.tags && doc.tags.trim()) {
                const tagList = doc.tags.split(',').map(tag => tag.trim());
                tagList.forEach(tag => {
                    if (tag) {
                        const badge = document.createElement('span');
                        badge.className = 'badge bg-secondary me-1';
                        badge.textContent = tag;
                        tagsElement.appendChild(badge);
                    }
                });
            }
            
            // Render markdown content
            const contentElement = document.getElementById('view-content');
            contentElement.innerHTML = marked.parse(doc.content);
            
            // Update document title header
            document.getElementById('doc-title-header').innerHTML = `
                <i class="fas fa-file-alt me-2"></i> ${doc.title}
            `;
            
            // Show view, hide others
            document.getElementById('doc-view').classList.remove('d-none');
            document.getElementById('doc-form').style.display = 'none';
            document.getElementById('doc-placeholder').style.display = 'none';
            document.getElementById('doc-actions').style.display = 'block';
            
            // Set up edit button
            document.getElementById('edit-doc-btn').onclick = function() {
                showDocForm(doc);
            };
            
            // Set up delete button
            document.getElementById('delete-doc-btn').onclick = function() {
                // Update the delete confirmation modal
                document.getElementById('delete-doc-title').textContent = doc.title;
                document.getElementById('confirm-delete-btn').setAttribute('data-doc-id', doc.id);
                
                // Show the modal
                const modal = new bootstrap.Modal(document.getElementById('deleteDocModal'));
                modal.show();
            };
        })
        .catch(error => {
            console.error('Error loading document:', error);
            showToast(`Error: ${error.message}`, 'danger');
        });
}

// Show document form (for new or edit)
function showDocForm(doc = null) {
    // Clear form first
    resetDocForm();
    
    // If editing existing doc, populate form
    if (doc) {
        document.getElementById('doc-id').value = doc.id;
        document.getElementById('doc-title').value = doc.title;
        document.getElementById('doc-tags').value = doc.tags || '';
        document.getElementById('doc-content').value = doc.content;
        
        // Update form title
        document.getElementById('doc-title-header').innerHTML = `
            <i class="fas fa-edit me-2"></i> Edit: ${doc.title}
        `;
    } else {
        // New document
        document.getElementById('doc-title-header').innerHTML = `
            <i class="fas fa-plus me-2"></i> New Document
        `;
    }
    
    // Show form, hide others
    document.getElementById('doc-form').style.display = 'block';
    document.getElementById('doc-view').classList.add('d-none');
    document.getElementById('doc-placeholder').style.display = 'none';
    document.getElementById('doc-actions').style.display = 'none';
    
    // Focus on title field
    document.getElementById('doc-title').focus();
}

// Reset document form
function resetDocForm() {
    document.getElementById('doc-id').value = '';
    document.getElementById('doc-title').value = '';
    document.getElementById('doc-tags').value = '';
    document.getElementById('doc-content').value = '';
}

// Show document placeholder
function showDocPlaceholder() {
    document.getElementById('doc-placeholder').style.display = 'block';
    document.getElementById('doc-form').style.display = 'none';
    document.getElementById('doc-view').classList.add('d-none');
    document.getElementById('doc-actions').style.display = 'none';
    document.getElementById('doc-title-header').innerHTML = `<i class="fas fa-file-alt me-2"></i> Document`;
    
    // Remove active class from all documents in list
    document.querySelectorAll('.doc-item').forEach(item => {
        item.classList.remove('active');
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
