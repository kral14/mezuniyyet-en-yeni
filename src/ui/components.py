# ui_components.py (Yekun Düzəliş Edilmiş Versiya)

import tkinter as tk
from tkinter import ttk, Toplevel
from datetime import datetime, date, timedelta
import calendar
import logging

def safe_date_format(date_value, format_str='%d.%m.%Y'):
    """Tarix dəyərini təhlükəsiz şəkildə format edir"""
    if isinstance(date_value, str):
        try:
            return datetime.strptime(date_value, '%Y-%m-%d').strftime(format_str)
        except ValueError:
            return str(date_value)
    elif hasattr(date_value, 'strftime'):
        return date_value.strftime(format_str)
    else:
        return str(date_value)

def safe_date_parse(date_value):
    """Tarix dəyərini təhlükəsiz şəkildə parse edir"""
    # Debug mesajlarını azaldıq - yalnız xəta halında log yazırıq
    # logging.debug(f"safe_date_parse çağırıldı. Dəyər: {date_value}, Tip: {type(date_value)}")
    
    if isinstance(date_value, str):
        try:
            # Əvvəlcə ISO formatını yoxlayırıq
            if 'T' in date_value:
                result = datetime.fromisoformat(date_value.replace('Z', '+00:00')).date()
            else:
                result = datetime.strptime(date_value, '%Y-%m-%d').date()
            # logging.debug(f"String parse uğurlu: {result}")
            return result
        except ValueError as e:
            # logging.debug(f"String parse xətası: {e}")
            return None
    elif isinstance(date_value, date):
        # logging.debug(f"Date tipi parse uğurlu: {date_value}")
        return date_value
    elif hasattr(date_value, 'date'):
        result = date_value.date()
        # logging.debug(f"Date obyekti parse uğurlu: {result}")
        return result
    else:
        # logging.debug(f"Naməlum tip: {type(date_value)}")
        return None

class Tooltip:
    def __init__(self, widget, text, font_name="Segoe UI"):
        self.widget = widget
        self.text = text
        self.tooltip_window = None
        self.font_name = font_name
        
        # Xəta idarəetməsi əlavə edirik
        try:
            self.widget.bind("<Enter>", self.show_tooltip, add='+')
            self.widget.bind("<Leave>", self.hide_tooltip, add='+')
        except tk.TclError as e:
            # Widget artıq mövcud deyilsə, xətanı ignore edirik
            print(f"Tooltip bind xətası (təhlükəsiz): {e}")
        
    def show_tooltip(self, event):
        if self.tooltip_window or not self.text: 
            return
            
        # Widget-in hələ də mövcud olduğunu yoxlayırıq
        try:
            self.widget.winfo_exists()
        except tk.TclError:
            return
            
        # Sadə və etibarlı pozisiya hesablaması - mouse pozisiyasından istifadə edirik
        x = event.x_root + 25
        y = event.y_root + 25
        
        try:
            self.tooltip_window = Toplevel(self.widget)
            self.tooltip_window.wm_overrideredirect(True)
            self.tooltip_window.wm_geometry(f"+{x}+{y}")
            
            label = tk.Label(self.tooltip_window, text=self.text, justify='left', 
                             background="#ffffe0", relief='solid', borderwidth=1, 
                             font=(self.font_name, 8))
            label.pack(ipadx=1)
        except tk.TclError as e:
            # Tooltip yaradılarkən xəta baş verərsə, ignore edirik
            print(f"Tooltip yaradılma xətası (təhlükəsiz): {e}")

    def hide_tooltip(self, event):
        if self.tooltip_window:
            try:
                self.tooltip_window.destroy()
            except tk.TclError:
                # Tooltip artıq yox olubsa, ignore edirik
                pass
        self.tooltip_window = None


# Universal kalendar import (nisbi yol ilə)
from .universal_calendar import DateEntry

class CustomDateEntry(ttk.Frame):
    def __init__(self, parent, date_pattern='dd.mm.yyyy', font_name="Segoe UI", **kwargs):
        # DÜZƏLİŞ: `font_name` kwargs-dan çıxarılır ki, super().__init__-ə ötürülməsin
        if 'font_name' in kwargs:
            del kwargs['font_name']

        super().__init__(parent, **kwargs)
        
        self.main_font = font_name
        self.date_var = tk.StringVar()
        self.strftime_pattern = date_pattern.replace('dd', '%d').replace('mm', '%m').replace('yyyy', '%Y')
        
        # Universal kalendar istifadə edirik
        self.date_entry = DateEntry(self, self.date_var)
        self.date_entry.pack(side="left", fill="x", expand=True)
        
        self.set_date(date.today())

    def get_date(self):
        try: 
            date_str = self.date_var.get()
            # Debug mesajlarını azaldıq - yalnız xəta halında log yazırıq
            # logging.debug(f"🔍 CustomDateEntry.get_date() çağırıldı - date_str: '{date_str}', pattern: '{self.strftime_pattern}'")
            if not date_str:
                # logging.debug("🔍 CustomDateEntry.get_date() - boş string, None qaytarılır")
                return None
            
            # Əvvəlcə öz formatımızı yoxla
            try:
                result = datetime.strptime(date_str, self.strftime_pattern).date()
                # logging.debug(f"🔍 CustomDateEntry.get_date() - öz format uğurlu: {result}")
                return result
            except ValueError:
                # Əgər öz formatımız işləmirsə, DateEntry formatını yoxla
                try:
                    result = datetime.strptime(date_str, '%Y-%m-%d').date()
                    logging.debug(f"🔍 CustomDateEntry.get_date() - DateEntry format uğurlu: {result}")
                    return result
                except ValueError:
                    logging.debug(f"🔍 CustomDateEntry.get_date() - hər iki format uğursuz")
                    return None
        except (ValueError, TypeError) as e: 
            logging.debug(f"🔍 CustomDateEntry.get_date() - parse xətası: {e}")
            return None

    def set_date(self, new_date):
        if isinstance(new_date, (date, datetime)): 
            self.date_var.set(new_date.strftime(self.strftime_pattern))
        elif isinstance(new_date, str): 
            self.date_var.set(new_date)
            self.master._update_days()
        elif hasattr(self.master.master, '_update_days'):
            self.master.master._update_days()

def mezuniyyet_muddetini_hesabla(baslama_str, bitme_str):
    """Məzuniyyət müddətini hesablayır (günlərlə)"""
    logging.debug(f"mezuniyyet_muddetini_hesabla çağırıldı. Başlama: {baslama_str}, Bitmə: {bitme_str}")
    
    try:
        # DÜZƏLİŞ: Təhlükəsiz tarix parse
        baslama_tarixi = safe_date_parse(baslama_str)
        bitme_tarixi = safe_date_parse(bitme_str)
        
        logging.debug(f"Parse edilmiş tarixlər - Başlama: {baslama_tarixi}, Bitmə: {bitme_tarixi}")
        
        if baslama_tarixi and bitme_tarixi:
            # Müddəti hesablayırıq (bitmə tarixi də daxil olmaqla)
            muddet = (bitme_tarixi - baslama_tarixi).days + 1
            result = max(0, muddet)  # Mənfi dəyərləri 0-a çeviririk
            logging.debug(f"Hesablanmış müddət: {result} gün")
            return result
        else:
            logging.debug(f"Tarix parse uğursuz oldu")
            return 0
    except (ValueError, TypeError, AttributeError) as e:
        logging.debug(f"Məzuniyyət müddəti hesablanarkən xəta: {e}")
        return 0

def get_vacation_status_and_color(vacation, reference_date=None):
    """Məzuniyyətin statusunu və rəngini müəyyən edir
    
    Args:
        vacation: məzuniyyət məlumatları
        reference_date: müqayisə tarixi (None olarsa, bu gün istifadə olunur)
    """
    logging.debug(f"get_vacation_status_and_color çağırıldı. Vacation: {vacation}, Reference date: {reference_date}")
    
    today = reference_date if reference_date else date.today()
    status = vacation.get('status', 'approved')
    
    if status == 'pending': 
        return "#E49B0F", "[Gözləyir]"
    if status == 'rejected': 
        return "gray", "[Rədd edilib]"
    if status == 'approved':
        try:
            # DÜZƏLİŞ: Təhlükəsiz tarix parse
            start_dt = safe_date_parse(vacation['baslama'])
            end_dt = safe_date_parse(vacation['bitme'])
            
            logging.debug(f"Status üçün tarixlər - Başlama: {start_dt}, Bitmə: {end_dt}")
            
            if start_dt and end_dt:
                if end_dt < today: 
                    return "red", "[Bitmiş]"
                elif start_dt <= today <= end_dt: 
                    return "green", "[Davam edən]"
                else: 
                    return "#007bff", "[Planlaşdırılıb]"
            else:
                logging.debug(f"Status üçün tarix parse uğursuz")
                return "black", "[Tarix xətası]"
        except (ValueError, TypeError, AttributeError) as e:
            logging.debug(f"Status hesablanarkən xəta: {e}")
            return "black", "[Xəta]"
    
    return "black", "[Naməlum]"

class VacationPanel(ttk.Frame):
    def __init__(self, parent, main_font, on_save_callback, on_close_callback, employee_name=None):
        super().__init__(parent, style="Card.TFrame", padding=20)
        self.main_font = main_font
        self.on_save_callback = on_save_callback
        self.on_close_callback = on_close_callback
        self.employee_name = employee_name
        self._build_panel()

    def _build_panel(self):
        # Paneli cədvəlin içində balanslı və kompakt açırıq
        self.config(width=500, height=350)
        self.pack_propagate(False)
        # Header
        header = ttk.Frame(self, style="Card.TFrame")
        header.pack(fill='x', pady=(0, 15))
        self.panel_title = ttk.Label(header, text="Yeni Məzuniyyət Sorğusu", font=(self.main_font, 14, "bold"), style="Card.TLabel")
        self.panel_title.pack(side='left')
        ttk.Button(header, text="✖", width=3, style="Close.TButton", command=self.on_close_callback).pack(side='right')

        # Employee name (readonly)
        self.employee_label = ttk.Label(self, text=f"İşçi: {self.employee_name if self.employee_name else ''}", font=(self.main_font, 11), style="Card.TLabel")
        self.employee_label.pack(anchor='w', pady=(0, 10))

        # Date pickers
        date_frame = ttk.Frame(self, style="Card.TFrame")
        date_frame.pack(fill='x', pady=(0, 10))
        ttk.Label(date_frame, text="Başlanğıc Tarixi:", style="Card.TLabel").grid(row=0, column=0, sticky='w', padx=(0,5))
        self.panel_start_cal = CustomDateEntry(date_frame, date_pattern='dd.mm.yyyy', font_name=self.main_font)
        self.panel_start_cal.grid(row=0, column=1, sticky='ew', padx=(0,10))
        ttk.Label(date_frame, text="Bitmə Tarixi:", style="Card.TLabel").grid(row=1, column=0, sticky='w', padx=(0,5), pady=(5,0))
        self.panel_end_cal = CustomDateEntry(date_frame, date_pattern='dd.mm.yyyy', font_name=self.main_font)
        self.panel_end_cal.grid(row=1, column=1, sticky='ew', pady=(5,0), padx=(0,10))
        date_frame.columnconfigure(1, weight=1)
        
        # Tarix dəyişikliklərini dinlə
        try:
            self.panel_start_cal.date_entry.variable.trace('w', lambda *args: self._update_days())
            self.panel_end_cal.date_entry.variable.trace('w', lambda *args: self._update_days())
        except Exception as e:
            logging.debug(f"Trace əlavə etmə xətası: {e}")

        # Gün sayı
        self.days_var = tk.StringVar(value="0 gün")
        days_frame = ttk.Frame(self, style="Card.TFrame")
        days_frame.pack(fill='x', pady=(0, 10))
        ttk.Label(days_frame, text="Məzuniyyət günləri:", style="Card.TLabel").pack(side='left')
        self.days_label = ttk.Label(days_frame, textvariable=self.days_var, font=(self.main_font, 10, "bold"), style="Card.TLabel")
        self.days_label.pack(side='left', padx=(5,0))

        # Qeyd sahəsinin hündürlüyünü panelin 3-də 1-i qədər edirik
        panel_height = 350
        note_height = int(panel_height // 3 // 20)  # təxmini 1 sətrin hündürlüyü 20px
        if note_height < 2:
            note_height = 2
        ttk.Label(self, text="Qeyd:", style="Card.TLabel").pack(anchor='w', pady=(5,2))
        self.panel_note_entry = tk.Text(self, height=note_height, relief="solid", borderwidth=1, font=(self.main_font, 10))
        self.panel_note_entry.pack(fill='both', expand=True, pady=(0,10))

        # Button frame
        btn_frame = ttk.Frame(self, style="Card.TFrame")
        btn_frame.pack(fill='x', pady=(10,0))
        
        # Sol tərəf düymələri
        left_btn_frame = ttk.Frame(btn_frame, style="Card.TFrame")
        left_btn_frame.pack(side='left', fill='x', expand=True)
        
        # EXE-də işləmək üçün callback-i wrapper funksiya ilə əhatə et
        def safe_save_callback():
            try:
                print(f"💾 DEBUG components: save_btn basıldı, callback çağırılır...")
                import sys
                if sys.stdout:
                    sys.stdout.flush()
                if self.on_save_callback:
                    self.on_save_callback()
                else:
                    print(f"❌ DEBUG components: on_save_callback None!")
            except Exception as e:
                print(f"❌ DEBUG components: save_callback xətası: {e}")
                import traceback
                traceback.print_exc()
                import sys
                if sys.stdout:
                    sys.stdout.flush()
        
        self.save_btn = ttk.Button(left_btn_frame, text="Sorğunu Göndər", command=safe_save_callback)
        self.save_btn.pack(side='left', expand=True, fill='x', padx=(0,5))
        
        self.print_btn = ttk.Button(left_btn_frame, text="🖨️ Çap Et", command=self._on_print_vacation)
        self.print_btn.pack(side='left', padx=(0,5))
        
        
        # Sağ tərəf düyməsi
        self.cancel_btn = ttk.Button(btn_frame, text="Ləğv et", command=self.on_close_callback)
        self.cancel_btn.pack(side='right', padx=(5,0))

        # Success message label (hidden by default)
        self.success_var = tk.StringVar(value="")
        self.success_label = ttk.Label(self, textvariable=self.success_var, foreground="green", font=(self.main_font, 10, "bold"), style="Card.TLabel")
        self.success_label.pack(pady=(5,0))
        self.success_label.pack_forget()

        # Date change events for auto day calculation
        self.panel_start_cal.date_entry.entry.bind("<FocusOut>", self._update_days)
        self.panel_end_cal.date_entry.entry.bind("<FocusOut>", self._update_days)
        self.panel_start_cal.date_entry.entry.bind("<KeyRelease>", self._update_days)
        self.panel_end_cal.date_entry.entry.bind("<KeyRelease>", self._update_days)
        
        # Employee data reference (will be set by parent)
        self.employee_data = None

    def set_mode(self, is_edit_mode, vacation=None, employee_name=None):
        logging.info(f"=== VacationPanel set_mode başladı: is_edit_mode={is_edit_mode}, employee_name={employee_name} ===")
        print(f"🔄 DEBUG: VacationPanel set_mode başladı - is_edit_mode={is_edit_mode}, employee={employee_name}")
        
        try:
            from datetime import datetime, date
            
            # Panel widget-lərinin mövcudluğunu yoxla
            print(f"🔍 DEBUG: Panel title widget: {self.panel_title}")
            print(f"🔍 DEBUG: Employee label widget: {self.employee_label}")
            print(f"🔍 DEBUG: Start calendar widget: {self.panel_start_cal}")
            print(f"🔍 DEBUG: End calendar widget: {self.panel_end_cal}")
            
            # Panel başlığını təyin et
            title_text = "Düzəliş Et" if is_edit_mode else "Yeni Məzuniyyət Sorğusu"
            self.panel_title.config(text=title_text)
            logging.info(f"Panel başlığı təyin edildi: {title_text}")
            print(f"📋 DEBUG: Panel başlığı təyin edildi: {title_text}")
            
            if employee_name:
                employee_text = f"İşçi: {employee_name}"
                self.employee_label.config(text=employee_text)
                logging.info(f"İşçi adı təyin edildi: {employee_name}")
                print(f"👤 DEBUG: İşçi adı təyin edildi: {employee_name}")
                
            if is_edit_mode and vacation:
                logging.info("Düzəliş rejimi - vacation məlumatları yüklənir...")
                print("📝 DEBUG: Düzəliş rejimi - vacation məlumatları yüklənir...")
                
                start_date = vacation['baslama']
                end_date = vacation['bitme']
                logging.info(f"Vacation tarixləri: {start_date} - {end_date}")
                print(f"📅 DEBUG: Vacation tarixləri: {start_date} - {end_date}")
                
                if isinstance(start_date, str):
                    start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
                if isinstance(end_date, str):
                    end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
                    
                logging.info(f"Tarixlər parse edildi: {start_date} - {end_date}")
                print(f"📅 DEBUG: Tarixlər parse edildi: {start_date} - {end_date}")
                
                # Calendar widget-lərinə tarixləri təyin et
                print("📅 DEBUG: Start calendar-a tarix təyin edilir...")
                self.panel_start_cal.set_date(start_date)
                print("📅 DEBUG: End calendar-a tarix təyin edilir...")
                self.panel_end_cal.set_date(end_date)
                
                # Tarix dəyişikliklərini dinlə (əgər hələ dinlənmirsə)
                try:
                    if not hasattr(self, '_trace_added'):
                        self.panel_start_cal.date_entry.variable.trace('w', lambda *args: self._update_days())
                        self.panel_end_cal.date_entry.variable.trace('w', lambda *args: self._update_days())
                        self._trace_added = True
                except Exception as e:
                    logging.debug(f"Trace əlavə etmə xətası: {e}")
                
                # Qeyd sahəsini təmizlə və doldur
                print("📝 DEBUG: Qeyd sahəsi təmizlənir və doldurulur...")
                self.panel_note_entry.delete("1.0", tk.END)
                self.panel_note_entry.insert("1.0", vacation.get('qeyd', ''))
                
                # Düymə mətnini dəyişdir
                self.save_btn.config(text="Yadda Saxla")
                logging.info("Düzəliş rejimi məlumatları yükləndi")
                print("✅ DEBUG: Düzəliş rejimi məlumatları yükləndi")
            else:
                logging.info("Yeni sorğu rejimi - default tarixlər təyin edilir...")
                print("🆕 DEBUG: Yeni sorğu rejimi - default tarixlər təyin edilir...")
                
                today = date.today()
                print(f"📅 DEBUG: Bugünkü tarix: {today}")
                
                print("📅 DEBUG: Start calendar-a bugünkü tarix təyin edilir...")
                self.panel_start_cal.set_date(today)
                print("📅 DEBUG: End calendar-a bugünkü tarix təyin edilir...")
                self.panel_end_cal.set_date(today)
                
                print("📝 DEBUG: Qeyd sahəsi təmizlənir...")
                self.panel_note_entry.delete("1.0", tk.END)
                
                self.save_btn.config(text="Sorğunu Göndər")
                logging.info("Yeni sorğu rejimi məlumatları təyin edildi")
                print("✅ DEBUG: Yeni sorğu rejimi məlumatları təyin edildi")
                
            # Success mesajını təmizlə
            print("🧹 DEBUG: Success mesajı təmizlənir...")
            self.success_var.set("")
            self.success_label.pack_forget()
            
            # Günləri yenilə
            print("🔄 DEBUG: Günlər yenilənir...")
            self._update_days()
            
            logging.info("=== VacationPanel set_mode uğurla tamamlandı ===")
            print("✅ DEBUG: VacationPanel set_mode uğurla tamamlandı")
            
        except Exception as e:
            logging.error(f"VacationPanel set_mode xətası: {e}")
            print(f"❌ DEBUG: VacationPanel set_mode xətası: {e}")
            import traceback
            error_traceback = traceback.format_exc()
            logging.error(f"Traceback: {error_traceback}")
            print(f"📋 DEBUG: Traceback: {error_traceback}")
            raise

    def _update_days(self, event=None):
        # Hesablamanı təhlükəsiz və dəqiq etmək üçün util funksiyasından istifadə edirik
        try:
            # Debug mesajlarını azaldıq - yalnız xəta halında log yazırıq
            # logging.debug("🔍 _update_days başladı - tarix dəyərlərini yoxlayırıq")
            
            # DateEntry obyektlərindən tarixləri al
            start = None
            end = None
            
            # Start date alma - debug mesajlarını azaldıq
            if hasattr(self, 'panel_start_cal') and self.panel_start_cal:
                if hasattr(self.panel_start_cal, 'get_date'):
                    start = self.panel_start_cal.get_date()
                elif hasattr(self.panel_start_cal, 'date_entry'):
                    if hasattr(self.panel_start_cal.date_entry, 'variable'):
                        start_str = self.panel_start_cal.date_entry.variable.get()
                        logging.debug(f"🔍 Start variable dəyəri: '{start_str}'")
                        if start_str:
                            try:
                                start = datetime.strptime(start_str, '%Y-%m-%d').date()
                                logging.debug(f"🔍 Start parse uğurlu: {start}")
                            except ValueError as ve:
                                logging.debug(f"🔍 Start parse xətası: {ve}")
                                start = None
                        else:
                            logging.debug("🔍 Start string boşdur")
                    else:
                        logging.debug("🔍 date_entry.variable mövcud deyil")
                else:
                    logging.debug("🔍 date_entry mövcud deyil")
            else:
                logging.debug("🔍 panel_start_cal mövcud deyil")
            
            # End date alma - ətraflı debug
            logging.debug(f"🔍 End calendar yoxlanılır: {hasattr(self, 'panel_end_cal')}")
            if hasattr(self, 'panel_end_cal') and self.panel_end_cal:
                logging.debug(f"🔍 panel_end_cal mövcuddur: {self.panel_end_cal}")
                logging.debug(f"🔍 panel_end_cal.get_date metodu: {hasattr(self.panel_end_cal, 'get_date')}")
                
                if hasattr(self.panel_end_cal, 'get_date'):
                    end = self.panel_end_cal.get_date()
                    logging.debug(f"🔍 get_date() nəticəsi: {end}")
                elif hasattr(self.panel_end_cal, 'date_entry'):
                    logging.debug(f"🔍 date_entry mövcuddur: {self.panel_end_cal.date_entry}")
                    if hasattr(self.panel_end_cal.date_entry, 'variable'):
                        end_str = self.panel_end_cal.date_entry.variable.get()
                        logging.debug(f"🔍 End variable dəyəri: '{end_str}'")
                        if end_str:
                            try:
                                end = datetime.strptime(end_str, '%Y-%m-%d').date()
                                logging.debug(f"🔍 End parse uğurlu: {end}")
                            except ValueError as ve:
                                logging.debug(f"🔍 End parse xətası: {ve}")
                                end = None
                        else:
                            logging.debug("🔍 End string boşdur")
                    else:
                        logging.debug("🔍 date_entry.variable mövcud deyil")
                else:
                    logging.debug("🔍 date_entry mövcud deyil")
            else:
                logging.debug("🔍 panel_end_cal mövcud deyil")
            
            logging.debug(f"🔍 Final tarixlər - Start: {start}, End: {end}")
            days = mezuniyyet_muddetini_hesabla(start, end)
            logging.debug(f"🔍 Hesablanmış günlər: {days}")
            self.days_var.set(f"{days} gün")
        except Exception as e:
            logging.debug(f"🔍 _update_days xətası: {e}")
            import traceback
            logging.debug(f"🔍 Traceback: {traceback.format_exc()}")
            self.days_var.set("0 gün")

    def _on_print_vacation(self):
        """Məzuniyyəti yığcam formatda çap edir"""
        try:
            from utils.print_service import generate_compact_vacation_html
            import tkinter.messagebox as messagebox
            import tempfile
            import webbrowser
            
            # Form məlumatlarını al
            vacation_data = self.get_form_data()
            
            # Məlumatları yoxla
            if not vacation_data['start_date'] or not vacation_data['end_date']:
                messagebox.showwarning("Xəbərdarlıq", "Zəhmət olmasa başlanğıc və bitmə tarixlərini daxil edin!")
                return
            
            if not self.employee_data:
                messagebox.showwarning("Xəbərdarlıq", "İşçi məlumatları tapılmadı!")
                return
            
            # Yığcam HTML yaradırıq
            html_content = generate_compact_vacation_html(self.employee_data, vacation_data)
            
            # Temp fayl yaradırıq
            with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False, encoding='utf-8') as temp_file:
                temp_file.write(html_content)
                temp_file_path = temp_file.name
            
            # Brauzer-də açırıq (çap üçün)
            webbrowser.open(f'file://{temp_file_path}')
            
            messagebox.showinfo("Uğur", "Məzuniyyət sənədi yığcam formatda çap üçün hazırlandı!")
                
        except Exception as e:
            import tkinter.messagebox as messagebox
            messagebox.showerror("Xəta", f"Çap xətası: {e}")
            print(f"Çap xətası: {e}")
    

    def set_employee_data(self, employee_data):
        """İşçi məlumatlarını təyin edir"""
        self.employee_data = employee_data

    def get_form_data(self):
        return {
            'start_date': self.panel_start_cal.get_date(),
            'end_date': self.panel_end_cal.get_date(),
            'note': self.panel_note_entry.get("1.0", tk.END).strip()
        }

    def show_success(self, message):
        self.success_var.set(message)
        self.success_label.pack(pady=(5,0))