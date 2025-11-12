#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Real-time sinxronizasiya üçün güclü debug sistemi
"""

import logging
import time
import json
from datetime import datetime
from pathlib import Path
import os

class RealtimeDebugger:
    def __init__(self, debug_file="realtime_debug.log"):
        self.debug_file = debug_file
        self.start_time = time.time()
        self.operation_count = 0
        
        # Debug faylını hazırla
        self.setup_debug_file()
        
        # Debug logger yaradır
        self.logger = self.setup_logger()
        
    def setup_debug_file(self):
        """Debug faylını hazırlayır"""
        try:
            # Log helper istifadə et
            try:
                from utils.log_helper import get_log_file_path, archive_existing_log
            except ImportError:
                from src.utils.log_helper import get_log_file_path, archive_existing_log
            
            # Mövcud log faylını arxiv et
            archive_existing_log(self.debug_file)
            
            # Yeni log faylının yolunu al (timestamp ilə)
            self.debug_file_path = Path(get_log_file_path(self.debug_file, with_timestamp=True))
                
        except Exception as e:
            print(f"Debug faylı hazırlanarkən xəta: {e}")
    
    def setup_logger(self):
        """Debug logger yaradır"""
        logger = logging.getLogger('realtime_debug')
        logger.setLevel(logging.DEBUG)
        
        # Fayl handler - hər dəfə yeni fayl yaradır
        file_handler = logging.FileHandler(self.debug_file_path, encoding='utf-8', mode='w')
        file_handler.setLevel(logging.DEBUG)
        
        # Format
        formatter = logging.Formatter(
            '%(asctime)s | %(levelname)s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(formatter)
        
        logger.addHandler(file_handler)
        return logger
    
    def log_operation(self, operation_type, details=None, source="unknown"):
        """Əməliyyatı log edir"""
        self.operation_count += 1
        elapsed_time = time.time() - self.start_time
        
        message = f"""
{'='*80}
OPERATION #{self.operation_count} | ELAPSED: {elapsed_time:.3f}s | SOURCE: {source}
TYPE: {operation_type}
TIME: {datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')}
DETAILS: {json.dumps(details, indent=2, ensure_ascii=False) if details else 'None'}
{'='*80}
"""
        self.logger.info(message)
        
        # Verilənlər bazasına da yaz
        try:
            try:
                from utils.log_helper import log_to_database_async
            except ImportError:
                from src.utils.log_helper import log_to_database_async
            
            log_file_name = str(self.debug_file_path) if hasattr(self, 'debug_file_path') else None
            if log_file_name:
                import os
                log_file_name = os.path.basename(log_file_name)
            log_to_database_async('realtime_debug', message, log_file_name)
        except Exception:
            pass
        
        # Console-a da yazdır
        print(f"DEBUG #{self.operation_count}: {operation_type} | {source} | {elapsed_time:.3f}s")
    
    def log_signal_sent(self, signal_type, details=None, source="unknown"):
        """Göndərilən signalı log edir"""
        self.log_operation(f"SIGNAL_SENT_{signal_type}", details, source)
    
    def log_signal_received(self, signal_type, details=None, source="unknown"):
        """Alınan signalı log edir"""
        self.log_operation(f"SIGNAL_RECEIVED_{signal_type}", details, source)
    
    def log_data_change(self, change_type, data_before=None, data_after=None, source="unknown"):
        """Məlumat dəyişikliyini log edir"""
        details = {
            "change_type": change_type,
            "data_before": data_before,
            "data_after": data_after
        }
        self.log_operation(f"DATA_CHANGE_{change_type}", details, source)
    
    def log_ui_update(self, ui_component, action, details=None, source="unknown"):
        """UI yeniləməsini log edir"""
        self.log_operation(f"UI_UPDATE_{ui_component}_{action}", details, source)
    
    def log_cache_operation(self, operation, cache_data=None, source="unknown"):
        """Cache əməliyyatını log edir"""
        self.log_operation(f"CACHE_{operation}", cache_data, source)
    
    def log_network_operation(self, operation, url=None, status=None, response_time=None, source="unknown"):
        """Şəbəkə əməliyyatını log edir"""
        details = {
            "url": url,
            "status": status,
            "response_time": response_time
        }
        self.log_operation(f"NETWORK_{operation}", details, source)
    
    def log_error(self, error_type, error_message, stack_trace=None, source="unknown"):
        """Xətanı log edir"""
        details = {
            "error_type": error_type,
            "error_message": error_message,
            "stack_trace": stack_trace
        }
        self.log_operation(f"ERROR_{error_type}", details, source)
    
    def log_performance(self, operation, duration, details=None, source="unknown"):
        """Performans məlumatını log edir"""
        details = details or {}
        details["duration_ms"] = duration * 1000
        self.log_operation(f"PERFORMANCE_{operation}", details, source)
    
    def log_sync_event(self, event_type, from_program, to_program, data=None):
        """Sinxronizasiya hadisəsini log edir"""
        details = {
            "from_program": from_program,
            "to_program": to_program,
            "data": data
        }
        self.log_operation(f"SYNC_{event_type}", details, f"{from_program}->{to_program}")
    
    def get_debug_summary(self):
        """Debug xülasəsini qaytarır"""
        elapsed_time = time.time() - self.start_time
        return {
            "total_operations": self.operation_count,
            "elapsed_time": elapsed_time,
            "operations_per_second": self.operation_count / elapsed_time if elapsed_time > 0 else 0,
            "debug_file": str(self.debug_file_path)
        }
    
    def print_summary(self):
        """Debug xülasəsini yazdırır"""
        summary = self.get_debug_summary()
        print(f"""
{'='*60}
📊 REAL-TIME DEBUG SUMMARY
{'='*60}
🔢 Total Operations: {summary['total_operations']}
⏱️  Elapsed Time: {summary['elapsed_time']:.3f}s
🚀 Operations/Second: {summary['operations_per_second']:.2f}
📁 Debug File: {summary['debug_file']}
{'='*60}
""")

# Global debug instance
debugger = None

def init_debugger(debug_file="realtime_debug.log"):
    """Global debugger instance-ini başladır"""
    global debugger
    debugger = RealtimeDebugger(debug_file)
    return debugger

def get_debugger():
    """Global debugger instance-ini qaytarır"""
    return debugger

def log_signal_sent(signal_type, details=None, source="unknown"):
    """Göndərilən signalı log edir"""
    global debugger
    if debugger:
        debugger.log_signal_sent(signal_type, details, source)

def log_signal_received(signal_type, details=None, source="unknown"):
    """Alınan signalı log edir"""
    global debugger
    if debugger:
        debugger.log_signal_received(signal_type, details, source)

def log_data_change(change_type, data_before=None, data_after=None, source="unknown"):
    """Məlumat dəyişikliyini log edir"""
    global debugger
    if debugger:
        debugger.log_data_change(change_type, data_before, data_after, source)

def log_ui_update(ui_component, action, details=None, source="unknown"):
    """UI yeniləməsini log edir"""
    global debugger
    if debugger:
        debugger.log_ui_update(ui_component, action, details, source)

def log_cache_operation(operation, cache_data=None, source="unknown"):
    """Cache əməliyyatını log edir"""
    global debugger
    if debugger:
        debugger.log_cache_operation(operation, cache_data, source)

def log_network_operation(operation, url=None, status=None, response_time=None, source="unknown"):
    """Şəbəkə əməliyyatını log edir"""
    global debugger
    if debugger:
        debugger.log_network_operation(operation, url, status, response_time, source)

def log_error(error_type, error_message, stack_trace=None, source="unknown"):
    """Xətanı log edir"""
    global debugger
    if debugger:
        debugger.log_error(error_type, error_message, stack_trace, source)

def log_performance(operation, duration, details=None, source="unknown"):
    """Performans məlumatını log edir"""
    global debugger
    if debugger:
        debugger.log_performance(operation, duration, details, source)

def log_sync_event(event_type, from_program, to_program, data=None):
    """Sinxronizasiya hadisəsini log edir"""
    global debugger
    if debugger:
        debugger.log_sync_event(event_type, from_program, to_program, data) 