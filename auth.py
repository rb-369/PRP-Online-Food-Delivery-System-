import tkinter as tk
from tkinter import ttk, messagebox
import hashlib
from db import Database
import config
from menu import FoodApp

def hash_password(password):
    """Hashes a password using SHA-256."""
    return hashlib.sha256(password.encode()).hexdigest()

class LoginWindow:
    def __init__(self, root):
        self.root = root
        self.root.title("Login - " + config.APP_TITLE)
        
        # Center the window
        window_width = 400
        window_height = 500
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = (screen_width / 2) - (window_width / 2)
        y = (screen_height / 2) - (window_height / 2)
        self.root.geometry(f'{window_width}x{window_height}+{int(x)}+{int(y)}')
        
        self.root.configure(bg=config.BG_COLOR)
        self.root.resizable(False, False)

        # Database connection
        self.db = Database()

        self.create_ui()

    def create_ui(self):
        """Creates the login and registration UI components."""
        # Main Frame
        main_frame = tk.Frame(self.root, bg=config.WHITE, padx=30, pady=30)
        main_frame.place(relx=0.5, rely=0.5, anchor=tk.CENTER, width=340, height=440)

        # Title
        title_lbl = tk.Label(main_frame, text="Welcome Back", font=config.FONT_HEADING, bg=config.WHITE, fg=config.PRIMARY_COLOR)
        title_lbl.pack(pady=(0, 20))

        # Username
        tk.Label(main_frame, text="Username", font=config.FONT_NORMAL, bg=config.WHITE, fg=config.TEXT_COLOR).pack(anchor=tk.W)
        self.username_var = tk.StringVar()
        self.username_entry = ttk.Entry(main_frame, textvariable=self.username_var, font=config.FONT_NORMAL)
        self.username_entry.pack(fill=tk.X, pady=(0, 15), ipady=5)

        # Password
        tk.Label(main_frame, text="Password", font=config.FONT_NORMAL, bg=config.WHITE, fg=config.TEXT_COLOR).pack(anchor=tk.W)
        self.password_var = tk.StringVar()
        self.password_entry = ttk.Entry(main_frame, textvariable=self.password_var, font=config.FONT_NORMAL, show="*")
        self.password_entry.pack(fill=tk.X, pady=(0, 25), ipady=5)

        # Buttons Frame
        btn_frame = tk.Frame(main_frame, bg=config.WHITE)
        btn_frame.pack(fill=tk.X)

        # Style for buttons
        style = ttk.Style()
        style.configure('Primary.TButton', font=config.FONT_BTN, background=config.PRIMARY_COLOR)
        
        login_btn = tk.Button(btn_frame, text="Login", font=config.FONT_BTN, bg=config.PRIMARY_COLOR, fg=config.WHITE, 
                              command=self.login, cursor="hand2", relief=tk.FLAT)
        login_btn.pack(fill=tk.X, pady=5, ipady=8)

        register_btn = tk.Button(btn_frame, text="Create New Account", font=config.FONT_BTN, bg=config.SECONDARY_COLOR, 
                                 fg=config.WHITE, command=self.register, cursor="hand2", relief=tk.FLAT)
        register_btn.pack(fill=tk.X, pady=5, ipady=8)

    def login(self):
        """Handles user login."""
        username = self.username_var.get().strip()
        password = self.password_var.get().strip()

        if not username or not password:
            messagebox.showwarning("Validation Error", "Please enter both username and password.")
            return

        hashed_pwd = hash_password(password)
        
        query = "SELECT id, username, role FROM users WHERE username = %s AND password = %s"
        user = self.db.fetch_one(query, (username, hashed_pwd))

        if user:
            messagebox.showinfo("Login Success", f"Welcome back, {user['username']}!")
            self.root.destroy()  # Close login window
            self.open_main_app(user)
        else:
            messagebox.showerror("Login Failed", "Invalid username or password.")

    def register(self):
        """Handles new user registration."""
        username = self.username_var.get().strip()
        password = self.password_var.get().strip()

        if not username or not password:
            messagebox.showwarning("Validation Error", "Please enter a username and password to register.")
            return
            
        if len(password) < 6:
            messagebox.showwarning("Validation Error", "Password must be at least 6 characters long.")
            return

        # Check if user already exists
        check_query = "SELECT id FROM users WHERE username = %s"
        if self.db.fetch_one(check_query, (username,)):
            messagebox.showerror("Registration Failed", "Username already exists. Please choose another.")
            return

        hashed_pwd = hash_password(password)
        insert_query = "INSERT INTO users (username, password, role) VALUES (%s, %s, 'user')"
        user_id = self.db.execute_query(insert_query, (username, hashed_pwd))

        if user_id:
            messagebox.showinfo("Registration Success", "Account created successfully! You can now log in.")
            self.password_var.set("") # Clear password field
        else:
            messagebox.showerror("Database Error", "Failed to register user. Please try again.")

    def open_main_app(self, user_info):
        """Launches the main food ordering application."""
        main_root = tk.Tk()
        app = FoodApp(main_root, user_info, self.db)
        main_root.protocol("WM_DELETE_WINDOW", lambda: self.on_main_app_close(main_root))
        main_root.mainloop()
        
    def on_main_app_close(self, main_root):
        """Clean up when main app is closed."""
        self.db.close()
        main_root.destroy()

if __name__ == "__main__":
    # Test just the login window independently
    root = tk.Tk()
    app = LoginWindow(root)
    root.mainloop()
