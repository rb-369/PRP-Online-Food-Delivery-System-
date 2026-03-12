import config
from db import Database
import os

def import_sql():
    db = Database()
    sql_file = "schema.sql"
    
    if not os.path.exists(sql_file):
        print(f"Error: {sql_file} not found.")
        return

    print(f"Importing {sql_file}...")
    
    with open(sql_file, 'r') as f:
        # Better splitting for SQL files: handle comments and multiline
        content = f.read()
        # Remove comments
        import re
        content = re.sub(r'--.*', '', content)
        # Split by semicolon
        commands = content.split(';')
        
    for command in commands:
        command = command.strip()
        if command:
            try:
                db.cursor.execute(command)
                db.connection.commit()
            except Exception as e:
                print(f"Error in command: {command[:50]}...\n{e}")
                
    print("Import complete.")
    
    count = db.fetch_one("SELECT COUNT(*) as total FROM food_items")
    print(f"Total food items now: {count['total']}")

if __name__ == "__main__":
    import_sql()
