# database/notification_queries.py

import psycopg2
from tkinter import messagebox
from .connection import db_connect

def _get_admin_ids(cursor):
    """(Yardımçı funksiya) Admin roluna sahib bütün istifadəçilərin ID-lərini qaytarır."""
    cursor.execute("SELECT id FROM employees WHERE role = 'admin'")
    return [row[0] for row in cursor.fetchall()]

def create_notification(recipient_id, message, related_vacation_id, cursor):
    """(Yardımçı funksiya) Verilənlər bazasına yeni bildiriş əlavə edir."""
    cursor.execute(
        "INSERT INTO notifications (recipient_id, message, related_vacation_id) VALUES (%s, %s, %s)",
        (recipient_id, message, related_vacation_id)
    )

def get_unread_notifications_for_user(user_id):
    """İstifadəçinin oxunmamış bildirişlərinin sayını qaytarır."""
    conn = db_connect()
    if not conn:
        return 0
        
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM notifications WHERE recipient_id = %s AND is_read = FALSE", (user_id,))
            result = cur.fetchone()
            return result[0] if result else 0
    except psycopg2.Error as e:
        messagebox.showerror("Baza Xətası", f"Bildirişləri sayarkən xəta baş verdi:\n{e}")
        return 0
    finally:
        if conn:
            conn.close()

def get_all_notifications_for_user(user_id):
    """İstifadəçinin bütün bildirişlərini (oxunmuş və oxunmamış) gətirir."""
    conn = db_connect()
    if not conn:
        return []
        
    try:
        with conn.cursor() as cur:
            # Məzuniyyət silindikdə belə əlaqəli işçi ID-sini götürmək üçün LEFT JOIN istifadə edilir
            cur.execute("""
                SELECT n.id, n.message, n.created_at, n.related_vacation_id, v.employee_id, n.is_read
                FROM notifications n
                LEFT JOIN vacations v ON n.related_vacation_id = v.id
                WHERE n.recipient_id = %s ORDER BY n.created_at DESC
            """, (user_id,))
            return cur.fetchall()
    except psycopg2.Error as e:
        messagebox.showerror("Baza Xətası", f"Bildirişləri oxuyarkən xəta baş verdi:\n{e}")
        return []
    finally:
        if conn:
            conn.close()

def mark_notifications_as_read(notification_ids):
    """Verilmiş ID-li bildirişləri 'oxunmuş' kimi işarələyir."""
    if not notification_ids:
        return
        
    conn = db_connect()
    if not conn:
        return
        
    try:
        with conn.cursor() as cur:
            # ID-lərin tuple olması üçün (notification_ids,) yazırıq
            cur.execute("UPDATE notifications SET is_read = TRUE WHERE id IN %s", (tuple(notification_ids),))
            conn.commit()
    except psycopg2.Error as e:
        messagebox.showerror("Baza Xətası", f"Bildirişlər yenilənərkən xəta baş verdi:\n{e}")
        conn.rollback()
    finally:
        if conn:
            conn.close()

def delete_notifications(notification_ids):
    """Verilmiş ID-li bildirişləri silir."""
    if not notification_ids:
        return
        
    conn = db_connect()
    if not conn:
        return
        
    try:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM notifications WHERE id IN %s", (tuple(notification_ids),))
            conn.commit()
        messagebox.showinfo("Uğurlu", f"{len(notification_ids)} bildiriş uğurla silindi.", parent=None)
    except psycopg2.Error as e:
        messagebox.showerror("Baza Xətası", f"Bildirişlər silinərkən xəta baş verdi:\n{e}")
        conn.rollback()
    finally:
        if conn:
            conn.close()