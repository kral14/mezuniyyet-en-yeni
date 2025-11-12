#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Real-time debug məlumatlarını göstərmək üçün pəncərə
"""

import ttkbootstrap as tb
from ttkbootstrap.constants import *
import tkinter as tk
from tkinter import ttk, messagebox
import logging
from datetime import datetime
import threading
import time
import json
import os
import glob
from pathlib import Path

class DebugViewerWindow(tb.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.title("🔍 Real-Time Debug Viewer")
        self.geometry("1200x800")
        self.resizable(True, True)
        
        # Pəncərəni mərkəzləşdir
        self.center_window()
        
        # Pəncərəni modal et
        self.transient(parent)
        self.grab_set()
        
        # Debug faylını izlə - ən son log faylını tap
        try:
            try:
                from utils.log_helper import get_debug_logs_dir
            except ImportError:
                from src.utils.log_helper import get_debug_logs_dir
            
            debug_logs_dir = get_debug_logs_dir()
            # Ən son realtime_debug log faylını tap
            log_files = glob.glob(os.path.join(debug_logs_dir, 'realtime_debug_*.log'))
            if log_files:
                # Ən son faylı seç
                self.debug_file_path = Path(max(log_files, key=os.path.getmtime))
            else:
                # Əgər timestamp ilə fayl yoxdursa, sadə adı istifadə et
                self.debug_file_path = Path(os.path.join(debug_logs_dir, 'realtime_debug.log'))
        except Exception:
            # Fallback
            self.debug_file_path = Path("debug_logs/realtime_debug.log")
        
        self.last_file_size = 0
        self.last_content = ""
        
        self.create_widgets()
        self.start_monitoring()
        
    def center_window(self):
        """Pəncərəni mərkəzləşdirir"""
        self.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - (1200 // 2)
        y = (self.winfo_screenheight() // 2) - (800 // 2)
        self.geometry(f"1200x800+{x}+{y}")
        
    def create_widgets(self):
        """Widget-ləri yaradır"""
        # Başlıq
        header_frame = tb.Frame(self)
        header_frame.pack(fill='x', padx=10, pady=10)
        
        tb.Label(header_frame, text="🔍 Real-Time Debug Viewer", font=('Helvetica', 16, 'bold')).pack(side='left')
        
        # Status göstəricisi
        self.status_label = tb.Label(header_frame, text="🔴 Debug faylı izlənir...", font=('Helvetica', 10))
        self.status_label.pack(side='right')
        
        # Kontrol paneli
        control_frame = tb.LabelFrame(self, text="🎛️ Kontrol Panel", bootstyle="secondary")
        control_frame.pack(fill='x', padx=10, pady=5)
        
        # Auto-scroll checkbox
        self.auto_scroll_var = tk.BooleanVar(value=True)
        auto_scroll_cb = tb.Checkbutton(
            control_frame, 
            text="Auto-scroll", 
            variable=self.auto_scroll_var,
            bootstyle="round-toggle"
        )
        auto_scroll_cb.pack(side='left', padx=10, pady=5)
        
        # Clear log düyməsi
        clear_btn = tb.Button(
            control_frame, 
            text="🗑️ Log Təmizlə", 
            command=self.clear_log,
            bootstyle="warning"
        )
        clear_btn.pack(side='left', padx=10, pady=5)
        
        # Export düyməsi
        export_btn = tb.Button(
            control_frame, 
            text="📤 Export", 
            command=self.export_log,
            bootstyle="info"
        )
        export_btn.pack(side='left', padx=10, pady=5)
        
        # Filter frame
        filter_frame = tb.Frame(control_frame)
        filter_frame.pack(side='right', padx=10, pady=5)
        
        tb.Label(filter_frame, text="Filter:").pack(side='left')
        self.filter_var = tk.StringVar(value="ALL")
        filter_combo = ttk.Combobox(
            filter_frame, 
            textvariable=self.filter_var,
            values=["ALL", "SIGNAL_SENT", "SIGNAL_RECEIVED", "DATA_CHANGE", "UI_UPDATE", "CACHE", "NETWORK", "ERROR", "PERFORMANCE", "SYNC"],
            width=15
        )
        filter_combo.pack(side='left', padx=5)
        filter_combo.bind('<<ComboboxSelected>>', self.apply_filter)
        
        # Debug log
        log_frame = tb.LabelFrame(self, text="📝 Real-Time Debug Log", bootstyle="secondary")
        log_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        # Log text widget
        self.log_text = tk.Text(
            log_frame,
            font=('Consolas', 9),
            wrap='word',
            bg='#1e1e1e',
            fg='#ffffff',
            insertbackground='#ffffff'
        )
        self.log_text.pack(side='left', fill='both', expand=True, padx=5, pady=5)
        
        # Scrollbar
        log_scrollbar = ttk.Scrollbar(log_frame, orient='vertical', command=self.log_text.yview)
        log_scrollbar.pack(side='right', fill='y')
        self.log_text.config(yscrollcommand=log_scrollbar.set)
        
        # Alt düymələr
        bottom_frame = tb.Frame(self)
        bottom_frame.pack(fill='x', padx=10, pady=10)
        
        # Stats
        self.stats_label = tb.Label(bottom_frame, text="📊 Stats: 0 operations", font=('Helvetica', 9))
        self.stats_label.pack(side='left')
        
        tb.Button(bottom_frame, text="❌ Bağla", command=self.destroy, bootstyle="danger").pack(side='right')
        
    def start_monitoring(self):
        """Debug faylını izləməyə başladır"""
        self.monitor_timer = self.after(100, self.check_debug_file)
        
    def check_debug_file(self):
        """Debug faylını yoxlayır"""
        try:
            if self.debug_file_path.exists():
                current_size = self.debug_file_path.stat().st_size
                
                if current_size != self.last_file_size:
                    # Fayl dəyişib, yeni məzmunu oxu
                    with open(self.debug_file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    if content != self.last_content:
                        # Yeni məzmun var, göstər
                        self.update_log_display(content)
                        self.last_content = content
                    
                    self.last_file_size = current_size
                    self.status_label.config(text="🟢 Debug faylı izlənir", foreground='green')
                else:
                    self.status_label.config(text="🟡 Debug faylı izlənir (dəyişiklik yoxdur)", foreground='orange')
            else:
                self.status_label.config(text="🔴 Debug faylı tapılmadı", foreground='red')
                
        except Exception as e:
            self.status_label.config(text=f"❌ Xəta: {e}", foreground='red')
        
        # Növbəti yoxlama
        self.monitor_timer = self.after(100, self.check_debug_file)
        
    def update_log_display(self, content):
        """Log məzmununu yeniləyir"""
        # Mövcud məzmunu təmizlə
        self.log_text.delete('1.0', tk.END)
        
        # Filter tətbiq et
        filtered_content = self.apply_content_filter(content)
        
        # Məzmunu əlavə et
        self.log_text.insert('1.0', filtered_content)
        
        # Auto-scroll
        if self.auto_scroll_var.get():
            self.log_text.see(tk.END)
        
        # Stats yenilə
        self.update_stats(filtered_content)
        
    def apply_content_filter(self, content):
        """Məzmunu filter edir"""
        filter_type = self.filter_var.get()
        
        if filter_type == "ALL":
            return content
        
        lines = content.split('\n')
        filtered_lines = []
        
        for line in lines:
            if filter_type in line:
                filtered_lines.append(line)
        
        return '\n'.join(filtered_lines)
    
    def apply_filter(self, event=None):
        """Filter tətbiq edir"""
        if hasattr(self, 'last_content'):
            self.update_log_display(self.last_content)
    
    def update_stats(self, content):
        """Statistikaları yeniləyir"""
        lines = content.split('\n')
        operation_count = len([line for line in lines if 'OPERATION #' in line])
        
        # Əməliyyat növlərini say
        stats = {
            'SIGNAL_SENT': len([line for line in lines if 'SIGNAL_SENT' in line]),
            'SIGNAL_RECEIVED': len([line for line in lines if 'SIGNAL_RECEIVED' in line]),
            'DATA_CHANGE': len([line for line in lines if 'DATA_CHANGE' in line]),
            'UI_UPDATE': len([line for line in lines if 'UI_UPDATE' in line]),
            'CACHE': len([line for line in lines if 'CACHE_' in line]),
            'NETWORK': len([line for line in lines if 'NETWORK_' in line]),
            'ERROR': len([line for line in lines if 'ERROR_' in line]),
            'PERFORMANCE': len([line for line in lines if 'PERFORMANCE_' in line]),
            'SYNC': len([line for line in lines if 'SYNC_' in line])
        }
        
        stats_text = f"📊 Stats: {operation_count} operations | "
        stats_text += f"📡 Sent: {stats['SIGNAL_SENT']} | "
        stats_text += f"📥 Received: {stats['SIGNAL_RECEIVED']} | "
        stats_text += f"🔄 Sync: {stats['SYNC']}"
        
        self.stats_label.config(text=stats_text)
    
    def clear_log(self):
        """Log-u təmizləyir"""
        try:
            if self.debug_file_path.exists():
                with open(self.debug_file_path, 'w', encoding='utf-8') as f:
                    f.write("")
                self.log_text.delete('1.0', tk.END)
                self.last_content = ""
                self.last_file_size = 0
                messagebox.showinfo("Uğurlu", "Debug log təmizləndi!")
        except Exception as e:
            messagebox.showerror("Xəta", f"Log təmizlənərkən xəta: {e}")
    
    def export_log(self):
        """Log-u export edir"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            export_path = f"debug_logs/debug_export_{timestamp}.txt"
            
            with open(export_path, 'w', encoding='utf-8') as f:
                f.write(self.log_text.get('1.0', tk.END))
            
            messagebox.showinfo("Uğurlu", f"Debug log export edildi: {export_path}")
        except Exception as e:
            messagebox.showerror("Xəta", f"Export xətası: {e}")
    
    def destroy(self):
        """Pəncərəni bağlayır"""
        if hasattr(self, 'monitor_timer'):
            self.after_cancel(self.monitor_timer)
        super().destroy() 