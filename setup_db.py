"""
Database Setup Script for Food Ordering System (SQLite)
Creates required tables and seeds initial data.
"""

import sqlite3
from werkzeug.security import generate_password_hash
import config


def setup_database():
    """Create SQLite database, tables, and sample data."""
    try:
        connection = sqlite3.connect(config.DB_PATH)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        cursor = connection.cursor()

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                email TEXT,
                phone TEXT,
                address TEXT,
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
                is_veg INTEGER NOT NULL DEFAULT 1,
                prep_time_minutes INTEGER NOT NULL DEFAULT 30,
                is_available INTEGER DEFAULT 1,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                order_date TEXT DEFAULT CURRENT_TIMESTAMP,
                total_amount REAL NOT NULL,
                delivery_address TEXT,
                phone_number TEXT,
                address_label TEXT,
                building_name TEXT,
                flat_no TEXT,
                address_id INTEGER,
                status TEXT DEFAULT 'Pending',
                notes TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
            """
        )

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

        users_data = [
            ("john_doe", "password", "john@example.com", "9876543210", "123 Main St", "customer"),
            ("admin", "admin123", "admin@example.com", "9999999999", "Admin Office", "admin"),
            ("admin2", "password", "admin2@example.com", "9999999998", "Admin Office 2", "admin"),
        ]

        for username, password, email, phone, address, role in users_data:
            hashed_password = generate_password_hash(password)
            cursor.execute(
                """
                INSERT OR IGNORE INTO users (username, password, email, phone, address, role)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (username, hashed_password, email, phone, address, role),
            )

        # Ensure admin credentials are deterministic for local usage.
        admin_password = generate_password_hash("admin123")
        cursor.execute(
            "UPDATE users SET password = ?, role = 'admin' WHERE username = ?",
            (admin_password, "admin"),
        )

        menu_data = [
            ("Classic Burger", "Juicy burger with lettuce, tomato, and cheese", 399, "Burgers", "burger.png", 0, 25),
            ("Margherita Pizza", "Fresh mozzarella, basil, and tomato sauce on crispy crust", 599, "Pizza", "pizza.png", 1, 30),
            ("Spaghetti Carbonara", "Creamy pasta with bacon and parmesan cheese", 499, "Pasta", "pasta.png", 0, 22),
            ("Grilled Chicken Sandwich", "Tender grilled chicken with fresh vegetables", 349, "Sandwiches", "sandwich.png", 0, 18),
            ("Crispy French Fries", "Golden and delicious fried potatoes with salt", 199, "Sides", "fries.png", 1, 12),
            ("Thai Noodles", "Stir-fried noodles with vegetables and spicy sauce", 399, "Noodles", "noodles.png", 1, 20),
            ("Vegetable Biryani", "Fragrant rice with vegetables and aromatic spices", 549, "Rice Dishes", "biryani.png", 1, 32),
            ("Iced Coffee", "Refreshing cold coffee with ice and cream", 249, "Beverages", "coffee.png", 1, 8),
            ("Tropical Juice", "Fresh blend of tropical fruits", 299, "Beverages", "juice.png", 1, 8),
            ("Chocolate Cake", "Rich and moist chocolate layer cake", 349, "Desserts", "cake.png", 1, 10),
            ("Paneer Butter Masala", "Rich tomato-butter gravy with soft paneer cubes", 429, "Indian Main Course", "paneer-butter-masala.jpeg", 1, 28),
            ("Dal Makhani", "Slow-cooked black lentils in creamy buttery gravy", 349, "Dal & Gravy", "dal_makhani.png", 1, 26),
            ("Kadai Paneer", "Paneer tossed with capsicum in spicy kadai masala", 399, "Indian Main Course", "kadai_paneer.png", 1, 24),
            ("Butter Chicken", "Tender chicken in creamy tomato-butter curry", 499, "Indian Curry", "butter_chicken.png", 0, 28),
            ("Chole Masala", "Punjabi chickpea curry cooked with aromatic spices", 329, "Indian Curry", "chole_masala.png", 1, 22),
            ("Jeera Rice", "Fragrant basmati rice tempered with cumin", 239, "Rice & Biryani", "jeera_rice.png", 1, 15),
        ]

        cursor.execute("DELETE FROM menu_items")
        cursor.executemany(
            """
            INSERT INTO menu_items (name, description, price, category, image_path, is_veg, prep_time_minutes)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            menu_data,
        )

        connection.commit()
        cursor.close()
        connection.close()

        print("SQLite database setup completed successfully.")
        print("DB file:", config.DB_PATH)
        print("Test user: john_doe / password")
        print("Admin user: admin / admin123")
        return True

    except sqlite3.Error as e:
        print(f"SQLite setup error: {e}")
        return False


if __name__ == "__main__":
    print("Food Ordering System - SQLite Setup")
    print("=" * 50)
    setup_database()
