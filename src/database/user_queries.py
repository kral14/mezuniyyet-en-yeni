# database/user_queries.py (DÜZƏLDİLMİŞ VƏ YEKUN VERSİYA)

import bcrypt
import psycopg2
# SQLite import silindi
from tkinter import messagebox
from .connection import db_connect, _active_connection_params
from .session_queries import get_active_session_counts

# --- VERSİYA FUNKSİYASI ---
def get_latest_version():
    """Verilənlər bazasından proqramın ən son versiyasını gətirir."""
    conn = db_connect()
    if not conn:
        return None
        
    try:
        with conn.cursor() as cur:
            # Cədvəlin mövcudluğunu yoxla
            cur.execute(
                """
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                      AND table_name = 'app_version'
                )
                """
            )
            table_exists = cur.fetchone()[0]
            if not table_exists:
                cur.execute(
                    """
                    CREATE TABLE app_version (
                        id INTEGER PRIMARY KEY,
                        latest_version TEXT NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                    """
                )
                cur.execute(
                    "INSERT INTO app_version (id, latest_version) VALUES (1, '6.8-final-unified-tkinter')"
                )
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

def get_user_for_login(username):
    """Giriş üçün istifadəçi məlumatlarını və maksimum sessiya sayını gətirir."""
    conn = db_connect()
    if not conn: return None
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id, name, password_hash, role, total_vacation_days, max_sessions FROM employees WHERE username = %s AND is_active = TRUE",
                (username,)
            )
            return cur.fetchone()
    except psycopg2.Error as e:
        messagebox.showerror("Baza Xətası", f"Giriş zamanı xəta: {e}")
        return None
    finally:
        if conn: conn.close()

def get_user_by_id(user_id):
    """İstifadəçi məlumatlarını ID-yə görə gətirir."""
    conn = db_connect()
    if not conn: return None
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, name, username, role, total_vacation_days, max_sessions, 
                       email, first_name, last_name, father_name, phone_number, birth_date, 
                       position, department, hire_date, salary, address, emergency_contact, profile_image,
                       fin_code, department_id, position_id
                FROM employees WHERE id = %s AND is_active = TRUE
                """,
                (user_id,)
            )
            row = cur.fetchone()
            if row:
                return {
                    'id': row[0], 'name': row[1], 'username': row[2], 'role': row[3],
                    'total_vacation_days': row[4], 'max_sessions': row[5], 'email': row[6],
                    'first_name': row[7], 'last_name': row[8], 'father_name': row[9],
                    'phone_number': row[10], 'birth_date': row[11], 'position': row[12],
                    'department': row[13], 'hire_date': row[14], 'salary': row[15], 'address': row[16],
                    'emergency_contact': row[17], 'profile_image': row[18], 'fin_code': row[19],
                    'department_id': row[20], 'position_id': row[21]
                }
            return None
    except psycopg2.Error as e:
        print(f"İstifadəçi məlumatları yüklənərkən xəta: {e}")
        return None
    finally:
        if conn: conn.close()

def update_user_profile(user_id, user_data):
    """İstifadəçi profil məlumatlarını yeniləyir."""
    conn = db_connect()
    if not conn: return False
    try:
        # Boş string-ləri None-a çevir (PostgreSQL üçün)
        def clean_value(value):
            if value == '' or value is None:
                return None
            return value
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE employees SET 
                    first_name = %s, last_name = %s, father_name = %s,
                    email = %s, phone_number = %s, birth_date = %s,
                    address = %s, position = %s, department = %s,
                    hire_date = %s, salary = %s, profile_image = %s,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = %s
                """,
                (
                    clean_value(user_data.get('first_name')),
                    clean_value(user_data.get('last_name')),
                    clean_value(user_data.get('father_name')),
                    clean_value(user_data.get('email')),
                    clean_value(user_data.get('phone_number')),
                    clean_value(user_data.get('birth_date')),
                    clean_value(user_data.get('address')),
                    clean_value(user_data.get('position')),
                    clean_value(user_data.get('department')),
                    clean_value(user_data.get('hire_date')),
                    clean_value(user_data.get('salary')),
                    clean_value(user_data.get('profile_image')),
                    user_id,
                ),
            )
            conn.commit()
            return True
    except psycopg2.Error as e:
        print(f"İstifadəçi profil yeniləmə xətası: {e}")
        return False
    finally:
        if conn: conn.close()

def create_new_user(name, username, password, role='user', total_days=30, max_sessions=1, email=None, first_name=None, last_name=None, father_name=None, phone_number=None, birth_date=None, fin_code=None, department_id=None, position_id=None, hire_date=None, salary=None, address=None, emergency_contact=None):
    """Yeni istifadəçi yaradır."""
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    conn = db_connect()
    if not conn: return False
    try:
        # İstifadəçi adı və email yoxlaması
        with conn.cursor() as cur:
            if username:
                cur.execute("SELECT id FROM employees WHERE username = %s", (username,))
                if cur.fetchone():
                    messagebox.showerror("Xəta", f"'{username}' istifadəçi adı artıq mövcuddur.")
                    return False
            
            if email and email.strip():
                cur.execute("SELECT id FROM employees WHERE email = %s", (email,))
                if cur.fetchone():
                    messagebox.showerror("Xəta", f"'{email}' email ünvanı artıq istifadə olunur.")
                    return False
        
        # PostgreSQL üçün yeni sütunları əlavə et (əgər yoxdursa)
        # Əvvəlcə mövcud sütunları yoxlayırıq
        with conn.cursor() as cur:
            cur.execute("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'employees' AND table_schema = 'public'
            """)
            existing_columns = [row[0] for row in cur.fetchall()]
            
            new_columns = [
                ("email", "TEXT"),
                ("first_name", "TEXT"),
                ("last_name", "TEXT"),
                ("father_name", "TEXT"),
                ("phone_number", "TEXT"),
                ("birth_date", "DATE"),
                ("profile_image", "TEXT"),
                ("fin_code", "TEXT"),
                ("department_id", "INTEGER"),
                ("position_id", "INTEGER"),
                ("hire_date", "DATE"),
                ("salary", "REAL"),
                ("address", "TEXT"),
                ("emergency_contact", "TEXT"),
                ("updated_at", "TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
            ]
            
            # Yalnız mövcud olmayan sütunları əlavə edirik
            columns_to_add = [col for col in new_columns if col[0] not in existing_columns]
            
            if columns_to_add:
                for column_name, column_type in columns_to_add:
                    try:
                        cur.execute(f"ALTER TABLE employees ADD COLUMN {column_name} {column_type}")
                        print(f"✅ {column_name} sütunu PostgreSQL cədvəlinə əlavə edildi")
                    except psycopg2.errors.DuplicateColumn:
                        # Sütun artıq mövcuddur
                        pass
                
                # Sütun əlavə etmə əməliyyatlarını commit edirik
                conn.commit()
            else:
                print("✅ Bütün sütunlar artıq mövcuddur")
        
        # İndi yeni istifadəçini əlavə edirik
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO employees (
                    name, username, password_hash, role, total_vacation_days, max_sessions, 
                    email, first_name, last_name, father_name, phone_number, birth_date, 
                    fin_code, department_id, position_id, hire_date, salary, address, emergency_contact
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                name, username, hashed_password.decode('utf-8'), role, total_days, max_sessions,
                email, first_name, last_name, father_name, phone_number, birth_date,
                fin_code, department_id, position_id, hire_date, salary, address, emergency_contact
            ))
            # INSERT əməliyyatını commit edirik
            conn.commit()
        return True
    except psycopg2.IntegrityError:
        messagebox.showerror("Xəta", "Bu istifadəçi adı artıq mövcuddur.")
        return False
    except psycopg2.Error as e:
        messagebox.showerror("Baza Xətası", f"Qeydiyyat zamanı xəta: {e}")
        return False
    finally:
        if conn: conn.close()

def update_employee(emp_id, new_name, total_days, max_sessions):
    """İşçi məlumatını yeniləyir."""
    conn = db_connect()
    if not conn: return
    try:
        with conn.cursor() as cur:
            cur.execute("UPDATE employees SET name = %s, total_vacation_days = %s, max_sessions = %s WHERE id = %s", (new_name, total_days, max_sessions, emp_id))
        conn.commit()
    except psycopg2.Error as e:
        messagebox.showerror("Baza Xətası", f"İşçi məlumatını yeniləyərkən xəta: \n{e}")
    finally:
        if conn: conn.close()

def delete_employee(emp_id):
    """(YENİ ƏLAVƏ EDİLDİ) İşçini verilənlər bazasından silir."""
    conn = db_connect()
    if not conn: return
    try:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM employees WHERE id = %s", (emp_id,))
        conn.commit()
    except psycopg2.Error as e:
        messagebox.showerror("Baza Xətası", f"İşçini silərkən xəta: \n{e}")
    finally:
        if conn: conn.close()

def set_user_activity(user_id, new_status):
    """İstifadəçinin aktiv statusunu dəyişir."""
    conn = db_connect()
    if not conn: return False
    try:
        with conn.cursor() as cur:
            cur.execute("UPDATE employees SET is_active = %s WHERE id = %s", (new_status, user_id))
        conn.commit()
        return True
    except psycopg2.Error as e:
        messagebox.showerror("Baza Xətası", f"Status dəyişdirilərkən xəta: {e}")
        return False
    finally:
        if conn: conn.close()

def update_user_password(user_id, new_password):
    """İstifadəçinin şifrəsini dəyişir."""
    conn = db_connect()
    if not conn: return False
    try:
        # Yeni şifrəni hash et
        hashed_password = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt())
        
        with conn.cursor() as cur:
            cur.execute("UPDATE employees SET password_hash = %s WHERE id = %s", 
                       (hashed_password.decode('utf-8'), user_id))
        conn.commit()
        return True
    except psycopg2.Error as e:
        messagebox.showerror("Baza Xətası", f"Şifrə dəyişdirilərkən xəta: {e}")
        return False
    finally:
        if conn: conn.close()

def reset_user_password(username, new_password):
    """İstifadəçi adına görə şifrəni sıfırlayır."""
    conn = db_connect()
    if not conn: return False
    try:
        # Yeni şifrəni hash et
        hashed_password = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt())
        
        with conn.cursor() as cur:
            cur.execute("UPDATE employees SET password_hash = %s WHERE username = %s", 
                       (hashed_password.decode('utf-8'), username))
        conn.commit()
        return True
    except psycopg2.Error as e:
        messagebox.showerror("Baza Xətası", f"Şifrə sıfırlanarkən xəta: {e}")
        return False
    finally:
        if conn: conn.close()

def check_if_name_exists(name):
    """(YENİ ƏLAVƏ EDİLDİ) Verilmiş adla işçinin mövcud olub-olmadığını yoxlayır."""
    conn = db_connect()
    if not conn: return False
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT 1 FROM employees WHERE name = %s", (name,))
            return cur.fetchone() is not None
    except psycopg2.Error as e:
        messagebox.showerror("Baza Xətası", f"Ad yoxlanarkən xəta baş verdi:\n{e}")
        return False
    finally:
        if conn: conn.close()
        
def load_data_for_user(current_user):
    """İstifadəçi roluna uyğun olaraq məlumatları gətirir."""
    conn = db_connect()
    if not conn: return {}
    data = {}
    active_sessions = get_active_session_counts()
    try:
        # PostgreSQL üçün bütün məlumatları bir cursor ilə alırıq
        with conn.cursor() as cur:
            # İşçi məlumatları
            if current_user['role'].strip() == 'admin':
                # Admin bütün işçiləri görə bilər
                cur.execute("""
                    SELECT id, name, total_vacation_days, is_active, max_sessions,
                           first_name, last_name, father_name, email, phone_number,
                           birth_date, address, position, department, hire_date, salary, profile_image, role, username
                    FROM employees 
                    WHERE hide IS NULL OR hide = FALSE 
                    ORDER BY name
                """)
            else:
                # Adi istifadəçi yalnız öz məlumatını görə bilər
                cur.execute("""
                    SELECT id, name, total_vacation_days, is_active, max_sessions,
                           first_name, last_name, father_name, email, phone_number,
                           birth_date, address, position, department, hire_date, salary, profile_image, role, username
                    FROM employees 
                    WHERE id = %s AND (hide IS NULL OR hide = FALSE)
                """, (current_user['id'],))
            
            employees = cur.fetchall()
            for emp in employees:
                emp_id, name, total_days, is_active, max_sessions, first_name, last_name, father_name, email, phone_number, birth_date, address, position, department, hire_date, salary, profile_image, role, username = emp
                
                data[name] = {
                    "db_id": emp_id,
                    "umumi_gun": total_days or 30,  # Default 30 gün
                    "is_active": is_active,
                    "max_sessions": max_sessions,
                    "active_session_count": active_sessions.get(emp_id, 0),
                    "goturulen_icazeler": [],
                    # Əlavə məlumatlar
                    "first_name": first_name or "",
                    "last_name": last_name or "",
                    "father_name": father_name or "",
                    "email": email or "",
                    "phone_number": phone_number or "",
                    "birth_date": birth_date.strftime('%Y-%m-%d') if birth_date else "",
                    "address": address or "",
                    "position": position or "",
                    "department": department or "",
                    "hire_date": hire_date.strftime('%Y-%m-%d') if hire_date else "",
                    "salary": salary or "",
                    "profile_image": profile_image or "",
                    "role": role or "user",
                    "username": username or ""
                }
            
            # Məzuniyyət məlumatları
            if current_user['role'].strip() == 'admin':
                # Admin bütün məzuniyyətləri görə bilər
                cur.execute("""
                    SELECT id, employee_id, start_date, end_date, note, is_inactive, created_at, status 
                    FROM vacations 
                    WHERE is_archived = FALSE 
                    ORDER BY start_date
                """)
            else:
                # Adi istifadəçi yalnız öz məzuniyyətlərini görə bilər
                cur.execute("""
                    SELECT id, employee_id, start_date, end_date, note, is_inactive, created_at, status 
                    FROM vacations 
                    WHERE employee_id = %s AND is_archived = FALSE 
                    ORDER BY start_date
                """, (current_user['id'],))
            
            vacations = cur.fetchall()

        # Məzuniyyət məlumatlarını emal edirik
        for vac_id, emp_id, start, end, note, inactive, created, status in vacations:
            for emp_name, emp_data in data.items():
                if emp_data["db_id"] == emp_id:
                    emp_data["goturulen_icazeler"].append({
                        "db_id": vac_id, "baslama": start, "bitme": end,
                        "qeyd": note, "aktiv_deyil": inactive,
                        "yaradilma_tarixi": created, "status": status
                    }); break
    except psycopg2.Error as e:
        messagebox.showerror("Baza Oxuma Xətası", "verilenler bazasi ile elaqe kesildi zehmet olmasa internete qosulmani yoxlayin")
    finally:
        if conn: conn.close()
    return data

def get_employee_by_email(email):
    """Email ünvanına görə işçi məlumatını gətirir."""
    conn = db_connect()
    if not conn: return None
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT id, name, username, email FROM employees WHERE email = %s AND is_active = TRUE", (email,))
            result = cur.fetchone()
            if result:
                return {
                    'id': result[0],
                    'name': result[1],
                    'username': result[2],
                    'email': result[3]
                }
        return None
    except psycopg2.Error as e:
        print(f"Email ilə işçi axtararkən xəta: {e}")
        return None
    finally:
        if conn: conn.close()