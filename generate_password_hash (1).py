"""
Password Hash Generator for FoodHub
This script helps create proper password hashes for test users
"""

from werkzeug.security import generate_password_hash

def generate_test_passwords():
    """Generate password hashes for test accounts"""
    
    print("="*60)
    print("FoodHub Password Hash Generator")
    print("="*60)
    
    # Common test passwords
    test_passwords = {
        "john_doe": "password",
        "admin": "password",
        "test_user": "test123"
    }
    
    print("\nGenerated Password Hashes for Test Accounts:\n")
    
    for username, password in test_passwords.items():
        hash_value = generate_password_hash(password)
        print(f"Username: {username}")
        print(f"Password: {password}")
        print(f"Hash: {hash_value}")
        print("-"*60)
    
    print("\n✅ Use these hashes to update the database tests.")
    print("\nSQL Command to update user passwords:")
    print("---")
    
    for username, password in test_passwords.items():
        hash_value = generate_password_hash(password)
        escaped_hash = hash_value.replace("'", "\\'")
        print(f"UPDATE users SET password='{hash_value}' WHERE username='{username}';")
    
    print("---\n")

def manual_password_hash():
    """Generate a hash for a custom password"""
    print("\n" + "="*60)
    print("Generate Hash for Custom Password")
    print("="*60)
    
    while True:
        password = input("\nEnter password (or 'quit' to exit): ").strip()
        if password.lower() == 'quit':
            break
        if not password:
            print("Please enter a valid password")
            continue
        
        hash_value = generate_password_hash(password)
        print(f"\nHash: {hash_value}")
        print(f"\nSQL: UPDATE users SET password='{hash_value}' WHERE username='YOUR_USERNAME';")

if __name__ == "__main__":
    generate_test_passwords()
    
    # Option to generate custom hashes
    choice = input("\nWould you like to generate a custom password hash? (y/n): ").strip().lower()
    if choice == 'y':
        manual_password_hash()
    
    print("\n✨ Done!")
