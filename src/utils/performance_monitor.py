#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Performance Monitor - UI bloklanmasını izləyir və loglaşdırır
"""

import time
import threading
import sys
import traceback
from collections import deque

class PerformanceMonitor:
    """UI bloklanmasını izləyir"""
    
    def __init__(self):
        self.monitoring = False
        self.monitor_thread = None
        self.blocking_operations = deque(maxlen=100)
        self.last_check_time = time.time()
        self.ui_responsive = True
        
    def start_monitoring(self):
        """Monitoring-i başlat"""
        if self.monitoring:
            return
        
        self.monitoring = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        print("🔍 Performance monitor başladıldı")
    
    def stop_monitoring(self):
        """Monitoring-i dayandır"""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=1)
        print("🛑 Performance monitor dayandırıldı")
    
    def _monitor_loop(self):
        """Monitoring loop"""
        while self.monitoring:
            try:
                current_time = time.time()
                elapsed = current_time - self.last_check_time
                
                # Əgər 1 saniyədən çox keçibsə, UI bloklanıb deməkdir
                if elapsed > 1.0:
                    self._log_blocking_operation(elapsed)
                
                self.last_check_time = current_time
                time.sleep(0.1)  # 100ms interval
            except Exception:
                pass
    
    def _log_blocking_operation(self, duration):
        """Bloklanan əməliyyatı logla"""
        try:
            import traceback
            stack = traceback.extract_stack()
            # Son 5 frame-i götür
            relevant_frames = stack[-5:] if len(stack) > 5 else stack
            stack_str = "\n".join([f"  {f.filename}:{f.lineno} in {f.name}" for f in relevant_frames])
            
            operation = {
                'duration': duration,
                'timestamp': time.time(),
                'stack': stack_str
            }
            self.blocking_operations.append(operation)
            
            print(f"⚠️ UI bloklanması aşkar edildi: {duration:.2f}s")
            print(f"Stack trace:\n{stack_str}")
        except Exception:
            pass
    
    def mark_ui_responsive(self):
        """UI-nin responsive olduğunu qeyd et"""
        self.last_check_time = time.time()
        self.ui_responsive = True
    
    def get_blocking_operations(self):
        """Bloklanan əməliyyatları qaytar"""
        return list(self.blocking_operations)

# Global instance
_performance_monitor = None

def get_performance_monitor():
    """Global performance monitor instance"""
    global _performance_monitor
    if _performance_monitor is None:
        _performance_monitor = PerformanceMonitor()
    return _performance_monitor

def start_monitoring():
    """Monitoring-i başlat"""
    get_performance_monitor().start_monitoring()

def stop_monitoring():
    """Monitoring-i dayandır"""
    get_performance_monitor().stop_monitoring()

def mark_ui_responsive():
    """UI-nin responsive olduğunu qeyd et"""
    get_performance_monitor().mark_ui_responsive()

def monitor_operation(operation_name):
    """
    Decorator - funksiyanın icra vaxtını izləyir
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                elapsed = time.time() - start_time
                # Yalnız uzun əməliyyatları logla (1 saniyədən çox)
                if elapsed > 1.0:
                    print(f"⏱️ {operation_name} tamamlandı: {elapsed:.2f}s")
                return result
            except Exception as e:
                elapsed = time.time() - start_time
                print(f"❌ {operation_name} xəta ilə bitdi ({elapsed:.2f}s): {e}")
                raise
        return wrapper
    return decorator
