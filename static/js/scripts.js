document.addEventListener('DOMContentLoaded', function() {
    // Initialize scripts page
    setupScriptsUI();
    
    // Set up form submission
    const scriptForm = document.getElementById('script-form-element');
    scriptForm.addEventListener('submit', handleScriptFormSubmit);
    
    // Cancel button handler
    document.getElementById('cancel-script-btn').addEventListener('click', function() {
        resetScriptForm();
        showScriptPlaceholder();
    });
    
    // New script button
    document.getElementById('new-script-btn').addEventListener('click', function() {
        resetScriptForm();
        showScriptForm();
    });
    
    // Attach event listeners to script items in list
    attachScriptItemListeners();
    
    // Delete confirmation setup
    document.getElementById('confirm-delete-btn').addEventListener('click', function() {
        const scriptId = this.getAttribute('data-script-id');
        if (scriptId) {
            deleteScript(scriptId);
        }
    });
});

// Set up the scripts UI
function setupScriptsUI() {
    // Initial state - hide form, show placeholder
    document.getElementById('script-form').style.display = 'none';
    document.getElementById('script-view').classList.add('d-none');
    document.getElementById('script-placeholder').style.display = 'block';
    document.getElementById('script-actions').style.display = 'none';
}

// Attach event listeners to all script items in the list
function attachScriptItemListeners() {
    const scriptItems = document.querySelectorAll('.script-item');
    
    scriptItems.forEach(item => {
        item.addEventListener('click', function() {
            const scriptId = this.getAttribute('data-id');
            loadScriptDetails(scriptId);
            
            // Highlight the selected item
            scriptItems.forEach(i => i.classList.remove('active'));
            this.classList.add('active');
        });
    });
}

// Handle script form submission
function handleScriptFormSubmit(event) {
    event.preventDefault();
    
    const scriptId = document.getElementById('script-id').value;
    const title = document.getElementById('script-title').value;
    const description = document.getElementById('script-description').value;
    const scriptType = document.getElementById('script-type').value;
    const scriptContent = document.getElementById('script-content').value;
    
    // Form validation
    if (!title.trim() || !scriptContent.trim()) {
        showToast('Title and script content are required', 'danger');
        return;
    }
    
    const scriptData = {
        title: title,
        description: description,
        script_type: scriptType,
        script_content: scriptContent
    };
    
    if (scriptId) {
        // Update existing script
        updateScript(scriptId, scriptData);
    } else {
        // Create new script
        createNewScript(scriptData);
    }
}

// Create a new script
function createNewScript(scriptData) {
    fetch('/api/scripts', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(scriptData)
    })
    .then(response => {
        if (!response.ok) {
            return response.json().then(err => { throw new Error(err.error || 'Failed to create script'); });
        }
        return response.json();
    })
    .then(result => {
        showToast('Script created successfully', 'success');
        
        // Reload the page to show the new script in the list
        window.location.reload();
    })
    .catch(error => {
        console.error('Error creating script:', error);
        showToast(`Error: ${error.message}`, 'danger');
    });
}

// Update an existing script
function updateScript(scriptId, scriptData) {
    fetch(`/api/scripts/${scriptId}`, {
        method: 'PUT',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(scriptData)
    })
    .then(response => {
        if (!response.ok) {
            return response.json().then(err => { throw new Error(err.error || 'Failed to update script'); });
        }
        return response.json();
    })
    .then(result => {
        showToast('Script updated successfully', 'success');
        
        // Switch to view mode and reload script
        loadScriptDetails(scriptId);
    })
    .catch(error => {
        console.error('Error updating script:', error);
        showToast(`Error: ${error.message}`, 'danger');
    });
}

// Delete a script
function deleteScript(scriptId) {
    fetch(`/api/scripts/${scriptId}`, {
        method: 'DELETE'
    })
    .then(response => {
        if (!response.ok) {
            return response.json().then(err => { throw new Error(err.error || 'Failed to delete script'); });
        }
        return response.json();
    })
    .then(result => {
        showToast('Script deleted successfully', 'success');
        
        // Close the modal
        const modal = bootstrap.Modal.getInstance(document.getElementById('deleteScriptModal'));
        modal.hide();
        
        // Reload the page to update the list
        window.location.reload();
    })
    .catch(error => {
        console.error('Error deleting script:', error);
        showToast(`Error: ${error.message}`, 'danger');
    });
}

// Load script details by ID
function loadScriptDetails(scriptId) {
    fetch(`/api/scripts/${scriptId}`)
        .then(response => {
            if (!response.ok) {
                return response.json().then(err => { throw new Error(err.error || 'Failed to load script'); });
            }
            return response.json();
        })
        .then(script => {
            // Fill the view with script data
            document.getElementById('view-script-title').textContent = script.title;
            document.getElementById('view-script-type').textContent = script.script_type;
            
            // Format created date
            const createdDate = new Date(script.created_at);
            document.getElementById('view-script-created').textContent = `Created: ${createdDate.toLocaleDateString()}`;
            
            // Set description
            document.getElementById('view-script-description').textContent = script.description || 'No description provided';
            
            // Set script content
            document.getElementById('view-script-content').textContent = script.script_content;
            
            // Update script title header
            document.getElementById('script-title-header').innerHTML = `
                <i class="fas fa-file-code me-2"></i> ${script.title}
            `;
            
            // Show view, hide others
            document.getElementById('script-view').classList.remove('d-none');
            document.getElementById('script-form').style.display = 'none';
            document.getElementById('script-placeholder').style.display = 'none';
            document.getElementById('script-actions').style.display = 'flex';
            
            // Set up copy button
            document.getElementById('copy-script-btn').onclick = function() {
                copyScriptToClipboard(script.script_content);
            };
            
            // Set up edit button
            document.getElementById('edit-script-btn').onclick = function() {
                showScriptForm(script);
            };
            
            // Set up delete button
            document.getElementById('delete-script-btn').onclick = function() {
                // Update the delete confirmation modal
                document.getElementById('delete-script-title').textContent = script.title;
                document.getElementById('confirm-delete-btn').setAttribute('data-script-id', script.id);
                
                // Show the modal
                const modal = new bootstrap.Modal(document.getElementById('deleteScriptModal'));
                modal.show();
            };
        })
        .catch(error => {
            console.error('Error loading script:', error);
            showToast(`Error: ${error.message}`, 'danger');
        });
}

// Copy script content to clipboard
function copyScriptToClipboard(scriptContent) {
    // Create temporary textarea to copy from
    const textarea = document.createElement('textarea');
    textarea.value = scriptContent;
    document.body.appendChild(textarea);
    textarea.select();
    
    try {
        // Execute copy command
        document.execCommand('copy');
        
        // Show success modal
        const modal = new bootstrap.Modal(document.getElementById('copySuccessModal'));
        modal.show();
    } catch (err) {
        console.error('Failed to copy script:', err);
        showToast('Failed to copy script to clipboard', 'danger');
    }
    
    // Remove temporary textarea
    document.body.removeChild(textarea);
}

// Show script form (for new or edit)
function showScriptForm(script = null) {
    // Clear form first
    resetScriptForm();
    
    // If editing existing script, populate form
    if (script) {
        document.getElementById('script-id').value = script.id;
        document.getElementById('script-title').value = script.title;
        document.getElementById('script-description').value = script.description || '';
        document.getElementById('script-type').value = script.script_type;
        document.getElementById('script-content').value = script.script_content;
        
        // Update form title
        document.getElementById('script-title-header').innerHTML = `
            <i class="fas fa-edit me-2"></i> Edit: ${script.title}
        `;
    } else {
        // New script
        document.getElementById('script-title-header').innerHTML = `
            <i class="fas fa-plus me-2"></i> New Script
        `;
    }
    
    // Show form, hide others
    document.getElementById('script-form').style.display = 'block';
    document.getElementById('script-view').classList.add('d-none');
    document.getElementById('script-placeholder').style.display = 'none';
    document.getElementById('script-actions').style.display = 'none';
    
    // Focus on title field
    document.getElementById('script-title').focus();
}

// Reset script form
function resetScriptForm() {
    document.getElementById('script-id').value = '';
    document.getElementById('script-title').value = '';
    document.getElementById('script-description').value = '';
    document.getElementById('script-type').value = 'bash'; // Default to bash
    document.getElementById('script-content').value = '';
}

// Show script placeholder
function showScriptPlaceholder() {
    document.getElementById('script-placeholder').style.display = 'block';
    document.getElementById('script-form').style.display = 'none';
    document.getElementById('script-view').classList.add('d-none');
    document.getElementById('script-actions').style.display = 'none';
    document.getElementById('script-title-header').innerHTML = `<i class="fas fa-file-code me-2"></i> Script`;
    
    // Remove active class from all scripts in list
    document.querySelectorAll('.script-item').forEach(item => {
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
