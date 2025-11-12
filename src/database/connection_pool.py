# connection_pool.py - Database connection pooling

import psycopg2
from psycopg2 import pool
import logging
import threading
import time
from contextlib import contextmanager

class DatabaseConnectionPool:
    def __init__(self, connection_params, min_connections=2, max_connections=10):
        self.connection_params = connection_params
        self.min_connections = min_connections
        self.max_connections = max_connections
        self.pool = None
        self._lock = threading.Lock()
        self._initialize_pool()
    
    def _initialize_pool(self):
        """Connection pool-u yaradır"""
        try:
            self.pool = pool.ThreadedConnectionPool(
                minconn=self.min_connections,
                maxconn=self.max_connections,
                **self.connection_params
            )
            logging.info(f"Database connection pool yaradıldı: {self.min_connections}-{self.max_connections}")
        except Exception as e:
            logging.error(f"Connection pool yaradılarkən xəta: {e}")
            self.pool = None
    
    @contextmanager
    def get_connection(self):
        """Thread-safe connection alır"""
        conn = None
        try:
            if self.pool:
                conn = self.pool.getconn()
                yield conn
            else:
                # Pool yoxdursa, normal connection yaradır
                conn = psycopg2.connect(**self.connection_params)
                yield conn
        except Exception as e:
            logging.error(f"Database connection xətası: {e}")
            raise
        finally:
            if conn:
                try:
                    if self.pool:
                        self.pool.putconn(conn)
                    else:
                        conn.close()
                except Exception as e:
                    logging.warning(f"Connection bağlanarkən xəta: {e}")
    
    def close(self):
        """Pool-u bağlayır"""
        if self.pool:
            self.pool.closeall()
            logging.info("Database connection pool bağlandı")

# Global pool instance
_connection_pool = None

def initialize_connection_pool(connection_params):
    """Global connection pool-u yaradır"""
    global _connection_pool
    if _connection_pool is None:
        _connection_pool = DatabaseConnectionPool(connection_params)
    return _connection_pool

def get_connection_pool():
    """Global connection pool-u qaytarır"""
    return _connection_pool

def close_connection_pool():
    """Global connection pool-u bağlayır"""
    global _connection_pool
    if _connection_pool:
        _connection_pool.close()
        _connection_pool = None 