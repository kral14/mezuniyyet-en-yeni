import tkinter as tk
from tkinter import ttk, Text, messagebox, filedialog
import database
import logging
import os
import json
from datetime import datetime

class ErrorViewerPage(tk.Frame):
    def __init__(self, parent, main_app_ref=None, on_back=None):
        super().__init__(parent)
        self.parent = parent
        self.main_app_ref = main_app_ref
        self.on_back = on_back
        
        # Rəng sxemi (alətlər paneli ilə eyni)
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

        # Debug rejimi tamamilə söndürülüb - performans üçün
        self.tk_log_handler = None
        self.prev_level = logging.getLogger().level
        
        # Seçilmiş log məlumatları
        self.selected_log_details = None
        self.selected_user_id = None
        
        # UI yarat
        self.create_widgets()
    
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
                                font=('Arial', 11, 'bold'),
                                relief="flat", padx=12, pady=4, cursor="hand2")
            back_btn.pack(side='left')
        
        # Başlıq (mərkəz)
        title_label = tk.Label(header_frame, text="📋 Xəta Jurnalı", 
                              font=('Arial', 16, "bold"), 
                              bg=self.colors['background'], fg=self.colors['text_primary'])
        title_label.pack(side='left', padx=(20, 0))

        # --- Əsas Pəncərə Hissələri ---
        top_frame = ttk.Frame(main_frame, padding=(10, 10, 10, 0))
        top_frame.pack(fill='x')

        filter_frame = ttk.LabelFrame(top_frame, text="Filtrləmə və Axtarış", padding=10)
        filter_frame.pack(fill='x')

        # DÜZƏLİŞ: -sashrelief parametri silindi
        main_paned_window = ttk.PanedWindow(main_frame, orient='vertical')
        main_paned_window.pack(fill='both', expand=True, padx=10, pady=10)

        list_frame = ttk.Frame(main_paned_window, padding=5)
        main_paned_window.add(list_frame, weight=2)

        details_frame = ttk.LabelFrame(main_paned_window, text="Seçilmiş Xətanın Detalları", padding=5)
        main_paned_window.add(details_frame, weight=3)
        
        # --- Filtrləmə Elementləri ---
        ttk.Label(filter_frame, text="Status:").pack(side='left', padx=(0, 5))
        self.status_filter = ttk.Combobox(filter_frame, values=["Bütün Statuslar", "Yeni", "Həll Edilib"], state="readonly")
        self.status_filter.pack(side='left', padx=5)
        self.status_filter.set("Bütün Statuslar")

        ttk.Label(filter_frame, text="İstifadəçi:").pack(side='left', padx=(10, 5))
        self.user_filter = ttk.Combobox(filter_frame, values=["Bütün İstifadəçilər"], state="readonly", width=20)
        self.user_filter.pack(side='left', padx=5)
        self.user_filter.set("Bütün İstifadəçilər")
        
        ttk.Label(filter_frame, text="Log Növü:").pack(side='left', padx=(10, 5))
        self.log_type_filter = ttk.Combobox(filter_frame, values=["Bütün Loglar", "Xəta", "Debug Console", "Realtime Debug", "Email Service", "Unified App"], state="readonly", width=20)
        self.log_type_filter.pack(side='left', padx=5)
        self.log_type_filter.set("Bütün Loglar")

        ttk.Label(filter_frame, text="Axtarış:").pack(side='left', padx=(10, 5))
        self.search_var = tk.StringVar()
        search_entry = ttk.Entry(filter_frame, textvariable=self.search_var, width=30)
        search_entry.pack(side='left', padx=5, fill='x', expand=True)

        ttk.Button(filter_frame, text="Tətbiq Et", command=self.apply_filters).pack(side='left', padx=10)
        ttk.Button(filter_frame, text="Sıfırla", command=self.reset_filters).pack(side='left')

        # --- Xətalar və Loglar Siyahısı (Treeview) ---
        columns = ('id', 'user', 'timestamp', 'log_type', 'content_preview')
        self.tree = ttk.Treeview(list_frame, columns=columns, show='headings')
        
        self.tree.heading('id', text='ID', command=lambda: self.sort_by_column('id', False))
        self.tree.heading('user', text='İstifadəçi', command=lambda: self.sort_by_column('user', False))
        self.tree.heading('timestamp', text='Tarix', command=lambda: self.sort_by_column('timestamp', False))
        self.tree.heading('log_type', text='Log Növü', command=lambda: self.sort_by_column('log_type', False))
        self.tree.heading('content_preview', text='Məzmun (İlk 100 simvol)', command=lambda: self.sort_by_column('content_preview', False))

        self.tree.column('id', width=50, anchor='center', stretch=tk.NO)
        self.tree.column('user', width=120, anchor='w')
        self.tree.column('timestamp', width=150, anchor='center')
        self.tree.column('log_type', width=120, anchor='w')
        self.tree.column('content_preview', width=400, anchor='w')
        
        vsb = ttk.Scrollbar(list_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        vsb.pack(side='right', fill='y')
        self.tree.pack(fill='both', expand=True)
        self.tree.bind("<<TreeviewSelect>>", self.on_error_select)

        # --- Xəta Detalları (Text Widget) və İdarəetmə ---
        action_frame = ttk.Frame(details_frame)
        action_frame.pack(fill='x', pady=5)
        
        # Sol tərəf - Əməliyyat düymələri
        left_buttons = ttk.Frame(action_frame)
        left_buttons.pack(side='left')
        
        self.resolve_button = ttk.Button(left_buttons, text="✅ Həll Edildi İşarələ", state="disabled", command=self.mark_as_resolved)
        self.resolve_button.pack(side='left', padx=(0, 10))
        self.delete_button = ttk.Button(left_buttons, text="🗑 Jurnaldan Sil", state="disabled", command=self.delete_log)
        self.delete_button.pack(side='left', padx=(0, 10))
        
        # İstifadəçinin bütün loglarını silmək üçün düymə
        self.delete_user_logs_button = ttk.Button(left_buttons, text="🗑 İstifadəçinin Bütün Loglarını Sil", 
                                                   state="disabled", command=self.delete_selected_user_logs)
        self.delete_user_logs_button.pack(side='left', padx=(0, 10))
        
        # Sağ tərəf - Export düymələri
        right_buttons = ttk.Frame(action_frame)
        right_buttons.pack(side='right')
        
        self.export_selected_button = ttk.Button(right_buttons, text="💾 Seçilən Logu Yüklə", 
                                                 state="disabled", command=self.export_selected_log)
        self.export_selected_button.pack(side='left', padx=(0, 5))
        
        self.export_user_logs_button = ttk.Button(right_buttons, text="📦 İstifadəçinin Bütün Loglarını Yüklə", 
                                                   state="disabled", command=self.export_user_logs)
        self.export_user_logs_button.pack(side='left')

        self.details_text = Text(details_frame, wrap='word', font=("Courier New", 10), relief='solid', borderwidth=1, state='disabled')
        txt_vsb = ttk.Scrollbar(details_frame, orient='vertical', command=self.details_text.yview)
        self.details_text.config(yscrollcommand=txt_vsb.set)
        txt_vsb.pack(side='right', fill='y')
        self.details_text.pack(fill='both', expand=True, pady=(5,0))
        
        self.load_errors()

    def load_errors(self):
        """Bu funksiya artıq bazadan real xətaları və log fayllarını çəkəcək."""
        self.all_errors = {} # Xətaları və logları saxlamaq üçün
        
        # Xətaları yüklə
        try:
            error_list = database.get_all_errors()
            for row in error_list:
                error_id, username, timestamp, status, traceback_text = row
                self.all_errors[f"error_{error_id}"] = {
                    'id': error_id,
                    'user': username if username else 'Bilinməyən',
                    'user_id': None,  # Xəta loglarında user_id yoxdur
                    'timestamp': timestamp.strftime('%d.%m.%Y %H:%M:%S'),
                    'log_type': 'Xəta',
                    'content': traceback_text,
                    'status': status
                }
        except Exception as e:
            print(f"Xətalar yüklənərkən xəta: {e}")
        
        # Log fayllarını yüklə
        try:
            from database.error_queries import get_user_logs, get_log_users
            log_list = get_user_logs()
            for row in log_list:
                log_id, user_id, username, log_type, log_content, log_timestamp, log_file_name = row
                # Log növünü tərcümə et
                log_type_display = {
                    'debug_console': 'Debug Console',
                    'realtime_debug': 'Realtime Debug',
                    'email_service': 'Email Service',
                    'unified_app_debug': 'Unified App'
                }.get(log_type, log_type)
                
                self.all_errors[f"log_{log_id}"] = {
                    'id': log_id,
                    'user': username if username else 'Bilinməyən',
                    'user_id': user_id,
                    'timestamp': log_timestamp.strftime('%d.%m.%Y %H:%M:%S') if log_timestamp else '',
                    'log_type': log_type_display,
                    'content': log_content,
                    'log_file_name': log_file_name,
                    'status': None
                }
        except Exception as e:
            print(f"Log faylları yüklənərkən xəta: {e}")
        
        # İstifadəçi filtrini dinamik doldur
        try:
            error_users = database.get_error_users()
            from database.error_queries import get_log_users
            log_users = [username for _, username in get_log_users()]
            all_users = list(set(error_users + log_users))
            self.user_filter['values'] = ["Bütün İstifadəçilər"] + sorted(all_users)
        except Exception as e:
            print(f"İstifadəçi siyahısı yüklənərkən xəta: {e}")
        
        self.apply_filters()
    def apply_filters(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        status = self.status_filter.get()
        user = self.user_filter.get()
        log_type = self.log_type_filter.get()
        search_term = self.search_var.get().lower()

        for key, data in self.all_errors.items():
            # Status filtr (yalnız xəta logları üçün)
            status_match = True
            if data.get('status'):
                status_match = (status == "Bütün Statuslar") or (data['status'] == status)
            
            # İstifadəçi filtr
            user_match = (user == "Bütün İstifadəçilər") or (data['user'] == user)
            
            # Log növü filtr
            log_type_match = True
            if log_type != "Bütün Loglar":
                log_type_map = {
                    "Xəta": "Xəta",
                    "Debug Console": "Debug Console",
                    "Realtime Debug": "Realtime Debug",
                    "Email Service": "Email Service",
                    "Unified App": "Unified App"
                }
                log_type_match = (data.get('log_type') == log_type_map.get(log_type, log_type))
            
            # Axtarış filtr
            search_match = (search_term == "") or (search_term in data.get('content', '').lower())

            if status_match and user_match and log_type_match and search_match:
                # Məzmunun ilk 100 simvolunu göstər
                content_preview = data.get('content', '')[:100] + ('...' if len(data.get('content', '')) > 100 else '')
                
                # Tag təyin et
                if data.get('status') == 'Həll Edilib':
                    tag = 'resolved'
                elif data.get('log_type') == 'Xəta':
                    tag = 'error'
                else:
                    tag = 'log'
                
                self.tree.insert('', 'end', iid=key, values=(
                    data['id'], 
                    data['user'], 
                    data['timestamp'], 
                    data.get('log_type', 'Bilinməyən'),
                    content_preview
                ), tags=(tag,))
        
        self.tree.tag_configure('resolved', foreground='gray')
        self.tree.tag_configure('error', foreground='red', font=("Helvetica", 10, "bold"))
        self.tree.tag_configure('log', foreground='blue')
        
        self.on_error_select(None)

    def reset_filters(self):
        self.status_filter.set("Bütün Statuslar")
        self.user_filter.set("Bütün İstifadəçilər")
        self.log_type_filter.set("Bütün Loglar")
        self.search_var.set("")
        self.apply_filters()
        
    def on_error_select(self, event):
        selected_items = self.tree.selection()
        
        self.details_text.config(state='normal')
        self.details_text.delete('1.0', tk.END)
        
        if not selected_items:
            self.resolve_button.config(state="disabled")
            self.delete_button.config(state="disabled")
            self.delete_user_logs_button.config(state="disabled")
            self.export_selected_button.config(state="disabled")
            self.export_user_logs_button.config(state="disabled")
            self.selected_log_details = None
        else:
            selected_key = selected_items[0]
            error_details = self.all_errors.get(selected_key)
            if error_details:
                # Məzmunu göstər
                content = error_details.get('content', '')
                if error_details.get('log_file_name'):
                    content = f"Fayl: {error_details['log_file_name']}\n\n{content}"
                self.details_text.insert('1.0', content)
                
                # Düymələri aktivləşdir/deaktivləşdir
                if error_details.get('status') == 'Yeni':
                    self.resolve_button.config(state="normal")
                else:
                    self.resolve_button.config(state="disabled")
                self.delete_button.config(state="normal")
                
                # İstifadəçinin bütün loglarını silmək düyməsini aktivləşdir
                user_id = error_details.get('user_id')
                if user_id:
                    self.delete_user_logs_button.config(state="normal")
                    self.export_user_logs_button.config(state="normal")
                    self.selected_user_id = user_id
                else:
                    self.delete_user_logs_button.config(state="disabled")
                    self.export_user_logs_button.config(state="disabled")
                    self.selected_user_id = None
                
                # Seçilən logu yükləmək düyməsini aktivləşdir
                self.export_selected_button.config(state="normal")
                self.selected_log_details = error_details

        self.details_text.config(state='disabled')

         
    def on_escape(self):
        """Geri qayıtma funksiyası"""
        try:
            if self.on_back:
                self.on_back(needs_refresh=False)
        except Exception as e:
            print(f"Geri qayıtma zamanı xəta: {e}")
            if self.on_back:
                self.on_back(needs_refresh=False)
    
    def sort_by_column(self, col, reverse):
        # print(f"Siyahı '{col}' sütununa görə çeşidləndi (Tərs: {reverse})")  # Debug mesajını söndürürük
        pass
    def mark_as_resolved(self):
        selected_key = self.tree.selection()[0]
        error_details = self.all_errors.get(selected_key)
        if not error_details:
            return
        
        # Yalnız xəta logları üçün işləyir
        if error_details.get('log_type') == 'Xəta':
            error_id = error_details['id']
            database.mark_error_as_resolved(error_id)
            
            # Real-time notification göndər (əgər main_app_ref varsa)
            if hasattr(self, 'main_app_ref') and hasattr(self.main_app_ref, 'send_realtime_signal'):
                self.main_app_ref.send_realtime_signal('error_resolved', {
                    'error_id': error_id,
                    'resolved_by': 'admin'
                })
            
            messagebox.showinfo("Uğurlu", f"Xəta {error_id} uğurla 'Həll Edildi' kimi işarələndi.", parent=self)
            self.load_errors()
        else:
            messagebox.showinfo("Məlumat", "Bu əməliyyat yalnız xəta logları üçün mövcuddur.", parent=self)

    def delete_log(self):
        selected_key = self.tree.selection()[0]
        error_details = self.all_errors.get(selected_key)
        if not error_details:
            return
        
        log_id = error_details['id']
        log_type = error_details.get('log_type', '')
        user_id = error_details.get('user_id')
        
        # Admin ID-ni al
        created_by_user_id = None
        if hasattr(self, 'main_app_ref') and hasattr(self.main_app_ref, 'current_user'):
            created_by_user_id = self.main_app_ref.current_user.get('id')
        
        if messagebox.askyesno("Təsdiq", f"{log_type} №{log_id} jurnalını tamamilə silmək istədiyinizə əminsiniz?", parent=self):
            if error_details.get('log_type') == 'Xəta':
                database.delete_error_log(log_id)
            else:
                # Log faylı sil - silmə siqnalı yaradılacaq
                try:
                    from database.error_queries import delete_user_logs
                    delete_user_logs(log_id=log_id, created_by_user_id=created_by_user_id)
                except Exception as e:
                    messagebox.showerror("Xəta", f"Log silinərkən xəta: {e}", parent=self)
                    return
            
            # Real-time notification göndər (əgər main_app_ref varsa)
            if hasattr(self, 'main_app_ref') and hasattr(self.main_app_ref, 'send_realtime_signal'):
                self.main_app_ref.send_realtime_signal('log_deleted', {
                    'log_id': log_id,
                    'user_id': user_id,
                    'deleted_by': 'admin'
                })
            
            self.load_errors()
    
    def delete_selected_user_logs(self):
        """Seçilmiş istifadəçinin bütün loglarını silir"""
        if not hasattr(self, 'selected_user_id') or not self.selected_user_id:
            messagebox.showwarning("Xəbərdarlıq", "Zəhmət olmasa, log seçin!", parent=self)
            return
        
        user_id = self.selected_user_id
        
        # İstifadəçi adını tap
        username = "Bilinməyən"
        for key, data in self.all_errors.items():
            if data.get('user_id') == user_id:
                username = data.get('user', 'Bilinməyən')
                break
        
        if messagebox.askyesno("Təsdiq", 
                               f"'{username}' istifadəçisinin bütün loglarını silmək istədiyinizə əminsiniz?\n\n"
                               f"Bu əməliyyat:\n"
                               f"1. Verilənlər bazasından logları siləcək\n"
                               f"2. İstifadəçiyə silmə siqnalı göndərəcək\n"
                               f"3. İstifadəçi proqramı açanda lokal log faylları silinəcək", 
                               parent=self):
            self.delete_user_logs(user_id)
    
    def delete_user_logs(self, user_id):
        """İstifadəçinin bütün loglarını silir"""
        # Admin ID-ni al
        created_by_user_id = None
        if hasattr(self, 'main_app_ref') and hasattr(self.main_app_ref, 'current_user'):
            created_by_user_id = self.main_app_ref.current_user.get('id')
        
        try:
            from database.error_queries import delete_user_logs
            delete_user_logs(user_id=user_id, created_by_user_id=created_by_user_id)
            
            # Real-time notification göndər
            if hasattr(self, 'main_app_ref') and hasattr(self.main_app_ref, 'send_realtime_signal'):
                self.main_app_ref.send_realtime_signal('user_logs_deleted', {
                    'user_id': user_id,
                    'deleted_by': 'admin'
                })
            
            messagebox.showinfo("Uğurlu", "İstifadəçinin bütün logları silindi və silmə siqnalı göndərildi.", parent=self)
            self.load_errors()
        except Exception as e:
            messagebox.showerror("Xəta", f"Loglar silinərkən xəta: {e}", parent=self)
    
    def export_selected_log(self):
        """Seçilən logu fayl kimi yükləyir"""
        if not hasattr(self, 'selected_log_details') or not self.selected_log_details:
            messagebox.showwarning("Xəbərdarlıq", "Zəhmət olmasa, log seçin!", parent=self)
            return
        
        try:
            log_details = self.selected_log_details
            log_id = log_details.get('id')
            log_type = log_details.get('log_type', 'Bilinməyən')
            username = log_details.get('user', 'Bilinməyən')
            timestamp = log_details.get('timestamp', '')
            log_file_name = log_details.get('log_file_name', f'log_{log_id}.txt')
            
            # Fayl adını təyin et
            if not log_file_name or log_file_name == 'None':
                log_file_name = f"{log_type}_{log_id}_{timestamp.replace(':', '-').replace('.', '-')}.txt"
            else:
                # Əgər fayl adı varsa, timestamp əlavə et
                name, ext = os.path.splitext(log_file_name)
                timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
                log_file_name = f"{name}_{timestamp_str}{ext}"
            
            # Fayl seçmə dialoqu
            initial_filename = log_file_name
            file_path = filedialog.asksaveasfilename(
                parent=self,
                title="Log Faylını Yüklə",
                defaultextension=".txt",
                initialfile=initial_filename,
                filetypes=[
                    ("Mətn faylı", "*.txt"),
                    ("JSON faylı", "*.json"),
                    ("Bütün fayllar", "*.*")
                ]
            )
            
            if not file_path:
                return
            
            # Fayl formatını təyin et
            file_ext = os.path.splitext(file_path)[1].lower()
            
            if file_ext == '.json':
                # JSON formatında yaz
                export_data = {
                    'log_id': log_id,
                    'log_type': log_type,
                    'username': username,
                    'timestamp': timestamp,
                    'log_file_name': log_details.get('log_file_name'),
                    'content': log_details.get('content', ''),
                    'exported_at': datetime.now().isoformat(),
                    'exported_by': 'admin'
                }
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(export_data, f, ensure_ascii=False, indent=2)
            else:
                # Mətn formatında yaz
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write("=" * 80 + "\n")
                    f.write(f"LOG MƏLUMATLARI\n")
                    f.write("=" * 80 + "\n")
                    f.write(f"Log ID: {log_id}\n")
                    f.write(f"Log Növü: {log_type}\n")
                    f.write(f"İstifadəçi: {username}\n")
                    f.write(f"Tarix: {timestamp}\n")
                    if log_details.get('log_file_name'):
                        f.write(f"Fayl Adı: {log_details['log_file_name']}\n")
                    f.write(f"Yüklənmə Tarixi: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                    f.write("=" * 80 + "\n\n")
                    f.write("LOG MƏZMUNU:\n")
                    f.write("-" * 80 + "\n")
                    f.write(log_details.get('content', ''))
                    f.write("\n" + "=" * 80 + "\n")
            
            messagebox.showinfo("Uğurlu", f"Log faylı uğurla yükləndi:\n{file_path}", parent=self)
        except Exception as e:
            messagebox.showerror("Xəta", f"Log yüklənərkən xəta: {e}", parent=self)
    
    def export_user_logs(self):
        """İstifadəçinin bütün loglarını fayl kimi yükləyir"""
        if not hasattr(self, 'selected_user_id') or not self.selected_user_id:
            messagebox.showwarning("Xəbərdarlıq", "Zəhmət olmasa, log seçin!", parent=self)
            return
        
        user_id = self.selected_user_id
        
        # İstifadəçi adını tap
        username = "Bilinməyən"
        for key, data in self.all_errors.items():
            if data.get('user_id') == user_id:
                username = data.get('user', 'Bilinməyən')
                break
        
        try:
            from database.error_queries import get_user_logs
            
            # İstifadəçinin bütün loglarını al
            user_logs = get_user_logs(user_id=user_id, limit=10000)
            
            if not user_logs:
                messagebox.showinfo("Məlumat", f"'{username}' istifadəçisinin log faylı yoxdur.", parent=self)
                return
            
            # Fayl seçmə dialoqu
            timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
            initial_filename = f"{username}_logs_{timestamp_str}.json"
            
            file_path = filedialog.asksaveasfilename(
                parent=self,
                title="İstifadəçi Loglarını Yüklə",
                defaultextension=".json",
                initialfile=initial_filename,
                filetypes=[
                    ("JSON faylı", "*.json"),
                    ("Mətn faylı", "*.txt"),
                    ("Bütün fayllar", "*.*")
                ]
            )
            
            if not file_path:
                return
            
            # Fayl formatını təyin et
            file_ext = os.path.splitext(file_path)[1].lower()
            
            if file_ext == '.json':
                # JSON formatında yaz
                export_data = {
                    'username': username,
                    'user_id': user_id,
                    'exported_at': datetime.now().isoformat(),
                    'exported_by': 'admin',
                    'total_logs': len(user_logs),
                    'logs': []
                }
                
                for log in user_logs:
                    log_id, log_user_id, log_username, log_type, log_content, log_timestamp, log_file_name = log
                    export_data['logs'].append({
                        'log_id': log_id,
                        'log_type': log_type,
                        'timestamp': log_timestamp.isoformat() if log_timestamp else '',
                        'log_file_name': log_file_name,
                        'content': log_content
                    })
                
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(export_data, f, ensure_ascii=False, indent=2)
            else:
                # Mətn formatında yaz
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write("=" * 80 + "\n")
                    f.write(f"İSTİFADƏÇİ LOGLARI\n")
                    f.write("=" * 80 + "\n")
                    f.write(f"İstifadəçi: {username}\n")
                    f.write(f"İstifadəçi ID: {user_id}\n")
                    f.write(f"Yüklənmə Tarixi: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                    f.write(f"Cəmi Log Sayı: {len(user_logs)}\n")
                    f.write("=" * 80 + "\n\n")
                    
                    for i, log in enumerate(user_logs, 1):
                        log_id, log_user_id, log_username, log_type, log_content, log_timestamp, log_file_name = log
                        f.write(f"\n{'=' * 80}\n")
                        f.write(f"LOG #{i}\n")
                        f.write(f"{'=' * 80}\n")
                        f.write(f"Log ID: {log_id}\n")
                        f.write(f"Log Növü: {log_type}\n")
                        f.write(f"Tarix: {log_timestamp.strftime('%Y-%m-%d %H:%M:%S') if log_timestamp else 'Bilinməyən'}\n")
                        if log_file_name:
                            f.write(f"Fayl Adı: {log_file_name}\n")
                        f.write(f"{'-' * 80}\n")
                        f.write("MƏZMUN:\n")
                        f.write(f"{'-' * 80}\n")
                        f.write(log_content)
                        f.write(f"\n{'=' * 80}\n\n")
            
            messagebox.showinfo("Uğurlu", 
                              f"'{username}' istifadəçisinin {len(user_logs)} log faylı uğurla yükləndi:\n{file_path}", 
                              parent=self)
        except Exception as e:
            messagebox.showerror("Xəta", f"Loglar yüklənərkən xəta: {e}", parent=self)

    def toggle_debug(self):
        # Debug rejimi tamamilə söndürülüb - performans üçün
        pass

    def destroy(self):
        # Pəncərə bağlananda debug rejimini tam deaktiv et
        if self.tk_log_handler:
            logging.getLogger().removeHandler(self.tk_log_handler)
            self.tk_log_handler = None
        logging.getLogger().setLevel(self.prev_level)
        super().destroy()
        
    # Tema sistemi silindi

if __name__ == "__main__":
    root = tk.Tk()
    root.title("Ana Proqram (Test üçün)")
    root.geometry("400x200")

    def open_error_viewer():
        viewer = AdvancedErrorViewer(root)

    ttk.Button(root, text="Peşəkar Xəta Panelini Aç", command=open_error_viewer).pack(expand=True)

    root.mainloop()