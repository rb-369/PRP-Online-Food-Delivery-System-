# Online Food Ordering Desktop Application

A complete, feature-rich Python Tkinter GUI application connected to a MySQL database, designed for a diploma final practical submission. This project demonstrates Object-Oriented Programming (OOP), modular design, database connectivity, error handling, and modern UI design.

## Folder Structure

```
python-project/
│
├── main.py                 # Application entry point
├── db.py                   # MySQL database connection & CRUD operations
├── auth.py                 # Login & Registration module
├── menu.py                 # Food menu display, search, and cart management
├── billing.py              # Bill generation and receipt window
├── history.py              # Order history viewing module
├── config.py               # Constants, colors, and database credentials
├── schema.sql              # MySQL database structure and sample data
├── requirements.txt        # Required python packages
├── README.md               # This file
│
└── images/                 # Folder containing food images
    ├── burger.png
    ├── pizza.png
    ├── pasta.png
    ├── sandwich.png
    ├── fries.png
    ├── noodles.png
    ├── biryani.png         (placeholder)
    ├── coffee.png          (placeholder)
    ├── juice.png           (placeholder)
    └── cake.png            (placeholder)
```

## Features Complete

1. **Modular Codebase:** Code is split into logical files (`auth`, `menu`, `billing`, `history`, `db`).
2. **OOP Architecture:** Uses Python classes (`Database`, `LoginWindow`, `FoodApp`, `BillingSystem`, `OrderHistory`).
3. **Database Integration:** Uses `mysql-connector-python` to perform CRUD operations on 4 tables.
4. **Authentication:** User login and registration with SHA-256 password hashing. Admin role support.
5. **Modern UI:** Uses `tkinter.ttk` widgets, custom fonts, color schemes, and `Treeview` tables.
6. **Cart Management:** Add to cart (with quantity spinbox), remove item, clear cart, total calculation.
7. **Search Functionality:** Real-time food searching in the menu.
8. **Billing System:** Generates a formatted text receipt and saves the order to the database.
9. **Order History:** Users can view their past orders and the detailed line items.
10. **Error Handling:** `try-except` blocks around database operations, validations for empty inputs and quantities.

---

## Step-by-Step Run Instructions

1. **Install MySQL & Start Server:**
   Ensure MySQL (e.g., via XAMPP or MySQL Workbench) is installed and the service is running on your machine (default port 3306).

2. **Setup the Database:**
   - Open your MySQL CLI or Workbench.
   - Copy the contents of `schema.sql`.
   - Execute the SQL script. This will create the `food_ordering_db` database, tables, and insert sample food items and a default admin user.

3. **Configure Database Connection:**
   - Open `config.py`.
   - Update `DB_USER` and `DB_PASSWORD` if your local MySQL root user has a password. By default, it uses `root` with no password.

4. **Install Python Dependencies:**
   - Open your terminal or command prompt in the project folder.
   - Run the following command:
     ```bash
     pip install -r requirements.txt
     ```
     *(This installs `mysql-connector-python` and `Pillow` for images).*

5. **Run the Application:**
   - In the terminal, execute:
     ```bash
     python main.py
     ```
   - **Login Credentials:**
     - You can register a new user from the GUI.
     - Default Admin: Username `admin`, Password `admin123`

---

## Frequently Asked Questions (Viva Questions)

**Q1: What is the purpose of `__init__` in your classes?**
**Answer:** The `__init__` method is a constructor. It initializes the class attributes when an object is created. For example, in `LoginWindow`, it sets up the root window dimensions, colors, and the initial database connection.

**Q2: How does the application connect to the database?**
**Answer:** It uses the `mysql.connector` library. In `db.py`, the `Database` class establishes a connection using the `host`, `user`, `password`, and `database` name provided in `config.py`. It creates a `cursor` to execute SQL queries.

**Q3: Explain the use of `try...except` blocks in `db.py`.**
**Answer:** `try...except` blocks handle runtime errors gracefully. If the database server is down or a SQL syntax error occurs, the `except mysql.connector.Error` block catches the exception and prevents the application from crashing abruptly, often showing a messagebox to the user instead.

**Q4: What is a `Treeview` widget?**
**Answer:** `ttk.Treeview` is a Tkinter widget used to display data in a tabular format with rows and columns. In this project, it is used for the Shopping Cart and the Order History tables.

**Q5: How is data passed between different windows?**
**Answer:** Data is passed via constructor arguments. For example, when `LoginWindow` opens `FoodApp`, it passes the `user_info` dictionary and the active `Database` instance. When `FoodApp` opens `BillingSystem`, it passes the `cart_items` list, `total_amount`, and the `user_id`.

**Q6: What does `bind` do in Tkinter?**
**Answer:** The `.bind()` method ties an event to a function. For example, `self.tree_orders.bind("<<TreeviewSelect>>", self.on_order_select)` ensures that when a user clicks a row in the Order History table, the `on_order_select` method is automatically called to load that order's details.

**Q7: How is the password stored securely?**
**Answer:** The password is not stored in plain text. It is hashed using the `hashlib.sha256()` algorithm before saving it to the `users` table. During login, the entered password is hashed again and compared to the database hash.
