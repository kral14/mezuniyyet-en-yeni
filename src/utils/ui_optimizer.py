#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
UI Refresh Optimizasiyası
Performanslı UI yeniləmə mexanizmi
"""

import threading
import time
from collections import deque
from typing import Dict, List, Callable, Any

class RefreshManager:
    """UI refresh əməliyyatlarını idarə edən sinif"""
    
    def __init__(self):
        self.pending_refreshes = deque()
        self.refresh_callbacks = {}
        self.last_refresh_time = {}
        self.refresh_throttle_ms = 100  # Minimum refresh interval
        self.batch_refresh_enabled = True
        self.batch_timer = None
        
    def register_callback(self, component_name: str, callback: Callable):
        """Refresh callback-i qeydiyyatdan keçirir"""
        self.refresh_callbacks[component_name] = callback
        self.last_refresh_time[component_name] = 0
        
    def schedule_refresh(self, component_name: str, priority: str = 'normal', data: Any = None):
        """Refresh əməliyyatını planlaşdırır"""
        current_time = time.time() * 1000  # milliseconds
        
        # Throttling yoxlaması
        if component_name in self.last_refresh_time:
            time_since_last = current_time - self.last_refresh_time[component_name]
            if time_since_last < self.refresh_throttle_ms:
                return  # Çox tez-tez refresh etmə
        
        refresh_item = {
            'component': component_name,
            'priority': priority,
            'data': data,
            'timestamp': current_time
        }
        
        # Priority əsasında sıralama
        if priority == 'high':
            self.pending_refreshes.appendleft(refresh_item)
        else:
            self.pending_refreshes.append(refresh_item)
        
        # Batch refresh-i başlat
        if self.batch_refresh_enabled:
            self._schedule_batch_refresh()
    
    def _schedule_batch_refresh(self):
        """Batch refresh-i planlaşdırır"""
        if self.batch_timer:
            return  # Artıq planlaşdırılıb
        
        def batch_refresh():
            try:
                self._execute_batch_refresh()
            finally:
                self.batch_timer = None
        
        # 50ms sonra batch refresh icra et
        self.batch_timer = threading.Timer(0.05, batch_refresh)
        self.batch_timer.start()
    
    def _execute_batch_refresh(self):
        """Batch refresh-i icra edir"""
        if not self.pending_refreshes:
            return
        
        # Komponentləri qruplaşdır
        component_groups = {}
        while self.pending_refreshes:
            item = self.pending_refreshes.popleft()
            component = item['component']
            
            if component not in component_groups:
                component_groups[component] = []
            component_groups[component].append(item)
        
        # Hər komponent üçün refresh icra et
        for component, items in component_groups.items():
            if component in self.refresh_callbacks:
                try:
                    # Ən son məlumatları istifadə et
                    latest_item = max(items, key=lambda x: x['timestamp'])
                    self.refresh_callbacks[component](latest_item['data'])
                    self.last_refresh_time[component] = latest_item['timestamp']
                except Exception as e:
                    print(f"⚠️ DEBUG: Refresh callback xətası ({component}): {e}")
    
    def force_refresh(self, component_name: str, data: Any = None):
        """Məcburi refresh icra edir"""
        if component_name in self.refresh_callbacks:
            try:
                self.refresh_callbacks[component_name](data)
                self.last_refresh_time[component_name] = time.time() * 1000
            except Exception as e:
                print(f"⚠️ DEBUG: Force refresh xətası ({component_name}): {e}")
    
    def clear_pending_refreshes(self, component_name: str = None):
        """Gözləyən refresh-ləri təmizləyir"""
        if component_name:
            # Müəyyən komponent üçün
            self.pending_refreshes = deque(
                item for item in self.pending_refreshes 
                if item['component'] != component_name
            )
        else:
            # Hamısını təmizlə
            self.pending_refreshes.clear()
    
    def set_throttle_interval(self, ms: int):
        """Refresh throttle interval-i təyin edir"""
        self.refresh_throttle_ms = ms
    
    def enable_batch_refresh(self, enabled: bool):
        """Batch refresh-i aktiv/deaktiv edir"""
        self.batch_refresh_enabled = enabled
        if not enabled and self.batch_timer:
            self.batch_timer.cancel()
            self.batch_timer = None

class PerformanceMonitor:
    """Performans monitorinqi"""
    
    def __init__(self):
        self.operation_times = {}
        self.operation_counts = {}
        self.slow_operations = []
        
    def start_operation(self, operation_name: str):
        """Əməliyyatı başladır"""
        self.operation_times[operation_name] = time.time()
        
    def end_operation(self, operation_name: str):
        """Əməliyyatı bitirir və vaxtı qeyd edir"""
        if operation_name in self.operation_times:
            duration = time.time() - self.operation_times[operation_name]
            
            # Operation count artır
            if operation_name not in self.operation_counts:
                self.operation_counts[operation_name] = 0
            self.operation_counts[operation_name] += 1
            
            # Yavaş əməliyyatları qeyd et
            if duration > 1.0:  # 1 saniyədən çox
                self.slow_operations.append({
                    'operation': operation_name,
                    'duration': duration,
                    'timestamp': time.time()
                })
            
            print(f"⏱️ DEBUG: {operation_name} tamamlandı - {duration:.2f}s")
            return duration
        
        return 0
    
    def get_performance_summary(self):
        """Performans xülasəsini qaytarır"""
        return {
            'operation_counts': dict(self.operation_counts),
            'slow_operations': self.slow_operations[-10:],  # Son 10 yavaş əməliyyat
            'total_operations': sum(self.operation_counts.values())
        }

# Global instance
refresh_manager = RefreshManager()
performance_monitor = PerformanceMonitor()

def optimize_ui_refresh():
    """UI refresh-i optimizasiya edir"""
    return refresh_manager

def monitor_performance():
    """Performans monitorinqi"""
    return performance_monitor
