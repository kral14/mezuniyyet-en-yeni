import psycopg2
# SQLite import silindi
from tkinter import messagebox
from .connection import db_connect, _active_connection_params
from .notification_queries import create_notification, _get_admin_ids

def add_vacation(employee_id, employee_name, vac_data, requested_by_role):
    """Verilənlər bazasına yeni məzuniyyət sorğusu əlavə edir."""
    conn = db_connect()
    if not conn:
        return
        
    status = 'approved' if requested_by_role == 'admin' else 'pending'
    try:
        # PostgreSQL üçün emal
            cursor = conn.execute(
                "INSERT INTO vacations (employee_id, start_date, end_date, note, created_at, status) VALUES (?, ?, ?, ?, ?, ?)",
                (employee_id, vac_data['baslama'], vac_data['bitme'], vac_data['qeyd'], vac_data['yaradilma_tarixi'], status)
            )
            vac_id = cursor.lastrowid
            
            # Əgər sorğunu işçi göndəribsə, adminlərə bildiriş getsin
            if status == 'pending':
                admin_cursor = conn.execute("SELECT id FROM employees WHERE role = 'admin'")
                admin_ids = [row[0] for row in admin_cursor.fetchall()]
                message = f"İşçi '{employee_name}' yeni məzuniyyət sorğusu göndərdi."
                for admin_id in admin_ids:
                    conn.execute(
                        "INSERT INTO notifications (recipient_id, message, related_vacation_id) VALUES (?, ?, ?)",
                        (admin_id, message, vac_id)
                    )
            conn.commit()
        else:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO vacations (employee_id, start_date, end_date, note, created_at, status) VALUES (%s, %s, %s, %s, %s, %s) RETURNING id",
                    (employee_id, vac_data['baslama'], vac_data['bitme'], vac_data['qeyd'], vac_data['yaradilma_tarixi'], status)
                )
                vac_id = cur.fetchone()[0]
                
                # Əgər sorğunu işçi göndəribsə, adminlərə bildiriş getsin
                if status == 'pending':
                    admin_ids = _get_admin_ids(cur)
                    message = f"İşçi '{employee_name}' yeni məzuniyyət sorğusu göndərdi."
                    for admin_id in admin_ids:
                        create_notification(admin_id, message, vac_id, cur)
                conn.commit()
            
    except psycopg2.Error as e:
        messagebox.showerror("Baza Xətası", f"Məzuniyyət əlavə edilərkən xəta baş verdi:\n{e}")
        conn.rollback()
    finally:
        if conn:
            conn.close()

def update_vacation(vac_id, vac_data, admin_name):
    """Mövcud məzuniyyət sorğusunun tarix və qeydini yeniləyir."""
    conn = db_connect()
    if not conn:
        return
        
    try:
        # PostgreSQL üçün emal
            cursor = conn.execute(
                "UPDATE vacations SET start_date=?, end_date=?, note=? WHERE id=?",
                (vac_data['baslama'], vac_data['bitme'], vac_data['qeyd'], vac_id)
            )
            recipient_cursor = conn.execute("SELECT employee_id FROM vacations WHERE id = ?", (vac_id,))
            recipient_id = recipient_cursor.fetchone()[0]
            
            # Dəyişiklik haqqında işçiyə bildiriş göndər
            message = f"Admin '{admin_name}' sizin {vac_data['baslama']} tarixli məzuniyyət sorğunuzda dəyişiklik etdi."
            conn.execute(
                "INSERT INTO notifications (recipient_id, message, related_vacation_id) VALUES (?, ?, ?)",
                (recipient_id, message, vac_id)
            )
            conn.commit()
        else:
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE vacations SET start_date=%s, end_date=%s, note=%s WHERE id=%s RETURNING employee_id",
                    (vac_data['baslama'], vac_data['bitme'], vac_data['qeyd'], vac_id)
                )
                recipient_id = cur.fetchone()[0]
                
                # Dəyişiklik haqqında işçiyə bildiriş göndər
                message = f"Admin '{admin_name}' sizin {vac_data['baslama']} tarixli məzuniyyət sorğunuzda dəyişiklik etdi."
                create_notification(recipient_id, message, vac_id, cur)
                conn.commit()
            
    except psycopg2.Error as e:
        messagebox.showerror("Baza Xətası", f"Məzuniyyət yenilənərkən xəta baş verdi:\n{e}")
        conn.rollback()
    finally:
        if conn:
            conn.close()

def update_vacation_status(vac_id, new_status, admin_name):
    """Məzuniyyət sorğusunun statusunu (təsdiq/rədd) dəyişir."""
    conn = db_connect()
    if not conn:
        return
        
    try:
        # PostgreSQL üçün emal
            conn.execute(
                "UPDATE vacations SET status = ? WHERE id = ?",
                (new_status, vac_id)
            )
            recipient_cursor = conn.execute("SELECT employee_id, start_date, end_date FROM vacations WHERE id = ?", (vac_id,))
            recipient_id, start_date, end_date = recipient_cursor.fetchone()
            
            status_az = "Təsdiqləndi" if new_status == 'approved' else "Rədd edildi"
            message = f"Admin '{admin_name}', sizin {start_date} - {end_date} arası sorğunuzu '{status_az}' statusu ilə yenilədi."
            conn.execute(
                "INSERT INTO notifications (recipient_id, message, related_vacation_id) VALUES (?, ?, ?)",
                (recipient_id, message, vac_id)
            )
            conn.commit()
        else:
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE vacations SET status = %s WHERE id = %s RETURNING employee_id, start_date, end_date",
                    (new_status, vac_id)
                )
                recipient_id, start_date, end_date = cur.fetchone()
                
                status_az = "Təsdiqləndi" if new_status == 'approved' else "Rədd edildi"
                message = f"Admin '{admin_name}', sizin {start_date.strftime('%d.%m.%Y')} - {end_date.strftime('%d.%m.%Y')} arası sorğunuzu '{status_az}' statusu ilə yenilədi."
                create_notification(recipient_id, message, vac_id, cur)
                conn.commit()
            
    except psycopg2.Error as e:
        messagebox.showerror("Baza Xətası", f"Məzuniyyət statusu yenilənərkən xəta baş verdi:\n{e}")
        conn.rollback()
    finally:
        if conn:
            conn.close()

def delete_vacation(vac_id, admin_name):
    """Məzuniyyət sorğusunu tamamilə silir."""
    conn = db_connect()
    if not conn:
        return
        
    try:
        # PostgreSQL üçün emal
            result_cursor = conn.execute("SELECT employee_id, start_date, end_date FROM vacations WHERE id = ?", (vac_id,))
            result = result_cursor.fetchone()
            if result:
                recipient_id, start_date, end_date = result
                
                # Əvvəlcə sil, sonra bildiriş göndər
                conn.execute("DELETE FROM vacations WHERE id = ?", (vac_id,))
                
                message = f"Admin '{admin_name}' sizin {start_date} - {end_date} arası sorğunuzu sildi."
                # Məzuniyyət silindiyi üçün `related_vacation_id` NULL olacaq
                conn.execute(
                    "INSERT INTO notifications (recipient_id, message, related_vacation_id) VALUES (?, ?, ?)",
                    (recipient_id, message, None)
                )
            conn.commit()
        else:
            with conn.cursor() as cur:
                cur.execute("SELECT employee_id, start_date, end_date FROM vacations WHERE id = %s", (vac_id,))
                result = cur.fetchone()
                if result:
                    recipient_id, start_date, end_date = result
                    
                    # Əvvəlcə sil, sonra bildiriş göndər
                    cur.execute("DELETE FROM vacations WHERE id = %s", (vac_id,))
                    
                    message = f"Admin '{admin_name}' sizin {start_date.strftime('%d.%m.%Y')} - {end_date.strftime('%d.%m.%Y')} arası sorğunuzu sildi."
                    # Məzuniyyət silindiyi üçün `related_vacation_id` NULL olacaq
                    create_notification(recipient_id, message, None, cur)
                conn.commit()
            
    except psycopg2.Error as e:
        messagebox.showerror("Baza Xətası", f"Məzuniyyət silinərkən xəta baş verdi:\n{e}")
        conn.rollback()
    finally:
        if conn:
            conn.close()

def toggle_vacation_activity(vac_id, new_status, admin_name):
    """Təsdiqlənmiş məzuniyyəti aktiv/deaktiv edir."""
    conn = db_connect()
    if not conn:
        return
        
    try:
        # PostgreSQL üçün emal
            conn.execute(
                "UPDATE vacations SET is_inactive = ? WHERE id = ?",
                (new_status, vac_id)
            )
            recipient_cursor = conn.execute("SELECT employee_id, start_date, end_date FROM vacations WHERE id = ?", (vac_id,))
            recipient_id, start_date, end_date = recipient_cursor.fetchone()
            
            status_az = "deaktiv" if new_status else "aktiv"
            message = f"Admin '{admin_name}' sizin {start_date} tarixli təsdiqlənmiş məzuniyyətinizi '{status_az}' etdi."
            conn.execute(
                "INSERT INTO notifications (recipient_id, message, related_vacation_id) VALUES (?, ?, ?)",
                (recipient_id, message, vac_id)
            )
            conn.commit()
        else:
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE vacations SET is_inactive = %s WHERE id = %s RETURNING employee_id, start_date, end_date",
                    (new_status, vac_id)
                )
                recipient_id, start_date, end_date = cur.fetchone()
                
                status_az = "deaktiv" if new_status else "aktiv"
                message = f"Admin '{admin_name}' sizin {start_date.strftime('%d.%m.%Y')} tarixli təsdiqlənmiş məzuniyyətinizi '{status_az}' etdi."
                create_notification(recipient_id, message, vac_id, cur)
                conn.commit()
            
    except psycopg2.Error as e:
        messagebox.showerror("Baza Xətası", f"Status dəyişdirilərkən xəta baş verdi:\n{e}")
        conn.rollback()
    finally:
        if conn:
            conn.close()

def get_all_active_vacations():
    """Arxivə salınmamış bütün aktiv məzuniyyətləri gətirir."""
    conn = db_connect()
    if not conn: return []
    vacations = []
    try:
        import logging
        logging.debug("get_all_active_vacations başladı")
        
        logging.debug("PostgreSQL rejimində çalışır")
        with conn.cursor() as cur:
                cur.execute("""
                    SELECT v.employee_id, e.name, v.start_date, v.end_date 
                    FROM vacations v
                    JOIN employees e ON v.employee_id = e.id
                    WHERE v.is_archived = FALSE AND v.status = 'approved' AND v.is_inactive = FALSE
                """)
                for row in cur.fetchall():
                    vacation_data = {
                        'employee_id': row[0],
                        'employee': row[1],
                        'employee_name': row[1],  # employee_name də əlavə edirik
                        'start_date': row[2],
                        'end_date': row[3]
                    }
                    vacations.append(vacation_data)
                    logging.debug(f"PostgreSQL məzuniyyət: {vacation_data}")
        
        logging.debug(f"get_all_active_vacations nəticəsi: {len(vacations)} məzuniyyət tapıldı")
        return vacations
    except Exception as e:
        import logging
        logging.error(f"get_all_active_vacations xətası: {e}")
        messagebox.showerror("Baza Xətası", f"Bütün məzuniyyətlər alınarkən xəta baş verdi:\n{e}")
        return []
    finally:
        if conn: conn.close()

def get_pending_vacation_requests(user_id=None):
    """
    Gözləmədə olan məzuniyyət sorğularını gətirir.
    Admin üçün hamısını (user_id=None), istifadəçi üçün isə yalnız özününkünü gətirir.
    """
    conn = db_connect()
    if not conn:
        return []
    
    requests = []
    try:
        # PostgreSQL üçün emal
            # SQL sorğusunun əsas hissəsi
            sql = """
                SELECT v.employee_id, e.name, v.start_date, v.end_date 
                FROM vacations v
                JOIN employees e ON v.employee_id = e.id
                WHERE v.status = 'pending'
            """
            params = []

            # Əgər funksiyaya user_id göndərilibsə, sorğuya şərt əlavə et
            if user_id:
                sql += " AND v.employee_id = ?"
                params.append(user_id)
            
            sql += " ORDER BY v.created_at ASC"
            cursor = conn.execute(sql, params)

            for row in cursor.fetchall():
                requests.append({
                    'employee_id': row[0],
                    'employee': row[1],
                    'start_date': row[2],
                    'end_date': row[3]
                })
        else:
            with conn.cursor() as cur:
                # SQL sorğusunun əsas hissəsi
                sql = """
                    SELECT v.employee_id, e.name, v.start_date, v.end_date 
                    FROM vacations v
                    JOIN employees e ON v.employee_id = e.id
                    WHERE v.status = 'pending'
                """
                params = []

                # Əgər funksiyaya user_id göndərilibsə, sorğuya şərt əlavə et
                if user_id:
                    sql += " AND v.employee_id = %s"
                    params.append(user_id)
                
                sql += " ORDER BY v.created_at ASC"
                cur.execute(sql, tuple(params))

                for row in cur.fetchall():
                    requests.append({
                        'employee_id': row[0],
                        'employee': row[1],
                        'start_date': row[2],
                        'end_date': row[3]
                    })
        return requests
    except Exception as e:
        messagebox.showerror("Baza Xətası", f"Gözləmədə olan sorğular alınarkən xəta baş verdi:\n{e}")
        return []
    finally:
        if conn: conn.close()