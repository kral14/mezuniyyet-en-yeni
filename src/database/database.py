# database.py (Giriş Tarixçəsi funksiyası əlavə edilmiş tam versiya)

import psycopg2
import bcrypt
import logging
# messagebox import silindi - thread-safe deyil, exception fırlatmaq lazımdır
from datetime import date, datetime
import uuid # Sessiya ID-ləri üçün
import os
from utils.text_formatter import format_name, format_full_name

# Logging səviyyəsini ERROR-a təyin edirik - performans üçün
logging.getLogger().setLevel(logging.ERROR)

# Realtime debug sistemi - şərti import
try:
    try:
        from utils.realtime_debug import log_signal_sent, log_error
    except ImportError:
        from src.utils.realtime_debug import log_signal_sent, log_error
except ImportError:
    # Əgər debug modulu tapılmazsa, boş funksiyalar yaradırıq
    def log_signal_sent(*args, **kwargs): pass
    def log_error(*args, **kwargs): pass

# Dinamik connection string idarəetməsi
_connection_string = None

def clear_connection_params():
    """Clear connection string from memory (təhlükəsizlik üçün)"""
    global _connection_string
    _connection_string = None
    logging.info("Database konfiqurasiyası yaddaşdan təmizləndi")

def set_connection_params(connection_string):
    """Connection string-i təyin edir"""
    global _connection_string
    _connection_string = connection_string
    # Təhlükəsizlik: Connection string log-larda göstərilmir
    logging.info("Database konfiqurasiyası təyin edildi")
    
    # connection.py moduluna da göndər (yalnız düzgün formatda connection string-lər üçün)
    if connection_string and '://' in connection_string:
        try:
            from .connection import set_connection_params as set_conn_params
            set_conn_params(connection_string)
        except ImportError:
            logging.warning("connection.py modulu tapılmadı")
        except Exception as e:
            logging.warning(f"connection.py moduluna göndərmə xətası: {e}")

def get_connection_params():
    """Connection string-i qaytarır"""
    global _connection_string
    if _connection_string:
        # Təhlükəsizlik: Connection string log-larda göstərilmir
        logging.debug("Database konfiqurasiyası qaytarılır")
        return _connection_string
    
    # connection.py modulundan da yoxla
    try:
        from .connection import _active_connection_params
        if _active_connection_params and "connection_string" in _active_connection_params:
            conn_str = _active_connection_params["connection_string"]
            # Təhlükəsizlik: Connection string log-larda göstərilmir
            logging.debug("Database konfiqurasiyası connection.py-dən alındı")
            return conn_str
    except ImportError:
        logging.warning("connection.py modulu tapılmadı")
    
    # Default connection string (əgər təyin edilməyibsə)
    # Təhlükəsizlik üçün hardcoded məlumatlar silindi
    # Connection string tenant sistemi vasitəsilə alınmalıdır
    logging.warning("Database konfiqurasiyası təyin edilməyib. Tenant sistemi vasitəsilə alınmalıdır.")
    return None

def db_connect():
    """Veritabanına qoşulur"""
    try:
        # DEBUG: Connection cəhdi başladı - debug mesajlarını azaldıq
        # log_signal_sent("database_connection_attempt", {}, "database")
        
        # Əvvəlcə öz connection string-imizlə cəhd et
        conn_string = get_connection_params()
        if conn_string:
            # Təhlükəsizlik: Database konfiqurasiyası log-larda göstərilmir
            logging.info("Veritabanına qoşulma cəhdi başladı")
            # Connection timeout əlavə edirik
            if 'postgresql' in conn_string:
                conn = psycopg2.connect(conn_string, connect_timeout=10)
            else:
                conn = psycopg2.connect(conn_string)
            logging.info("Veritabanına uğurla qoşuldu")
            
            # DEBUG: Uğurlu connection - debug mesajlarını azaldıq
            # log_signal_sent("database_connection_success", {"method": "direct"}, "database")
            
            return conn
        
        # Əgər öz connection string-imiz yoxdursa, connection.py modulundan cəhd et
        try:
            from .connection import db_connect as conn_connect
            conn = conn_connect()
            if conn:
                logging.info("connection.py modulu vasitəsilə baza qoşulması uğurlu oldu")
                
                # DEBUG: Uğurlu connection - debug mesajlarını azaldıq
                # log_signal_sent("database_connection_success", {"method": "connection_module"}, "database")
                
                return conn
        except ImportError:
            logging.warning("connection.py modulu tapılmadı")
        except Exception as e:
            logging.warning(f"connection.py modulu ilə qoşulma xətası: {e}")
        
        # DEBUG: Connection string tapılmadı
        log_error("connection_string_not_found", "Connection string təyin edilməyib", None, "database")
        
        logging.warning("Database konfiqurasiyası təyin edilməyib. Tenant sistemi vasitəsilə alınmalıdır.")
        return None
    except psycopg2.OperationalError as e:
        # DEBUG: Operational xəta
        log_error("database_operational_error", f"Veritabanı qoşulma xətası: {e}", None, "database")
        logging.warning(f"Veritabanı qoşulma xətası: {e}")
        return None
    except psycopg2.Error as e:
        # DEBUG: Digər PostgreSQL xətaları
        log_error("database_error", f"PostgreSQL xətası: {e}", None, "database")
        logging.error(f"PostgreSQL xətası: {e}")
        return None
    except Exception as e:
        # DEBUG: Gözlənilməyən xəta
        log_error("database_unexpected_error", f"Gözlənilməyən qoşulma xətası: {e}", None, "database")
        logging.warning(f"Gözlənilməyən qoşulma xətası: {e}")
        return None

# --- ÇATIŞMAYAN FUNKSİYALAR ƏLAVƏ EDİLİR ---

def get_all_active_vacations():
    """Arxivə salınmamış bütün aktiv məzuniyyətləri gətirir."""
    import logging
    logging.debug("get_all_active_vacations çağırıldı")
    
    # PostgreSQL cəhd et
    logging.debug("PostgreSQL cəhd edirik...")
    conn = db_connect()
    if conn:
        vacations = []
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT v.employee_id, e.name, v.start_date, v.end_date 
                    FROM vacations v
                    JOIN employees e ON v.employee_id = e.id
                    WHERE v.is_archived = FALSE AND v.status = 'approved' AND v.is_inactive = FALSE
                """)
                for row in cur.fetchall():
                    vacations.append({
                        'employee_id': row[0],
                        'employee': row[1],  # name sütununu employee kimi qaytarırıq
                        'employee_name': row[1],  # employee_name də əlavə edirik
                        'start_date': row[2],
                        'end_date': row[3]
                    })
            logging.debug(f"PostgreSQL bazasından {len(vacations)} məzuniyyət tapıldı")
            return vacations
        except Exception as e:
            logging.warning(f"PostgreSQL bazasından məzuniyyət alınarkən xəta: {e}")
        finally:
            if conn: conn.close()
    
    # Hər iki baza da işləmirsə boş list qaytar
    logging.warning("Heç bir baza işləmir, boş list qaytarılır")
    return []

# SQLite funksiyası silindi

def get_pending_vacation_requests(user_id=None):
    """
    Gözləmədə olan məzuniyyət sorğularını gətirir.
    Admin üçün hamısını (user_id=None), istifadəçi üçün isə yalnız özününkünü gətirir.
    """
    conn = db_connect()
    if not conn: return []
    
    requests = []
    try:
        with conn.cursor() as cur:
            sql = """
                SELECT v.employee_id, e.name, v.start_date, v.end_date 
                FROM vacations v
                JOIN employees e ON v.employee_id = e.id
                WHERE v.status = 'pending'
            """
            params = []

            if user_id:
                sql += " AND v.employee_id = %s"
                params.append(user_id)
            
            sql += " ORDER BY v.created_at ASC"
            cur.execute(sql, tuple(params))

            for row in cur.fetchall():
                requests.append({
                    'employee_id': row[0],
                    'employee_name': row[1],  # name sütununu employee_name kimi qaytarırıq
                    'start_date': row[2],
                    'end_date': row[3]
                })
        return requests
    except Exception as e:
        messagebox.showerror("Baza Xətası", f"Gözləmədə olan sorğular alınarkən xəta baş verdi:\n{e}")
        return []
    finally:
        if conn: conn.close()

def get_active_user_details():
    """Aktiv istifadəçilərin detallı məlumatlarını gətirir."""
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
            LEFT JOIN login_history lh ON l.user_id = lh.user_id AND l.last_login = lh.login_time
            """
            cur.execute(sql)
            for row in cur.fetchall():
                users.append({
                    'user_id': row[0], 'username': row[1], 'name': row[2],
                    'ip_address': row[3], 'login_time': row[4]
                })
    except Exception as e:
        messagebox.showerror("Baza Xətası", f"Aktiv istifadəçilərin məlumatları alınarkən xəta baş verdi:\n{e}")
    finally:
        if conn: conn.close()
    return users

# --- SESSİYA (SESSION) FUNKSİYALARI ---
def add_user_session(user_id, ip_address="127.0.0.1"):
    """Verilən istifadəçi üçün yeni sessiya yaradır və sessiya ID-sini qaytarır."""
    conn = db_connect()
    if not conn: return None, None
    session_id = str(uuid.uuid4())
    login_history_id = None
    try:
        with conn.cursor() as cur:
            # Login history yaradırıq
            cur.execute("INSERT INTO login_history (user_id, login_time) VALUES (%s, NOW()) RETURNING id", (user_id,))
            login_history_id = cur.fetchone()[0]
            
            # Aktiv sessiya yaradırıq
            cur.execute("INSERT INTO active_sessions (session_id, user_id, ip_address) VALUES (%s, %s, %s)", 
                      (session_id, user_id, ip_address))
            conn.commit()
        return session_id, login_history_id
    except psycopg2.Error as e:
        messagebox.showerror("Baza Xətası", f"Sessiya yaradılarkən xəta: \n{e}")
        return None, None
    finally:
        if conn: conn.close()

def remove_user_session(session_id, login_history_id):
    """Verilən sessiyanı silir."""
    if not session_id: return
    conn = db_connect()
    if not conn: return
    try:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM active_sessions WHERE session_id = %s", (str(session_id),))
            
            # Logout vaxtını qeyd edirik
            if login_history_id:
                cur.execute("UPDATE login_history SET logout_time = NOW() WHERE id = %s", (login_history_id,))
            
            conn.commit()
    except psycopg2.Error as e:
        messagebox.showerror("Baza Xətası", f"Sessiya silinərkən xəta: \n{e}")
    finally:
        if conn: conn.close()

def get_active_session_counts():
    """Hər bir istifadəçinin aktiv sessiya sayını qaytarır."""
    conn = db_connect()
    if not conn: return {}
    counts = {}
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT user_id, COUNT(*) FROM active_sessions GROUP BY user_id")
            for user_id, count in cur.fetchall():
                counts[user_id] = count
    except psycopg2.Error as e:
        messagebox.showerror("Baza Xətası", f"Aktiv sessiyalar alınarkən xəta: \n{e}")
    finally:
        if conn: conn.close()
    return counts

# --- BİLDİRİŞ FUNKSİYALARI ---
def get_unread_notifications_for_user(user_id):
    """Yalnız oxunmamış bildirişlərin SAYINI qaytarır."""
    conn = db_connect()
    if not conn: return 0
    count = 0
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM notifications WHERE recipient_id = %s AND is_read = FALSE", (user_id,))
            result = cur.fetchone()
            if result: count = result[0]
    except psycopg2.Error as e: messagebox.showerror("Baza Xətası", f"Bildirişləri sayarkən xəta: \n{e}")
    finally:
        if conn: conn.close()
    return count

def get_all_notifications_for_user(user_id):
    """İstifadəçinin bütün bildirişlərini (oxunmuş və oxunmamış) gətirir."""
    conn = db_connect()
    if not conn: return []
    notifications = []
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT n.id, n.message, n.created_at, n.related_vacation_id, v.employee_id, n.is_read
                FROM notifications n
                LEFT JOIN vacations v ON n.related_vacation_id = v.id
                WHERE n.recipient_id = %s ORDER BY n.created_at DESC
            """, (user_id,))
            notifications = cur.fetchall()
    except psycopg2.Error as e: messagebox.showerror("Baza Xətası", f"Bildirişləri oxuyarkən xəta: \n{e}")
    finally:
        if conn: conn.close()
    return notifications

def mark_notifications_as_read(notification_ids):
    if not notification_ids: return
    conn = db_connect()
    if not conn: return
    try:
        with conn.cursor() as cur:
            cur.execute("UPDATE notifications SET is_read = TRUE WHERE id IN %s", (tuple(notification_ids),))
            conn.commit()
    except psycopg2.Error as e: messagebox.showerror("Baza Xətası", f"Bildirişləri yeniləyərkən xəta: \n{e}")
    finally:
        if conn: conn.close()

def delete_notifications(notification_ids):
    if not notification_ids: return
    conn = db_connect()
    if not conn: return
    try:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM notifications WHERE id IN %s", (tuple(notification_ids),))
            conn.commit()
            messagebox.showinfo("Uğurlu", f"{len(notification_ids)} bildiriş uğurla silindi.", parent=None)
    except psycopg2.Error as e: messagebox.showerror("Baza Xətası", f"Bildirişləri silərkən xəta baş verdi: \n{e}")
    finally:
        if conn: conn.close()

def create_notification(recipient_id, message, related_vacation_id, cursor):
    cursor.execute("INSERT INTO notifications (recipient_id, message, related_vacation_id) VALUES (%s, %s, %s)", (recipient_id, message, related_vacation_id))

# --- İSTİFADƏÇİ (EMPLOYEE) FUNKSİYALARI ---
def get_user_for_login(username):
    """Giriş üçün istifadəçi məlumatlarını və maksimum sessiya sayını gətirir."""
    conn = db_connect()
    if not conn: 
        logging.warning(f"İstifadəçi {username} üçün baza qoşulması uğursuz oldu - offline rejimə keçirik")
        # Offline rejimə keçirik
        try:
            from .offline_db import authenticate_offline
            offline_user = authenticate_offline(username, "")
            if offline_user:
                # Offline mode - return placeholder tuple to match expected format
                return (offline_user.get('id', 0), offline_user.get('name', username), 
                        offline_user.get('password_hash', ''), offline_user.get('role', 'user'), 
                        30, 1)  # Default 30 days, max 1 session
        except Exception as e:
            logging.warning(f"Offline authentication failed: {e}")
        return None
    user_data = None
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT id, name, password_hash, role, total_vacation_days, max_sessions FROM employees WHERE username = %s AND is_active = TRUE", (username,))
            user_data = cur.fetchone()
            if user_data:
                logging.info(f"İstifadəçi {username} tapıldı")
                # Save user for offline access
                try:
                    from .offline_db import save_user_for_offline
                    password_hash = user_data[2]  # password_hash is at index 2
                    save_user_for_offline(username, password_hash, user_data[1], user_data[3])
                except Exception as e:
                    logging.warning(f"Failed to save user for offline: {e}")
            else:
                logging.warning(f"İstifadəçi {username} tapılmadı")
    except psycopg2.Error as e: 
        logging.error(f"Giriş zamanı xəta: {e}")
    finally:
        if conn: conn.close()
    return user_data

def get_user_by_id(user_id):
    """İstifadəçi məlumatlarını ID-yə görə gətirir."""
    conn = db_connect()
    if not conn: 
        logging.warning(f"İstifadəçi ID {user_id} üçün baza qoşulması uğursuz oldu")
        return None
    user_data = None
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT id, username, name, role, total_vacation_days, max_sessions, is_active FROM employees WHERE id = %s", (user_id,))
            user_data = cur.fetchone()
            if user_data:
                logging.info(f"İstifadəçi ID {user_id} tapıldı")
            else:
                logging.warning(f"İstifadəçi ID {user_id} tapılmadı")
    except psycopg2.Error as e: 
        logging.error(f"İstifadəçi ID {user_id} üçün baza xətası: {e}")
        messagebox.showerror("Baza Xətası", f"İstifadəçi ID {user_id} üçün baza xətası: {e}")
    finally:
        if conn: conn.close()
    return user_data

def update_user_profile(user_id, user_data):
    """İstifadəçi profil məlumatlarını yeniləyir."""
    conn = db_connect()
    if not conn: 
        logging.warning(f"İstifadəçi ID {user_id} üçün baza qoşulması uğursuz oldu")
        return False
    try:
        # Salary sahəsini düzəldirik - boş string əvəzinə None göndəririk
        salary_value = user_data.get('salary', '')
        if salary_value == '' or salary_value is None:
            salary_value = None
        else:
            try:
                salary_value = float(salary_value)
            except (ValueError, TypeError):
                salary_value = None
        
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE employees SET 
                    first_name = %s, last_name = %s, father_name = %s,
                    email = %s, phone_number = %s, birth_date = %s,
                    address = %s, position = %s, department = %s,
                    hire_date = %s, salary = %s, profile_image = %s,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = %s
            """, (
                user_data.get('first_name', ''),
                user_data.get('last_name', ''),
                user_data.get('father_name', ''),
                user_data.get('email', ''),
                user_data.get('phone_number', ''),
                user_data.get('birth_date', ''),
                user_data.get('address', ''),
                user_data.get('position', ''),
                user_data.get('department', ''),
                user_data.get('hire_date', ''),
                salary_value,  # Düzəldilmiş salary dəyəri
                user_data.get('profile_image', ''),
                user_id
            ))
            conn.commit()
            logging.info(f"İstifadəçi ID {user_id} profil məlumatları yeniləndi")
            return True
    except psycopg2.Error as e: 
        logging.error(f"İstifadəçi ID {user_id} profil yeniləmə xətası: {e}")
        messagebox.showerror("Baza Xətası", f"Profil yeniləmə xətası: {e}")
        return False
    finally:
        if conn: conn.close()

def create_new_user(name, username, password, role='user', total_days=30, max_sessions=1, email=None, first_name=None, last_name=None, father_name=None, phone_number=None, birth_date=None, fin_code=None, department_id=None, position_id=None, hire_date=None, salary=None, address=None, emergency_contact=None):
    logging.info(f"💾 [DB] create_new_user çağırıldı: Username={username}, Email={email}")
    print(f"💾 [DB] create_new_user çağırıldı: Username={username}, Email={email}")
    
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    
    logging.info(f"🔌 [DB] Database qoşulması başladı")
    print(f"🔌 [DB] Database qoşulması başladı")
    conn = db_connect()
    if not conn:
        logging.error(f"❌ [DB] Database qoşulması uğursuz oldu")
        print(f"❌ [DB] Database qoşulması uğursuz oldu")
        return False
    
    logging.info(f"✅ [DB] Database qoşulması uğurlu")
    print(f"✅ [DB] Database qoşulması uğurlu")
    
    success = False
    try:
        with conn.cursor() as cur:
            # İstifadəçi adı və email yoxlaması
            if username:
                logging.info(f"🔍 [DB] Username yoxlanılır: {username}")
                print(f"🔍 [DB] Username yoxlanılır: {username}")
                cur.execute("SELECT id FROM employees WHERE username = %s", (username,))
                if cur.fetchone():
                    logging.warning(f"⚠️ [DB] Username artıq mövcuddur: {username}")
                    print(f"⚠️ [DB] Username artıq mövcuddur: {username}")
                    messagebox.showerror("Xəta", f"'{username}' istifadəçi adı artıq mövcuddur.")
                    return False
            
            if email and email.strip():
                logging.info(f"🔍 [DB] Email yoxlanılır: {email}")
                print(f"🔍 [DB] Email yoxlanılır: {email}")
                cur.execute("SELECT id FROM employees WHERE email = %s", (email,))
                if cur.fetchone():
                    logging.warning(f"⚠️ [DB] Email artıq mövcuddur: {email}")
                    print(f"⚠️ [DB] Email artıq mövcuddur: {email}")
                    messagebox.showerror("Xəta", f"'{email}' email ünvanı artıq istifadə olunur.")
                    return False
            
            # Yeni sütunları əlavə et (əgər yoxdursa)
            # Əvvəlcə mövcud sütunları yoxlayırıq
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
        logging.info(f"📝 [DB] INSERT sorgusu hazırlanır: Username={username}, Email={email}")
        print(f"📝 [DB] INSERT sorgusu hazırlanır: Username={username}, Email={email}")
        
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
            logging.info(f"💾 [DB] INSERT commit edilir: Username={username}")
            print(f"💾 [DB] INSERT commit edilir: Username={username}")
            conn.commit()
            logging.info(f"✅ [DB] INSERT uğurlu: Username={username}")
            print(f"✅ [DB] INSERT uğurlu: Username={username}")
        
        # Cache-i etibarsız et
        try:
            try:
                from utils import cache
            except ImportError:
                from src.utils import cache
            cache.invalidate_cache()
            logging.info("Yeni istifadəçi yaradıldı - cache etibarsız edildi")
        except Exception as cache_error:
            logging.warning(f"Cache etibarsız etmə xətası: {cache_error}")
            
        success = True
        logging.info(f"✅ [DB] create_new_user uğurlu: Username={username}, Email={email}")
        print(f"✅ [DB] create_new_user uğurlu: Username={username}, Email={email}")
    except psycopg2.IntegrityError as e:
        logging.error(f"❌ [DB] IntegrityError: {e}, Username={username}, Email={email}")
        print(f"❌ [DB] IntegrityError: {e}, Username={username}, Email={email}")
        messagebox.showerror("Xəta", "Bu istifadəçi adı artıq mövcuddur.")
    except psycopg2.Error as e:
        logging.error(f"❌ [DB] PostgreSQL xətası: {e}, Username={username}, Email={email}")
        print(f"❌ [DB] PostgreSQL xətası: {e}, Username={username}, Email={email}")
        import traceback
        logging.error(f"❌ [DB] Traceback: {traceback.format_exc()}")
        print(f"❌ [DB] Traceback: {traceback.format_exc()}")
        messagebox.showerror("Baza Xətası", f"Qeydiyyat zamanı xəta: {e}")
    except Exception as e:
        logging.error(f"❌ [DB] Gözlənilməz xəta: {e}, Username={username}, Email={email}")
        print(f"❌ [DB] Gözlənilməz xəta: {e}, Username={username}, Email={email}")
        import traceback
        logging.error(f"❌ [DB] Traceback: {traceback.format_exc()}")
        print(f"❌ [DB] Traceback: {traceback.format_exc()}")
        messagebox.showerror("Baza Xətası", f"Qeydiyyat zamanı xəta: {e}")
    finally:
        if conn: conn.close()
        logging.info(f"🔌 [DB] Database bağlantısı bağlandı")
        print(f"🔌 [DB] Database bağlantısı bağlandı")
    return success

def update_employee(emp_id, new_name, total_days, max_sessions):
    conn = db_connect()
    if not conn: return False
    try:
        with conn.cursor() as cur:
            cur.execute("UPDATE employees SET name = %s, total_vacation_days = %s, max_sessions = %s WHERE id = %s", (new_name, total_days, max_sessions, emp_id))
        conn.commit()
        
        # Cache-i etibarsız et
        try:
            try:
                from utils import cache
            except ImportError:
                from src.utils import cache
            cache.invalidate_cache()
            logging.info("İşçi məlumatları yeniləndi - cache etibarsız edildi")
        except Exception as cache_error:
            logging.warning(f"Cache etibarsız etmə xətası: {cache_error}")
            
        return True
    except psycopg2.Error as e: messagebox.showerror("Baza Xətası", f"İşçi yenilənərkən xəta: {e}")
    finally:
        if conn: conn.close()
    return False

def update_employee_full(emp_id, employee_data):
    """İşçinin bütün məlumatlarını yeniləyir"""
    print(f"DEBUG: update_employee_full çağırıldı - emp_id: {emp_id}, employee_data: {employee_data}")
    conn = db_connect()
    if not conn: 
        print("DEBUG: Veritabanına qoşulma uğursuz")
        return False
    print("DEBUG: Veritabanına qoşuldu")
    try:
        with conn.cursor() as cur:
            # Salary sahəsini düzəldirik - boş string əvəzinə None göndəririk
            salary_value = employee_data.get('salary', '')
            if salary_value == '' or salary_value is None:
                salary_value = None
            else:
                try:
                    salary_value = float(salary_value)
                except (ValueError, TypeError):
                    salary_value = None
            
            # Əsas məlumatları yenilə
            # department_id və position_id dəyərlərini düzəldirik
            department_id = employee_data.get('department_id')
            if department_id == '' or department_id is None:
                department_id = None
            else:
                try:
                    department_id = int(department_id)
                except (ValueError, TypeError):
                    department_id = None
            
            position_id = employee_data.get('position_id')
            if position_id == '' or position_id is None:
                position_id = None
            else:
                try:
                    position_id = int(position_id)
                except (ValueError, TypeError):
                    position_id = None
            
            # Şöbə və vəzifənin adlarını da tapırıq ki, mətn sütunları sinxron olsun
            department_name = None
            position_name = None
            try:
                if department_id is not None:
                    cur.execute("SELECT name FROM departments WHERE id = %s", (department_id,))
                    row = cur.fetchone()
                    if row: department_name = row[0]
                if position_id is not None:
                    cur.execute("SELECT name FROM positions WHERE id = %s", (position_id,))
                    row = cur.fetchone()
                    if row: position_name = row[0]
            except Exception:
                # Cədvəllər mövcud deyilsə, bu addımı səssiz keçirik
                department_name = None
                position_name = None

            # Tam ad sütununu da yeniləyirik
            first_name = employee_data.get('first_name', '').strip()
            last_name = employee_data.get('last_name', '').strip()
            full_name = format_full_name(first_name, last_name)

            update_values = (
                full_name,
                employee_data.get('first_name', ''),
                employee_data.get('last_name', ''),
                employee_data.get('father_name', ''),
                employee_data.get('email', ''),
                employee_data.get('phone_number', ''),
                employee_data.get('birth_date') if employee_data.get('birth_date') else None,
                employee_data.get('address', ''),
                department_name,
                position_name,
                employee_data.get('fin_code', ''),
                department_id,  # Düzəldilmiş department_id
                position_id,    # Düzəldilmiş position_id
                employee_data.get('hire_date') if employee_data.get('hire_date') else None,
                salary_value,  # Düzəldilmiş salary dəyəri
                employee_data.get('profile_image', ''),
                emp_id
            )
            
            print(f"DEBUG: SQL sorğu dəyərləri: {update_values}")
            print(f"DEBUG: department_id: {department_id}, position_id: {position_id}")
            
            # SQL sorğusunu icra etməzdən əvvəl işçinin mövcud məlumatlarını yoxla
            cur.execute("SELECT first_name, last_name, department_id, position_id, fin_code FROM employees WHERE id = %s", (emp_id,))
            old_data = cur.fetchone()
            print(f"DEBUG: Köhnə məlumatlar: {old_data}")
            
            cur.execute("""
                UPDATE employees SET 
                    name = %s,
                    first_name = %s, last_name = %s, father_name = %s,
                    email = %s, phone_number = %s, birth_date = %s,
                    address = %s, department = %s, position = %s,
                    fin_code = %s, department_id = %s, position_id = %s,
                    hire_date = %s, salary = %s, profile_image = %s
                WHERE id = %s
            """, update_values)
            
            print(f"DEBUG: SQL sorğu icra edildi. Dəyişdirilən sətirlər: {cur.rowcount}")
            
            # Yenilənmiş məlumatları yoxla
            cur.execute("SELECT first_name, last_name, department_id, position_id, fin_code FROM employees WHERE id = %s", (emp_id,))
            new_data = cur.fetchone()
            print(f"DEBUG: Yeni məlumatlar: {new_data}")
            
        conn.commit()
        print(f"DEBUG: Veritabanı commit edildi")
        
        # Cache-i etibarsız et
        try:
            try:
                from utils import cache
            except ImportError:
                from src.utils import cache
            cache.invalidate_cache()
            logging.info("İşçi məlumatları tam yeniləndi - cache etibarsız edildi")
        except Exception as cache_error:
            logging.warning(f"Cache etibarsız etmə xətası: {cache_error}")
            
        return True
    except psycopg2.Error as e: 
        logging.error(f"İşçi məlumatları yenilənərkən xəta: {e}")
        messagebox.showerror("Baza Xətası", f"İşçi məlumatları yenilənərkən xəta: {e}")
    finally:
        if conn: conn.close()
    return False

def delete_employee(emp_id):
    conn = db_connect()
    if not conn: return False
    try:
        with conn.cursor() as cur:
            cur.execute("UPDATE employees SET is_active = FALSE WHERE id = %s", (emp_id,))
        conn.commit()
        
        # Cache-i etibarsız et
        try:
            try:
                from utils import cache
            except ImportError:
                from src.utils import cache
            cache.invalidate_cache()
            logging.info("İşçi deaktiv edildi - cache etibarsız edildi")
        except Exception as cache_error:
            logging.warning(f"Cache etibarsız etmə xətası: {cache_error}")
            
        return True
    except psycopg2.Error as e: messagebox.showerror("Baza Xətası", f"İşçi silinərkən xəta: {e}")
    finally:
        if conn: conn.close()
    return False

def set_user_activity(user_id, new_status):
    conn = db_connect()
    if not conn: return False
    try:
        with conn.cursor() as cur:
            cur.execute("UPDATE employees SET is_active = %s WHERE id = %s", (new_status, user_id))
        conn.commit()
        return True
    except psycopg2.Error as e: messagebox.showerror("Baza Xətası", f"İstifadəçi statusu dəyişdirilərkən xəta: {e}")
    finally:
        if conn: conn.close()
    return False

def check_if_name_exists(name):
    conn = db_connect()
    if not conn: return False
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM employees WHERE name = %s", (name,))
            count = cur.fetchone()[0]
            return count > 0
    except psycopg2.Error as e: messagebox.showerror("Baza Xətası", f"Ad yoxlanarkən xəta: {e}")
    finally:
        if conn: conn.close()
    return False

def check_if_username_exists(username):
    """İstifadəçi adının mövcudluğunu yoxlayır"""
    conn = db_connect()
    if not conn: return False
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM employees WHERE username = %s", (username,))
            count = cur.fetchone()[0]
            return count > 0
    except psycopg2.Error as e: 
        logging.error(f"İstifadəçi adı yoxlanarkən xəta: {e}")
        return False
    finally:
        if conn: conn.close()
    return False

def get_employee_by_email(email):
    """Email ünvanı ilə işçi məlumatlarını tapır"""
    logging.info(f"🔍 [EMAIL_LOOKUP] Email ünvanı ilə işçi axtarılır: {email}")
    
    conn = db_connect()
    if not conn:
        logging.warning(f"❌ [EMAIL_LOOKUP] Database qoşulması uğursuz oldu: {email}")
        return None
    
    logging.info(f"✅ [EMAIL_LOOKUP] Database qoşulması uğurlu: {email}")
    
    try:
        with conn.cursor() as cur:
            # Əvvəlcə status sütununun olub-olmadığını yoxla
            logging.debug(f"🔍 [EMAIL_LOOKUP] Status sütunu yoxlanılır: {email}")
            cur.execute("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'employees' AND column_name = 'status'
            """)
            status_column_exists = cur.fetchone() is not None
            logging.debug(f"📊 [EMAIL_LOOKUP] Status sütunu mövcuddur: {status_column_exists}")
            
            if status_column_exists:
                # Status sütunu varsa, onu da əlavə et
                logging.info(f"🔍 [EMAIL_LOOKUP] İşçi axtarılır (status sütunu ilə): {email}")
                cur.execute("""
                    SELECT id, first_name, last_name, father_name, email, username, 
                           phone_number, birth_date, address, fin_code, department, 
                           position, department_id, position_id, status, created_at
                    FROM employees 
                    WHERE email = %s
                """, (email,))
                result = cur.fetchone()
                
                if result:
                    employee_data = {
                        'id': result[0],
                        'first_name': result[1],
                        'last_name': result[2],
                        'father_name': result[3],
                        'email': result[4],
                        'username': result[5],
                        'phone_number': result[6],
                        'birth_date': result[7],
                        'address': result[8],
                        'fin_code': result[9],
                        'department': result[10],
                        'position': result[11],
                        'department_id': result[12],
                        'position_id': result[13],
                        'status': result[14],
                        'created_at': result[15],
                        'name': f"{result[1]} {result[2]}" if result[1] and result[2] else result[5]
                    }
                    logging.info(f"✅ [EMAIL_LOOKUP] İşçi tapıldı: ID={result[0]}, Ad={employee_data['name']}, Email={email}")
                    return employee_data
                else:
                    logging.warning(f"⚠️ [EMAIL_LOOKUP] İşçi tapılmadı: {email}")
            else:
                # Status sütunu yoxdursa, onu istisna et
                logging.info(f"🔍 [EMAIL_LOOKUP] İşçi axtarılır (status sütunu olmadan): {email}")
                cur.execute("""
                    SELECT id, first_name, last_name, father_name, email, username, 
                           phone_number, birth_date, address, fin_code, department, 
                           position, department_id, position_id, created_at
                    FROM employees 
                    WHERE email = %s
                """, (email,))
                result = cur.fetchone()
                
                if result:
                    employee_data = {
                        'id': result[0],
                        'first_name': result[1],
                        'last_name': result[2],
                        'father_name': result[3],
                        'email': result[4],
                        'username': result[5],
                        'phone_number': result[6],
                        'birth_date': result[7],
                        'address': result[8],
                        'fin_code': result[9],
                        'department': result[10],
                        'position': result[11],
                        'department_id': result[12],
                        'position_id': result[13],
                        'created_at': result[14],
                        'name': f"{result[1]} {result[2]}" if result[1] and result[2] else result[5]
                    }
                    logging.info(f"✅ [EMAIL_LOOKUP] İşçi tapıldı: ID={result[0]}, Ad={employee_data['name']}, Email={email}")
                    return employee_data
                else:
                    logging.warning(f"⚠️ [EMAIL_LOOKUP] İşçi tapılmadı: {email}")
            return None
    except psycopg2.Error as e:
        logging.error(f"❌ [EMAIL_LOOKUP] Database xətası: {e}, Email: {email}")
        return None
    finally:
        if conn: conn.close()
    return None


def update_employee_system_settings(emp_id, new_role, vacation_days, max_sessions, new_username):
    """İşçinin sistem tənzimləmələrini yeniləyir"""
    conn = db_connect()
    if not conn: 
        logging.error(f"İşçi ID {emp_id} üçün baza qoşulması uğursuz oldu")
        return False
    try:
        # Məlumatları validasiya edirik
        if not isinstance(vacation_days, int) or vacation_days < 0:
            logging.error(f"Yanlış məzuniyyət günləri: {vacation_days}")
            return False
            
        if not isinstance(max_sessions, int) or max_sessions < 1:
            logging.error(f"Yanlış sessiya sayı: {max_sessions}")
            return False
            
        if not new_username or not new_username.strip():
            logging.error("Boş istifadəçi adı")
            return False
        
        with conn.cursor() as cur:
            # Əvvəlcə umumi_gun sütununun mövcudluğunu yoxlayırıq və əgər yoxdursa əlavə edirik
            try:
                cur.execute("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name = 'employees' AND column_name = 'umumi_gun'
                """)
                if not cur.fetchone():
                    logging.info("umumi_gun sütunu əlavə edilir...")
                    cur.execute("ALTER TABLE employees ADD COLUMN umumi_gun INTEGER DEFAULT 30")
                    conn.commit()
                    logging.info("umumi_gun sütunu uğurla əlavə edildi")
            except Exception as e:
                logging.warning(f"umumi_gun sütunu yoxlanarkən xəta: {e}")
            
            # Sistem tənzimləmələrini yenilə
            cur.execute("""
                UPDATE employees SET 
                    role = %s, total_vacation_days = %s, umumi_gun = %s, max_sessions = %s, username = %s
                WHERE id = %s
            """, (new_role, vacation_days, vacation_days, max_sessions, new_username.strip(), emp_id))
            
            # Yenilənən sətir sayını yoxlayırıq
            if cur.rowcount == 0:
                logging.error(f"İşçi ID {emp_id} tapılmadı")
                return False
                
        conn.commit()
        logging.info(f"İşçi ID {emp_id} sistem tənzimləmələri yeniləndi: role={new_role}, vacation_days={vacation_days}, max_sessions={max_sessions}, username={new_username}")
        
        # Cache-i etibarsız et
        try:
            try:
                from utils import cache
            except ImportError:
                from src.utils import cache
            cache.invalidate_cache()
            logging.info("İşçi sistem tənzimləmələri yeniləndi - cache etibarsız edildi")
        except Exception as cache_error:
            logging.warning(f"Cache etibarsız etmə xətası: {cache_error}")
            
        return True
    except psycopg2.Error as e: 
        logging.error(f"İşçi sistem tənzimləmələri yenilənərkən xəta: {e}")
        return False
    except Exception as e:
        logging.error(f"Gözlənilməyən xəta: {e}")
        return False
    finally:
        if conn: conn.close()
    return False

def change_user_password(user_id, current_password, new_password):
    """İstifadəçinin şifrəsini dəyişdirir (cari şifrə tələb olunur)"""
    conn = db_connect()
    if not conn: return False
    try:
        with conn.cursor() as cur:
            # Cari şifrəni yoxla
            cur.execute("SELECT password_hash FROM employees WHERE id = %s", (user_id,))
            result = cur.fetchone()
            if not result:
                return False
            
            stored_password = result[0]
            
            # Şifrəni yoxla
            import bcrypt
            if not bcrypt.checkpw(current_password.encode('utf-8'), stored_password.encode('utf-8')):
                return False
            
            # Yeni şifrəni hash et
            hashed_password = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt())
            
            # Şifrəni yenilə
            cur.execute("UPDATE employees SET password_hash = %s WHERE id = %s", 
                       (hashed_password.decode('utf-8'), user_id))
        conn.commit()
        return True
    except psycopg2.Error as e: 
        logging.error(f"Şifrə dəyişdirilərkən xəta: {e}")
        return False
    finally:
        if conn: conn.close()
    return False

def update_user_password(user_id, new_password):
    """İstifadəçinin şifrəsini dəyişir."""
    conn = db_connect()
    if not conn: return False
    try:
        # Yeni şifrəni hash et
        import bcrypt
        hashed_password = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt())
        
        with conn.cursor() as cur:
            cur.execute("UPDATE employees SET password_hash = %s WHERE id = %s", 
                       (hashed_password.decode('utf-8'), user_id))
        conn.commit()
        return True
    except Exception as e:
        logging.error(f"Şifrə dəyişdirilərkən xəta: {e}")
        return False
    finally:
        if conn: conn.close()

def change_employee_password_admin(employee_id, new_password):
    """Admin işçilərin şifrəsini cari şifrə bilmədən dəyişir"""
    conn = db_connect()
    if not conn: return False
    try:
        with conn.cursor() as cur:
            # Yeni şifrəni hash et
            import bcrypt
            hashed_password = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt())
            
            # Şifrəni yenilə (cari şifrə yoxlanmır)
            cur.execute("UPDATE employees SET password_hash = %s WHERE id = %s", 
                       (hashed_password.decode('utf-8'), employee_id))
            
            # Yenilənən sətir sayını yoxlayırıq
            if cur.rowcount == 0:
                logging.error(f"İşçi ID {employee_id} tapılmadı")
                return False
                
        conn.commit()
        logging.info(f"Admin tərəfindən işçi ID {employee_id} şifrəsi dəyişdirildi")
        return True
    except psycopg2.Error as e: 
        logging.error(f"Admin şifrə dəyişdirilərkən xəta: {e}")
        return False
    except Exception as e:
        logging.error(f"Gözlənilməyən xəta: {e}")
        return False
    finally:
        if conn: conn.close()
    return False

def load_data_for_user(current_user, force_refresh=False):
    """Bütün işçilərin məlumatlarını və aktiv sessiya saylarını gətirir."""
    # monitor_operation decorator-ını şərti olaraq import et
    try:
        try:
            from utils.performance_monitor import monitor_operation
        except ImportError:
            from src.utils.performance_monitor import monitor_operation
    except ImportError:
        # Əgər import uğursuz olsa, boş decorator istifadə et
        def monitor_operation(name):
            def decorator(func):
                return func
            return decorator
    
    @monitor_operation("load_data_for_user")
    def _load_data():
        logging.info(f"load_data_for_user başladı. İstifadəçi: {current_user['name']} (ID: {current_user['id']}, Rol: {current_user['role']}), force_refresh: {force_refresh}")
        
        # hide sütununun mövcudluğunu yoxlayırıq
        ensure_hide_column_exists()
        
        # Cache sistemi ilə inteqrasiya
        from utils import cache
        
        # Force refresh deyilsə və cache etibarlıdırsa, cache-dən gətir
        if not force_refresh and cache.is_cache_valid_for_user():
            cached_data = cache.load_cache()
            if cached_data and 'employees' in cached_data:
                logging.info("Məlumatlar cache-dən gətirildi")
                return cached_data
        else:
            if force_refresh:
                logging.info("Force refresh tələb edildi - cache atlanılır")
                # Cache-i etibarsız et
                cache.invalidate_cache()
        
        return _perform_database_load(current_user)
    
    return _load_data()

def _perform_database_load(current_user):
    """Database-dən məlumatları yükləyir"""
    # DÜZƏLİŞ: İşçi məzuniyyət günlərini yoxlayırıq və düzəldirik
    check_and_fix_employee_vacation_days()
    
    logging.info("Database məlumatları yüklənir...")
    
    try:
        conn = db_connect()
        if not conn: 
            logging.error("Veritabanı qoşulması uğursuz oldu")
            return {}
        
        logging.info("Veritabanı qoşulması uğurlu oldu")
        data = {}
        
        with conn.cursor() as cur:
            # Aktiv sessiya saylarını alırıq
            try:
                cur.execute("SELECT user_id, COUNT(*) FROM active_sessions GROUP BY user_id")
                session_counts = dict(cur.fetchall())
                logging.info(f"Aktiv sessiyalar: {session_counts}")
            except Exception as e:
                logging.warning(f"Aktiv sessiyalar alınarkən xəta: {e}")
                session_counts = {}
            
            # İşçi məlumatlarını alırıq - Admin və adi istifadəçi üçün fərqli sorğular
            try:
                if current_user['role'].strip() == 'admin':
                    # Admin bütün işçiləri görə bilər
                    cur.execute("""
                        SELECT id, name, total_vacation_days, is_active, max_sessions,
                               first_name, last_name, father_name, email, phone_number,
                               birth_date, address, position, department, hire_date, salary, profile_image, role, username,
                               fin_code, department_id, position_id
                        FROM employees 
                        WHERE hide IS NULL OR hide = FALSE 
                        ORDER BY name
                    """)
                else:
                    # Adi istifadəçi yalnız öz məlumatını görə bilər
                    cur.execute("""
                        SELECT id, name, total_vacation_days, is_active, max_sessions,
                               first_name, last_name, father_name, email, phone_number,
                               birth_date, address, position, department, hire_date, salary, profile_image, role, username,
                               fin_code, department_id, position_id
                        FROM employees 
                        WHERE id = %s AND (hide IS NULL OR hide = FALSE)
                    """, (current_user['id'],))
                
                employees = cur.fetchall()
                logging.info(f"İşçi sayı: {len(employees)}")
                
                for emp in employees:
                    emp_id, name, total_days, is_active, max_sessions, first_name, last_name, father_name, email, phone_number, birth_date, address, position, department, hire_date, salary, profile_image, role, username, fin_code, department_id, position_id = emp
                    
                    # İşçi məlumatlarını dictionary-ə əlavə edirik
                    data[name] = {
                        'db_id': emp_id,
                        'umumi_gun': total_days or 30,  # Default 30 gün
                        'is_active': bool(is_active),
                        'max_sessions': max_sessions or 1,
                        'active_session_count': session_counts.get(emp_id, 0),
                        'goturulen_icazeler': [],
                        'first_name': first_name or '',
                        'last_name': last_name or '',
                        'father_name': father_name or '',
                        'email': email or '',
                        'phone_number': phone_number or '',
                        'birth_date': birth_date.strftime('%Y-%m-%d') if birth_date else '',
                        'address': address or '',
                        'position': position or '',
                        'department': department or '',
                        'hire_date': hire_date.strftime('%Y-%m-%d') if hire_date else '',
                        'salary': salary or '',
                        'profile_image': profile_image or '',
                        'role': role or 'user',
                        'username': username or '',
                        'fin_code': fin_code if fin_code is not None else '',
                        'department_id': department_id if department_id is not None else '',
                        'position_id': position_id if position_id is not None else ''
                    }
                
                logging.info(f"✅ {len(data)} işçi məlumatı yükləndi")
                
            except Exception as e:
                logging.error(f"İşçi məlumatları alınarkən xəta: {e}")
                return {}
            
            # Məzuniyyət məlumatlarını alırıq - Admin və adi istifadəçi üçün fərqli sorğular
            try:
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
                logging.info(f"Məzuniyyət sayı: {len(vacations)}")
                
                for vac in vacations:
                    vac_id, employee_id, start_date, end_date, note, is_inactive, created_at, status = vac
                    
                    # İşçi adını tapırıq
                    employee_name = None
                    for name, emp_data in data.items():
                        if emp_data['db_id'] == employee_id:
                            employee_name = name
                            break
                    
                    if employee_name:
                        # Məzuniyyət məlumatlarını əlavə edirik
                        vacation_data = {
                            'db_id': vac_id,
                            'baslama': start_date,
                            'bitme': end_date,
                            'qeyd': note or '',
                            'aktiv_deyil': bool(is_inactive),
                            'yaradilma_tarixi': created_at,
                            'status': status or 'pending'
                        }
                        data[employee_name]['goturulen_icazeler'].append(vacation_data)
                
                logging.info("Məzuniyyət məlumatları emal edildi")
                
            except Exception as e:
                logging.error(f"Məzuniyyət məlumatları alınarkən xəta: {e}")
            
        conn.commit()
        logging.info(f"✅ Database məlumatları uğurla yükləndi: {len(data)} işçi")
        
        # TƏHLÜKƏSİZLİK: İşçi məlumatları heç vaxt cache edilmir!
        # Bu məlumatlar həssas məlumatlardır və yerli faylda saxlanılmamalıdır
        logging.info("TƏHLÜKƏSİZLİK: İşçi məlumatları cache edilmir - həssas məlumatlar yerli faylda saxlanılmır")
        
        return data
        
    except Exception as e:
        logging.error(f"Database yükləmə xətası: {e}")
        return {}
    finally:
        if 'conn' in locals() and conn is not None:
            conn.close()
            logging.info("Database qoşulması bağlandı")

# --- MƏZUNİYYƏT (VACATION) FUNKSİYALARI ---

def add_vacation(employee_id, employee_name, vac_data, requested_by_role):
    # DEBUG: Sorğu göndərilməyə başladı
    print(f"🔵 DEBUG add_vacation: Funksiya çağırıldı - employee_id={employee_id}, employee_name={employee_name}")
    log_signal_sent("vacation_request_started", {
        "employee_id": employee_id,
        "employee_name": employee_name,
        "vac_data": vac_data,
        "requested_by_role": requested_by_role
    }, "database")
    
    print(f"🔵 DEBUG add_vacation: db_connect() çağırılır...")
    print(f"🔵 DEBUG add_vacation: Connection parametrləri yoxlanılır...")
    
    # Connection parametrlərinin olub-olmadığını yoxla
    try:
        from .connection import _active_connection_params
        if not _active_connection_params:
            error_msg = "Connection parametrləri təyin edilməyib. Zəhmət olmasa əvvəlcə bazaya qoşulun."
            print(f"❌ DEBUG add_vacation: {error_msg}")
            log_error("database_connection_params_missing", error_msg, None, "database")
            raise Exception(error_msg)
        print(f"✅ DEBUG add_vacation: Connection parametrləri mövcuddur")
    except ImportError:
        print(f"⚠️ DEBUG add_vacation: connection modulu import edilə bilmədi")
    
    conn = db_connect()
    if not conn:
        # DEBUG: Connection xətası
        error_msg = "Veritabanına qoşulma uğursuz oldu. Zəhmət olmasa yenidən cəhd edin."
        print(f"❌ DEBUG add_vacation: Connection None qayıtdı!")
        print(f"❌ DEBUG add_vacation: Xəta mesajı: {error_msg}")
        log_error("database_connection_failed", error_msg, None, "database")
        # Thread içində messagebox işləmir, exception fırlat
        raise Exception(error_msg)
    
    print(f"✅ DEBUG add_vacation: Connection uğurlu!")
    status = 'approved' if requested_by_role == 'admin' else 'pending'
    try:
        with conn.cursor() as cur:
            cur.execute( "INSERT INTO vacations (employee_id, start_date, end_date, note, created_at, status) VALUES (%s, %s, %s, %s, %s, %s) RETURNING id",
                (employee_id, vac_data['baslama'], vac_data['bitme'], vac_data['qeyd'], vac_data['yaradilma_tarixi'], status))
            vac_id = cur.fetchone()[0]
            if status == 'pending':
                # Admin ID-lərini alırıq
                cur.execute("SELECT id FROM employees WHERE role = 'admin'")
                admin_ids = [row[0] for row in cur.fetchall()]
                message = f"İşçi '{employee_name}' yeni məzuniyyət sorğusu göndərdi."
                for admin_id in admin_ids: 
                    create_notification(admin_id, message, vac_id, cur)
        conn.commit()
        
        # DEBUG: Uğurlu əlavə etmə
        try:
            log_signal_sent("vacation_request_success", {
                "vacation_id": vac_id,
                "employee_id": employee_id,
                "employee_name": employee_name,
                "status": status
            }, "database")
        except Exception as e:
            logging.warning(f"Debug log xətası: {e}")
        
        # Cache-i etibarsız et
        try:
            try:
                from utils import cache
            except ImportError:
                from src.utils import cache
            cache.invalidate_cache()
            logging.info("Məzuniyyət əlavə edildi - cache etibarsız edildi")
        except Exception as cache_error:
            logging.warning(f"Cache etibarsız etmə xətası: {cache_error}")
            
    except psycopg2.Error as e:
        # DEBUG: Database xətası
        try:
            try:
                from utils.realtime_debug import log_error
            except ImportError:
                from src.utils.realtime_debug import log_error
            log_error("database_insert_failed", f"Məzuniyyəti əlavə edərkən xəta: {e}", None, "database")
        except Exception as debug_e:
            logging.warning(f"Debug log xətası: {debug_e}")
        # Thread içində messagebox çağırma - exception fırlat ki UI thread-də göstərilsin
        logging.error(f"Məzuniyyəti əlavə edərkən xəta: {e}")
        raise Exception(f"Məzuniyyəti əlavə edərkən xəta: {e}")
    finally:
        if conn: conn.close()

def update_vacation(vac_id, vac_data, admin_name):
    conn = db_connect()
    if not conn: 
        raise Exception("Veritabanına qoşulma uğursuz oldu. Zəhmət olmasa yenidən cəhd edin.")
    try:
        with conn.cursor() as cur:
            cur.execute("UPDATE vacations SET start_date=%s, end_date=%s, note=%s WHERE id=%s RETURNING employee_id", (vac_data['baslama'], vac_data['bitme'], vac_data['qeyd'], vac_id))
            result = cur.fetchone()
            if result:
                recipient_id = result[0]
                message = f"Admin '{admin_name}' sizin {vac_data['baslama']} tarixli məzuniyyət sorğunuzda dəyişiklik etdi."
                create_notification(recipient_id, message, vac_id, cur)
        conn.commit()
        
        # Cache-i etibarsız et
        try:
            try:
                from utils import cache
            except ImportError:
                from src.utils import cache
            cache.invalidate_cache()
            logging.info("Məzuniyyət yeniləndi - cache etibarsız edildi")
        except Exception as cache_error:
            logging.warning(f"Cache etibarsız etmə xətası: {cache_error}")
            
    except psycopg2.Error as e: messagebox.showerror("Baza Xətası", f"Məzuniyyəti yeniləyərkən xəta: \n{e}")
    finally:
        if conn: conn.close()

def update_vacation_status(vac_id, new_status, admin_name):
    conn = db_connect()
    if not conn: return
    try:
        with conn.cursor() as cur:
            cur.execute("UPDATE vacations SET status = %s WHERE id = %s RETURNING employee_id, start_date, end_date", (new_status, vac_id))
            result = cur.fetchone()
            if result:
                recipient_id, start_date, end_date = result
                status_az = "Təsdiqləndi" if new_status == 'approved' else "Rədd edildi"
                message = f"Admin '{admin_name}', sizin {start_date.strftime('%d.%m.%Y')} - {end_date.strftime('%d.%m.%Y')} arası sorğunuzu '{status_az}' statusu ilə yenilədi."
                create_notification(recipient_id, message, vac_id, cur)
        conn.commit()
        
        # Cache-i etibarsız et
        try:
            try:
                from utils import cache
            except ImportError:
                from src.utils import cache
            cache.invalidate_cache()
            logging.info("Məzuniyyət statusu yeniləndi - cache etibarsız edildi")
        except Exception as cache_error:
            logging.warning(f"Cache etibarsız etmə xətası: {cache_error}")
            
    except psycopg2.Error as e: messagebox.showerror("Baza Xətası", f"Məzuniyyət statusunu dəyişərkən xəta: \n{e}")
    finally:
        if conn: conn.close()

def delete_vacation(vac_id, admin_name):
    conn = db_connect()
    if not conn: return False
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT employee_id, start_date, end_date FROM vacations WHERE id = %s", (vac_id,))
            result = cur.fetchone()
            if result:
                recipient_id, start_date, end_date = result
                cur.execute("DELETE FROM vacations WHERE id = %s", (vac_id,))
                message = f"Admin '{admin_name}' sizin {start_date.strftime('%d.%m.%Y')} - {end_date.strftime('%d.%m.%Y')} arası sorğunuzu sildi."
                create_notification(recipient_id, message, None, cur)
                conn.commit()
                
                # Cache-i etibarsız et
                try:
                    try:
                        from utils import cache
                    except ImportError:
                        from src.utils import cache
                    cache.invalidate_cache()
                    logging.info("Məzuniyyət silindi - cache etibarsız edildi")
                except Exception as cache_error:
                    logging.warning(f"Cache etibarsız etmə xətası: {cache_error}")
                
                return True
            else:
                return False
            
    except psycopg2.Error as e: 
        messagebox.showerror("Baza Xətası", f"Məzuniyyəti silərkən xəta: \n{e}")
        return False
    finally:
        if conn: conn.close()

def toggle_vacation_activity(vac_id, new_status, admin_name):
    conn = db_connect()
    if not conn: return
    try:
        with conn.cursor() as cur:
            cur.execute("UPDATE vacations SET is_inactive = %s WHERE id = %s RETURNING employee_id, start_date, end_date", (new_status, vac_id))
            result = cur.fetchone()
            if result:
                recipient_id, start_date, end_date = result
                status_az = "deaktiv" if new_status else "aktiv"
                message = f"Admin '{admin_name}' sizin {start_date.strftime('%d.%m.%Y')} tarixli təsdiqlənmiş məzuniyyətinizi '{status_az}' etdi."
                create_notification(recipient_id, message, vac_id, cur)
        conn.commit()
    except psycopg2.Error as e: messagebox.showerror("Baza Xətası", f"Statusu dəyişərkən xəta: \n{e}")
    finally:
        if conn: conn.close()

# --- ARXİVLƏMƏ FUNKSİYALARI ---
def get_employees_with_archivable_vacations():
    conn = db_connect()
    if not conn: return []
    employees = []
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
            employees = cur.fetchall()
    except psycopg2.Error as e: messagebox.showerror("Baza Xətası", f"Arxivlənəcək işçilər alınarkən xəta: \n{e}")
    finally:
        if conn: conn.close()
    return employees

def start_new_vacation_year(employee_ids, default_days=30):
    conn = db_connect()
    if not conn: return False
    try:
        with conn.cursor() as cur:
            # Köhnə məzuniyyətləri arxivə edirik
            current_year = date.today().year
            cur.execute("UPDATE vacations SET is_archived = TRUE WHERE EXTRACT(YEAR FROM start_date) < %s AND status = 'approved'", (current_year,))
            
            # İşçilərin məzuniyyət günlərini yeniləyirik
            for emp_id in employee_ids:
                cur.execute("UPDATE employees SET total_vacation_days = %s WHERE id = %s", (default_days, emp_id))
            
        conn.commit()
        return True
    except psycopg2.Error as e: messagebox.showerror("Baza Xətası", f"Yeni il başladılarkən xəta: \n{e}")
    finally:
        if conn: conn.close()
    return False

def load_archived_vacations_for_year(employee_id, year):
    conn = db_connect()
    if not conn: return []
    vacations = []
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT id, start_date, end_date, note, status, created_at
                FROM vacations 
                WHERE employee_id = %s AND EXTRACT(YEAR FROM start_date) = %s AND is_archived = TRUE
                ORDER BY start_date
            """, (employee_id, year))
            vacations = cur.fetchall()
    except psycopg2.Error as e: messagebox.showerror("Baza Xətası", f"Arxiv məzuniyyətlər alınarkən xəta: \n{e}")
    finally:
        if conn: conn.close()
    return vacations

def get_latest_version():
    """Ən son versiya məlumatını qaytarır (bu funksiya gələcəkdə serverdən alınacaq)"""
    return {
        "version": "6.4-final-unified-tkinter",
        "release_date": "2024-12-20",
        "download_url": "https://github.com/your-repo/releases/latest",
        "changelog": "Universal link sistemi və çoxlu şirkət dəstəyi əlavə edildi"
    }

def record_login(user_id):
    """İstifadəçinin giriş vaxtını qeyd edir"""
    conn = db_connect()
    if not conn: return None
    try:
        with conn.cursor() as cur:
            cur.execute("INSERT INTO login_history (user_id, login_time) VALUES (%s, NOW()) RETURNING id", (user_id,))
            history_id = cur.fetchone()[0]
            conn.commit()
            return history_id
    except psycopg2.Error as e:
        messagebox.showerror("Baza Xətası", f"Giriş qeyd edilərkən xəta: \n{e}")
        return None
    finally:
        if conn: conn.close()

def record_logout(history_id):
    """İstifadəçinin çıxış vaxtını qeyd edir"""
    if not history_id: return
    conn = db_connect()
    if not conn: return
    try:
        with conn.cursor() as cur:
            cur.execute("UPDATE login_history SET logout_time = NOW() WHERE id = %s", (history_id,))
            conn.commit()
    except psycopg2.Error as e:
        messagebox.showerror("Baza Xətası", f"Çıxış qeyd edilərkən xəta: \n{e}")
    finally:
        if conn: conn.close()

def get_login_history(user_id):
    """İstifadəçinin giriş-çıxış tarixçəsini gətirir"""
    conn = db_connect()
    if not conn: return []
    history = []
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT login_time, logout_time 
                FROM login_history 
                WHERE user_id = %s 
                ORDER BY login_time DESC
            """, (user_id,))
            history = cur.fetchall()
    except psycopg2.Error as e:
        messagebox.showerror("Baza Xətası", f"Tarixçə oxunarkən xəta: \n{e}")
    finally:
        if conn: conn.close()
    return history

def check_and_fix_employee_vacation_days():
    """İşçilərin məzuniyyət günlərini yoxlayır və düzəldir"""
    conn = db_connect()
    if not conn: return False
    
    try:
        with conn.cursor() as cur:
            # İşçilərin məzuniyyət günlərini yoxlayırıq
            cur.execute("SELECT id, name, total_vacation_days FROM employees WHERE is_active = TRUE")
            employees = cur.fetchall()
            
            logging.debug("İşçi məzuniyyət günləri yoxlanır...")
            for emp_id, name, total_days in employees:
                logging.debug(f"İşçi - ID: {emp_id}, Ad: {name}, Məzuniyyət günləri: {total_days}")
                
                # Əgər məzuniyyət günləri 0 və ya NULL-dırsa, 30-a təyin edirik
                if total_days is None or total_days == 0:
                    logging.debug(f"{name} üçün məzuniyyət günləri düzəldilir: 0 -> 30")
                    cur.execute("UPDATE employees SET total_vacation_days = 30 WHERE id = %s", (emp_id,))
            
            conn.commit()
            logging.debug("İşçi məzuniyyət günləri düzəldildi")
            return True
            
    except Exception as e:
        logging.debug(f"İşçi məzuniyyət günləri düzəldilərkən xəta: {e}")
        return False
    finally:
        if conn: conn.close()

def fix_all_employee_vacation_days():
    """Bütün işçilərin məzuniyyət günlərini 30-a təyin edir"""
    conn = db_connect()
    if not conn: return False
    
    try:
        with conn.cursor() as cur:
            # Bütün aktiv işçilərin məzuniyyət günlərini 30-a təyin edirik
            cur.execute("UPDATE employees SET total_vacation_days = 30 WHERE is_active = TRUE AND (total_vacation_days = 0 OR total_vacation_days IS NULL)")
            updated_count = cur.rowcount
            conn.commit()
            logging.debug(f"{updated_count} işçinin məzuniyyət günləri 30-a təyin edildi")
            return True
            
    except Exception as e:
        logging.debug(f"İşçi məzuniyyət günləri düzəldilərkən xəta: {e}")
        return False
    finally:
        if conn: conn.close()

def hide_employee(emp_id, admin_password, current_admin_id):
    """İşçini gizlədir (hide=true) - admin parolu tələb edir"""
    conn = db_connect()
    if not conn: return False
    
    try:
        with conn.cursor() as cur:
            # Admin parolunu yoxlayırıq - cari admin istifadəçisinin parolunu yoxlayırıq
            cur.execute("SELECT password_hash FROM employees WHERE id = %s AND role = 'admin'", (current_admin_id,))
            result = cur.fetchone()
            if not result:
                messagebox.showerror("Xəta", "Admin parolu yanlışdır!")
                return False
            
            stored_password = result[0]
            if not bcrypt.checkpw(admin_password.encode('utf-8'), stored_password.encode('utf-8')):
                messagebox.showerror("Xəta", "Admin parolu yanlışdır!")
                return False
            
            # İşçini gizlədirik
            cur.execute("UPDATE employees SET hide = TRUE WHERE id = %s", (emp_id,))
        conn.commit()
        
        # Cache-i etibarsız et
        try:
            try:
                from utils import cache
            except ImportError:
                from src.utils import cache
            cache.invalidate_cache()
            logging.info("İşçi gizlədildi - cache etibarsız edildi")
        except Exception as cache_error:
            logging.warning(f"Cache etibarsız etmə xətası: {cache_error}")
            
        return True
    except psycopg2.Error as e: 
        messagebox.showerror("Baza Xətası", f"İşçi gizlədilərkən xəta: {e}")
    finally:
        if conn: conn.close()
    return False

def unhide_employee(emp_id):
    """İşçini göstərir (hide=false)"""
    conn = db_connect()
    if not conn: return False
    try:
        with conn.cursor() as cur:
            cur.execute("UPDATE employees SET hide = FALSE WHERE id = %s", (emp_id,))
        conn.commit()
        
        # Cache-i etibarsız et
        try:
            try:
                from utils import cache
            except ImportError:
                from src.utils import cache
            cache.invalidate_cache()
            logging.info("İşçi göstərildi - cache etibarsız edildi")
        except Exception as cache_error:
            logging.warning(f"Cache etibarsız etmə xətası: {cache_error}")
            
        return True
    except psycopg2.Error as e: 
        messagebox.showerror("Baza Xətası", f"İşçi göstərilərkən xəta: {e}")
    finally:
        if conn: conn.close()
    return False

def permanently_delete_employee(emp_id, admin_password, current_admin_id):
    """İşçini həqiqətən silir - admin parolu tələb edir"""
    conn = db_connect()
    if not conn: return False
    
    try:
        with conn.cursor() as cur:
            # Admin parolunu yoxlayırıq - cari admin istifadəçisinin parolunu yoxlayırıq
            cur.execute("SELECT password_hash FROM employees WHERE id = %s AND role = 'admin'", (current_admin_id,))
            result = cur.fetchone()
            if not result:
                messagebox.showerror("Xəta", "Admin parolu yanlışdır!")
                return False
            
            stored_password = result[0]
            if not bcrypt.checkpw(admin_password.encode('utf-8'), stored_password.encode('utf-8')):
                messagebox.showerror("Xəta", "Admin parolu yanlışdır!")
                return False
            
            # İşçini həqiqətən silirik
            cur.execute("DELETE FROM employees WHERE id = %s", (emp_id,))
        conn.commit()
        
        # Cache-i etibarsız et
        try:
            try:
                from utils import cache
            except ImportError:
                from src.utils import cache
            cache.invalidate_cache()
            logging.info("İşçi həqiqətən silindi - cache etibarsız edildi")
        except Exception as cache_error:
            logging.warning(f"Cache etibarsız etmə xətası: {cache_error}")
            
        return True
    except psycopg2.Error as e: 
        messagebox.showerror("Baza Xətası", f"İşçi silinərkən xəta: {e}")
    finally:
        if conn: conn.close()
    return False

def get_hidden_employees():
    """Gizlənmiş işçiləri gətirir"""
    conn = db_connect()
    if not conn: return []
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT id, name, total_vacation_days, is_active, max_sessions FROM employees WHERE hide = TRUE ORDER BY name")
            return cur.fetchall()
    except psycopg2.Error as e: 
        messagebox.showerror("Baza Xətası", f"Gizlənmiş işçilər alınarkən xəta: {e}")
    finally:
        if conn: conn.close()
    return []

def ensure_hide_column_exists():
    """employees cədvəlində hide sütununun olub-olmadığını yoxlayır və əgər yoxdursa əlavə edir"""
    conn = db_connect()
    if not conn: return False
    
    try:
        with conn.cursor() as cur:
            # hide sütununun olub-olmadığını yoxlayırıq
            cur.execute("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'employees' AND column_name = 'hide'
            """)
            result = cur.fetchone()
            
            if not result:
                # hide sütunu yoxdur, əlavə edirik
                cur.execute("ALTER TABLE employees ADD COLUMN hide BOOLEAN DEFAULT FALSE")
                conn.commit()
                logging.info("hide sütunu employees cədvəlinə əlavə edildi")
                return True
            else:
                logging.info("hide sütunu artıq mövcuddur")
                return True
                
    except psycopg2.Error as e:
        logging.error(f"hide sütunu əlavə edilərkən xəta: {e}")
        return False
    finally:
        if conn: conn.close()