"""
Configuration and Constants for Flask Application
"""

# SQLite database configuration
DB_PATH = "food_ordering.db"
DB_NAME = DB_PATH  # Backward-compatible alias used by legacy scripts

# Flask Configuration
DEBUG = True
SECRET_KEY = "your-secret-key-change-in-production"

# Application Settings
APP_TITLE = "FoodHub - Online Food Delivery"
APP_VERSION = "1.0.0"

# UI Colors (Ultra-Premium Modern Theme)
BG_COLOR = "#F0F2F5"          # Soft light gray (Facebook-style)
PRIMARY_COLOR = "#1A237E"     # Indigo 900 (Deep, Professional)
SECONDARY_COLOR = "#FF6F00"   # Amber 900 (Deep Orange)
ACCENT_COLOR = "#00C853"      # Green A700 (Vibrant Success)
TEXT_MAIN = "#212121"         # Gray 900
TEXT_COLOR = TEXT_MAIN        # Legacy Alias
TEXT_SECONDARY = "#757575"    # Gray 600
WHITE = "#FFFFFF"             
DANGER_COLOR = "#D50000"      # Red A700
SUCCESS_COLOR = "#00C853"
CARD_BG = "#FFFFFF"
BORDER_COLOR = "#E0E0E0"

# Pagination
ITEMS_PER_PAGE = 12

# Tax and Fees
TAX_RATE = 0.10  # 10%
DELIVERY_FEE = 2.00
