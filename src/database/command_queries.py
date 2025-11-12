# database/command_queries.py (Yekun Versiya)

import psycopg2
from tkinter import messagebox
from datetime import datetime, timedelta
from .connection import db_connect

def issue_timed_logout_command(user_ids, minutes):
    if not user_ids: return 0
    conn = db_connect()
    if not conn: return 0
    try:
        with conn.cursor() as cur:
            logout_time = datetime.now() + timedelta(minutes=minutes)
            for user_id in user_ids:
                cur.execute("INSERT INTO system_commands (target_user_id, command_type, command_value) VALUES (%s, 'TIMED_LOGOUT', %s)", (user_id, logout_time.isoformat()))
            conn.commit()
            return len(user_ids)
    except psycopg2.Error as e:
        messagebox.showerror("Baza Xətası", f"Əmr göndərərkən xəta baş verdi:\n{e}"); conn.rollback(); return 0
    finally:
        if conn: conn.close()

def issue_immediate_logout_command(user_ids):
    if not user_ids: return 0
    conn = db_connect()
    if not conn: return 0
    try:
        with conn.cursor() as cur:
            for user_id in user_ids:
                cur.execute("INSERT INTO system_commands (target_user_id, command_type) VALUES (%s, 'IMMEDIATE_LOGOUT')", (user_id,))
            conn.commit()
            return len(user_ids)
    except psycopg2.Error as e:
        messagebox.showerror("Baza Xətası", f"Əmr göndərərkən xəta baş verdi:\n{e}"); conn.rollback(); return 0
    finally:
        if conn: conn.close()

def get_pending_commands(user_id):
    conn = db_connect()
    if not conn: return None
    command = None
    try:
        with conn.cursor() as cur:
            # DÜZƏLİŞ: Yalnız icra edilməmiş və bu istifadəçiyə aid olan ƏN SON əmri alırıq
            cur.execute(
                "SELECT id, command_type, command_value FROM system_commands WHERE target_user_id = %s AND is_executed = FALSE ORDER BY created_at DESC LIMIT 1",
                (user_id,)
            )
            result = cur.fetchone()
            if result:
                command = {'id': result[0], 'type': result[1], 'value': result[2]}
    except psycopg2.Error as e:
        print(f"Sistem əmrləri yoxlanarkən xəta baş verdi: {e}")
    finally:
        if conn: conn.close()
    return command

def mark_command_as_executed(command_id):
    conn = db_connect()
    if not conn: return
    try:
        with conn.cursor() as cur:
            cur.execute("UPDATE system_commands SET is_executed = TRUE WHERE id = %s", (command_id,))
            conn.commit()
    except psycopg2.Error as e:
        print(f"Əmr statusu yenilənərkən xəta baş verdi: {e}"); conn.rollback()
    finally:
        if conn: conn.close()