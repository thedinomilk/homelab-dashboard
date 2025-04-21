document.addEventListener('DOMContentLoaded', function() {
    // Check if analysis is already loaded
    if (document.getElementById('analysisSection').style.display === 'block') {
        loadRecommendations();
    }
    
    // Add event listeners
    const implementationButtons = document.querySelectorAll('.implement-recommendation');
    implementationButtons.forEach(btn => {
        btn.addEventListener('click', handleImplementation);
    });
});

function loadRecommendations() {
    fetch('/api/recommendations')
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                console.error('Error loading recommendations:', data.error);
                return;
            }
            
            updateRecommendationsUI(data.recommendations);
        })
        .catch(error => {
            console.error('Error:', error);
        });
}

function updateRecommendationsUI(recommendations) {
    // Update each category
    const categories = ['infrastructure', 'virtualization', 'storage', 'networking', 'services'];
    
    categories.forEach(category => {
        const categoryRecs = recommendations.filter(rec => rec.category === category);
        const listElement = document.getElementById(`${category}Recommendations`);
        
        if (listElement) {
            listElement.innerHTML = '';
            
            if (categoryRecs.length === 0) {
                listElement.innerHTML = '<li class="list-group-item bg-dark">No recommendations available.</li>';
                return;
            }
            
            // Sort by priority
            categoryRecs.sort((a, b) => a.priority - b.priority);
            
            categoryRecs.forEach(rec => {
                const li = document.createElement('li');
                li.className = 'list-group-item bg-dark';
                
                // Add priority indicator
                const priorityBadge = document.createElement('span');
                priorityBadge.className = `badge rounded-pill me-2 ${getPriorityClass(rec.priority)}`;
                priorityBadge.textContent = getPriorityLabel(rec.priority);
                
                // Main recommendation text
                const recText = document.createElement('span');
                recText.textContent = rec.recommendation;
                
                // Implementation button 
                const actionButton = document.createElement('button');
                actionButton.className = 'btn btn-sm btn-outline-primary float-end implement-recommendation';
                actionButton.setAttribute('data-rec-id', rec.id);
                actionButton.textContent = rec.implemented ? 'Implemented' : 'Implement';
                if (rec.implemented) {
                    actionButton.classList.add('disabled');
                }
                
                // Add all elements to the list item
                li.appendChild(priorityBadge);
                li.appendChild(recText);
                li.appendChild(actionButton);
                listElement.appendChild(li);
            });
        }
    });
    
    // Add event listeners to the new buttons
    const implementationButtons = document.querySelectorAll('.implement-recommendation');
    implementationButtons.forEach(btn => {
        btn.addEventListener('click', handleImplementation);
    });
}

function handleImplementation(event) {
    const recId = event.target.getAttribute('data-rec-id');
    
    // Show implementation modal
    const modal = new bootstrap.Modal(document.getElementById('implementationModal'));
    
    // Fetch recommendation details
    fetch(`/api/recommendations/${recId}`)
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                console.error('Error:', data.error);
                return;
            }
            
            // Populate modal
            document.getElementById('modalTitle').textContent = `Implement: ${data.category.charAt(0).toUpperCase() + data.category.slice(1)}`;
            document.getElementById('recommendationText').textContent = data.recommendation;
            document.getElementById('implementationForm').setAttribute('data-rec-id', recId);
            
            // Show the modal
            modal.show();
        })
        .catch(error => {
            console.error('Error:', error);
        });
}

function saveImplementationPlan() {
    const recId = document.getElementById('implementationForm').getAttribute('data-rec-id');
    const title = document.getElementById('planTitle').value;
    const description = document.getElementById('planDescription').value;
    const steps = document.getElementById('implementationSteps').value;
    
    if (!title) {
        alert('Please enter a title for your implementation plan');
        return;
    }
    
    const planData = {
        recommendation_id: recId,
        title: title,
        description: description,
        steps: steps,
        status: 'Planned'
    };
    
    fetch('/api/implementation-plans', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(planData)
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            alert('Error saving plan: ' + data.error);
            return;
        }
        
        // Hide modal
        const modal = bootstrap.Modal.getInstance(document.getElementById('implementationModal'));
        modal.hide();
        
        // Mark recommendation as implemented
        fetch(`/api/recommendations/${recId}/implement`, {
            method: 'POST'
        })
        .then(() => {
            // Reload recommendations
            loadRecommendations();
            
            // Show success message
            showToast('Implementation plan created successfully!', 'success');
        });
    })
    .catch(error => {
        console.error('Error:', error);
        alert('Failed to save implementation plan. Please try again.');
    });
}

function showToast(message, type = 'info') {
    const toast = document.createElement('div');
    toast.className = `toast align-items-center text-white bg-${type} border-0`;
    toast.setAttribute('role', 'alert');
    toast.setAttribute('aria-live', 'assertive');
    toast.setAttribute('aria-atomic', 'true');
    
    const content = document.createElement('div');
    content.className = 'd-flex';
    
    const body = document.createElement('div');
    body.className = 'toast-body';
    body.textContent = message;
    
    const closeButton = document.createElement('button');
    closeButton.type = 'button';
    closeButton.className = 'btn-close btn-close-white me-2 m-auto';
    closeButton.setAttribute('data-bs-dismiss', 'toast');
    closeButton.setAttribute('aria-label', 'Close');
    
    content.appendChild(body);
    content.appendChild(closeButton);
    toast.appendChild(content);
    
    const toastContainer = document.getElementById('toastContainer');
    if (!toastContainer) {
        const container = document.createElement('div');
        container.className = 'toast-container position-fixed bottom-0 end-0 p-3';
        container.id = 'toastContainer';
        document.body.appendChild(container);
    }
    
    document.getElementById('toastContainer').appendChild(toast);
    
    const toastInstance = new bootstrap.Toast(toast);
    toastInstance.show();
    
    // Remove toast after it's hidden
    toast.addEventListener('hidden.bs.toast', function() {
        toast.remove();
    });
}

function getPriorityClass(priority) {
    switch(priority) {
        case 1: return 'bg-danger';
        case 2: return 'bg-warning text-dark';
        case 3: return 'bg-info text-dark';
        case 4: return 'bg-primary';
        case 5: return 'bg-secondary';
        default: return 'bg-info text-dark';
    }
}

function getPriorityLabel(priority) {
    switch(priority) {
        case 1: return 'Critical';
        case 2: return 'High';
        case 3: return 'Medium';
        case 4: return 'Low';
        case 5: return 'Optional';
        default: return 'Medium';
    }
}