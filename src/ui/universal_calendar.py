import tkinter as tk
from tkinter import ttk
from datetime import datetime, date
import calendar
import time
import logging

# Debug üçün logging konfiqurasiyası
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class CalendarWidget(tk.Toplevel):
    """Səliqəli kalendar widget-i"""
    
    def __init__(self, parent, current_date=None, callback=None):
        logger.debug("🔵 CalendarWidget __init__ başlayır")
        logger.debug(f"🔵 Parent widget: {parent}")
        logger.debug(f"🔵 Parent class: {type(parent).__name__}")
        
        super().__init__(parent)
        self.parent = parent
        self.current_date = current_date or date.today()
        self.callback = callback
        self.selected_date = None
        
        self.month_names = [
            "Yanvar", "Fevral", "Mart", "Aprel", "May", "İyun",
            "İyul", "Avqust", "Sentyabr", "Oktyabr", "Noyabr", "Dekabr"
        ]
        
        logger.debug("🔵 setup_window çağırılır")
        self.setup_window()
        
        logger.debug("🔵 _build_styles çağırılır")
        self._build_styles()
        
        logger.debug("🔵 _build_ui çağırılır")
        self._build_ui()
        
        logger.debug("🔵 _update_calendar çağırılır")
        self._update_calendar()
        
        logger.debug("🔵 CalendarWidget __init__ tamamlandı")
        
    def setup_window(self):
        self.title("Tarix Seçin")
        self.resizable(False, False)
        self.transient(self.parent)
        self.grab_set()
        self.configure(bg="white")
        
    def _build_styles(self):
        # Style konfiqurasiyasını tamamilə silirik
        # Bunun əvəzinə sadə tk widget-lərdən istifadə edəcəyik
        logger.debug("🔵 _build_styles başlayır - Style konfiqurasiyası silinir")
        self.calendar_style = None
        logger.debug("🔵 _build_styles tamamlandı - Style konfiqurasiyası silindi")

    def _build_ui(self):
        self.main_frame = tk.Frame(self, bg="white", padx=10, pady=10)
        self.main_frame.pack(fill='both', expand=True)
        
        # Ay və il seçimi bir sətirdə
        nav_row = tk.Frame(self.main_frame, bg="white")
        nav_row.pack(fill='x', pady=(0, 8))
        
        # İl
        tk.Button(nav_row, text="<", bg="lightgray", fg="black", font=("Segoe UI", 10, "bold"), 
                 width=2, relief="flat", command=lambda: self._change_year(-1)).pack(side='left')
        self.year_btn = tk.Button(nav_row, text=str(self.current_date.year), 
                                 bg="lightgray", fg="black", font=("Segoe UI", 10, "bold"),
                                 relief="flat", command=self._show_year_popup)
        self.year_btn.pack(side='left', padx=(2, 8))
        tk.Button(nav_row, text=">", bg="lightgray", fg="black", font=("Segoe UI", 10, "bold"), 
                 width=2, relief="flat", command=lambda: self._change_year(1)).pack(side='left')
        
        # Ay
        tk.Button(nav_row, text="<", bg="lightgray", fg="black", font=("Segoe UI", 10, "bold"), 
                 width=2, relief="flat", command=lambda: self._change_month(-1)).pack(side='left', padx=(16,0))
        self.month_btn = tk.Button(nav_row, text=self.month_names[self.current_date.month-1], 
                                  bg="lightgray", fg="black", font=("Segoe UI", 10, "bold"),
                                  relief="flat", command=self._show_month_popup)
        self.month_btn.pack(side='left', padx=(2, 8))
        tk.Button(nav_row, text=">", bg="lightgray", fg="black", font=("Segoe UI", 10, "bold"), 
                 width=2, relief="flat", command=lambda: self._change_month(1)).pack(side='left')
        
        # Həftə günləri
        week_frame = tk.Frame(self.main_frame, bg="white")
        week_frame.pack(fill='x')
        weekdays = ['B.e', 'Ç.a', 'Çər', 'C.a', 'Cüm', 'Şən', 'Baz']
        for i, day in enumerate(weekdays):
            bg_color = "lightgray" if i < 5 else "lightblue"
            fg_color = "black"
            lbl = tk.Label(week_frame, text=day, bg=bg_color, fg=fg_color, 
                          font=("Segoe UI", 10, "bold"), width=4, anchor='center')
            lbl.grid(row=0, column=i, padx=2, pady=1, sticky='nsew')
            week_frame.grid_columnconfigure(i, weight=1)
        
        # Günlər
        self.days_frame = tk.Frame(self.main_frame, bg="white")
        self.days_frame.pack()

    def _update_calendar(self):
        for widget in self.days_frame.winfo_children():
            widget.destroy()
        
        year = self.current_date.year
        month = self.current_date.month
        today = date.today()
        cal = calendar.monthcalendar(year, month)
        
        for r, week in enumerate(cal):
            for c, day in enumerate(week):
                if day == 0:
                    tk.Label(self.days_frame, text="", bg="white", width=4).grid(row=r, column=c, padx=2, pady=1, sticky='nsew')
                else:
                    # Rəng seçimi
                    if year == today.year and month == today.month and day == today.day:
                        bg_color = "blue"  # Bu gün - mavi
                        fg_color = "white"
                        font_weight = "bold"
                    elif day == self.current_date.day:
                        bg_color = "lightgreen"  # Seçilmiş gün - yaşıl
                        fg_color = "black"
                        font_weight = "bold"
                    elif c >= 5:
                        bg_color = "lightblue"  # Həftə sonu - açıq yaşıl
                        fg_color = "black"
                        font_weight = "bold"
                    else:
                        bg_color = "white"  # Normal gün - ağ
                        fg_color = "black"
                        font_weight = "normal"
                    
                    btn = tk.Button(self.days_frame, text=str(day), bg=bg_color, fg=fg_color,
                                   font=("Arial", 10, font_weight), width=4, relief="flat",
                                   command=lambda d=day: self._select_day(d))
                    btn.grid(row=r, column=c, padx=2, pady=1, sticky='nsew')
                    self.days_frame.grid_columnconfigure(c, weight=1)

    def _change_month(self, delta):
        m = self.current_date.month + delta
        y = self.current_date.year
        if m < 1:
            m = 12
            y -= 1
        elif m > 12:
            m = 1
            y += 1
        d = min(self.current_date.day, calendar.monthrange(y, m)[1])
        self.current_date = self.current_date.replace(year=y, month=m, day=d)
        self.month_btn.config(text=self.month_names[m-1])
        self.year_btn.config(text=str(y))
        self._update_calendar()

    def _change_year(self, delta):
        y = self.current_date.year + delta
        m = self.current_date.month
        d = min(self.current_date.day, calendar.monthrange(y, m)[1])
        self.current_date = self.current_date.replace(year=y, day=d)
        self.year_btn.config(text=str(y))
        self._update_calendar()

    def _show_year_popup(self):
        if hasattr(self, '_month_overlay') and self._month_overlay:
            self._month_overlay.destroy()
        if hasattr(self, '_year_overlay') and self._year_overlay and self._year_overlay.winfo_exists():
            self._year_overlay.destroy()
            self._year_overlay = None
            return
        self._year_overlay = tk.Frame(self.main_frame, bg="#fff", bd=1, relief="solid")
        btn_x = self.year_btn.winfo_x()
        btn_y = self.year_btn.winfo_y() + self.year_btn.winfo_height()
        self._year_overlay.place(x=btn_x, y=btn_y)
        overlay_width = 90
        canvas = tk.Canvas(self._year_overlay, bg="#fff", height=180, width=overlay_width, highlightthickness=0, bd=0)
        canvas.pack(side="left", fill="y", expand=True, padx=0, pady=6)
        frame = tk.Frame(canvas, bg="#fff", width=overlay_width)
        canvas.create_window((0, 0), window=frame, anchor="n", width=overlay_width)
        def on_frame_configure(event):
            canvas.configure(scrollregion=canvas.bbox("all"))
            frame.update_idletasks()
        frame.bind("<Configure>", on_frame_configure)
        y0 = self.current_date.year - 6
        for i in range(18):
            y = y0 + i
            fg = "#222"
            bg = "#e2f0cb" if y == self.current_date.year else "#fff"
            lbl = tk.Label(frame, text=str(y), width=10, height=1, font=("Arial", 11), fg=fg, bg=bg, anchor="center", cursor="hand2", padx=0, pady=2)
            lbl.grid(row=i, column=0, padx=0, pady=0, sticky="ew")
            lbl.bind("<Button-1>", lambda e, yy=y: self._select_year_overlay(yy))
        frame.grid_rowconfigure(tuple(range(18)), weight=1)
        frame.grid_columnconfigure(0, weight=1)
        # Mouse wheel vertical scroll
        def on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        canvas.bind_all('<MouseWheel>', on_mousewheel)

    def _show_month_popup(self):
        if hasattr(self, '_year_overlay') and self._year_overlay:
            self._year_overlay.destroy()
        if hasattr(self, '_month_overlay') and self._month_overlay and self._month_overlay.winfo_exists():
            self._month_overlay.destroy()
            self._month_overlay = None
            return
        self._month_overlay = tk.Frame(self.main_frame, bg="#fff", bd=1, relief="solid")
        btn_x = self.month_btn.winfo_x()
        btn_y = self.month_btn.winfo_y() + self.month_btn.winfo_height()
        self._month_overlay.place(x=btn_x, y=btn_y)
        overlay_width = 90
        canvas = tk.Canvas(self._month_overlay, bg="#fff", height=180, width=overlay_width, highlightthickness=0, bd=0)
        canvas.pack(side="left", fill="y", expand=True, padx=0, pady=6)
        frame = tk.Frame(canvas, bg="#fff", width=overlay_width)
        canvas.create_window((0, 0), window=frame, anchor="n", width=overlay_width)
        def on_frame_configure(event):
            canvas.configure(scrollregion=canvas.bbox("all"))
            frame.update_idletasks()
        frame.bind("<Configure>", on_frame_configure)
        months = self.month_names
        for i, name in enumerate(months):
            bg = "#e2f0cb" if i+1 == self.current_date.month else "#fff"
            lbl = tk.Label(frame, text=name, width=10, height=1, font=("Arial", 11), fg="#222", bg=bg, anchor="center", cursor="hand2", padx=0, pady=2)
            lbl.grid(row=i, column=0, padx=0, pady=0, sticky="ew")
            lbl.bind("<Button-1>", lambda e, idx=i: self._select_month_overlay(idx))
        frame.grid_rowconfigure(tuple(range(12)), weight=1)
        frame.grid_columnconfigure(0, weight=1)
        # Mouse wheel vertical scroll
        def on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        canvas.bind_all('<MouseWheel>', on_mousewheel)

    def _select_month_overlay(self, idx):
        m = idx + 1
        y = self.current_date.year
        d = min(self.current_date.day, calendar.monthrange(y, m)[1])
        self.current_date = self.current_date.replace(month=m, day=d)
        self.month_btn.config(text=self.month_names[idx])
        self._update_calendar()
        if hasattr(self, '_month_overlay') and self._month_overlay:
            self._month_overlay.destroy()

    def _select_year_overlay(self, y):
        m = self.current_date.month
        d = min(self.current_date.day, calendar.monthrange(y, m)[1])
        self.current_date = self.current_date.replace(year=y, day=d)
        self.year_btn.config(text=str(y))
        self._update_calendar()
        if hasattr(self, '_year_overlay') and self._year_overlay:
            self._year_overlay.destroy()

    def _select_day(self, day):
        self.current_date = self.current_date.replace(day=day)
        if self.callback:
            self.callback(self.current_date.strftime("%Y-%m-%d"))
        self.destroy()
    
    def destroy(self):
        """Pəncərəni bağlayır"""
        logger.debug("🔵 CalendarWidget destroy başlayır")
        logger.debug("🔵 Kalendar pəncərəsi bağlanır")
        super().destroy()
        logger.debug("🔵 CalendarWidget destroy tamamlandı")


class DateEntry(tk.Frame):
    """Tarix daxil etmə sahəsi kalendar ilə"""
    
    def __init__(self, parent, variable, **kwargs):
        super().__init__(parent, **kwargs)
        self.variable = variable
        self.calendar_window = None
        
        # Entry və kalendar düyməsi
        self.entry = tk.Entry(self, textvariable=variable, font=('Arial', 12), 
                             relief="solid", bd=1, width=15)
        self.entry.pack(side="left", fill="x", expand=True)
        
        self.calendar_button = tk.Button(self, text="📅", command=self.open_calendar,
                                        bg='#3498db', fg='white', font=('Arial', 10),
                                        relief="flat", width=3)
        self.calendar_button.pack(side="right", padx=(5, 0))
        
        # Entry-yə klik edildikdə kalendar açılsın
        self.entry.bind("<Button-1>", self.on_entry_click)
        self.entry.bind("<Double-1>", self.open_calendar)
        
        # Avtomatik tarix formatlaması üçün Enter və FocusOut event-ləri
        self.entry.bind("<Return>", self.on_enter_pressed)
        self.entry.bind("<FocusOut>", self.on_focus_out)
        self.entry.bind("<KeyRelease>", self.on_key_release)
        
    def on_entry_click(self, event):
        """Entry-yə klik edildikdə"""
        # İkiqat klik yoxlayırıq
        current_time = time.time()
        if hasattr(self, '_last_click_time'):
            if current_time - self._last_click_time < 0.3:
                self.open_calendar()
        self._last_click_time = current_time
        
    def open_calendar(self, event=None):
        """Kalendarı açır"""
        logger.debug("🔵 DateEntry open_calendar başlayır")
        logger.debug(f"🔵 Mövcud calendar_window: {self.calendar_window}")
        
        if self.calendar_window and self.calendar_window.winfo_exists():
            logger.debug("🔵 Kalendar pəncərəsi artıq mövcuddur, çıxılır")
            return
            
        # Mövcud tarixi parse et
        current_date = date.today()
        if self.variable.get():
            try:
                current_date = datetime.strptime(self.variable.get(), '%Y-%m-%d').date()
                logger.debug(f"🔵 Parse edilmiş tarix: {current_date}")
            except ValueError:
                logger.debug("🔵 Tarix parse edilə bilmədi, bugünkü tarix istifadə edilir")
                pass
        else:
            logger.debug("🔵 Dəyişən boşdur, bugünkü tarix istifadə edilir")
                
        logger.debug(f"🔵 CalendarWidget yaradılır, tarix: {current_date}")
        self.calendar_window = CalendarWidget(self, current_date, self.on_date_selected)
        
        # Kalendarı düzgün yerləşdir - entry-nin altında
        self.calendar_window.update_idletasks()
        ex = self.entry.winfo_rootx()
        ey = self.entry.winfo_rooty() + self.entry.winfo_height() + 2
        self.calendar_window.geometry(f"+{ex}+{ey}")
        logger.debug(f"🔵 Kalendar yerləşdirildi: x={ex}, y={ey}")
        logger.debug("🔵 DateEntry open_calendar tamamlandı")
        
    def on_date_selected(self, date_str):
        """Tarix seçildikdə"""
        logger.debug(f"🔵 Tarix seçildi: {date_str}")
        self.variable.set(date_str)
        self.calendar_window = None
        logger.debug("🔵 calendar_window None-a təyin edildi")
        logger.debug("🔵 on_date_selected tamamlandı")
    
    def on_enter_pressed(self, event):
        """Enter düyməsi basıldıqda avtomatik tarix formatlaması"""
        self.format_date_input()
        return "break"  # Event-i dayandır
    
    def on_focus_out(self, event):
        """Focus çıxdıqda avtomatik tarix formatlaması"""
        self.format_date_input()
    
    def on_key_release(self, event):
        """Açar buraxıldıqda real-time formatlaması"""
        # Sadəcə rəqəm və nöqtə daxil etməyə icazə ver
        if event.char and event.char not in '0123456789.':
            return
    
    def set_date(self, date_value):
        """Tarix dəyərini təyin edir"""
        try:
            if isinstance(date_value, date):
                formatted_date = date_value.strftime('%Y-%m-%d')
                self.variable.set(formatted_date)
                logger.debug(f"🔵 Tarix təyin edildi: {formatted_date}")
            elif isinstance(date_value, str):
                # String formatını yoxla və düzəlt
                if len(date_value) == 10 and '-' in date_value:
                    self.variable.set(date_value)
                    logger.debug(f"🔵 String tarix təyin edildi: {date_value}")
                else:
                    # Avtomatik formatla
                    formatted_date = self._auto_format_date(date_value)
                    if formatted_date:
                        self.variable.set(formatted_date)
                        logger.debug(f"🔵 String tarix formatlandı: {date_value} -> {formatted_date}")
            else:
                logger.debug(f"🔵 Naməlum tarix tipi: {type(date_value)}")
        except Exception as e:
            logger.debug(f"🔵 set_date xətası: {e}")
    
    def get_date(self):
        """Tarix dəyərini qaytarır"""
        try:
            date_str = self.variable.get()
            logging.debug(f"🔵 DateEntry.get_date() çağırıldı - date_str: '{date_str}'")
            if date_str:
                result = datetime.strptime(date_str, '%Y-%m-%d').date()
                logging.debug(f"🔵 DateEntry.get_date() - parse uğurlu: {result}")
                return result
            logging.debug("🔵 DateEntry.get_date() - boş string, None qaytarılır")
            return None
        except ValueError as e:
            logging.debug(f"🔵 DateEntry.get_date() - parse xətası: {e}")
            return None
    
    def format_date_input(self):
        """Daxil edilən mətnə görə tarixi avtomatik formatla"""
        try:
            input_text = self.variable.get().strip()
            if not input_text:
                return
            
            # Mövcud formatları yoxla
            if self._is_valid_date_format(input_text):
                return
            
            # Avtomatik formatlaması
            formatted_date = self._auto_format_date(input_text)
            if formatted_date:
                self.variable.set(formatted_date)
                logger.debug(f"🔵 Tarix avtomatik formatlandı: {input_text} -> {formatted_date}")
                
        except Exception as e:
            logger.error(f"🔴 Tarix formatlaması xətası: {e}")
    
    def _is_valid_date_format(self, date_str):
        """Tarix formatının düzgün olub-olmadığını yoxlayır"""
        try:
            # YYYY-MM-DD formatını yoxla
            datetime.strptime(date_str, '%Y-%m-%d')
            return True
        except ValueError:
            return False
    
    def _auto_format_date(self, input_text):
        """Daxil edilən mətnə görə tarixi avtomatik formatla"""
        try:
            # Rəqəmləri və nöqtələri təmizlə
            cleaned = ''.join(c for c in input_text if c.isdigit() or c == '.')
            parts = cleaned.split('.')
            
            current_year = datetime.now().year
            current_month = datetime.now().month
            
            if len(parts) == 1 and len(parts[0]) <= 2:
                # Sadəcə gün daxil edilib (məsələn: "05")
                day = int(parts[0])
                if 1 <= day <= 31:
                    return f"{current_year}-{current_month:02d}-{day:02d}"
                    
            elif len(parts) == 2:
                # Gün və ay daxil edilib (məsələn: "05.07")
                if len(parts[0]) <= 2 and len(parts[1]) <= 2:
                    day = int(parts[0])
                    month = int(parts[1])
                    if 1 <= day <= 31 and 1 <= month <= 12:
                        return f"{current_year}-{month:02d}-{day:02d}"
                        
            elif len(parts) == 3:
                # Gün, ay və il daxil edilib (məsələn: "05.07.1993")
                if len(parts[0]) <= 2 and len(parts[1]) <= 2 and len(parts[2]) <= 4:
                    day = int(parts[0])
                    month = int(parts[1])
                    year = int(parts[2])
                    
                    # İl 2 rəqəmlidirsə, 2000+ əlavə et
                    if len(parts[2]) == 2:
                        year = 2000 + year
                    
                    if 1 <= day <= 31 and 1 <= month <= 12 and 1900 <= year <= 2100:
                        return f"{year}-{month:02d}-{day:02d}"
            
            return None
            
        except (ValueError, IndexError):
            return None 