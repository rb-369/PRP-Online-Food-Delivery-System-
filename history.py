import tkinter as tk
from tkinter import ttk, messagebox
import config
from db import Database

class OrderHistory:
    def __init__(self, parent, user_id, db: Database):
        self.top = tk.Toplevel(parent)
        self.top.title("Order History")
        
        # Geometry
        self.top.geometry("800x600+100+100")
        self.top.configure(bg=config.BG_COLOR)
        self.top.grab_set() # Modal window
        self.top.focus_set()
        
        self.user_id = user_id
        self.db = db
        
        self.create_ui()
        self.load_orders()

    def create_ui(self):
        # Header Frame
        header_frame = tk.Frame(self.top, bg=config.PRIMARY_COLOR, height=60, pady=10)
        header_frame.pack(fill=tk.X)
        header_frame.pack_propagate(False)
        
        lbl_title = tk.Label(header_frame, text="Your Order History", bg=config.PRIMARY_COLOR, fg=config.WHITE, font=config.FONT_HEADING)
        lbl_title.pack(anchor=tk.CENTER)
        
        # Main Split Frame
        main_frame = tk.Frame(self.top, bg=config.BG_COLOR, padx=20, pady=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Left Panel (Orders List)
        left_frame = tk.LabelFrame(main_frame, text="All Orders", font=config.FONT_SUBHEADING, bg=config.BG_COLOR)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        
        columns_orders = ("OrderID", "Date", "Total")
        self.tree_orders = ttk.Treeview(left_frame, columns=columns_orders, show="headings", height=15)
        self.tree_orders.heading("OrderID", text="Order #")
        self.tree_orders.heading("Date", text="Date & Time")
        self.tree_orders.heading("Total", text="Total (₹)")
        
        self.tree_orders.column("OrderID", width=80, anchor=tk.CENTER)
        self.tree_orders.column("Date", width=180, anchor=tk.W)
        self.tree_orders.column("Total", width=100, anchor=tk.E)
        
        self.tree_orders.pack(fill=tk.BOTH, expand=True, pady=10, padx=10)
        
        # Bind row click event
        self.tree_orders.bind("<<TreeviewSelect>>", self.on_order_select)
        
        # Scrollbar for Orders List
        scrollbar_ord = ttk.Scrollbar(left_frame, orient=tk.VERTICAL, command=self.tree_orders.yview)
        self.tree_orders.configure(yscrollcommand=scrollbar_ord.set)
        scrollbar_ord.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Right Panel (Order Details)
        right_frame = tk.LabelFrame(main_frame, text="Order Details", font=config.FONT_SUBHEADING, bg=config.BG_COLOR)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(10, 0))
        
        columns_details = ("Item", "Qty", "Price", "Subtotal")
        self.tree_details = ttk.Treeview(right_frame, columns=columns_details, show="headings", height=15)
        self.tree_details.heading("Item", text="Item Name")
        self.tree_details.heading("Qty", text="Quantity")
        self.tree_details.heading("Price", text="Price")
        self.tree_details.heading("Subtotal", text="Subtotal")
        
        self.tree_details.column("Item", width=150, anchor=tk.W)
        self.tree_details.column("Qty", width=60, anchor=tk.CENTER)
        self.tree_details.column("Price", width=80, anchor=tk.E)
        self.tree_details.column("Subtotal", width=80, anchor=tk.E)
        
        self.tree_details.pack(fill=tk.BOTH, expand=True, pady=10, padx=10)

        # Scrollbar for Details
        scrollbar_det = ttk.Scrollbar(right_frame, orient=tk.VERTICAL, command=self.tree_details.yview)
        self.tree_details.configure(yscrollcommand=scrollbar_det.set)
        scrollbar_det.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Close Button
        btn_close = tk.Button(self.top, text="Close", font=config.FONT_BTN, bg=config.SECONDARY_COLOR, 
                              fg=config.WHITE, command=self.top.destroy, cursor="hand2")
        btn_close.pack(pady=(0, 20), ipadx=20, ipady=5)

    def load_orders(self):
        """Fetch all orders from DB for the user."""
        query = "SELECT id, DATE_FORMAT(order_date, '%Y-%m-%d %H:%i:%s') as fdate, total_amount FROM orders WHERE user_id = %s ORDER BY order_date DESC"
        orders = self.db.fetch_all(query, (self.user_id,))
        
        for row in self.tree_orders.get_children():
            self.tree_orders.delete(row)
            
        if not orders:
            # Insert a dummy row to indicate no orders
            self.tree_orders.insert("", tk.END, values=("-", "No previous orders found", "₹0.00"))
            return
            
        for order in orders:
            # Note: Fetching using dict keys as fetch_all uses dictionary=True cursor
            self.tree_orders.insert("", tk.END, values=(order['id'], order['fdate'], f"₹{order['total_amount']}"))

    def on_order_select(self, event):
        """Fetch item details when an order is clicked."""
        selected_item = self.tree_orders.selection()
        if not selected_item:
            return
            
        item_values = self.tree_orders.item(selected_item[0], "values")
        order_id = item_values[0]
        
        if order_id == "-": # Handle the 'no orders found' dummy row click
            return
            
        for row in self.tree_details.get_children():
            self.tree_details.delete(row)
            
        query = """
            SELECT f.name, oi.quantity, f.price, oi.subtotal 
            FROM order_items oi
            JOIN food_items f ON oi.food_item_id = f.id
            WHERE oi.order_id = %s
        """
        
        details = self.db.fetch_all(query, (order_id,))
        for det in details:
            self.tree_details.insert("", tk.END, values=(det['name'], det['quantity'], f"₹{det['price']}", f"₹{det['subtotal']}"))

if __name__ == "__main__":
    pass  # Only to be called from main app
