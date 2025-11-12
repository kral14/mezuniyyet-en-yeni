# database/settings_queries.py

import psycopg2
from .connection import db_connect

def get_maintenance_mode():
    """Texniki iş rejiminin statusunu (true/false) qaytarır."""
    conn = db_connect()
    if not conn: return True # Baza yoxdursa, girişi bağlayaq
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT setting_value FROM app_settings WHERE setting_name = 'maintenance_mode'")
            result = cur.fetchone()
            # Nəticə 'true' stringidirsə, True, əks halda False qaytar
            return result[0].lower() == 'true' if result else False
    except psycopg2.Error:
        return False
    finally:
        if conn: conn.close()

def set_maintenance_mode(status: bool):
    """Texniki iş rejimini aktiv və ya deaktiv edir."""
    conn = db_connect()
    if not conn: return
    try:
        with conn.cursor() as cur:
            # status True isə 'true', False isə 'false' stringi yazırıq
            cur.execute("UPDATE app_settings SET setting_value = %s WHERE setting_name = 'maintenance_mode'", (str(status).lower(),))
            conn.commit()
    finally:
        if conn: conn.close()