// Main JavaScript - Cart Management and Common Functions

// Initialize cart count on page load
document.addEventListener('DOMContentLoaded', function() {
    updateCartCount();
});

// Show cart offcanvas
function showCart() {
    const cartOffcanvas = new bootstrap.Offcanvas(document.getElementById('cartOffcanvas'));
    cartOffcanvas.show();
    loadCartItems();
}

// Load cart items
function loadCartItems() {
    fetch('/api/cart')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                const container = document.getElementById('cartItems');
                
                if (data.items.length === 0) {
                    container.innerHTML = '<div class="text-center py-4 text-muted"><i class="fas fa-shopping-cart" style="font-size: 32px;"></i><p class="mt-3">Your cart is empty</p></div>';
                    document.getElementById('cartTotal').textContent = '$0.00';
                    return;
                }
                
                let html = '';
                data.items.forEach(item => {
                    html += `
                        <div class="cart-item">
                            <div class="cart-item-details">
                                <h6>${item.name}</h6>
                                <small>₹${parseFloat(item.price).toFixed(0)} × ${item.quantity}</small>
                            </div>
                            <div class="cart-item-actions">
                                <div class="input-group input-group-sm">
                                    <button class="btn btn-outline-secondary btn-sm" onclick="updateQuantity(${item.item_id}, ${item.quantity - 1})">-</button>
                                    <input type="text" class="form-control form-control-sm text-center" value="${item.quantity}" disabled style="flex: 0 0 40px;">
                                    <button class="btn btn-outline-secondary btn-sm" onclick="updateQuantity(${item.item_id}, ${item.quantity + 1})">+</button>
                                </div>
                                <button class="btn btn-outline-danger btn-sm" onclick="removeFromCart(${item.item_id})" style="padding: 0.25rem 0.5rem;"><i class="fas fa-trash" style="font-size: 0.8rem;"></i></button>
                            </div>
                        </div>
                    `;
                });
                
                container.innerHTML = html;
                document.getElementById('cartTotal').textContent = '₹' + parseFloat(data.total).toFixed(0);
            }
        })
        .catch(error => console.error('Error loading cart:', error));
}

// Update item quantity
function updateQuantity(itemId, newQuantity) {
    fetch(`/api/cart/update/${itemId}`, {
        method: 'PUT',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ quantity: newQuantity })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            loadCartItems();
            updateCartCount();
        }
    })
    .catch(error => console.error('Error updating cart:', error));
}

// Remove from cart
function removeFromCart(itemId) {
    fetch(`/api/cart/remove/${itemId}`, {
        method: 'DELETE'
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            loadCartItems();
            updateCartCount();
            showNotification('Item removed from cart', 'info');
        }
    })
    .catch(error => console.error('Error removing from cart:', error));
}

// Clear entire cart
function clearCart() {
    if (confirm('Are you sure you want to clear your cart?')) {
        fetch('/api/cart/clear', {
            method: 'POST'
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                loadCartItems();
                updateCartCount();
                showNotification('Cart cleared', 'info');
            }
        })
        .catch(error => console.error('Error clearing cart:', error));
    }
}

// Go to checkout
function goToCheckout() {
    fetch('/api/cart')
        .then(response => response.json())
        .then(data => {
            if (data.items.length === 0) {
                showNotification('Your cart is empty', 'warning');
            } else {
                window.location.href = '/checkout';
            }
        })
        .catch(error => console.error('Error:', error));
}

// Update cart count badge
function updateCartCount() {
    fetch('/api/cart')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                const badge = document.getElementById('cartCount');
                const count = data.count;
                badge.textContent = count;
                badge.style.display = count > 0 ? 'inline-block' : 'none';
            }
        })
        .catch(error => console.error('Error updating cart count:', error));
}

// Show notification/toast
function showNotification(message, type = 'info') {
    const alertTypes = {
        'success': 'alert-success',
        'error': 'alert-danger',
        'warning': 'alert-warning',
        'info': 'alert-info'
    };
    
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert ${alertTypes[type] || alertTypes['info']} alert-dismissible fade show`;
    alertDiv.style.position = 'fixed';
    alertDiv.style.top = '100px';
    alertDiv.style.right = '20px';
    alertDiv.style.zIndex = '9999';
    alertDiv.style.minWidth = '300px';
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    document.body.appendChild(alertDiv);
    
    setTimeout(() => {
        alertDiv.remove();
    }, 5000);
}

// Format currency
function formatCurrency(amount) {
    return '$' + parseFloat(amount).toFixed(2);
}

// Format date
function formatDate(dateString) {
    const options = { year: 'numeric', month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' };
    return new Date(dateString).toLocaleDateString(undefined, options);
}
