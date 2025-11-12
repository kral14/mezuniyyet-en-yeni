#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Alətlər Səhifəsi - Şöbə və Vəzifə İdarəetməsi
"""

import tkinter as tk
from tkinter import ttk, messagebox
import threading

# Database import - EXE rejimi üçün alternativ yollar
try:
    from database.departments_positions_queries import *
except ImportError:
    try:
        from src.database.departments_positions_queries import *
    except ImportError:
        # Son alternativ
        import sys
        import os
        current_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        sys.path.insert(0, current_dir)
        from database.departments_positions_queries import *

class ToolsPage(tk.Frame):
    def __init__(self, parent, on_back=None):
        super().__init__(parent)
        self.parent = parent
        self.on_back = on_back
        
        # Font
        self.main_font = "Arial"
        
        # Rəng sxemi
        self.colors = {
            'primary': '#2980b9',
            'secondary': '#27ae60', 
            'danger': '#e74c3c',
            'success': '#27ae60',
            'warning': '#f39c12',
            'light': '#ecf0f1',
            'white': 'white',
            'dark': '#2c3e50',
            'text_primary': '#2c3e50',
            'text_secondary': '#7f8c8d',
            'border': '#bdc3c7',
            'background': '#f8f9fa'
        }
        
        # Frame konfiqurasiyası
        self.configure(background=self.colors['background'])
        
        # UI yarat
        self.create_widgets()
        
        # Loading göstəricisi əlavə et
        self.show_loading()
        
        # Məlumatları arxa fonda yüklə
        threading.Thread(target=self.load_data_async, daemon=True).start()
    
    def create_widgets(self):
        """UI elementlərini yaradır"""
        # Ana frame
        main_frame = tk.Frame(self, bg=self.colors['background'])
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Başlıq və geri düyməsi
        header_frame = tk.Frame(main_frame, bg=self.colors['background'])
        header_frame.pack(fill="x", pady=(0, 20))
        
        # Geri qayıtma düyməsi (sol tərəf)
        if self.on_back:
            back_btn = tk.Button(header_frame, text="← Geri", 
                                command=self.on_escape,
                                bg=self.colors['primary'], fg=self.colors['white'], 
                                font=(self.main_font, 11, 'bold'),
                                relief="flat", padx=12, pady=4, cursor="hand2")
            back_btn.pack(side='left')
        
        # Başlıq (mərkəz)
        title_label = tk.Label(header_frame, text="🔧 Alətlər - Şöbə və Vəzifə İdarəetməsi", 
                              font=(self.main_font, 16, "bold"), 
                              bg=self.colors['background'], fg=self.colors['text_primary'])
        title_label.pack(side='left', padx=(20, 0))
        
        # Notebook (tab sistemi)
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill="both", expand=True)
        
        # Şöbələr tab
        self.create_departments_tab()
        
        # Vəzifələr tab
        self.create_positions_tab()
    
    def on_escape(self):
        """Geri qayıtma funksiyası"""
        try:
            if self.on_back:
                self.on_back(needs_refresh=False)
        except Exception as e:
            print(f"Geri qayıtma zamanı xəta: {e}")
            if self.on_back:
                self.on_back(needs_refresh=False)
    
    def create_departments_tab(self):
        """Şöbələr tab-ını yaradır"""
        # Şöbələr frame
        dept_frame = ttk.Frame(self.notebook)
        self.notebook.add(dept_frame, text="🏢 Şöbələr")
        
        # Sol panel - Şöbə əlavə etmə
        left_panel = tk.Frame(dept_frame, bg='#f8f9fa', relief='raised', bd=1)
        left_panel.pack(side='left', fill='y', padx=(10, 5), pady=10)
        left_panel.configure(width=300)
        left_panel.pack_propagate(False)
        
        # Şöbə əlavə etmə başlığı
        add_dept_label = tk.Label(left_panel, text="Yeni Şöbə Əlavə Et", 
                                 font=(self.main_font, 12, 'bold'),
                                 bg='#f8f9fa', fg='#2c3e50')
        add_dept_label.pack(pady=(15, 10))
        
        # Şöbə adı
        tk.Label(left_panel, text="Şöbə Adı:", 
                font=(self.main_font, 10, 'bold'),
                bg='#f8f9fa', fg='#2c3e50').pack(anchor='w', padx=10)
        
        self.dept_name_entry = tk.Entry(left_panel, font=(self.main_font, 10), width=30)
        self.dept_name_entry.pack(padx=10, pady=(5, 10), fill='x')
        
        # Şöbə təsviri
        tk.Label(left_panel, text="Təsvir:", 
                font=(self.main_font, 10, 'bold'),
                bg='#f8f9fa', fg='#2c3e50').pack(anchor='w', padx=10)
        
        self.dept_desc_text = tk.Text(left_panel, font=(self.main_font, 10), 
                                     width=30, height=4)
        self.dept_desc_text.pack(padx=10, pady=(5, 15), fill='x')
        
        # Düymələr
        button_frame = tk.Frame(left_panel, bg='#f8f9fa')
        button_frame.pack(fill='x', padx=10, pady=10)
        
        add_btn = tk.Button(button_frame, text="➕ Əlavə Et", 
                           command=self.add_department,
                           font=(self.main_font, 10, 'bold'),
                           bg='#27ae60', fg='white',
                           relief='flat', bd=0, padx=20, pady=8)
        add_btn.pack(side='left', padx=(0, 5))
        
        clear_btn = tk.Button(button_frame, text="🗑️ Təmizlə", 
                             command=self.clear_department_form,
                             font=(self.main_font, 10),
                             bg='#95a5a6', fg='white',
                             relief='flat', bd=0, padx=20, pady=8)
        clear_btn.pack(side='left')
        
        # Sağ panel - Şöbələr siyahısı
        right_panel = tk.Frame(dept_frame, bg='#ffffff', relief='raised', bd=1)
        right_panel.pack(side='right', fill='both', expand=True, padx=(5, 10), pady=10)
        
        # Şöbələr siyahısı başlığı
        list_label = tk.Label(right_panel, text="Mövcud Şöbələr", 
                             font=(self.main_font, 12, 'bold'),
                             bg='#ffffff', fg='#2c3e50')
        list_label.pack(pady=(15, 10))
        
        # Treeview
        columns = ('ID', 'Ad', 'Təsvir', 'Yaradılma Tarixi')
        self.dept_tree = ttk.Treeview(right_panel, columns=columns, show='headings', height=15)
        
        # Sütun başlıqları
        self.dept_tree.heading('ID', text='ID')
        self.dept_tree.heading('Ad', text='Ad')
        self.dept_tree.heading('Təsvir', text='Təsvir')
        self.dept_tree.heading('Yaradılma Tarixi', text='Yaradılma Tarixi')
        
        # Sütun genişlikləri
        self.dept_tree.column('ID', width=50, anchor='center')
        self.dept_tree.column('Ad', width=150)
        self.dept_tree.column('Təsvir', width=200)
        self.dept_tree.column('Yaradılma Tarixi', width=120, anchor='center')
        
        # Scrollbar
        dept_scrollbar = ttk.Scrollbar(right_panel, orient='vertical', command=self.dept_tree.yview)
        self.dept_tree.configure(yscrollcommand=dept_scrollbar.set)
        
        self.dept_tree.pack(side='left', fill='both', expand=True, padx=(10, 0), pady=(0, 10))
        dept_scrollbar.pack(side='right', fill='y', pady=(0, 10))
        
        # Düymələr
        dept_button_frame = tk.Frame(right_panel, bg='#ffffff')
        dept_button_frame.pack(fill='x', padx=10, pady=(0, 10))
        
        edit_dept_btn = tk.Button(dept_button_frame, text="✏️ Düzəlt", 
                                 command=self.edit_department,
                                 font=(self.main_font, 10),
                                 bg='#3498db', fg='white',
                                 relief='flat', bd=0, padx=15, pady=5)
        edit_dept_btn.pack(side='left', padx=(0, 5))
        
        delete_dept_btn = tk.Button(dept_button_frame, text="🗑️ Sil", 
                                   command=self.delete_department,
                                   font=(self.main_font, 10),
                                   bg='#e74c3c', fg='white',
                                   relief='flat', bd=0, padx=15, pady=5)
        delete_dept_btn.pack(side='left')
        
        refresh_dept_btn = tk.Button(dept_button_frame, text="🔄 Yenilə", 
                                    command=self.load_departments,
                                    font=(self.main_font, 10),
                                    bg='#95a5a6', fg='white',
                                    relief='flat', bd=0, padx=15, pady=5)
        refresh_dept_btn.pack(side='right')
    
    def create_positions_tab(self):
        """Vəzifələr tab-ını yaradır"""
        # Vəzifələr frame
        pos_frame = ttk.Frame(self.notebook)
        self.notebook.add(pos_frame, text="👔 Vəzifələr")
        
        # Sol panel - Vəzifə əlavə etmə
        left_panel = tk.Frame(pos_frame, bg='#f8f9fa', relief='raised', bd=1)
        left_panel.pack(side='left', fill='y', padx=(10, 5), pady=10)
        left_panel.configure(width=300)
        left_panel.pack_propagate(False)
        
        # Vəzifə əlavə etmə başlığı
        add_pos_label = tk.Label(left_panel, text="Yeni Vəzifə Əlavə Et", 
                                font=(self.main_font, 12, 'bold'),
                                bg='#f8f9fa', fg='#2c3e50')
        add_pos_label.pack(pady=(15, 10))
        
        # Vəzifə adı
        tk.Label(left_panel, text="Vəzifə Adı:", 
                font=(self.main_font, 10, 'bold'),
                bg='#f8f9fa', fg='#2c3e50').pack(anchor='w', padx=10)
        
        self.pos_name_entry = tk.Entry(left_panel, font=(self.main_font, 10), width=30)
        self.pos_name_entry.pack(padx=10, pady=(5, 10), fill='x')
        
        # Şöbə seçimi
        tk.Label(left_panel, text="Şöbə:", 
                font=(self.main_font, 10, 'bold'),
                bg='#f8f9fa', fg='#2c3e50').pack(anchor='w', padx=10)
        
        self.pos_dept_combo = ttk.Combobox(left_panel, font=(self.main_font, 10), width=28)
        self.pos_dept_combo.pack(padx=10, pady=(5, 10), fill='x')
        
        # Vəzifə təsviri
        tk.Label(left_panel, text="Təsvir:", 
                font=(self.main_font, 10, 'bold'),
                bg='#f8f9fa', fg='#2c3e50').pack(anchor='w', padx=10)
        
        self.pos_desc_text = tk.Text(left_panel, font=(self.main_font, 10), 
                                    width=30, height=3)
        self.pos_desc_text.pack(padx=10, pady=(5, 15), fill='x')
        
        # Düymələr
        button_frame = tk.Frame(left_panel, bg='#f8f9fa')
        button_frame.pack(fill='x', padx=10, pady=10)
        
        add_btn = tk.Button(button_frame, text="➕ Əlavə Et", 
                           command=self.add_position,
                           font=(self.main_font, 10, 'bold'),
                           bg='#27ae60', fg='white',
                           relief='flat', bd=0, padx=20, pady=8)
        add_btn.pack(side='left', padx=(0, 5))
        
        clear_btn = tk.Button(button_frame, text="🗑️ Təmizlə", 
                             command=self.clear_position_form,
                             font=(self.main_font, 10),
                             bg='#95a5a6', fg='white',
                             relief='flat', bd=0, padx=20, pady=8)
        clear_btn.pack(side='left')
        
        # Sağ panel - Vəzifələr siyahısı
        right_panel = tk.Frame(pos_frame, bg='#ffffff', relief='raised', bd=1)
        right_panel.pack(side='right', fill='both', expand=True, padx=(5, 10), pady=10)
        
        # Vəzifələr siyahısı başlığı
        list_label = tk.Label(right_panel, text="Mövcud Vəzifələr", 
                             font=(self.main_font, 12, 'bold'),
                             bg='#ffffff', fg='#2c3e50')
        list_label.pack(pady=(15, 10))
        
        # Treeview
        columns = ('ID', 'Ad', 'Şöbə', 'Təsvir', 'Yaradılma Tarixi')
        self.pos_tree = ttk.Treeview(right_panel, columns=columns, show='headings', height=15)
        
        # Sütun başlıqları
        self.pos_tree.heading('ID', text='ID')
        self.pos_tree.heading('Ad', text='Ad')
        self.pos_tree.heading('Şöbə', text='Şöbə')
        self.pos_tree.heading('Təsvir', text='Təsvir')
        self.pos_tree.heading('Yaradılma Tarixi', text='Yaradılma Tarixi')
        
        # Sütun genişlikləri
        self.pos_tree.column('ID', width=50, anchor='center')
        self.pos_tree.column('Ad', width=150)
        self.pos_tree.column('Şöbə', width=120)
        self.pos_tree.column('Təsvir', width=180)
        self.pos_tree.column('Yaradılma Tarixi', width=120, anchor='center')
        
        # Scrollbar
        pos_scrollbar = ttk.Scrollbar(right_panel, orient='vertical', command=self.pos_tree.yview)
        self.pos_tree.configure(yscrollcommand=pos_scrollbar.set)
        
        self.pos_tree.pack(side='left', fill='both', expand=True, padx=(10, 0), pady=(0, 10))
        pos_scrollbar.pack(side='right', fill='y', pady=(0, 10))
        
        # Düymələr
        pos_button_frame = tk.Frame(right_panel, bg='#ffffff')
        pos_button_frame.pack(fill='x', padx=10, pady=(0, 10))
        
        edit_pos_btn = tk.Button(pos_button_frame, text="✏️ Düzəlt", 
                                command=self.edit_position,
                                font=(self.main_font, 10),
                                bg='#3498db', fg='white',
                                relief='flat', bd=0, padx=15, pady=5)
        edit_pos_btn.pack(side='left', padx=(0, 5))
        
        delete_pos_btn = tk.Button(pos_button_frame, text="🗑️ Sil", 
                                  command=self.delete_position,
                                  font=(self.main_font, 10),
                                  bg='#e74c3c', fg='white',
                                  relief='flat', bd=0, padx=15, pady=5)
        delete_pos_btn.pack(side='left')
        
        refresh_pos_btn = tk.Button(pos_button_frame, text="🔄 Yenilə", 
                                   command=self.load_positions,
                                   font=(self.main_font, 10),
                                   bg='#95a5a6', fg='white',
                                   relief='flat', bd=0, padx=15, pady=5)
        refresh_pos_btn.pack(side='right')
    
    def load_data(self):
        """Məlumatları yükləyir"""
        try:
            # Cədvəlləri yalnız lazım olduqda yarat (əvvəlcə yoxla)
            self.ensure_tables_exist()
            
            # Məlumatları yüklə
            self.load_departments()
            self.load_positions()
            self.load_department_combo()
        except Exception as e:
            print(f"Alətlər paneli yüklənərkən xəta: {e}")
            messagebox.showerror("Xəta", f"Alətlər paneli yüklənərkən xəta: {e}")
    
    def ensure_tables_exist(self):
        """Cədvəllərin mövcudluğunu yoxlayır və lazım olduqda yaradır"""
        try:
            # Əvvəlcə cədvəllərin mövcudluğunu yoxla - EXE rejimi üçün alternativ import
            try:
                from database.departments_positions_queries import check_tables_exist
            except ImportError:
                try:
                    from src.database.departments_positions_queries import check_tables_exist
                except ImportError:
                    # Əgər import alınmasa, cədvəlləri yarat
                    create_departments_table()
                    create_positions_table()
                    initialize_default_data()
                    return
            
            if not check_tables_exist():
                print("Cədvəllər mövcud deyil, yaradılır...")
                create_departments_table()
                create_positions_table()
                initialize_default_data()
                print("Cədvəllər uğurla yaradıldı")
            else:
                print("Cədvəllər artıq mövcuddur")
        except Exception as e:
            print(f"Cədvəl yoxlaması xətası: {e}")
            # Xəta baş verdikdə cədvəlləri yenidən yarat
            create_departments_table()
            create_positions_table()
            initialize_default_data()
    
    def show_loading(self):
        """Loading göstəricisini göstərir"""
        self.loading_frame = tk.Frame(self, bg=self.colors['background'])
        self.loading_frame.pack(fill="both", expand=True)
        
        # Loading mesajı
        loading_label = tk.Label(self.loading_frame, 
                                text="⏳ Alətlər paneli yüklənir...",
                                font=(self.main_font, 16, 'bold'),
                                bg=self.colors['background'],
                                fg=self.colors['text_primary'])
        loading_label.pack(expand=True)
    
    def hide_loading(self):
        """Loading göstəricisini gizlədir"""
        if hasattr(self, 'loading_frame'):
            self.loading_frame.destroy()
    
    def load_data_async(self):
        """Məlumatları arxa fonda yükləyir"""
        try:
            # Cədvəlləri yalnız lazım olduqda yarat
            self.ensure_tables_exist()
            
            # UI yeniləməsini ana thread-də et
            self.after(0, self.load_data_ui)
        except Exception as e:
            print(f"Async yükləmə xətası: {e}")
            self.after(0, lambda: messagebox.showerror("Xəta", f"Alətlər paneli yüklənərkən xəta: {e}"))
    
    def load_data_ui(self):
        """UI məlumatlarını yükləyir (ana thread-də)"""
        try:
            # Loading-i gizlət
            self.hide_loading()
            
            # Məlumatları yüklə
            self.load_departments()
            self.load_positions()
            self.load_department_combo()
        except Exception as e:
            print(f"UI yükləmə xətası: {e}")
            messagebox.showerror("Xəta", f"UI yüklənərkən xəta: {e}")
    
    def load_departments(self):
        """Şöbələri yükləyir"""
        # Treeview-i təmizlə
        for item in self.dept_tree.get_children():
            self.dept_tree.delete(item)
        
        # Şöbələri yüklə
        departments = get_all_departments()
        for dept in departments:
            dept_id, name, description, created_at = dept
            self.dept_tree.insert('', 'end', values=(
                dept_id, name, description or '', 
                created_at.strftime('%Y-%m-%d') if created_at else ''
            ))
    
    def load_positions(self):
        """Vəzifələri yükləyir"""
        # Treeview-i təmizlə
        for item in self.pos_tree.get_children():
            self.pos_tree.delete(item)
        
        # Vəzifələri yüklə
        positions = get_all_positions()
        for pos in positions:
            pos_id, name, description, dept_id, dept_name, created_at = pos
            self.pos_tree.insert('', 'end', values=(
                pos_id, name, dept_name or 'Ümumi', description or '', 
                created_at.strftime('%Y-%m-%d') if created_at else ''
            ))
    
    def load_department_combo(self):
        """Şöbə combo box-ını yükləyir"""
        departments = get_departments_for_combo()
        dept_names = ['Ümumi'] + [dept[1] for dept in departments]
        self.pos_dept_combo['values'] = dept_names
        if dept_names:
            self.pos_dept_combo.set(dept_names[0])
    
    def add_department(self):
        """Yeni şöbə əlavə edir"""
        name = self.dept_name_entry.get().strip()
        description = self.dept_desc_text.get('1.0', 'end').strip()
        
        if not name:
            messagebox.showerror("Xəta", "Şöbə adını daxil edin!")
            return
        
        if add_department(name, description if description else None):
            messagebox.showinfo("Uğurlu", f"Şöbə '{name}' uğurla əlavə edildi!")
            self.clear_department_form()
            self.load_departments()
            self.load_department_combo()
        else:
            messagebox.showerror("Xəta", "Şöbə əlavə edilə bilmədi!")
    
    def add_position(self):
        """Yeni vəzifə əlavə edir"""
        name = self.pos_name_entry.get().strip()
        dept_name = self.pos_dept_combo.get().strip()
        description = self.pos_desc_text.get('1.0', 'end').strip()
        
        if not name:
            messagebox.showerror("Xəta", "Vəzifə adını daxil edin!")
            return
        
        # Şöbə ID-ni tap
        dept_id = None
        if dept_name and dept_name != 'Ümumi':
            departments = get_departments_for_combo()
            for dept in departments:
                if dept[1] == dept_name:
                    dept_id = dept[0]
                    break
        
        if add_position(name, dept_id, description if description else None):
            messagebox.showinfo("Uğurlu", f"Vəzifə '{name}' uğurla əlavə edildi!")
            self.clear_position_form()
            self.load_positions()
        else:
            messagebox.showerror("Xəta", "Vəzifə əlavə edilə bilmədi!")
    
    def clear_department_form(self):
        """Şöbə formunu təmizləyir"""
        self.dept_name_entry.delete(0, 'end')
        self.dept_desc_text.delete('1.0', 'end')
    
    def clear_position_form(self):
        """Vəzifə formunu təmizləyir"""
        self.pos_name_entry.delete(0, 'end')
        self.pos_dept_combo.set('Ümumi')
        self.pos_desc_text.delete('1.0', 'end')
    
    def edit_department(self):
        """Şöbəni redaktə edir"""
        selected = self.dept_tree.selection()
        if not selected:
            messagebox.showwarning("Xəbərdarlıq", "Redaktə etmək üçün şöbə seçin!")
            return
        
        item = self.dept_tree.item(selected[0])
        dept_id = item['values'][0]
        name = item['values'][1]
        description = item['values'][2]
        
        # Redaktə pəncərəsi
        self.edit_department_window(dept_id, name, description)
    
    def edit_position(self):
        """Vəzifəni redaktə edir"""
        selected = self.pos_tree.selection()
        if not selected:
            messagebox.showwarning("Xəbərdarlıq", "Redaktə etmək üçün vəzifə seçin!")
            return
        
        item = self.pos_tree.item(selected[0])
        pos_id = item['values'][0]
        name = item['values'][1]
        dept_name = item['values'][2]
        description = item['values'][3]
        
        # Redaktə pəncərəsi
        self.edit_position_window(pos_id, name, dept_name, description)
    
    def edit_department_window(self, dept_id, name, description):
        """Şöbə redaktə pəncərəsi"""
        edit_window = tk.Toplevel(self)
        edit_window.title("Şöbə Redaktə Et")
        edit_window.geometry("400x300")
        edit_window.transient(self)
        edit_window.grab_set()
        
        # Form
        tk.Label(edit_window, text="Şöbə Adı:", font=(self.main_font, 10, 'bold')).pack(anchor='w', padx=10, pady=(20, 5))
        name_entry = tk.Entry(edit_window, font=(self.main_font, 10), width=40)
        name_entry.pack(padx=10, pady=(0, 10))
        name_entry.insert(0, name)
        
        tk.Label(edit_window, text="Təsvir:", font=(self.main_font, 10, 'bold')).pack(anchor='w', padx=10, pady=(10, 5))
        desc_text = tk.Text(edit_window, font=(self.main_font, 10), width=40, height=6)
        desc_text.pack(padx=10, pady=(0, 20))
        desc_text.insert('1.0', description)
        
        # Düymələr
        button_frame = tk.Frame(edit_window)
        button_frame.pack(pady=10)
        
        def save_changes():
            new_name = name_entry.get().strip()
            new_desc = desc_text.get('1.0', 'end').strip()
            
            if not new_name:
                messagebox.showerror("Xəta", "Şöbə adını daxil edin!")
                return
            
            if update_department(dept_id, new_name, new_desc if new_desc else None):
                messagebox.showinfo("Uğurlu", "Şöbə uğurla yeniləndi!")
                edit_window.destroy()
                self.load_departments()
                self.load_department_combo()
            else:
                messagebox.showerror("Xəta", "Şöbə yenilənə bilmədi!")
        
        tk.Button(button_frame, text="💾 Saxla", command=save_changes,
                 font=(self.main_font, 10, 'bold'), bg='#27ae60', fg='white',
                 relief='flat', bd=0, padx=20, pady=5).pack(side='left', padx=5)
        
        tk.Button(button_frame, text="❌ Ləğv Et", command=edit_window.destroy,
                 font=(self.main_font, 10), bg='#95a5a6', fg='white',
                 relief='flat', bd=0, padx=20, pady=5).pack(side='left', padx=5)
    
    def edit_position_window(self, pos_id, name, dept_name, description):
        """Vəzifə redaktə pəncərəsi"""
        edit_window = tk.Toplevel(self)
        edit_window.title("Vəzifə Redaktə Et")
        edit_window.geometry("400x350")
        edit_window.transient(self)
        edit_window.grab_set()
        
        # Form
        tk.Label(edit_window, text="Vəzifə Adı:", font=(self.main_font, 10, 'bold')).pack(anchor='w', padx=10, pady=(20, 5))
        name_entry = tk.Entry(edit_window, font=(self.main_font, 10), width=40)
        name_entry.pack(padx=10, pady=(0, 10))
        name_entry.insert(0, name)
        
        tk.Label(edit_window, text="Şöbə:", font=(self.main_font, 10, 'bold')).pack(anchor='w', padx=10, pady=(10, 5))
        dept_combo = ttk.Combobox(edit_window, font=(self.main_font, 10), width=37)
        dept_combo.pack(padx=10, pady=(0, 10))
        
        # Şöbə siyahısını yüklə
        departments = get_departments_for_combo()
        dept_names = ['Ümumi'] + [dept[1] for dept in departments]
        dept_combo['values'] = dept_names
        dept_combo.set(dept_name if dept_name else 'Ümumi')
        
        tk.Label(edit_window, text="Təsvir:", font=(self.main_font, 10, 'bold')).pack(anchor='w', padx=10, pady=(10, 5))
        desc_text = tk.Text(edit_window, font=(self.main_font, 10), width=40, height=5)
        desc_text.pack(padx=10, pady=(0, 20))
        desc_text.insert('1.0', description)
        
        # Düymələr
        button_frame = tk.Frame(edit_window)
        button_frame.pack(pady=10)
        
        def save_changes():
            new_name = name_entry.get().strip()
            new_dept_name = dept_combo.get().strip()
            new_desc = desc_text.get('1.0', 'end').strip()
            
            if not new_name:
                messagebox.showerror("Xəta", "Vəzifə adını daxil edin!")
                return
            
            # Şöbə ID-ni tap
            new_dept_id = None
            if new_dept_name and new_dept_name != 'Ümumi':
                for dept in departments:
                    if dept[1] == new_dept_name:
                        new_dept_id = dept[0]
                        break
            
            if update_position(pos_id, new_name, new_dept_id, new_desc if new_desc else None):
                messagebox.showinfo("Uğurlu", "Vəzifə uğurla yeniləndi!")
                edit_window.destroy()
                self.load_positions()
            else:
                messagebox.showerror("Xəta", "Vəzifə yenilənə bilmədi!")
        
        tk.Button(button_frame, text="💾 Saxla", command=save_changes,
                 font=(self.main_font, 10, 'bold'), bg='#27ae60', fg='white',
                 relief='flat', bd=0, padx=20, pady=5).pack(side='left', padx=5)
        
        tk.Button(button_frame, text="❌ Ləğv Et", command=edit_window.destroy,
                 font=(self.main_font, 10), bg='#95a5a6', fg='white',
                 relief='flat', bd=0, padx=20, pady=5).pack(side='left', padx=5)
    
    def delete_department(self):
        """Şöbəni silir"""
        selected = self.dept_tree.selection()
        if not selected:
            messagebox.showwarning("Xəbərdarlıq", "Silmək üçün şöbə seçin!")
            return
        
        item = self.dept_tree.item(selected[0])
        dept_id = item['values'][0]
        name = item['values'][1]
        
        if messagebox.askyesno("Təsdiq", f"'{name}' şöbəsini silmək istədiyinizə əminsiniz?"):
            if delete_department(dept_id):
                messagebox.showinfo("Uğurlu", f"Şöbə '{name}' uğurla silindi!")
                self.load_departments()
                self.load_department_combo()
            else:
                messagebox.showerror("Xəta", "Şöbə silinə bilmədi!")
    
    def delete_position(self):
        """Vəzifəni silir"""
        selected = self.pos_tree.selection()
        if not selected:
            messagebox.showwarning("Xəbərdarlıq", "Silmək üçün vəzifə seçin!")
            return
        
        item = self.pos_tree.item(selected[0])
        pos_id = item['values'][0]
        name = item['values'][1]
        
        if messagebox.askyesno("Təsdiq", f"'{name}' vəzifəsini silmək istədiyinizə əminsiniz?"):
            if delete_position(pos_id):
                messagebox.showinfo("Uğurlu", f"Vəzifə '{name}' uğurla silindi!")
                self.load_positions()
            else:
                messagebox.showerror("Xəta", "Vəzifə silinə bilmədi!")
