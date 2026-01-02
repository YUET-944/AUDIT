"""
Enhanced database connection pooling for better performance and concurrency
"""
import sqlite3
from contextlib import contextmanager
import threading
from queue import Queue
import time
import os

class DatabasePool:
    def __init__(self, max_connections=10):
        self.pool = Queue(maxsize=max_connections)
        self.lock = threading.Lock()
        
        for _ in range(max_connections):
            # Check if PostgreSQL is configured
            if os.getenv('DB_TYPE', 'sqlite').lower() == 'postgresql':
                # For PostgreSQL, we'll use the psycopg2 connection pool
                # This is a placeholder - in production, use psycopg2.pool.ThreadedConnectionPool
                conn = self._create_postgresql_connection()
            else:
                # Use SQLite for development
                conn = sqlite3.connect('finance.db', check_same_thread=False, timeout=30)
                conn.execute("PRAGMA journal_mode=WAL")  # Better concurrency
                conn.execute("PRAGMA synchronous=NORMAL")
            self.pool.put(conn)
    
    def _create_postgresql_connection(self):
        """Create a PostgreSQL connection"""
        try:
            import psycopg2
            conn = psycopg2.connect(
                host=os.getenv('DB_HOST', 'localhost'),
                database=os.getenv('DB_NAME', 'algohub'),
                user=os.getenv('DB_USER', 'user'),
                password=os.getenv('DB_PASSWORD', 'password')
            )
            return conn
        except ImportError:
            print("Warning: psycopg2 not available, falling back to SQLite")
            # Fallback to SQLite
            conn = sqlite3.connect('finance.db', check_same_thread=False, timeout=30)
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA synchronous=NORMAL")
            return conn
    
    @contextmanager
    def get_connection(self):
        conn = self.pool.get()
        try:
            yield conn
        finally:
            self.pool.put(conn)

# Global pool instance
db_pool = DatabasePool()