#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Progress Indicator Komponenti
Uzun əməliyyatlar üçün progress bar və status göstəricisi
"""

import tkinter as tk
from tkinter import ttk
import threading
import time

class ProgressIndicator:
    """Uzun əməliyyatlar üçün progress göstəricisi"""
    
    def __init__(self, parent_window, title="Əməliyyat davam edir..."):
        self.parent_window = parent_window
        self.title = title
        self.progress_window = None
        self.progress_bar = None
        self.status_label = None
        self.cancel_button = None
        self.is_cancelled = False
        
    def show(self, max_value=100):
        """Progress window göstərir"""
        if self.progress_window:
            return
            
        # Progress window yaradır
        self.progress_window = tk.Toplevel(self.parent_window)
        self.progress_window.title(self.title)
        self.progress_window.geometry("400x150")
        self.progress_window.resizable(False, False)
        
        # Pəncərəni mərkəzləşdir
        self.progress_window.transient(self.parent_window)
        self.progress_window.grab_set()
        
        # Ana frame
        main_frame = ttk.Frame(self.progress_window, padding="20")
        main_frame.pack(expand=True, fill='both')
        
        # Status label
        self.status_label = ttk.Label(main_frame, text="Hazırlanır...", font=("Arial", 10))
        self.status_label.pack(pady=(0, 10))
        
        # Progress bar
        self.progress_bar = ttk.Progressbar(
            main_frame, 
            mode='determinate',
            maximum=max_value,
            length=350
        )
        self.progress_bar.pack(pady=(0, 15))
        
        # Cancel button
        button_frame = ttk.Frame(main_frame)
        button_frame.pack()
        
        self.cancel_button = ttk.Button(
            button_frame, 
            text="Ləğv et", 
            command=self.cancel
        )
        self.cancel_button.pack()
        
        # Pəncərəni mərkəzləşdir
        self.center_window()
        
        # Pəncərəni göstər
        self.progress_window.focus()
        
    def center_window(self):
        """Pəncərəni ekranın mərkəzində yerləşdirir"""
        self.progress_window.update_idletasks()
        
        # Ana pəncərənin koordinatları
        parent_x = self.parent_window.winfo_x()
        parent_y = self.parent_window.winfo_y()
        parent_width = self.parent_window.winfo_width()
        parent_height = self.parent_window.winfo_height()
        
        # Progress pəncərəsinin ölçüləri
        window_width = 400
        window_height = 150
        
        # Mərkəz koordinatları
        x = parent_x + (parent_width - window_width) // 2
        y = parent_y + (parent_height - window_height) // 2
        
        self.progress_window.geometry(f"{window_width}x{window_height}+{x}+{y}")
        
    def update(self, current_value, max_value=None, status_text=None):
        """Progress bar və status yeniləyir"""
        if not self.progress_window:
            return
            
        try:
            # Progress bar yenilə
            if max_value:
                self.progress_bar.config(maximum=max_value)
            self.progress_bar.config(value=current_value)
            
            # Status text yenilə
            if status_text:
                self.status_label.config(text=status_text)
            
            # UI-ni yenilə
            self.progress_window.update_idletasks()
            
        except tk.TclError:
            # Pəncərə bağlanıbsa, xəta vermə
            pass
            
    def set_status(self, status_text):
        """Yalnız status text yeniləyir"""
        if self.progress_window and self.status_label:
            try:
                self.status_label.config(text=status_text)
                self.progress_window.update_idletasks()
            except tk.TclError:
                pass
                
    def cancel(self):
        """Əməliyyatı ləğv edir"""
        self.is_cancelled = True
        if self.cancel_button:
            self.cancel_button.config(text="Ləğv edilir...", state='disabled')
        
    def hide(self):
        """Progress window gizlədir"""
        if self.progress_window:
            try:
                self.progress_window.grab_release()
                self.progress_window.destroy()
            except tk.TclError:
                pass
            finally:
                self.progress_window = None
                
    def is_cancelled(self):
        """Əməliyyatın ləğv edilib-edilmədiyini yoxlayır"""
        return self.is_cancelled

class BulkOperationDialog:
    """Toplu əməliyyatlar üçün dialoq pəncərəsi"""
    
    def __init__(self, parent, operation_type="sil"):
        self.parent = parent
        self.operation_type = operation_type
        self.dialog_window = None
        self.tree = None
        self.selected_items = []
        
    def show(self, vacation_data, callback=None):
        """Toplu əməliyyat dialoqunu göstərir"""
        self.dialog_window = tk.Toplevel(self.parent)
        self.dialog_window.title(f"Toplu {self.operation_type.capitalize()}mə")
        self.dialog_window.geometry("600x400")
        self.dialog_window.resizable(True, True)
        
        # Pəncərəni mərkəzləşdir
        self.dialog_window.transient(self.parent)
        self.dialog_window.grab_set()
        
        # Ana frame
        main_frame = ttk.Frame(self.dialog_window, padding="10")
        main_frame.pack(expand=True, fill='both')
        
        # Başlıq
        title_label = ttk.Label(
            main_frame, 
            text=f"Toplu {self.operation_type.capitalize()}mə", 
            font=("Arial", 12, "bold")
        )
        title_label.pack(pady=(0, 10))
        
        # Məzuniyyət siyahısı
        list_frame = ttk.LabelFrame(main_frame, text="Məzuniyyətlər", padding="5")
        list_frame.pack(expand=True, fill='both', pady=(0, 10))
        
        # Treeview yaradır
        columns = ('ID', 'İşçi', 'Başlama', 'Bitmə', 'Status')
        self.tree = ttk.Treeview(list_frame, columns=columns, show='headings', height=10)
        
        # Sütun başlıqları
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=100)
        
        # Scrollbar əlavə et
        scrollbar = ttk.Scrollbar(list_frame, orient='vertical', command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        # Pack et
        self.tree.pack(side='left', expand=True, fill='both')
        scrollbar.pack(side='right', fill='y')
        
        # Məlumatları doldur
        for vac in vacation_data:
            self.tree.insert('', 'end', values=(
                vac.get('db_id', ''),
                vac.get('employee_name', ''),
                vac.get('baslama', ''),
                vac.get('bitme', ''),
                vac.get('status', '')
            ))
        
        # Button frame
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill='x')
        
        # Seçim buttonları
        ttk.Button(button_frame, text="Hamısını seç", command=self.select_all).pack(side='left', padx=(0, 5))
        ttk.Button(button_frame, text="Seçimi ləğv et", command=self.deselect_all).pack(side='left', padx=(0, 5))
        
        # Əməliyyat buttonları
        ttk.Button(button_frame, text=f"Seçilənləri {self.operation_type}", command=self.execute_operation).pack(side='right', padx=(5, 0))
        ttk.Button(button_frame, text="Bağla", command=self.close).pack(side='right')
        
        # Pəncərəni mərkəzləşdir
        self.center_window()
        
        # Callback-i saxla
        self.callback = callback
        
    def center_window(self):
        """Pəncərəni ekranın mərkəzində yerləşdirir"""
        self.dialog_window.update_idletasks()
        
        # Ana pəncərənin koordinatları
        parent_x = self.parent.winfo_x()
        parent_y = self.parent.winfo_y()
        parent_width = self.parent.winfo_width()
        parent_height = self.parent.winfo_height()
        
        # Dialog pəncərəsinin ölçüləri
        window_width = 600
        window_height = 400
        
        # Mərkəz koordinatları
        x = parent_x + (parent_width - window_width) // 2
        y = parent_y + (parent_height - window_height) // 2
        
        self.dialog_window.geometry(f"{window_width}x{window_height}+{x}+{y}")
        
    def select_all(self):
        """Bütün elementləri seçir"""
        for item in self.tree.get_children():
            self.tree.selection_add(item)
            
    def deselect_all(self):
        """Bütün seçimləri ləğv edir"""
        self.tree.selection_remove(self.tree.selection())
        
    def execute_operation(self):
        """Seçilən elementlər üzərində əməliyyat icra edir"""
        selected_items = self.tree.selection()
        if not selected_items:
            tk.messagebox.showwarning("Xəbərdarlıq", "Heç bir məzuniyyət seçilməyib!")
            return
            
        # Təsdiq soruş
        if tk.messagebox.askyesno("Təsdiq", f"{len(selected_items)} məzuniyyəti {self.operation_type}mək istədiyinizə əminsiniz?"):
            # Seçilən ID-ləri al
            vacation_ids = []
            for item in selected_items:
                values = self.tree.item(item)['values']
                if values:
                    vacation_ids.append(values[0])  # ID sütunu
            
            # Callback-i çağır
            if self.callback:
                self.callback(vacation_ids)
                
            self.close()
            
    def close(self):
        """Dialoq pəncərəsini bağlayır"""
        if self.dialog_window:
            try:
                self.dialog_window.grab_release()
                self.dialog_window.destroy()
            except tk.TclError:
                pass
            finally:
                self.dialog_window = None
