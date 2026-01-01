"""
Enhanced database connection pooling for better performance and concurrency
"""
import sqlite3
from contextlib import contextmanager
import threading
from queue import Queue
import time

class DatabasePool:
    def __init__(self, max_connections=10):
        self.pool = Queue(maxsize=max_connections)
        self.lock = threading.Lock()
        
        for _ in range(max_connections):
            conn = sqlite3.connect('finance.db', check_same_thread=False, timeout=30)
            conn.execute("PRAGMA journal_mode=WAL")  # Better concurrency
            conn.execute("PRAGMA synchronous=NORMAL")
            self.pool.put(conn)
    
    @contextmanager
    def get_connection(self):
        conn = self.pool.get()
        try:
            yield conn
        finally:
            self.pool.put(conn)

# Global pool instance
db_pool = DatabasePool()