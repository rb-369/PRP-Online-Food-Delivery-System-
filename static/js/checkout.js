// Checkout Page JavaScript

const TAX_RATE = 0.10; // 10% tax
const DELIVERY_FEE = 100; // ₹100 delivery fee
let savedAddresses = [];

document.addEventListener('DOMContentLoaded', function() {
    loadCheckoutData();
    initializeLocationFeatures();
    initializeAddressBook();
    
    const checkoutForm = document.getElementById('checkoutForm');
    if (checkoutForm) {
        checkoutForm.addEventListener('submit', handleCheckout);
    }
});

function initializeAddressBook() {
    const addressSelect = document.getElementById('savedAddressSelect');
    const deleteBtn = document.getElementById('deleteAddressBtn');
    const saveAddressCheck = document.getElementById('saveAddressCheck');
    const saveAddressLabel = document.getElementById('saveAddressLabel');

    if (addressSelect) {
        addressSelect.addEventListener('change', onSavedAddressChange);
    }

    if (deleteBtn) {
        deleteBtn.addEventListener('click', deleteSelectedAddress);
    }

    if (saveAddressCheck && saveAddressLabel) {
        saveAddressLabel.disabled = !saveAddressCheck.checked;
        saveAddressCheck.addEventListener('change', () => {
            saveAddressLabel.disabled = !saveAddressCheck.checked;
        });
    }

    loadSavedAddresses();
}

function loadSavedAddresses() {
    fetch('/api/addresses')
        .then((response) => response.json())
        .then((data) => {
            if (!data.success) return;

            savedAddresses = data.addresses || [];
            const select = document.getElementById('savedAddressSelect');
            if (!select) return;

            select.innerHTML = '<option value="">Select saved address</option>';
            savedAddresses.forEach((address) => {
                const option = document.createElement('option');
                option.value = address.id;
                const segments = [address.flat_no, address.building_name, address.address].filter(Boolean);
                option.textContent = `${address.label}: ${segments.join(', ')}`;
                select.appendChild(option);
            });
        })
        .catch((error) => {
            console.error('Address load error:', error);
        });
}

function onSavedAddressChange(e) {
    const addressId = Number(e.target.value);
    const selected = savedAddresses.find((addr) => addr.id === addressId);
    if (!selected) return;

    document.getElementById('flatNo').value = selected.flat_no || '';
    document.getElementById('buildingName').value = selected.building_name || '';
    document.getElementById('deliveryAddress').value = selected.address || '';
}

function deleteSelectedAddress() {
    const select = document.getElementById('savedAddressSelect');
    const addressId = Number(select?.value || 0);
    if (!addressId) {
        showAlert('Select an address to delete', 'warning');
        return;
    }

    if (!confirm('Delete selected saved address?')) {
        return;
    }

    fetch(`/api/addresses/${addressId}`, { method: 'DELETE' })
        .then((response) => response.json())
        .then((data) => {
            if (!data.success) {
                showAlert(data.message || 'Unable to delete address', 'danger');
                return;
            }
            showAlert('Address deleted', 'success');
            loadSavedAddresses();
            select.value = '';
        })
        .catch((error) => {
            console.error('Address delete error:', error);
            showAlert('Error deleting address', 'danger');
        });
}

function initializeLocationFeatures() {
    const locationBtn = document.getElementById('useCurrentLocationBtn');
    if (locationBtn) {
        locationBtn.addEventListener('click', useCurrentLocation);
    }
}

function setLocationStatus(message, type = 'muted') {
    const status = document.getElementById('locationStatus');
    if (!status) return;

    status.textContent = message;
    status.classList.remove('text-muted', 'text-success', 'text-danger');
    if (type === 'success') {
        status.classList.add('text-success');
    } else if (type === 'danger') {
        status.classList.add('text-danger');
    } else {
        status.classList.add('text-muted');
    }
}

async function useCurrentLocation() {
    const locationBtn = document.getElementById('useCurrentLocationBtn');
    const addressInput = document.getElementById('deliveryAddress');

    if (!locationBtn || !addressInput) return;

    if (!navigator.geolocation) {
        setLocationStatus('Geolocation is not supported in this browser.', 'danger');
        return;
    }

    const originalBtn = locationBtn.innerHTML;
    locationBtn.disabled = true;
    locationBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Detecting...';
    setLocationStatus('Requesting location permission...');

    navigator.geolocation.getCurrentPosition(
        async (position) => {
            const { latitude, longitude } = position.coords;
            let finalAddress = `Lat: ${latitude.toFixed(6)}, Lng: ${longitude.toFixed(6)}`;

            try {
                const reverseGeocodeUrl = `https://nominatim.openstreetmap.org/reverse?format=jsonv2&lat=${latitude}&lon=${longitude}`;
                const response = await fetch(reverseGeocodeUrl, {
                    headers: { 'Accept': 'application/json' }
                });
                if (response.ok) {
                    const data = await response.json();
                    if (data && data.display_name) {
                        finalAddress = data.display_name;
                    }
                }
            } catch (error) {
                // Keep coordinate fallback if reverse geocoding fails.
            }

            addressInput.value = finalAddress;
            setLocationStatus('Current location added to delivery address.', 'success');
            locationBtn.disabled = false;
            locationBtn.innerHTML = originalBtn;
        },
        (error) => {
            let message = 'Unable to fetch current location.';
            if (error.code === error.PERMISSION_DENIED) {
                message = 'Location permission denied. Please allow location access and try again.';
            } else if (error.code === error.POSITION_UNAVAILABLE) {
                message = 'Location information is unavailable right now.';
            } else if (error.code === error.TIMEOUT) {
                message = 'Location request timed out. Please retry.';
            }

            setLocationStatus(message, 'danger');
            locationBtn.disabled = false;
            locationBtn.innerHTML = originalBtn;
        },
        {
            enableHighAccuracy: true,
            timeout: 15000,
            maximumAge: 0,
        }
    );
}

// Load checkout data
function loadCheckoutData() {
    fetch('/api/cart')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                if (data.items.length === 0) {
                    window.location.href = '/menu';
                    return;
                }
                displayOrderSummary(data.items, data.total);
            }
        })
        .catch(error => {
            console.error('Error loading checkout data:', error);
            showAlert('Error loading checkout data', 'danger');
        });
}

// Display order summary
function displayOrderSummary(items, subtotal) {
    const itemsList = document.getElementById('orderItemsList');
    let html = '';
    
    items.forEach(item => {
        html += `
            <div class="order-item">
                <div class="order-item-info">
                    <h6>${item.name}</h6>
                    <small>${item.quantity} × ₹${parseFloat(item.price).toFixed(0)}</small>
                </div>
                <span class="order-item-price">₹${parseFloat(item.total).toFixed(0)}</span>
            </div>
        `;
    });
    
    itemsList.innerHTML = html;
    
    // Calculate totals
    const tax = subtotal * TAX_RATE;
    const total = subtotal + tax + DELIVERY_FEE;
    
    document.getElementById('subtotal').textContent = '₹' + parseFloat(subtotal).toFixed(0);
    document.getElementById('tax').textContent = '₹' + parseFloat(tax).toFixed(0);
    document.getElementById('deliveryFee').textContent = '₹' + DELIVERY_FEE.toFixed(0);
    document.getElementById('orderTotal').textContent = '₹' + parseFloat(total).toFixed(0);
}

// Handle checkout form submission
function handleCheckout(e) {
    e.preventDefault();
    
    const address = document.getElementById('deliveryAddress').value.trim();
    const buildingName = document.getElementById('buildingName').value.trim();
    const flatNo = document.getElementById('flatNo').value.trim();
    const phone = document.getElementById('phoneNumber').value.trim();
    const paymentMethod = document.getElementById('paymentMethod').value;
    const selectedAddressId = document.getElementById('savedAddressSelect').value;
    const saveAddress = document.getElementById('saveAddressCheck').checked;
    const saveAddressLabel = document.getElementById('saveAddressLabel').value;
    const alertDiv = document.getElementById('orderAlert');
    
    // Validation
    if (!address || !phone || !paymentMethod) {
        showAlert('Please fill in all fields', 'danger', alertDiv);
        return;
    }
    
    // Phone validation (basic)
    if (!/^[0-9\-\+\s\(\)]+$/.test(phone) || phone.replace(/\D/g, '').length < 10) {
        showAlert('Please enter a valid phone number', 'danger', alertDiv);
        return;
    }
    
    // Show loading state
    const submitBtn = e.target.querySelector('button[type="submit"]');
    const originalHTML = submitBtn.innerHTML;
    submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Processing...';
    submitBtn.disabled = true;
    
    // Place order
    fetch('/api/place-order', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            address: address,
            building_name: buildingName,
            flat_no: flatNo,
            phone: phone,
            payment_method: paymentMethod,
            address_id: selectedAddressId ? Number(selectedAddressId) : null,
            address_label: saveAddressLabel,
            save_address: saveAddress,
            save_address_label: saveAddressLabel
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showAlert('Order placed successfully!', 'success', alertDiv);
            
            // Show order confirmation
            setTimeout(() => {
                showOrderConfirmation(data.order_id, data.total);
            }, 1500);
        } else {
            showAlert(data.message || 'Failed to place order', 'danger', alertDiv);
            submitBtn.innerHTML = originalHTML;
            submitBtn.disabled = false;
        }
    })
    .catch(error => {
        console.error('Error placing order:', error);
        showAlert('Error placing order', 'danger', alertDiv);
        submitBtn.innerHTML = originalHTML;
        submitBtn.disabled = false;
    });
}

// Show order confirmation
function showOrderConfirmation(orderId, total) {
    const modal = document.createElement('div');
    modal.className = 'modal fade show';
    modal.style.display = 'block';
    modal.innerHTML = `
        <div class="modal-dialog modal-dialog-centered">
            <div class="modal-content">
                <div class="modal-body text-center py-5">
                    <div style="font-size: 64px; color: #00C853; margin-bottom: 20px;">
                        <i class="fas fa-check-circle"></i>
                    </div>
                    <h3>Order Confirmed!</h3>
                    <p class="text-muted mt-3">
                        Your order has been placed successfully.
                    </p>
                    <div class="bg-light p-3 rounded mt-3">
                        <p><strong>Order ID:</strong> #${orderId}</p>
                        <p><strong>Total Amount:</strong> $${parseFloat(total).toFixed(2)}</p>
                    </div>
                    <p class="text-muted small mt-3">
                        You will receive updates about your order at your registered phone number.
                    </p>
                    <button class="btn btn-primary mt-4" onclick="window.location.href='/orders'">
                        <i class="fas fa-history"></i> View My Orders
                    </button>
                </div>
            </div>
        </div>
    `;
    
    const backdrop = document.createElement('div');
    backdrop.className = 'modal-backdrop fade show';
    
    document.body.appendChild(backdrop);
    document.body.appendChild(modal);
    document.body.style.overflow = 'hidden';
}

// Show alert message
function showAlert(message, type, container) {
    if (!container) {
        container = document.getElementById('orderAlert');
    }
    
    if (!container) return;
    
    const alertTypes = {
        'success': 'alert-success',
        'danger': 'alert-danger',
        'warning': 'alert-warning',
        'info': 'alert-info'
    };
    
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert ${alertTypes[type] || alertTypes['info']} alert-dismissible fade show`;
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    container.innerHTML = '';
    container.appendChild(alertDiv);
    
    // Auto-dismiss success alerts
    if (type === 'success') {
        setTimeout(() => {
            alertDiv.remove();
        }, 3000);
    }
}
