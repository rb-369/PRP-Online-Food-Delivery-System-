// Authentication JavaScript - Login and Registration

document.addEventListener('DOMContentLoaded', function() {
    // Login form submission
    const loginForm = document.getElementById('loginForm');
    if (loginForm) {
        loginForm.addEventListener('submit', handleLogin);
    }
    
    // Register form submission
    const registerForm = document.getElementById('registerForm');
    if (registerForm) {
        registerForm.addEventListener('submit', handleRegister);
    }
});

// Handle login
function handleLogin(e) {
    e.preventDefault();
    
    const username = document.getElementById('login-username').value.trim();
    const password = document.getElementById('login-password').value;
    const alertDiv = document.getElementById('loginAlert');
    
    // Validation
    if (!username || !password) {
        showAlert(alertDiv, 'Please enter both username and password', 'danger');
        return;
    }
    
    // Show loading state
    const submitBtn = e.target.querySelector('button[type="submit"]');
    const originalText = submitBtn.innerHTML;
    submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Logging in...';
    submitBtn.disabled = true;
    
    // Send login request
    fetch('/login', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            username: username,
            password: password
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showAlert(alertDiv, 'Login successful! Redirecting...', 'success');
            setTimeout(() => {
                window.location.href = data.redirect;
            }, 1500);
        } else {
            showAlert(alertDiv, data.message || 'Login failed', 'danger');
            submitBtn.innerHTML = originalText;
            submitBtn.disabled = false;
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showAlert(alertDiv, 'An error occurred. Please try again.', 'danger');
        submitBtn.innerHTML = originalText;
        submitBtn.disabled = false;
    });
}

// Handle registration
function handleRegister(e) {
    e.preventDefault();
    
    const username = document.getElementById('register-username').value.trim();
    const password = document.getElementById('register-password').value;
    const confirmPassword = document.getElementById('register-confirm-password').value;
    const alertDiv = document.getElementById('registerAlert');
    
    // Validation
    if (!username || !password || !confirmPassword) {
        showAlert(alertDiv, 'Please fill in all fields', 'danger');
        return;
    }
    
    if (username.length < 3) {
        showAlert(alertDiv, 'Username must be at least 3 characters', 'danger');
        return;
    }
    
    if (password.length < 6) {
        showAlert(alertDiv, 'Password must be at least 6 characters', 'danger');
        return;
    }
    
    if (password !== confirmPassword) {
        showAlert(alertDiv, 'Passwords do not match', 'danger');
        return;
    }
    
    // Show loading state
    const submitBtn = e.target.querySelector('button[type="submit"]');
    const originalText = submitBtn.innerHTML;
    submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Creating account...';
    submitBtn.disabled = true;
    
    // Send register request
    fetch('/register', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            username: username,
            password: password,
            confirm_password: confirmPassword
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showAlert(alertDiv, data.message, 'success');
            // Clear form
            e.target.reset();
            // Switch to login tab
            setTimeout(() => {
                const loginTab = document.getElementById('login-tab');
                if (loginTab) {
                    loginTab.click();
                }
            }, 1500);
        } else {
            showAlert(alertDiv, data.message || 'Registration failed', 'danger');
            submitBtn.innerHTML = originalText;
            submitBtn.disabled = false;
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showAlert(alertDiv, 'An error occurred. Please try again.', 'danger');
        submitBtn.innerHTML = originalText;
        submitBtn.disabled = false;
    });
}

// Show alert message
function showAlert(alertDiv, message, type) {
    if (!alertDiv) return;
    
    const alertTypes = {
        'success': 'alert-success',
        'danger': 'alert-danger',
        'warning': 'alert-warning',
        'info': 'alert-info'
    };
    
    alertDiv.innerHTML = `
        <div class="alert ${alertTypes[type] || alertTypes['info']} alert-dismissible fade show" role="alert">
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        </div>
    `;
    
    // Auto-dismiss success alerts
    if (type === 'success') {
        setTimeout(() => {
            const alert = alertDiv.querySelector('.alert');
            if (alert) {
                alert.remove();
            }
        }, 3000);
    }
}

// Toggle password visibility
function togglePasswordVisibility(inputId, iconId) {
    const input = document.getElementById(inputId);
    const icon = document.getElementById(iconId);
    
    if (input.type === 'password') {
        input.type = 'text';
        icon.classList.remove('fa-eye-slash');
        icon.classList.add('fa-eye');
    } else {
        input.type = 'password';
        icon.classList.remove('fa-eye');
        icon.classList.add('fa-eye-slash');
    }
}
