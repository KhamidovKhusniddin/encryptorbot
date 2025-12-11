import sqlite3
import datetime
import os

DB_NAME = "users.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            first_name TEXT,
            last_name TEXT,
            joined_at TIMESTAMP,
            last_active TIMESTAMP,
            files_encrypted INTEGER DEFAULT 0,
            files_decrypted INTEGER DEFAULT 0
        )
    ''')
    conn.commit()
    conn.close()

def add_user(user_id, username, first_name, last_name):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # Check if exists
    cursor.execute("SELECT user_id FROM users WHERE user_id = ?", (user_id,))
    if cursor.fetchone() is None:
        now = datetime.datetime.now()
        cursor.execute('''
            INSERT INTO users (user_id, username, first_name, last_name, joined_at, last_active)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (user_id, username, first_name, last_name, now, now))
        conn.commit()
    else:
        update_activity(user_id)
        
    conn.close()

def update_activity(user_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    now = datetime.datetime.now()
    cursor.execute("UPDATE users SET last_active = ? WHERE user_id = ?", (now, user_id))
    conn.commit()
    conn.close()

def increment_stats(user_id, type="encrypt"):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    if type == "encrypt":
        cursor.execute("UPDATE users SET files_encrypted = files_encrypted + 1 WHERE user_id = ?", (user_id,))
    elif type == "decrypt":
        cursor.execute("UPDATE users SET files_decrypted = files_decrypted + 1 WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()

def get_all_users_csv():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users")
    rows = cursor.fetchall()
    
    csv_content = "user_id,username,first_name,last_name,joined_at,last_active,files_encrypted,files_decrypted\n"
    for row in rows:
        # Avoid CSV injection or commas breaking format
        safe_row = [str(x).replace(',', ' ') if x else "" for x in row]
        csv_content += ",".join(safe_row) + "\n"
        
    conn.close()
    return csv_content

def get_stats_summary():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM users")
    total_users = cursor.fetchone()[0]
    cursor.execute("SELECT SUM(files_encrypted) FROM users")
    total_enc = cursor.fetchone()[0] or 0
    cursor.execute("SELECT SUM(files_decrypted) FROM users")
    total_dec = cursor.fetchone()[0] or 0
    conn.close()
    return f"👥 Jami foydalanuvchilar: {total_users}\n🔒 Shifrlangan fayllar: {total_enc}\n🔓 Ochilgan fayllar: {total_dec}"

def get_all_user_ids():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT user_id FROM users")
    ids = [row[0] for row in cursor.fetchall()]
    conn.close()
    return ids
