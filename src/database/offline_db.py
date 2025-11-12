# offline_db.py - Offline authentication using local SQLite

import sqlite3
import os
import logging
import json
from datetime import datetime

# Local database path
DB_DIR = os.path.join(os.getenv('APPDATA'), 'MezuniyyetSistemi')
OFFLINE_DB_PATH = os.path.join(DB_DIR, 'offline_auth.db')

def init_offline_db():
    """Initialize offline database for authentication"""
    try:
        os.makedirs(DB_DIR, exist_ok=True)
        conn = sqlite3.connect(OFFLINE_DB_PATH)
        cursor = conn.cursor()
        
        # Create users table for offline authentication
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS offline_users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                name TEXT,
                role TEXT,
                last_sync TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create connection info table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS connection_info (
                id INTEGER PRIMARY KEY,
                tenant_id TEXT,
                company_name TEXT,
                connection_string TEXT,
                last_online TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        conn.commit()
        conn.close()
        logging.info("Offline database initialized successfully")
        return True
    except Exception as e:
        logging.error(f"Failed to initialize offline database: {e}")
        return False

def verify_password(password, password_hash):
    """Verify password against bcrypt hash from database"""
    try:
        import bcrypt
        # The password_hash from database is a bcrypt hash, verify directly
        return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))
    except Exception as e:
        logging.error(f"Password verification error: {e}")
        return False

def save_user_for_offline(username, password_hash, name, role):
    """Save user credentials for offline authentication"""
    try:
        conn = sqlite3.connect(OFFLINE_DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT OR REPLACE INTO offline_users (username, password_hash, name, role, last_sync)
            VALUES (?, ?, ?, ?, ?)
        """, (username, password_hash, name, role, datetime.now()))
        
        conn.commit()
        conn.close()
        logging.info(f"User {username} saved for offline access")
        return True
    except Exception as e:
        logging.error(f"Failed to save user for offline: {e}")
        return False

def authenticate_offline(username, password):
    """Authenticate user using offline database"""
    try:
        if not os.path.exists(OFFLINE_DB_PATH):
            init_offline_db()
        
        conn = sqlite3.connect(OFFLINE_DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute("SELECT username, password_hash, name, role FROM offline_users WHERE username = ?", (username,))
        user = cursor.fetchone()
        conn.close()
        
        if user and verify_password(password, user[1]):
            logging.info(f"Offline authentication successful for {username}")
            return {
                'id': 0,  # Placeholder ID for offline mode
                'username': user[0],
                'name': user[2],
                'role': user[3]
            }
        
        logging.warning(f"Offline authentication failed for {username}")
        return None
    except Exception as e:
        logging.error(f"Offline authentication error: {e}")
        return None

def save_connection_info(tenant_id, company_name, connection_string):
    """Save connection information for reconnection (connection_string saxlanılmır - təhlükəsizlik üçün)"""
    try:
        conn = sqlite3.connect(OFFLINE_DB_PATH)
        cursor = conn.cursor()
        
        # Təhlükəsizlik: connection_string saxlanılmır, yalnız tenant_id və company_name
        cursor.execute("""
            INSERT OR REPLACE INTO connection_info (id, tenant_id, company_name, connection_string, last_online)
            VALUES (1, ?, ?, NULL, ?)
        """, (tenant_id, company_name, datetime.now()))
        
        conn.commit()
        conn.close()
        logging.info("Connection info saved (connection_string saxlanılmadı - təhlükəsizlik üçün)")
        return True
    except Exception as e:
        logging.error(f"Failed to save connection info: {e}")
        return False

def get_connection_info():
    """Get saved connection information (connection_string artıq qaytarılmır - təhlükəsizlik üçün)"""
    try:
        if not os.path.exists(OFFLINE_DB_PATH):
            return None
        
        conn = sqlite3.connect(OFFLINE_DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute("SELECT tenant_id, company_name FROM connection_info WHERE id = 1")
        info = cursor.fetchone()
        conn.close()
        
        if info:
            return {
                'tenant_id': info[0],
                'company_name': info[1],
                'connection_string': None  # Təhlükəsizlik: connection_string qaytarılmır
            }
        return None
    except Exception as e:
        logging.error(f"Failed to get connection info: {e}")
        return None

def clear_connection_info():
    """Clear connection string from offline database (təhlükəsizlik üçün)"""
    try:
        if not os.path.exists(OFFLINE_DB_PATH):
            return True
        
        conn = sqlite3.connect(OFFLINE_DB_PATH)
        cursor = conn.cursor()
        
        # Connection string-i NULL-a çeviririk (tenant_id və company_name saxlanılır)
        cursor.execute("""
            UPDATE connection_info 
            SET connection_string = NULL 
            WHERE id = 1
        """)
        
        conn.commit()
        conn.close()
        logging.info("Database konfiqurasiyası offline bazadan təmizləndi")
        return True
    except Exception as e:
        logging.error(f"Failed to clear connection info: {e}")
        return False

def clear_offline_data():
    """Clear all offline data"""
    try:
        if os.path.exists(OFFLINE_DB_PATH):
            os.remove(OFFLINE_DB_PATH)
            logging.info("Offline data cleared")
        return True
    except Exception as e:
        logging.error(f"Failed to clear offline data: {e}")
        return False

def is_offline_mode():
    """Check if we should use offline mode (when server is down)"""
    # This will be called when server connection fails
    return True  # For now, always allow offline mode if database exists

