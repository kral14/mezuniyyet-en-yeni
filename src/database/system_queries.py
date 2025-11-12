# database/system_queries.py

import psycopg2
# SQLite import silindi
from tkinter import messagebox
from datetime import date
from .connection import db_connect, _active_connection_params

# --- ARXİVLƏMƏ FUNKSİYALARI ---

def get_employees_with_archivable_vacations():
    """Arxivlənə bilən məzuniyyətləri olan işçilərin siyahısını qaytarır."""
    conn = db_connect()
    if not conn:
        return []
        
    try:
        with conn.cursor() as cur:
            current_year = date.today().year
            sql = """
                SELECT e.id, e.name, COUNT(v.id) FILTER (WHERE EXTRACT(YEAR FROM v.start_date) < %s AND v.is_archived = FALSE AND v.status = 'approved')
                FROM employees e
                LEFT JOIN vacations v ON e.id = v.employee_id
                WHERE e.is_active = TRUE
                GROUP BY e.id, e.name ORDER BY e.name
            """
            cur.execute(sql, (current_year,))
            return cur.fetchall()
    except psycopg2.Error as e:
        messagebox.showerror("Baza Xətası", f"Arxiv məlumatı alınarkən xəta baş verdi:\n{e}")
        return []
    finally:
        if conn:
            conn.close()

def start_new_vacation_year(employee_ids, default_days=30):
    """Seçilmiş işçilər üçün yeni məzuniyyət ili başladır."""
    if not employee_ids:
        return False
        
    conn = db_connect()
    if not conn:
        return False
        
    try:
        with conn.cursor() as cur:
            current_year = date.today().year
            ids_tuple = tuple(employee_ids)
            cur.execute("UPDATE vacations SET is_archived = TRUE WHERE status = 'approved' AND EXTRACT(YEAR FROM start_date) < %s AND employee_id IN %s", (current_year, ids_tuple))
            archived_count = cur.rowcount
            cur.execute("UPDATE employees SET total_vacation_days = %s WHERE id IN %s", (default_days, ids_tuple))
            updated_employees = cur.rowcount
            conn.commit()
        messagebox.showinfo("Əməliyyat Uğurlu", f"{updated_employees} işçinin məzuniyyət hüququ yeniləndi və {archived_count} köhnə məzuniyyət arxivləşdirildi.")
        return True
    except psycopg2.Error as e:
        messagebox.showerror("Baza Xətası", f"Yeni məzuniyyət ilinə başlarkən xəta baş verdi:\n{e}")
        conn.rollback()
        return False
    finally:
        if conn:
            conn.close()

def load_archived_vacations_for_year(employee_id, year):
    """İşçinin seçilmiş ilə aid arxiv məlumatlarını gətirir."""
    conn = db_connect()
    if not conn:
        return []
        
    vacations = []
    try:
        with conn.cursor() as cur:
            sql = """
                SELECT id, start_date, end_date, note, is_inactive, created_at, status
                FROM vacations
                WHERE employee_id = %s AND is_archived = TRUE AND EXTRACT(YEAR FROM start_date) = %s
                ORDER BY start_date
            """
            cur.execute(sql, (employee_id, year))
            for row in cur.fetchall():
                vacations.append({
                    "db_id": row[0], "baslama": row[1].isoformat(), "bitme": row[2].isoformat(),
                    "qeyd": row[3], "aktiv_deyil": row[4],
                    "yaradilma_tarixi": row[5].isoformat(), "status": row[6]
                })
    except psycopg2.Error as e:
        messagebox.showerror("Baza Oxuma Xətası", f"Arxiv məlumatlarını oxuyarkən xəta baş verdi:\n{e}")
    finally:
        if conn:
            conn.close()
    return vacations

# --- VERSİYA FUNKSİYASI ---

def get_latest_version():
    """Verilənlər bazasından proqramın ən son versiyasını gətirir."""
    conn = db_connect()
    if not conn:
        return None
        
    try:
        # PostgreSQL connection
        with conn.cursor() as cur:
            # Əvvəlcə app_version cədvəlinin mövcudluğunu yoxla
            cur.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = 'app_version'
                )
            """)
            table_exists = cur.fetchone()[0]
            
            if not table_exists:
                # Cədvəl yoxdursa yarat
                cur.execute("""
                    CREATE TABLE app_version (
                        id INTEGER PRIMARY KEY,
                        latest_version TEXT NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                # Default versiya əlavə et
                cur.execute("INSERT INTO app_version (id, latest_version) VALUES (1, '6.8-final-unified-tkinter')")
                conn.commit()
                return '6.8-final-unified-tkinter'
            
            cur.execute("SELECT latest_version FROM app_version WHERE id = 1")
            result = cur.fetchone()
            return result[0] if result else None
    except psycopg2.Error as e:
        print(f"Versiya yoxlanarkən xəta baş verdi: {e}")
        return None
    finally:
        if conn:
            conn.close()