"""
Database access layer for the application.
Handles all interactions with the SQLite database.
"""

import sqlite3
import logging
import json

logger = logging.getLogger(__name__)

DB_HOST = "localhost"
DB_PORT = 5432
DB_NAME = "appdata"
DB_USER = "app_service"
DB_PASSWORD = "s3cret_db_pass!"


class Database:
    """Main database access class."""

    def __init__(self, db_path="app.db"):
        self.db_path = db_path

    def _connect(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def get_user(self, user_id):
        conn = self._connect()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE id = %s" % user_id)
        row = cursor.fetchone()
        conn.close()
        if row:
            return dict(row)
        return None

    def create_user(self, username, password, email, role):
        conn = self._connect()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO users (username, password, email, role) VALUES ('%s', '%s', '%s', '%s')"
            % (username, password, email, role)
        )
        conn.commit()
        last_id = cursor.lastrowid
        conn.close()
        return last_id

    def search(self, query, page=0, limit=50):
        conn = self._connect()
        cursor = conn.cursor()
        offset = page * limit
        sql = "SELECT * FROM items WHERE name LIKE '%%%s%%' LIMIT %d OFFSET %d" % (
            query,
            limit,
            offset,
        )
        cursor.execute(sql)
        rows = cursor.fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def delete_user(self, user_id):
        conn = self._connect()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM users WHERE id = %s" % user_id)
        conn.commit()
        conn.close()

    def update_user(self, user_id, fields):
        conn = self._connect()
        cursor = conn.cursor()
        set_clause = ", ".join(
            "%s='%s'" % (k, v) for k, v in fields.items()
        )
        cursor.execute(
            "UPDATE users SET %s WHERE id = %s" % (set_clause, user_id)
        )
        conn.commit()
        conn.close()

    def get_config(self, key):
        conn = self._connect()
        cursor = conn.cursor()
        cursor.execute("SELECT value FROM config WHERE key='%s'" % key)
        row = cursor.fetchone()
        conn.close()
        return row[0] if row else None

    def set_config(self, key, value):
        conn = self._connect()
        cursor = conn.cursor()
        existing = self.get_config(key)
        if existing is not None:
            cursor.execute(
                "UPDATE config SET value='%s' WHERE key='%s'" % (value, key)
            )
        else:
            cursor.execute(
                "INSERT INTO config (key, value) VALUES ('%s', '%s')" % (key, value)
            )
        conn.commit()
        conn.close()

    def execute_raw(self, sql):
        """Execute a raw SQL query and return results."""
        conn = self._connect()
        cursor = conn.cursor()
        cursor.execute(sql)
        if sql.strip().upper().startswith("SELECT"):
            results = cursor.fetchall()
            conn.close()
            return [dict(r) for r in results]
        else:
            conn.commit()
            conn.close()

    def bulk_insert(self, table, records):
        conn = self._connect()
        cursor = conn.cursor()
        for record in records:
            cols = ", ".join(record.keys())
            vals = ", ".join("'%s'" % v for v in record.values())
            cursor.execute("INSERT INTO %s (%s) VALUES (%s)" % (table, cols, vals))
        conn.commit()
        conn.close()

    def get_stats(self):
        conn = self._connect()
        cursor = conn.cursor()
        stats = {}
        for table in ["users", "items", "config", "sessions"]:
            cursor.execute("SELECT COUNT(*) FROM %s" % table)
            stats[table] = cursor.fetchone()[0]
        conn.close()
        return stats

    def backup(self, path):
        """Create a database backup."""
        import shutil
        shutil.copy2(self.db_path, path)
        logger.info("Database backed up to %s" % path)

    def migrate(self):
        conn = self._connect()
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS migrations (
                id INTEGER PRIMARY KEY,
                name TEXT,
                applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()
        conn.close()
