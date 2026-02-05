import os
import bcrypt
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
import getpass


load_dotenv()

DB_USER = os.getenv('DB_USER')
DB_PASS = os.getenv('DB_PASS')
DB_NAME = os.getenv('DB_NAME')
DB_HOST = os.getenv('DB_HOST')
DB_PORT = os.getenv('DB_PORT')

if not all([DB_USER, DB_PASS, DB_NAME, DB_HOST, DB_PORT]):
    print("Error: Database environment variables are not set.")
    print("Please check your .env file.")
    exit(1)

try:
    engine = create_engine(f'postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}')
except Exception as e:
    print(f"Error connecting to the database: {e}")
    exit(1)

def add_admin():

    print("--- Add New Admin User ---")
    username = input("Enter admin username: ").strip()
    if not username:
        print("Username cannot be empty.")
        return

    password = getpass.getpass("Enter admin password: ")
    if not password:
        print("Password cannot be empty.")
        return
        
    password_confirm = getpass.getpass("Confirm admin password: ")
    if password != password_confirm:
        print("Passwords do not match.")
        return

    
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    try:
        with engine.connect() as conn:
            res = conn.execute(text("SELECT id FROM users WHERE username = :username"), {"username": username}).fetchone()
            if res:
                print(f"User with username '{username}' already exists.")
                update = input("Do you want to update the password for this user? (y/n): ").lower()
                if update == 'y':
                    update_query = text("UPDATE users SET password = :password WHERE username = :username")
                    conn.execute(update_query, {"password": hashed_password, "username": username})
                    conn.commit()
                    print(f"Password for user '{username}' updated successfully!")
                else:
                    print("Operation cancelled.")
            else:
                
                insert_query = text("INSERT INTO users (username, password, name) VALUES (:username, :password, :name)")
                conn.execute(insert_query, {"username": username, "password": hashed_password, "name": "Admin"})
                conn.commit()
                print(f"Admin user '{username}' created successfully!")

    except Exception as e:
        print(f"\nAn error occurred: {e}")

