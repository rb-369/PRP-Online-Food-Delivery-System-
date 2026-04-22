// Menu Page JavaScript

let allMenuItems = [];
let itemQuantities = {}; // Track quantities for each item

document.addEventListener('DOMContentLoaded', function() {
    loadMenuItems();
    
    // Search input event listener
    const searchInput = document.getElementById('searchInput');
    if (searchInput) {
        searchInput.addEventListener('input', handleSearch);
    }
});

// Load all menu items
function loadMenuItems() {
    const container = document.getElementById('menuItemsContainer');
    
    // Show skeleton loaders
    container.innerHTML = Array(8).fill().map(() => `
        <div class="col-lg-3 col-md-4 col-sm-6">
            <div class="food-card-skeleton" style="height: 420px; border-radius: 12px;"></div>
        </div>
    `).join('');
    
    fetch('/api/menu')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                allMenuItems = data.items;
                displayMenuItems(allMenuItems);
            } else {
                showError('Failed to load menu items');
            }
        })
        .catch(error => {
            console.error('Error loading menu:', error);
            showError('Error loading menu items');
        });
}

// Display menu items in grid
function displayMenuItems(items) {
    const container = document.getElementById('menuItemsContainer');
    const emptyState = document.getElementById('emptyState');
    
    if (items.length === 0) {
        container.innerHTML = '';
        emptyState.style.display = 'block';
        return;
    }
    
    emptyState.style.display = 'none';
    
    let html = '';
    items.forEach(item => {
        // Handle image paths - check if it's an emoji or file path
        let itemImage;
        if (item.image_path && item.image_path.endsWith('.png')) {
            // It's an image file from images folder
            itemImage = `<img src="/static/images/${item.image_path}" alt="${item.name}" style="object-fit: cover; width: 100%; height: 100%;" onerror="this.parentElement.innerHTML='<div style=\\'font-size: 3rem; display: flex; align-items: center; justify-content: center; height: 100%;\\'>🍔</div>'">`;
        } else if (item.image_path && item.image_path.endsWith('.jpg')) {
            // JPG image file
            itemImage = `<img src="/static/images/${item.image_path}" alt="${item.name}" style="object-fit: cover; width: 100%; height: 100%;" onerror="this.parentElement.innerHTML='<div style=\\'font-size: 3rem; display: flex; align-items: center; justify-content: center; height: 100%;\\'>🍔</div>'">`;
        } else {
            // Default emoji
            itemImage = `<div style="font-size: 3rem; display: flex; align-items: center; justify-content: center; height: 100%;">🍔</div>`;
        }
        
        const qty = itemQuantities[item.id] || 1;
        
        html += `
            <div class="col-lg-3 col-md-4 col-sm-6">
                <div class="card food-card">
                    <div class="food-card-img">
                        ${itemImage}
                    </div>
                    <div class="food-card-body">
                        <h5 class="food-card-title">${item.name}</h5>
                        <p class="food-card-description">${item.description || 'Delicious food item'}</p>
                        <div class="quantity-section">
                            <div class="quantity-selector">
                                <button class="qty-btn" onclick="decreaseQty(${item.id})">−</button>
                                <input type="number" class="qty-input" id="qty-${item.id}" value="${qty}" min="1" onchange="updateQty(${item.id}, this.value)">
                                <button class="qty-btn" onclick="increaseQty(${item.id})">+</button>
                            </div>
                            <div style="display: flex; gap: 8px; align-items: center; flex: 1;">
                                <span class="food-card-price">₹${parseFloat(item.price).toFixed(0)}</span>
                                <button class="btn-add-to-cart" onclick="addItemToCart(${item.id}, '${item.name}', ${item.price})" title="Add to cart">
                                    <i class="fas fa-shopping-cart"></i> Add
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;
    });
    
    container.innerHTML = html;
}

// Quantity functions
function increaseQty(itemId) {
    const input = document.getElementById(`qty-${itemId}`);
    input.value = parseInt(input.value) + 1;
    itemQuantities[itemId] = parseInt(input.value);
}

function decreaseQty(itemId) {
    const input = document.getElementById(`qty-${itemId}`);
    if (parseInt(input.value) > 1) {
        input.value = parseInt(input.value) - 1;
        itemQuantities[itemId] = parseInt(input.value);
    }
}

function updateQty(itemId, value) {
    const qty = parseInt(value) || 1;
    if (qty < 1) {
        document.getElementById(`qty-${itemId}`).value = 1;
        itemQuantities[itemId] = 1;
    } else {
        itemQuantities[itemId] = qty;
    }
}

// Add item to cart
function addItemToCart(itemId, itemName, itemPrice) {
    const btn = event?.target?.closest('.btn-add-to-cart');
    if (!btn) return;
    
    const quantity = itemQuantities[itemId] || 1;
    const originalHTML = btn.innerHTML;
    
    btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';
    btn.disabled = true;
    
    fetch('/api/cart/add', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            item_id: itemId,
            quantity: quantity
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showNotification(`${itemName} × ${quantity} added to cart!`, 'success');
            updateCartCount();
            loadCartItems(); // Refresh cart display
            
            // Update button to show "+" icon
            btn.innerHTML = '<i class="fas fa-plus"></i> <i class="fas fa-shopping-cart"></i>';
            btn.style.backgroundColor = '#00C853';
            btn.style.color = 'white';
            
            setTimeout(() => {
                btn.innerHTML = originalHTML;
                btn.disabled = false;
                btn.style.backgroundColor = '';
                btn.style.color = '';
            }, 2000);
        } else {
            showNotification(data.message || 'Failed to add item', 'error');
            btn.innerHTML = originalHTML;
            btn.disabled = false;
        }
    })
    .catch(error => {
        console.error('Error adding to cart:', error);
        showNotification('Error adding to cart', 'error');
        btn.innerHTML = originalHTML;
        btn.disabled = false;
    });
}

// Handle search
function handleSearch(e) {
    const searchQuery = e.target.value.trim();
    
    if (!searchQuery) {
        displayMenuItems(allMenuItems);
        return;
    }
    
    // Search locally for faster response
    const filtered = allMenuItems.filter(item =>
        item.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        item.description.toLowerCase().includes(searchQuery.toLowerCase())
    );
    
    displayMenuItems(filtered);
}

// Show error message
function showError(message) {
    const container = document.getElementById('menuItemsContainer');
    container.innerHTML = `
        <div class="col-12 text-center py-5">
            <i class="fas fa-exclamation-circle" style="font-size: 48px; color: #ccc;"></i>
            <h3 class="mt-3 text-muted">${message}</h3>
            <button class="btn btn-primary mt-3" onclick="loadMenuItems()">
                <i class="fas fa-redo"></i> Retry
            </button>
        </div>
    `;
}
