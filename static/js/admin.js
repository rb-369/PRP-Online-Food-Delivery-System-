// Admin Dashboard JavaScript

document.addEventListener('DOMContentLoaded', function() {
    loadItemsOnPageStart();
});

// Load items when page starts
function loadItemsOnPageStart() {
    const tableSection = document.getElementById('tableSection');
    const loadingSpinner = document.getElementById('loadingSpinner');
    
    // Show loading
    if (loadingSpinner) loadingSpinner.style.display = 'block';
    if (tableSection) tableSection.style.display = 'none';
    
    // Fetch items
    fetch('/api/admin/menu-items')
        .then(res => res.json())
        .then(data => {
            // Hide loading
            if (loadingSpinner) loadingSpinner.style.display = 'none';
            if (tableSection) tableSection.style.display = 'block';
            
            if (data.success && data.items) {
                displayItems(data.items);
            } else {
                showErrorAlert('Failed to load items');
                document.getElementById('itemsTableBody').innerHTML = '<tr><td colspan="7" class="text-center py-4 text-muted">Error loading items</td></tr>';
            }
        })
        .catch(err => {
            console.error('Error:', err);
            if (loadingSpinner) loadingSpinner.style.display = 'none';
            if (tableSection) tableSection.style.display = 'block';
            showErrorAlert('Failed to load items: ' + err.message);
            document.getElementById('itemsTableBody').innerHTML = '<tr><td colspan="7" class="text-center py-4 text-muted">Error loading items</td></tr>';
        });
}

// Display items in table
function displayItems(items) {
    const tbody = document.getElementById('itemsTableBody');
    
    if (!items || items.length === 0) {
        tbody.innerHTML = '<tr><td colspan="7" class="text-center py-4 text-muted">No items found</td></tr>';
        return;
    }
    
    let html = '';
    items.forEach(item => {
        html += `
            <tr>
                <td class="px-4 py-3"><strong>#${item.id}</strong></td>
                <td class="px-4 py-3"><strong>${item.name}</strong></td>
                <td class="px-4 py-3"><span class="badge bg-secondary">${item.category}</span></td>
                <td class="px-4 py-3"><span class="badge bg-success">₹${item.price}</span></td>
                <td class="px-4 py-3"><small>${item.image_path || 'None'}</small></td>
                <td class="px-4 py-3"><small>${item.description ? item.description.substring(0, 30) + '...' : '-'}</small></td>
                <td class="px-4 py-3">
                    <button class="btn btn-sm btn-info" onclick="openEditForm(${item.id}, '${item.name.replace(/'/g, "\\'")}', '${item.category}', ${item.price}, '${(item.description || '').replace(/'/g, "\\'")}', '${(item.image_path || '').replace(/'/g, "\\'")}')" title="Edit">
                        <i class="fas fa-edit"></i> Edit
                    </button>
                    <button class="btn btn-sm btn-danger" onclick="deleteItemConfirm(${item.id}, '${item.name.replace(/'/g, "\\'")}')" title="Delete">
                        <i class="fas fa-trash"></i> Delete
                    </button>
                </td>
            </tr>
        `;
    });
    
    tbody.innerHTML = html;
}

// Open Add Modal
function openAddModal() {
    document.getElementById('addForm').reset();
    document.getElementById('addAlertBox').innerHTML = '';
    const modal = new bootstrap.Modal(document.getElementById('addModal'));
    modal.show();
}

// Save new item
function saveNewItem() {
    const name = document.getElementById('addFoodName').value.trim();
    const category = document.getElementById('addCategory').value.trim();
    const price = document.getElementById('addPrice').value;
    const description = document.getElementById('addDescription').value.trim();
    const imagePath = document.getElementById('addImagePath').value.trim();
    
    if (!name || !category || !price) {
        showAlert('Please fill all required fields', 'danger', 'addAlertBox');
        return;
    }
    
    const btn = event.target;
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
    .then(res => res.json())
    .then(data => {
        btn.disabled = false;
        btn.innerHTML = '<i class="fas fa-save"></i> Add Item';
        
        if (data.success) {
            showAlert(data.message, 'success', 'addAlertBox');
            setTimeout(() => {
                bootstrap.Modal.getInstance(document.getElementById('addModal')).hide();
                loadItemsOnPageStart();
            }, 1500);
        } else {
            showAlert(data.message || 'Failed', 'danger', 'addAlertBox');
        }
    })
    .catch(err => {
        btn.disabled = false;
        btn.innerHTML = '<i class="fas fa-save"></i> Add Item';
        showAlert('Error: ' + err.message, 'danger', 'addAlertBox');
    });
}

// Open Edit Modal
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

// Update item
function updateItem() {
    const id = document.getElementById('editItemId').value;
    const name = document.getElementById('editFoodName').value.trim();
    const category = document.getElementById('editCategory').value.trim();
    const price = document.getElementById('editPrice').value;
    const description = document.getElementById('editDescription').value.trim();
    const imagePath = document.getElementById('editImagePath').value.trim();
    
    if (!name || !category || !price) {
        showAlert('Please fill all required fields', 'danger', 'editAlertBox');
        return;
    }
    
    const btn = event.target;
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
    .then(res => res.json())
    .then(data => {
        btn.disabled = false;
        btn.innerHTML = '<i class="fas fa-save"></i> Update Item';
        
        if (data.success) {
            showAlert(data.message, 'success', 'editAlertBox');
            setTimeout(() => {
                bootstrap.Modal.getInstance(document.getElementById('editModal')).hide();
                loadItemsOnPageStart();
            }, 1500);
        } else {
            showAlert(data.message || 'Failed', 'danger', 'editAlertBox');
        }
    })
    .catch(err => {
        btn.disabled = false;
        btn.innerHTML = '<i class="fas fa-save"></i> Update Item';
        showAlert('Error: ' + err.message, 'danger', 'editAlertBox');
    });
}

// Delete item with confirmation
function deleteItemConfirm(id, name) {
    if (confirm(`Are you sure you want to delete "${name}"?`)) {
        deleteItem(id);
    }
}

// Delete item
function deleteItem(id) {
    fetch(`/api/admin/menu-items/${id}/delete`, {
        method: 'DELETE',
        headers: { 'Content-Type': 'application/json' }
    })
    .then(res => res.json())
    .then(data => {
        if (data.success) {
            showErrorAlert(data.message);
            loadItemsOnPageStart();
        } else {
            showErrorAlert(data.message || 'Failed to delete');
        }
    })
    .catch(err => {
        showErrorAlert('Error: ' + err.message);
    });
}

// Show alert in specific container
function showAlert(message, type, containerID) {
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

// Show error alert at top
function showErrorAlert(message) {
    const alertHTML = `
        <div class="alert alert-danger alert-dismissible fade show" role="alert" style="position: fixed; top: 80px; right: 20px; z-index: 9999; max-width: 500px;">
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        </div>
    `;
    document.body.insertAdjacentHTML('beforeend', alertHTML);
    
    // Auto dismiss after 5 seconds
    setTimeout(() => {
        const alerts = document.querySelectorAll('.alert-danger[style*="position: fixed"]');
        if (alerts.length > 0) {
            alerts[0].remove();
        }
    }, 5000);
}
