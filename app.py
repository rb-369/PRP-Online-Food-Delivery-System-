"""
Flask Backend for Online Food Delivery Application
"""

from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
from datetime import datetime
from functools import wraps
import config

app = Flask(__name__)
app.secret_key = 'your_secret_key_here_change_in_production'

Error = sqlite3.Error


class SQLiteCursorWrapper:
    def __init__(self, cursor):
        self._cursor = cursor

    def execute(self, query, params=None):
        sqlite_query = query.replace("%s", "?")
        self._cursor.execute(sqlite_query, params or ())
        return self

    def fetchone(self):
        row = self._cursor.fetchone()
        return dict(row) if isinstance(row, sqlite3.Row) else row

    def fetchall(self):
        rows = self._cursor.fetchall()
        return [dict(row) if isinstance(row, sqlite3.Row) else row for row in rows]

    @property
    def lastrowid(self):
        return self._cursor.lastrowid

    @property
    def rowcount(self):
        return self._cursor.rowcount

    def close(self):
        self._cursor.close()


class SQLiteConnectionWrapper:
    def __init__(self, connection):
        self._connection = connection

    def cursor(self, dictionary=False):
        return SQLiteCursorWrapper(self._connection.cursor())

    def commit(self):
        self._connection.commit()

    def rollback(self):
        self._connection.rollback()

    def close(self):
        self._connection.close()


def ensure_column(cursor, table_name, column_name, definition):
    """Add a column if it does not exist (SQLite migration-safe)."""
    cursor.execute(f"PRAGMA table_info({table_name})")
    existing_columns = {row[1] for row in cursor.fetchall()}
    if column_name not in existing_columns:
        cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {definition}")


def initialize_database(connection):
    """Create required tables and seed defaults for SQLite."""
    cursor = connection.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'customer',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS menu_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            price REAL NOT NULL,
            category TEXT,
            image_path TEXT,
            is_available INTEGER DEFAULT 1,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    ensure_column(cursor, 'menu_items', 'is_veg', 'INTEGER NOT NULL DEFAULT 1')
    ensure_column(cursor, 'menu_items', 'prep_time_minutes', 'INTEGER NOT NULL DEFAULT 30')
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            order_date TEXT DEFAULT CURRENT_TIMESTAMP,
            total_amount REAL NOT NULL,
            delivery_address TEXT,
            phone_number TEXT,
            status TEXT DEFAULT 'Pending',
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
        """
    )

    ensure_column(cursor, 'orders', 'address_label', 'TEXT')
    ensure_column(cursor, 'orders', 'building_name', 'TEXT')
    ensure_column(cursor, 'orders', 'flat_no', 'TEXT')
    ensure_column(cursor, 'orders', 'address_id', 'INTEGER')
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS order_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER NOT NULL,
            food_item_id INTEGER NOT NULL,
            quantity INTEGER NOT NULL,
            price REAL NOT NULL,
            FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE,
            FOREIGN KEY (food_item_id) REFERENCES menu_items(id)
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS addresses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            label TEXT NOT NULL DEFAULT 'Other',
            address TEXT NOT NULL,
            building_name TEXT,
            flat_no TEXT,
            is_default INTEGER NOT NULL DEFAULT 0,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS order_reviews (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            order_id INTEGER NOT NULL,
            rating INTEGER NOT NULL CHECK (rating BETWEEN 1 AND 5),
            comment TEXT,
            status TEXT NOT NULL DEFAULT 'pending',
            moderated_by INTEGER,
            moderated_at TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, order_id),
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS item_reviews (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            order_id INTEGER NOT NULL,
            menu_item_id INTEGER NOT NULL,
            rating INTEGER NOT NULL CHECK (rating BETWEEN 1 AND 5),
            comment TEXT,
            status TEXT NOT NULL DEFAULT 'pending',
            moderated_by INTEGER,
            moderated_at TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, order_id, menu_item_id),
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE,
            FOREIGN KEY (menu_item_id) REFERENCES menu_items(id) ON DELETE CASCADE
        )
        """
    )

    # Seed and enforce default admin credentials for local development.
    admin_password = generate_password_hash('admin123')
    cursor.execute(
        "INSERT OR IGNORE INTO users (username, password, role) VALUES (?, ?, ?)",
        ('admin', admin_password, 'admin')
    )
    cursor.execute(
        "UPDATE users SET password = ?, role = 'admin' WHERE username = ?",
        (admin_password, 'admin')
    )

    cursor.execute("SELECT COUNT(*) AS total FROM menu_items")
    menu_count = cursor.fetchone()[0]
    if menu_count == 0:
        menu_items = [
            ('Classic Burger', 'Juicy burger with lettuce, tomato, and cheese', 399.0, 'Burgers', 'burger.png', 0, 25),
            ('Margherita Pizza', 'Fresh mozzarella, basil, and tomato sauce on crispy crust', 599.0, 'Pizza', 'pizza.png', 1, 30),
            ('Spaghetti Carbonara', 'Creamy pasta with bacon and parmesan cheese', 499.0, 'Pasta', 'pasta.png', 0, 22),
            ('Grilled Chicken Sandwich', 'Tender grilled chicken with fresh vegetables', 349.0, 'Sandwiches', 'sandwich.png', 0, 18),
            ('Crispy French Fries', 'Golden and delicious fried potatoes with salt', 199.0, 'Sides', 'fries.png', 1, 12),
            ('Thai Noodles', 'Stir-fried noodles with vegetables and spicy sauce', 399.0, 'Noodles', 'noodles.png', 1, 20),
            ('Vegetable Biryani', 'Fragrant rice with vegetables and aromatic spices', 549.0, 'Rice Dishes', 'biryani.png', 1, 32),
            ('Iced Coffee', 'Refreshing cold coffee with ice and cream', 249.0, 'Beverages', 'coffee.png', 1, 8),
            ('Tropical Juice', 'Fresh blend of tropical fruits', 299.0, 'Beverages', 'juice.png', 1, 8),
            ('Chocolate Cake', 'Rich and moist chocolate layer cake', 349.0, 'Desserts', 'cake.png', 1, 10),
            ('Paneer Butter Masala', 'Rich tomato-butter gravy with soft paneer cubes', 429.0, 'Indian Main Course', 'paneer-butter-masala.jpeg', 1, 28),
            ('Dal Makhani', 'Slow-cooked black lentils in creamy buttery gravy', 349.0, 'Dal & Gravy', 'dal_makhani.png', 1, 26),
            ('Kadai Paneer', 'Paneer tossed with capsicum in spicy kadai masala', 399.0, 'Indian Main Course', 'kadai_paneer.png', 1, 24),
            ('Butter Chicken', 'Tender chicken in creamy tomato-butter curry', 499.0, 'Indian Curry', 'butter_chicken.png', 0, 28),
            ('Chole Masala', 'Punjabi chickpea curry cooked with aromatic spices', 329.0, 'Indian Curry', 'chole_masala.png', 1, 22),
            ('Jeera Rice', 'Fragrant basmati rice tempered with cumin', 239.0, 'Rice & Biryani', 'jeera_rice.png', 1, 15),
        ]
        cursor.executemany(
            """
            INSERT INTO menu_items (name, description, price, category, image_path, is_veg, prep_time_minutes)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            menu_items
        )

    cursor.execute("UPDATE menu_items SET is_veg = 1 WHERE is_veg IS NULL")
    cursor.execute("UPDATE menu_items SET prep_time_minutes = 30 WHERE prep_time_minutes IS NULL OR prep_time_minutes <= 0")
    cursor.execute("UPDATE menu_items SET is_veg = 0 WHERE LOWER(name) LIKE '%chicken%' OR LOWER(name) LIKE '%carbonara%'")

    connection.commit()
    cursor.close()


def format_order_date(value):
    """Normalize date values from SQLite into API-friendly strings."""
    if isinstance(value, datetime):
        return value.strftime('%Y-%m-%d %H:%M:%S')
    if isinstance(value, str):
        return value
    return str(value)


def fetch_menu_items(filters):
    """Fetch menu items using search, filter and sort inputs."""
    query = filters.get('q', '').strip()
    category = filters.get('category', '').strip()
    veg_type = filters.get('veg_type', '').strip().lower()
    popularity = filters.get('popularity', '').strip().lower()
    sort_by = filters.get('sort_by', '').strip().lower()

    where_clauses = ["m.is_available = 1"]
    params = []

    if query:
        where_clauses.append("(m.name LIKE %s OR m.description LIKE %s)")
        params.extend([f"%{query}%", f"%{query}%"])

    if category and category.lower() != 'all':
        where_clauses.append("m.category = %s")
        params.append(category)

    if veg_type == 'veg':
        where_clauses.append("m.is_veg = 1")
    elif veg_type == 'non-veg':
        where_clauses.append("m.is_veg = 0")

    try:
        min_price = float(filters.get('min_price', '').strip()) if filters.get('min_price', '').strip() else None
    except ValueError:
        min_price = None

    try:
        max_price = float(filters.get('max_price', '').strip()) if filters.get('max_price', '').strip() else None
    except ValueError:
        max_price = None

    if min_price is not None:
        where_clauses.append("m.price >= %s")
        params.append(min_price)
    if max_price is not None:
        where_clauses.append("m.price <= %s")
        params.append(max_price)

    if popularity == 'high':
        where_clauses.append("COALESCE(pop.order_count, 0) >= 10")
    elif popularity == 'medium':
        where_clauses.append("COALESCE(pop.order_count, 0) BETWEEN 4 AND 9")
    elif popularity == 'low':
        where_clauses.append("COALESCE(pop.order_count, 0) <= 3")

    sort_map = {
        'rating': "avg_rating DESC, rating_count DESC, m.name ASC",
        'price_asc': "m.price ASC",
        'price_desc': "m.price DESC",
        'time': "m.prep_time_minutes ASC",
        'popularity': "popularity_score DESC, avg_rating DESC",
        'newest': "m.id DESC",
    }
    order_by_clause = sort_map.get(sort_by, "m.id DESC")

    sql = f"""
        SELECT
            m.id,
            m.name,
            m.description,
            m.price,
            m.category,
            m.image_path,
            m.is_veg,
            m.prep_time_minutes,
            COALESCE(avg_rev.avg_rating, 0) AS avg_rating,
            COALESCE(avg_rev.rating_count, 0) AS rating_count,
            COALESCE(pop.order_count, 0) AS popularity_score
        FROM menu_items m
        LEFT JOIN (
            SELECT menu_item_id, ROUND(AVG(rating), 1) AS avg_rating, COUNT(*) AS rating_count
            FROM item_reviews
            WHERE status = 'approved'
            GROUP BY menu_item_id
        ) avg_rev ON avg_rev.menu_item_id = m.id
        LEFT JOIN (
            SELECT food_item_id, COUNT(*) AS order_count
            FROM order_items
            GROUP BY food_item_id
        ) pop ON pop.food_item_id = m.id
        WHERE {' AND '.join(where_clauses)}
        ORDER BY {order_by_clause}
    """

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(sql, tuple(params))
    items = cursor.fetchall()
    cursor.close()
    conn.close()

    return items

# Database connection function
def get_db_connection():
    """Establish database connection"""
    try:
        connection = sqlite3.connect(config.DB_PATH)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        initialize_database(connection)
        return SQLiteConnectionWrapper(connection)
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
    """API endpoint to get food items with smart search/filter/sort."""
    try:
        items = fetch_menu_items({
            'q': request.args.get('q', ''),
            'category': request.args.get('category', ''),
            'min_price': request.args.get('min_price', ''),
            'max_price': request.args.get('max_price', ''),
            'veg_type': request.args.get('veg_type', ''),
            'popularity': request.args.get('popularity', ''),
            'sort_by': request.args.get('sort_by', ''),
        })

        categories = sorted({item['category'] for item in items if item.get('category')})
        
        return jsonify({'success': True, 'items': items, 'categories': categories})
    except Error as e:
        print(f"Menu fetch error: {e}")
        return jsonify({'success': False, 'message': 'Error fetching menu'}), 500

@app.route('/api/search')
@login_required
def search():
    """Search food items"""
    try:
        items = fetch_menu_items({'q': request.args.get('q', '')})
        
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

        address_text = (data.get('address') or '').strip()
        building_name = (data.get('building_name') or '').strip()
        flat_no = (data.get('flat_no') or '').strip()
        address_label = (data.get('address_label') or '').strip()
        phone = (data.get('phone') or '').strip()
        address_id = data.get('address_id')
        save_address = bool(data.get('save_address', False))
        save_address_label = (data.get('save_address_label') or 'Other').strip()

        if address_id:
            try:
                address_id = int(address_id)
            except (TypeError, ValueError):
                address_id = None
        else:
            address_id = None
        
        # Calculate total
        total_amount = sum(float(item['price']) * item['quantity'] for item in cart.values())
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            if address_id:
                cursor.execute(
                    """SELECT id, label, address, building_name, flat_no
                       FROM addresses WHERE id = %s AND user_id = %s""",
                    (address_id, user_id)
                )
                saved_address = cursor.fetchone()
                if not saved_address:
                    return jsonify({'success': False, 'message': 'Selected saved address not found'}), 404

                address_label = saved_address['label']
                address_text = saved_address['address']
                building_name = saved_address['building_name'] or ''
                flat_no = saved_address['flat_no'] or ''

            if not address_text or not phone:
                return jsonify({'success': False, 'message': 'Address and phone are required'}), 400

            if save_address and not address_id:
                cursor.execute(
                    """INSERT INTO addresses (user_id, label, address, building_name, flat_no, is_default)
                       VALUES (%s, %s, %s, %s, %s, 0)""",
                    (user_id, save_address_label or 'Other', address_text, building_name, flat_no)
                )

            address_parts = [flat_no, building_name, address_text]
            full_address = ', '.join([part for part in address_parts if part])

            # Insert order
            order_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            cursor.execute(
                """INSERT INTO orders (user_id, order_date, total_amount, delivery_address, phone_number, status, address_label, building_name, flat_no, address_id)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                (user_id, order_date, float(total_amount), full_address, phone, 'Pending', address_label, building_name, flat_no, address_id)
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
            """SELECT o.id, o.order_date, o.total_amount, o.status,
                      CASE WHEN r.id IS NOT NULL THEN 1 ELSE 0 END AS has_order_review
               FROM orders o
               LEFT JOIN order_reviews r ON r.order_id = o.id AND r.user_id = %s
               WHERE o.user_id = %s
               ORDER BY o.order_date DESC""",
            (user_id, user_id)
        )
        orders_list = cursor.fetchall()
        
        # Format dates and convert Decimal to float
        for order in orders_list:
            order['order_date'] = format_order_date(order['order_date'])
            order['total_amount'] = float(order['total_amount'])
            order['has_order_review'] = bool(order.get('has_order_review', 0))
        
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
            """SELECT o.id, o.order_date, o.total_amount, o.status, o.delivery_address, o.address_label, o.building_name, o.flat_no,
                      oi.food_item_id, oi.quantity, oi.price, m.name,
                      ir.id AS item_review_id, ir.rating AS item_rating, ir.comment AS item_comment, ir.status AS item_review_status
               FROM orders o
               LEFT JOIN order_items oi ON o.id = oi.order_id
               LEFT JOIN menu_items m ON oi.food_item_id = m.id
               LEFT JOIN item_reviews ir ON ir.order_id = oi.order_id AND ir.menu_item_id = oi.food_item_id AND ir.user_id = %s
               WHERE o.id = %s AND o.user_id = %s""",
            (user_id, order_id, user_id)
        )
        rows = cursor.fetchall()

        cursor.execute(
            """SELECT id, rating, comment, status
               FROM order_reviews
               WHERE order_id = %s AND user_id = %s
               LIMIT 1""",
            (order_id, user_id)
        )
        order_review = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if not rows:
            return jsonify({'success': False, 'message': 'Order not found'}), 404
        
        # Format response
        first_row = rows[0]
        order_details = {
            'id': first_row['id'],
            'order_date': format_order_date(first_row['order_date']),
            'total_amount': float(first_row['total_amount']),
            'status': first_row['status'],
            'delivery_address': first_row.get('delivery_address'),
            'address_label': first_row.get('address_label'),
            'building_name': first_row.get('building_name'),
            'flat_no': first_row.get('flat_no'),
            'order_review': {
                'id': order_review['id'],
                'rating': order_review['rating'],
                'comment': order_review.get('comment') or '',
                'status': order_review['status'],
            } if order_review else None,
            'items': []
        }
        
        for row in rows:
            if row['food_item_id']:
                order_details['items'].append({
                    'menu_item_id': row['food_item_id'],
                    'name': row['name'],
                    'quantity': row['quantity'],
                    'price': float(row['price']),
                    'total': float(row['quantity'] * row['price']),
                    'review': {
                        'id': row['item_review_id'],
                        'rating': row['item_rating'],
                        'comment': row.get('item_comment') or '',
                        'status': row.get('item_review_status') or 'pending',
                    } if row.get('item_review_id') else None,
                })
        
        return jsonify({'success': True, 'order': order_details})
    except Error as e:
        print(f"Fetch order details error: {e}")
        return jsonify({'success': False, 'message': 'Error fetching order details'}), 500


@app.route('/api/addresses')
@login_required
def get_addresses():
    """Get saved delivery addresses for current user."""
    try:
        user_id = session.get('user_id')
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            """SELECT id, label, address, building_name, flat_no, is_default
               FROM addresses
               WHERE user_id = %s
               ORDER BY is_default DESC, id DESC""",
            (user_id,)
        )
        addresses = cursor.fetchall()
        cursor.close()
        conn.close()

        return jsonify({'success': True, 'addresses': addresses})
    except Error as e:
        print(f"Fetch addresses error: {e}")
        return jsonify({'success': False, 'message': 'Error fetching addresses'}), 500


@app.route('/api/addresses', methods=['POST'])
@login_required
def add_address():
    """Add a new saved address for current user."""
    try:
        data = request.get_json() or {}
        user_id = session.get('user_id')
        label = (data.get('label') or 'Other').strip()
        address = (data.get('address') or '').strip()
        building_name = (data.get('building_name') or '').strip()
        flat_no = (data.get('flat_no') or '').strip()
        is_default = 1 if data.get('is_default') else 0

        if not address:
            return jsonify({'success': False, 'message': 'Address is required'}), 400

        conn = get_db_connection()
        cursor = conn.cursor()

        if is_default:
            cursor.execute("UPDATE addresses SET is_default = 0 WHERE user_id = %s", (user_id,))

        cursor.execute(
            """INSERT INTO addresses (user_id, label, address, building_name, flat_no, is_default)
               VALUES (%s, %s, %s, %s, %s, %s)""",
            (user_id, label, address, building_name, flat_no, is_default)
        )
        conn.commit()
        new_id = cursor.lastrowid
        cursor.close()
        conn.close()

        return jsonify({'success': True, 'message': 'Address saved', 'address_id': new_id})
    except Error as e:
        print(f"Add address error: {e}")
        return jsonify({'success': False, 'message': 'Error saving address'}), 500


@app.route('/api/addresses/<int:address_id>', methods=['DELETE'])
@login_required
def delete_address(address_id):
    """Delete one saved address owned by current user."""
    try:
        user_id = session.get('user_id')
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM addresses WHERE id = %s AND user_id = %s", (address_id, user_id))
        conn.commit()
        deleted = cursor.rowcount
        cursor.close()
        conn.close()

        if not deleted:
            return jsonify({'success': False, 'message': 'Address not found'}), 404

        return jsonify({'success': True, 'message': 'Address deleted'})
    except Error as e:
        print(f"Delete address error: {e}")
        return jsonify({'success': False, 'message': 'Error deleting address'}), 500


@app.route('/api/reviews', methods=['POST'])
@login_required
def submit_reviews():
    """Submit or update per-order and per-item reviews."""
    try:
        data = request.get_json() or {}
        user_id = session.get('user_id')
        order_id = data.get('order_id')
        order_rating = data.get('order_rating')
        order_comment = (data.get('order_comment') or '').strip()
        item_reviews = data.get('item_reviews') or []

        try:
            order_id = int(order_id)
        except (TypeError, ValueError):
            return jsonify({'success': False, 'message': 'Invalid order ID'}), 400

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT id FROM orders WHERE id = %s AND user_id = %s", (order_id, user_id))
        order = cursor.fetchone()
        if not order:
            cursor.close()
            conn.close()
            return jsonify({'success': False, 'message': 'Order not found'}), 404

        if order_rating is not None:
            try:
                order_rating = int(order_rating)
            except (TypeError, ValueError):
                cursor.close()
                conn.close()
                return jsonify({'success': False, 'message': 'Order rating must be a number between 1 and 5'}), 400

            if order_rating < 1 or order_rating > 5:
                cursor.close()
                conn.close()
                return jsonify({'success': False, 'message': 'Order rating must be between 1 and 5'}), 400

            cursor.execute(
                """INSERT INTO order_reviews (user_id, order_id, rating, comment, status)
                   VALUES (%s, %s, %s, %s, 'pending')
                   ON CONFLICT(user_id, order_id)
                   DO UPDATE SET rating = excluded.rating, comment = excluded.comment, status = 'pending', moderated_by = NULL, moderated_at = NULL""",
                (user_id, order_id, order_rating, order_comment)
            )

        for review in item_reviews:
            menu_item_id = review.get('menu_item_id')
            rating = review.get('rating')
            comment = (review.get('comment') or '').strip()

            if not menu_item_id or rating is None:
                continue

            try:
                menu_item_id = int(menu_item_id)
                rating = int(rating)
            except (TypeError, ValueError):
                continue

            if rating < 1 or rating > 5:
                continue

            cursor.execute(
                """SELECT 1 FROM order_items WHERE order_id = %s AND food_item_id = %s LIMIT 1""",
                (order_id, menu_item_id)
            )
            exists_in_order = cursor.fetchone()
            if not exists_in_order:
                continue

            cursor.execute(
                """INSERT INTO item_reviews (user_id, order_id, menu_item_id, rating, comment, status)
                   VALUES (%s, %s, %s, %s, %s, 'pending')
                   ON CONFLICT(user_id, order_id, menu_item_id)
                   DO UPDATE SET rating = excluded.rating, comment = excluded.comment, status = 'pending', moderated_by = NULL, moderated_at = NULL""",
                (user_id, order_id, menu_item_id, rating, comment)
            )

        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({'success': True, 'message': 'Review submitted and pending admin moderation'})
    except Error as e:
        print(f"Submit review error: {e}")
        return jsonify({'success': False, 'message': 'Error submitting review'}), 500

# ======================== Admin Routes ========================

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            if request.path.startswith('/api/'):
                return jsonify({'success': False, 'message': 'Authentication required'}), 401
            return redirect(url_for('login'))
        
        # Check if user is admin
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT role FROM users WHERE id = %s", (session.get('user_id'),))
        user = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if not user or user['role'] != 'admin':
            if request.path.startswith('/api/'):
                return jsonify({'success': False, 'message': 'Admin access required'}), 403
            return redirect(url_for('menu'))
        
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


@app.route('/api/admin/reviews/pending')
@admin_required
def admin_get_pending_reviews():
    """Get pending order and item reviews for moderation."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute(
            """SELECT 'order' AS review_type, r.id, r.order_id, NULL AS menu_item_id,
                      NULL AS item_name, u.username, r.rating, r.comment, r.status, r.created_at
               FROM order_reviews r
               JOIN users u ON u.id = r.user_id
               WHERE r.status = 'pending'
               ORDER BY r.created_at DESC"""
        )
        order_reviews = cursor.fetchall()

        cursor.execute(
            """SELECT 'item' AS review_type, r.id, r.order_id, r.menu_item_id,
                      m.name AS item_name, u.username, r.rating, r.comment, r.status, r.created_at
               FROM item_reviews r
               JOIN users u ON u.id = r.user_id
               JOIN menu_items m ON m.id = r.menu_item_id
               WHERE r.status = 'pending'
               ORDER BY r.created_at DESC"""
        )
        item_reviews = cursor.fetchall()

        cursor.close()
        conn.close()

        return jsonify({'success': True, 'reviews': order_reviews + item_reviews})
    except Error as e:
        print(f"Pending reviews error: {e}")
        return jsonify({'success': False, 'message': 'Error fetching pending reviews'}), 500


@app.route('/api/admin/reviews/<review_type>/<int:review_id>/moderate', methods=['PUT'])
@admin_required
def admin_moderate_review(review_type, review_id):
    """Approve or reject a review."""
    try:
        data = request.get_json() or {}
        next_status = (data.get('status') or '').strip().lower()
        if next_status not in ('approved', 'rejected'):
            return jsonify({'success': False, 'message': 'Invalid status'}), 400

        table_name = 'order_reviews' if review_type == 'order' else 'item_reviews' if review_type == 'item' else None
        if not table_name:
            return jsonify({'success': False, 'message': 'Invalid review type'}), 400

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            f"UPDATE {table_name} SET status = %s, moderated_by = %s, moderated_at = %s WHERE id = %s",
            (next_status, session.get('user_id'), datetime.now().strftime('%Y-%m-%d %H:%M:%S'), review_id)
        )
        conn.commit()
        updated = cursor.rowcount
        cursor.close()
        conn.close()

        if not updated:
            return jsonify({'success': False, 'message': 'Review not found'}), 404

        return jsonify({'success': True, 'message': f'Review {next_status} successfully'})
    except Error as e:
        print(f"Moderation error: {e}")
        return jsonify({'success': False, 'message': 'Error moderating review'}), 500

# ======================== Error Handlers ========================

@app.errorhandler(404)
def not_found(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def server_error(error):
    return jsonify({'success': False, 'message': 'Internal server error'}), 500

if __name__ == '__main__':
    app.run(debug=True, host='localhost', port=5000)
