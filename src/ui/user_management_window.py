import tkinter as tk
from tkinter import ttk, messagebox
import database
from .archive_window import ArchiveWindow
from .login_history_window import LoginHistoryWindow
import logging

class UserManagementPage(tk.Frame):
    def __init__(self, parent, main_app_ref, on_back=None):
        super().__init__(parent)
        self.parent = parent
        self.main_app_ref = main_app_ref
        self.on_back = on_back
        self.selection_state = {}
        
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
        title_label = tk.Label(header_frame, text="👥 İstifadəçi İdarəetməsi", 
                              font=('Arial', 16, "bold"), 
                              bg=self.colors['background'], fg=self.colors['text_primary'])
        title_label.pack(side='left', padx=(20, 0))

        # --- Pəncərənin əsas hissələrinin yaradılması ---
        top_frame = ttk.Frame(main_frame, padding=10)
        top_frame.pack(fill='x', side='top')

        list_frame = ttk.Frame(main_frame, padding=10)
        list_frame.pack(expand=True, fill='both', side='top')
        
        bottom_frame = ttk.Frame(main_frame, padding=10)
        bottom_frame.pack(fill='x', side='bottom')
        
        self.setup_ui_elements(top_frame, list_frame, bottom_frame)
    
    def on_escape(self):
        """Geri qayıtma funksiyası"""
        try:
            if self.on_back:
                self.on_back(needs_refresh=False)
        except Exception as e:
            print(f"Geri qayıtma zamanı xəta: {e}")
            if self.on_back:
                self.on_back(needs_refresh=False)
    
    def setup_ui_elements(self, top_frame, list_frame, bottom_frame):
        """UI elementlərini quraşdırır"""
        # --- Yuxarıdakı idarəetmə elementləri ---
        self.select_all_var = tk.BooleanVar()
        ttk.Checkbutton(top_frame, text="Hamısını Seç", variable=self.select_all_var, command=self.toggle_select_all, style="Accent.TButton").pack(side='left', padx=(0, 20))
        
        ttk.Button(top_frame, text="Siyahını Yenilə", command=self.load_active_users, style="Accent.TButton").pack(side='left')

        self.history_button = ttk.Button(top_frame, text="Seçilmiş İstifadəçinin Giriş Tarixçəsi", command=self.open_login_history, state="disabled", style="Accent.TButton")
        self.history_button.pack(side='left', padx=10)

        # "Sistemi Kilidlə/Aç" düyməsi
        maintenance_frame = ttk.Frame(top_frame)
        maintenance_frame.pack(side='right', padx=10)
        self.maintenance_status_var = tk.StringVar()
        self.maintenance_btn = ttk.Button(maintenance_frame, textvariable=self.maintenance_status_var, command=self.toggle_maintenance_mode, style="Accent.TButton")
        self.maintenance_btn.pack()
        self.update_maintenance_button_status() # Düymənin ilkin vəziyyətini təyin edirik

        self.status_label = ttk.Label(top_frame, text="Hazır", foreground="blue")
        self.status_label.pack(side='right')

        # --- Aktiv istifadəçilərin siyahısı üçün cədvəl (Treeview) ---
        columns = ('select', 'username', 'name', 'login_time', 'ip_address')
        self.tree = ttk.Treeview(list_frame, columns=columns, show='headings', selectmode="browse")
        
        self.tree.heading('select', text='Seç')
        self.tree.heading('username', text='İstifadəçi Adı')
        self.tree.heading('name', text='Ad, Soyad')
        self.tree.heading('login_time', text='Giriş Vaxtı')
        self.tree.heading('ip_address', text='IP Ünvan')
        
        self.tree.column('select', width=50, anchor='center', stretch=tk.NO)
        self.tree.column('username', width=120, anchor='w')
        self.tree.column('name', width=180, anchor='w')
        self.tree.column('login_time', width=150, anchor='center')
        self.tree.column('ip_address', width=120, anchor='center')
        
        vsb = ttk.Scrollbar(list_frame, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(list_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        
        vsb.pack(side='right', fill='y')
        hsb.pack(side='bottom', fill='x')
        self.tree.pack(side='left', expand=True, fill='both')
        
        # Cədvəl üçün hadisələri (events) təyin edirik
        self.tree.bind('<Button-1>', self.on_tree_click)
        self.tree.bind('<<TreeviewSelect>>', self.on_row_select)

        # --- Aşağıdakı idarəetmə düymələri ---
        force_logout_btn = ttk.Button(bottom_frame, text="Seçilənləri Dərhal Sistemdən At", command=self.force_logout_selected, style="Accent.TButton")
        force_logout_btn.pack(side='left', padx=(0, 20))
        
        timed_logout_frame = ttk.LabelFrame(bottom_frame, text="Vaxtla Çıxış")
        timed_logout_frame.pack(side='left', fill='x')
        self.time_entry = ttk.Entry(timed_logout_frame, width=5)
        self.time_entry.pack(side='left', padx=5)
        self.time_entry.insert(0, "5")
        ttk.Label(timed_logout_frame, text="dəqiqə sonra sistemdən at").pack(side='left')
        ttk.Button(timed_logout_frame, text="Əmri Göndər", command=self.timed_logout_selected, style="Accent.TButton").pack(side='left', padx=5)

        # Pəncərə açılan kimi aktiv istifadəçiləri yükləyirik
        self.load_active_users()
    def update_maintenance_button_status(self):
        """Sistemin kilidli olub-olmamağına görə düymənin mətnini və rəngini dəyişir."""
        is_locked = database.get_maintenance_mode()
        if is_locked:
            self.maintenance_status_var.set("🔴 Sistemi AÇ")
            # Stil də əlavə etmək olar
        else:
            self.maintenance_status_var.set("🟢 Sistemi KİLİDLƏ")

    def toggle_maintenance_mode(self):
        """Texniki iş rejimini aktiv/deaktiv edir və istifadəçiləri sistemdən atır."""
        is_currently_locked = database.get_maintenance_mode()
        new_status = not is_currently_locked
        
        status_text = "kilidləmək" if new_status else "açmaq"
        if messagebox.askyesno("Təsdiq", f"Sistemi digər istifadəçilər üçün {status_text} istədiyinizə əminsiniz?\n(Adminlər giriş edə biləcək)", parent=self):
            database.set_maintenance_mode(new_status)
            
            # Əgər sistem KİLİDLƏNİRSƏ, bütün aktiv istifadəçiləri sistemdən ataq
            if new_status is True:
                non_admin_ids = database.get_all_active_non_admin_user_ids()
                if non_admin_ids:
                    database.issue_immediate_logout_command(non_admin_ids)
                    database.force_remove_sessions_by_user_id(non_admin_ids)
                    
                    # Real-time notification göndər
                    if hasattr(self.main_app_ref, 'send_realtime_signal'):
                        self.main_app_ref.send_realtime_signal('maintenance_mode_enabled', {
                            'affected_users': non_admin_ids,
                            'enabled_by': 'admin',
                            'action': 'system_locked',
                            'exclude_current_user': True  # YENİ: Cari istifadəçini signal-dən çıxar
                        })
                    
                    messagebox.showinfo("Əməliyyat Uğurlu", f"Sistem kilidləndi və {len(non_admin_ids)} aktiv istifadəçi üçün çıxış əmri göndərildi.")
                else:
                    messagebox.showinfo("Əməliyyat Uğurlu", "Sistem kilidləndi. Aktiv istifadəçi tapılmadı.")
            else:
                # Real-time notification göndər
                if hasattr(self.main_app_ref, 'send_realtime_signal'):
                    self.main_app_ref.send_realtime_signal('maintenance_mode_disabled', {
                        'disabled_by': 'admin',
                        'action': 'system_unlocked',
                        'exclude_current_user': True  # YENİ: Cari istifadəçini signal-dən çıxar
                    })

            self.update_maintenance_button_status()
    def on_row_select(self, event):
        selected_items = self.tree.selection()
        self.history_button.config(state="normal" if len(selected_items) == 1 else "disabled")

    def open_login_history(self):
        selected_items = self.tree.selection()
        if not selected_items: return
        user_id = int(selected_items[0])
        username = self.tree.item(selected_items[0])['values'][1]
        win = LoginHistoryWindow(self, user_id, username)
        self.main_app_ref._center_toplevel(win)

    def on_tree_click(self, event):
        region = self.tree.identify_region(event.x, event.y)
        if region != "cell": return
        column_id = self.tree.identify_column(event.x)
        if column_id == '#1':
            item_id = self.tree.identify_row(event.y)
            if not item_id: return
            user_id = int(item_id)
            self.selection_state[user_id] = not self.selection_state.get(user_id, False)
            self.update_row_visuals(item_id)
            self.update_select_all_checkbox_state()

    def toggle_select_all(self):
        is_selected = self.select_all_var.get()
        for item_id in self.tree.get_children():
            user_id = int(item_id)
            self.selection_state[user_id] = is_selected
            self.update_row_visuals(item_id)
            
    def update_row_visuals(self, item_id):
        user_id = int(item_id)
        is_selected = self.selection_state.get(user_id, False)
        current_values = list(self.tree.item(item_id, 'values'))
        current_values[0] = '[✓]' if is_selected else '[ ]'
        self.tree.item(item_id, values=tuple(current_values))
        
    def update_select_all_checkbox_state(self):
        if not self.selection_state:
            self.select_all_var.set(False)
            return
        all_selected = all(self.selection_state.values())
        self.select_all_var.set(all_selected)

    def load_active_users(self):
        try:
            if hasattr(self, 'status_label') and self.status_label.winfo_exists():
                self.status_label.config(text="Məlumatlar yüklənir...")
        except:
            pass
        self.after(100, self._load_data_from_db)

    def _load_data_from_db(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        self.selection_state.clear()
        
        active_users = database.get_active_user_details()
        for user in active_users:
            user_id = user['user_id']
            self.selection_state[user_id] = False
            login_time_str = user['login_time'].strftime('%d.%m.%Y %H:%M:%S') if user.get('login_time') else 'Bilinmir'
            self.tree.insert('', 'end', values=('[ ]', user['username'], user['name'], login_time_str, user['ip_address']), iid=user_id)
        
        try:
            if hasattr(self, 'status_label') and self.status_label.winfo_exists():
                self.status_label.config(text="Hazır", foreground="blue")
        except:
            pass
        self.update_select_all_checkbox_state()
        try:
            if hasattr(self, 'history_button') and self.history_button.winfo_exists():
                self.history_button.config(state="disabled")
        except:
            pass

    def get_selected_user_ids(self):
        selected_ids = [user_id for user_id, is_selected in self.selection_state.items() if is_selected]
        if not selected_ids:
            messagebox.showwarning("Seçim Yoxdur", "Zəhmət olmasa, əməliyyat üçün ən az bir istifadəçi seçin.", parent=self)
            return None
        
        # YENİ: Admin özünü seçməyə icazə vermə
        current_user_id = self.main_app_ref.current_user.get('id')
        if current_user_id in selected_ids:
            messagebox.showwarning("Xəta", "Özünüzü sistemdən atmaq istəyə bilməzsiniz! Özünüzü seçimdən çıxarın.", parent=self)
            return None
            
        return selected_ids

    def force_logout_selected(self):
        selected_ids = self.get_selected_user_ids()
        if selected_ids:
            # DEBUG: Admin logout əməliyyatı başladıldı
            current_user_id = self.main_app_ref.current_user.get('id')
            logging.info(f"🔍 DEBUG: Admin logout əməliyyatı başladıldı")
            logging.info(f"🔍 DEBUG: Admin ID: {current_user_id}")
            logging.info(f"🔍 DEBUG: Seçilmiş istifadəçi ID-ləri: {selected_ids}")
            
            if messagebox.askyesno("Təsdiq", f"{len(selected_ids)} istifadəçini dərhal sistemdən atmaq istədiyinizə əminsiniz?", parent=self):
                # DEBUG: Təsdiq verildi, əmrlər göndərilir
                logging.info(f"🔍 DEBUG: Təsdiq verildi, əmrlər göndərilir")
                
                database.issue_immediate_logout_command(selected_ids)
                result = database.force_remove_sessions_by_user_id(selected_ids)
                
                # Real-time notification göndər - admin özünü daxil etmə
                if hasattr(self.main_app_ref, 'send_realtime_signal'):
                    # Admin özünü affected_users siyahısından çıxar
                    affected_users = [uid for uid in selected_ids if uid != current_user_id]
                    
                    # DEBUG: Signal göndərilməsi
                    logging.info(f"🔍 DEBUG: Signal göndəriləcək affected_users: {affected_users}")
                    logging.info(f"🔍 DEBUG: Admin özü affected_users-də: {current_user_id in affected_users}")
                    
                    if affected_users:  # Yalnız admin olmayan istifadəçilər varsa signal göndər
                        signal_details = {
                            'affected_users': affected_users,
                            'action': 'force_logout',
                            'executed_by': 'admin',
                            'exclude_current_user': True,  # YENİ: Cari istifadəçini signal-dən çıxar
                            'admin_id': current_user_id  # DEBUG: Admin ID-ni əlavə et
                        }
                        logging.info(f"🔍 DEBUG: Signal göndərilir: {signal_details}")
                        self.main_app_ref.send_realtime_signal('users_force_logout', signal_details)
                    else:
                        logging.info(f"🔍 DEBUG: Signal göndərilmədi - affected_users boş")
                        
                if result:
                    messagebox.showinfo("Uğurlu", f"{len(selected_ids)} istifadəçi üçün çıxış əmri göndərildi və sessiyaları silindi.", parent=self)
                    self.load_active_users()
    
    def timed_logout_selected(self):
        selected_ids = self.get_selected_user_ids()
        if not selected_ids: return
        
        try:
            minutes = int(self.time_entry.get())
            if minutes <= 0: raise ValueError
        except ValueError:
            messagebox.showerror("Xəta", "Zəhmət olmasa, dəqiqə üçün müsbət bir rəqəm daxil edin.", parent=self)
            return
            
        if messagebox.askyesno("Təsdiq", f"Seçilmiş {len(selected_ids)} istifadəçi üçün {minutes} dəqiqə sonra sistemdən atma əmri göndərilsin?", parent=self):
            success_count = database.issue_timed_logout_command(selected_ids, minutes)
            
            # Real-time notification göndər - admin özünü daxil etmə
            if hasattr(self.main_app_ref, 'send_realtime_signal'):
                # Admin özünü affected_users siyahısından çıxar
                current_user_id = self.main_app_ref.current_user.get('id')
                affected_users = [uid for uid in selected_ids if uid != current_user_id]
                
                if affected_users:  # Yalnız admin olmayan istifadəçilər varsa signal göndər
                    self.main_app_ref.send_realtime_signal('users_timed_logout', {
                        'affected_users': affected_users,
                        'timeout_minutes': minutes,
                        'action': 'timed_logout',
                        'executed_by': 'admin',
                        'exclude_current_user': True  # YENİ: Cari istifadəçini signal-dən çıxar
                    })
            
            if success_count > 0:
                messagebox.showinfo("Əmr Göndərildi", f"{success_count} istifadəçi üçün əmr uğurla göndərildi.", parent=self)

    # Tema sistemi silindi