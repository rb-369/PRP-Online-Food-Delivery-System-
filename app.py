"""
Flask Backend for Online Food Delivery Application
"""

from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from werkzeug.security import generate_password_hash, check_password_hash
import mysql.connector
from mysql.connector import Error
from datetime import datetime
from functools import wraps
import config

app = Flask(__name__)
app.secret_key = 'your_secret_key_here_change_in_production'

# Database connection function
def get_db_connection():
    """Establish database connection"""
    try:
        connection = mysql.connector.connect(
            host=config.DB_HOST,
            user=config.DB_USER,
            password=config.DB_PASSWORD,
            database=config.DB_NAME
        )
        return connection
    except Error as e:
        print(f"Database connection error: {e}")
        return None

# Login required decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# ======================== Authentication Routes ========================

@app.route('/')
def index():
    """Home page - redirect to menu if logged in"""
    if 'user_id' in session:
        return redirect(url_for('menu'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    """User login"""
    if request.method == 'POST':
        data = request.get_json()
        username = data.get('username', '').strip()
        password = data.get('password', '').strip()
        
        if not username or not password:
            return jsonify({'success': False, 'message': 'Please enter username and password'}), 400
        
        try:
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT id, username, password, role FROM users WHERE username = %s", (username,))
            user = cursor.fetchone()
            cursor.close()
            conn.close()
            
            if user and check_password_hash(user['password'], password):
                session['user_id'] = user['id']
                session['username'] = user['username']
                session['role'] = user['role']
                return jsonify({'success': True, 'message': 'Login successful', 'redirect': '/menu'})
            else:
                return jsonify({'success': False, 'message': 'Invalid username or password'}), 401
                
        except Error as e:
            print(f"Login error: {e}")
            return jsonify({'success': False, 'message': 'Database error'}), 500
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    """User registration"""
    if request.method == 'POST':
        data = request.get_json()
        username = data.get('username', '').strip()
        password = data.get('password', '').strip()
        confirm_password = data.get('confirm_password', '').strip()
        
        if not all([username, password, confirm_password]):
            return jsonify({'success': False, 'message': 'All fields are required'}), 400
        
        if len(username) < 3:
            return jsonify({'success': False, 'message': 'Username must be at least 3 characters'}), 400
        
        if len(password) < 6:
            return jsonify({'success': False, 'message': 'Password must be at least 6 characters'}), 400
        
        if password != confirm_password:
            return jsonify({'success': False, 'message': 'Passwords do not match'}), 400
        
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Check if username exists
            cursor.execute("SELECT id FROM users WHERE username = %s", (username,))
            if cursor.fetchone():
                cursor.close()
                conn.close()
                return jsonify({'success': False, 'message': 'Username already exists'}), 400
            
            # Insert new user
            hashed_password = generate_password_hash(password)
            cursor.execute(
                "INSERT INTO users (username, password, role) VALUES (%s, %s, %s)",
                (username, hashed_password, 'customer')
            )
            conn.commit()
            cursor.close()
            conn.close()
            
            return jsonify({'success': True, 'message': 'Registration successful! Please login.'})
            
        except Error as e:
            print(f"Registration error: {e}")
            return jsonify({'success': False, 'message': 'Database error'}), 500
    
    return render_template('register.html')

@app.route('/logout')
def logout():
    """User logout"""
    session.clear()
    return redirect(url_for('login'))

# ======================== Menu & Food Items ========================

@app.route('/menu')
@login_required
def menu():
    """Display food menu"""
    return render_template('menu.html', username=session.get('username'))

@app.route('/api/menu')
@login_required
def api_menu():
    """API endpoint to get all food items"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT id, name, description, price, image_path FROM menu_items ORDER BY id")
        items = cursor.fetchall()
        cursor.close()
        conn.close()
        
        return jsonify({'success': True, 'items': items})
    except Error as e:
        print(f"Menu fetch error: {e}")
        return jsonify({'success': False, 'message': 'Error fetching menu'}), 500

@app.route('/api/search')
@login_required
def search():
    """Search food items"""
    query = request.args.get('q', '').strip()
    
    if not query:
        return jsonify({'success': True, 'items': []})
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            "SELECT id, name, description, price, image_path FROM menu_items WHERE name LIKE %s OR description LIKE %s ORDER BY id",
            (f'%{query}%', f'%{query}%')
        )
        items = cursor.fetchall()
        cursor.close()
        conn.close()
        
        return jsonify({'success': True, 'items': items})
    except Error as e:
        print(f"Search error: {e}")
        return jsonify({'success': False, 'message': 'Error searching menu'}), 500

# ======================== Cart Management ========================

@app.route('/api/cart/add', methods=['POST'])
@login_required
def add_to_cart():
    """Add item to cart (stored in session)"""
    data = request.get_json()
    item_id = data.get('item_id')
    quantity = data.get('quantity', 1)
    
    if 'cart' not in session:
        session['cart'] = {}
    
    try:
        quantity = int(quantity)
        if quantity <= 0:
            return jsonify({'success': False, 'message': 'Invalid quantity'}), 400
        
        # Get item details from database
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT id, name, price FROM menu_items WHERE id = %s", (item_id,))
        item = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if not item:
            return jsonify({'success': False, 'message': 'Item not found'}), 404
        
        # Add/update item in cart
        if str(item_id) in session['cart']:
            session['cart'][str(item_id)]['quantity'] += quantity
        else:
            session['cart'][str(item_id)] = {
                'name': item['name'],
                'price': float(item['price']),
                'quantity': quantity
            }
        
        session.modified = True
        
        return jsonify({
            'success': True,
            'message': f'{item["name"]} added to cart',
            'cart_count': sum(item['quantity'] for item in session['cart'].values())
        })
        
    except Exception as e:
        print(f"Add to cart error: {e}")
        return jsonify({'success': False, 'message': 'Error adding to cart'}), 500

@app.route('/api/cart')
@login_required
def get_cart():
    """Get cart items"""
    cart = session.get('cart', {})
    items = []
    total = 0
    
    for item_id, item in cart.items():
        item_total = float(item['price']) * item['quantity']
        total += item_total
        items.append({
            'item_id': item_id,
            'name': item['name'],
            'price': item['price'],
            'quantity': item['quantity'],
            'total': round(item_total, 2)
        })
    
    return jsonify({
        'success': True,
        'items': items,
        'total': round(total, 2),
        'count': len(items)
    })

@app.route('/api/cart/remove/<item_id>', methods=['DELETE'])
@login_required
def remove_from_cart(item_id):
    """Remove item from cart"""
    cart = session.get('cart', {})
    
    if str(item_id) in cart:
        del cart[str(item_id)]
        session['cart'] = cart
        session.modified = True
    
    return jsonify({
        'success': True,
        'message': 'Item removed from cart',
        'cart_count': sum(item['quantity'] for item in session['cart'].values()) if session['cart'] else 0
    })

@app.route('/api/cart/update/<item_id>', methods=['PUT'])
@login_required
def update_cart_item(item_id):
    """Update item quantity in cart"""
    data = request.get_json()
    quantity = data.get('quantity', 0)
    cart = session.get('cart', {})
    
    try:
        quantity = int(quantity)
        
        if quantity <= 0:
            if str(item_id) in cart:
                del cart[str(item_id)]
        else:
            if str(item_id) in cart:
                cart[str(item_id)]['quantity'] = quantity
        
        session['cart'] = cart
        session.modified = True
        
        return jsonify({
            'success': True,
            'message': 'Cart updated',
            'cart_count': sum(item['quantity'] for item in session['cart'].values()) if session['cart'] else 0
        })
    except Exception as e:
        return jsonify({'success': False, 'message': 'Error updating cart'}), 500

@app.route('/api/cart/clear', methods=['POST'])
@login_required
def clear_cart():
    """Clear entire cart"""
    session['cart'] = {}
    session.modified = True
    return jsonify({'success': True, 'message': 'Cart cleared'})

# ======================== Checkout & Orders ========================

@app.route('/checkout')
@login_required
def checkout():
    """Checkout page"""
    cart = session.get('cart', {})
    if not cart:
        return redirect(url_for('menu'))
    
    return render_template('checkout.html', username=session.get('username'))

@app.route('/api/place-order', methods=['POST'])
@login_required
def place_order():
    """Place an order"""
    try:
        data = request.get_json()
        cart = session.get('cart', {})
        user_id = session.get('user_id')
        
        if not cart:
            return jsonify({'success': False, 'message': 'Cart is empty'}), 400
        
        # Calculate total
        total_amount = sum(float(item['price']) * item['quantity'] for item in cart.values())
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            # Insert order
            order_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            cursor.execute(
                """INSERT INTO orders (user_id, order_date, total_amount, delivery_address, phone_number, status)
                   VALUES (%s, %s, %s, %s, %s, %s)""",
                (user_id, order_date, float(total_amount), data.get('address', ''), data.get('phone', ''), 'Pending')
            )
            conn.commit()
            order_id = cursor.lastrowid
            
            # Insert order items
            for item_id, item in cart.items():
                cursor.execute(
                    """INSERT INTO order_items (order_id, food_item_id, quantity, price)
                       VALUES (%s, %s, %s, %s)""",
                    (order_id, int(item_id), item['quantity'], float(item['price']))
                )
            conn.commit()
            
            # Clear cart
            session['cart'] = {}
            session.modified = True
            
            cursor.close()
            conn.close()
            
            return jsonify({
                'success': True,
                'message': 'Order placed successfully!',
                'order_id': order_id,
                'total': round(total_amount, 2)
            })
            
        except Error as e:
            conn.rollback()
            print(f"Order error: {e}")
            return jsonify({'success': False, 'message': 'Error placing order'}), 500
        finally:
            cursor.close()
            conn.close()
            
    except Exception as e:
        print(f"Place order error: {e}")
        return jsonify({'success': False, 'message': 'Error processing order'}), 500

@app.route('/orders')
@login_required
def orders():
    """View order history"""
    return render_template('order_history.html', username=session.get('username'))

@app.route('/api/orders')
@login_required
def api_orders():
    """Get user's orders"""
    try:
        user_id = session.get('user_id')
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute(
            """SELECT id, order_date, total_amount, status FROM orders 
               WHERE user_id = %s ORDER BY order_date DESC""",
            (user_id,)
        )
        orders_list = cursor.fetchall()
        
        # Format dates and convert Decimal to float
        for order in orders_list:
            order['order_date'] = order['order_date'].strftime('%Y-%m-%d %H:%M:%S')
            order['total_amount'] = float(order['total_amount'])
        
        cursor.close()
        conn.close()
        
        return jsonify({'success': True, 'orders': orders_list})
    except Error as e:
        print(f"Fetch orders error: {e}")
        return jsonify({'success': False, 'message': 'Error fetching orders'}), 500

@app.route('/api/order-details/<int:order_id>')
@login_required
def api_order_details(order_id):
    """Get order details"""
    try:
        user_id = session.get('user_id')
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Verify ownership
        cursor.execute("SELECT id FROM orders WHERE id = %s AND user_id = %s", (order_id, user_id))
        if not cursor.fetchone():
            cursor.close()
            conn.close()
            return jsonify({'success': False, 'message': 'Order not found'}), 404
        
        # Get order details
        cursor.execute(
            """SELECT o.id, o.order_date, o.total_amount, o.status, 
                      oi.food_item_id, oi.quantity, oi.price, m.name
               FROM orders o
               LEFT JOIN order_items oi ON o.id = oi.order_id
               LEFT JOIN menu_items m ON oi.food_item_id = m.id
               WHERE o.id = %s AND o.user_id = %s""",
            (order_id, user_id)
        )
        rows = cursor.fetchall()
        cursor.close()
        conn.close()
        
        if not rows:
            return jsonify({'success': False, 'message': 'Order not found'}), 404
        
        # Format response
        first_row = rows[0]
        order_details = {
            'id': first_row['id'],
            'order_date': first_row['order_date'].strftime('%Y-%m-%d %H:%M:%S'),
            'total_amount': float(first_row['total_amount']),
            'status': first_row['status'],
            'items': []
        }
        
        for row in rows:
            if row['food_item_id']:
                order_details['items'].append({
                    'name': row['name'],
                    'quantity': row['quantity'],
                    'price': float(row['price']),
                    'total': float(row['quantity'] * row['price'])
                })
        
        return jsonify({'success': True, 'order': order_details})
    except Error as e:
        print(f"Fetch order details error: {e}")
        return jsonify({'success': False, 'message': 'Error fetching order details'}), 500

# ======================== Admin Routes ========================

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        
        # Check if user is admin
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT role FROM users WHERE id = %s", (session.get('user_id'),))
        user = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if not user or user['role'] != 'admin':
            return jsonify({'success': False, 'message': 'Admin access required'}), 403
        
        return f(*args, **kwargs)
    return decorated_function

@app.route('/admin/dashboard')
@admin_required
def admin_dashboard():
    """Admin dashboard"""
    return render_template('admin.html', username=session.get('username'))

@app.route('/admin/test')
@admin_required
def admin_test():
    """Admin test page - ultra simple"""
    return render_template('admin_test.html', username=session.get('username'))

@app.route('/api/admin/menu-items')
@admin_required
def admin_get_menu_items():
    """Get all menu items for admin"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM menu_items ORDER BY name ASC")
        items = cursor.fetchall()
        cursor.close()
        conn.close()
        
        return jsonify({
            'success': True,
            'items': items
        })
    except Error as e:
        print(f"Error fetching menu items: {e}")
        return jsonify({'success': False, 'message': 'Error fetching menu items'}), 500

@app.route('/api/admin/menu-items/add', methods=['POST'])
@admin_required
def admin_add_menu_item():
    """Add new food item"""
    try:
        data = request.get_json()
        name = data.get('name', '').strip()
        description = data.get('description', '').strip()
        price = data.get('price')
        category = data.get('category', '').strip()
        image_path = data.get('image_path', '').strip()
        
        if not name or not price or not category:
            return jsonify({'success': False, 'message': 'Missing required fields'}), 400
        
        try:
            price = float(price)
            if price <= 0:
                return jsonify({'success': False, 'message': 'Price must be greater than 0'}), 400
        except ValueError:
            return jsonify({'success': False, 'message': 'Invalid price format'}), 400
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            """INSERT INTO menu_items (name, description, price, category, image_path)
               VALUES (%s, %s, %s, %s, %s)""",
            (name, description, price, category, image_path)
        )
        conn.commit()
        item_id = cursor.lastrowid
        cursor.close()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': f'Food item "{name}" added successfully!',
            'item_id': item_id
        })
    except Exception as e:
        print(f"Add item error: {e}")
        return jsonify({'success': False, 'message': 'Error adding food item'}), 500

@app.route('/api/admin/menu-items/<int:item_id>/edit', methods=['PUT'])
@admin_required
def admin_edit_menu_item(item_id):
    """Edit food item"""
    try:
        data = request.get_json()
        name = data.get('name', '').strip()
        description = data.get('description', '').strip()
        price = data.get('price')
        category = data.get('category', '').strip()
        image_path = data.get('image_path', '').strip()
        
        if not name or not price or not category:
            return jsonify({'success': False, 'message': 'Missing required fields'}), 400
        
        try:
            price = float(price)
            if price <= 0:
                return jsonify({'success': False, 'message': 'Price must be greater than 0'}), 400
        except ValueError:
            return jsonify({'success': False, 'message': 'Invalid price format'}), 400
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            """UPDATE menu_items 
               SET name = %s, description = %s, price = %s, category = %s, image_path = %s
               WHERE id = %s""",
            (name, description, price, category, image_path, item_id)
        )
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': f'Food item "{name}" updated successfully!'
        })
    except Exception as e:
        print(f"Edit item error: {e}")
        return jsonify({'success': False, 'message': 'Error updating food item'}), 500

@app.route('/api/admin/menu-items/<int:item_id>/delete', methods=['DELETE'])
@admin_required
def admin_delete_menu_item(item_id):
    """Delete food item"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Get item name before deletion
        cursor.execute("SELECT name FROM menu_items WHERE id = %s", (item_id,))
        item = cursor.fetchone()
        
        if not item:
            return jsonify({'success': False, 'message': 'Item not found'}), 404
        
        # Delete the item
        cursor.execute("DELETE FROM menu_items WHERE id = %s", (item_id,))
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': f'Food item "{item["name"]}" deleted successfully!'
        })
    except Exception as e:
        print(f"Delete item error: {e}")
        return jsonify({'success': False, 'message': 'Error deleting food item'}), 500

# ======================== Error Handlers ========================

@app.errorhandler(404)
def not_found(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def server_error(error):
    return jsonify({'success': False, 'message': 'Internal server error'}), 500

if __name__ == '__main__':
    app.run(debug=True, host='localhost', port=5000)
