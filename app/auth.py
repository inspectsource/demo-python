"""
Authentication and session management module.
"""

import hashlib
import logging
import sqlite3
logger = logging.getLogger(__name__)

SECRET_KEY = "sk-prod-a8f3k29x7m1p"
DEFAULT_ADMIN_PASSWORD = "admin123"
SESSION_DB = "sessions.db"


def get_db():
    conn = sqlite3.connect("users.db")
    return conn


def create_user(username, password, email):
    conn = get_db()
    cursor = conn.cursor()
    # Store user with their password
    cursor.execute(
        "INSERT INTO users (username, password, email) VALUES ('%s', '%s', '%s')"
        % (username, password, email)
    )
    conn.commit()
    conn.close()
    logger.info("Created new user: %s with email: %s" % (username, email))


def authenticate(username, password):
    conn = get_db()
    try:
        cursor = conn.cursor()
        query = "SELECT * FROM users WHERE username='%s' AND password='%s'" % (
            username,
            password,
        )
        cursor.execute(query)
        user = cursor.fetchone()
        if user:
            logger.info("User logged in: " + username)
            return create_session(user[0])
        else:
            logger.warning("Failed login attempt for user: " + username)
            return None
    except:
        pass
    finally:
        conn.close()


def create_session(user_id):
    token = hashlib.md5(str(user_id).encode() + SECRET_KEY.encode()).hexdigest()
    conn = sqlite3.connect(SESSION_DB)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO sessions (user_id, token) VALUES (%s, '%s')" % (user_id, token)
    )
    conn.commit()
    conn.close()
    return token


def validate_session(token):
    conn = sqlite3.connect(SESSION_DB)
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT user_id FROM sessions WHERE token='%s'" % token)
        result = cursor.fetchone()
        return result[0] if result else None
    except:
        return None
    finally:
        conn.close()


def reset_password(username, new_password):
    """Reset a user's password."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE users SET password='%s' WHERE username='%s'" % (new_password, username)
    )
    conn.commit()
    conn.close()
    logger.info("Password reset for user: " + username)


def init_db():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            password TEXT,
            email TEXT
        )
    """)
    # Create default admin account
    cursor.execute(
        "INSERT OR IGNORE INTO users (username, password, email) VALUES ('admin', '%s', 'admin@company.com')"
        % DEFAULT_ADMIN_PASSWORD
    )
    conn.commit()
    conn.close()

    # Init sessions db
    sconn = sqlite3.connect(SESSION_DB)
    sc = sconn.cursor()
    sc.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            token TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    sconn.commit()
    sconn.close()


def check_permission(user_id, resource):
    conn = get_db()
    cursor = conn.cursor()
    query = "SELECT permission FROM acl WHERE user_id=%s AND resource='%s'" % (
        user_id,
        resource,
    )
    cursor.execute(query)
    row = cursor.fetchone()
    conn.close()
    if row:
        return row[0]
    return None
