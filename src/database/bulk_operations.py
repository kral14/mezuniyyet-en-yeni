#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Toplu Məzuniyyət Silmə Funksiyası
Performans optimizasiyası üçün bulk operations
"""

import threading
import time
from tkinter import messagebox
from database.connection import db_connect
from database.connection_pool import get_connection_pool
from utils.debug_manager import debug_log

def bulk_delete_vacations(vacation_ids, admin_name, progress_callback=None):
    """
    Toplu məzuniyyət silmə funksiyası
    Background thread-də işləyir və UI-ni bloklamır
    
    Args:
        vacation_ids: Silinəcək məzuniyyət ID-ləri listi
        admin_name: Admin adı
        progress_callback: Progress callback funksiyası (optional)
    
    Returns:
        dict: {'success': bool, 'deleted_count': int, 'errors': list}
    """
    if not vacation_ids:
        return {'success': False, 'deleted_count': 0, 'errors': ['Məzuniyyət ID-ləri verilməyib']}
    
    debug_log('bulk_delete', f'Toplu silmə başladı: {len(vacation_ids)} məzuniyyət', '🔵')
    
    # Connection pool istifadə et
    try:
        pool = get_connection_pool()
        if pool:
            conn = pool.getconn()
        else:
            conn = db_connect()
    except Exception as e:
        debug_log('bulk_delete', f'Connection pool xətası: {e}', '❌')
        conn = db_connect()
    
    if not conn:
        return {'success': False, 'deleted_count': 0, 'errors': ['Database bağlantısı qurula bilmədi']}
    
    deleted_count = 0
    errors = []
    
    try:
        with conn.cursor() as cur:
            # Əvvəlcə silinəcək məzuniyyətlərin məlumatlarını al
            ids_tuple = tuple(vacation_ids)
            cur.execute("""
                SELECT id, employee_id, start_date, end_date 
                FROM vacations 
                WHERE id IN %s
            """, (ids_tuple,))
            
            vacations_to_delete = cur.fetchall()
            
            if not vacations_to_delete:
                return {'success': False, 'deleted_count': 0, 'errors': ['Məzuniyyətlər tapılmadı']}
            
            # Progress callback-i çağır
            if progress_callback:
                progress_callback(0, len(vacations_to_delete), "Məzuniyyətlər silinir...")
            
            # Toplu silmə əməliyyatı
            cur.execute("DELETE FROM vacations WHERE id IN %s", (ids_tuple,))
            deleted_count = cur.rowcount
            
            # Bildirişləri toplu şəkildə əlavə et
            notifications = []
            for vac_id, emp_id, start_date, end_date in vacations_to_delete:
                message = f"Admin '{admin_name}' sizin {start_date.strftime('%d.%m.%Y')} - {end_date.strftime('%d.%m.%Y')} arası sorğunuzu sildi."
                notifications.append((emp_id, message, None))
            
            if notifications:
                cur.executemany("""
                    INSERT INTO notifications (recipient_id, message, related_vacation_id) 
                    VALUES (%s, %s, %s)
                """, notifications)
            
            conn.commit()
            
            # Progress callback-i tamamlandı kimi işarələ
            if progress_callback:
                progress_callback(len(vacations_to_delete), len(vacations_to_delete), "Tamamlandı!")
            
            debug_log('bulk_delete', f'Toplu silmə uğurlu: {deleted_count} məzuniyyət silindi', '✅')
            
            return {
                'success': True, 
                'deleted_count': deleted_count, 
                'errors': errors
            }
            
    except Exception as e:
        conn.rollback()
        error_msg = f"Toplu silmə xətası: {str(e)}"
        debug_log('bulk_delete', error_msg, '❌')
        return {'success': False, 'deleted_count': deleted_count, 'errors': [error_msg]}
    
    finally:
        if conn:
            try:
                pool = get_connection_pool()
                if pool:
                    pool.putconn(conn)
                else:
                    conn.close()
            except Exception as e:
                debug_log('bulk_delete', f'Connection qaytarılarkən xəta: {e}', '⚠️')
                conn.close()

def bulk_delete_vacations_threaded(vacation_ids, admin_name, success_callback=None, error_callback=None, progress_callback=None):
    """
    Toplu silmə əməliyyatını background thread-də icra edir
    UI thread-i bloklamır
    """
    def _bulk_delete_worker():
        try:
            result = bulk_delete_vacations(vacation_ids, admin_name, progress_callback)
            
            if result['success']:
                if success_callback:
                    success_callback(result)
            else:
                if error_callback:
                    error_callback(result)
                    
        except Exception as e:
            error_result = {'success': False, 'deleted_count': 0, 'errors': [str(e)]}
            if error_callback:
                error_callback(error_result)
    
    # Background thread-də işlə
    thread = threading.Thread(target=_bulk_delete_worker, daemon=True)
    thread.start()
    return thread

def bulk_update_vacation_status(vacation_ids, new_status, admin_name, progress_callback=None):
    """
    Toplu məzuniyyət status yeniləmə funksiyası
    """
    if not vacation_ids:
        return {'success': False, 'updated_count': 0, 'errors': ['Məzuniyyət ID-ləri verilməyib']}
    
    debug_log('bulk_update', f'Toplu status yeniləmə başladı: {len(vacation_ids)} məzuniyyət', '🔵')
    
    # Connection pool istifadə et
    try:
        pool = get_connection_pool()
        if pool:
            conn = pool.getconn()
        else:
            conn = db_connect()
    except Exception as e:
        debug_log('bulk_update', f'Connection pool xətası: {e}', '❌')
        conn = db_connect()
    
    if not conn:
        return {'success': False, 'updated_count': 0, 'errors': ['Database bağlantısı qurula bilmədi']}
    
    updated_count = 0
    errors = []
    
    try:
        with conn.cursor() as cur:
            # Əvvəlcə yenilənəcək məzuniyyətlərin məlumatlarını al
            ids_tuple = tuple(vacation_ids)
            cur.execute("""
                SELECT id, employee_id, start_date, end_date 
                FROM vacations 
                WHERE id IN %s
            """, (ids_tuple,))
            
            vacations_to_update = cur.fetchall()
            
            if not vacations_to_update:
                return {'success': False, 'updated_count': 0, 'errors': ['Məzuniyyətlər tapılmadı']}
            
            # Progress callback-i çağır
            if progress_callback:
                progress_callback(0, len(vacations_to_update), "Statuslar yenilənir...")
            
            # Toplu status yeniləmə
            cur.execute("UPDATE vacations SET status = %s WHERE id IN %s", (new_status, ids_tuple))
            updated_count = cur.rowcount
            
            # Bildirişləri toplu şəkildə əlavə et
            status_az = "Təsdiqləndi" if new_status == 'approved' else "Rədd edildi"
            notifications = []
            
            for vac_id, emp_id, start_date, end_date in vacations_to_update:
                message = f"Admin '{admin_name}', sizin {start_date.strftime('%d.%m.%Y')} - {end_date.strftime('%d.%m.%Y')} arası sorğunuzu '{status_az}' statusu ilə yenilədi."
                notifications.append((emp_id, message, vac_id))
            
            if notifications:
                cur.executemany("""
                    INSERT INTO notifications (recipient_id, message, related_vacation_id) 
                    VALUES (%s, %s, %s)
                """, notifications)
            
            conn.commit()
            
            # Progress callback-i tamamlandı kimi işarələ
            if progress_callback:
                progress_callback(len(vacations_to_update), len(vacations_to_update), "Tamamlandı!")
            
            debug_log('bulk_update', f'Toplu status yeniləmə uğurlu: {updated_count} məzuniyyət yeniləndi', '✅')
            
            return {
                'success': True, 
                'updated_count': updated_count, 
                'errors': errors
            }
            
    except Exception as e:
        conn.rollback()
        error_msg = f"Toplu status yeniləmə xətası: {str(e)}"
        debug_log('bulk_update', error_msg, '❌')
        return {'success': False, 'updated_count': updated_count, 'errors': [error_msg]}
    
    finally:
        if conn:
            try:
                pool = get_connection_pool()
                if pool:
                    pool.putconn(conn)
                else:
                    conn.close()
            except Exception as e:
                debug_log('bulk_update', f'Connection qaytarılarkən xəta: {e}', '⚠️')
                conn.close()

def bulk_update_vacation_status_threaded(vacation_ids, new_status, admin_name, success_callback=None, error_callback=None, progress_callback=None):
    """
    Toplu status yeniləmə əməliyyatını background thread-də icra edir
    """
    def _bulk_update_worker():
        try:
            result = bulk_update_vacation_status(vacation_ids, new_status, admin_name, progress_callback)
            
            if result['success']:
                if success_callback:
                    success_callback(result)
            else:
                if error_callback:
                    error_callback(result)
                    
        except Exception as e:
            error_result = {'success': False, 'updated_count': 0, 'errors': [str(e)]}
            if error_callback:
                error_callback(error_result)
    
    # Background thread-də işlə
    thread = threading.Thread(target=_bulk_update_worker, daemon=True)
    thread.start()
    return thread
