import sqlite3
import datetime
import os

DB_NAME = "users.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # Users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            first_name TEXT,
            last_name TEXT,
            joined_at TIMESTAMP,
            last_active TIMESTAMP,
            files_encrypted INTEGER DEFAULT 0,
            files_decrypted INTEGER DEFAULT 0,
            language TEXT DEFAULT 'uz'
        )
    ''')
    
    # File history table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS file_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            filename TEXT,
            algorithm TEXT,
            action TEXT,
            timestamp TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        )
    ''')
    
    # Blocked users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS blocked_users (
            user_id INTEGER PRIMARY KEY,
            blocked_at TIMESTAMP,
            reason TEXT
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

def get_users_paginated(page=1, limit=5):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    offset = (page - 1) * limit
    
    # Get total count
    cursor.execute("SELECT COUNT(*) FROM users")
    total_users = cursor.fetchone()[0]
    
    # Get page users
    cursor.execute('''
        SELECT user_id, username, first_name, last_name, joined_at, files_encrypted, files_decrypted 
        FROM users 
        ORDER BY joined_at DESC 
        LIMIT ? OFFSET ?
    ''', (limit, offset))
    
    users = cursor.fetchall()
    conn.close()
    
    import math
    total_pages = math.ceil(total_users / limit)
    
    return users, total_pages, total_users

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

# Language management
def set_user_language(user_id, language):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET language = ? WHERE user_id = ?", (language, user_id))
    conn.commit()
    conn.close()

def get_user_language(user_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT language FROM users WHERE user_id = ?", (user_id,))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else 'uz'

# File history
def add_file_history(user_id, filename, algorithm, action):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    now = datetime.datetime.now()
    cursor.execute('''
        INSERT INTO file_history (user_id, filename, algorithm, action, timestamp)
        VALUES (?, ?, ?, ?, ?)
    ''', (user_id, filename, algorithm, action, now))
    conn.commit()
    conn.close()

def get_user_file_history(user_id, limit=10):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT filename, algorithm, action, timestamp 
        FROM file_history 
        WHERE user_id = ? 
        ORDER BY timestamp DESC 
        LIMIT ?
    ''', (user_id, limit))
    rows = cursor.fetchall()
    conn.close()
    return rows

# User blocking
def block_user(user_id, reason=""):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    now = datetime.datetime.now()
    cursor.execute('''
        INSERT OR REPLACE INTO blocked_users (user_id, blocked_at, reason)
        VALUES (?, ?, ?)
    ''', (user_id, now, reason))
    conn.commit()
    conn.close()

def unblock_user(user_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM blocked_users WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()

def is_blocked(user_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT user_id FROM blocked_users WHERE user_id = ?", (user_id,))
    result = cursor.fetchone()
    conn.close()
    return result is not None

# Statistics
def get_daily_stats(days=7):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # Get daily user registrations
    cursor.execute('''
        SELECT DATE(joined_at) as date, COUNT(*) as count
        FROM users
        WHERE joined_at >= datetime('now', '-' || ? || ' days')
        GROUP BY DATE(joined_at)
        ORDER BY date
    ''', (days,))
    registrations = cursor.fetchall()
    
    # Get daily file operations
    cursor.execute('''
        SELECT DATE(timestamp) as date, action, COUNT(*) as count
        FROM file_history
        WHERE timestamp >= datetime('now', '-' || ? || ' days')
        GROUP BY DATE(timestamp), action
        ORDER BY date
    ''', (days,))
    operations = cursor.fetchall()
    
    conn.close()
    return {'registrations': registrations, 'operations': operations}

def get_active_users(hours=24):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT COUNT(DISTINCT user_id) 
        FROM file_history 
        WHERE timestamp >= datetime('now', '-' || ? || ' hours')
    ''', (hours,))
    count = cursor.fetchone()[0]
    conn.close()
    return count

