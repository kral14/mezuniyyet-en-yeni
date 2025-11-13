# ui/dashboard_calendar_frame.py (Rola görə dinamik görünüş)

import tkinter as tk
from tkinter import ttk, messagebox
import calendar
import logging
from datetime import datetime, date, timedelta
from database import database
from .components import Tooltip, safe_date_format, get_vacation_status_and_color

class DashboardCalendarFrame(ttk.Frame):
    def __init__(self, parent, main_app_ref):
        super().__init__(parent)
        self.main_app_ref = main_app_ref
        self.current_user = main_app_ref.current_user
        self.is_admin = self.current_user['role'].strip() == 'admin'
        self.main_font = main_app_ref.main_font
        
        self.current_date = datetime.now()
        # DÜZƏLİŞ: İşçi rəngləri əvəzinə status rəngləri istifadə edirik
        self.status_colors = {
            "red": "#FF6B6B",           # Bitmiş məzuniyyətlər
            "green": "#4ECDC4",         # Davam edən məzuniyyətlər  
            "#007bff": "#45B7D1",       # Planlaşdırılan məzuniyyətlər
            "#E49B0F": "#FFEAA7",       # Gözləyən məzuniyyətlər
            "gray": "#85929E",          # Rədd edilmiş məzuniyyətlər
            "black": "#2C3E50"          # Xəta vəziyyəti
        }
        # Əlavə olaraq işçi rənglərini də saxlayırıq (tooltip üçün)
        self.colors = [
            "#FF6B6B", "#4ECDC4", "#45B7D1", "#96CEB4", "#FFEAA7",
            "#DDA0DD", "#98D8C8", "#F7DC6F", "#BB8FCE", "#85C1E9",
            "#82E0AA", "#F8C471", "#F1948A", "#85929E", "#D7BDE2",
            "#A9DFBF", "#FAD7A0", "#AED6F1", "#F9E79F", "#D5A6BD"
        ]
        self.employee_colors = {}
        # DÜZƏLİŞ: vacations atributunu başlanğıcda boş list kimi təyin et
        self.vacations = []

        self.create_widgets()
        
    def create_widgets(self):
        import logging
        logging.debug("DashboardCalendarFrame create_widgets başladı")
        print("DEBUG: DashboardCalendarFrame create_widgets started")
        
        notebook = ttk.Notebook(self)
        notebook.pack(expand=True, fill='both', padx=5, pady=5)
        print("DEBUG: Notebook created")

        dashboard_tab = ttk.Frame(notebook, padding=10)
        notebook.add(dashboard_tab, text='İdarə Paneli')
        print("DEBUG: Dashboard tab added")
        self.create_dashboard_widgets(dashboard_tab)
        
        calendar_tab = ttk.Frame(notebook, padding=10)
        notebook.add(calendar_tab, text='Ümumi Təqvim')
        print("DEBUG: Calendar tab added")
        self.create_calendar_widgets(calendar_tab)
        
        # Notebook-un mövcudluğunu yoxla
        print(f"DEBUG: Notebook tabs count: {len(notebook.tabs())}")
        for i, tab_id in enumerate(notebook.tabs()):
            tab_text = notebook.tab(tab_id, "text")
            # Azərbaycan hərflərini ASCII-ə çevir
            safe_text = tab_text.encode('ascii', 'ignore').decode('ascii')
            print(f"DEBUG: Tab {i}: '{safe_text}'")
        
        logging.debug("DashboardCalendarFrame create_widgets tamamlandı")
        print("DEBUG: DashboardCalendarFrame create_widgets completed")

    def load_data(self):
        """Məlumatları bazadan yükləyir və komponentləri yeniləyir - ASİNXRON."""
        import threading
        import time
        
        load_start = time.time()
        print(f"🟡 [DEBUG] [UI THREAD] ⏱️ dashboard.load_data BAŞLADI (UI thread-də)")
        logging.debug("load_data başladı")
        
        # OPTİMALLAŞDIRMA: Database işlərini asinxron thread-də et - UI bloklanmasın
        def load_in_thread():
            thread_start = time.time()
            thread_id = threading.current_thread().ident
            thread_name = threading.current_thread().name
            print(f"🟡 [DEBUG] ⏱️ dashboard.load_data THREAD BAŞLADI: Thread ID={thread_id}, Name={thread_name}")
            
            try:
                # Təhlükəsizlik: SQL sorğusunda birbaşa filtr tətbiq edilir
                all_vacations = database.get_all_active_vacations(current_user=self.current_user)
                print(f"🟡 [DEBUG] ⏱️ get_all_active_vacations bitdi: {time.time() - thread_start:.3f}s")
                
                # Artıq SQL sorğusunda filtr tətbiq edildiyi üçün, yalnız admin üçün bütün məzuniyyətləri göstər
                # User üçün yalnız eyni şöbədəki məzuniyyətlər artıq SQL-də filtr edilib
                self.vacations = all_vacations
                
                # Filtr tətbiq et (əgər seçilibsə)
                if hasattr(self, 'selected_department_filter') and self.selected_department_filter:
                    # Optimallaşdırılmış filtr - bir dəfə sorğu ilə bütün işçilərin şöbələrini alırıq
                    try:
                        from database import database as db
                        conn = db.db_connect()
                        if conn:
                            with conn.cursor() as cur:
                                # Seçilmiş şöbədəki bütün işçilərin ID-lərini alırıq
                                cur.execute("SELECT id, name FROM employees WHERE department = %s AND (hide IS NULL OR hide = FALSE)", 
                                          (self.selected_department_filter,))
                                dept_employees = cur.fetchall()
                                dept_employee_ids = {emp[0] for emp in dept_employees}
                                dept_employee_names = {emp[1] for emp in dept_employees}
                                
                                logging.info(f"Şöbə '{self.selected_department_filter}' üçün {len(dept_employee_ids)} işçi tapıldı")
                                
                                # Yalnız seçilmiş şöbədəki işçilərin məzuniyyətlərini göstər
                                filtered_vacations = []
                                for vac in self.vacations:
                                    employee_id = vac.get('employee_id')
                                    employee_name = vac.get('employee', '')
                                    
                                    # İşçi ID və ya adına görə yoxla
                                    if employee_id and employee_id in dept_employee_ids:
                                        filtered_vacations.append(vac)
                                    elif employee_name and employee_name in dept_employee_names:
                                        filtered_vacations.append(vac)
                                
                                self.vacations = filtered_vacations
                                logging.info(f"Filtr tətbiq edildi: {len(filtered_vacations)} məzuniyyət tapıldı")
                            conn.close()
                        else:
                            logging.warning("Database qoşulması uğursuz - filtr tətbiq edilmədi")
                    except Exception as e:
                        logging.error(f"Filtr tətbiq edilərkən xəta: {e}", exc_info=True)
                        # Xəta baş verdikdə bütün məzuniyyətləri göstər
                        self.vacations = all_vacations
            
                logging.debug(f"get_all_active_vacations nəticəsi: {self.vacations}")
                logging.debug(f"self.vacations uzunluğu: {len(self.vacations)}")
                # DÜZƏLİŞ: Məzuniyyət məlumatlarını düzgün emal edirik
                for vacation in self.vacations:
                    # Tarixləri date obyektinə çeviririk
                    if isinstance(vacation['start_date'], str):
                        vacation['start_date'] = datetime.strptime(vacation['start_date'], '%Y-%m-%d').date()
                    if isinstance(vacation['end_date'], str):
                        vacation['end_date'] = datetime.strptime(vacation['end_date'], '%Y-%m-%d').date()
                # DÜZƏLİŞ: employee_name də əlavə edirik
                for vacation in self.vacations:
                    if 'employee' in vacation and 'employee_name' not in vacation:
                        vacation['employee_name'] = vacation['employee']
                    # DÜZƏLİŞ: Məzuniyyət məlumatlarına status əlavə edirik ui_components uyğun format üçün
                    vacation['baslama'] = vacation['start_date']
                    vacation['bitme'] = vacation['end_date']
                # DÜZƏLİŞ: İşçi rənglərini tooltip üçün saxlayırıq
                unique_employees = sorted(list({vac['employee'] for vac in self.vacations}))
                logging.debug(f"📋 Unikal işçilər tapıldı: {unique_employees}")
                logging.debug(f"🎨 Mövcud rənglər: {self.colors}")
                for i, emp in enumerate(unique_employees):
                    selected_color = self.colors[i % len(self.colors)]
                    self.employee_colors[emp] = selected_color
                    logging.debug(f"  🎨 {emp} → Rəng: {selected_color} (indeks: {i}, modul: {i % len(self.colors)})")
                logging.debug(f"📊 İşçi rəngləri: {self.employee_colors}")
                
                thread_time = time.time() - thread_start
                print(f"🟡 [DEBUG] ⏱️ dashboard.load_data THREAD bitdi: {thread_time:.3f}s")
                
                # UI thread-də refresh et - thread-də bloklanmamaq üçün
                def refresh_ui():
                    try:
                        ui_start = time.time()
                        print(f"🟡 [DEBUG] [UI THREAD] ⏱️ dashboard.load_data UI refresh BAŞLADI")
                        
                        # OPTİMALLAŞDIRMA: Təqvim yeniləməsini asinxron et - UI bloklanmasın
                        self.update_dashboard_data()
                        # calendar_frame yaradılıbmışdırsa yenilə - asinxron
                        if hasattr(self, 'calendar_frame') and self.calendar_frame.winfo_exists():
                            # UI thread-də bloklanmamaq üçün after() istifadə et
                            self.after(0, self.update_calendar)
                        
                        ui_time = time.time() - ui_start
                        print(f"🟡 [DEBUG] [UI THREAD] ⏱️ dashboard.load_data UI refresh bitdi: {ui_time:.3f}s")
                    except Exception as e:
                        print(f"❌ [DEBUG] [UI THREAD] dashboard.load_data UI refresh xətası: {e}")
                        import traceback
                        print(f"❌ [DEBUG] [UI THREAD] dashboard.load_data UI refresh xəta traceback:\n{traceback.format_exc()}")
                        messagebox.showerror("Məlumat Yükləmə Xətası", f"Dashboard UI yenilənərkən xəta baş verdi:\n{e}", parent=self)
                
                # UI thread-də çağır
                root = self.winfo_toplevel()
                if root and root.winfo_exists():
                    root.after(0, refresh_ui)
                else:
                    self.after(0, refresh_ui)
                    
            except Exception as e:
                thread_time = time.time() - thread_start
                print(f"❌ [DEBUG] ⏱️ dashboard.load_data THREAD xətası: {e}, vaxt: {thread_time:.3f}s")
                import traceback
                error_details = traceback.format_exc()
                print(f"❌ [DEBUG] dashboard.load_data THREAD xəta traceback:\n{error_details}")
                logging.error(f"Dashboard load_data xətası: {e}", exc_info=True)
                
                # UI thread-də xəta mesajı göstər
                def show_error():
                    messagebox.showerror("Məlumat Yükləmə Xətası", f"Dashboard məlumatları yüklənərkən xəta baş verdi:\n{e}", parent=self)
                
                root = self.winfo_toplevel()
                if root and root.winfo_exists():
                    root.after(0, show_error)
                else:
                    self.after(0, show_error)
        
        # Asinxron thread-də yüklə - UI bloklanmasın
        thread = threading.Thread(target=load_in_thread, daemon=True, name="DashboardDataLoader")
        thread.start()
        print(f"🟡 [DEBUG] [UI THREAD] ⏱️ dashboard.load_data thread başladıldı, ID: {thread.ident}")
        
        load_time = time.time() - load_start
        print(f"🟡 [DEBUG] [UI THREAD] ⏱️ dashboard.load_data funksiyası bitdi: {load_time:.3f}s (thread başladıldı)")

    def create_dashboard_widgets(self, parent_frame):
        parent_frame.rowconfigure(0, weight=1)

        self.pending_card = ttk.LabelFrame(parent_frame, text="Gözləyən Sorğular (0)")
        self.pending_card.grid(row=0, column=0, padx=10, pady=10, sticky='nsew')
        
        # DƏYİŞİKLİK: Panelləri rola görə yerləşdiririk
        if self.is_admin:
            parent_frame.columnconfigure((0, 1, 2), weight=1)
            self.active_users_card = ttk.LabelFrame(parent_frame, text="Aktiv İstifadəçilər (0)")
            self.active_users_card.grid(row=0, column=1, padx=10, pady=10, sticky='nsew')
            self.on_vacation_card = ttk.LabelFrame(parent_frame, text="Bu Gün Məzuniyyətdə (0)")
            self.on_vacation_card.grid(row=0, column=2, padx=10, pady=10, sticky='nsew')
        else:
            # Əgər admin deyilsə, Aktiv İstifadəçilər paneli heç yaradılmır
            parent_frame.columnconfigure((0, 1), weight=1)
            self.on_vacation_card = ttk.LabelFrame(parent_frame, text="Bu Gün Məzuniyyətdə (0)")
            self.on_vacation_card.grid(row=0, column=1, padx=10, pady=10, sticky='nsew')

    def update_dashboard_data(self):
        try:
            # Köhnə məlumatları təmizləyirik
            for widget in self.pending_card.winfo_children(): widget.destroy()
            for widget in self.on_vacation_card.winfo_children(): widget.destroy()
            
            # DƏYİŞİKLİK: Aktiv istifadəçiləri yalnız adminlər üçün yükləyirik
            if self.is_admin and hasattr(self, 'active_users_card'):
                for widget in self.active_users_card.winfo_children(): widget.destroy()
                active_users = database.get_active_user_details()
                self.active_users_card.config(text=f"Aktiv İstifadəçilər ({len(active_users)})")
                for user in active_users:
                    link = ttk.Label(self.active_users_card, text=f"● {user['name']}", foreground="green", cursor="hand2", anchor="w")
                    link.pack(fill='x', padx=10, pady=2)
                    link.bind("<Button-1>", lambda e, u=user: self.main_app_ref.show_employee_by_id(u['user_id']))

            # Bu gün məzuniyyətdə olanlar (dəyişiklik yoxdur)
            today = date.today()
            on_vacation_today = [v for v in self.vacations if v.get('start_date') and v.get('end_date') and v['start_date'] <= today <= v['end_date']]
            self.on_vacation_card.config(text=f"Bu Gün Məzuniyyətdə ({len(on_vacation_today)})")
            for vac in on_vacation_today:
                link = ttk.Label(self.on_vacation_card, text=vac['employee'], foreground="purple", cursor="hand2", anchor="w")
                link.pack(fill='x', padx=10, pady=2)
                link.bind("<Button-1>", lambda e, v=vac: self.main_app_ref.show_employee_by_id(v['employee_id']))

            # DƏYİŞİKLİK: Gözləyən sorğuları rola görə yükləyirik
            pending_requests = []
            if self.is_admin:
                pending_requests = database.get_pending_vacation_requests()
            else:
                pending_requests = database.get_pending_vacation_requests(user_id=self.current_user['id'])
            
            self.pending_card.config(text=f"Gözləyən Sorğular ({len(pending_requests)})")
            for req in pending_requests:
                # DÜZƏLİŞ: employee_name yoxdursa employee istifadə edirik
                employee_name = req.get('employee_name', req.get('employee', 'Naməlum'))
                start_str = safe_date_format(req['start_date'])
                text = f"{employee_name}: {start_str}"
                link = ttk.Label(self.pending_card, text=text, foreground="#E49B0F", cursor="hand2", anchor="w")
                link.pack(fill='x', padx=10, pady=2)
                link.bind("<Button-1>", lambda e, r=req: self.main_app_ref.show_employee_by_id(r['employee_id']))
        except Exception as e:
            messagebox.showerror("Dashboard Xətası", f"Dashboard məlumatları yenilənərkən xəta baş verdi:\n{e}", parent=self)

    def create_calendar_widgets(self, parent_frame):
        # Header frame
        header_frame = ttk.Frame(parent_frame)
        header_frame.pack(fill='x', pady=(0, 10))
        ttk.Button(header_frame, text="<", command=lambda: self.change_month(-1)).pack(side='left')
        self.month_year_label = ttk.Label(header_frame, text="", font=(self.main_font, 16, "bold"), anchor='center')
        self.month_year_label.pack(side='left', expand=True, fill='x')
        ttk.Button(header_frame, text=">", command=lambda: self.change_month(1)).pack(side='right')
        
        # Admin üçün filtr paneli
        if self.is_admin:
            filter_frame = ttk.Frame(parent_frame)
            filter_frame.pack(fill='x', pady=(0, 10))
            
            filter_label = ttk.Label(filter_frame, text="Şöbə:", font=(self.main_font, 9))
            filter_label.pack(side='left', padx=(0, 5))
            
            self.department_filter_var = tk.StringVar()
            self.department_filter_var.trace('w', lambda *args: self._on_calendar_filter_change())
            
            # Şöbələri yüklə
            try:
                from database.departments_positions_queries import get_departments_for_combo
                departments = get_departments_for_combo()
                dept_options = ["Bütün şöbələr"] + [dept[1] for dept in departments]
            except:
                dept_options = ["Bütün şöbələr"]
            
            department_combo = ttk.Combobox(filter_frame, textvariable=self.department_filter_var, 
                                          values=dept_options, state='readonly', width=20)
            department_combo.pack(side='left', padx=(0, 5))
            department_combo.set("Bütün şöbələr")
            
            self.selected_department_filter = None

        self.calendar_frame = ttk.Frame(parent_frame)
        self.calendar_frame.pack(expand=True, fill='both')
    
    def _on_calendar_filter_change(self):
        """Kalendarda filtr dəyişdikdə çağırılır"""
        if hasattr(self, 'department_filter_var'):
            selected = self.department_filter_var.get()
            if selected == "Bütün şöbələr" or not selected:
                self.selected_department_filter = None
            else:
                self.selected_department_filter = selected
            logging.info(f"Kalendarda filtr dəyişdi: {self.selected_department_filter}")
            self.load_data()  # Məlumatları yenidən yüklə


    def update_calendar(self):
        """Təqvim yeniləməsi - OPTİMALLAŞDIRILMIŞ VERSİYA"""
        import logging
        import time
        start_time = time.time()
        
        # calendar_frame yaradılıbmışdırsa davam et
        if not hasattr(self, 'calendar_frame') or not self.calendar_frame.winfo_exists():
            logging.warning("calendar_frame hələ yaradılmayıb, update_calendar atlanılır")
            return
        
        # OPTİMALLAŞDIRMA: vacations atributu hələ yaradılmayıbsa, gözlə
        if not hasattr(self, 'vacations'):
            logging.debug(f"=== update_calendar: vacations hələ yüklənməyib, gözləyirəm... ===")
            return
        
        # OPTİMALLAŞDIRMA: Yalnız vacib loglar
        logging.debug(f"=== update_calendar başladı: {self.current_date.month}/{self.current_date.year}, {len(self.vacations)} məzuniyyət ===")
        
        for widget in self.calendar_frame.winfo_children(): widget.destroy()
        month_names_az = ["Yanvar", "Fevral", "Mart", "Aprel", "May", "İyun", "İyul", "Avqust", "Sentyabr", "Oktyabr", "Noyabr", "Dekabr"]
        self.month_year_label.config(text=f"{month_names_az[self.current_date.month - 1]} {self.current_date.year}")
        days_of_week = ["B.e.", "Ç.a.", "Çər.", "C.a.", "Cüm.", "Şən.", "Baz."]
        for i, day in enumerate(days_of_week):
            self.calendar_frame.grid_columnconfigure(i, weight=1)
            ttk.Label(self.calendar_frame, text=day, font=(self.main_font, 10, "bold"), anchor='center', relief='groove', padding=5).grid(row=0, column=i, sticky='nsew', pady=5)
        for i in range(1, 8):
            self.calendar_frame.grid_rowconfigure(i, weight=1, uniform="week_row")
        month_calendar = calendar.monthcalendar(self.current_date.year, self.current_date.month)
        today = date.today()
        
        # OPTİMALLAŞDIRMA: Bütün günləri bir dəfəyə hesabla - batch processing
        # Bütün günləri və onların məzuniyyətlərini bir dəfəyə hesabla
        vacations_by_day = {}
        for week in month_calendar:
            for day_val in week:
                if day_val == 0:
                    continue
                day_date = date(self.current_date.year, self.current_date.month, day_val)
                # Bütün məzuniyyətləri bir dəfəyə filter et
                vacations_on_this_day = [
                    v for v in self.vacations 
                    if v.get('start_date') and v.get('end_date') 
                    and v['start_date'] <= day_date <= v['end_date']
                ]
                vacations_by_day[day_date] = vacations_on_this_day
        # OPTİMALLAŞDIRMA: Bütün günləri bir dəfəyə render et - batch processing
        for week_num, week in enumerate(month_calendar, 1):
            for day_num_idx, day_val in enumerate(week):
                if day_val == 0: 
                    continue
                day_date = date(self.current_date.year, self.current_date.month, day_val)
                
                # OPTİMALLAŞDIRMA: Vacations artıq hesablanıb - cache-dən götür
                vacations_on_this_day = vacations_by_day.get(day_date, [])
                
                frame_config = {'relief': 'solid', 'borderwidth': 1}
                is_weekend = day_num_idx >= 5
                is_today = (day_date == today)
                if is_today:
                    frame_config['bg'] = '#e8f0fe'
                    frame_config['highlightbackground'] = '#007bff'
                    frame_config['highlightthickness'] = 2
                elif is_weekend:
                    frame_config['bg'] = '#f5f5f5'
                else:
                    frame_config['bg'] = 'white'
                day_frame = tk.Frame(self.calendar_frame, **frame_config)
                day_frame.vacation_date = day_date
                try:
                    day_frame.grid(row=week_num, column=day_num_idx, sticky='nsew')
                    day_frame.grid_propagate(False)
                    day_frame.configure(width=100, height=80)
                    self.calendar_frame.grid_columnconfigure(day_num_idx, weight=1)
                    self.calendar_frame.grid_rowconfigure(week_num, weight=1)
                except tk.TclError as e:
                    logging.debug(f"Day frame yaradılma xətası: {e}")
                    continue
                day_label = tk.Label(day_frame, text=str(day_val), font=(self.main_font, 9), anchor='ne', padx=4, pady=1)
                try:
                    day_label.place(relx=1.0, rely=0.0, anchor='ne')
                except tk.TclError as e:
                    logging.debug(f"Day label yerləşdirmə xətası: {e}")
                
                # OPTİMALLAŞDIRMA: Log mesajlarını azalt - yalnız vacib məlumatları logla
                if not vacations_on_this_day:
                    day_label.config(bg=frame_config['bg'])
                else:
                    # Kvadratlar üçün grid ölçüsünü təyin edirik
                    num_vac = len(vacations_on_this_day)
                    grid_size = 1
                    if num_vac > 6:
                        grid_size = 3
                    elif num_vac > 2:
                        grid_size = 2
                    
                    # Kvadratları yerləşdiririk
                    for i, vac in enumerate(vacations_on_this_day):
                        # OPTİMALLAŞDIRMA: Rəng hesablaması - log yoxdur
                        if day_date > vac['end_date']:
                            color = self.status_colors['red']  # Bitmiş
                        elif vac['start_date'] <= day_date <= vac['end_date']:
                            color = self.employee_colors.get(vac['employee'], self.status_colors['gray'])  # Aktiv
                        else:
                            color = self.status_colors['gray']  # Planlaşdırılan
                        
                        # Grid pozisiyasını hesablayırıq
                        row = i // grid_size
                        col = i % grid_size
                        
                        indicator = tk.Frame(day_frame, background=color, width=12, height=12, relief='ridge', borderwidth=1)
                        try:
                            indicator.grid(row=row, column=col, padx=1, pady=1, sticky='nsew')
                            indicator.configure(background=color)
                            day_frame.grid_columnconfigure(col, weight=1)
                            day_frame.grid_rowconfigure(row, weight=1)
                        except tk.TclError as e:
                            logging.debug(f"Widget yaradılma xətası: {e}")
                            continue
                        
                        # OPTİMALLAŞDIRMA: Rəng yoxlaması - yalnız xəta halında log
                        try:
                            actual_color = indicator.cget('background')
                            if actual_color != color:
                                indicator.configure(background=color)
                        except tk.TclError:
                            pass
                        
                        # OPTİMALLAŞDIRMA: Görünürlük yoxlaması - log yoxdur
                        try:
                            indicator.lift()
                        except tk.TclError:
                            pass
                        # Tooltip
                        tooltip_text = f"{vac['employee']}\n{vac['start_date'].strftime('%d.%m.%Y')} - {vac['end_date'].strftime('%d.%m.%Y')}"
                        try:
                            Tooltip(indicator, tooltip_text, font_name=self.main_font)
                        except Exception:
                            pass
                        handler = lambda e, v=vac: self.on_day_click(v)
                        try:
                            indicator.bind("<Button-1>", handler)
                        except tk.TclError:
                            pass
                    try:
                        day_label.lift()
                    except tk.TclError:
                        pass
        
        # OPTİMALLAŞDIRMA: Performans ölçməsi
        elapsed_time = time.time() - start_time
        logging.debug(f"=== update_calendar tamamlandı: {elapsed_time:.3f}s ===")

    def on_day_click(self, vacation_info):
        """Günə klik edildikdə məzuniyyət məlumatlarını göstərir"""
        try:
            import logging
            logging.info(f"on_day_click çağırıldı: {vacation_info}")
            
            employee_id = vacation_info.get('employee_id')
            employee_name = vacation_info.get('employee', '')
            
            if not employee_id:
                logging.warning("Employee ID tapılmadı")
                return
            
            # Admin üçün bütün işçilərin məzuniyyətlərini göstər
            if self.is_admin:
                logging.info(f"Admin {employee_name} məzuniyyətini açır")
                self.main_app_ref.show_employee_by_id(employee_id)
                return
            
            # Adi istifadəçi üçün yalnız öz məzuniyyətini göstər
            current_user_name = self.current_user.get('name', '')
            if employee_name == current_user_name:
                logging.info(f"İstifadəçi öz məzuniyyətini açır: {employee_name}")
                # Öz məzuniyyət pəncərəsinə apar
                self.main_app_ref.open_my_queries_window()
            else:
                logging.warning(f"İstifadəçi başqa işçinin məzuniyyətini görə bilməz: {employee_name}")
                messagebox.showwarning(
                    "İcazə Yoxdur",
                    f"Yalnız öz məzuniyyətlərinizi görə bilərsiniz.\n"
                    f"'{employee_name}' məzuniyyətini görə bilməzsiniz."
                )
                
        except Exception as e:
            import logging
            logging.error(f"on_day_click xətası: {e}")
            import traceback
            logging.error(f"Traceback: {traceback.format_exc()}")

    def change_month(self, month_delta):
        # ... (Bu funksiyada dəyişiklik yoxdur)
        current_year, current_month = self.current_date.year, self.current_date.month
        new_month = current_month + month_delta
        new_year = current_year
        if new_month > 12:
            new_month = 1
            new_year += 1
        elif new_month < 1:
            new_month = 12
            new_year -= 1
        self.current_date = self.current_date.replace(year=new_year, month=new_month, day=1)
        self.update_calendar()

    def _is_dark_color(self, hex_color):
        """Rəngin tünd olub-olmadığını müəyyən edir (mətn rəngini seçmək üçün)"""
        try:
            # Hex rəngdən RGB-yə çevir
            hex_color = hex_color.lstrip('#')
            r = int(hex_color[0:2], 16)
            g = int(hex_color[2:4], 16)
            b = int(hex_color[4:6], 16)
            # Luminance hesabla
            luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255
            return luminance < 0.5
        except:
            return False

    def get_status_color_legend(self):
        """Status rəng əfsanəsini qaytarır"""
        return [
            {"status": "Bitmiş", "color": self.status_colors["red"], "description": "Artıq başa çatan məzuniyyətlər"},
            {"status": "Davam edən", "color": self.status_colors["green"], "description": "Hazırda davam edən məzuniyyətlər"},  
            {"status": "Planlaşdırılan", "color": self.status_colors["#007bff"], "description": "Gələcəkdə planlaşdırılan məzuniyyətlər"},
            {"status": "Gözləyir", "color": self.status_colors["#E49B0F"], "description": "Təsdiq gözləyən sorğular"},
            {"status": "Rədd edilib", "color": self.status_colors["gray"], "description": "Rədd edilmiş sorğular"}
        ]

    def get_employee_color_legend(self):
        """İşçilərin rəng əfsanəsini qaytarır (tooltip üçün)"""
        legend = []
        for employee, color in self.employee_colors.items():
            legend.append({"employee": employee, "color": color})
        return legend

    def highlight_vacation(self, vacation):
        """Verilmiş məzuniyyəti kalendarda işarələyir"""
        try:
            import logging
            print(f"DEBUG: highlight_vacation started - vacation: {vacation}")
            logging.info(f"highlight_vacation çağırıldı: {vacation}")
            
            # Məzuniyyətin başlama və bitmə tarixlərini al
            start_date = vacation.get('baslama') or vacation.get('start_date')
            end_date = vacation.get('bitme') or vacation.get('end_date')
            
            print(f"DEBUG: Start date: {start_date}, End date: {end_date}")
            
            if not start_date or not end_date:
                print("DEBUG: Vacation dates not found")
                logging.warning("Məzuniyyət tarixləri tapılmadı")
                return
            
            # Tarixləri date obyektinə çevir
            if isinstance(start_date, str):
                start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
            if isinstance(end_date, str):
                end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
            
            print(f"DEBUG: Vacation dates parsed: {start_date} - {end_date}")
            logging.info(f"Məzuniyyət tarixləri: {start_date} - {end_date}")
            
            # Məzuniyyətin başlama ayına keç
            target_month = start_date.replace(day=1)
            current_month = self.current_date.replace(day=1)
            
            print(f"DEBUG: Current month: {current_month}, Target month: {target_month}")
            
            if current_month != target_month:
                # Aya keç
                month_diff = (target_month.year - self.current_date.year) * 12 + (target_month.month - self.current_date.month)
                print(f"🔄 DEBUG: Aya keç: {month_diff} ay fərqi")
                logging.info(f"Aya keç: {month_diff} ay fərqi")
                self.change_month(month_diff)
                
                # Kalendar yeniləndikdən sonra günləri işarələ
                print("⏳ DEBUG: Kalendar yeniləndikdən sonra günləri işarələ (500ms gecikmə)")
                self.after(500, lambda: self._highlight_vacation_days(start_date, end_date, vacation))
            else:
                # Eyni aydadırsa, dərhal işarələ
                print("⏳ DEBUG: Eyni aydadır, dərhal işarələ (200ms gecikmə)")
                self.after(200, lambda: self._highlight_vacation_days(start_date, end_date, vacation))
            
        except Exception as e:
            print(f"❌ DEBUG: highlight_vacation xətası: {e}")
            import logging
            logging.error(f"highlight_vacation xətası: {e}")
            import traceback
            logging.error(f"Traceback: {traceback.format_exc()}")

    def _highlight_vacation_days(self, start_date, end_date, vacation):
        """Məzuniyyət günlərini kalendarda işarələyir"""
        try:
            import logging
            print(f"🔍 DEBUG: _highlight_vacation_days başladı: {start_date} - {end_date}")
            logging.info(f"_highlight_vacation_days: {start_date} - {end_date}")
            
            # Məzuniyyət günlərini tap və işarələ
            current_date = start_date
            highlighted_days = []
            found_days = 0
            
            print(f"🔍 DEBUG: Günlər axtarılır: {start_date} - {end_date}")
            
            while current_date <= end_date:
                print(f"🔍 DEBUG: Gün axtarılır: {current_date}")
                # Günün grid pozisiyasını tap
                day_widget = self._find_day_widget(current_date)
                if day_widget:
                    # Günü işarələ (qırmızı border)
                    day_widget.configure(relief='solid', borderwidth=3, highlightbackground='red', highlightthickness=2)
                    highlighted_days.append((day_widget, current_date))
                    found_days += 1
                    print(f"✅ DEBUG: Gün işarələndi: {current_date}")
                    logging.info(f"Gün işarələndi: {current_date}")
                else:
                    print(f"❌ DEBUG: Gün widget tapılmadı: {current_date}")
                
                current_date += timedelta(days=1)
            
            print(f"📊 DEBUG: Cəmi {found_days} gün işarələndi")
            
            # İşçi adını göstər
            employee_name = vacation.get('employee_name') or vacation.get('employee', 'Naməlum')
            print(f"✅ DEBUG: Məzuniyyət işarələndi: {employee_name}")
            
            messagebox.showinfo(
                "Məzuniyyət Tapıldı",
                f"'{employee_name}' məzuniyyəti kalendarda işarələndi:\n"
                f"Başlama: {safe_date_format(start_date)}\n"
                f"Bitmə: {safe_date_format(end_date)}\n\n"
                "Qırmızı border ilə işarələnmiş günlərə baxın."
            )
            
            # 5 saniyədən sonra işarələri təmizlə
            print("⏳ DEBUG: 5 saniyədən sonra işarələr təmizlənəcək")
            self.after(5000, lambda: self._clear_highlights(highlighted_days))
            
        except Exception as e:
            print(f"❌ DEBUG: _highlight_vacation_days xətası: {e}")
            import logging
            logging.error(f"_highlight_vacation_days xətası: {e}")

    def _find_day_widget(self, target_date):
        """Verilmiş tarixə uyğun gün widget-ini tapır"""
        try:
            import logging
            print(f"🔍 DEBUG: _find_day_widget axtarılır: {target_date}")
            logging.debug(f"_find_day_widget axtarılır: {target_date}")
            
            # Kalendar frame-lərini yoxla
            print(f"🔍 DEBUG: Self winfo_children sayı: {len(self.winfo_children())}")
            for i, child in enumerate(self.winfo_children()):
                print(f"🔍 DEBUG: Child {i}: {type(child)} - {child}")
                if isinstance(child, ttk.Notebook):
                    print(f"🔍 DEBUG: Notebook tapıldı, tab-lar yoxlanılır...")
                    for tab_id in child.tabs():
                        tab = child.nametowidget(tab_id)
                        print(f"🔍 DEBUG: Tab: {tab} - {type(tab)}")
                        if "calendar" in str(tab).lower():
                            print(f"🔍 DEBUG: Calendar tab tapıldı, gün widget-ləri axtarılır...")
                            # Calendar tab-də gün widget-lərini yoxla
                            for day_widget in tab.winfo_children():
                                if hasattr(day_widget, 'vacation_date'):
                                    if day_widget.vacation_date == target_date:
                                        print(f"✅ DEBUG: Gün widget tapıldı: {target_date}")
                                        logging.debug(f"Gün widget tapıldı: {target_date}")
                                        return day_widget
                            
                            # Əgər vacation_date atributu ilə tapılmadısa, bütün frame-ləri yoxla
                            for frame in tab.winfo_children():
                                if isinstance(frame, tk.Frame):
                                    print(f"🔍 DEBUG: Frame tapıldı, uşaqlar yoxlanılır...")
                                    for day_widget in frame.winfo_children():
                                        if hasattr(day_widget, 'vacation_date'):
                                            if day_widget.vacation_date == target_date:
                                                print(f"✅ DEBUG: Gün widget tapıldı (frame içində): {target_date}")
                                                logging.debug(f"Gün widget tapıldı (frame içində): {target_date}")
                                                return day_widget
                                        
                                        # Əgər day_widget-in özü frame-dirsə, onun uşaqlarını da yoxla
                                        if isinstance(day_widget, tk.Frame):
                                            for sub_widget in day_widget.winfo_children():
                                                if hasattr(sub_widget, 'vacation_date'):
                                                    if sub_widget.vacation_date == target_date:
                                                        print(f"✅ DEBUG: Gün widget tapıldı (sub-frame içində): {target_date}")
                                                        logging.debug(f"Gün widget tapıldı (sub-frame içində): {target_date}")
                                                        return sub_widget
            
            # Əgər hələ də tapılmadısa, bütün widget-ləri recursive olaraq yoxla
            print(f"🔍 DEBUG: Recursive axtarış başladılır...")
            def search_recursive(widget):
                if hasattr(widget, 'vacation_date') and widget.vacation_date == target_date:
                    print(f"✅ DEBUG: Gün widget tapıldı (recursive): {target_date}")
                    logging.debug(f"Gün widget tapıldı (recursive): {target_date}")
                    return widget
                
                for child in widget.winfo_children():
                    result = search_recursive(child)
                    if result:
                        return result
                return None
            
            for child in self.winfo_children():
                result = search_recursive(child)
                if result:
                    return result
            
            print(f"❌ DEBUG: Gün widget tapılmadı: {target_date}")
            logging.warning(f"Gün widget tapılmadı: {target_date}")
            return None
        except Exception as e:
            print(f"❌ DEBUG: _find_day_widget xətası: {e}")
            import logging
            logging.error(f"_find_day_widget xətası: {e}")
            return None

    def _clear_highlights(self, highlighted_days):
        """İşarələnmiş günlərin işarələrini təmizləyir"""
        try:
            for day_widget, date in highlighted_days:
                if day_widget.winfo_exists():
                    # Normal görünüşə qaytar
                    day_widget.configure(relief='solid', borderwidth=1, highlightbackground='', highlightthickness=0)
        except Exception as e:
            import logging
            logging.error(f"_clear_highlights xətası: {e}")