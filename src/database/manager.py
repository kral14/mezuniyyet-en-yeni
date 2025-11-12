# database_manager.py - Çoxlu veritaban dəstəyi

import os
import logging
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

class DatabaseManager:
    """Çoxlu veritaban dəstəyi üçün universal menecer"""
    
    def __init__(self):
        self.supported_databases = {
            'postgresql': self._test_postgresql,
            'mysql': self._test_mysql,
            'mssql': self._test_mssql,
            'oracle': self._test_oracle
        }
    
    def detect_database_type(self, connection_string: str) -> str:
        """Connection string-dən veritaban növünü müəyyən edir"""
        if connection_string.startswith('postgresql://') or connection_string.startswith('postgres://'):
            return 'postgresql'
        elif connection_string.startswith('mysql://') or connection_string.startswith('mariadb://'):
            return 'mysql'
        elif connection_string.startswith('mssql://') or connection_string.startswith('sqlserver://'):
            return 'mssql'
        elif connection_string.startswith('oracle://'):
            return 'oracle'
        else:
            return 'unknown'
    
    def test_connection(self, connection_string: str) -> tuple[bool, str]:
        """Veritaban qoşulmasını test edir"""
        try:
            db_type = self.detect_database_type(connection_string)
            
            if db_type == 'unknown':
                return False, "Dəstəklənməyən veritaban növü"
            
            if db_type in self.supported_databases:
                return self.supported_databases[db_type](connection_string)
            else:
                return False, f"{db_type} veritabanı hələ dəstəklənmir"
                
        except Exception as e:
            logging.error(f"Veritaban test xətası: {e}")
            return False, f"Qoşulma xətası: {str(e)}"
    
    def _test_postgresql(self, connection_string: str) -> tuple[bool, str]:
        """PostgreSQL qoşulmasını test edir"""
        try:
            engine = create_engine(connection_string)
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            return True, "PostgreSQL qoşulması uğurludur"
        except Exception as e:
            return False, f"PostgreSQL xətası: {str(e)}"
    
    def _test_mysql(self, connection_string: str) -> tuple[bool, str]:
        """MySQL qoşulmasını test edir"""
        try:
            # MySQL üçün əlavə parametrlər
            if '?' not in connection_string:
                connection_string += '?charset=utf8mb4'
            engine = create_engine(connection_string)
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            return True, "MySQL qoşulması uğurludur"
        except Exception as e:
            return False, f"MySQL xətası: {str(e)}"
    
    
    def _test_mssql(self, connection_string: str) -> tuple[bool, str]:
        """SQL Server qoşulmasını test edir"""
        try:
            engine = create_engine(connection_string)
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            return True, "SQL Server qoşulması uğurludur"
        except Exception as e:
            return False, f"SQL Server xətası: {str(e)}"
    
    def _test_oracle(self, connection_string: str) -> tuple[bool, str]:
        """Oracle qoşulmasını test edir"""
        try:
            engine = create_engine(connection_string)
            with engine.connect() as conn:
                conn.execute(text("SELECT 1 FROM DUAL"))
            return True, "Oracle qoşulması uğurludur"
        except Exception as e:
            return False, f"Oracle xətası: {str(e)}"
    
    def get_database_info(self, connection_string: str) -> dict:
        """Veritaban məlumatlarını qaytarır"""
        db_type = self.detect_database_type(connection_string)
        
        info = {
            'type': db_type,
            'supported': db_type in self.supported_databases,
            'connection_string': '***'  # Təhlükəsizlik üçün gizlədildi
        }
        
        if db_type == 'postgresql':
            info['name'] = 'PostgreSQL'
            info['description'] = 'Güclü, açıq mənbəli veritaban'
        elif db_type == 'mysql':
            info['name'] = 'MySQL'
            info['description'] = 'Populyar açıq mənbəli veritaban'
        elif db_type == 'mssql':
            info['name'] = 'SQL Server'
            info['description'] = 'Microsoft veritaban sistemi'
        elif db_type == 'oracle':
            info['name'] = 'Oracle'
            info['description'] = 'Korporativ veritaban sistemi'
        else:
            info['name'] = 'Naməlum'
            info['description'] = 'Dəstəklənməyən veritaban növü'
        
        return info

# Test funksiyası
def test_database_manager():
    """Database manager-i test edir"""
    manager = DatabaseManager()
    
    # Test connection string-ləri (nümunə formatlar - təhlükəsizlik üçün gizlədildi)
    test_connections = [
        "postgresql://***:***@***/***",
        "mysql://***:***@***/***",
        "mssql://***:***@***/***",
        "oracle://***:***@***:1521/***"
    ]
    
    for conn_str in test_connections:
        db_type = manager.detect_database_type(conn_str)
        info = manager.get_database_info(conn_str)
        print(f"Database konfiqurasiyası: [Təhlükəsizlik üçün gizlədildi]")
        print(f"Type: {db_type}")
        print(f"Info: {info}")
        print("-" * 50)

if __name__ == "__main__":
    test_database_manager() 