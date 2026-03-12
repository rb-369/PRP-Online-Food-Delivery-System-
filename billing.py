import tkinter as tk
from tkinter import ttk, messagebox
import config
from db import Database
from datetime import datetime

class BillingSystem:
    def __init__(self, parent, cart_items, total_amount, user_id, db: Database, on_success_callback):
        self.top = tk.Toplevel(parent)
        self.top.title("Bill Receipt")
        
        # Geometry
        self.top.geometry("500x700+300+100")
        self.top.configure(bg=config.WHITE)
        self.top.grab_set() # Modal window
        self.top.focus_set()
        
        self.cart_items = cart_items
        self.total_amount = total_amount
        self.user_id = user_id
        self.db = db
        self.on_success_callback = on_success_callback
        self.order_id = None
        
        self.create_receipt_ui()
        self.save_order_to_db()

    def create_receipt_ui(self):
        # Header Frame
        header_frame = tk.Frame(self.top, bg=config.WHITE, pady=20)
        header_frame.pack(fill=tk.X)
        
        lbl_title = tk.Label(header_frame, text=config.APP_TITLE, font=("Courier", 18, "bold"), bg=config.WHITE, fg=config.TEXT_COLOR)
        lbl_title.pack()
        
        lbl_subtitle = tk.Label(header_frame, text="123 Food Street, Tech City\nPhone: +91 9876543210", font=("Courier", 10), bg=config.WHITE, fg=config.TEXT_COLOR)
        lbl_subtitle.pack()
        
        # Receipt Text Area
        self.txt_receipt = tk.Text(self.top, font=("Courier", 10), bg=config.WHITE, fg=config.TEXT_COLOR, relief=tk.FLAT, padx=20, pady=10)
        self.txt_receipt.pack(fill=tk.BOTH, expand=True)
        self.txt_receipt.config(state=tk.DISABLED)
        
        # Buttons Frame
        btn_frame = tk.Frame(self.top, bg=config.WHITE, pady=10)
        btn_frame.pack(fill=tk.X, side=tk.BOTTOM)
        
        btn_print = tk.Button(btn_frame, text="Print Receipt", font=config.FONT_BTN, bg=config.PRIMARY_COLOR, 
                              fg=config.WHITE, command=self.print_receipt, cursor="hand2")
        btn_print.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=10, ipady=5)
        
        btn_close = tk.Button(btn_frame, text="Close", font=config.FONT_BTN, bg=config.DANGER_COLOR, 
                              fg=config.WHITE, command=self.close_window, cursor="hand2")
        btn_close.pack(side=tk.RIGHT, expand=True, fill=tk.X, padx=10, ipady=5)

    def save_order_to_db(self):
        """Save the order header and details to the database."""
        try:
            # Insert Order Header
            order_query = "INSERT INTO orders (user_id, total_amount) VALUES (%s, %s)"
            self.order_id = self.db.execute_query(order_query, (self.user_id, self.total_amount))
            
            if not self.order_id:
                messagebox.showerror("Error", "Failed to save order header.")
                return

            # Insert Order Items
            item_query = "INSERT INTO order_items (order_id, food_item_id, quantity, subtotal) VALUES (%s, %s, %s, %s)"
            for item in self.cart_items:
                # cart_items structure: (id, name, qty, price, subtotal)
                self.db.execute_query(item_query, (self.order_id, item[0], item[2], item[4]))

            # Order saved successfully, update the receipt text
            self.generate_receipt_text()
            
            # Call success callback to clear the main cart
            if self.on_success_callback:
                self.on_success_callback()

        except Exception as e:
            messagebox.showerror("Database Error", f"An error occurred while saving the order.\n{str(e)}")

    def generate_receipt_text(self):
        """Populate the text widget with receipt details."""
        self.txt_receipt.config(state=tk.NORMAL)
        self.txt_receipt.delete('1.0', tk.END)
        
        now = datetime.now()
        dt_string = now.strftime("%Y-%m-%d %H:%M:%S")
        
        receipt_content = f"""
{'='*48}
Receipt No: {self.order_id if self.order_id else 'N/A'}
Date: {dt_string}
{'='*48}
Item Name              Qty    Price   Subtotal
{'-'*48}
"""
        for item in self.cart_items:
            name = item[1][:20].ljust(22)
            qty = str(item[2]).rjust(3)
            price = f"{item[3]:.2f}".rjust(8)
            subtotal = f"{item[4]:.2f}".rjust(10)
            receipt_content += f"{name} {qty} {price} {subtotal}\n"
            
        receipt_content += f"""
{'-'*48}
Total Amount:                      ₹{self.total_amount:10.2f}
{'='*48}
          Thank you for ordering!
          Visit Again!
"""
        self.txt_receipt.insert(tk.END, receipt_content)
        self.txt_receipt.config(state=tk.DISABLED)

    def print_receipt(self):
        """Mock print function."""
        messagebox.showinfo("Print", "Receipt sent to printer successfully!")

    def close_window(self):
        self.top.destroy()
