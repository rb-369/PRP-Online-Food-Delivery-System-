// Order History Page JavaScript

document.addEventListener('DOMContentLoaded', function() {
    loadOrders();
});

// Load orders
function loadOrders() {
    const container = document.getElementById('ordersContainer');
    
    // Show skeleton loaders
    container.innerHTML = Array(3).fill().map(() => `
        <div class="col-12">
            <div class="skeleton-card"></div>
        </div>
    `).join('');
    
    fetch('/api/orders')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                if (data.orders.length === 0) {
                    displayEmptyState();
                } else {
                    displayOrders(data.orders);
                }
            } else {
                displayError('Failed to load orders');
            }
        })
        .catch(error => {
            console.error('Error loading orders:', error);
            displayError('Error loading orders');
        });
}

// Display orders
function displayOrders(orders) {
    const container = document.getElementById('ordersContainer');
    const emptyState = document.getElementById('emptyState');
    emptyState.style.display = 'none';
    
    let html = '';
    orders.forEach(order => {
        const statusClass = getStatusClass(order.status);
        const formattedDate = formatDate(order.order_date);
        
        html += `
            <div class="col-md-6 col-lg-4">
                <div class="card order-card">
                    <div class="order-card-header">
                        <div class="order-id">Order #${order.id}</div>
                        <div class="order-date">
                            <i class="fas fa-calendar"></i> ${formattedDate}
                        </div>
                    </div>
                    <div class="order-card-body">
                        <div class="order-info-row">
                            <span class="order-info-label">Status</span>
                            <span class="order-status ${statusClass}">${order.status}</span>
                        </div>
                        <div class="order-info-row">
                            <span class="order-info-label">Total Amount</span>
                            <span class="order-total">$${parseFloat(order.total_amount).toFixed(2)}</span>
                        </div>
                    </div>
                    <div class="order-card-footer">
                        <button class="btn-view-details" onclick="showOrderDetails(${order.id})">
                            <i class="fas fa-eye"></i> View Details
                        </button>
                    </div>
                </div>
            </div>
        `;
    });
    
    container.innerHTML = html;
}

// Display empty state
function displayEmptyState() {
    const container = document.getElementById('ordersContainer');
    const emptyState = document.getElementById('emptyState');
    
    container.innerHTML = '';
    emptyState.style.display = 'block';
}

// Display error
function displayError(message) {
    const container = document.getElementById('ordersContainer');
    container.innerHTML = `
        <div class="col-12 text-center py-5">
            <i class="fas fa-exclamation-circle" style="font-size: 48px; color: #ccc;"></i>
            <h3 class="mt-3 text-muted">${message}</h3>
            <button class="btn btn-primary mt-3" onclick="loadOrders()">
                <i class="fas fa-redo"></i> Retry
            </button>
        </div>
    `;
}

// Show order details modal
function showOrderDetails(orderId) {
    fetch(`/api/order-details/${orderId}`)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                displayOrderDetailsModal(data.order);
            } else {
                alert('Failed to load order details');
            }
        })
        .catch(error => {
            console.error('Error loading order details:', error);
            alert('Error loading order details');
        });
}

// Display order details in modal
function displayOrderDetailsModal(order) {
    const content = document.getElementById('orderDetailsContent');
    const statusClass = getStatusClass(order.status);
    
    let itemsHtml = '';
    if (order.items && order.items.length > 0) {
        order.items.forEach(item => {
            itemsHtml += `
                <div class="order-item-detail">
                    <div>
                        <div class="item-name">${item.name}</div>
                        <div class="item-qty">Quantity: ${item.quantity}</div>
                    </div>
                    <div class="item-price">
                        ${item.quantity} × $${parseFloat(item.price).toFixed(2)} = $${parseFloat(item.total).toFixed(2)}
                    </div>
                </div>
            `;
        });
    }
    
    content.innerHTML = `
        <div class="details-section">
            <div class="details-section-title">Order Information</div>
            <div class="detail-row">
                <span class="detail-label">Order ID:</span>
                <span class="detail-value">#${order.id}</span>
            </div>
            <div class="detail-row">
                <span class="detail-label">Order Date:</span>
                <span class="detail-value">${formatDate(order.order_date)}</span>
            </div>
            <div class="detail-row">
                <span class="detail-label">Status:</span>
                <span class="order-status ${statusClass}">${order.status}</span>
            </div>
        </div>
        
        <div class="details-section">
            <div class="details-section-title">Order Items</div>
            <div class="order-items-list">
                ${itemsHtml}
            </div>
        </div>
        
        <div class="details-section">
            <div class="details-section-title">Order Summary</div>
            <div class="detail-row">
                <span class="detail-label">Total Amount:</span>
                <span class="detail-value" style="color: #FF6F00; font-size: 1.2rem;">$${parseFloat(order.total_amount).toFixed(2)}</span>
            </div>
        </div>
    `;
    
    const modal = new bootstrap.Modal(document.getElementById('orderDetailsModal'));
    modal.show();
}

// Get status CSS class
function getStatusClass(status) {
    const statusMap = {
        'Pending': 'status-pending',
        'Confirmed': 'status-confirmed',
        'Delivered': 'status-delivered',
        'Cancelled': 'status-cancelled'
    };
    return statusMap[status] || 'status-pending';
}

// Format date
function formatDate(dateString) {
    const options = { 
        year: 'numeric', 
        month: 'short', 
        day: 'numeric', 
        hour: '2-digit', 
        minute: '2-digit'
    };
    return new Date(dateString).toLocaleDateString(undefined, options);
}
