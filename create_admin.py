import sqlite3
from pathlib import Path
from getpass import getpass
from werkzeug.security import generate_password_hash

DATABASE = Path(__file__).resolve().parent / "database.db"

username = input("Enter admin username: ").strip()
password = getpass("Enter admin password: ")
name = input("Enter admin name: ").strip()

if not username or not password or not name:
    print("All fields are required.")
else:
    conn = sqlite3.connect(str(DATABASE))
    try:
        conn.execute("""
            INSERT INTO users (name, username, password_hash, role)
            VALUES (?, ?, ?, 'admin')
        """, (name, username, generate_password_hash(password)))
        conn.commit()
        print("Admin account created successfully!")
    except sqlite3.IntegrityError:
        print("That username already exists. Choose another.")
    finally:
        conn.close()