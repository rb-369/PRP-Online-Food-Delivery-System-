// Admin Dashboard JavaScript

document.addEventListener('DOMContentLoaded', function() {
    cleanupStaleOverlays();
    loadItems();
    loadPendingReviews();
});

function cleanupStaleOverlays() {
    // If a stale backdrop remains, it can make the whole page look blank/dim.
    document.querySelectorAll('.modal-backdrop, .offcanvas-backdrop').forEach((el) => el.remove());
    document.body.classList.remove('modal-open');
    document.body.style.overflow = '';
    document.body.style.paddingRight = '';
}

function parseResponseAsJson(response) {
    const contentType = response.headers.get('content-type') || '';
    if (!contentType.includes('application/json')) {
        return response.text().then(text => {
            throw new Error(`Server returned non-JSON response (${response.status}).`);
        });
    }
    return response.json();
}

function loadItems() {
    const loadingDiv = document.getElementById('loadingDiv');
    const tableContainer = document.getElementById('tableContainer');
    const errorDiv = document.getElementById('errorDiv');
    
    // Show loading
    if (loadingDiv) {
        loadingDiv.style.setProperty('display', 'block', 'important');
        loadingDiv.style.visibility = 'visible';
    }
    if (tableContainer) {
        tableContainer.style.setProperty('display', 'none', 'important');
    }
    if (errorDiv) {
        errorDiv.style.setProperty('display', 'none', 'important');
    }
    
    fetch('/api/admin/menu-items')
        .then(parseResponseAsJson)
        .then(data => {
            if (loadingDiv) {
                loadingDiv.style.setProperty('display', 'none', 'important');
            }
            
            if (data.success && data.items) {
                displayItems(data.items);
                if (tableContainer) {
                    tableContainer.style.setProperty('display', 'block', 'important');
                    tableContainer.style.visibility = 'visible';
                    tableContainer.style.opacity = '1';
                }
            } else {
                showError('Failed to load items: ' + (data.message || 'Unknown error'));
            }
        })
        .catch(error => {
            if (loadingDiv) loadingDiv.style.setProperty('display', 'none', 'important');
            showError('Error loading items: ' + error.message);
        });
}

function displayItems(items) {
    const tbody = document.getElementById('itemsTableBody');
    if (!tbody) return;
    
    let html = '';
    items.forEach(item => {
        html += `
            <tr>
                <td>${item.id}</td>
                <td>${item.name}</td>
                <td><span class="badge bg-secondary">${item.category}</span></td>
                <td>₹${item.price}</td>
                <td>
                    <button class="btn btn-sm btn-primary" onclick="openEditForm(${item.id}, '${item.name.replace(/'/g, "\\'")}', '${item.category}', ${item.price}, '${(item.description || '').replace(/'/g, "\\'")}', '${(item.image_path || '').replace(/'/g, "\\'")}')">Edit</button>
                    <button class="btn btn-sm btn-danger" onclick="deleteFood(${item.id}, '${item.name.replace(/'/g, "\\'")}')" >Delete</button>
                </td>
            </tr>
        `;
    });
    
    tbody.innerHTML = html;
}

function loadPendingReviews() {
    const loadingDiv = document.getElementById('reviewLoadingDiv');
    const tableContainer = document.getElementById('reviewTableContainer');
    const emptyDiv = document.getElementById('reviewEmptyDiv');

    if (loadingDiv) loadingDiv.style.display = 'block';
    if (tableContainer) tableContainer.style.display = 'none';
    if (emptyDiv) emptyDiv.style.display = 'none';

    fetch('/api/admin/reviews/pending')
        .then(parseResponseAsJson)
        .then((data) => {
            if (loadingDiv) loadingDiv.style.display = 'none';

            if (!data.success || !Array.isArray(data.reviews)) {
                if (emptyDiv) {
                    emptyDiv.className = 'alert alert-danger';
                    emptyDiv.textContent = data.message || 'Failed to load pending reviews.';
                    emptyDiv.style.display = 'block';
                }
                return;
            }

            if (data.reviews.length === 0) {
                if (emptyDiv) {
                    emptyDiv.className = 'alert alert-success';
                    emptyDiv.textContent = 'No pending reviews to moderate.';
                    emptyDiv.style.display = 'block';
                }
                return;
            }

            renderReviewRows(data.reviews);
            if (tableContainer) tableContainer.style.display = 'block';
        })
        .catch((error) => {
            if (loadingDiv) loadingDiv.style.display = 'none';
            if (emptyDiv) {
                emptyDiv.className = 'alert alert-danger';
                emptyDiv.textContent = `Error loading pending reviews: ${error.message}`;
                emptyDiv.style.display = 'block';
            }
        });
}

function renderReviewRows(reviews) {
    const tbody = document.getElementById('reviewsTableBody');
    if (!tbody) return;

    tbody.innerHTML = reviews.map((review) => `
        <tr>
            <td><span class="badge ${review.review_type === 'item' ? 'bg-primary' : 'bg-secondary'}">${review.review_type}</span></td>
            <td>${escapeHtml(review.username || '-')}</td>
            <td>#${review.order_id}</td>
            <td>${escapeHtml(review.item_name || '-')}</td>
            <td>${'★'.repeat(Number(review.rating || 0))}</td>
            <td>${escapeHtml(review.comment || '-')}</td>
            <td>
                <button class="btn btn-sm btn-success" onclick="moderateReview('${review.review_type}', ${review.id}, 'approved')">Approve</button>
                <button class="btn btn-sm btn-danger" onclick="moderateReview('${review.review_type}', ${review.id}, 'rejected')">Reject</button>
            </td>
        </tr>
    `).join('');
}

function moderateReview(reviewType, reviewId, status) {
    fetch(`/api/admin/reviews/${reviewType}/${reviewId}/moderate`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ status })
    })
    .then(parseResponseAsJson)
    .then((data) => {
        if (!data.success) {
            showError(data.message || 'Unable to moderate review.');
            return;
        }
        showSuccess(data.message || 'Review updated');
        loadPendingReviews();
    })
    .catch((error) => {
        showError(`Error moderating review: ${error.message}`);
    });
}

function escapeHtml(value) {
    return String(value)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#39;');
}

function showError(message) {
    const errorDiv = document.getElementById('errorDiv');
    const errorText = document.getElementById('errorText');
    if (errorDiv && errorText) {
        errorText.textContent = message;
        errorDiv.style.display = 'block';
    }
}

function openAddModal() {
    document.getElementById('addForm').reset();
    document.getElementById('addAlertBox').innerHTML = '';
    const modal = new bootstrap.Modal(document.getElementById('addModal'));
    modal.show();
}

function saveNewItem(event) {
    const name = document.getElementById('addFoodName').value.trim();
    const category = document.getElementById('addCategory').value.trim();
    const price = document.getElementById('addPrice').value;
    const description = document.getElementById('addDescription').value.trim();
    const imagePath = document.getElementById('addImagePath').value.trim();
    
    if (!name || !category || !price) {
        showAlertInModal('Please fill all required fields', 'danger', 'addAlertBox');
        return;
    }
    
    const btn = event?.target || document.querySelector('#addModal .btn-success');
    btn.disabled = true;
    btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Adding...';
    
    fetch('/api/admin/menu-items/add', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            name: name,
            category: category,
            price: parseFloat(price),
            description: description,
            image_path: imagePath
        })
    })
    .then(parseResponseAsJson)
    .then(data => {
        btn.disabled = false;
        btn.innerHTML = '<i class="fas fa-save"></i> Add Item';
        
        if (data.success) {
            showAlertInModal(data.message, 'success', 'addAlertBox');
            setTimeout(() => {
                bootstrap.Modal.getInstance(document.getElementById('addModal')).hide();
                loadItems();
            }, 1500);
        } else {
            showAlertInModal(data.message || 'Failed', 'danger', 'addAlertBox');
        }
    })
    .catch(err => {
        btn.disabled = false;
        btn.innerHTML = '<i class="fas fa-save"></i> Add Item';
        showAlertInModal('Error: ' + err.message, 'danger', 'addAlertBox');
    });
}

function openEditForm(id, name, category, price, description, imagePath) {
    document.getElementById('editItemId').value = id;
    document.getElementById('editFoodName').value = name;
    document.getElementById('editCategory').value = category;
    document.getElementById('editPrice').value = price;
    document.getElementById('editDescription').value = description;
    document.getElementById('editImagePath').value = imagePath;
    document.getElementById('editAlertBox').innerHTML = '';
    
    const modal = new bootstrap.Modal(document.getElementById('editModal'));
    modal.show();
}

function updateItem(event) {
    const id = document.getElementById('editItemId').value;
    const name = document.getElementById('editFoodName').value.trim();
    const category = document.getElementById('editCategory').value.trim();
    const price = document.getElementById('editPrice').value;
    const description = document.getElementById('editDescription').value.trim();
    const imagePath = document.getElementById('editImagePath').value.trim();
    
    if (!name || !category || !price) {
        showAlertInModal('Please fill all required fields', 'danger', 'editAlertBox');
        return;
    }
    
    const btn = event?.target || document.querySelector('#editModal .btn-primary');
    btn.disabled = true;
    btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Updating...';
    
    fetch(`/api/admin/menu-items/${id}/edit`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            name: name,
            category: category,
            price: parseFloat(price),
            description: description,
            image_path: imagePath
        })
    })
    .then(parseResponseAsJson)
    .then(data => {
        btn.disabled = false;
        btn.innerHTML = '<i class="fas fa-save"></i> Update Item';
        
        if (data.success) {
            showAlertInModal(data.message, 'success', 'editAlertBox');
            setTimeout(() => {
                bootstrap.Modal.getInstance(document.getElementById('editModal')).hide();
                loadItems();
            }, 1500);
        } else {
            showAlertInModal(data.message || 'Failed', 'danger', 'editAlertBox');
        }
    })
    .catch(err => {
        btn.disabled = false;
        btn.innerHTML = '<i class="fas fa-save"></i> Update Item';
        showAlertInModal('Error: ' + err.message, 'danger', 'editAlertBox');
    });
}

function deleteFood(id, name) {
    if (confirm(`Are you sure you want to delete "${name}"?`)) {
        fetch(`/api/admin/menu-items/${id}/delete`, {
            method: 'DELETE',
            headers: { 'Content-Type': 'application/json' }
        })
        .then(res => res.json())
        .then(data => {
            if (data.success) {
                loadItems();
                showSuccess(data.message);
            } else {
                showError(data.message || 'Failed to delete');
            }
        })
        .catch(err => {
            showError('Error: ' + err.message);
        });
    }
}

function showAlertInModal(message, type, containerID) {
    const container = document.getElementById(containerID);
    if (!container) return;
    
    const alertHTML = `
        <div class="alert alert-${type} alert-dismissible fade show" role="alert">
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        </div>
    `;
    container.innerHTML = alertHTML;
}

function showSuccess(message) {
    const alerts = document.createElement('div');
    alerts.className = 'alert alert-success alert-dismissible fade show';
    alerts.style.position = 'fixed';
    alerts.style.top = '80px';
    alerts.style.right = '20px';
    alerts.style.zIndex = '9999';
    alerts.style.maxWidth = '400px';
    alerts.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    document.body.appendChild(alerts);
    
    setTimeout(() => alerts.remove(), 5000);
}
