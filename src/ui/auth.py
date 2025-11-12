# auth_windows.py (Yenilənmiş)

import tkinter as tk
from tkinter import ttk
import json  # JSON import əlavə edildi
try:
    from tkinter import font as tkFont
except ImportError:
    # Exe faylında font modulu tapılmadıqda
    tkFont = None
from utils import cache as cache_manager  # Yeni import
from utils.text_formatter import format_name, format_full_name

# Universal kalendar import (nisbi yol ilə)
from .universal_calendar import CalendarWidget, DateEntry

def create_azerbaijani_entry(parent, textvariable, **kwargs):
    """Azərbaycan hərfləri üçün xüsusi Entry widget yaradır"""
    entry = ttk.Entry(parent, textvariable=textvariable, **kwargs)
    
    # Azərbaycan hərfləri üçün xüsusi event binding
    def on_key_press(event):
        # Debug məlumatları
        print(f"Key pressed: char='{event.char}', keysym='{event.keysym}', state={event.state}")
        
        # Klaviatura kombinasiyalarını yoxla
        if event.state & 0x4:  # Ctrl basılıdır
            if event.keysym == 'e' or event.char == 'e':
                # Ctrl+E = ə
                entry.insert(tk.INSERT, 'ə')
                return 'break'
            elif event.keysym == 'g' or event.char == 'g':
                # Ctrl+G = ğ
                entry.insert(tk.INSERT, 'ğ')
                return 'break'
            elif event.keysym == 'u' or event.char == 'u':
                # Ctrl+U = ü
                entry.insert(tk.INSERT, 'ü')
                return 'break'
            elif event.keysym == 'o' or event.char == 'o':
                # Ctrl+O = ö
                entry.insert(tk.INSERT, 'ö')
                return 'break'
            elif event.keysym == 's' or event.char == 's':
                # Ctrl+S = ş
                entry.insert(tk.INSERT, 'ş')
                return 'break'
            elif event.keysym == 'c' or event.char == 'c':
                # Ctrl+C = ç
                entry.insert(tk.INSERT, 'ç')
                return 'break'
            elif event.keysym == 'i' or event.char == 'i':
                # Ctrl+I = ı
                entry.insert(tk.INSERT, 'ı')
                return 'break'
        
        # Alt kombinasiyaları yoxla
        if event.state & 0x20000:  # Alt basılıdır
            if event.keysym == 'e' or event.char == 'e':
                # Alt+E = ə
                entry.insert(tk.INSERT, 'ə')
                return 'break'
            elif event.keysym == 'g' or event.char == 'g':
                # Alt+G = ğ
                entry.insert(tk.INSERT, 'ğ')
                return 'break'
            elif event.keysym == 'u' or event.char == 'u':
                # Alt+U = ü
                entry.insert(tk.INSERT, 'ü')
                return 'break'
            elif event.keysym == 'o' or event.char == 'o':
                # Alt+O = ö
                entry.insert(tk.INSERT, 'ö')
                return 'break'
            elif event.keysym == 's' or event.char == 's':
                # Alt+S = ş
                entry.insert(tk.INSERT, 'ş')
                return 'break'
            elif event.keysym == 'c' or event.char == 'c':
                # Alt+C = ç
                entry.insert(tk.INSERT, 'ç')
                return 'break'
            elif event.keysym == 'i' or event.char == 'i':
                # Alt+I = ı
                entry.insert(tk.INSERT, 'ı')
                return 'break'
        
        # Direkt ə hərfi yoxlaması
        if event.char == 'ə':
            entry.insert(tk.INSERT, 'ə')
            return 'break'
        
        # Sual işarəsi problemini həll et
        if event.char == '?':
            # Əgər sual işarəsi yazılırsa, ə hərfi olaraq dəyişdir
            entry.insert(tk.INSERT, 'ə')
            return 'break'
    
    entry.bind('<KeyPress>', on_key_press)
    
    # Focus olduqda xüsusi ayarlar
    def on_focus_in(event):
        # Entry focus olduqda encoding təyin et
        entry.configure(insertbackground='black')
        print("Entry focus oldu - Azərbaycan hərfləri aktiv")
    
    entry.bind('<FocusIn>', on_focus_in)
    
    return entry

try:
    from .components import Tooltip
except ImportError:
    class Tooltip:
        def __init__(self, *args, **kwargs):
            print("Xəbərdarlıq: 'ui_components.py' faylı tapılmadığı üçün Tooltip işləməyəcək.")

class LoginFrame(ttk.Frame):
    def __init__(self, parent, login_callback, register_callback, change_company_callback, company_name):
        super().__init__(parent, padding="20")
        self.login_callback = login_callback
        self.register_callback = register_callback
        self.change_company_callback = change_company_callback
        self.company_name = company_name
        self.server_connected = False
        self.animation = None

        # --- Stil Təyinləmələri ---
        try:
            style = ttk.Style(self)
            
            # Sadə stil təyinləmələri
            style.configure('TFrame', background='white')
            style.configure('TLabel', background='white')
            style.configure('TButton', padding=(10, 5))
            style.configure('TCheckbutton', background='white')
            
            self.configure(style='TFrame')
        except Exception as e:
            # Əgər stil təyinləməsi xəta versə, sadəcə keçirik
            pass
        
        try:
            container = ttk.Frame(self, style='TFrame')
        except:
            container = ttk.Frame(self)
        container.pack(expand=True)
        
        title_label = tk.Label(container, text="Sistemə Giriş", font=('Tahoma', 18), foreground='#333', background='white')
        title_label.pack(pady=(0, 5))
        
        # Şirkət adını yuxarıya qaldır
        company_display = company_name if company_name else "Naməlum Şirkət"
        self.company_label = ttk.Label(container, text=f"Şirkət: {company_display}", foreground='#555', cursor="hand2")
        self.company_label.pack(pady=(0, 20))
        self.company_label.bind("<Double-1>", lambda event: self.change_company_callback())
        Tooltip(self.company_label, text="Şirkəti dəyişmək üçün 2 dəfə klikləyin")
        
        ttk.Label(container, text="İstifadəçi adı:").pack(padx=10, pady=(10, 0), anchor='w')
        self.username = tk.StringVar()
        username_entry = ttk.Entry(container, textvariable=self.username, width=35)
        username_entry.pack(padx=10, pady=(0, 10), ipady=4)
        username_entry.focus()
        
        ttk.Label(container, text="Şifrə:").pack(padx=10, pady=(10, 0), anchor='w')
        self.password = tk.StringVar()
        password_entry = ttk.Entry(container, textvariable=self.password, show="*", width=35)
        password_entry.pack(padx=10, pady=(0, 5), ipady=4)
        
        # --- YENİ "MƏNİ XATIRLA" CHECKBOX ---
        # Default olaraq Məni xatırla aktiv olsun
        # "Məni xatırla" default olaraq seçilidir
        self.remember_var = tk.BooleanVar(value=True)
        remember_cb = ttk.Checkbutton(container, text="Məni xatırla (Avtomatik giriş)", variable=self.remember_var, style='TCheckbutton')
        remember_cb.pack(pady=(0, 10), padx=10, anchor='w')
        
        # İstifadəçiyə məlumat ver
        info_label = tk.Label(container, text="✓ Seçildikdə, növbəti dəfə avtomatik giriş ediləcək", 
                             font=('Tahoma', 8), foreground='#666', background='white')
        info_label.pack(pady=(0, 5), padx=10, anchor='w')
        # --- YENİLƏMƏNİN SONU ---

        password_entry.bind('<Return>', self._attempt_login_event)
        
        # --- ŞİFRƏMİ UNUTDUM DÜYMƏSİ ---
        self.forgot_password_callback = None  # Callback funksiyası
        
        try:
            button_frame = ttk.Frame(container, style='TFrame')
        except:
            button_frame = ttk.Frame(container)
        button_frame.pack(pady=10)
        
        ttk.Button(button_frame, text="Giriş", command=self.attempt_login, width=12).pack(side="left", padx=5)
        ttk.Button(button_frame, text="Qeydiyyat", command=self.register_callback, width=12).pack(side="left", padx=5)
        
        # Şifrəmi unutdum düyməsi
        try:
            forgot_frame = ttk.Frame(container, style='TFrame')
        except:
            forgot_frame = ttk.Frame(container)
        forgot_frame.pack(pady=(5, 0))
        
        forgot_button = ttk.Button(forgot_frame, text="Şifrəmi Unutdum", 
                                  command=self.forgot_password, 
                                  width=15)
        forgot_button.pack()

        self._load_from_cache()



    def set_forgot_password_callback(self, callback):
        """Şifrəmi unutdum callback funksiyasını təyin edir"""
        self.forgot_password_callback = callback
    
    def forgot_password(self):
        """Şifrəmi unutdum düyməsinə basıldıqda"""
        if self.forgot_password_callback:
            self.forgot_password_callback()

    def _load_from_cache(self):
        """Yadda saxlanmış məlumatları yükləyir."""
        import logging
        import os
        import threading
        
        def cache_worker():
            try:
                logging.info("=== _load_from_cache başladı ===")
                
                # Cache fayllarının mövcudluğunu yoxlayırıq
                cache_file = os.path.join(os.getenv('APPDATA'), 'MezuniyyetSistemi', 'user_cache.json')
                user_data_file = os.path.join(os.getenv('APPDATA'), 'MezuniyyetSistemi', 'user_data.json')
                
                logging.info(f"Cache file exists: {os.path.exists(cache_file)}")
                logging.info(f"User data file exists: {os.path.exists(user_data_file)}")
                
                # Yeni cache sistemi ilə istifadəçi məlumatlarını alırıq
                credentials = cache_manager.get_user_credentials()
                logging.info(f"Retrieved credentials: {credentials}")
                
                username = credentials.get('username', '')
                password = credentials.get('password', '')
                remember_me = credentials.get('remember_me', False)
                
                logging.info(f"Username: '{username}', Password: {'*' * len(password) if password else 'None'}, Remember: {remember_me}")
                
                if username and password:
                    logging.info(f"Cache-də məlumatlar tapıldı - Username: '{username}', Remember: {remember_me}")
                    
                    # UI yeniləməsini əsas thread-də edirik
                    self.after(0, self._update_cache_ui, username, password, remember_me)
                    
                    logging.info("Məlumatlar uğurla yükləndi")
                else:
                    logging.info("Cache-də istifadəçi məlumatları tapılmadı")
                
                logging.info("=== _load_from_cache bitdi ===")
            except Exception as e:
                logging.error(f"Cache yükləmə xətası: {e}")
        
        # Cache yükləməsini arxa fonda edirik
        threading.Thread(target=cache_worker, daemon=True).start()
    
    def _update_cache_ui(self, username, password, remember_me):
        """Cache məlumatlarını UI-da yeniləyir"""
        # Məlumatları təyin edirik
        self.username.set(username)
        self.password.set(password)
        self.remember_var.set(remember_me)
        
        # Pəncərəni yeniləyirik
        self.update()
        self.update_idletasks()
        
        import logging
        logging.info(f"Məlumatlar təyin edildi - Username: '{self.username.get()}', Password: '{self.password.get()}', Remember: {self.remember_var.get()}")

    def attempt_login(self):
        """Giriş cəhdini "Məni xatırla" statusu ilə birlikdə göndərir."""
        self.login_callback(self.username.get(), self.password.get(), self.remember_var.get())
        
    def _attempt_login_event(self, event=None):
        self.attempt_login()

class RegisterFrame(ttk.Frame):
    def __init__(self, parent, register_callback, back_callback):
        super().__init__(parent, padding="20")

        self.register_callback = register_callback
        self.back_callback = back_callback

        try:
            style = ttk.Style(self)
            self.configure(style='TFrame')
        except Exception as e:
            # Əgər stil təyinləməsi xəta versə, sadəcə keçirik
            pass

        # Scrollable frame yaradaq
        canvas = tk.Canvas(self)
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        # Başlıq
        title_frame = ttk.Frame(scrollable_frame)
        title_frame.pack(fill='x', pady=(0, 20))
        title_label = ttk.Label(title_frame, text="Yeni İstifadəçi Qeydiyyatı", 
                 style='Title.TLabel')
        title_label.pack()
        
        # Başlıq altındakı xətt
        separator1 = ttk.Separator(scrollable_frame, orient='horizontal')
        separator1.pack(fill='x', pady=(0, 20))

        # Şəxsi məlumatlar bölməsi
        personal_frame = ttk.LabelFrame(scrollable_frame, text="👤 Şəxsi Məlumatlar", padding="15")
        personal_frame.pack(fill='x', pady=(0, 15), padx=5)
        
        # Şəxsi məlumatlar - 2 sütun
        personal_row1 = ttk.Frame(personal_frame)
        personal_row1.pack(fill='x', pady=(0, 10))
        
        # Sol sütun
        personal_left = ttk.Frame(personal_row1)
        personal_left.pack(side='left', fill='x', expand=True, padx=(0, 10))
        
        ttk.Label(personal_left, text="Ad:", font=('Tahoma', 10, 'bold'), foreground='#2E86AB').pack(anchor='w')
        self.first_name = tk.StringVar()
        create_azerbaijani_entry(personal_left, self.first_name, width=25).pack(fill='x', pady=(2, 8), ipady=3)
        
        ttk.Label(personal_left, text="Ata adı:", font=('Tahoma', 10, 'bold'), foreground='#2E86AB').pack(anchor='w')
        self.father_name = tk.StringVar()
        create_azerbaijani_entry(personal_left, self.father_name, width=25).pack(fill='x', pady=(2, 8), ipady=3)
        
        ttk.Label(personal_left, text="Telefon nömrəsi:", font=('Tahoma', 10, 'bold'), foreground='#2E86AB').pack(anchor='w')
        self.phone_number = tk.StringVar()
        create_azerbaijani_entry(personal_left, self.phone_number, width=25).pack(fill='x', pady=(2, 8), ipady=3)
        
        ttk.Label(personal_left, text="Ünvan:", font=('Tahoma', 10, 'bold'), foreground='#2E86AB').pack(anchor='w')
        self.address = tk.StringVar()
        create_azerbaijani_entry(personal_left, self.address, width=25).pack(fill='x', pady=(2, 8), ipady=3)
        
        # Sağ sütun
        personal_right = ttk.Frame(personal_row1)
        personal_right.pack(side='right', fill='x', expand=True, padx=(10, 0))
        
        ttk.Label(personal_right, text="Soyad:", font=('Tahoma', 10, 'bold'), foreground='#2E86AB').pack(anchor='w')
        self.last_name = tk.StringVar()
        create_azerbaijani_entry(personal_right, self.last_name, width=25).pack(fill='x', pady=(2, 8), ipady=3)
        
        ttk.Label(personal_right, text="Doğum tarixi:", font=('Tahoma', 10, 'bold'), foreground='#2E86AB').pack(anchor='w')
        self.birth_date = tk.StringVar()
        self.birth_date.set("1990-01-01")
        birth_date_entry = DateEntry(personal_right, variable=self.birth_date)
        birth_date_entry.pack(fill='x', pady=(2, 8), ipady=3)
        
        ttk.Label(personal_right, text="Email ünvanı:", font=('Tahoma', 10, 'bold'), foreground='#2E86AB').pack(anchor='w')
        self.email = tk.StringVar()
        create_azerbaijani_entry(personal_right, self.email, width=25).pack(fill='x', pady=(2, 8), ipady=3)
        
        # İş məlumatları bölməsi
        work_frame = ttk.LabelFrame(scrollable_frame, text="💼 İş Məlumatları", padding="15")
        work_frame.pack(fill='x', pady=(0, 15), padx=5)
        
        # İş məlumatları - 2 sütun
        work_row1 = ttk.Frame(work_frame)
        work_row1.pack(fill='x', pady=(0, 10))
        
        # Sol sütun
        work_left = ttk.Frame(work_row1)
        work_left.pack(side='left', fill='x', expand=True, padx=(0, 10))
        
        ttk.Label(work_left, text="🆔 FIN Kodu:", font=('Tahoma', 10, 'bold'), foreground='#2E86AB').pack(anchor='w')
        self.fin_code = tk.StringVar()
        ttk.Entry(work_left, textvariable=self.fin_code, width=25).pack(fill='x', pady=(2, 8), ipady=3)
        
        ttk.Label(work_left, text="🏢 Şöbə:", font=('Tahoma', 10, 'bold'), foreground='#2E86AB').pack(anchor='w')
        self.department_var = tk.StringVar()
        self.department_combo = ttk.Combobox(work_left, textvariable=self.department_var, 
                                           font=('Tahoma', 10), state="readonly", width=23)
        self.department_combo.pack(fill='x', pady=(2, 8), ipady=3)
        
        # Sağ sütun
        work_right = ttk.Frame(work_row1)
        work_right.pack(side='right', fill='x', expand=True, padx=(10, 0))
        
        ttk.Label(work_right, text="👔 Vəzifə:", font=('Tahoma', 10, 'bold'), foreground='#2E86AB').pack(anchor='w')
        self.position_var = tk.StringVar()
        self.position_combo = ttk.Combobox(work_right, textvariable=self.position_var, 
                                         font=('Tahoma', 10), state="readonly", width=23)
        self.position_combo.pack(fill='x', pady=(2, 8), ipady=3)
        
        # Şöbə və vəzifə məlumatlarını yüklə (xəta olsa belə davam et)
        try:
            self.load_department_and_position_data()
        except Exception as e:
            print(f"DEBUG: Şöbə və vəzifə məlumatları yüklənərkən xəta: {e}")
            logging.warning(f"Şöbə və vəzifə məlumatları yüklənərkən xəta: {e}")
            # Xəta olsa belə, boş list ilə davam et
            self.department_combo['values'] = []
            self.position_combo['values'] = []

        # Sistem məlumatları bölməsi
        system_frame = ttk.LabelFrame(scrollable_frame, text="🔐 Sistem Məlumatları", padding="15")
        system_frame.pack(fill='x', pady=(0, 20), padx=5)
        
        # Sistem məlumatları - 2 sütun
        system_row1 = ttk.Frame(system_frame)
        system_row1.pack(fill='x', pady=(0, 10))
        
        # Sol sütun
        system_left = ttk.Frame(system_row1)
        system_left.pack(side='left', fill='x', expand=True, padx=(0, 10))
        
        ttk.Label(system_left, text="İstifadəçi adı:", font=('Tahoma', 10, 'bold'), foreground='#F18F01').pack(anchor='w')
        self.username = tk.StringVar()
        ttk.Entry(system_left, textvariable=self.username, width=25).pack(fill='x', pady=(2, 8), ipady=3)
        
        ttk.Label(system_left, text="Şifrə:", font=('Tahoma', 10, 'bold'), foreground='#F18F01').pack(anchor='w')
        self.password = tk.StringVar()
        ttk.Entry(system_left, textvariable=self.password, show="*", width=25).pack(fill='x', pady=(2, 8), ipady=3)
        
        # Sağ sütun
        system_right = ttk.Frame(system_row1)
        system_right.pack(side='right', fill='x', expand=True, padx=(10, 0))
        
        ttk.Label(system_right, text="Şifrəni təsdiq edin:", font=('Tahoma', 10, 'bold'), foreground='#F18F01').pack(anchor='w')
        self.confirm_password = tk.StringVar()
        password_confirm_entry = ttk.Entry(system_right, textvariable=self.confirm_password, show="*", width=25)
        password_confirm_entry.pack(fill='x', pady=(2, 8), ipady=3)
        password_confirm_entry.bind('<Return>', self._attempt_register_event)

        # Düymələr
        button_frame = ttk.Frame(scrollable_frame)
        button_frame.pack(pady=20)
        
        # Düymə stilləri
        style.configure('Register.TButton', font=('Tahoma', 11, 'bold'), padding=10)
        style.configure('Back.TButton', font=('Tahoma', 10), padding=8)
        
        ttk.Button(button_frame, text="✅ Qeydiyyatdan Keç", command=self.attempt_register, 
                  style='Register.TButton', width=22).pack(side="left", padx=8)
        ttk.Button(button_frame, text="⬅️ Geri", command=self.back_callback, 
                  style='Back.TButton', width=18).pack(side="left", padx=8)

        # Scrollbar və canvas-ı pack edək
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Mouse wheel event bind edək
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        canvas.bind_all("<MouseWheel>", _on_mousewheel)
    
    def load_department_and_position_data(self):
        """Şöbə və vəzifə məlumatlarını yükləyir"""
        try:
            from database import database as db
            
            # Veritabanına qoşul
            conn = db.db_connect()
            if not conn:
                print("DEBUG: Veritabanına qoşulmaq mümkün olmadı - boş list ilə davam edirik")
                # Boş list ilə davam et
                self.department_combo['values'] = []
                self.position_combo['values'] = []
                return
                
            cursor = conn.cursor()

            dept_options = []
            pos_options = []

            try:
                # Şöbələri yüklə (əsas cədvəldən)
                cursor.execute("SELECT id, name FROM departments WHERE is_active = true ORDER BY name")
                departments = cursor.fetchall()
                dept_options = [f"{dept[0]} - {dept[1]}" for dept in departments]
            except Exception:
                # Fallback: employees cədvəlindən unikalları götür
                try:
                    cursor.execute("SELECT DISTINCT department FROM employees WHERE department IS NOT NULL AND department <> '' ORDER BY department")
                    departments = [row[0] for row in cursor.fetchall()]
                    dept_options = departments
                except Exception as e:
                    try:
                        conn.rollback()
                    except Exception:
                        pass
                    print(f"Şöbə məlumatları alına bilmədi: {e}")

            try:
                # Vəzifələri yüklə (əsas cədvəldən)
                cursor.execute("SELECT id, name FROM positions WHERE is_active = true ORDER BY name")
                positions = cursor.fetchall()
                pos_options = [f"{pos[0]} - {pos[1]}" for pos in positions]
            except Exception:
                # Fallback: employees cədvəlindən unikalları götür
                try:
                    cursor.execute("SELECT DISTINCT position FROM employees WHERE position IS NOT NULL AND position <> '' ORDER BY position")
                    positions = [row[0] for row in cursor.fetchall()]
                    pos_options = positions
                except Exception as e:
                    try:
                        conn.rollback()
                    except Exception:
                        pass
                    print(f"Vəzifə məlumatları alına bilmədi: {e}")

            self.department_combo['values'] = dept_options
            self.position_combo['values'] = pos_options

            # Əgər boşdursa placeholder qoyaq
            if not self.department_combo['values']:
                self.department_combo['values'] = ["— Məlumat yoxdur —"]
            if not self.position_combo['values']:
                self.position_combo['values'] = ["— Məlumat yoxdur —"]
            
            conn.close()
            
        except Exception as e:
            print(f"Şöbə və vəzifə məlumatları yüklənərkən xəta: {e}")
    
    def _extract_id_from_combobox(self, combo_value):
        """Combobox dəyərindən ID-ni çıxarır (format: "ID - Name")"""
        if not combo_value or not combo_value.strip():
            return None
        try:
            # "ID - Name" formatından ID-ni çıxar
            parts = combo_value.strip().split(" - ", 1)
            if len(parts) == 2:
                return int(parts[0])
            return None
        except (ValueError, IndexError):
            return None

    def attempt_register(self):
        # Ad və soyadı birləşdirərək tam ad yaradaq
        first_name = self.first_name.get().strip()
        last_name = self.last_name.get().strip()
        full_name = format_full_name(first_name, last_name)
        
        # Doğum tarixini yoxlayırıq - default tarix olaraq saxlayırıq
        birth_date_value = self.birth_date.get().strip()
        if birth_date_value == "":
            birth_date_value = "1990-01-01"  # Default tarix
        
        # Combobox-lardan ID-ləri çıxar
        department_id = self._extract_id_from_combobox(self.department_var.get())
        position_id = self._extract_id_from_combobox(self.position_var.get())
        
        self.register_callback(
            full_name,  # name
            self.username.get(),
            self.email.get(),
            self.password.get(),
            self.confirm_password.get(),
            "30",  # total_days - default dəyər
            self.first_name.get(),
            self.last_name.get(),
            self.father_name.get(),
            self.phone_number.get(),
            birth_date_value,  # birth_date
            self.fin_code.get().strip(),  # fin_code
            department_id,  # department_id
            position_id,  # position_id
            "",  # hire_date - boş
            "",  # salary - boş
            self.address.get(),
            ""  # emergency_contact - boş
        )
        
    def _attempt_register_event(self, event=None):
        self.attempt_register()