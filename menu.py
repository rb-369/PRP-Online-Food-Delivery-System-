import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk # type: ignore
import os
import typing
import config # type: ignore
from db import Database # type: ignore
from billing import BillingSystem # type: ignore
from history import OrderHistory # type: ignore

class FoodApp:
    def __init__(self, root, user_info, db: Database):
        self.root = root
        self.root.title(config.APP_TITLE)
        self.root.geometry(config.APP_GEOMETRY)
        self.root.configure(bg=config.BG_COLOR)
        self.root.state('zoomed') # Maximize output

        self.user_info = user_info
        self.db = db
        
        # Type placeholders to satisfy strict type checkers
        self.search_var: typing.Any = None
        self.main_content: typing.Any = None
        self.left_panel: typing.Any = None
        self.menu_canvas: typing.Any = None
        self.menu_scrollbar: typing.Any = None
        self.menu_frame: typing.Any = None
        self.frame_id: typing.Any = None
        self.right_panel: typing.Any = None
        self.cart_tree: typing.Any = None
        self.lbl_total: typing.Any = None
        
        # key: food_item_id, value: {'name': name, 'qty': qty, 'price': price}
        self.cart_items: typing.Dict[int, typing.Any] = {} 
        
        # Load Images Dictionary
        self.images: typing.Dict[int, typing.Any] = {}
        
        self.create_header()
        self.create_main_layout()
        self.load_food_items()

    def create_header(self):
        """Creates a premium top header bar."""
        header_frame = tk.Frame(self.root, bg=config.PRIMARY_COLOR, pady=20)
        header_frame.pack(fill=tk.X, side=tk.TOP)
        
        # Project Logo/Title with better font
        lbl_title = tk.Label(header_frame, text=config.APP_TITLE.upper(), bg=config.PRIMARY_COLOR, 
                             fg=config.WHITE, font=(config.FONT_FAMILY, 20, "bold"))
        lbl_title.pack(side=tk.LEFT, padx=40)
        
        # User Welcome with role badge
        user_role = f" [{self.user_info['role'].upper()}]" if self.user_info['role'] == 'admin' else ""
        lbl_user = tk.Label(header_frame, text=f"Welcome, {self.user_info['username']}{user_role}", 
                            bg=config.PRIMARY_COLOR, fg="#B0BEC5", font=config.FONT_NORMAL)
        lbl_user.pack(side=tk.RIGHT, padx=(10, 40))

        # Logout Button - Styled
        btn_logout = tk.Button(header_frame, text="LOGOUT", font=config.FONT_BTN, bg=config.DANGER_COLOR, 
                               fg=config.WHITE, cursor="hand2", command=self.logout, 
                               relief=tk.FLAT, padx=15, pady=5)
        btn_logout.pack(side=tk.RIGHT, padx=10)

        # Search Bar with minimal design
        search_frame = tk.Frame(header_frame, bg=config.PRIMARY_COLOR)
        search_frame.pack(side=tk.RIGHT, padx=30)
        
        tk.Label(search_frame, text="Search:", bg=config.PRIMARY_COLOR, fg=config.WHITE, 
                 font=config.FONT_NORMAL).pack(side=tk.LEFT, padx=5)
        self.search_var = tk.StringVar()
        self.search_var.trace('w', self.on_search)
        search_entry = tk.Entry(search_frame, textvariable=self.search_var, font=config.FONT_NORMAL, 
                                width=25, bg="#3949AB", fg=config.WHITE, insertbackground=config.WHITE, bd=0)
        search_entry.pack(side=tk.LEFT, ipady=8, padx=5)

    def create_main_layout(self):
        """Creates the split view: Menu on Left, Cart on Right."""
        self.main_content = tk.Frame(self.root, bg=config.BG_COLOR, padx=20, pady=20)
        self.main_content.pack(fill=tk.BOTH, expand=True)
        
        # Left Panel - Food Menu
        self.left_panel = tk.Frame(self.main_content, bg=config.BG_COLOR)
        self.left_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        
        tk.Label(self.left_panel, text="Food Menu", font=config.FONT_HEADING, bg=config.BG_COLOR, fg=config.TEXT_COLOR).pack(anchor=tk.W, pady=(0, 10))
        
        # Canvas for scrollable menu items
        self.menu_canvas = tk.Canvas(self.left_panel, bg=config.WHITE, highlightthickness=0)
        self.menu_scrollbar = ttk.Scrollbar(self.left_panel, orient="vertical", command=self.menu_canvas.yview)
        
        self.menu_frame = tk.Frame(self.menu_canvas, bg=config.WHITE)
        self.menu_frame.bind(
            "<Configure>",
            lambda e: self.menu_canvas.configure(
                scrollregion=self.menu_canvas.bbox("all")
            )
        )
        
        self.frame_id = self.menu_canvas.create_window((0, 0), window=self.menu_frame, anchor="nw")
        
        self.menu_canvas.bind(
            "<Configure>",
            lambda e: self.menu_canvas.itemconfig(self.frame_id, width=e.width)
        )
        self.menu_canvas.configure(yscrollcommand=self.menu_scrollbar.set)
        
        self.menu_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.menu_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Right Panel - Shopping Cart & Billing
        self.right_panel = tk.Frame(self.main_content, bg=config.WHITE, width=400, relief=tk.RAISED, borderwidth=1)
        self.right_panel.pack(side=tk.RIGHT, fill=tk.Y, padx=(10, 0))
        self.right_panel.pack_propagate(False) # Prevent shrinking
        
        tk.Label(self.right_panel, text="Shopping Cart", font=config.FONT_HEADING, bg=config.WHITE, fg=config.TEXT_COLOR).pack(pady=10)
        
        # Cart Table (Treeview)
        columns = ("ID", "Item", "Qty", "Price", "Subtotal")
        self.cart_tree = ttk.Treeview(self.right_panel, columns=columns, show="headings", height=15)
        self.cart_tree.heading("ID", text="ID")
        self.cart_tree.heading("Item", text="Item Name")
        self.cart_tree.heading("Qty", text="Qty")
        self.cart_tree.heading("Price", text="Price")
        self.cart_tree.heading("Subtotal", text="Total")
        
        self.cart_tree.column("ID", width=0, stretch=tk.NO) # Hide ID column
        self.cart_tree.column("Item", width=120, anchor=tk.W)
        self.cart_tree.column("Qty", width=50, anchor=tk.CENTER)
        self.cart_tree.column("Price", width=70, anchor=tk.E)
        self.cart_tree.column("Subtotal", width=80, anchor=tk.E)
        
        self.cart_tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        cart_scroll = ttk.Scrollbar(self.cart_tree, orient="vertical", command=self.cart_tree.yview)
        self.cart_tree.configure(yscrollcommand=cart_scroll.set)
        cart_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        # Cart Controls (Update quantity, remove)
        cart_ctrl_frame = tk.Frame(self.right_panel, bg=config.WHITE)
        cart_ctrl_frame.pack(fill=tk.X, padx=10, pady=5)
        
        btn_remove = tk.Button(cart_ctrl_frame, text="Remove Selected", font=config.FONT_BTN, bg=config.DANGER_COLOR, 
                               fg=config.WHITE, cursor="hand2", command=self.remove_from_cart)
        btn_remove.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2)
        
        btn_clear = tk.Button(cart_ctrl_frame, text="Clear Cart", font=config.FONT_BTN, bg=config.SECONDARY_COLOR, 
                              fg=config.WHITE, cursor="hand2", command=self.clear_cart)
        btn_clear.pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=2)

        # Cart Total & Buttons
        cart_btm_frame = tk.Frame(self.right_panel, bg=config.WHITE, padx=20, pady=20)
        cart_btm_frame.pack(fill=tk.X, side=tk.BOTTOM)

        self.lbl_total = tk.Label(cart_btm_frame, text="TOTAL: ₹0.00", font=config.FONT_PRICE, 
                                  bg=config.WHITE, fg=config.TEXT_MAIN)
        self.lbl_total.pack(pady=(0, 20))

        btn_bill = tk.Button(cart_btm_frame, text="GENERATE BILL", font=config.FONT_SUBHEADING, 
                             bg=config.SUCCESS_COLOR, fg=config.WHITE, cursor="hand2", 
                             command=self.generate_bill, pady=12, relief=tk.FLAT, bd=0)
        btn_bill.pack(fill=tk.X, pady=5)
        
        btn_history = tk.Button(cart_btm_frame, text="ORDER HISTORY", font=config.FONT_BTN, 
                                bg=config.PRIMARY_COLOR, fg=config.WHITE, cursor="hand2", 
                                command=self.show_history, pady=8, relief=tk.FLAT, bd=0)
        btn_history.pack(fill=tk.X, pady=5)

    def load_food_items(self, search_query=""):
        """Fetches food items from DB and renders them in the menu frame."""
        # Clear existing items
        for widget in self.menu_frame.winfo_children():
            widget.destroy()
            
        # Fetch items from database
        query = "SELECT id, name, category, price, image_path FROM food_items WHERE name LIKE %s"
        params = (f"%{search_query}%",)
        foods = self.db.fetch_all(query, params)
        
        if not foods:
            no_items_lbl = tk.Label(self.menu_frame, text="No items found. Please adjust your search.", 
                                    bg=config.WHITE, font=config.FONT_NORMAL, fg=config.TEXT_SECONDARY)
            no_items_lbl.pack(pady=40, fill=tk.X)
            return

        # Grid configuration
        cols = int(config.GRID_COLS)
        
        for i, food in enumerate(foods):
            current_row, current_col = divmod(i, cols)
            food_id = food['id']
            name = food['name']
            price = food['price']
            category = food['category']
            img_path = food['image_path']

            # --- CARD CONTAINER ---
            # Increase card width and spacing for a more open, premium feel
            card_outer = tk.Frame(self.menu_frame, bg=config.BORDER_COLOR, bd=1)
            card_outer.grid(row=current_row, column=current_col, padx=25, pady=25, sticky="nsew")
            
            card = tk.Frame(card_outer, bg=config.CARD_BG, padx=25, pady=25)
            card.pack(fill=tk.BOTH, expand=True)

            # --- IMAGE ---
            img_container = tk.Frame(card, bg=config.CARD_BG, width=config.IMG_SIZE[0], height=config.IMG_SIZE[1])
            img_container.pack_propagate(False)
            img_container.pack(pady=(0, 15))
            
            img_label = tk.Label(img_container, bg=config.BG_COLOR)
            try:
                if os.path.exists(img_path):
                    img = Image.open(img_path)
                    img = img.resize(config.IMG_SIZE, Image.LANCZOS)
                    photo = ImageTk.PhotoImage(img)
                    self.images[food_id] = photo 
                    img_label.config(image=photo)
                else:
                    img_label.config(text="No Image", font=config.FONT_NORMAL, fg=config.TEXT_SECONDARY)
            except Exception as e:
                img_label.config(text="Image Error")
            img_label.pack(fill=tk.BOTH, expand=True)

            # --- DETAILS ---
            tk.Label(card, text=name, font=config.FONT_SUBHEADING, bg=config.CARD_BG, 
                     fg=config.TEXT_MAIN, anchor=tk.W).pack(fill=tk.X)
            tk.Label(card, text=category.upper(), font=(config.FONT_FAMILY, 9, "bold"), 
                     bg=config.CARD_BG, fg=config.TEXT_SECONDARY, anchor=tk.W).pack(fill=tk.X, pady=(2, 5))
            
            price_label = tk.Label(card, text=f"₹{price:.2f}", font=config.FONT_PRICE, 
                                   bg=config.CARD_BG, fg=config.SECONDARY_COLOR, anchor=tk.W)
            price_label.pack(fill=tk.X, pady=(5, 15))

            # --- ACTION BAR ---
            action_frame = tk.Frame(card, bg=config.CARD_BG)
            action_frame.pack(fill=tk.X)
            
            qty_frame = tk.Frame(action_frame, bg=config.CARD_BG)
            qty_frame.pack(side=tk.LEFT)
            
            tk.Label(qty_frame, text="QTY:", bg=config.CARD_BG, font=(config.FONT_FAMILY, 9), 
                     fg=config.TEXT_SECONDARY).pack(side=tk.LEFT)
            
            # Using a StringVar for the spinbox to handle validation easily
            qty_var = tk.StringVar(value="1")
            qty_spin = ttk.Spinbox(qty_frame, from_=1, to=20, textvariable=qty_var, width=3, font=config.FONT_NORMAL)
            qty_spin.pack(side=tk.LEFT, padx=8)
            
            def create_add_cmd(f_id=food_id, f_name=name, f_price=price, q_v=qty_var):
                return lambda: self.add_to_cart(f_id, f_name, f_price, q_v)

            btn_add = tk.Button(action_frame, text="ADD TO CART", font=config.FONT_BTN, 
                                bg=config.ACCENT_COLOR, fg=config.WHITE, cursor="hand2", 
                                relief=tk.FLAT, bd=0, padx=20, pady=8,
                                command=create_add_cmd())
            btn_add.pack(side=tk.RIGHT)

        # Configure columns to distribute equally
        for i in range(cols):
            self.menu_frame.grid_columnconfigure(i, weight=1)

    def on_search(self, *args):
        """Callback for search entry typing."""
        query = self.search_var.get().strip()
        self.load_food_items(query)

    def add_to_cart(self, food_id, name, price, qty_var):
        """Adds an item to the shopping cart."""
        print(f"DEBUG: add_to_cart called for {name} (ID: {food_id})")
        try:
            qty_val = qty_var.get()
            print(f"DEBUG: qty_var value is '{qty_val}'")
            qty = int(qty_val)
            if qty <= 0:
                raise ValueError
        except (ValueError, tk.TclError) as e:
            print(f"DEBUG: Validation error: {e}")
            messagebox.showwarning("Invalid Quantity", "Please enter a valid quantity greater than 0.")
            return

        if food_id in self.cart_items:
            # Update quantity if item already in cart
            current_qty = int(self.cart_items[food_id]['qty'])
            self.cart_items[food_id]['qty'] = current_qty + qty
            print(f"DEBUG: Updated {name} quantity in cart to {self.cart_items[food_id]['qty']}")
        else:
            # Add new item
            self.cart_items[food_id] = {
                'name': name,
                'price': float(price),
                'qty': qty
            }
            print(f"DEBUG: Added {name} to cart as new item")
            
        self.update_cart_ui()
        # messagebox.showinfo("Cart Update", f"Added {qty} x {name} to cart.")

    def update_cart_ui(self):
        """Refreshes the cart treeview and total amount."""
        # Clear current treeview items
        for row in self.cart_tree.get_children():
            self.cart_tree.delete(row)
            
        total_amount = 0.0
        
        for f_id, details in self.cart_items.items():
            # Ensure price and qty are treated correctly to avoid Decimal vs float errors
            try:
                price = float(details['price'])
                qty = int(details['qty'])
                subtotal = float(qty * price)
            except (TypeError, ValueError):
                subtotal = 0.0
                
            total_amount += subtotal
            
            # ID, Item Name, Qty, Price, Subtotal
            self.cart_tree.insert("", tk.END, values=(f_id, details['name'], details['qty'], f"₹{price:.2f}", f"₹{subtotal:.2f}"))
            
        self.lbl_total.config(text=f"TOTAL: ₹{total_amount:.2f}")

    def remove_from_cart(self):
        """Removes the selected item(s) from the cart."""
        selected_items = self.cart_tree.selection()
        if not selected_items:
            messagebox.showwarning("No Selection", "Please select an item from the cart to remove.")
            return
            
        for item in selected_items:
            item_values = self.cart_tree.item(item, "values")
            food_id = int(item_values[0])
            if food_id in self.cart_items:
                self.cart_items.pop(food_id, None)
                
        self.update_cart_ui()

    def clear_cart(self):
        """Empties the cart."""
        if not self.cart_items: return
        
        if messagebox.askyesno("Clear Cart", "Are you sure you want to clear the entire cart?"):
            self.cart_items.clear()
            self.update_cart_ui()

    def generate_bill(self):
        """Initiates the billing process."""
        if not self.cart_items:
            messagebox.showwarning("Empty Cart", "Cannot generate bill for an empty cart. Please add items first.")
            return

        # Prepare cart data for billing: list of tuples (id, name, qty, price, subtotal)
        cart_data = []
        total_amount = 0.0
        for f_id, details in self.cart_items.items():
            try:
                price = float(details['price'])
                qty = int(details['qty'])
                subtotal = float(qty * price)
            except (TypeError, ValueError):
                subtotal = 0.0
                
            total_amount += subtotal
            cart_data.append((f_id, details['name'], qty, price, subtotal))

        # Open Billing Window
        BillingSystem(self.root, cart_data, total_amount, self.user_info['id'], self.db, self.on_bill_success)

    def on_bill_success(self):
        """Callback to clear cart after successful bill generation."""
        self.cart_items.clear()
        self.update_cart_ui()
        messagebox.showinfo("Success", "Order saved and bill generated successfully!")

    def show_history(self):
        """Opens the order history window."""
        OrderHistory(self.root, self.user_info['id'], self.db)

    def logout(self):
        """Logs out user and closes main app."""
        if messagebox.askyesno("Logout", "Are you sure you want to log out?"):
            self.root.quit() # Stop mainloop, control returns to auth.py

if __name__ == "__main__":
    pass # Managed by auth.py
