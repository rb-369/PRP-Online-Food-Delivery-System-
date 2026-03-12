import config
from db import Database

try:
    db = Database()
    count = db.fetch_one("SELECT COUNT(*) as total FROM food_items")
    print(f"Total food items in database: {count['total']}")
except Exception as e:
    print(f"Error checking database: {e}")
