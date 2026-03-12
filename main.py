import tkinter as tk
from auth import LoginWindow # type: ignore

def main():
    """Entry point for the Online Food Ordering Application."""
    root = tk.Tk()
    
    # Hide the root window initially (optional, but good practice if Splash Screen is desired)
    # root.withdraw() 
    
    app = LoginWindow(root)
    root.mainloop()

if __name__ == "__main__":
    main()
