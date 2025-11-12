#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Log Helper - Bütün log faylları üçün vahid helper funksiyalar
"""

import os
import sys
from datetime import datetime
from pathlib import Path

# Global current user ID - proqram başlayanda təyin ediləcək
_current_user_id = None

def set_current_user_id(user_id):
    """Cari istifadəçi ID-ni təyin edir"""
    global _current_user_id
    _current_user_id = user_id

def get_current_user_id():
    """Cari istifadəçi ID-ni qaytarır"""
    return _current_user_id


def get_debug_logs_dir():
    """
    Debug logs qovluğunun yolunu qaytarır
    EXE rejimində: %APPDATA%\MezuniyyetSistemi\debug_logs
    Normal rejimdə: debug_logs (cari qovluqda)
    """
    if getattr(sys, 'frozen', False):
        # EXE rejimində - AppData qovluğunda
        app_data_dir = os.path.join(os.getenv('APPDATA', ''), 'MezuniyyetSistemi')
        debug_logs_dir = os.path.join(app_data_dir, 'debug_logs')
    else:
        # Normal rejimdə - cari qovluqda
        debug_logs_dir = 'debug_logs'
    
    # Qovluğu yarat
    os.makedirs(debug_logs_dir, exist_ok=True)
    return debug_logs_dir


def get_log_file_path(log_name, with_timestamp=True):
    """
    Log faylının tam yolunu qaytarır
    
    Args:
        log_name: Log faylının adı (məsələn: 'debug_console.log', 'email_service.log')
        with_timestamp: Əgər True olarsa, hər dəfə yeni timestamp ilə fayl yaradır
    
    Returns:
        Log faylının tam yolu
    """
    debug_logs_dir = get_debug_logs_dir()
    
    if with_timestamp:
        # Timestamp əlavə et
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        # Fayl adını və uzantısını ayır
        if '.' in log_name:
            name, ext = log_name.rsplit('.', 1)
            log_file_name = f"{name}_{timestamp}.{ext}"
        else:
            log_file_name = f"{log_name}_{timestamp}.log"
    else:
        log_file_name = log_name
    
    return os.path.join(debug_logs_dir, log_file_name)


def archive_existing_log(log_name):
    """
    Mövcud log faylını arxiv edir (timestamp ilə)
    
    Args:
        log_name: Log faylının adı
    """
    try:
        debug_logs_dir = get_debug_logs_dir()
        log_file_path = os.path.join(debug_logs_dir, log_name)
        
        if os.path.exists(log_file_path):
            # Timestamp əlavə et
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            if '.' in log_name:
                name, ext = log_name.rsplit('.', 1)
                archive_name = f"{name}_{timestamp}.{ext}"
            else:
                archive_name = f"{log_name}_{timestamp}.log"
            
            archive_path = os.path.join(debug_logs_dir, archive_name)
            os.rename(log_file_path, archive_path)
    except Exception as e:
        # Xəta olsa belə davam et
        pass

def log_to_database_async(log_type, log_content, log_file_name=None):
    """
    Log məlumatını verilənlər bazasına asinxron yazır
    Xəta olsa belə proqramı dayandırmır
    
    Args:
        log_type: Log növü (debug_console, realtime_debug, email_service, unified_app_debug)
        log_content: Log məzmunu
        log_file_name: Log faylının adı
    """
    try:
        user_id = get_current_user_id()
        if not user_id:
            # İstifadəçi ID yoxdursa, yazmırıq
            return
        
        # Verilənlər bazasına yazmaq üçün import et
        try:
            from database.error_queries import log_to_database
        except ImportError:
            try:
                from src.database.error_queries import log_to_database
            except ImportError:
                return
        
        # Asinxron yazmaq üçün thread istifadə et
        import threading
        def write_log():
            try:
                log_to_database(user_id, log_type, log_content, log_file_name)
            except Exception:
                # Xəta olsa belə davam et
                pass
        
        thread = threading.Thread(target=write_log, daemon=True)
        thread.start()
    except Exception:
        # Xəta olsa belə davam et
        pass

def check_and_process_deletion_signals(user_id):
    """
    Silmə siqnallarını yoxlayır və lokal log fayllarını silir
    
    Args:
        user_id: İstifadəçi ID-si
    
    Returns:
        Silinmiş fayl adlarının siyahısı
    """
    deleted_files = []
    try:
        # Verilənlər bazasından silmə siqnallarını al
        try:
            from database.error_queries import get_pending_deletion_signals, mark_deletion_signals_processed
        except ImportError:
            try:
                from src.database.error_queries import get_pending_deletion_signals, mark_deletion_signals_processed
            except ImportError:
                return deleted_files
        
        # Gözləyən silmə siqnallarını al
        deletion_signals = get_pending_deletion_signals(user_id)
        
        if not deletion_signals:
            return deleted_files
        
        debug_logs_dir = get_debug_logs_dir()
        processed_files = []
        
        # Hər siqnal üçün faylı sil
        for log_file_name, log_type in deletion_signals:
            if not log_file_name:
                continue
            
            try:
                log_file_path = os.path.join(debug_logs_dir, log_file_name)
                
                # Əgər fayl mövcuddursa, sil
                if os.path.exists(log_file_path):
                    try:
                        os.remove(log_file_path)
                        deleted_files.append(log_file_name)
                        processed_files.append(log_file_name)
                        print(f"✅ Log faylı silindi: {log_file_name}")
                    except Exception as e:
                        print(f"⚠️ Log faylı silinə bilmədi {log_file_name}: {e}")
                else:
                    # Fayl yoxdursa da, siqnalı işlənmiş kimi işarələ
                    processed_files.append(log_file_name)
            except Exception:
                pass
        
        # İşlənmiş siqnalları işarələ
        if processed_files:
            try:
                mark_deletion_signals_processed(user_id, processed_files)
            except Exception:
                pass
        
        if deleted_files:
            print(f"✅ {len(deleted_files)} log faylı silmə siqnalına görə silindi")
        
    except Exception as e:
        # Xəta olsa belə davam et
        pass
    
    return deleted_files

def sync_existing_logs_to_database(user_id):
    """
    Mövcud log fayllarını verilənlər bazasına sinxronlaşdırır
    Proqram başlayanda və ya login zamanı çağırılmalıdır
    ƏVVƏLCƏ silmə siqnallarını yoxlayır və faylları silir
    
    Args:
        user_id: İstifadəçi ID-si
    """
    try:
        # ƏVVƏLCƏ: Silmə siqnallarını yoxla və faylları sil
        check_and_process_deletion_signals(user_id)
        
        debug_logs_dir = get_debug_logs_dir()
        if not os.path.exists(debug_logs_dir):
            return
        
        # Verilənlər bazasına yazmaq üçün import et
        try:
            from database.error_queries import log_to_database, get_user_logs
        except ImportError:
            try:
                from src.database.error_queries import log_to_database, get_user_logs
            except ImportError:
                return
        
        # Bazada mövcud log fayllarının siyahısını al (duplikat yoxlamaq üçün)
        existing_logs = {}
        try:
            user_logs = get_user_logs(user_id=user_id, limit=10000)
            for log in user_logs:
                log_file_name = log[6]  # log_file_name sütunu
                if log_file_name:
                    existing_logs[log_file_name] = True
        except Exception:
            pass
        
        # Log fayllarını tap və sinxronlaşdır
        log_patterns = {
            'debug_console': 'debug_console_*.log',
            'realtime_debug': 'realtime_debug_*.log',
            'email_service': 'email_service_*.log',
            'unified_app_debug': 'unified_app_debug_*.log'
        }
        
        import glob
        synced_count = 0
        
        for log_type, pattern in log_patterns.items():
            log_files = glob.glob(os.path.join(debug_logs_dir, pattern))
            
            for log_file_path in log_files:
                try:
                    log_file_name = os.path.basename(log_file_path)
                    
                    # Əgər bu fayl artıq bazada varsa, atla
                    if log_file_name in existing_logs:
                        continue
                    
                    # Faylın məzmununu oxu
                    try:
                        with open(log_file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            log_content = f.read()
                    except Exception:
                        # Əgər oxuya bilməsək, atla
                        continue
                    
                    # Əgər fayl boşdursa, atla
                    if not log_content.strip():
                        continue
                    
                    # Bazaya yaz
                    try:
                        log_to_database(user_id, log_type, log_content, log_file_name)
                        synced_count += 1
                    except Exception:
                        # Xəta olsa belə davam et
                        pass
                        
                except Exception:
                    # Xəta olsa belə davam et
                    pass
        
        if synced_count > 0:
            print(f"✅ {synced_count} log faylı verilənlər bazasına sinxronlaşdırıldı")
        
    except Exception as e:
        # Xəta olsa belə davam et - sinxronlaşdırma proqramı dayandırmamalıdır
        pass

