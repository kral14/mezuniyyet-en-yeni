# database/error_queries.py

import psycopg2
from .connection import db_connect

def create_user_logs_table():
    """İstifadəçi log faylları üçün cədvəl yaradır"""
    conn = db_connect()
    if not conn: return False
    try:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS user_application_logs (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER REFERENCES employees(id) ON DELETE CASCADE,
                    log_type VARCHAR(50) NOT NULL,
                    log_content TEXT NOT NULL,
                    log_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    log_file_name VARCHAR(255),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            # İndekslər
            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_user_logs_user_id ON user_application_logs(user_id)
            """)
            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_user_logs_timestamp ON user_application_logs(log_timestamp)
            """)
            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_user_logs_type ON user_application_logs(log_type)
            """)
            
            # Log silmə siqnalları üçün cədvəl
            cur.execute("""
                CREATE TABLE IF NOT EXISTS log_deletion_signals (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER REFERENCES employees(id) ON DELETE CASCADE,
                    log_file_name VARCHAR(255),
                    log_type VARCHAR(50),
                    signal_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    processed BOOLEAN DEFAULT FALSE,
                    processed_at TIMESTAMP,
                    created_by_user_id INTEGER REFERENCES employees(id) ON DELETE SET NULL
                )
            """)
            # İndekslər
            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_log_deletion_signals_user_id ON log_deletion_signals(user_id)
            """)
            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_log_deletion_signals_processed ON log_deletion_signals(processed)
            """)
            
            conn.commit()
            return True
    except psycopg2.Error as e:
        print(f"user_application_logs cədvəli yaradılarkən xəta: {e}")
        conn.rollback()
        return False
    finally:
        if conn: conn.close()

def log_to_database(user_id, log_type, log_content, log_file_name=None):
    """Log məlumatını verilənlər bazasına yazır"""
    # Əvvəlcə cədvəlin mövcudluğunu yoxla və yarat
    create_user_logs_table()
    
    conn = db_connect()
    if not conn: return False
    try:
        with conn.cursor() as cur:
            # Əgər eyni fayl adı və istifadəçi üçün log varsa, yenilə (duplikat yoxlama)
            if log_file_name:
                cur.execute("""
                    SELECT id FROM user_application_logs 
                    WHERE user_id = %s AND log_file_name = %s
                    LIMIT 1
                """, (user_id, log_file_name))
                existing = cur.fetchone()
                
                if existing:
                    # Mövcud logu yenilə
                    cur.execute("""
                        UPDATE user_application_logs 
                        SET log_content = %s, log_timestamp = CURRENT_TIMESTAMP
                        WHERE id = %s
                    """, (log_content, existing[0]))
                else:
                    # Yeni log əlavə et
                    cur.execute("""
                        INSERT INTO user_application_logs (user_id, log_type, log_content, log_file_name)
                        VALUES (%s, %s, %s, %s)
                    """, (user_id, log_type, log_content, log_file_name))
            else:
                # Fayl adı yoxdursa, həmişə yeni log əlavə et
                cur.execute("""
                    INSERT INTO user_application_logs (user_id, log_type, log_content, log_file_name)
                    VALUES (%s, %s, %s, %s)
                """, (user_id, log_type, log_content, log_file_name))
            
            conn.commit()
            return True
    except psycopg2.Error as e:
        # Xəta olsa belə davam et - log yazma xətası proqramı dayandırmamalıdır
        print(f"Log bazaya yazılarkən xəta: {e}")
        conn.rollback()
        return False
    finally:
        if conn: conn.close()

def get_user_logs(user_id=None, log_type=None, limit=1000):
    """İstifadəçi log fayllarını gətirir"""
    conn = db_connect()
    if not conn: return []
    try:
        with conn.cursor() as cur:
            query = """
                SELECT l.id, l.user_id, emp.username, l.log_type, l.log_content, 
                       l.log_timestamp, l.log_file_name
                FROM user_application_logs l
                LEFT JOIN employees emp ON l.user_id = emp.id
                WHERE 1=1
            """
            params = []
            
            if user_id:
                query += " AND l.user_id = %s"
                params.append(user_id)
            
            if log_type:
                query += " AND l.log_type = %s"
                params.append(log_type)
            
            query += " ORDER BY l.log_timestamp DESC LIMIT %s"
            params.append(limit)
            
            cur.execute(query, params)
            return cur.fetchall()
    except psycopg2.Error as e:
        print(f"Log faylları gətirilərkən xəta: {e}")
        return []
    finally:
        if conn: conn.close()

def get_log_users():
    """Log faylı olan istifadəçilərin siyahısını qaytarır"""
    conn = db_connect()
    if not conn: return []
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT DISTINCT emp.id, emp.username 
                FROM user_application_logs l
                JOIN employees emp ON l.user_id = emp.id
                WHERE emp.username IS NOT NULL
                ORDER BY emp.username
            """)
            return cur.fetchall()
    except psycopg2.Error as e:
        print(f"Log istifadəçiləri gətirilərkən xəta: {e}")
        return []
    finally:
        if conn: conn.close()

def delete_user_logs(user_id=None, log_id=None, created_by_user_id=None):
    """
    Log qeydlərini silir və silmə siqnalı yaradır
    
    Args:
        user_id: İstifadəçi ID-si (bütün logları silmək üçün)
        log_id: Log ID-si (tək log silmək üçün)
        created_by_user_id: Silmə əməliyyatını edən istifadəçi ID-si
    """
    conn = db_connect()
    if not conn: return False
    try:
        with conn.cursor() as cur:
            log_files_to_delete = []
            
            if log_id:
                # Tək log silmək - fayl adını al
                cur.execute("""
                    SELECT user_id, log_file_name, log_type 
                    FROM user_application_logs 
                    WHERE id = %s
                """, (log_id,))
                log_info = cur.fetchone()
                if log_info:
                    target_user_id, log_file_name, log_type = log_info
                    if log_file_name:
                        log_files_to_delete.append((target_user_id, log_file_name, log_type))
                    cur.execute("DELETE FROM user_application_logs WHERE id = %s", (log_id,))
            elif user_id:
                # İstifadəçinin bütün loglarını silmək - fayl adlarını al
                cur.execute("""
                    SELECT DISTINCT log_file_name, log_type 
                    FROM user_application_logs 
                    WHERE user_id = %s AND log_file_name IS NOT NULL
                """, (user_id,))
                for log_file_name, log_type in cur.fetchall():
                    if log_file_name:
                        log_files_to_delete.append((user_id, log_file_name, log_type))
                cur.execute("DELETE FROM user_application_logs WHERE user_id = %s", (user_id,))
            else:
                return False
            
            # Silmə siqnalları yarat
            for target_user_id, log_file_name, log_type in log_files_to_delete:
                cur.execute("""
                    INSERT INTO log_deletion_signals (user_id, log_file_name, log_type, created_by_user_id)
                    VALUES (%s, %s, %s, %s)
                """, (target_user_id, log_file_name, log_type, created_by_user_id))
            
            conn.commit()
            return True
    except psycopg2.Error as e:
        print(f"Log silinərkən xəta: {e}")
        conn.rollback()
        return False
    finally:
        if conn: conn.close()

def get_pending_deletion_signals(user_id):
    """
    İstifadəçi üçün gözləyən silmə siqnallarını gətirir
    
    Args:
        user_id: İstifadəçi ID-si
    
    Returns:
        Silmə siqnallarının siyahısı: [(log_file_name, log_type), ...]
    """
    conn = db_connect()
    if not conn: return []
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT log_file_name, log_type 
                FROM log_deletion_signals
                WHERE user_id = %s AND processed = FALSE
                ORDER BY signal_timestamp ASC
            """, (user_id,))
            return cur.fetchall()
    except psycopg2.Error as e:
        print(f"Silmə siqnalları gətirilərkən xəta: {e}")
        return []
    finally:
        if conn: conn.close()

def mark_deletion_signals_processed(user_id, log_file_names):
    """
    Silmə siqnallarını işlənmiş kimi işarələyir
    
    Args:
        user_id: İstifadəçi ID-si
        log_file_names: İşlənmiş fayl adlarının siyahısı
    """
    conn = db_connect()
    if not conn: return False
    try:
        with conn.cursor() as cur:
            for log_file_name in log_file_names:
                cur.execute("""
                    UPDATE log_deletion_signals 
                    SET processed = TRUE, processed_at = CURRENT_TIMESTAMP
                    WHERE user_id = %s AND log_file_name = %s AND processed = FALSE
                """, (user_id, log_file_name))
            conn.commit()
            return True
    except psycopg2.Error as e:
        print(f"Silmə siqnalları işarələnərkən xəta: {e}")
        conn.rollback()
        return False
    finally:
        if conn: conn.close()

def log_error_to_db(user_id, traceback_str):
    """Baş verən xətanı verilənlər bazasına yazır."""
    conn = db_connect()
    if not conn: return
    try:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO error_logs (user_id, traceback_text) VALUES (%s, %s)",
                (user_id, traceback_str)
            )
            conn.commit()
    except psycopg2.Error as e:
        # Bu funksiya xəta baş verərkən işlədiyi üçün,
        # burada messagebox göstərmək olmaz, çünki sonsuz dövrə girə bilər.
        # Sadəcə terminala yazırıq.
        print(f"XƏTA LOGUNU YAZARKƏN XƏTA BAŞ VERDİ: {e}")
    finally:
        if conn: conn.close()

def get_all_errors():
    """Bütün xəta qeydlərini bazadan çəkir."""
    conn = db_connect()
    if not conn: return []
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT e.id, emp.username, e.error_timestamp, e.status, e.traceback_text 
                FROM error_logs e
                LEFT JOIN employees emp ON e.user_id = emp.id
                ORDER BY e.error_timestamp DESC
            """)
            return cur.fetchall()
    finally:
        if conn: conn.close()

def get_error_users():
    """Xətası qeydə alınmış unikal istifadəçilərin siyahısını qaytarır."""
    conn = db_connect()
    if not conn: return []
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT DISTINCT emp.username FROM error_logs e
                JOIN employees emp ON e.user_id = emp.id
                WHERE emp.username IS NOT NULL
                ORDER BY emp.username
            """)
            return [row[0] for row in cur.fetchall()]
    finally:
        if conn: conn.close()

def mark_error_as_resolved(error_id):
    """Xətanın statusunu 'Həll Edildi' olaraq dəyişir."""
    conn = db_connect()
    if not conn: return
    try:
        with conn.cursor() as cur:
            cur.execute("UPDATE error_logs SET status = 'Həll Edildi' WHERE id = %s", (error_id,))
            conn.commit()
    finally:
        if conn: conn.close()

def delete_error_log(error_id):
    """Seçilmiş xəta qeydini jurnaldan silir."""
    conn = db_connect()
    if not conn: return
    try:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM error_logs WHERE id = %s", (error_id,))
            conn.commit()
    finally:
        if conn: conn.close()