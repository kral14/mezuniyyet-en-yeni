# database/session_queries.py (DÜZƏLDİLMİŞ VƏ TAM VERSİYA)

import psycopg2
# SQLite import silindi
import uuid
from tkinter import messagebox
from .connection import db_connect, _active_connection_params

def get_all_active_non_admin_user_ids():
    """Sistemdə aktiv olan bütün admin olmayan istifadəçilərin ID-lərini qaytarır."""
    conn = db_connect()
    if not conn: return []
    user_ids = []
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT s.user_id
                FROM active_sessions s
                JOIN employees e ON s.user_id = e.id
                WHERE e.role != 'admin'
                """
            )
            user_ids = [row[0] for row in cur.fetchall()]
    except psycopg2.Error as e:
        messagebox.showerror("Baza Xətası", f"Aktiv istifadəçilər alınarkən xəta: \n{e}")
    finally:
        if conn: conn.close()
    return user_ids

def add_user_session(user_id, ip_address):
    conn = db_connect()
    if not conn: return None, None
    session_id, history_id = uuid.uuid4(), None
    try:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO active_sessions (session_id, user_id, ip_address) VALUES (%s, %s, %s)",
                (str(session_id), user_id, ip_address)
            )
            cur.execute("INSERT INTO login_history (user_id) VALUES (%s) RETURNING id", (user_id,))
            result = cur.fetchone()
            if result:
                history_id = result[0]
            conn.commit()
        return str(session_id), history_id
    except psycopg2.Error as e:
        messagebox.showerror("Baza Xətası", f"Sessiya yaradılarkən xəta baş verdi:\n{e}")
        conn.rollback()
        return None, None
    finally:
        if conn: conn.close()

def remove_user_session(session_id, history_id):
    if not session_id: return
    conn = db_connect()
    if not conn: return
    try:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM active_sessions WHERE session_id = %s", (session_id,))
            if history_id:
                cur.execute("UPDATE login_history SET logout_time = CURRENT_TIMESTAMP WHERE id = %s", (history_id,))
            conn.commit()
    except psycopg2.Error as e:
        messagebox.showerror("Baza Xətası", f"Sessiya silinərkən xəta baş verdi:\n{e}")
        conn.rollback()
    finally:
        if conn: conn.close()

def get_active_session_counts():
    conn = db_connect()
    if not conn: return {}
    counts = {}
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT user_id, COUNT(*) FROM active_sessions GROUP BY user_id")
            for user_id, count in cur.fetchall():
                counts[user_id] = count
    except psycopg2.Error as e:
        messagebox.showerror("Baza Xətası", f"Aktiv sessiyalar alınarkən xəta baş verdi:\n{e}")
    finally:
        if conn: conn.close()
    return counts

def get_active_user_details():
    conn = db_connect()
    if not conn: return []
    users = []
    try:
        with conn.cursor() as cur:
            sql = """
                SELECT DISTINCT ON (s.user_id)
                    s.user_id,
                    e.username,
                    e.name,
                    s.ip_address,
                    COALESCE(lh.login_time, s.created_at) as display_time
                FROM active_sessions s
                JOIN employees e ON s.user_id = e.id
                LEFT JOIN (
                    SELECT user_id, MAX(login_time) as last_login
                    FROM login_history
                    WHERE logout_time IS NULL
                    GROUP BY user_id
                ) l ON s.user_id = l.user_id
                LEFT JOIN login_history lh ON l.user_id = lh.user_id AND l.last_login = lh.login_time;
            """
            cur.execute(sql)
            for row in cur.fetchall():
                users.append({
                    'user_id': row[0], 'username': row[1], 'name': row[2],
                    'ip_address': row[3], 'login_time': row[4]
                })
    except psycopg2.Error as e:
        messagebox.showerror("Baza Xətası", f"Aktiv istifadəçilərin məlumatları alınarkən xəta baş verdi:\n{e}")
    finally:
        if conn: conn.close()
    return users

def force_remove_sessions_by_user_id(user_ids):
    if not user_ids: return False
    conn = db_connect()
    if not conn: return False
    try:
        with conn.cursor() as cur:
            ids_tuple = tuple(user_ids)
            cur.execute(
                "UPDATE login_history SET logout_time = CURRENT_TIMESTAMP WHERE user_id IN %s AND logout_time IS NULL",
                (ids_tuple,)
            )
            cur.execute("DELETE FROM active_sessions WHERE user_id IN %s", (ids_tuple,))
            conn.commit()
        return True
    except psycopg2.Error as e:
        messagebox.showerror("Baza Xətası", f"Sessiyalar silinərkən xəta baş verdi:\n{e}")
        conn.rollback()
        return False
    finally:
        if conn: conn.close()

# YENİ ƏLAVƏ EDİLƏN FUNKSİYA
def get_login_history(user_id):
    """İstifadəçinin giriş-çıxış tarixçəsini gətirir."""
    conn = db_connect()
    if not conn: return []
    history = []
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT login_time, logout_time FROM login_history WHERE user_id = %s ORDER BY login_time DESC",
                (user_id,)
            )
            history = cur.fetchall()
    except psycopg2.Error as e:
        messagebox.showerror("Baza Xətası", f"Tarixçə oxunarkən xəta: \n{e}")
    finally:
        if conn: conn.close()
    return history