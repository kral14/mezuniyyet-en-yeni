# database/connection.py (Düzəldilmiş)

import psycopg2
import logging
from tkinter import messagebox

_active_connection_params = {}

def clear_connection_params():
    """Clear connection parameters from memory (təhlükəsizlik üçün)"""
    global _active_connection_params
    _active_connection_params.clear()
    logging.info("Database konfiqurasiyası yaddaşdan təmizləndi")

def set_connection_params(connection_string: str):
    """
    Aktiv şirkətin qoşulma məlumatlarını qlobal olaraq təyin edir.
    Format: postgresql+psycopg2://user:password@host[:port]/dbname?param1=value1&param2=value2...
    Yalnız PostgreSQL/Neon bazası dəstəklənir.
    """
    global _active_connection_params
    _active_connection_params.clear()
    
    # İcazə verilən sxemlər: postgresql://, postgres://, postgresql+psycopg2://
    allowed_schemes = (
        'postgresql://',
        'postgres://',
        'postgresql+psycopg2://'
    )
    
    try:
        if '://' not in connection_string:
            raise ValueError("URL-də '://' tapılmadı.")
        
        # PostgreSQL connection string-i yoxlayır və normalize edirik
        if not connection_string.startswith(allowed_schemes):
            raise ValueError("Yalnız PostgreSQL connection string-ləri dəstəklənir.")

        # Parse üçün normalizasiya: bütün sxemləri 'postgresql://' şəklinə çeviririk
        normalized = connection_string
        if normalized.startswith('postgresql+psycopg2://'):
            normalized = normalized.replace('postgresql+psycopg2://', 'postgresql://', 1)
        elif normalized.startswith('postgres://'):
            normalized = normalized.replace('postgres://', 'postgresql://', 1)

        main_part = normalized.split('://')[1]
        
        if '@' not in main_part:
            raise ValueError("URL-də istifadəçi məlumatları ('@') tapılmadı.")
            
        user_pass, host_db = main_part.split('@', 1)
        
        if ':' not in user_pass:
            raise ValueError("İstifadəçi məlumatlarında parol ayırıcı (':') tapılmadı.")
            
        user, password = user_pass.split(':', 1)
        
        if '/' not in host_db:
             raise ValueError("URL-də verilənlər bazası adı ayırıcı ('/') tapılmadı.")
             
        host_port, db_details = host_db.split('/', 1)

        if ':' in host_port:
            host, port = host_port.split(':', 1)
        else:
            host = host_port
            port = "5432"

        # --- ƏSAS DÜZƏLİŞ BURADADIR ---
        # Qoşulma sətrindəki bütün əlavə parametrləri (`?`-dən sonra) düzgün təhlil edirik
        if '?' in db_details:
            dbname, query_part = db_details.split('?', 1)
            # Parametrləri '&' ilə ayırıb bir lüğətə (dictionary) yığırıq
            query_params = {}
            for param in query_part.split('&'):
                if '=' in param:
                    key, value = param.split('=', 1)
                    query_params[key] = value
        else:
            dbname = db_details
            query_params = {}
        # --- DÜZƏLİŞİN SONU ---

        # PostgreSQL connection parametrləri (database_type olmadan)
        connection_params = {
            "dbname": dbname,
            "user": user,
            "password": password,
            "host": host,
            "port": port,
            "connect_timeout": 10  # PostgreSQL connection timeout (saniyə)
        }
        # Təhlil edilmiş parametrləri əsas parametrlərə əlavə edirik
        connection_params.update(query_params)
        
        # Qlobal parametrlərə database_type və connection_string əlavə edirik
        _active_connection_params = connection_params.copy()
        _active_connection_params["database_type"] = "postgresql"
        _active_connection_params["connection_string"] = connection_string
        
        # connection_string parametrini PostgreSQL connection üçün çıxarırıq
        _active_connection_params.pop("connection_string", None)
        
        # Qoşulma zamanı 'channel_binding' parametrinin olub-olmadığını yoxlayaq
        # Bəzi psycopg2 versiyaları bunu dəstəkləməyə bilər
        if 'channel_binding' in connection_params:
            print("Warning: 'channel_binding' parameter may be required for NeonDB, but may cause problems on some systems.")
        
        # NeonDB üçün xüsusi parametrlər əlavə edirik
        if 'neon' in connection_string.lower():
            connection_params['sslmode'] = 'require'
            # channel_binding parametrini təhlükəsiz şəkildə əlavə edirik
            if 'channel_binding' not in connection_params:
                connection_params['channel_binding'] = 'prefer'

    except (IndexError, ValueError) as e:
        messagebox.showerror("Format Error", f"Connection string is not in correct format: {e}")
        raise ValueError("Connection string is not in correct format.") from e

def db_connect():
    """
    Qlobal olaraq təyin edilmiş parametrlərlə bazaya qoşulur.
    """
    print(f"🔵 DEBUG db_connect: Funksiya çağırıldı")
    print(f"🔵 DEBUG db_connect: Database konfiqurasiyası mövcuddur: {bool(_active_connection_params)}")
    # Təhlükəsizlik: Parametrlərin adları gizlədilir
    if _active_connection_params:
        # Təhlükəsizlik: Parametrlərin sayını göstəririk, adlarını yox
        param_count = len([k for k in _active_connection_params.keys() if k not in ['connection_string', 'database_type']])
        print(f"🔵 DEBUG db_connect: Database parametrləri sayı: {param_count}")
    else:
        print(f"🔵 DEBUG db_connect: Database konfiqurasiyası yoxdur")
    
    if not _active_connection_params:
        error_msg = "Baza qoşulma parametrləri təyin edilməyib. Əvvəlcə set_connection_params() çağırılmalıdır."
        print(f"❌ DEBUG db_connect: {error_msg}")
        logging.error(error_msg)
        # Proqramın çökmemesi üçün None qaytaraq
        return None
    
    try:
        # PostgreSQL üçün - database_type və connection_string parametrlərini çıxarırıq
        connection_params = _active_connection_params.copy()
        connection_params.pop("database_type", None)
        connection_params.pop("connection_string", None)
        
        # Əlavə təhlükəsizlik: bütün qeyri-dəstəklənən parametrləri çıxarırıq
        valid_params = {}
        valid_keys = ['dbname', 'user', 'password', 'host', 'port', 'connect_timeout', 'sslmode', 'channel_binding']
        for key, value in connection_params.items():
            if key in valid_keys:
                valid_params[key] = value
        
        print(f"🔵 DEBUG db_connect: psycopg2.connect() çağırılır...")
        # Təhlükəsizlik: Parametrlərin adları gizlədilir, yalnız sayı göstərilir
        param_count = len(valid_params)
        print(f"🔵 DEBUG db_connect: Database parametrləri sayı: {param_count}")
        conn = psycopg2.connect(**valid_params)
        print(f"✅ DEBUG db_connect: Connection uğurlu!")
        return conn
    except psycopg2.OperationalError as e:
        error_msg = f"Database qoşulması uğursuz (OperationalError): {e}"
        print(f"❌ DEBUG db_connect: {error_msg}")
        logging.error(error_msg)
        return None
    except psycopg2.Error as e:
        error_msg = f"Database qoşulması uğursuz (psycopg2.Error): {e}"
        print(f"❌ DEBUG db_connect: {error_msg}")
        logging.error(error_msg)
        return None
    except Exception as e:
        error_msg = f"Database qoşulması uğursuz (Gözlənilməz xəta): {e}"
        print(f"❌ DEBUG db_connect: {error_msg}")
        import traceback
        traceback.print_exc()
        logging.error(error_msg, exc_info=True)
        return None