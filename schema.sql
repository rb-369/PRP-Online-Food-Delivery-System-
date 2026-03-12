CREATE DATABASE IF NOT EXISTS food_ordering_db;
USE food_ordering_db;

-- Users table (Admins & Customers)
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    role ENUM('admin', 'user') DEFAULT 'user',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Food Items catalog
CREATE TABLE IF NOT EXISTS food_items (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    category VARCHAR(50) NOT NULL,
    price DECIMAL(10, 2) NOT NULL,
    image_path VARCHAR(255)
);

-- Orders header table
CREATE TABLE IF NOT EXISTS orders (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    total_amount DECIMAL(10, 2) NOT NULL,
    order_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Order details table
CREATE TABLE IF NOT EXISTS order_items (
    id INT AUTO_INCREMENT PRIMARY KEY,
    order_id INT NOT NULL,
    food_item_id INT NOT NULL,
    quantity INT NOT NULL,
    subtotal DECIMAL(10, 2) NOT NULL,
    FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE,
    FOREIGN KEY (food_item_id) REFERENCES food_items(id)
);

-- Seed Default Admin User (Password is 'admin123' hashed using SHA-256 for simplicity in our app: 240be518fabd2724ddb6f04eeb1da5967448d7e831c08c8fa822809f74c720a9)
INSERT IGNORE INTO users (username, password, role) VALUES 
('admin', '240be518fabd2724ddb6f04eeb1da5967448d7e831c08c8fa822809f74c720a9', 'admin');

-- Seed Food Data
TRUNCATE TABLE food_items;
INSERT INTO food_items (name, category, price, image_path) VALUES
('Classic Burger', 'Snacks', 150.00, 'images/burger.png'),
('Cheese Pizza', 'Main Course', 300.00, 'images/pizza.png'),
('White Sauce Pasta', 'Main Course', 250.00, 'images/pasta.png'),
('Club Sandwich', 'Snacks', 120.00, 'images/sandwich.png'),
('French Fries', 'Snacks', 90.00, 'images/fries.png'),
('Hakka Noodles', 'Main Course', 180.00, 'images/noodles.png'),
('Chicken Biryani', 'Main Course', 350.00, 'images/biryani.png'),
('Cold Coffee', 'Beverages', 100.00, 'images/coffee.png'),
('Fresh Orange Juice', 'Beverages', 80.00, 'images/juice.png'),
('Chocolate Cake', 'Desserts', 400.00, 'images/cake.png');
