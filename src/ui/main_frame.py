#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import tkinter as tk
from tkinter import ttk, messagebox, Toplevel
from datetime import datetime, date
import logging
import sys
import os
import time
import math
import threading
import importlib
import inspect
logging.basicConfig(level=logging.DEBUG)

# ttkbootstrap import etməyə çalış, əgər yoxdursa ttk istifadə et
try:
    import ttkbootstrap as tb
except ImportError:
    # ttkbootstrap yoxdursa, ttk istifadə et
    import tkinter.ttk as tb

# Debug sistemi əlavə et
current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, current_dir)
# Realtime debug sistemi - şərti import
try:
    try:
        from utils.realtime_debug import log_signal_sent, log_signal_received, log_data_change, log_ui_update, log_performance, log_sync_event
    except ImportError:
        from src.utils.realtime_debug import log_signal_sent, log_signal_received, log_data_change, log_ui_update, log_performance, log_sync_event
except ImportError:
    # Əgər debug modulu tapılmazsa, boş funksiyalar yaradırıq
    def log_signal_sent(*args, **kwargs): pass
    def log_signal_received(*args, **kwargs): pass
    def log_data_change(*args, **kwargs): pass
    def log_ui_update(*args, **kwargs): pass
    def log_performance(*args, **kwargs): pass
    def log_sync_event(*args, **kwargs): pass

# Düzgün importlar əlavə edildi
from .components import mezuniyyet_muddetini_hesabla, CustomDateEntry, VacationPanel

from .employee_detail_frame import EmployeeDetailFrame
from .dashboard_calendar_frame import DashboardCalendarFrame
from .notifications_window import NotificationsWindow
from .user_management_window import UserManagementPage
from .employee_form_window import EmployeeFormWindow
from .archive_window import ArchiveWindow
from .error_viewer_window import ErrorViewerPage
# from .tools_window import ToolsWindow  # Silindi


# Proyekt importları
from database import database, command_queries, session_queries
from utils.updater import UpdaterService
from core.real_time_notifier import init_notifier, get_notifier, stop_notifier
import tkinter as tk

# Debug manager import
try:
    from utils.debug_manager import show_debug_window, debug_log, setup_debug_print_intercept
    setup_debug_print_intercept()  # Print intercept'ini aktivləşdir
except ImportError:
    try:
        from src.utils.debug_manager import show_debug_window, debug_log, setup_debug_print_intercept
        setup_debug_print_intercept()  # Print intercept'ini aktivləşdir
    except ImportError:
        def show_debug_window():
            pass
        def debug_log(*args, **kwargs):
            pass

# Dashboard imports removed

class MainAppFrame(ttk.Frame):
    def __init__(self, parent, current_user, version_info, logout_callback):
        import time
        frame_init_start = time.time()
        
        super().__init__(parent)
        self.parent = parent
        self.current_user = current_user
        self.logout_callback = logout_callback
        self.version_info = version_info
        self.current_date = date.today() # <--- BU SƏTRİ ƏLAVƏ EDİN
        # Font təyinini düzgün formatda et
        top_level_font = self.winfo_toplevel().main_font if hasattr(self.winfo_toplevel(), 'main_font') else 'Helvetica'
        self.main_font = top_level_font if isinstance(top_level_font, str) else 'Helvetica'
        # Tema sistemi silindi - sadə stillər istifadə edilir
        style = ttk.Style(self)
        style.configure("Card.TFrame", background='#ffffff')
        style.configure("Card.TLabel", background='#ffffff', font=(self.main_font, 9))
        style.configure("Close.TButton", font=(self.main_font, 10, 'bold'), borderwidth=0, relief="flat")
        style.configure("Summary.TLabel", font=(self.main_font, 9), background='#ffffff')
        style.configure("SummaryValue.TLabel", font=(self.main_font, 10, "bold"), background='#ffffff')
        style.configure("Sidebar.TFrame", background='#f8f9fa')
        style.configure("Sidebar.TLabel", background='#f8f9fa')
        style.configure("Header.TFrame", background='#007bff')
        style.configure("Header.TLabel", background='#007bff', foreground='white', font=(self.main_font, 14, 'bold'))
        style.configure("TableHeader.TLabel", background='#222831', foreground='white', font=(self.main_font, 11, 'bold'))
        style.configure("TableRow.TLabel", background='#ffffff', font=(self.main_font, 10))
        style.configure("Accent.TButton")
        
        # Bildiriş pəncərəsi üçün stillər (sarı fondan qurtarmaq)
        style.configure("Notification.TFrame", background='#ffffff', borderwidth=1)
        style.configure("Notification.TLabel", background='#ffffff', foreground='#000000')
        style.configure("Notification.TCheckbutton", background='#ffffff')
        style.configure("Read.TFrame", background='#f0f0f0', borderwidth=1)
        style.configure("Read.TLabel", background='#f0f0f0', foreground='#666666')
        style.configure("Read.TCheckbutton", background='#f0f0f0')
        
        # ttkbootstrap üçün font stilləri
        style.configure("Info.TButton", font=(self.main_font, 11, 'bold'))
        style.configure("Primary.TButton", font=(self.main_font, 11, 'bold'))
        
        # Navbar üçün səliqəli stillər
        style.configure("Navbar.TFrame", background='#1a1a1a')
        style.configure("Navbar.TLabel", background='#1a1a1a', foreground='#ffffff')
        style.configure("Navbar.TButton", font=(self.main_font, 9), padding=(4, 2))
        
        self.opened_windows = []  # Açıq pəncərələri izləmək üçün
        self.current_vacation_window = None  # Məzuniyyət pəncərəsini izləmək üçün
        self.notif_window = None
        self.command_check_timer = None
        self.auto_refresh_timer = None
        self.master_logout_timer_id = None
        self.is_admin = self.current_user['role'].strip() == 'admin'

        self.vacation_panel_active = False
        self.animation_in_progress = False
        self.is_update_active = False
        self.current_view = 'dashboard'  # Default view
        self.data = {}  # İşçi məlumatları üçün başlanğıc boş dict

        # Load icon images - dərhal yüklə ki, setup_left_panel-də istifadə oluna bilsin
        self.load_icon_images()

        self.create_main_layout()
        self.create_views()
        # vacation_form_panel-i yalnız lazım olduqda yaradacağıq
        self.vacation_form_panel = None
        self.current_vacation_window = None
        
        # İlk dəfə məlumatları yüklə - animasiya gizlədildikdən sonra
        # Bu, proqramın daha tez açılmasına kömək edir
        self.data = {}  # Boş dict ilə başla
        self.show_view('dashboard')
        self.update_profile_button()
        
        # Məlumatları asinxron şəkildə yüklə (animasiya gizlədildikdən sonra)
        # Daha uzun gecikmə - UI tam yüklənəndən və animasiya gizlədildikdən sonra
        
        # MainAppFrame yaradılmasının vaxtını ölç
        import time
        frame_init_end = time.time()
        frame_init_duration = frame_init_end - frame_init_start
        print(f"⏱️ [STARTUP] MainAppFrame.__init__ tamamlandı: {frame_init_duration:.3f} saniyə")
        
        # OPTİMALLAŞDIRMA: Lazy loading - yalnız dashboard üçün lazım olan məlumatları yüklə
        # User üçün daha tez yüklə - UI donmasın
        # Dərhal başlat - asinxron olduğu üçün UI bloklanmayacaq
        # Delay artırıldı - UI tam yüklənəndən sonra məlumat yükləmə başlasın
        delay = 100 if not self.is_admin else 300
        self.after(delay, lambda: self.load_and_refresh_data(load_full_data=False))
    
    def _safe_flush_stdout(self):
        """Təhlükəsiz sys.stdout.flush() - EXE-də sys.stdout None ola bilər"""
        try:
            if sys.stdout:
                self._safe_flush_stdout()
        except Exception:
            pass  # Xəta olsa belə davam et
    
    def load_icon_images(self):
        """Load icon images from file system - optimallaşdırılıb"""
        self.icon_images = {}
        self.navbar_icons = {}  # Navbar iconları üçün yeni dict
        
        try:
            # Get the icon directory path
            if getattr(sys, 'frozen', False):
                # PyInstaller EXE mode - icons are in root icons folder
                base_path = sys._MEIPASS
                icon_dir = os.path.join(base_path, 'icons', 'isci redakte iconlari')
            else:
                # Normal Python mode - go up 3 levels to get to project root
                base_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
                icon_dir = os.path.join(base_path, 'src', 'icons', 'isci redakte iconlari')
            
            # Load each icon if it exists - yalnız əsas iconlar
            try:
                from PIL import Image, ImageTk
                
                icon_files = {
                    'add': 'add-user.png',
                    'edit': 'edit.png',
                    'delete': 'delete.png',
                    'hide': 'hide.png'
                }
                
                for key, filename in icon_files.items():
                    icon_path = os.path.join(icon_dir, filename)
                    if os.path.exists(icon_path):
                        try:
                            img = Image.open(icon_path)
                            img = img.resize((30, 30), Image.Resampling.LANCZOS)
                            self.icon_images[key] = ImageTk.PhotoImage(img)
                        except Exception as e:
                            logging.warning(f"Failed to load icon {filename}: {e}")
                            self.icon_images[key] = None
                    else:
                        self.icon_images[key] = None
            except ImportError:
                # PIL not available, use None for all icons
                logging.warning("PIL not available, icons will not be displayed")
                for key in ['add', 'edit', 'delete', 'hide']:
                    self.icon_images[key] = None
        except Exception as e:
            logging.warning(f"Failed to load icon images: {e}")
            # Set all to None if loading fails
            for key in ['add', 'edit', 'delete', 'hide']:
                self.icon_images[key] = None
        
        # Navbar iconlarını dərhal yüklə (iconlar görünməlidir)
        self._load_navbar_icons()
        
        # Keyboard shortcuts
        self._setup_keyboard_shortcuts()
    
    def _load_navbar_icons(self):
        """Navbar iconlarını yükləyir"""
        try:
            from PIL import Image, ImageTk
            import os
            
            # Get the icon directory path
            if getattr(sys, 'frozen', False):
                base_path = sys._MEIPASS
                icon_dir = os.path.join(base_path, 'icons', 'ana pencere iconlari')
                print(f"🔍 DEBUG: EXE mode navbar - base_path: {base_path}")
                print(f"🔍 DEBUG: EXE mode navbar - icon_dir: {icon_dir}")
            else:
                base_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
                icon_dir = os.path.join(base_path, 'src', 'icons', 'ana pencere iconlari')
                print(f"🔍 DEBUG: Dev mode navbar - base_path: {base_path}")
                print(f"🔍 DEBUG: Dev mode navbar - icon_dir: {icon_dir}")
            
            print(f"🔍 DEBUG: navbar icon_dir exists: {os.path.exists(icon_dir)}")
            if os.path.exists(icon_dir):
                print(f"🔍 DEBUG: navbar icon_dir contents: {os.listdir(icon_dir)}")
            
            # Navbar icon faylları
            navbar_icon_files = {
                'refresh': 'melumatlari yenileme.png',
                'profil': 'profil.png',
                'adminpanel': 'adminpanel.png',
                'bildirim': 'bildirim.png',
                'cixis': 'cixis.png',
                'anasehife': 'anasehife.png',
                'aletler': 'aletler.png',
            }
            
            for key, filename in navbar_icon_files.items():
                icon_path = os.path.join(icon_dir, filename)
                if os.path.exists(icon_path):
                    try:
                        img = Image.open(icon_path)
                        
                        # PNG-i transparent background üçün RGBA-ya çevir
                        if img.mode != 'RGBA':
                            img = img.convert("RGBA")
                        
                        # Sarı rəngləri transparent et (#F0ED00 və oxşarları)
                        pixels = img.load()
                        for y in range(img.height):
                            for x in range(img.width):
                                r, g, b, a = pixels[x, y]
                                # Sarı rəngləri aşkar et (#F0ED00, #F5F500, #FFFF00 oxşarları)
                                if r > 220 and g > 220 and b < 50:
                                    pixels[x, y] = (r, g, b, 0)  # Transparent et
                        
                        img = img.resize((28, 28), Image.Resampling.LANCZOS)
                        self.navbar_icons[key] = ImageTk.PhotoImage(img)
                    except Exception as e:
                        logging.warning(f"Failed to load navbar icon {filename}: {e}")
                        self.navbar_icons[key] = None
                else:
                    logging.warning(f"Navbar icon file not found: {icon_path}")
                    self.navbar_icons[key] = None
                    
        except ImportError:
            logging.warning("PIL not available, navbar icons will not be displayed")
            self.navbar_icons = {}
        except Exception as e:
            logging.warning(f"Failed to load navbar icons: {e}")
            self.navbar_icons = {}

    def _setup_hot_reload(self):
        """Hot reload sistemini quraşdırır - artıq navbar dropdown-da inteqrasiya edilib"""
        try:
            # File watcher başladır
            self._start_file_watcher()
            
            # Global keyboard shortcuts
            self.parent.bind_all('<Control-Shift-R>', lambda e: self._global_hot_reload())
            
        except Exception as e:
            logging.warning(f"Hot reload quraşdırıla bilmədi: {e}")
    
    def _global_hot_reload(self):
        """Global hot reload - bütün pəncərələri yeniləyir"""
        try:
            logging.info("Global hot reload başladıldı...")
            if hasattr(self, 'update_status_label'):
                self.update_status_label.config(text="Global yeniləmə başladı...")
                self.update()
            
            # Bütün modulları yenidən yüklə (tam siyahı)
            modules_to_reload = [
                'src.ui.components',
                'src.ui.employee_form_window',
                'src.ui.employee_detail_frame',
                'src.ui.tools_window',
                'src.ui.user_management_window',
                'src.ui.error_viewer_window',
                'src.ui.profile_window',
                'src.ui.password_reset_window',
                'src.ui.auth',
                'src.ui.main_frame',
                'src.ui.vacation_tree',
                'src.database.database',
                'src.database.user_queries',
                'src.database.vacation_queries',
                'src.database.departments_positions_queries',
                'src.database.connection',
                'src.database.manager',
                'src.core.tenant_manager',
                'src.core.email_service',
                'src.utils.print_service',
                'src.utils.cache',
                'src.utils.updater'
            ]
            
            reload_count = 0
            for module_name in modules_to_reload:
                try:
                    if module_name in sys.modules:
                        importlib.reload(sys.modules[module_name])
                        reload_count += 1
                        logging.info(f"Global modul yeniləndi: {module_name}")
                        if hasattr(self, 'update_status_label'):
                            self.update_status_label.config(text=f"Global: {module_name}")
                            self.update()
                except Exception as e:
                    logging.warning(f"Global modul yenilənə bilmədi {module_name}: {e}")
            
            # Bütün açıq pəncərələri yenilə
            self._refresh_all_windows()
            
            # Məlumatları yenidən yüklə
            self.load_and_refresh_data()
            
            if hasattr(self, 'update_status_label'):
                self.update_status_label.config(text=f"🌍 Global: {reload_count} modul yeniləndi")
            messagebox.showinfo("Uğurlu", f"Global yeniləmə tamamlandı!\nYenilənən modullar: {reload_count}\nBütün pəncərələr və məlumatlar yeniləndi!")
            
        except Exception as e:
            logging.error(f"Global hot reload xətası: {e}")
            if hasattr(self, 'update_status_label'):
                self.update_status_label.config(text="❌ Global yeniləmə xətası")
            messagebox.showerror("Xəta", f"Global hot reload xətası: {e}")
    
    def _refresh_all_windows(self):
        """Bütün açıq pəncərələri yeniləyir"""
        try:
            # Mövcud məlumatları yenilə
            self.load_and_refresh_data()
            
            # Açıq pəncərələri yenilə
            for window in self.opened_windows[:]:
                try:
                    if hasattr(window, 'refresh_data'):
                        window.refresh_data()
                    elif hasattr(window, 'load_department_and_position_data'):
                        window.load_department_and_position_data()
                except Exception as e:
                    logging.warning(f"Pəncərə yenilənə bilmədi: {e}")
            
            logging.info("Bütün pəncərələr yeniləndi")
            
        except Exception as e:
            logging.error(f"Pəncərələr yeniləmə xətası: {e}")
    
    def _start_file_watcher(self):
        """Fayl dəyişikliklərini izləyir"""
        try:
            import watchdog
            from watchdog.observers import Observer
            from watchdog.events import FileSystemEventHandler
            
            class FileChangeHandler(FileSystemEventHandler):
                def __init__(self, callback):
                    self.callback = callback
                    self.last_modified = {}
                
                def on_modified(self, event):
                    if event.is_directory:
                        return
                    if event.src_path.endswith('.py'):
                        # Duplicate event-ləri qarşısını al
                        current_time = time.time()
                        if event.src_path in self.last_modified:
                            if current_time - self.last_modified[event.src_path] < 1.0:
                                return
                        self.last_modified[event.src_path] = current_time
                        
                        logging.info(f"Fayl dəyişikliyi aşkar edildi: {event.src_path}")
                        self.callback()
            
            # src papkasını izlə
            src_path = os.path.join(os.path.dirname(os.path.dirname(__file__)))
            event_handler = FileChangeHandler(self._on_file_changed)
            self.observer = Observer()
            self.observer.schedule(event_handler, src_path, recursive=True)
            self.observer.start()
            
            logging.info(f"File watcher başladıldı: {src_path}")
            
        except ImportError:
            logging.warning("watchdog modulu tapılmadı - avtomatik yeniləmə işləməyəcək")
        except Exception as e:
            logging.warning(f"File watcher başladıla bilmədi: {e}")
    
    def _on_file_changed(self):
        """Fayl dəyişikliyi zamanı çağırılır"""
        if hasattr(self, 'auto_reload_var') and self.auto_reload_var.get():
            print("🔄 Fayl dəyişikliyi aşkar edildi - hot reload başladılacaq...")
            logging.info("Fayl dəyişikliyi aşkar edildi - hot reload başladılacaq...")
            self.after(1000, self._hot_reload)  # 1 saniyə gecikmə
        else:
            print("⚠️ Fayl dəyişikliyi aşkar edildi, amma auto reload deaktivdir")
            logging.info("Fayl dəyişikliyi aşkar edildi, amma auto reload deaktivdir")
    
    # _toggle_auto_reload funksiyası artıq dropdown-da inteqrasiya edilib
    
    
    def _refresh_ui(self):
        """UI-ni yeniləyir"""
        try:
            if hasattr(self, 'update_status_label'):
                self.update_status_label.config(text="UI yenilənir...")
                self.update()
            
            # Mövcud məlumatları yenilə
            self.load_and_refresh_data()
            
            # Açıq pəncərələri yenilə
            refreshed_count = 0
            for window in self.opened_windows[:]:
                try:
                    if hasattr(window, 'refresh_data'):
                        window.refresh_data()
                        refreshed_count += 1
                    elif hasattr(window, 'refresh') and callable(window.refresh):
                        window.refresh()
                        refreshed_count += 1
                    elif hasattr(window, 'load_data') and callable(window.load_data):
                        window.load_data()
                        refreshed_count += 1
                except Exception as e:
                    logging.warning(f"Pəncərə yenilənə bilmədi: {e}")
            
            # Əgər profil və ya digər frame-lər açıqdırsa onları da yenilə
            if hasattr(self, 'views'):
                for view_name, view in self.views.items():
                    try:
                        if hasattr(view, 'refresh') and callable(view.refresh):
                            view.refresh()
                        elif hasattr(view, 'load_data') and callable(view.load_data):
                            view.load_data()
                    except Exception as e:
                        logging.warning(f"View yenilənə bilmədi {view_name}: {e}")
            
            # Navbar-ı yenilə
            if hasattr(self, 'update_profile_button'):
                self.update_profile_button()
            
            logging.info("UI yeniləndi")
            
            if hasattr(self, 'update_status_label'):
                self.update_status_label.config(text=f"✅ UI yeniləndi ({refreshed_count} pəncərə)")
                    
        except Exception as e:
            logging.error(f"UI yeniləmə xətası: {e}")
            if hasattr(self, 'update_status_label'):
                self.update_status_label.config(text="❌ UI yeniləmə xətası")
    
    def _setup_keyboard_shortcuts(self):
        """Keyboard shortcut-ları quraşdırır"""
        try:
            # Ctrl+R - Hot reload
            self.bind_all('<Control-r>', lambda e: self._hot_reload())
            
            # F5 - Manual refresh data
            self.bind_all('<F5>', lambda e: self.manual_refresh_data())
            
            # Ctrl+Shift+R - Force reload
            self.bind_all('<Control-Shift-R>', lambda e: self._force_reload())
            
            # Ctrl+F5 - Force refresh with cache clear
            self.bind_all('<Control-F5>', lambda e: self._force_refresh_data())
            
            logging.info("Keyboard shortcuts quraşdırıldı: Ctrl+R (reload), F5 (manual refresh), Ctrl+Shift+R (force reload), Ctrl+F5 (force refresh)")
            
        except Exception as e:
            logging.warning(f"Keyboard shortcuts quraşdırıla bilmədi: {e}")
    
    def _force_reload(self):
        """Məcburi yenidən yükləmə"""
        try:
            logging.info("Məcburi reload başladıldı...")
            
            # Bütün modulları yenidən yüklə
            modules_to_reload = [
                'src.ui.components',
                'src.ui.employee_form_window', 
                'src.ui.tools_window',
                'src.ui.auth',
                'src.ui.main_frame',
                'src.database.database',
                'src.database.user_queries',
                'src.database.vacation_queries',
                'src.database.connection',
                'src.core.tenant_manager'
            ]
            
            for module_name in modules_to_reload:
                try:
                    if module_name in sys.modules:
                        importlib.reload(sys.modules[module_name])
                        logging.info(f"Modul məcburi yeniləndi: {module_name}")
                except Exception as e:
                    logging.warning(f"Modul məcburi yenilənə bilmədi {module_name}: {e}")
            
            # UI-ni tam yenilə
            self._refresh_ui()
            
            messagebox.showinfo("Uğurlu", "Məcburi reload uğurla tamamlandı!")
            
        except Exception as e:
            logging.error(f"Məcburi reload xətası: {e}")
            messagebox.showerror("Xəta", f"Məcburi reload xətası: {e}")
    
    def _full_system_reload(self):
        """Tam sistem yeniləməsi - bütün modullar, cache və UI"""
        try:
            logging.info("Tam sistem yeniləməsi başladıldı...")
            if hasattr(self, 'update_status_label'):
                self.update_status_label.config(text="🔄 Tam sistem yeniləməsi...")
                self.update()
            
            # 1. Cache-i təmizlə
            try:
                from utils.cache import clear_cache
                clear_cache()
                logging.info("Cache təmizləndi")
            except Exception as e:
                logging.warning(f"Cache təmizlənə bilmədi: {e}")
            
            # 2. Python modullarını sys.modules-dan sil (tam yeniləmə üçün)
            modules_to_clear = []
            for module_name in list(sys.modules.keys()):
                if any(pattern in module_name for pattern in [
                    'src.ui', 'src.database', 'src.core', 'src.utils',
                    'ui.', 'database.', 'core.', 'utils.',
                    'print_service', 'employee_detail_frame'
                ]):
                    modules_to_clear.append(module_name)
            
            for module_name in modules_to_clear:
                try:
                    del sys.modules[module_name]
                    logging.info(f"Modul sys.modules-dan silindi: {module_name}")
                except:
                    pass
            
            # 3. Bütün modulları yenidən yüklə (ən geniş siyahı)
            modules_to_reload = [
                # UI modulları
                'src.ui.components',
                'src.ui.employee_form_window',
                'src.ui.employee_detail_frame',
                'src.ui.tools_window',
                'src.ui.user_management_window',
                'src.ui.error_viewer_window',
                'src.ui.profile_window',
                'src.ui.password_reset_window',
                'src.ui.auth',
                'src.ui.main_frame',
                'src.ui.vacation_tree',
                'src.ui.archive_window',
                'src.ui.notifications_window',
                'src.ui.login_history_window',
                'src.ui.realtime_status_window',
                'src.ui.debug_viewer_window',
                # Database modulları
                'src.database.database',
                'src.database.user_queries',
                'src.database.vacation_queries',
                'src.database.departments_positions_queries',
                'src.database.connection',
                'src.database.manager',
                'src.database.connection_pool',
                'src.database.command_queries',
                'src.database.error_queries',
                'src.database.notification_queries',
                'src.database.session_queries',
                'src.database.settings_queries',
                'src.database.system_queries',
                # Core modulları
                'src.core.tenant_manager',
                'src.core.email_service',
                'src.core.main',
                'src.core.real_time_notifier',
                # Utils modulları
                'src.utils.print_service',
                'src.utils.cache',
                'src.utils.updater',
                'src.utils.performance_monitor',
                'src.utils.realtime_debug',
                'src.utils.setup_windows',
                'src.utils.debug_loading',
                'src.utils.fix_central_server'
            ]
            
            reload_count = 0
            for module_name in modules_to_reload:
                try:
                    # Əvvəlcə import et, sonra reload et
                    module = importlib.import_module(module_name)
                    importlib.reload(module)
                    reload_count += 1
                    logging.info(f"Tam yeniləmə - modul: {module_name}")
                    if hasattr(self, 'update_status_label'):
                        self.update_status_label.config(text=f"Tam: {module_name}")
                        self.update()
                except Exception as e:
                    logging.warning(f"Tam yeniləmə - modul xətası {module_name}: {e}")
            
            # 4. Bütün pəncərələri bağla və yenilə
            for window in self.opened_windows[:]:
                try:
                    window.destroy()
                except:
                    pass
            self.opened_windows.clear()
            
            # 5. Məlumatları yenidən yüklə
            self.load_and_refresh_data()
            
            # 6. UI-ni tam yenilə
            self._refresh_ui()
            
            # 7. Background task-ları yenidən başlat
            self.stop_background_tasks()
            self.start_background_tasks()
            
            # 8. Yeni funksiyaları yenidən import et
            try:
                # Print service funksiyalarını yenidən import et
                from utils.print_service import generate_compact_vacation_html, generate_compact_all_vacations_html
                logging.info("Yeni print service funksiyaları import edildi")
            except Exception as e:
                logging.warning(f"Yeni funksiyalar import edilə bilmədi: {e}")
            
            if hasattr(self, 'update_status_label'):
                self.update_status_label.config(text=f"🔄 Tam yeniləmə: {reload_count} modul")
            
            messagebox.showinfo("Tam Yeniləmə Tamamlandı!", 
                              f"Sistem tamamilə yeniləndi!\n\n"
                              f"✅ {reload_count} modul yeniləndi\n"
                              f"✅ Cache təmizləndi\n"
                              f"✅ Bütün pəncərələr yeniləndi\n"
                              f"✅ Məlumatlar yenidən yükləndi\n"
                              f"✅ Background task-lar yeniləndi\n"
                              f"✅ Yeni funksiyalar yükləndi")
            
        except Exception as e:
            logging.error(f"Tam sistem yeniləməsi xətası: {e}")
            if hasattr(self, 'update_status_label'):
                self.update_status_label.config(text="❌ Tam yeniləmə xətası")
            messagebox.showerror("Xəta", f"Tam sistem yeniləməsi xətası: {e}")

    def start_background_tasks(self):
        """Arxa fonda işləyən periodik yoxlamaları başladır."""
        self.command_check_timer = self.after(5000, self._check_for_commands)  # 5 saniyədə bir
        self.auto_refresh_timer = self.after(300000, self._auto_refresh_data)   # 5 dəqiqə - performans üçün artırıldı

    def stop_background_tasks(self):
        """Pəncərə məhv edilməzdən əvvəl periodik yoxlamaları dayandırır."""
        if self.command_check_timer: self.after_cancel(self.command_check_timer)
        if self.auto_refresh_timer: self.after_cancel(self.auto_refresh_timer)
        if self.master_logout_timer_id: self.after_cancel(self.master_logout_timer_id)

    def destroy(self):
        """Pəncərə məhv edilərkən çağırılır."""
        # Navbar animasiyalarını dayandır
        if hasattr(self, 'navbar_animation_running'):
            self.navbar_animation_running = False
        
        self.stop_background_tasks()
        
        # File watcher-ı dayandır
        if hasattr(self, 'observer'):
            try:
                self.observer.stop()
                self.observer.join()
                logging.info("File watcher dayandırıldı")
            except Exception as e:
                logging.warning(f"File watcher dayandırıla bilmədi: {e}")
        
        # Keyboard shortcut-ları təmizlə
        try:
            self.unbind_all('<Control-r>')
            self.unbind_all('<F5>')
            self.unbind_all('<Control-Shift-R>')
            logging.info("Keyboard shortcuts təmizləndi")
        except Exception as e:
            logging.warning(f"Keyboard shortcuts təmizlənə bilmədi: {e}")
        
        # Real-time notification sistemini dayandır
        try:
            stop_notifier()
            logging.info("Real-time notification sistemi dayandırıldı")
        except Exception as e:
            logging.error(f"Real-time notification sistemi dayandırılarkən xəta: {e}")
        
        super().destroy()

    
    def _refresh_ui(self):
        """UI-ni yeniləyir"""
        try:
            # Mövcud məlumatları yenilə
            if hasattr(self, 'load_and_refresh_data'):
                self.load_and_refresh_data()
            
            # Açıq pəncərələri yenilə
            if hasattr(self, 'opened_windows'):
                for window in self.opened_windows[:]:
                    try:
                        if hasattr(window, 'refresh_data'):
                            window.refresh_data()
                        elif hasattr(window, 'load_department_and_position_data'):
                            window.load_department_and_position_data()
                    except Exception as e:
                        logging.warning(f"Pəncərə yenilənə bilmədi: {e}")
            
            logging.info("UI yeniləndi")
            
        except Exception as e:
            logging.error(f"UI yeniləmə xətası: {e}")

    def create_main_layout(self):
        # Səliqəli Navbar - Professional görünüş
        self.create_animated_navbar()
        
        # Navbar altında separator - daha professional görünüş
        separator = ttk.Separator(self, orient='horizontal')
        separator.pack(fill='x', pady=(0, 3))
        
        self.content_container = ttk.Frame(self)
        self.content_container.pack(expand=True, fill='both')
        
        # Sol panel - genişləndirilmiş
        self.left_frame = ttk.Frame(self.content_container, style="Sidebar.TFrame", width=300)  # Eni azaldıldı (350-dən 300-ə)
        self.left_frame.pack(side="left", fill="both", expand=False, padx=(5, 5))  # Sağ və sol 5px boşluq
        self.left_frame.pack_propagate(False)  # Genişliyi sabit saxla
        
        self.right_frame = ttk.Frame(self.content_container)
        self.right_frame.pack(side="right", expand=True, fill="both", padx=(5, 5))  # Sağ və sol 5px boşluq

        self.setup_left_panel()
        
        # View-ləri yarat - artıq __init__-də çağırılıb, burada yenidən çağırmırıq
        # self.create_views()  # SİLİNDİ - artıq __init__-də çağırılır
        
    def create_animated_navbar(self):
        """Səliqəli və professional navbar yaradır"""
        # Əsas navbar container - daha səliqəli
        self.navbar = tk.Frame(self, bg='#1a1a1a', height=60)
        self.navbar.pack(fill='x', pady=(0, 0))
        self.navbar.pack_propagate(False)
        
        # Navbar content - ağ fon yoxdur
        self.navbar_content = tk.Frame(self.navbar, bg='#1a1a1a')
        self.navbar_content.pack(fill='both', expand=True, padx=15, pady=8)
        
        # Sol bölmə - Logo və Ana Səhifə
        self.create_navbar_left_section()
        
        # Orta bölmə - Profil
        self.create_navbar_center_section()
        
        # Sağ bölmə - Funksiyalar
        self.create_navbar_right_section()
        
        # Animasiyaları başladırıq
        self.start_navbar_animations()
        
        # Click outside event binding
        self.bind("<Button-1>", self._on_click_outside)
        
    def create_navbar_left_section(self):
        """Navbar sol bölməsini yaradır"""
        left_frame = tk.Frame(self.navbar_content, bg='#1a1a1a')
        left_frame.pack(side='left')
        
        # Ana Səhifə icon düyməsi
        self.home_button = self.create_navbar_icon_label(
            left_frame, 'anasehife', lambda: self.show_view('dashboard'),
            tooltip_text='Ana Səhifə'
        )
        self.home_button.pack(side='left', padx=(0, 8), pady=2)
        
        # Sistem adı
        self.system_label = tk.Label(left_frame, text="Məzuniyyət Sistemi", 
                                    font=(self.main_font, 14, 'bold'), 
                                    bg='#1a1a1a', fg='#ffffff')
        self.system_label.pack(side='left', padx=(0, 15))
        
    def create_navbar_center_section(self):
        """Navbar orta bölməsini yaradır"""
        center_frame = tk.Frame(self.navbar_content, bg='#1a1a1a')
        center_frame.pack(side='left', expand=True, fill='x', padx=15)
        
        # Admin düymələri orta bölmədə (yalnız admin üçün)
        if self.is_admin:
            # Admin Paneli icon düyməsi
            self.admin_panel_button = self.create_navbar_icon_label(
                center_frame, 'adminpanel', None,  # Command yoxdur, hover ilə idarə edilir
                tooltip_text='Admin Paneli'
            )
            # Hover event-lərini əlavə et
            self.admin_panel_button.bind("<Enter>", self.on_admin_panel_enter)
            self.admin_panel_button.bind("<Leave>", self.on_admin_panel_leave)
            self.admin_panel_button.pack(side='left', padx=3, pady=2)
            
            # Dropdown menü container
            self.admin_dropdown_menu = None
            self.dropdown_close_job = None
            
            # Profil icon düyməsi
            self.profile_button = self.create_navbar_icon_label(
                center_frame, 'profil', self.open_profile_window,
                tooltip_text=f"{self.current_user['name']} ({self.current_user['role']})"
            )
            self.profile_button.pack(side='left', padx=3, pady=2)
            
            # Alətlər icon düyməsi
            self.tools_button = self.create_navbar_icon_label(
                center_frame, 'aletler', self.open_tools_window,
                tooltip_text='Alətlər'
            )
            self.tools_button.pack(side='left', padx=3, pady=2)
            
            # Bildirişlər icon düyməsi
            self.notifications_button = self.create_navbar_icon_label(
                center_frame, 'bildirim', self.open_notifications_window,
                tooltip_text='Bildirişlər'
            )
            self.notifications_button.pack(side='left', padx=3, pady=2)
            
            # Məlumatları Yenilə icon düyməsi
            self.refresh_button = self.create_navbar_icon_label(
                center_frame, 'refresh', self.manual_refresh_data, 
                tooltip_text='Məlumatları Yenilə (F5)'
            )
            self.refresh_button.pack(side='left', padx=3, pady=2)
        
        # Adi istifadəçilər üçün
        else:
            self.profile_button = self.create_navbar_icon_label(
                center_frame, 'profil', self.open_profile_window,
                tooltip_text=f"{self.current_user['name']} ({self.current_user['role']})"
            )
            self.profile_button.pack(side='left', padx=3, pady=2)
            
            self.notifications_button = self.create_navbar_icon_label(
                center_frame, 'bildirim', self.open_notifications_window,
                tooltip_text='Bildirişlər'
            )
            self.notifications_button.pack(side='left', padx=3, pady=2)
            
            self.refresh_button = self.create_navbar_icon_label(
                center_frame, 'refresh', self.manual_refresh_data, 
                tooltip_text='Məlumatları Yenilə (F5)'
            )
            self.refresh_button.pack(side='left', padx=3, pady=2)
        
    def create_navbar_right_section(self):
        """Navbar sağ bölməsini yaradır - səliqəli"""
        right_frame = tk.Frame(self.navbar_content, bg='#1a1a1a')
        right_frame.pack(side='right')
        
        # Debug window butonu - DEAKTİV EDİLDİ
        # self.debug_button = ttk.Button(
        #     right_frame,
        #     text="🔍",
        #     command=self.open_debug_window,
        #     width=3
        # )
        # self.debug_button.pack(side='left', padx=3, pady=2)
        
        # Çıxış icon düyməsi (yalnız sağda)
        self.logout_button = self.create_navbar_icon_label(
            right_frame, 'cixis', self.logout_callback,
            tooltip_text='Çıxış'
        )
        self.logout_button.pack(side='left', padx=3, pady=2)
        
    def create_animated_navbar_button(self, parent, text, command, **kwargs):
        """Səliqəli animasiyalı düymə yaradır"""
        # bootstyle parametrini silirik
        if 'bootstyle' in kwargs:
            del kwargs['bootstyle']
            
        # Düyməni səliqəli yaradırıq
        button = tk.Button(parent, text=text, command=command, 
                          font=(self.main_font, 9), relief='flat',
                          borderwidth=0, padx=8, pady=4, 
                          activebackground=kwargs.get('bg', '#2c3e50'),  # Hover rəngi
                          activeforeground='#ffffff',  # Hover mətn rəngi
                          **kwargs)
        
        # Hover effektləri
        button.bind("<Enter>", lambda e, btn=button: self.on_navbar_button_hover(btn, True))
        button.bind("<Leave>", lambda e, btn=button: self.on_navbar_button_hover(btn, False))
        
        # Click effekti
        button.bind("<Button-1>", lambda e, btn=button: self.on_navbar_button_click(btn))
        
        return button
    
    def create_navbar_icon_label(self, parent, icon_key, command, tooltip_text='', size=28):
        """PNG icon ilə navbar Label yaradır - bildiriş sayı ilə"""
        navbar_bg = '#1a1a1a'
        
        # Icon var yoxla
        if hasattr(self, 'navbar_icons') and self.navbar_icons.get(icon_key):
            icon_img = self.navbar_icons[icon_key]
            # Parent-in background rəngini al
            parent_bg = parent.cget('bg') if hasattr(parent, 'cget') else navbar_bg
            
            # Container Frame yarad (icon + badge üçün)
            container = tk.Frame(parent, bg=parent_bg, bd=0, highlightthickness=0)
            
            lbl = tk.Label(
                container,
                image=icon_img,
                bg=parent_bg,
                cursor='hand2',
                bd=0,
                highlightthickness=0,
                borderwidth=0,
                activebackground=parent_bg,
                highlightbackground=parent_bg
            )
            lbl.image = icon_img  # Referansı saxla
            lbl.pack()
            
            # Bildiriş iconu üçün badge yarad - iconun sağ yuxarı küncündə, yarısı çıxacaq
            if icon_key == 'bildirim':
                badge = tk.Label(
                    container,
                    text='0',
                    bg='#dc3545',  # Qırmızı
                    fg='white',
                    font=(self.main_font, 8, 'bold'),
                    bd=0,
                    highlightthickness=0,
                    width=2,
                    height=1,
                    relief='flat'
                )
                # Badge-i iconun sağ yuxarı küncünə yerləşdir - yarısı icondan çıxacaq
                # relx=1.0 və rely=0.0 - sağ yuxarı künc, anchor='ne' - şimal-şərq
                badge.place(relx=1.0, rely=0.0, anchor='ne', x=2, y=-2)
                badge.pack_forget()  # İlk öncə gizlət
                lbl.badge = badge  # Badge-i label-ə bağla
                container.badge = badge  # Container-ə də bağla
                
                # Animasiya üçün dəyişənlər
                container.animation_running = False
                container.animation_job = None
            
            if command:
                container.bind("<Button-1>", lambda e: command())
                lbl.bind("<Button-1>", lambda e: command())
            
            # Hover effektləri
            def on_enter(e):
                container.config(bg='#2c3e50')
                lbl.config(bg='#2c3e50')
            def on_leave(e):
                container.config(bg=parent_bg)
                lbl.config(bg=parent_bg)
            
            container.bind("<Enter>", on_enter)
            container.bind("<Leave>", on_leave)
            lbl.bind("<Enter>", on_enter)
            lbl.bind("<Leave>", on_leave)
            
            # Tooltip əlavə et
            if tooltip_text:
                self.create_tooltip(container, tooltip_text)
            
            return container
        else:
            # Icon yoxdursa, sadə Label yaradır
            lbl = tk.Label(
                parent,
                text='?',
                bg=navbar_bg,
                fg='white',
                cursor='hand2',
                font=(self.main_font, 10),
                bd=0,
                highlightthickness=0,
                borderwidth=0
            )
            lbl.bind("<Button-1>", lambda e: command())
            return lbl
    
    def create_icon_navbar_button(self, parent, icon, command, **kwargs):
        """Icon-only navbar düyməsi yaradır tooltip ilə"""
        tooltip_text = kwargs.pop('tooltip', '')
        
        # Icon düyməsi yaradır
        button = tk.Button(parent, text=icon, command=command, 
                          font=(self.main_font, 14), relief='flat',
                          borderwidth=0, padx=8, pady=5, 
                          activebackground=kwargs.get('bg', '#34495e'),
                          activeforeground='white',
                          **kwargs)
        
        # Hover effektləri
        button.bind("<Enter>", lambda e, btn=button: self.on_navbar_button_hover(btn, True))
        button.bind("<Leave>", lambda e, btn=button: self.on_navbar_button_hover(btn, False))
        
        # Click effekti
        button.bind("<Button-1>", lambda e, btn=button: self.on_navbar_button_click(btn))
        
        # Tooltip əlavə et
        if tooltip_text:
            self.create_tooltip(button, tooltip_text)
        
        return button
    
    def create_tooltip(self, widget, text):
        """Tooltip yaradır"""
        def on_enter(event):
            tooltip = tk.Toplevel()
            tooltip.wm_overrideredirect(True)
            tooltip.wm_geometry(f"+{event.x_root+10}+{event.y_root+10}")
            
            label = tk.Label(tooltip, text=text, 
                           font=(self.main_font, 9),
                           bg='#2c3e50', fg='white',
                           relief='solid', bd=1, padx=5, pady=2)
            label.pack()
            
            widget.tooltip = tooltip
        
        def on_leave(event):
            if hasattr(widget, 'tooltip'):
                widget.tooltip.destroy()
                delattr(widget, 'tooltip')
        
        widget.bind("<Enter>", on_enter)
        widget.bind("<Leave>", on_leave)
        
    def on_logo_hover(self, entering):
        """Logo hover effekti - test faylına uyğun"""
        if entering:
            self.logo_label.configure(font=(self.main_font, 28), fg='#f39c12')
            self.start_logo_glow()
        else:
            self.logo_label.configure(font=(self.main_font, 24), fg='white')
            self.stop_logo_glow()
    
    def start_logo_glow(self):
        """Logo glow effekti"""
        self.logo_glow_active = True
        self.animate_logo_glow()
    
    def stop_logo_glow(self):
        """Logo glow effektini dayandır"""
        self.logo_glow_active = False
    
    def animate_logo_glow(self):
        """Logo glow animasiyası - test faylına uyğun"""
        if not hasattr(self, 'logo_glow_active') or not self.logo_glow_active:
            return
            
        # Glow effekti
        current_time = time.time()
        glow_intensity = abs(math.sin(current_time * 3)) * 0.5 + 0.5
        
        # Rəng dəyişikliyi
        r = int(243 * glow_intensity)
        g = int(156 * glow_intensity)
        b = int(18 * glow_intensity)
        
        self.logo_label.configure(fg=f'#{r:02x}{g:02x}{b:02x}')
        
        # Növbəti frame
        self.after(50, self.animate_logo_glow)
    
    def on_navbar_button_hover(self, button, entering):
        """Navbar düyməsi sadə hover effekti"""
        if entering:
            # Sadə hover effekti
            self.animate_navbar_button_hover(button, True)
        else:
            # Normal vəziyyətə qayıtma
            self.animate_navbar_button_hover(button, False)
    
    def animate_navbar_button_hover(self, button, hovering):
        """Düymə hover animasiyası - fərqli rənglərlə"""
        if hovering:
            # Hover effekti - daha açıq rəng
            current_bg = button.cget('bg')
            if current_bg == '#3498db':  # Ana Səhifə
                button.configure(bg='#5dade2')
            elif current_bg == '#9b59b6':  # Profil
                button.configure(bg='#bb8fce')
            elif current_bg == '#27ae60':  # Sorgularım
                button.configure(bg='#58d68d')
            elif current_bg == '#e67e22':  # Alətlər
                button.configure(bg='#f39c12')
            elif current_bg == '#8e44ad':  # İstifadəçi İdarəetməsi
                button.configure(bg='#a569bd')
            elif current_bg == '#34495e':  # Xəta Jurnalı
                button.configure(bg='#566573')
            elif current_bg == '#f39c12':  # Bildirişlər
                button.configure(bg='#f4b942')
            elif current_bg == '#e74c3c':  # Çıxış
                button.configure(bg='#ec7063')
            
            # Subtle scale effekti
            current_font = button.cget('font')
            if isinstance(current_font, str):
                font_size = int(current_font.split()[-1])
                if font_size < 11:
                    button.configure(font=(self.main_font, font_size + 1))
        else:
            # Normal vəziyyət
            current_bg = button.cget('bg')
            if current_bg == '#5dade2':
                button.configure(bg='#3498db')
            elif current_bg == '#bb8fce':
                button.configure(bg='#9b59b6')
            elif current_bg == '#58d68d':
                button.configure(bg='#27ae60')
            elif current_bg == '#f39c12':
                button.configure(bg='#e67e22')
            elif current_bg == '#a569bd':
                button.configure(bg='#8e44ad')
            elif current_bg == '#566573':
                button.configure(bg='#34495e')
            elif current_bg == '#f4b942':
                button.configure(bg='#f39c12')
            elif current_bg == '#ec7063':
                button.configure(bg='#e74c3c')
            
            # Font ölçüsünü bərpa et
            current_font = button.cget('font')
            if isinstance(current_font, str):
                font_size = int(current_font.split()[-1])
                if font_size > 9:
                    button.configure(font=(self.main_font, font_size - 1))
    
    def on_navbar_button_click(self, button):
        """Navbar düyməsi click effekti"""
        # Click animasiyası
        self.animate_navbar_button_click(button)
    
    def animate_navbar_button_click(self, button):
        """Düymə click animasiyası - test faylına uyğun"""
        # Kiçik scale effekti - font ölçüsünü azalt
        current_font = button.cget('font')
        if isinstance(current_font, str):
            font_size = int(current_font.split()[-1])
            button.configure(font=(self.main_font, font_size - 1))
        
        # 100ms sonra normal ölçüyə qayıt
        self.after(100, lambda: self.restore_navbar_button_size(button))
    
    def restore_navbar_button_size(self, button):
        """Düymə ölçüsünü bərpa edir"""
        current_font = button.cget('font')
        if isinstance(current_font, str):
            font_size = int(current_font.split()[-1])
            if font_size < 10:
                button.configure(font=(self.main_font, font_size + 1))
    
    def on_admin_panel_enter(self, event):
        """Admin panel düyməsinə hover olduqda dropdown menüni açır"""
        if self.admin_dropdown_menu is None:
            self._create_admin_dropdown()
    
    def on_admin_panel_leave(self, event):
        """Admin panel düyməsindən çıxdıqda dropdown menüni bağlayır (əgər dropdown-da deyilsə)"""
        # Kursorun dropdown-da olub-olmadığını yoxla
        if self.admin_dropdown_menu:
            try:
                x = self.winfo_pointerx()
                y = self.winfo_pointery()
                if not self._is_cursor_over_widget(self.admin_dropdown_menu, x, y):
                    self.schedule_dropdown_close()
            except:
                self.schedule_dropdown_close()
    
    def _create_admin_dropdown(self):
        """Admin panel dropdown menyusunu yaradır"""
        if self.admin_dropdown_menu is not None:
            return  # Artıq açıqdır
        
        # Menü item-lər
        menu_items = [
            ("👥 İstifadəçi İdarəetməsi", self.open_user_management, '#8e44ad'),
            ("🚫 Gizlənmiş İşçilər", self.show_hidden_employees, '#e74c3c'),
            ("🐞 Xəta Jurnalı", self.open_error_viewer, '#34495e'),
            ("📅 Yeni Məzuniyyət İli", self._confirm_and_start_new_year, '#16a085'),
            ("📦 Məzuniyyət Arxivi", self.open_archive_view_window, '#2980b9'),
            ("📊 Realtime Status", self.open_realtime_status_window, '#d35400'),
        ]
        
        # Toplevel pəncərə yaradırıq - navbar kənarında göstərmək üçün
        root_window = self.winfo_toplevel()
        
        # Button mövqeyini al (screen koordinatları - mütləq)
        self.admin_panel_button.update_idletasks()
        root_window.update_idletasks()
        
        button_x = self.admin_panel_button.winfo_rootx()
        button_y = self.admin_panel_button.winfo_rooty() + self.admin_panel_button.winfo_height()
        button_width = self.admin_panel_button.winfo_width()
        
        # Dropdown pəncərəsini yarad
        dropdown_window = tk.Toplevel(root_window)
        dropdown_window.overrideredirect(True)
        dropdown_window.attributes("-topmost", True)
        dropdown_window.transient(root_window)
        
        # Dropdown container
        dropdown_frame = tk.Frame(dropdown_window, bg='#2c3e50', relief='raised', borderwidth=2)
        dropdown_frame.pack(fill='both', expand=True)
        
        for text, command, bg_color in menu_items:
            btn = tk.Button(dropdown_frame, text=text, command=lambda c=command: [c(), self.close_admin_dropdown()],
                          font=(self.main_font, 9), relief='flat', bg=bg_color, fg='#ffffff',
                          activebackground=bg_color, activeforeground='#ffffff',
                          anchor='w', padx=12, pady=6, width=20)
            btn.pack(fill='x', pady=1)
        
        # Ölçüləri hesabla
        dropdown_frame.update_idletasks()
        window_width = dropdown_frame.winfo_reqwidth()
        window_height = dropdown_frame.winfo_reqheight()
        
        # Button-un mərkəzindən dropdown-un soluna qədər
        centered_x = button_x + (button_width // 2) - (window_width // 2)
        
        # Çox ekranlı konfiqurasiya üçün - button-un olduğu ekranı tap
        # winfo_screenwidth() yalnız əsas ekranı qaytarır, amma button başqa ekranda ola bilər
        try:
            primary_screen_width = root_window.winfo_screenwidth()
            
            # Button-un mövqeyinə görə ekran sərhədlərini təyin et
            if button_x >= 0 and button_x < primary_screen_width:
                # Button əsas ekrandadır
                screen_left = 0
                screen_right = primary_screen_width
            elif button_x < 0:
                # Button soldakı ekrandadır (mənfi koordinat)
                screen_left = button_x - 1000  # Təxmin
                screen_right = 0
            else:
                # Button sağdakı ekrandadır
                screen_left = primary_screen_width
                screen_right = button_x + window_width + 1000  # Təxmin
            
            # Ekrandan kənara çıxmaması üçün yoxla
            if centered_x + window_width > screen_right:
                centered_x = screen_right - window_width - 5
            if centered_x < screen_left:
                centered_x = screen_left + 5
        except:
            # Xəta olsa, sadə yoxlama
            screen_width = root_window.winfo_screenwidth()
            if centered_x + window_width > screen_width:
                centered_x = screen_width - window_width - 5
            if centered_x < 0:
                centered_x = 5
        
        # Y koordinatı - button-un altında
        screen_height = root_window.winfo_screenheight()
        if button_y + window_height > screen_height:
            button_y = self.admin_panel_button.winfo_rooty() - window_height
        if button_y < 0:
            button_y = 5
        
        # Pəncərəni button-un altında yerləşdir
        dropdown_window.geometry(f'{window_width}x{window_height}+{centered_x}+{button_y}')
        
        # Dropdown-a hover olun solduqda menüni açıq saxla
        dropdown_window.bind("<Enter>", lambda e: self.cancel_dropdown_close())
        dropdown_window.bind("<Leave>", lambda e: self.schedule_dropdown_close())
        dropdown_frame.bind("<Enter>", lambda e: self.cancel_dropdown_close())
        dropdown_frame.bind("<Leave>", lambda e: self.schedule_dropdown_close())
        
        # Pəncərəni göstər
        dropdown_window.deiconify()
        dropdown_window.lift()
        dropdown_window.focus_force()
        
        # Ana pəncərə hərəkət etdikdə dropdown menyunun mövqeyini yenilə
        def on_window_move(event=None):
            if self.admin_dropdown_menu and self.admin_dropdown_menu.winfo_exists():
                try:
                    # Button mövqeyi (screen koordinatları - mütləq)
                    self.admin_panel_button.update_idletasks()
                    root_window.update_idletasks()
                    
                    button_x = self.admin_panel_button.winfo_rootx()
                    button_y = self.admin_panel_button.winfo_rooty() + self.admin_panel_button.winfo_height()
                    button_width = self.admin_panel_button.winfo_width()
                    
                    # Pəncərə ölçüləri
                    dropdown_frame.update_idletasks()
                    window_width = dropdown_frame.winfo_reqwidth()
                    window_height = dropdown_frame.winfo_reqheight()
                    
                    # Button-un mərkəzindən dropdown-un soluna
                    centered_x = button_x + (button_width // 2) - (window_width // 2)
                    
                    # Çox ekranlı konfiqurasiya üçün ekran sərhədlərini tap
                    try:
                        primary_screen_width = root_window.winfo_screenwidth()
                        
                        if button_x >= 0 and button_x < primary_screen_width:
                            screen_left = 0
                            screen_right = primary_screen_width
                        elif button_x < 0:
                            screen_left = button_x - 1000
                            screen_right = 0
                        else:
                            screen_left = primary_screen_width
                            screen_right = button_x + window_width + 1000
                        
                        # Ekrandan kənara çıxmaması üçün yoxla
                        if centered_x + window_width > screen_right:
                            centered_x = screen_right - window_width - 5
                        if centered_x < screen_left:
                            centered_x = screen_left + 5
                    except:
                        screen_width = root_window.winfo_screenwidth()
                        if centered_x + window_width > screen_width:
                            centered_x = screen_width - window_width - 5
                        if centered_x < 0:
                            centered_x = 5
                    
                    # Y koordinatı
                    screen_height = root_window.winfo_screenheight()
                    if button_y + window_height > screen_height:
                        button_y = self.admin_panel_button.winfo_rooty() - window_height
                    if button_y < 0:
                        button_y = 5
                    
                    # Pəncərəni yenilə
                    dropdown_window.geometry(f'{window_width}x{window_height}+{centered_x}+{button_y}')
                except Exception as e:
                    print(f"DEBUG: Dropdown mövqeyi yenilənərkən xəta: {e}")
        
        # Ana pəncərənin hərəkət event-lərini dinlə
        root_window.bind("<Configure>", on_window_move)
        
        # Dropdown menyu bağlandıqda event listener-i sil
        def cleanup_on_destroy():
            try:
                root_window.unbind("<Configure>")
            except:
                pass
        
        dropdown_window.protocol("WM_DELETE_WINDOW", cleanup_on_destroy)
        
        self.admin_dropdown_menu = dropdown_window
    
    def close_admin_dropdown(self):
        """Admin panel dropdown menüni bağlayır"""
        if self.admin_dropdown_menu:
            # Ana pəncərədən event listener-i sil
            try:
                root_window = self.winfo_toplevel()
                root_window.unbind("<Configure>")
            except:
                pass
            
            self.admin_dropdown_menu.destroy()
            self.admin_dropdown_menu = None
            if self.dropdown_close_job:
                self.after_cancel(self.dropdown_close_job)
                self.dropdown_close_job = None
    
    def schedule_dropdown_close(self):
        """Dropdown menüni bağlamağı planlaşdırır"""
        if self.dropdown_close_job:
            self.after_cancel(self.dropdown_close_job)
        self.dropdown_close_job = self.after(200, self.close_admin_dropdown)
    
    def cancel_dropdown_close(self):
        """Dropdown menünün bağlanmasını ləğv edir"""
        if self.dropdown_close_job:
            self.after_cancel(self.dropdown_close_job)
            self.dropdown_close_job = None
    
    def on_admin_panel_leave(self, event):
        """Admin panel dropdown-dan çıxdıqda menüni bağlayır"""
        # İstifadəçi düymədən çıxdıqda dropdown-ı bağla (dropdown-da deyilsə)
        if self.admin_dropdown_menu is not None:
            # Kursorun dropdown-da olło olub-olmadığını yoxla
            try:
                x = self.winfo_pointerx()
                y = self.winfo_pointery()
                if not self._is_cursor_over_widget(self.admin_dropdown_menu, x, y):
                    self.schedule_dropdown_close()
            except:
                self.schedule_dropdown_close()
    
    def _is_cursor_over_widget(self, widget, x, y):
        """Kursorun widget üzərində olło olub-olmadığını yoxlayır"""
        try:
            widget_x = widget.winfo_x()
            widget_y = widget.winfo_y()
            widget_width = widget.winfo_width()
            widget_height = widget.winfo_height()
            
            # Ana pəncərənin koordinatlarını nəzərə al
            root_x = widget.winfo_rootx()
            root_y = widget.winfo_rooty()
            
            return (root_x <= x <= root_x + widget_width and 
                    root_y <= y <= root_y + widget_height)
        except:
            return False

    def start_navbar_animations(self):
        """Səliqəli animasiyaları başladır"""
        self.navbar_animation_running = False  # Animasiyalar deaktivdir (sarı fondan qurtarmaq üçün)
        
        # Bildirişlər düyməsi üçün subtle pulse effekti - deaktivdir
        # self.animate_notifications_pulse()
    
    def animate_notifications_pulse(self):
        """Bildirişlər düyməsi subtle pulse effekti - artıq deaktivdir (sarı fondan qurtarmaq üçün)"""
        # Pulse effekti deaktiv edildi - artıq sarı fon olmayacaq
        return
        
        # Aşağıdakı kod səhv üçün comment edildi - sarı arxa planı əvəzləyir
        if not hasattr(self, 'navbar_animation_running') or not self.navbar_animation_running:
            return
            
        current_time = time.time()
        pulse_intensity = abs(math.sin(current_time * 1.5)) * 0.1 + 0.9
        
        # Rəng dəyişikliyi - daha subtle
        r = int(243 * pulse_intensity)
        g = int(156 * pulse_intensity)
        b = int(18 * pulse_intensity)
        
        try:
            self.notifications_button.configure(bg=f'#{r:02x}{g:02x}{b:02x}')
        except:
            pass
        
        # Növbəti frame - daha yavaş
        self.after(150, self.animate_notifications_pulse)
        
    def setup_left_panel(self):
        """Sol paneli yaradır"""
        # Ana Səhifə və Profil düymələri yuxarıya köçürüldü, burada yalnız digər funksiyalar qalır
        
        # Manual refresh düyməsi artıq navbar-dadır

        # Realtime status göstəricisi
        self.realtime_status_label = ttk.Label(self.left_frame, text="Realtime aktiv", style="Sidebar.TLabel", font=(self.main_font, 9))
        self.realtime_status_label.pack(pady=(0, 2))
        
        # Update status göstəricisi
        self.update_status_label = ttk.Label(self.left_frame, text="Sistem hazırdır", style="Sidebar.TLabel", font=(self.main_font, 9))
        self.update_status_label.pack(pady=(0, 2))

        if self.is_admin:
            # Admin düymələri navbar dropdown-dadır, burada yalnız işçilər paneli
            pass

        # İşçilər bölməsi
        try:
            self.employee_frame_bg = self.left_frame.cget('bg')
        except:
            self.employee_frame_bg = '#ffffff'
        
        # Axtarış və filtr panelləri (başlanğıcda gizli)
        self.search_panel = None
        self.filter_panel = None
        
        # Admin üçün icon düymələri - frame-in üstündə
        try:
            bg_color = self.left_frame.cget('bg')
        except:
            bg_color = '#ffffff'
        administrative_button_frame = tk.Frame(self.left_frame, bg=bg_color)
        administrative_button_frame.pack(fill='x', pady=(0, 1), padx=5)  # Sağ və sol 5px boşluq
        
        # Frame-i ortalamaq üçün wrapper - listbox-u uzatmaq üçün expand=True
        employee_wrapper = tk.Frame(self.left_frame, bg=bg_color)
        employee_wrapper.pack(fill='both', expand=True, pady=(0, 2))   # expand=True - listbox-u uzatmaq üçün
        
        # Sol kiçik spacer - silindi, çünki sola sıxlaşdırmaq lazımdır
        # left_frame_spacer = tk.Frame(employee_wrapper, bg=bg_color, width=2)
        # left_frame_spacer.pack(side='left')

        # İşçilər frame - daha gözəl görünüş üçün
        employee_frame = tb.LabelFrame(employee_wrapper, text="İşçilər", bootstyle="secondary")
        employee_frame.pack(side='left', fill='both', expand=True, padx=5)   # Sağ və sol 5px boşluq, expand=True
        # Frame-in görünüşünü yaxşılaşdır
        try:
            employee_frame.configure(relief='flat', borderwidth=1)
        except:
            pass
        
        # Sağ spacer – silindi, çünki sola sıxlaşdırmaq lazımdır
        # right_frame_spacer = tk.Frame(employee_wrapper, bg=bg_color, width=2)
        # right_frame_spacer.pack(side='left')
        
        # Edit və Delete funksiyalarını import edək
        try:
            from .employee_form_window import EmployeeFormWindow
            edit_form_available = True
        except:
            edit_form_available = False
            
        # İkonları ortalamaq üçün sol boş frame
        left_spacer = tk.Frame(administrative_button_frame, bg=bg_color)
        left_spacer.pack(side='left', expand=True, fill='x')
        
        # İkonları yan-yana yerləşdirmək üçün container - ortalanmış
        icon_container = tk.Frame(administrative_button_frame, bg=bg_color)
        icon_container.pack(side='left', expand=False, pady=2)  # Optimizasiya: boşluq azaldıldı
        
        # İkonları ortalamaq üçün sağ boş frame
        right_spacer = tk.Frame(administrative_button_frame, bg=bg_color)
        right_spacer.pack(side='left', expand=True, fill='x')
        
        # Axtarış və filtr ikonları - yalnız admin üçün
        if self.is_admin:
            try:
                from PIL import Image, ImageTk
                import os
                
                if getattr(sys, 'frozen', False):
                    base_path = sys._MEIPASS
                else:
                    base_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
                icon_base_path = os.path.join(base_path, 'src', 'icons', 'isci redakte iconlari')
                
                if not hasattr(self, 'icon_images'):
                    self.icon_images = {}
                
                # Search icon
                if 'search' not in self.icon_images:
                    search_img = Image.open(os.path.join(icon_base_path, 'search.png')).convert("RGBA")
                    search_img = search_img.resize((24, 24), Image.Resampling.LANCZOS)
                    self.icon_images['search'] = ImageTk.PhotoImage(search_img)
                
                # Filter icon
                if 'filter' not in self.icon_images:
                    filter_img = Image.open(os.path.join(icon_base_path, 'filter.png')).convert("RGBA")
                    filter_img = filter_img.resize((24, 24), Image.Resampling.LANCZOS)
                    self.icon_images['filter'] = ImageTk.PhotoImage(filter_img)
                
                # Search button
                self.search_button = tk.Label(
                    icon_container,
                    image=self.icon_images['search'],
                    bg=bg_color,
                    cursor='hand2',
                    bd=0
                )
                self.search_button.image = self.icon_images['search']
                self.search_button.pack(side='left', padx=(0, 3), pady=3)
                self.search_button.bind("<Button-1>", lambda e: self._toggle_search())
                
                # Filter button
                self.filter_button = tk.Label(
                    icon_container,
                    image=self.icon_images['filter'],
                    bg=bg_color,
                    cursor='hand2',
                    bd=0
                )
                self.filter_button.image = self.icon_images['filter']
                self.filter_button.pack(side='left', padx=(0, 3), pady=3)
                self.filter_button.bind("<Button-1>", lambda e: self._toggle_filter())
                
            except Exception as e:
                print(f"⚠️ Search/Filter iconları yüklənmədi: {e}")
                # Fallback - emoji istifadə et
                self.search_button = tk.Button(
                    icon_container,
                    text="🔍",
                    command=self._toggle_search,
                    bg=bg_color,
                    relief='flat',
                    font=(self.main_font, 11),
                    width=2,
                    cursor='hand2',
                    bd=0,
                    highlightthickness=0
                )
                self.search_button.pack(side='left', padx=(0, 3), pady=3)
                
                self.filter_button = tk.Button(
                    icon_container,
                    text="🔽",
                    command=self._toggle_filter,
                    bg=bg_color,
                    relief='flat',
                    font=(self.main_font, 11),
                    width=2,
                    cursor='hand2',
                    bd=0,
                    highlightthickness=0
                )
                self.filter_button.pack(side='left', padx=(0, 3), pady=3)
        else:
            # Adi istifadəçilər üçün search və filter ikonları yoxdur
            self.search_button = None
            self.filter_button = None
        
        # Admin üçün düymələr yaradılır amma başlanğıcda deaktivdir
        if edit_form_available and self.is_admin:
            # PNG iconları Pillow ilə yüklə
            try:
                from PIL import Image, ImageTk
                import os
                
                # Get the correct absolute path to icons directory
                if getattr(sys, 'frozen', False):
                    base_path = sys._MEIPASS
                else:
                    base_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
                icon_base_path = os.path.join(base_path, 'src', 'icons', 'isci redakte iconlari')
                frame_bg = administrative_button_frame.cget('bg')
                
                # Əgər icon_images yoxdursa yaradın
                if not hasattr(self, 'icon_images'):
                    self.icon_images = {}
                    print("🔧 DEBUG: icon_images dictionary yaradıldı")
                
                print(f"🔍 DEBUG: icon_images mövcud: {hasattr(self, 'icon_images')}, add mövcud: {'add' in self.icon_images if hasattr(self, 'icon_images') else 'N/A'}")
                
                # 1. Add icon (26x26) - Label kimi (həmişə aktiv)
                if 'add' not in self.icon_images:
                    print("🆕 DEBUG: Add icon yaradılır...")
                    add_img = Image.open(os.path.join(icon_base_path, 'add-user.png')).convert("RGBA")
                    add_img = add_img.resize((26, 26), Image.Resampling.LANCZOS)
                    self.icon_images['add'] = ImageTk.PhotoImage(add_img)
                else:
                    print("✅ DEBUG: Add icon artıq mövcuddur")
                add_icon = self.icon_images['add']
                
                self.add_employee_button = tk.Label(
                    icon_container, 
                    image=add_icon,
                    bg=frame_bg,
                    cursor='hand2',
                    bd=0
                )
                self.add_employee_button.image = add_icon  # Referansı saxla
                print(f"✅ DEBUG: Add icon yaradıldı: {self.icon_images['add'] is add_icon}")
                self.add_employee_button.pack(side='left', padx=(0, 3), pady=3)
                self.add_employee_button.bind("<Button-1>", lambda e: self.add_new_employee())
                
                # 2. Edit düyməsi (26x26) - Label kimi
                if 'edit' not in self.icon_images:
                    print("🆕 DEBUG: Edit icon yaradılır...")
                    edit_img = Image.open(os.path.join(icon_base_path, 'edit.png')).convert("RGBA")
                    edit_img = edit_img.resize((26, 26), Image.Resampling.LANCZOS)
                    self.icon_images['edit'] = ImageTk.PhotoImage(edit_img)
                edit_icon = self.icon_images['edit']
                
                self.edit_employee_button = tk.Label(
                    icon_container, 
                    image=edit_icon,
                    bg=frame_bg,
                    cursor='hand2',
                    bd=0
                )
                self.edit_employee_button.image = edit_icon  # Referansı saxla
                print(f"✅ DEBUG: Edit button yaradıldı, image: {edit_icon is not None}")
                self.edit_employee_button.pack(side='left', padx=(0, 3), pady=3)
                self.edit_employee_button.bind("<Button-1>", lambda e: self._handle_icon_click('edit'))
                
                # 3. Hide icon (26x26) - Label kimi
                if 'hide' not in self.icon_images:
                    print("🆕 DEBUG: Hide icon yaradılır...")
                    hide_img = Image.open(os.path.join(icon_base_path, 'hide.png')).convert("RGBA")
                    hide_img = hide_img.resize((26, 26), Image.Resampling.LANCZOS)
                    self.icon_images['hide'] = ImageTk.PhotoImage(hide_img)
                hide_icon = self.icon_images['hide']
                
                self.hide_employee_button = tk.Label(
                    icon_container, 
                    image=hide_icon,
                    bg=frame_bg,
                    cursor='hand2',
                    bd=0
                )
                self.hide_employee_button.image = hide_icon  # Referansı saxla
                print(f"✅ DEBUG: Hide button yaradıldı, image: {hide_icon is not None}")
                self.hide_employee_button.pack(side='left', padx=(0, 3), pady=3)
                self.hide_employee_button.bind("<Button-1>", lambda e: self._handle_icon_click('hide'))
                
                # 4. Delete düyməsi (26x26) - Label kimi
                if 'delete' not in self.icon_images:
                    print("🆕 DEBUG: Delete icon yaradılır...")
                    delete_img = Image.open(os.path.join(icon_base_path, 'delete.png')).convert("RGBA")
                    delete_img = delete_img.resize((26, 26), Image.Resampling.LANCZOS)
                    self.icon_images['delete'] = ImageTk.PhotoImage(delete_img)
                delete_icon = self.icon_images['delete']
                
                self.delete_employee_button = tk.Label(
                    icon_container, 
                    image=delete_icon,
                    bg=frame_bg,
                    cursor='hand2',
                    bd=0
                )
                self.delete_employee_button.image = delete_icon  # Referansı saxla
                print(f"✅ DEBUG: Delete button yaradıldı, image: {delete_icon is not None}")
                self.delete_employee_button.pack(side='left', padx=(0, 3), pady=3)
                self.delete_employee_button.bind("<Button-1>", lambda e: self._handle_icon_click('delete'))
                
            except Exception as e:
                print(f"⚠️ Pillow iconları yüklənmədi: {e}")
                # Fallback - emoji istifadə et
                try:
                    # Get correct absolute path for fallback icons
                    if getattr(sys, 'frozen', False):
                        fallback_base = sys._MEIPASS
                    else:
                        fallback_base = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
                    fallback_icon_path = os.path.join(fallback_base, 'src', 'icons', 'isci redakte iconlari')
                    
                    edit_icon = tk.PhotoImage(file=os.path.join(fallback_icon_path, 'edit.png'))
                    edit_icon = edit_icon.subsample(3, 3)  # Ölçüləri kiçildirik
                    self.edit_employee_button = tk.Button(
                        administrative_button_frame, 
                        image=edit_icon,
                        command=self.edit_selected_employee,
                        bg=administrative_button_frame.cget('bg'),
                        relief='flat',
                        width=30,
                        height=30,
                        state='disabled',
                        bd=0,
                        highlightthickness=0
                    )
                    self.edit_employee_button.image = edit_icon  # Referansı saxla
                    self.edit_employee_button.pack(side='left', padx=5)
                    
                    # Delete düyməsi
                    delete_icon = tk.PhotoImage(file=os.path.join(fallback_icon_path, 'delete.png'))
                    delete_icon = delete_icon.subsample(3, 3)
                    self.delete_employee_button = tk.Button(
                        administrative_button_frame, 
                        image=delete_icon,
                        command=self.delete_employee,
                        bg=administrative_button_frame.cget('bg'),
                        relief='flat',
                        width=30,
                        height=30,
                        state='disabled',
                        bd=0,
                        highlightthickness=0
                    )
                    self.delete_employee_button.image = delete_icon  # Referansı saxla
                    self.delete_employee_button.pack(side='left', padx=5)
                    
                    # Add düyməsi
                    add_icon = tk.PhotoImage(file=os.path.join(fallback_icon_path, 'add-user.png'))
                    add_icon = add_icon.subsample(3, 3)
                    add_button = tk.Button(
                        administrative_button_frame, 
                        image=add_icon,
                        command=self.add_new_employee,
                        bg=administrative_button_frame.cget('bg'),
                        relief='flat',
                        width=30,
                        height=30,
                        bd=0,
                        highlightthickness=0
                    )
                    add_button.image = add_icon
                    add_button.pack(side='left', padx=5)
                    
                    # Permanently delete düyməsi
                    self.permanently_delete_button = tk.Button(
                        administrative_button_frame,
                        text="🗑️",
                        command=self.permanently_delete_employee,
                        bg=administrative_button_frame.cget('bg'),
                        relief='flat',
                        width=30,
                        height=30,
                        state='disabled',
                        fg='black',
                        bd=0,
                        highlightthickness=0
                    )
                    self.permanently_delete_button.pack(side='left', padx=5)
                except Exception as e:
                    print(f"İcon yüklənərkən xəta: {e}")
                    logging.error(f"İcon yüklənərkən xəta: {e}")
                    # İcon yüklənmədiyi təqdirdə sadə düymələr istifadə edək
                    self.edit_employee_button = tk.Button(
                        administrative_button_frame,
                        text="✏️",
                        command=self.edit_selected_employee,
                        bg=administrative_button_frame.cget('bg'),
                        relief='flat',
                        font=(self.main_font, 11),
                        width=2,
                        state='disabled',
                        cursor='hand2',
                        bd=0,
                        highlightthickness=0
                    )
                    self.edit_employee_button.pack(side='left', padx=2, pady=2)
                    
                    self.delete_employee_button = tk.Button(
                        administrative_button_frame,
                        text="🗑️",
                        command=self.delete_employee,
                        bg=administrative_button_frame.cget('bg'),
                        relief='flat',
                        font=(self.main_font, 11),
                        width=2,
                        state='disabled',
                        cursor='hand2',
                        bd=0,
                        highlightthickness=0
                    )
                    self.delete_employee_button.pack(side='left', padx=2, pady=2)
                    
                    # Add düyməsi əlavə edək
                    add_button = tk.Button(
                        administrative_button_frame,
                        text="➕",
                        command=self.add_new_employee,
                        bg=administrative_button_frame.cget('bg'),
                        relief='flat',
                        font=(self.main_font, 11),
                        width=2,
                        cursor='hand2',
                        bd=0,
                        highlightthickness=0
                    )
                    add_button.pack(side='left', padx=2, pady=2)
                    
                    # Hide düyməsi
                    self.hide_employee_button = tk.Button(
                        administrative_button_frame,
                        text="👁️",
                        command=self.delete_employee,
                        bg=administrative_button_frame.cget('bg'),
                        relief='flat',
                        font=(self.main_font, 13),
                        width=3,
                        state='disabled',
                        cursor='hand2',
                        bd=0,
                        highlightthickness=0
                    )
                    self.hide_employee_button.pack(side='left', padx=3, pady=3)
        
        # Listbox frame - daha gözəl görünüş üçün
        listbox_frame = tb.Frame(employee_frame)
        listbox_frame.pack(expand=True, fill='both', pady=4, padx=4)  # Optimizasiya: boşluq azaldıldı
        # Frame-in görünüşünü yaxşılaşdır
        try:
            listbox_frame.configure(relief='flat')
        except:
            pass
        
        # Listbox-un görünüşünü yaxşılaşdır - daha modern və gözəl
        self.employee_listbox = tk.Listbox(
            listbox_frame, 
            font=(self.main_font, 10),  # Font ölçüsü azaldıldı - daha kompakt
            relief="flat", 
            highlightthickness=0,  # Border gizlədirildi - daha təmiz görünüş
            width=25,  # Eni azaldıldı (35-dən 25-ə)
            height=25,  # Hündürlüyü artırıldı - daha uzun
            bg='#ffffff',  # Ağ fon
            fg='#333333',  # Tünd boz mətn
            selectbackground='#ffffff',  # Ağ seçim fonu - gri highlight yoxdur
            selectforeground='#333333',  # Tünd boz seçilmiş mətn
            activestyle='none',  # Aktiv stil yoxdur - mouse hover highlight-ı bloklayır
            borderwidth=0,  # Border yoxdur
            highlightcolor='#ffffff',  # Ağ focus rəngi - highlight yoxdur
            cursor='hand2',  # Əl kursoru
            takefocus=False  # Focus almasın - avtomatik highlight-ı bloklayır
        )
        # Scrollbar gizlədirildi
        # vsb = ttk.Scrollbar(listbox_frame, orient="vertical", command=self.employee_listbox.yview)
        # self.employee_listbox.configure(yscrollcommand=vsb.set)
        # vsb.pack(side='right', fill='y', padx=(2, 0))
        self.employee_listbox.pack(side='left', expand=True, fill="both")
        
        # Scroll pozisyonunu saxla (Button-1 event-dən əvvəl)
        self._listbox_scroll_pos_before_click = None
        self._listbox_button1_pressed = False  # Button-1 basılıb-basılmadığını izlə
        self._listbox_last_click_time = 0  # Son klik vaxtı (avtomatik seçimi qarşısını almaq üçün)
        self._last_valid_selection = None  # Son etibarlı seçim (avtomatik seçim bloklandıqda bərpa etmək üçün)
        import time
        
        def on_listbox_button1(e):
            """Button-1 event handler - scroll pozisyonunu saxla"""
            try:
                if hasattr(self, 'employee_listbox'):
                    self._listbox_button1_pressed = True  # Button-1 basıldı
                    self._listbox_last_click_time = time.time()  # Son klik vaxtını qeyd et
                    self._listbox_scroll_pos_before_click = self.employee_listbox.index("@0,0")
                    
                    # Klik edilən item-i tap və etibarlı seçim kimi saxla
                    try:
                        click_y = e.y
                        click_index = self.employee_listbox.nearest(click_y)
                        self._last_valid_selection = click_index
                        print(f"🔍 [DEBUG] Button-1 event: scroll pozisyonu saxlandı: {self._listbox_scroll_pos_before_click}, click_index={click_index}")
                    except:
                        print(f"🔍 [DEBUG] Button-1 event: scroll pozisyonu saxlandı: {self._listbox_scroll_pos_before_click}")
            except Exception as ex:
                print(f"🔍 [DEBUG] Button-1 event: scroll pozisyonu saxlanma xətası: {ex}")
        
        def on_listbox_button1_release(e):
            """Button-1 release event handler"""
            # Button-1 buraxıldı, amma qısa müddət ərzində seçim dəyişikliyinə icazə ver (200ms)
            # Bu, normal klik davranışını təmin edir
            self.after(200, lambda: setattr(self, '_listbox_button1_pressed', False))
        
        def on_listbox_motion(e):
            """Mouse motion event handler - avtomatik seçimi və highlight-ı tam bloklayır"""
            # Yalnız Button-1 basılı olduqda və ya yaxın zamanda basıldıqda seçimə icazə ver
            current_time = time.time()
            time_since_click = current_time - self._listbox_last_click_time
            allow_selection = self._listbox_button1_pressed or time_since_click < 0.3  # 300ms icazə ver
            
            if not allow_selection:
                # Button-1 basılmadıqda və ya çox vaxt keçibsə, avtomatik seçimi və highlight-ı tam blokla
                try:
                    # Mouse altındakı item index-i
                    mouse_y = e.y
                    mouse_index = self.employee_listbox.nearest(mouse_y)
                    
                    # Cari seçimi yoxla
                    current_selection = self.employee_listbox.curselection()
                    
                    # Avtomatik selection-ı tam blokla - həmişə əvvəlki seçimi saxla
                    self.employee_listbox.unbind("<<ListboxSelect>>")
                    if self._last_valid_selection is not None:
                        # Əvvəlki seçimi bərpa et
                        self.employee_listbox.selection_clear(0, tb.END)
                        self.employee_listbox.selection_set(self._last_valid_selection)
                    else:
                        # Əgər etibarlı seçim yoxdursa, cari seçimi saxla
                        if current_selection:
                            self.employee_listbox.selection_clear(0, tb.END)
                            self.employee_listbox.selection_set(current_selection[0])
                        else:
                            # Heç bir seçim yoxdursa, seçimi tam təmizlə
                            self.employee_listbox.selection_clear(0, tb.END)
                    self.employee_listbox.bind("<<ListboxSelect>>", self.on_employee_select)
                    
                    # Focus-u blokla - bu, gri highlight-ı qarşısını alır
                    try:
                        parent_widget = self.employee_listbox.master
                        if parent_widget:
                            parent_widget.focus_set()
                    except:
                        pass
                        
                except Exception as ex:
                    print(f"🔍 [DEBUG] Motion handler xətası: {ex}")
                
                return "break"  # Event-i dayandır, avtomatik seçimi və highlight-ı tam blokla
            # Button-1 basılıdırsa və ya yaxın zamanda basıldıqsa, normal davranışa icazə ver
        
        def on_listbox_key(e):
            """Keyboard event handler - klaviatura ilə gezinməni bloklayır"""
            # Arrow keys və digər navigation keys-i blokla
            if e.keysym in ['Up', 'Down', 'Prior', 'Next', 'Home', 'End']:
                # Yalnız Button-1 basılı olduqda və ya yaxın zamanda basıldıqda icazə ver
                current_time = time.time()
                time_since_click = current_time - self._listbox_last_click_time
                allow_selection = self._listbox_button1_pressed or time_since_click < 0.3
                
                if not allow_selection:
                    print(f"🔍 [DEBUG] Keyboard navigation bloklandı: {e.keysym}")
                    return "break"  # Keyboard navigation-u blokla
        
        # Button-1 event-dən əvvəl scroll pozisyonunu saxla
        # Motion event-i Button-1-dən ƏVVƏL bind et ki, avtomatik seçim bloklansın
        self.employee_listbox.bind("<Motion>", on_listbox_motion, add=True)  # Mouse motion event-i əlavə et (ƏVVƏL)
        self.employee_listbox.bind("<Button-1>", on_listbox_button1, add=True)
        self.employee_listbox.bind("<ButtonRelease-1>", on_listbox_button1_release, add=True)
        self.employee_listbox.bind("<Key>", on_listbox_key, add=True)  # Keyboard event-i əlavə et
        
        # <<ListboxSelect>> event-ini bloklamaq üçün wrapper funksiya
        def on_listbox_select_wrapper(event):
            """<<ListboxSelect>> event wrapper - avtomatik seçimi bloklayır"""
            # Yalnız Button-1 basıldıqda və ya yaxın zamanda basıldıqda icazə ver
            current_time = time.time()
            time_since_click = current_time - self._listbox_last_click_time
            allow_selection = self._listbox_button1_pressed or time_since_click < 0.5  # 500ms icazə ver
            
            if not allow_selection:
                # Avtomatik seçim bloklandı - əvvəlki seçimi bərpa et
                print(f"🔍 [DEBUG] <<ListboxSelect>>: Avtomatik seçim bloklandı (time_since_click={time_since_click:.3f}s)")
                try:
                    if self._last_valid_selection is not None:
                        self.employee_listbox.selection_clear(0, tb.END)
                        self.employee_listbox.selection_set(self._last_valid_selection)
                except:
                    pass
                return  # Event-i blokla
            
            # Button-1 basıldıqda və ya yaxın zamanda basıldıqsa, normal handler-i çağır
            self.on_employee_select(event)
        
        self.employee_listbox.bind("<<ListboxSelect>>", on_listbox_select_wrapper)
        
        # Hover effekti üçün event binding
        def on_enter_listbox(e):
            """Listbox-a daxil olduqda - cursor dəyişir, amma focus və highlight yoxdur"""
            self.employee_listbox.config(cursor='hand2')
            # Focus-u blokla - bu, gri highlight-ı qarşısını alır
            try:
                parent_widget = self.employee_listbox.master
                if parent_widget:
                    parent_widget.focus_set()
            except:
                pass
        
        def on_leave_listbox(e):
            """Listbox-dan çıxdıqda"""
            self.employee_listbox.config(cursor='')
        
        self.employee_listbox.bind('<Enter>', on_enter_listbox)
        self.employee_listbox.bind('<Leave>', on_leave_listbox)
        
        # Realtime status yeniləmə timer-i (realtime üçün əlavə edildi)
        self.update_realtime_status()

    def create_views(self):
        self.views = {}
        
        # Dashboard calendar view
        self.views['dashboard'] = DashboardCalendarFrame(self.right_frame, main_app_ref=self)
        self.views['dashboard'].place(in_=self.right_frame, x=0, y=0, relwidth=1, relheight=1)
        
        self.views['employee_details'] = EmployeeDetailFrame(self.right_frame, self)
        self.views['employee_details'].place(in_=self.right_frame, x=0, y=0, relwidth=1, relheight=1)

    def show_view(self, view_name):
        logging.info(f"show_view çağırıldı: {view_name}")
        # Debug print mətnləri söndürüldü
        # print(f"DEBUG: show_view called: {view_name}")
        
        # Mövcud views-ləri yoxla
        # print(f"DEBUG: Available views: {list(self.views.keys()) if hasattr(self, 'views') else 'no views'}")
        
        # Təhlükəsizlik yoxlaması: Adi istifadəçi yalnız dashboard və employee_details görünüşlərini görə bilər
        if self.current_user['role'].strip() != 'admin' and view_name not in ['dashboard', 'employee_details']:
            logging.warning(f"Adi istifadəçi {view_name} görünüşünü görə bilməz")
            # print(f"DEBUG: Regular user cannot access {view_name} view")
            view_name = 'dashboard'
            # print(f"DEBUG: View changed to dashboard")
        
        if view_name == 'dashboard':
            # Dashboard load_data-nı asinxron çağır (proqramın daha tez açılması üçün)
            if hasattr(self.views['dashboard'], 'load_data'):
                logging.info("Dashboard load_data asinxron çağırılır...")
                # load_data-nı 200ms sonra çağır ki, UI tam yüklənsin
                self.after(200, lambda: self.views['dashboard'].load_data() if hasattr(self, 'views') and 'dashboard' in self.views else None)
            
            # Dashboard üçün yalnız işçi siyahısını yüklə (vacation məlumatları dashboard özü yükləyir)
            if not hasattr(self, '_dashboard_data_loaded') or not self._dashboard_data_loaded:
                if not self.data or all(not emp.get('goturulen_icazeler') for emp in self.data.values()):
                    # Yalnız işçi siyahısını yüklə
                    self.after(300, lambda: self._load_employee_list_only() if hasattr(self, 'refresh_employee_list') else None)
                    self.after(400, lambda: self.refresh_employee_list() if hasattr(self, 'refresh_employee_list') else None)
                    self._dashboard_data_loaded = True
        elif view_name == 'employee_details':
            # Current view-u əvvəlcə təyin et ki, load_and_refresh_data düzgün işləsin
            self.current_view = view_name
            print(f"DEBUG: Current view updated (before load): {self.current_view}")
            
            # Employee details üçün tam məlumatları yüklə (vacation məlumatları lazımdır)
            # _full_data_loaded flag-ini yoxlamaq lazım deyil - hər dəfə yeniləmək lazımdır
            # Scroll pozisyonunu korumaq üçün cari seçimi saxla
            _, current_selection = self.get_selected_employee_name() if hasattr(self, 'get_selected_employee_name') else (None, None)
            logging.info("Employee details üçün tam məlumatlar yüklənir...")
            self.after(100, lambda sel=current_selection: self.load_and_refresh_data(load_full_data=True, selection_to_keep=sel) if hasattr(self, 'load_and_refresh_data') else None)
            # Flag-i silmək lazım deyil - hər dəfə yeniləmək lazımdır
            # self._full_data_loaded = True
        
        frame = self.views.get(view_name)
        # print(f"DEBUG: Frame found: {frame}")
        # print(f"DEBUG: Frame type: {type(frame) if frame else 'None'}")
        
        if frame:
            # Frame-in mövcudluğunu yoxla
            try:
                frame_exists = frame.winfo_exists()
                print(f"DEBUG: Frame winfo_exists: {frame_exists}")
            except Exception as e:
                print(f"DEBUG: Frame winfo_exists yoxlanıla bilmədi: {e}")
                frame_exists = False
            
            if frame_exists:
                logging.info(f"Frame tapıldı, tkraise() çağırılır...")
                print(f"DEBUG: Frame found, calling tkraise()...")
                
                try:
                    frame.tkraise()
                    logging.info(f"Frame tkraise() tamamlandı")
                    print(f"DEBUG: Frame tkraise() completed")
                    
                    # Current view-u yenilə (əgər əvvəlcə təyin olunmayıbsa)
                    if not hasattr(self, 'current_view') or self.current_view != view_name:
                        self.current_view = view_name
                    print(f"DEBUG: Current view updated: {self.current_view}")
                    
                    # Frame-in görünürlüyünü yoxla
                    try:
                        frame_visible = frame.winfo_viewable()
                        print(f"DEBUG: Frame visible: {frame_visible}")
                    except Exception as e:
                        print(f"DEBUG: Frame visibility check failed: {e}")
                        
                except Exception as e:
                    logging.error(f"Frame tkraise() xətası: {e}")
                    print(f"DEBUG: Frame tkraise() xətası: {e}")
                    import traceback
                    print(f"DEBUG: Traceback: {traceback.format_exc()}")
            else:
                logging.error(f"Frame mövcud deyil: {view_name}")
                print(f"DEBUG: Frame mövcud deyil: {view_name}")
        else:
            logging.error(f"Frame tapılmadı: {view_name}")
            print(f"DEBUG: Frame tapılmadı: {view_name}")
            print(f"DEBUG: Mövcud views: {list(self.views.keys())}")

    def _handle_edit_click(self):
        """Edit düyməsi üçün helper - seçilmiş işçini yoxlayır"""
        _, selected_name = self.get_selected_employee_name()
        if selected_name:
            self.edit_selected_employee()
        else:
            print("ℹ️ İşçi seçilməyib")
    
    def _handle_delete_click(self):
        """Delete düyməsi üçün helper - seçilmiş işçini yoxlayır"""
        _, selected_name = self.get_selected_employee_name()
        if selected_name:
            self.delete_employee()
        else:
            print("ℹ️ İşçi seçilməyib")
    
    def _handle_icon_click(self, icon_type):
        """Iconların tıklamasını idarə edir - işçi seçilmədikdə xəbərdarlıq göstərir"""
        _, selected_name = self.get_selected_employee_name()
        
        if not selected_name:
            messagebox.showwarning("Xəbərdarlıq", "Əvvəlcə işçi seçin!")
            return
        
        if icon_type == 'edit':
            self.edit_selected_employee()
        elif icon_type == 'delete':
            self.permanently_delete_employee()
        elif icon_type == 'hide':
            self.delete_employee()
    
    def on_employee_select(self, event=None):
        import traceback
        
        # Debug: Çağırılan yeri və event məlumatlarını logla
        caller_stack = ''.join(traceback.format_stack()[-3:-1])
        event_info = f"event={event}, widget={getattr(event, 'widget', None) if event else None}"
        print(f"🔍 [DEBUG] on_employee_select çağırıldı: {event_info}")
        print(f"🔍 [DEBUG] Çağırılan yer:\n{caller_stack}")
        
        # Avtomatik gezinmə yoxlaması artıq wrapper-də edilir, burada yalnız proqramatik seçimləri yoxla
        # Proqramatik seçimləri yoxla (event None və ya widget fərqli ola bilər)
        is_programmatic = (event is None) or (hasattr(event, 'widget') and event.widget != self.employee_listbox)
        
        # Wrapper-dən gələn event-lər artıq yoxlanılıb, burada yalnız proqramatik seçimləri icazə ver
        if not is_programmatic:
            # Normal event (wrapper-dən gəlir), davam et
            pass
        
        # Scroll pozisyonunu logla və saxla (show_view çağrıldıqdan sonra geri yükləmək üçün)
        # Button-1 event-dən əvvəl saxlanmış scroll pozisyonunu istifadə et
        scroll_pos_to_restore = getattr(self, '_listbox_scroll_pos_before_click', None)
        try:
            if hasattr(self, 'employee_listbox'):
                current_selection = self.employee_listbox.curselection()
                if current_selection:
                    selected_idx = current_selection[0]
                    try:
                        first_visible = self.employee_listbox.index("@0,0")
                        last_visible = self.employee_listbox.index("@0,{}".format(self.employee_listbox.winfo_height()))
                        # Əgər Button-1 event-dən əvvəl scroll pozisyonu yoxdursa, cari pozisyonu istifadə et
                        if scroll_pos_to_restore is None:
                            scroll_pos_to_restore = first_visible
                        print(f"🔍 [DEBUG] on_employee_select: selected_idx={selected_idx}, first_visible={first_visible}, last_visible={last_visible}, görünür={first_visible <= selected_idx <= last_visible}, scroll_pos_to_restore={scroll_pos_to_restore} (Button-1-dən: {getattr(self, '_listbox_scroll_pos_before_click', None)})")
                    except Exception as e:
                        print(f"🔍 [DEBUG] on_employee_select: scroll pozisyonu alına bilmədi: {e}")
        except Exception as e:
            print(f"🔍 [DEBUG] on_employee_select: scroll pozisyonu xətası: {e}")
        
        # Yalnızca event-in mənbəyi listbox-dursa və seçim varsa işləsin
        if event and event.widget != self.employee_listbox:
            logging.debug("Event widget employee_listbox deyil, çıxırıq.")
            print(f"🔍 [DEBUG] Event widget employee_listbox deyil, çıxırıq. widget={event.widget}")
            return
        
        # Cari seçimi etibarlı seçim kimi saxla (avtomatik seçim bloklandıqda bərpa etmək üçün)
        if hasattr(self, 'employee_listbox') and self.employee_listbox.curselection():
            current_idx = self.employee_listbox.curselection()[0]
            self._last_valid_selection = current_idx
        
        # Əgər şöbə başlığı seçilibsə, aç/yığ
        if hasattr(self, 'employee_listbox') and self.employee_listbox.curselection():
            index = self.employee_listbox.curselection()[0]
            item_text = self.employee_listbox.get(index)
            # Şöbə başlığı yoxlaması - ▶ və ya ▼ ilə başlayan
            if item_text.strip().startswith("▶") or item_text.strip().startswith("▼"):
                # Şöbə adını çıxar
                dept_name = item_text.replace("▶", "").replace("▼", "").strip()
                dept_name = dept_name.strip()
                
                # Şöbə görünürlüyünü dəyişdir
                if dept_name in self.department_visibility:
                    self.department_visibility[dept_name] = not self.department_visibility[dept_name]
                else:
                    self.department_visibility[dept_name] = True  # İlk dəfə açılır
                
                # List-i yenilə - cari seçimi saxla (scroll pozisyonunu koru)
                _, current_selection = self.get_selected_employee_name()
                self.refresh_employee_list(selection_to_keep=current_selection)
                return
            
        if not self.employee_listbox.curselection():
            logging.debug("employee_listbox-da heç bir seçim yoxdur, heç bir səhifə dəyişmirik.")
            print("DEBUG: employee_listbox-da heç bir seçim yoxdur, heç bir səhifə dəyişmirik.")
            return
        
        # Açıq məzuniyyət sorğusu pəncərələrini yoxla və xəbərdarlıq et
        if self._has_open_vacation_windows():
            result = messagebox.askyesno(
                "Açıq Məzuniyyət Sorğusu", 
                "Açıq məzuniyyət sorğusu pəncərəsi var. İşçi dəyişdiriləndə bu pəncərə bağlanacaq. Davam etmək istəyirsiniz?",
                icon='warning'
            )
            if not result:
                return
            # İstifadəçi razıdırsa, pəncərələri bağla
            self._close_vacation_windows()
            
        # Təhlükəsizlik yoxlaması: Adi istifadəçi yalnız öz məlumatını seçə bilər
        _, selected_name = self.get_selected_employee_name()
        logging.debug(f"Seçilmiş işçi adı: {selected_name}")
        print(f"👤 DEBUG: Seçilmiş işçi adı: {selected_name}")
        
        if not selected_name:
            logging.debug("Seçilmiş işçi adı tapılmadı, çıxırıq.")
            print("❌ DEBUG: Seçilmiş işçi adı tapılmadı, çıxırıq.")
            return
            
        # Adi istifadəçi üçün yalnız öz məlumatını seçə bilər
        if self.current_user['role'].strip() != 'admin':
            current_user_name = self.current_user.get('name', '')
            if selected_name != current_user_name:
                logging.warning(f"Adi istifadəçi başqa işçinin məlumatını seçməyə çalışır: {selected_name}")
                print(f"⚠️ DEBUG: Adi istifadəçi başqa işçinin məlumatını seçməyə çalışır: {selected_name}")
                return
        
        # Admin düymələri həmişə aktivdir (görünüş dəyişmir, sadəcə xəbərdarlıq verir)
        
        # İşçi seçildikdə real vaxtda məlumatları yeniləmirik - performans üçün
        # logging.info("İşçi seçildi - real vaxtda məlumatlar yenilənir...")
        # self.data = database.load_data_for_user(self.current_user)
        
        info = self.data.get(selected_name)
        if not info:
            logging.debug("İşçi məlumatı tapılmadı, çıxırıq.")
            print("❌ DEBUG: İşçi məlumatı tapılmadı, çıxırıq.")
            return
        
        # info string və ya boolean ola bilər, yoxlayırıq
        if isinstance(info, (str, bool)):
            logging.debug(f"İşçi məlumatı dictionary deyil: {type(info)}")
            print(f"⚠️ DEBUG: İşçi məlumatı dictionary deyil: {type(info)}")
            return
            
        info['name'] = selected_name
        logging.info(f"Employee details update_data çağırılır: {selected_name}")
        print(f"📋 DEBUG: Employee details update_data çağırılır: {selected_name}")
        self.views['employee_details'].update_data(info, self.current_user)
        
        # Təhlükəsizlik yoxlaması: Adi istifadəçi yalnız öz məlumatını görə bilər
        # show_view çağrıldığında load_and_refresh_data çağrılır, bu da refresh_employee_list çağırır
        # Bu, otomatik gezinməyə səbəb olmaması üçün event'i geçici olaraq devre dışı bıraktıq
        print(f"🔍 [DEBUG] on_employee_select: show_view çağrılmadan əvvəl current_view={getattr(self, 'current_view', None)}")
        if self.current_user['role'].strip() == 'admin':
            logging.info("Admin üçün employee_details görünüşü göstərilir")
            print("👑 DEBUG: Admin üçün employee_details görünüşü göstərilir")
            self.show_view('employee_details')
        else:
            # Adi istifadəçi üçün öz məlumatını employee_details görünüşündə göstəririk
            logging.info("Adi istifadəçi üçün employee_details görünüşü göstərilir")
            print("👤 DEBUG: Adi istifadəçi üçün employee_details görünüşü göstərilir")
            self.show_view('employee_details')
        
        print(f"🔍 [DEBUG] on_employee_select: show_view çağrıldıqdan sonra current_view={getattr(self, 'current_view', None)}")
        
        # Scroll pozisyonunu geri yüklə (show_view içində refresh_employee_list çağrıldığı üçün scroll pozisyonu dəyişə bilər)
        if scroll_pos_to_restore is not None:
            try:
                # Qısa gecikmə əlavə et ki refresh_employee_list bitə bilsin
                def restore_scroll():
                    try:
                        if hasattr(self, 'employee_listbox'):
                            current_selection = self.employee_listbox.curselection()
                            if current_selection:
                                selected_idx = current_selection[0]
                                try:
                                    first_visible = self.employee_listbox.index("@0,0")
                                    last_visible = self.employee_listbox.index("@0,{}".format(self.employee_listbox.winfo_height()))
                                    # Əgər seçim görünürdürsə və scroll pozisyonu dəyişibsə, geri yüklə
                                    if first_visible <= selected_idx <= last_visible:
                                        if first_visible != scroll_pos_to_restore:
                                            print(f"🔍 [DEBUG] on_employee_select: Scroll pozisyonu geri yüklənir: {scroll_pos_to_restore} (cari: {first_visible})")
                                            self.employee_listbox.see(scroll_pos_to_restore)
                                            try:
                                                restored_first_visible = self.employee_listbox.index("@0,0")
                                                print(f"🔍 [DEBUG] on_employee_select: Scroll pozisyonu geri yükləndi: {restored_first_visible}")
                                            except:
                                                pass
                                        else:
                                            print(f"🔍 [DEBUG] on_employee_select: Scroll pozisyonu dəyişməyib: {first_visible}")
                                    else:
                                        print(f"🔍 [DEBUG] on_employee_select: Seçim görünür deyil, scroll pozisyonu geri yüklənmir: selected_idx={selected_idx}, first_visible={first_visible}, last_visible={last_visible}")
                                except Exception as e:
                                    print(f"🔍 [DEBUG] on_employee_select: Scroll pozisyonu geri yükləmə xətası: {e}")
                    except Exception as e:
                        print(f"🔍 [DEBUG] on_employee_select: restore_scroll xətası: {e}")
                
                # 200ms gecikmə ilə scroll pozisyonunu geri yüklə
                self.after(200, restore_scroll)
            except Exception as e:
                print(f"🔍 [DEBUG] on_employee_select: Scroll pozisyonu geri yükləmə planlama xətası: {e}")
        
        print(f"✅ DEBUG: on_employee_select tamamlandı - {selected_name}")

    def show_employee_by_id(self, employee_id):
        logging.info(f"=== show_employee_by_id başladı: {employee_id} ===")
        print(f"🔄 DEBUG: show_employee_by_id başladı: {employee_id}")
        
        # Açıq məzuniyyət sorğusu pəncərələrini yoxla və xəbərdarlıq et
        if self._has_open_vacation_windows():
            result = messagebox.askyesno(
                "Açıq Məzuniyyət Sorğusu", 
                "Açıq məzuniyyət sorğusu pəncərəsi var. İşçi dəyişdiriləndə bu pəncərə bağlanacaq. Davam etmək istəyirsiniz?",
                icon='warning'
            )
            if not result:
                return
            # İstifadəçi razıdırsa, pəncərələri bağla
            self._close_vacation_windows()
        
        # Təhlükəsizlik yoxlaması: Adi istifadəçi yalnız öz məlumatını görə bilər
        if self.current_user['role'].strip() != 'admin':
            # Adi istifadəçi üçün yalnız öz məlumatını göstərə bilər
            current_user_id = self.current_user.get('id')
            logging.info(f"Adi istifadəçi - current_user_id: {current_user_id}, employee_id: {employee_id}")
            print(f"🔒 DEBUG: Adi istifadəçi - current_user_id: {current_user_id}, employee_id: {employee_id}")
            if employee_id != current_user_id:
                logging.warning(f"Adi istifadəçi başqa işçinin məlumatını görə bilməz: {employee_id}")
                print(f"⚠️ DEBUG: Adi istifadəçi başqa işçinin məlumatını görə bilməz: {employee_id}")
                return
        
        # Real vaxtda məlumatları yeniləmirik - performans üçün
        # logging.info("show_employee_by_id - real vaxtda məlumatlar yenilənir...")
        # self.data = database.load_data_for_user(self.current_user)
        
        target_name = None
        target_department = None
        logging.info(f"Data-dan employee_id {employee_id} axtarılır...")
        print(f"🔍 DEBUG: Data-dan employee_id {employee_id} axtarılır...")
        for name, data in self.data.items():
            if data.get('db_id') == employee_id:
                target_name = name
                target_department = data.get('department', 'Şöbə təyin edilməyib')
                logging.info(f"Tapılan target_name: {target_name}, şöbə: {target_department}")
                print(f"✅ DEBUG: Tapılan target_name: {target_name}, şöbə: {target_department}")
                break
                
        if not target_name:
            logging.error(f"employee_id {employee_id} üçün target_name tapılmadı")
            print(f"❌ DEBUG: employee_id {employee_id} üçün target_name tapılmadı")
            return

        # Təhlükəsizlik: Şöbə məlumatını yoxla
        if not target_department:
            target_department = 'Şöbə təyin edilməyib'
        
        # Qrupu aç (əgər bağlıdırsa)
        if not hasattr(self, 'department_visibility'):
            self.department_visibility = {}
        
        # İşçinin şöbəsi bağlıdırsa, aç
        if target_department in self.department_visibility:
            if not self.department_visibility[target_department]:
                logging.info(f"Şöbə '{target_department}' bağlıdır, açılır...")
                print(f"🔓 DEBUG: Şöbə '{target_department}' bağlıdır, açılır...")
                self.department_visibility[target_department] = True
                # Listbox-u yenilə
                self.refresh_employee_list()
                # UI-nin yenilənməsi üçün qısa gecikmə
                self.after(50, lambda: self._select_employee_after_expand(target_name))
                return
        else:
            # Şöbə dictionary-də yoxdursa, əlavə et və aç
            self.department_visibility[target_department] = True
            self.refresh_employee_list()
            self.after(50, lambda: self._select_employee_after_expand(target_name))
            return

        # Qrup artıq açıqdırsa, birbaşa işçini tap
        logging.info(f"Listbox-dan {target_name} axtarılır...")
        print(f"🔍 DEBUG: Listbox-dan {target_name} axtarılır...")
        listbox_items = self.employee_listbox.get(0, tb.END)
        for i, item in enumerate(listbox_items):
            clean_item = item.replace("● ", "").replace("○ ", "").split(" [")[0].split(" (")[0].strip()
            if clean_item == target_name:
                logging.info(f"Listbox-da {target_name} tapıldı, index: {i}")
                print(f"✅ DEBUG: Listbox-da {target_name} tapıldı, index: {i}")
                
                # Event'i geçici olaraq devre dışı bırak ki, selection_set() <<ListboxSelect>> event'ini tetiklemesin
                try:
                    self.employee_listbox.unbind("<<ListboxSelect>>")
                    print(f"🔍 [DEBUG] show_employee_by_id: <<ListboxSelect>> event'i geçici olaraq kaldırıldı")
                    
                    # Scroll pozisyonunu saxla
                    scroll_pos_before = None
                    try:
                        scroll_pos_before = self.employee_listbox.index("@0,0")
                        last_visible_before = self.employee_listbox.index("@0,{}".format(self.employee_listbox.winfo_height()))
                        print(f"🔍 [DEBUG] show_employee_by_id: selection_set-dən ƏVVƏL scroll pozisyonu: first_visible={scroll_pos_before}, last_visible={last_visible_before}, target_idx={i}, görünür={scroll_pos_before <= i <= last_visible_before}")
                    except:
                        pass
                    
                    self.employee_listbox.selection_clear(0, tb.END)
                    self.employee_listbox.selection_set(i)
                    
                    # Seçim görünür deyilsə, scroll et
                    try:
                        first_visible_after = self.employee_listbox.index("@0,0")
                        last_visible_after = self.employee_listbox.index("@0,{}".format(self.employee_listbox.winfo_height()))
                        print(f"🔍 [DEBUG] show_employee_by_id: selection_set-dən SONRA scroll pozisyonu: first_visible={first_visible_after}, last_visible={last_visible_after}")
                        
                        # Əgər seçim görünür deyilsə, scroll et
                        if i < first_visible_after or i > last_visible_after:
                            print(f"🔍 [DEBUG] show_employee_by_id: Seçim görünür deyil, see({i}) çağırılır")
                            self.employee_listbox.see(i)
                            try:
                                first_visible_final = self.employee_listbox.index("@0,0")
                                last_visible_final = self.employee_listbox.index("@0,{}".format(self.employee_listbox.winfo_height()))
                                print(f"🔍 [DEBUG] show_employee_by_id: see({i}) sonrası scroll pozisyonu: first_visible={first_visible_final}, last_visible={last_visible_final}")
                            except:
                                pass
                        else:
                            print(f"🔍 [DEBUG] show_employee_by_id: Seçim artıq görünür, see() çağırılmadı")
                            # Əgər Tkinter otomatik scroll etmişsə və seçim artıq görünürsə, scroll pozisyonunu geri qaytar
                            if scroll_pos_before is not None and first_visible_after != scroll_pos_before:
                                print(f"🔍 [DEBUG] show_employee_by_id: ⚠️ Tkinter otomatik scroll etdi! Əvvəl: {scroll_pos_before}, sonra: {first_visible_after}, geri qaytarılır...")
                                self.employee_listbox.see(scroll_pos_before)
                                try:
                                    restored_first_visible = self.employee_listbox.index("@0,0")
                                    print(f"🔍 [DEBUG] show_employee_by_id: ✅ Scroll pozisyonu geri qaytarıldı: {restored_first_visible}")
                                except:
                                    pass
                    except Exception as e:
                        print(f"🔍 [DEBUG] show_employee_by_id: Scroll kontrolü xətası: {e}")
                        # Xəta halında sadəcə see() çağır
                        self.employee_listbox.see(i)
                    
                    self.employee_listbox.bind("<<ListboxSelect>>", self.on_employee_select)
                    print(f"🔍 [DEBUG] show_employee_by_id: <<ListboxSelect>> event'i geri qaytarıldı")
                except Exception as e:
                    print(f"❌ [DEBUG] show_employee_by_id event binding xətası: {e}")
                    self.employee_listbox.selection_clear(0, tb.END)
                    self.employee_listbox.selection_set(i)
                    self.employee_listbox.see(i)
                
                print(f"✅ DEBUG: {target_name} listbox-da seçildi")
                break
        else:
            logging.warning(f"Listbox-da {target_name} tapılmadı (qrup açıq olsa belə)")
            print(f"⚠️ DEBUG: Listbox-da {target_name} tapılmadı (qrup açıq olsa belə)")
            return

        # İşçi seçildikdə on_employee_select çağır
        logging.info(f"on_employee_select çağırılır...")
        print(f"🔄 DEBUG: on_employee_select çağırılır...")
        self.on_employee_select(None)
        
        logging.info(f"=== show_employee_by_id bitdi ===")
        print(f"🏁 DEBUG: show_employee_by_id bitdi")
    
    def _select_employee_after_expand(self, target_name):
        """Qrup açıldıqdan sonra işçini seç"""
        logging.info(f"Qrup açıldıqdan sonra {target_name} seçilir...")
        print(f"🔍 DEBUG: Qrup açıldıqdan sonra {target_name} seçilir...")
        
        listbox_items = self.employee_listbox.get(0, tb.END)
        for i, item in enumerate(listbox_items):
            clean_item = item.replace("● ", "").replace("○ ", "").split(" [")[0].split(" (")[0].strip()
            if clean_item == target_name:
                logging.info(f"Listbox-da {target_name} tapıldı, index: {i}")
                print(f"✅ DEBUG: Listbox-da {target_name} tapıldı, index: {i}")
                
                # Event'i geçici olaraq devre dışı bırak ki, selection_set() <<ListboxSelect>> event'ini tetiklemesin
                try:
                    self.employee_listbox.unbind("<<ListboxSelect>>")
                    print(f"🔍 [DEBUG] _select_employee_after_expand: <<ListboxSelect>> event'i geçici olaraq kaldırıldı")
                    
                    # Scroll pozisyonunu saxla
                    scroll_pos_before = None
                    try:
                        scroll_pos_before = self.employee_listbox.index("@0,0")
                        last_visible_before = self.employee_listbox.index("@0,{}".format(self.employee_listbox.winfo_height()))
                        print(f"🔍 [DEBUG] show_employee_by_id: selection_set-dən ƏVVƏL scroll pozisyonu: first_visible={scroll_pos_before}, last_visible={last_visible_before}, target_idx={i}, görünür={scroll_pos_before <= i <= last_visible_before}")
                    except:
                        pass
                    
                    self.employee_listbox.selection_clear(0, tb.END)
                    self.employee_listbox.selection_set(i)
                    
                    # Seçim görünür deyilsə, scroll et
                    try:
                        first_visible_after = self.employee_listbox.index("@0,0")
                        last_visible_after = self.employee_listbox.index("@0,{}".format(self.employee_listbox.winfo_height()))
                        print(f"🔍 [DEBUG] show_employee_by_id: selection_set-dən SONRA scroll pozisyonu: first_visible={first_visible_after}, last_visible={last_visible_after}")
                        
                        # Əgər seçim görünür deyilsə, scroll et
                        if i < first_visible_after or i > last_visible_after:
                            print(f"🔍 [DEBUG] show_employee_by_id: Seçim görünür deyil, see({i}) çağırılır")
                            self.employee_listbox.see(i)
                            try:
                                first_visible_final = self.employee_listbox.index("@0,0")
                                last_visible_final = self.employee_listbox.index("@0,{}".format(self.employee_listbox.winfo_height()))
                                print(f"🔍 [DEBUG] show_employee_by_id: see({i}) sonrası scroll pozisyonu: first_visible={first_visible_final}, last_visible={last_visible_final}")
                            except:
                                pass
                        else:
                            print(f"🔍 [DEBUG] show_employee_by_id: Seçim artıq görünür, see() çağırılmadı")
                            # Əgər Tkinter otomatik scroll etmişsə və seçim artıq görünürsə, scroll pozisyonunu geri qaytar
                            if scroll_pos_before is not None and first_visible_after != scroll_pos_before:
                                print(f"🔍 [DEBUG] show_employee_by_id: ⚠️ Tkinter otomatik scroll etdi! Əvvəl: {scroll_pos_before}, sonra: {first_visible_after}, geri qaytarılır...")
                                self.employee_listbox.see(scroll_pos_before)
                                try:
                                    restored_first_visible = self.employee_listbox.index("@0,0")
                                    print(f"🔍 [DEBUG] show_employee_by_id: ✅ Scroll pozisyonu geri qaytarıldı: {restored_first_visible}")
                                except:
                                    pass
                    except Exception as e:
                        print(f"🔍 [DEBUG] show_employee_by_id: Scroll kontrolü xətası: {e}")
                        # Xəta halında sadəcə see() çağır
                        self.employee_listbox.see(i)
                    
                    self.employee_listbox.bind("<<ListboxSelect>>", self.on_employee_select)
                    print(f"🔍 [DEBUG] _select_employee_after_expand: <<ListboxSelect>> event'i geri qaytarıldı")
                except Exception as e:
                    print(f"❌ [DEBUG] _select_employee_after_expand event binding xətası: {e}")
                    self.employee_listbox.selection_clear(0, tb.END)
                    self.employee_listbox.selection_set(i)
                    self.employee_listbox.see(i)
                
                print(f"✅ DEBUG: {target_name} listbox-da seçildi")
                # İşçi seçildikdə on_employee_select çağır (event=None ilə, çünkü programatik çağırışdır)
                self.on_employee_select(None)
                return
        
        logging.warning(f"Qrup açıldıqdan sonra da {target_name} tapılmadı")
        print(f"⚠️ DEBUG: Qrup açıldıqdan sonra da {target_name} tapılmadı")

    def load_and_refresh_data(self, selection_to_keep=None, load_full_data=False):
        """
        Məlumatları yükləyir - lazy loading ilə optimallaşdırılıb
        load_full_data=True olduqda bütün məlumatları yükləyir, False olduqda yalnız cari görünüş üçün lazım olanları
        Bütün yükləmə əməliyyatları asinxron şəkildə işləyir - UI bloklanmır
        """
        import time
        import threading
        func_start = time.time()
        thread_id = threading.current_thread().ident
        thread_name = threading.current_thread().name
        print(f"🟢 [DEBUG] ⏱️ load_and_refresh_data BAŞLADI: load_full_data={load_full_data}, selection_to_keep={selection_to_keep}")
        print(f"🟢 [DEBUG] ⏱️ Thread ID: {thread_id}, Name: {thread_name}")
        logging.info(f"load_and_refresh_data başladı (load_full_data={load_full_data})")
        
        # Versiya yoxlamasını yalnız ilk dəfə işləyəndə edirik
        if not hasattr(self, '_version_check_done'):
            self._version_check_done = True
            logging.info("Versiya yoxlaması təyin edildi - 60 saniyə sonra işləyəcək")
            self.after(60000, self._check_for_update)
        elif not self._version_check_done:
            self._version_check_done = True
            logging.info("Versiya yoxlaması təyin edildi - 60 saniyə sonra işləyəcək")
            self.after(60000, self._check_for_update)
        else:
            logging.info("Versiya yoxlaması artıq edilib")
        
        # Cari görünüşü saxlayırıq - thread-dən əvvəl müəyyən et
        # Əvvəlcə self.current_view-i yoxla (show_view tərəfindən təyin olunub)
        current_view = getattr(self, 'current_view', None)
        
        # Əgər self.current_view yoxdursa və ya load_full_data=True deyilsə, winfo_viewable() ilə yoxla
        if current_view is None or (not load_full_data and current_view == 'dashboard'):
            try:
                for view_name, view_frame in self.views.items():
                    if hasattr(view_frame, 'winfo_viewable') and view_frame.winfo_viewable():
                        current_view = view_name
                        break
            except:
                pass
        
        # Əgər current_view hələ də tapılmadısa, default olaraq 'dashboard' qəbul et
        if current_view is None:
            current_view = 'dashboard'
            print(f"🔵 [DEBUG] current_view None idi, default 'dashboard' təyin edildi")
        
        print(f"🔵 [DEBUG] load_and_refresh_data: current_view={current_view}, load_full_data={load_full_data}, self.current_view={getattr(self, 'current_view', None)}")
        
        if not selection_to_keep and hasattr(self, 'employee_listbox') and self.employee_listbox.curselection():
            _, selection_to_keep = self.get_selected_employee_name()
        
        # Bütün yükləmə əməliyyatlarını asinxron et - UI bloklanmasın
        thread_create_start = time.time()
        print(f"🟢 [DEBUG] ⏱️ Thread yaradılır...")
        
        def load_data_async():
            thread_start_time = time.time()
            thread_id = threading.current_thread().ident
            thread_name = threading.current_thread().name
            print(f"🔵 [DEBUG] ⏱️ load_data_async THREAD BAŞLADI: {thread_start_time}")
            print(f"🔵 [DEBUG] ⏱️ Thread ID: {thread_id}, Name: {thread_name}")
            logging.info(f"🔵 [DEBUG] load_data_async thread başladı")
            try:
                # Thread-də də current_view-i yenidən yoxla (views yaradıla bilər)
                # Əvvəlcə self.current_view-i yoxla (show_view tərəfindən təyin olunub)
                thread_current_view = getattr(self, 'current_view', None) or current_view
                
                # Əgər load_full_data=True olduqsa, self.current_view-i istifadə et (show_view tərəfindən təyin olunub)
                if not load_full_data:
                    try:
                        for view_name, view_frame in self.views.items():
                            if hasattr(view_frame, 'winfo_viewable') and view_frame.winfo_viewable():
                                thread_current_view = view_name
                                break
                    except:
                        pass
                
                if thread_current_view is None:
                    thread_current_view = 'dashboard'
                
                print(f"🔵 [DEBUG] Thread-də current_view={thread_current_view}, load_full_data={load_full_data}")
                
                # Əgər load_full_data=True olduqsa, dərhal tam məlumatları yüklə (vacation məlumatları ilə)
                if load_full_data:
                    print(f"🔵 [DEBUG] Tam məlumatlar yüklənir (load_full_data=True)...")
                    logging.info("Tam məlumatlar yüklənir (load_full_data=True)...")
                    self._load_full_data_async(selection_to_keep)
                    return  # Thread-də bloklanmamaq üçün dərhal return et
                
                # Lazy loading: Yalnız lazım olan məlumatları yüklə
                if not load_full_data:
                    print(f"🔵 [DEBUG] load_full_data=False, current_view={thread_current_view}")
                    # İlk açılışda yalnız dashboard üçün lazım olan məlumatları yüklə
                    if thread_current_view == 'dashboard':
                        print(f"🔵 [DEBUG] Dashboard görünüşü üçün məlumatlar yüklənir...")
                        logging.info("Dashboard görünüşü üçün yalnız lazım olan məlumatlar yüklənir...")
                        # Dashboard üçün yalnız işçi siyahısını yüklə (vacation məlumatları dashboard özü yükləyir)
                        # Cache yoxlamasını da thread-də et - UI bloklanmasın
                        try:
                            print(f"🔵 [DEBUG] Cache import edilir...")
                            from utils import cache
                            print(f"🔵 [DEBUG] Cache import edildi, is_admin={self.is_admin}")
                            # Cache-dən yoxla - yalnız admin üçün (thread-də)
                            if self.is_admin:
                                print(f"🔵 [DEBUG] Admin üçün cache yoxlanılır...")
                                cache_valid = cache.is_cache_valid_for_user()
                                print(f"🔵 [DEBUG] Cache valid: {cache_valid}")
                                if cache_valid:
                                    try:
                                        print(f"🔵 [DEBUG] Cache yüklənir...")
                                        cache_start = time.time()
                                        cached_data = cache.load_cache()
                                        cache_time = time.time() - cache_start
                                        print(f"🔵 [DEBUG] Cache yükləndi {cache_time:.3f}s, data type: {type(cached_data)}, len: {len(cached_data) if isinstance(cached_data, dict) else 'N/A'}")
                                        if cached_data and isinstance(cached_data, dict) and len(cached_data) > 0:
                                            print(f"🔵 [DEBUG] Cache-dən məlumatlar alınır...")
                                            # Yalnız işçi məlumatlarını götür, vacation məlumatlarını dashboard özü yükləyir
                                            self.data = {k: {**v, 'goturulen_icazeler': []} for k, v in cached_data.items() if isinstance(v, dict)}
                                            print(f"🔵 [DEBUG] Cache-dən məlumatlar alındı. Ölçü: {len(self.data)}")
                                            logging.info(f"Dashboard üçün cache-dən işçi məlumatları yükləndi. Ölçü: {len(self.data)}")
                                            # UI thread-də refresh et - thread-də bloklanmamaq üçün dərhal return et
                                            sel_keep = selection_to_keep
                                            print(f"🔵 [DEBUG] UI thread-də refresh çağırılır (cache)...")
                                            thread_time = time.time() - thread_start_time
                                            print(f"🔵 [DEBUG] load_data_async thread bitdi (cache): {thread_time:.3f}s")
                                            # after çağırışını thread-dən sonra et - thread-də bloklanmamaq üçün
                                            def refresh_ui_cache():
                                                try:
                                                    self._update_notification_button()
                                                    self.refresh_employee_list(sel_keep)
                                                except Exception as e:
                                                    print(f"❌ [DEBUG] UI refresh xətası (cache): {e}")
                                            try:
                                                root = self.winfo_toplevel()
                                                if root and root.winfo_exists():
                                                    root.after(0, refresh_ui_cache)
                                                else:
                                                    self.after(0, refresh_ui_cache)
                                            except:
                                                pass
                                            return
                                    except Exception as cache_error:
                                        print(f"❌ [DEBUG] Cache yükləmə xətası: {cache_error}")
                                        logging.warning(f"Cache yükləmə xətası, veritabanından yüklənir: {cache_error}")
                                        import traceback
                                        print(f"❌ [DEBUG] Cache xəta traceback:\n{traceback.format_exc()}")
                        except Exception as e:
                            print(f"❌ [DEBUG] Cache yoxlama xətası: {e}")
                            logging.error(f"Cache yoxlama xətası: {e}", exc_info=True)
                            import traceback
                            print(f"❌ [DEBUG] Cache yoxlama xəta traceback:\n{traceback.format_exc()}")
                        
                        # Cache yoxdursa və ya xəta varsa, yalnız işçi məlumatlarını yüklə - thread-də
                        print(f"🔵 [DEBUG] Veritabanından işçi siyahısı yüklənir...")
                        db_start = time.time()
                        self._load_employee_list_only()
                        db_time = time.time() - db_start
                        print(f"🔵 [DEBUG] Veritabanından yükləmə bitdi: {db_time:.3f}s, data ölçü: {len(self.data) if hasattr(self, 'data') and self.data else 0}")
                        # UI thread-də refresh et - thread-də bloklanmamaq üçün dərhal return et
                        sel_keep = selection_to_keep
                        print(f"🔵 [DEBUG] UI thread-də refresh çağırılır (veritabanı)...")
                        # Thread-də bloklanmamaq üçün dərhal return et - after çağırışını thread-dən sonra et
                        thread_time = time.time() - thread_start_time
                        print(f"🔵 [DEBUG] load_data_async thread bitdi (veritabanı): {thread_time:.3f}s")
                        # Thread-də bloklanmamaq üçün dərhal return et - UI refresh finally blokunda ediləcək
                        return  # Thread-də bloklanmamaq üçün dərhal return et
                    else:
                        # Digər görünüşlər üçün tam məlumatları yüklə - asinxron
                        print(f"🔵 [DEBUG] Digər görünüş üçün tam məlumatlar yüklənir: {thread_current_view}")
                        logging.info(f"{thread_current_view} görünüşü üçün tam məlumatlar yüklənir...")
                        self._load_full_data_async(selection_to_keep)
                
                # User üçün də məlumatların yükləndiyini yoxla
                if not self.data and not self.is_admin:
                    print(f"🔵 [DEBUG] User üçün məlumatlar yoxdur, yenidən yükləmə cəhdi...")
                    logging.warning("User üçün məlumatlar yüklənmədi, yenidən yükləmə cəhdi...")
                    self._load_employee_list_only()
                    # UI thread-də refresh et - thread-də bloklanmamaq üçün dərhal return et
                    sel_keep = selection_to_keep
                    def refresh_ui_user():
                        try:
                            self._update_notification_button()
                            self.refresh_employee_list(sel_keep)
                        except Exception as e:
                            print(f"❌ [DEBUG] UI refresh xətası (user): {e}")
                    # after çağırışını thread-dən sonra et - thread-də bloklanmamaq üçün
                    try:
                        root = self.winfo_toplevel()
                        if root and root.winfo_exists():
                            root.after(0, refresh_ui_user)
                        else:
                            self.after(0, refresh_ui_user)
                    except:
                        pass
            except Exception as e:
                print(f"❌ [DEBUG] load_data_async xətası: {e}")
                logging.error(f"load_and_refresh_data xətası: {e}", exc_info=True)
                import traceback
                print(f"❌ [DEBUG] load_data_async xəta traceback:\n{traceback.format_exc()}")
                logging.error(traceback.format_exc())
            finally:
                thread_time = time.time() - thread_start_time
                print(f"🔵 [DEBUG] load_data_async thread tam bitdi: {thread_time:.3f}s")
                # Thread bitdikdən sonra UI refresh et - thread-də bloklanmamaq üçün
                try:
                    sel_keep = selection_to_keep
                    def refresh_ui_final():
                        try:
                            import time
                            final_start = time.time()
                            print(f"🔵 [DEBUG] refresh_ui_final çağırıldı (UI thread-də)")
                            
                            # refresh_employee_list UI thread-də işləyir
                            self.refresh_employee_list(sel_keep)
                            
                            # _update_notification_button artıq asinxrondur
                            self._update_notification_button()
                            
                            final_time = time.time() - final_start
                            print(f"🔵 [DEBUG] refresh_ui_final tam bitdi: {final_time:.3f}s")
                        except Exception as e:
                            print(f"❌ [DEBUG] UI refresh final xətası: {e}")
                            import traceback
                            print(f"❌ [DEBUG] UI refresh final xəta traceback:\n{traceback.format_exc()}")
                            logging.error(f"UI refresh final xətası: {e}", exc_info=True)
                    
                    # UI thread-də çağır - thread-də bloklanmamaq üçün
                    root = self.winfo_toplevel()
                    if root and root.winfo_exists():
                        root.after(0, refresh_ui_final)
                    else:
                        self.after(0, refresh_ui_final)
                except Exception as e:
                    print(f"❌ [DEBUG] Thread-dən sonra UI refresh xətası: {e}")
                    import traceback
                    print(f"❌ [DEBUG] Thread-dən sonra UI refresh xəta traceback:\n{traceback.format_exc()}")
        
        # Asinxron thread-də yüklə - UI bloklanmasın
        thread_create_time = time.time() - thread_create_start
        print(f"🟢 [DEBUG] ⏱️ Thread yaradılması bitdi: {thread_create_time:.3f}s")
        
        thread_start_time = time.time()
        print(f"🟢 [DEBUG] ⏱️ Thread yaradılır və başladılır...")
        thread = threading.Thread(target=load_data_async, daemon=True, name="DataLoader")
        thread_create_done = time.time()
        print(f"🟢 [DEBUG] ⏱️ Thread obyekti yaradıldı: {thread_create_done - thread_start_time:.3f}s")
        
        start_time = time.time()
        thread.start()
        start_done = time.time()
        print(f"🟢 [DEBUG] ⏱️ Thread.start() çağırıldı: {start_done - start_time:.3f}s")
        print(f"🟢 [DEBUG] ⏱️ Thread başladıldı, ID: {thread.ident}, is_alive: {thread.is_alive()}")
        
        func_time = time.time() - func_start
        print(f"🟢 [DEBUG] ⏱️ load_and_refresh_data funksiyası bitdi: {func_time:.3f}s (thread yaradıldı və başladıldı)")
    
    def _load_employee_list_only(self):
        """Yalnız işçi siyahısını yükləyir (vacation məlumatları olmadan) - daha sürətli"""
        import time
        start_time = time.time()
        user_role = self.current_user.get('role', 'unknown').strip()
        user_id = self.current_user.get('id', 'unknown')
        print(f"🔵 [DEBUG] _load_employee_list_only başladı: User={user_role}, ID={user_id}")
        logging.info(f"Yalnız işçi siyahısı yüklənir (vacation məlumatları olmadan)... User: {user_role}, ID: {user_id}")
        conn = None
        try:
            print(f"🔵 [DEBUG] Database import edilir...")
            from database import database as db
            print(f"🔵 [DEBUG] Database import edildi, db_connect çağırılır...")
            db_connect_start = time.time()
            conn = db.db_connect()
            db_connect_time = time.time() - db_connect_start
            print(f"🔵 [DEBUG] db_connect bitdi: {db_connect_time:.3f}s, conn={conn is not None}")
            if not conn:
                print(f"❌ [DEBUG] Veritabanı qoşulması uğursuz oldu")
                logging.error("Veritabanı qoşulması uğursuz oldu")
                self.data = {}
                return
            
            data = {}
            print(f"🔵 [DEBUG] Cursor yaradılır...")
            with conn.cursor() as cur:
                # Aktiv sessiya saylarını alırıq
                try:
                    print(f"🔵 [DEBUG] Aktiv sessiyalar sorğusu işləyir...")
                    session_start = time.time()
                    cur.execute("SELECT user_id, COUNT(*) FROM active_sessions GROUP BY user_id")
                    session_counts = dict(cur.fetchall())
                    session_time = time.time() - session_start
                    print(f"🔵 [DEBUG] Aktiv sessiyalar alındı: {session_time:.3f}s, say: {len(session_counts)}")
                except Exception as e:
                    print(f"⚠️ [DEBUG] Aktiv sessiyalar xətası: {e}")
                    session_counts = {}
                
                # İşçi məlumatlarını alırıq (vacation məlumatları olmadan)
                print(f"🔵 [DEBUG] İşçi məlumatları sorğusu hazırlanır, role={self.current_user['role'].strip()}")
                if self.current_user['role'].strip() == 'admin':
                    cur.execute("""
                        SELECT id, name, total_vacation_days, is_active, max_sessions,
                               first_name, last_name, father_name, email, phone_number,
                               birth_date, address, position, department, hire_date, salary, profile_image, role, username,
                               fin_code, department_id, position_id
                        FROM employees 
                        WHERE hide IS NULL OR hide = FALSE 
                        ORDER BY name
                    """)
                else:
                    # User üçün - yalnız öz məlumatlarını yüklə
                    user_id = self.current_user.get('id')
                    if not user_id:
                        logging.error(f"User ID tapılmadı! current_user: {self.current_user}")
                        self.data = {}
                        conn.close()
                        return
                    logging.info(f"User üçün məlumatlar yüklənir. User ID: {user_id}")
                    cur.execute("""
                        SELECT id, name, total_vacation_days, is_active, max_sessions,
                               first_name, last_name, father_name, email, phone_number,
                               birth_date, address, position, department, hire_date, salary, profile_image, role, username,
                               fin_code, department_id, position_id
                        FROM employees 
                        WHERE id = %s AND (hide IS NULL OR hide = FALSE)
                    """, (user_id,))
                
                print(f"🔵 [DEBUG] İşçi sorğusu işləyir...")
                emp_query_start = time.time()
                employees = cur.fetchall()
                emp_query_time = time.time() - emp_query_start
                print(f"🔵 [DEBUG] İşçi sorğusu bitdi: {emp_query_time:.3f}s, say: {len(employees)}")
                logging.info(f"İşçi sayı tapıldı: {len(employees)} (User: {user_role}, ID: {user_id})")
                print(f"🔵 [DEBUG] İşçi məlumatları işlənir...")
                emp_process_start = time.time()
                for emp in employees:
                    emp_id, name, total_days, is_active, max_sessions, first_name, last_name, father_name, email, phone_number, birth_date, address, position, department, hire_date, salary, profile_image, role, username, fin_code, department_id, position_id = emp
                    
                    data[name] = {
                        'db_id': emp_id,
                        'umumi_gun': total_days or 30,
                        'is_active': bool(is_active),
                        'max_sessions': max_sessions or 1,
                        'active_session_count': session_counts.get(emp_id, 0),
                        'goturulen_icazeler': [],  # Boş - vacation məlumatları yoxdur
                        'first_name': first_name or '',
                        'last_name': last_name or '',
                        'father_name': father_name or '',
                        'email': email or '',
                        'phone_number': phone_number or '',
                        'birth_date': birth_date.strftime('%Y-%m-%d') if birth_date else '',
                        'address': address or '',
                        'position': position or '',
                        'department': department or '',
                        'hire_date': hire_date.strftime('%Y-%m-%d') if hire_date else '',
                        'salary': salary or '',
                        'profile_image': profile_image or '',
                        'role': role or 'user',
                        'username': username or '',
                        'fin_code': fin_code if fin_code is not None else '',
                        'department_id': department_id if department_id is not None else '',
                        'position_id': position_id if position_id is not None else ''
                    }
            
                emp_process_time = time.time() - emp_process_start
                print(f"🔵 [DEBUG] İşçi məlumatları işləndi: {emp_process_time:.3f}s")
            
            self.data = data
            total_time = time.time() - start_time
            print(f"🔵 [DEBUG] _load_employee_list_only bitdi: {total_time:.3f}s, data ölçü: {len(self.data)}")
            logging.info(f"Yalnız işçi siyahısı yükləndi. Ölçü: {len(self.data)}")
        except Exception as e:
            total_time = time.time() - start_time
            print(f"❌ [DEBUG] _load_employee_list_only xətası ({total_time:.3f}s): {e}")
            logging.error(f"İşçi siyahısı yüklənərkən xəta: {e}", exc_info=True)
            import traceback
            print(f"❌ [DEBUG] _load_employee_list_only xəta traceback:\n{traceback.format_exc()}")
            self.data = {}
        finally:
            # Bağlantını həmişə bağla
            if conn:
                try:
                    print(f"🔵 [DEBUG] Veritabanı bağlantısı bağlanır...")
                    conn.close()
                    print(f"🔵 [DEBUG] Veritabanı bağlantısı bağlandı")
                except Exception as e:
                    print(f"⚠️ [DEBUG] Veritabanı bağlantısı bağlanarkən xəta: {e}")
    
    def _load_employee_list_async(self):
        """İşçi siyahısını asinxron şəkildə yükləyir - UI donmasın"""
        import threading
        def load_in_thread():
            try:
                self._load_employee_list_only()
                # UI thread-də refresh et
                if hasattr(self, 'refresh_employee_list'):
                    logging.info(f"Asinxron yükləmə tamamlandı, refresh çağırılır. Data ölçü: {len(self.data)}")
                    self.after(0, self.refresh_employee_list)
                else:
                    logging.warning("refresh_employee_list funksiyası tapılmadı!")
            except Exception as e:
                logging.error(f"Asinxron yükləmə xətası: {e}", exc_info=True)
        
        thread = threading.Thread(target=load_in_thread, daemon=True)
        thread.start()
    
    def _load_full_data(self):
        """Tam məlumatları yükləyir (işçilər + vacation məlumatları) - sinxron versiya"""
        logging.info("Tam məlumatlar yüklənir...")
        try:
            is_first_load = not hasattr(self, '_data_loaded_once')
            self.data = database.load_data_for_user(self.current_user, force_refresh=not is_first_load)
            self._data_loaded_once = True
            self._full_data_loaded = True
            logging.info(f"Tam məlumatlar yükləndi. Ölçü: {len(self.data)}")
        except Exception as e:
            logging.error(f"Tam məlumatlar yüklənərkən xəta: {e}", exc_info=True)
            self.data = {}
    
    def _load_full_data_async(self, selection_to_keep=None):
        """Tam məlumatları asinxron şəkildə yükləyir (işçilər + vacation məlumatları) - UI bloklanmır"""
        import threading
        import time
        def load_in_thread():
            thread_start = time.time()
            print(f"🔵 [DEBUG] _load_full_data_async thread başladı")
            try:
                is_first_load = not hasattr(self, '_data_loaded_once')
                print(f"🔵 [DEBUG] _load_full_data_async: database.load_data_for_user çağırılır...")
                load_start = time.time()
                self.data = database.load_data_for_user(self.current_user, force_refresh=not is_first_load)
                load_time = time.time() - load_start
                print(f"🔵 [DEBUG] _load_full_data_async: database.load_data_for_user bitdi: {load_time:.3f}s, data ölçü: {len(self.data)}")
                self._data_loaded_once = True
                self._full_data_loaded = True
                logging.info(f"Tam məlumatlar yükləndi. Ölçü: {len(self.data)}")
                
                # UI thread-də refresh et - asinxron funksiyaları ayrı-ayrı çağır
                sel_keep = selection_to_keep
                def refresh_ui():
                    try:
                        print(f"🔵 [DEBUG] _load_full_data_async: UI refresh başladı")
                        refresh_start = time.time()
                        # refresh_employee_list UI thread-də işləyir, amma tez olmalıdır
                        self.refresh_employee_list(sel_keep)
                        refresh_time = time.time() - refresh_start
                        print(f"🔵 [DEBUG] _load_full_data_async: refresh_employee_list bitdi: {refresh_time:.3f}s")
                        
                        # _update_notification_button artıq asinxrondur, sadəcə çağır
                        self._update_notification_button()
                        
                        # update_profile_button UI thread-də işləyir
                        if hasattr(self, 'update_profile_button'):
                            self.update_profile_button()
                        
                        # _check_employee_selection_after_load UI thread-də işləyir
                        self._check_employee_selection_after_load()
                        
                        total_refresh_time = time.time() - refresh_start
                        print(f"🔵 [DEBUG] _load_full_data_async: UI refresh tam bitdi: {total_refresh_time:.3f}s")
                    except Exception as e:
                        print(f"❌ [DEBUG] _load_full_data_async: UI refresh xətası: {e}")
                        import traceback
                        print(f"❌ [DEBUG] _load_full_data_async: UI refresh xəta traceback:\n{traceback.format_exc()}")
                        logging.error(f"UI refresh xətası: {e}", exc_info=True)
                
                # UI thread-də refresh et
                try:
                    root = self.winfo_toplevel()
                    if root and root.winfo_exists():
                        root.after(0, refresh_ui)
                    else:
                        self.after(0, refresh_ui)
                except Exception as e:
                    print(f"❌ [DEBUG] _load_full_data_async: after çağırışı xətası: {e}")
                
                thread_time = time.time() - thread_start
                print(f"🔵 [DEBUG] _load_full_data_async thread bitdi: {thread_time:.3f}s")
            except Exception as e:
                thread_time = time.time() - thread_start
                print(f"❌ [DEBUG] _load_full_data_async xətası ({thread_time:.3f}s): {e}")
                logging.error(f"Tam məlumatlar yüklənərkən xəta: {e}", exc_info=True)
                import traceback
                print(f"❌ [DEBUG] _load_full_data_async xəta traceback:\n{traceback.format_exc()}")
                self.data = {}
                # UI thread-də refresh et (boş data ilə)
                sel_keep = selection_to_keep
                def refresh_ui_error():
                    try:
                        self.refresh_employee_list(sel_keep)
                        self._update_notification_button()
                    except Exception as e2:
                        print(f"❌ [DEBUG] _load_full_data_async: Error refresh xətası: {e2}")
                try:
                    root = self.winfo_toplevel()
                    if root and root.winfo_exists():
                        root.after(0, refresh_ui_error)
                    else:
                        self.after(0, refresh_ui_error)
                except:
                    pass
        
        thread = threading.Thread(target=load_in_thread, daemon=True, name="FullDataLoader")
        thread.start()
        print(f"🔵 [DEBUG] _load_full_data_async thread başladıldı")
    
    def _check_employee_selection_after_load(self):
        """Məlumatlar yükləndikdən sonra işçi seçimini yoxla"""
        try:
            # Təhlükəsizlik yoxlaması: Adi istifadəçi yalnız dashboard görünüşünü görə bilər
            current_view = None
            for view_name, view_frame in self.views.items():
                if view_frame.winfo_viewable():
                    current_view = view_name
                    break
            
            if self.current_user['role'].strip() == 'admin' and current_view != 'dashboard' and hasattr(self, 'employee_listbox') and self.employee_listbox.curselection():
                self.on_employee_select(None)  # None event ilə çağırırıq
        except Exception as e:
            logging.error(f"_check_employee_selection_after_load xətası: {e}", exc_info=True)
        
    def refresh_employee_list(self, selection_to_keep=None):
        """İşçi siyahısını yeniləyir - asinxron batch processing ilə UI bloklanmır"""
        import time
        import threading
        import traceback
        
        # Debug: Çağırılan yeri tap
        caller_stack = ''.join(traceback.format_stack()[-3:-1])
        print(f"🔍 [DEBUG] refresh_employee_list çağırıldı: selection_to_keep={selection_to_keep}")
        print(f"🔍 [DEBUG] Çağırılan yer:\n{caller_stack}")
        
        # Əgər artıq refresh işləyirsə, gözlə
        if hasattr(self, '_refresh_in_progress') and self._refresh_in_progress:
            print(f"⚠️ [DEBUG] refresh_employee_list: Artıq refresh işləyir, gözləyirəm...")
            self.after(100, lambda: self.refresh_employee_list(selection_to_keep))
            return
        
        refresh_start = time.time()
        thread_id = threading.current_thread().ident
        thread_name = threading.current_thread().name
        print(f"🔵 [DEBUG] [UI THREAD] ⏱️ refresh_employee_list BAŞLADI: selection_to_keep={selection_to_keep}")
        print(f"🔵 [DEBUG] [UI THREAD] ⏱️ Thread ID: {thread_id}, Name: {thread_name}")
        
        if not hasattr(self, 'employee_listbox'): 
            print(f"⚠️ [DEBUG] [UI THREAD] ⏱️ refresh_employee_list: employee_listbox tapılmadı!")
            logging.warning("employee_listbox tapılmadı!")
            return
        
        # Scroll pozisyonunu logla və saxla (listbox təmizlənmədən əvvəl)
        scroll_pos_to_preserve = None
        try:
            if hasattr(self, 'employee_listbox'):
                try:
                    first_visible_before = self.employee_listbox.index("@0,0")
                    last_visible_before = self.employee_listbox.index("@0,{}".format(self.employee_listbox.winfo_height()))
                    scroll_pos_to_preserve = first_visible_before
                    print(f"🔍 [DEBUG] refresh_employee_list BAŞLAMADAN ƏVVƏL: scroll pozisyonu: first_visible={first_visible_before}, last_visible={last_visible_before}, scroll_pos_to_preserve={scroll_pos_to_preserve}")
                except Exception as e:
                    print(f"🔍 [DEBUG] refresh_employee_list BAŞLAMADAN ƏVVƏL: scroll pozisyonu alına bilmədi: {e}")
        except Exception as e:
            print(f"🔍 [DEBUG] refresh_employee_list BAŞLAMADAN ƏVVƏL: scroll pozisyonu xətası: {e}")
        
        # Cari seçimi saxla (listbox təmizlənmədən əvvəl)
        current_selection_name = None
        current_idx_before = None
        if not selection_to_keep:
            try:
                current_selection = self.employee_listbox.curselection()
                if current_selection:
                    current_idx_before = current_selection[0]
                    current_item_text = self.employee_listbox.get(current_idx_before)
                    # İşçi adını çıxar (● və ya ○ işarələrini və digər məlumatları sil)
                    current_selection_name = current_item_text.replace("● ", "").replace("○ ", "").split(" [")[0].split(" (")[0].strip()
                    print(f"🔍 [DEBUG] Cari seçim tapıldı (listbox təmizlənmədən əvvəl): index={current_idx_before}, name={current_selection_name}, item_text={current_item_text[:50]}")
            except Exception as e:
                print(f"🔍 [DEBUG] Cari seçimi alma xətası: {e}")
                import traceback
                print(f"🔍 [DEBUG] Cari seçimi alma xəta traceback:\n{traceback.format_exc()}")
        
        # Əgər selection_to_keep None idisə və cari seçim varsa, onu istifadə et
        if not selection_to_keep and current_selection_name:
            selection_to_keep = current_selection_name
            print(f"🔍 [DEBUG] selection_to_keep None idi, cari seçim istifadə edildi: {selection_to_keep}")
        
        print(f"🔍 [DEBUG] refresh_employee_list: selection_to_keep={selection_to_keep}, current_idx_before={current_idx_before}")
        
        delete_start = time.time()
        print(f"🔵 [DEBUG] [UI THREAD] ⏱️ listbox.delete çağırılır...")
        self.employee_listbox.delete(0, tb.END)
        delete_time = time.time() - delete_start
        print(f"🔵 [DEBUG] [UI THREAD] ⏱️ listbox təmizləndi: {delete_time:.3f}s")
        if delete_time > 0.1:
            print(f"⚠️ [DEBUG] [UI THREAD] ⚠️ listbox.delete() ÇOX UZUN: {delete_time:.3f}s - UI BLOKLANIR!")
        
        if not hasattr(self, 'data') or not self.data: 
            print(f"⚠️ [DEBUG] [UI THREAD] refresh_employee_list: Data yoxdur! hasattr data: {hasattr(self, 'data')}, data: {getattr(self, 'data', None)}")
            logging.warning(f"Data yoxdur! hasattr data: {hasattr(self, 'data')}, data: {getattr(self, 'data', None)}")
            return
        
        print(f"🔵 [DEBUG] [UI THREAD] refresh_employee_list: Data ölçü: {len(self.data)}, User: {self.current_user.get('name', 'unknown')}")
        logging.info(f"refresh_employee_list çağırıldı. Data ölçü: {len(self.data)}, User: {self.current_user.get('name', 'unknown')}")
        
        # Təhlükəsizlik yoxlaması: Adi istifadəçi yalnız öz adını görə bilər
        filter_start = time.time()
        if self.current_user['role'].strip() != 'admin':
            # Adi istifadəçi üçün yalnız öz adını göstəririk
            current_user_name = self.current_user.get('name', '')
            filtered_data = {}
            # Yalnız öz adını göstər
            if current_user_name in self.data:
                filtered_data[current_user_name] = self.data[current_user_name]
        else:
            # Admin üçün bütün məlumatları göstəririk (filtr varsa tətbiq edilir)
            filtered_data = self.data.copy()
            
            # Filtr tətbiq et (şöbə və axtarış)
            if hasattr(self, 'selected_department_filter') and self.selected_department_filter:
                filtered_data = {name: data for name, data in filtered_data.items() 
                               if isinstance(data, dict) and data.get('department', '') == self.selected_department_filter}
            
            if hasattr(self, 'search_text') and self.search_text:
                search_lower = self.search_text.lower()
                filtered_data = {name: data for name, data in filtered_data.items() 
                               if search_lower in name.lower() or 
                               (isinstance(data, dict) and search_lower in data.get('department', '').lower())}
        
        filter_time = time.time() - filter_start
        print(f"🔵 [DEBUG] [UI THREAD] refresh_employee_list: Filtr tətbiq edildi: {filter_time:.3f}s, filtered_data ölçü: {len(filtered_data)}")
        
        # Şöbələr üzrə qruplaşdırma
        group_start = time.time()
        departments_dict = {}
        for name, emp_data in filtered_data.items():
            if isinstance(emp_data, dict):
                dept = emp_data.get('department', 'Şöbə təyin edilməyib')
            else:
                dept = 'Şöbə təyin edilməyib'
            
            if dept not in departments_dict:
                departments_dict[dept] = []
            departments_dict[dept].append((name, emp_data))
        
        group_time = time.time() - group_start
        print(f"🔵 [DEBUG] refresh_employee_list: Qruplaşdırma bitdi: {group_time:.3f}s, departments: {len(departments_dict)}")
        
        # Hazırlıq: Şöbələri və işçiləri hazırla
        prep_start = time.time()
        restored_idx = -1
        
        # Şöbələrin gizlənməsi üçün dictionary
        if not hasattr(self, 'department_visibility'):
            self.department_visibility = {}
        
        # Başlanğıcda bütün şöbələr bağlıdır (False) - yalnız ilk dəfə
        if not self.department_visibility:
            for dept in sorted(departments_dict.keys()):
                self.department_visibility[dept] = False
        
        # Filtr tətbiq olunubsa, yalnız seçilmiş şöbəni göstər
        filtered_departments = sorted(departments_dict.keys())
        if hasattr(self, 'selected_department_filter') and self.selected_department_filter:
            filtered_departments = [dept for dept in filtered_departments if dept == self.selected_department_filter]
        
        # User üçün şöbə başlığı göstərmə - yalnız öz adı görünür
        show_department_headers = self.is_admin or len(departments_dict) > 1
        
        # Bütün item-ləri hazırla (listbox-a yazmadan)
        all_items = []  # [(item_text, fg_color, bg_color, is_dept_header, name_for_selection), ...]
        
        for dept in filtered_departments:
            # Şöbə başlığı
            if show_department_headers:
                if dept not in self.department_visibility:
                    self.department_visibility[dept] = False
                
                if hasattr(self, 'selected_department_filter') and self.selected_department_filter == dept:
                    self.department_visibility[dept] = True
                
                is_expanded = self.department_visibility.get(dept, False)
                expand_indicator = "▼" if is_expanded else "▶"
                dept_header = f"{expand_indicator} {dept}"
                all_items.append((dept_header, '#1976d2', '#f5f5f5', True, None))
            
            # Şöbədəki işçilər
            should_show_employees = True if not self.is_admin else self.department_visibility.get(dept, True)
            if should_show_employees:
                employees_in_dept = sorted(departments_dict[dept], key=lambda x: x[0])
                for name, employee_data in employees_in_dept:
                    if isinstance(employee_data, bool):
                        is_active_account = employee_data
                        active_sessions = 0
                    elif isinstance(employee_data, str):
                        is_active_account = True
                        active_sessions = 0
                    else:
                        is_active_account = employee_data.get("is_active", True)
                        active_sessions = employee_data.get("active_session_count", 0)

                    if not is_active_account:
                        indicator = "○"
                        color = "#9e9e9e"
                        display_name = f"  {indicator} {name} [Deaktiv]"
                        bg_color = "#fafafa"
                    elif active_sessions > 0:
                        indicator = "●"
                        color = "#2e7d32"
                        session_text = f" ({active_sessions})" if active_sessions > 1 else ""
                        display_name = f"  {indicator} {name}{session_text}"
                        bg_color = "#e8f5e9"
                    else:
                        indicator = "●"
                        color = "#424242"
                        display_name = f"  {indicator} {name}"
                        bg_color = "#ffffff"
                    
                    all_items.append((display_name, color, bg_color, False, name))
        
        prep_time = time.time() - prep_start
        print(f"🔵 [DEBUG] [UI THREAD] Hazırlıq bitdi: {prep_time:.3f}s, items: {len(all_items)}")
        
        # OPTİMALLAŞDIRMA: Asinxron batch processing ilə listbox-a yaz
        self._refresh_in_progress = True
        batch_size = 50  # OPTİMALLAŞDIRMA: 10-dan 50-yə artırdıq - daha az batch, daha sürətli
        self._refresh_batch_index = 0
        self._refresh_items = all_items
        self._refresh_selection_to_keep = selection_to_keep
        self._refresh_start_time = refresh_start
        self._refresh_delete_time = delete_time
        self._refresh_filter_time = filter_time
        self._refresh_group_time = group_time
        self._refresh_display_start_time = time.time()  # Display başlanğıc vaxtı
        self._refresh_batch_count = 0  # OPTİMALLAŞDIRMA: Batch sayğacı
        
        def process_batch():
            try:
                batch_start = time.time()
                start_idx = self._refresh_batch_index
                end_idx = min(start_idx + batch_size, len(self._refresh_items))
                
                print(f"🔵 [DEBUG] [UI THREAD] ⏱️ process_batch BAŞLADI: batch={self._refresh_batch_count}, start_idx={start_idx}, end_idx={end_idx}, total={len(self._refresh_items)}")
                
                if start_idx >= len(self._refresh_items):
                    # Bitdi
                    self._refresh_in_progress = False
                    display_end_time = time.time()
                    display_time = display_end_time - self._refresh_display_start_time
                    
                    print(f"🔵 [DEBUG] [UI THREAD] ⏱️ process_batch: Bütün batch-lər bitdi, display_time: {display_time:.3f}s")
                    
                    # Seçimi bərpa et
                    restore_start = time.time()
                    if hasattr(self, 'employee_listbox'):
                        restored_idx = -1
                        restored_name = None
                        
                        print(f"🔍 [DEBUG] [UI THREAD] Seçim bərpa prosesi başladı: selection_to_keep={self._refresh_selection_to_keep}, total_items={len(self._refresh_items)}")
                        
                        # Əgər selection_to_keep None deyilsə, onu tap
                        if self._refresh_selection_to_keep:
                            print(f"🔍 [DEBUG] [UI THREAD] selection_to_keep axtarılır: '{self._refresh_selection_to_keep}'")
                            for idx, (_, _, _, _, name) in enumerate(self._refresh_items):
                                if name == self._refresh_selection_to_keep:
                                    restored_idx = idx
                                    restored_name = name
                                    print(f"🔍 [DEBUG] selection_to_keep tapıldı: name={name}, index={idx}")
                                    break
                            if restored_idx == -1:
                                print(f"🔍 [DEBUG] [UI THREAD] ⚠️ selection_to_keep tapılmadı: '{self._refresh_selection_to_keep}'")
                                # İlk 5 item-in adlarını göster
                                print(f"🔍 [DEBUG] [UI THREAD] İlk 5 item: {[(idx, name) for idx, (_, _, _, _, name) in enumerate(self._refresh_items[:5])]}")
                        else:
                            print(f"🔍 [DEBUG] [UI THREAD] selection_to_keep None, seçim bərpa edilməyəcək")
                        # selection_to_keep artıq refresh_employee_list başında təyin olunub (cari seçimdən)
                        # Burada yalnız selection_to_keep varsa onu tapırıq
                        
                        if restored_idx != -1:
                            sel_start = time.time()
                            print(f"🔵 [DEBUG] [UI THREAD] ⏱️ Seçim bərpa edilir: index={restored_idx}, name={restored_name}, selection_to_keep={self._refresh_selection_to_keep}")
                            
                            # Event'i geçici olaraq devre dışı bırak ki, selection_set() <<ListboxSelect>> event'ini tetiklemesin
                            # Bu, otomatik gezinməyə səbəb olan döngünü qırır
                            try:
                                # Scroll pozisyonunu selection_set-dən əvvəl saxla
                                scroll_pos_before = None
                                try:
                                    scroll_pos_before = self.employee_listbox.index("@0,0")
                                    print(f"🔍 [DEBUG] [UI THREAD] selection_set-dən ƏVVƏL scroll pozisyonu: first_visible={scroll_pos_before}")
                                except:
                                    pass
                                
                                # Event binding'i geçici olaraq kaldır
                                self.employee_listbox.unbind("<<ListboxSelect>>")
                                print(f"🔍 [DEBUG] <<ListboxSelect>> event'i geçici olaraq kaldırıldı (restore üçün)")
                                
                                # Seçimin görünür olub olmadığını selection_set-dən ƏVVƏL yoxla
                                first_visible_before_set = None
                                last_visible_before_set = None
                                try:
                                    first_visible_before_set = self.employee_listbox.index("@0,0")
                                    last_visible_before_set = self.employee_listbox.index("@0,{}".format(self.employee_listbox.winfo_height()))
                                    print(f"🔍 [DEBUG] [UI THREAD] selection_set-dən ƏVVƏL görünürlük: restored_idx={restored_idx}, first_visible={first_visible_before_set}, last_visible={last_visible_before_set}, görünür={first_visible_before_set <= restored_idx <= last_visible_before_set}")
                                except Exception as e:
                                    print(f"🔍 [DEBUG] [UI THREAD] selection_set-dən ƏVVƏL görünürlük xətası: {e}")
                                
                                self.employee_listbox.selection_set(restored_idx)
                                sel_time1 = time.time() - sel_start
                                print(f"🔵 [DEBUG] [UI THREAD] ⏱️ selection_set bitdi: {sel_time1:.3f}s, index={restored_idx}")
                                
                                # selection_set-dən SONRA scroll pozisyonunu yoxla (Tkinter otomatik scroll edib edilmədiyini görmək üçün)
                                try:
                                    first_visible_after_set = self.employee_listbox.index("@0,0")
                                    last_visible_after_set = self.employee_listbox.index("@0,{}".format(self.employee_listbox.winfo_height()))
                                    print(f"🔍 [DEBUG] [UI THREAD] selection_set-dən SONRA scroll pozisyonu: first_visible={first_visible_after_set}, last_visible={last_visible_after_set}")
                                    
                                    # Əgər Tkinter otomatik scroll etmişsə və seçim artıq görünürsə, scroll pozisyonunu geri qaytar
                                    if scroll_pos_before is not None and first_visible_before_set is not None:
                                        if first_visible_before_set <= restored_idx <= last_visible_before_set:
                                            # Seçim əvvəldən görünürdü, scroll pozisyonu dəyişməməlidir
                                            if first_visible_after_set != first_visible_before_set:
                                                print(f"🔍 [DEBUG] [UI THREAD] ⚠️ Tkinter otomatik scroll etdi! Əvvəl: {first_visible_before_set}, sonra: {first_visible_after_set}, geri qaytarılır...")
                                                self.employee_listbox.see(scroll_pos_before)
                                                try:
                                                    first_visible_restored = self.employee_listbox.index("@0,0")
                                                    print(f"🔍 [DEBUG] [UI THREAD] ✅ Scroll pozisyonu geri qaytarıldı: {first_visible_restored}")
                                                except:
                                                    pass
                                            else:
                                                print(f"🔍 [DEBUG] [UI THREAD] ✅ Scroll pozisyonu dəyişmədi (gözlənilən)")
                                except Exception as e:
                                    print(f"🔍 [DEBUG] [UI THREAD] selection_set-dən SONRA scroll pozisyonu xətası: {e}")
                                
                                # Event binding'i geri qaytar
                                self.employee_listbox.bind("<<ListboxSelect>>", self.on_employee_select)
                                print(f"🔍 [DEBUG] <<ListboxSelect>> event'i geri qaytarıldı (restore üçün)")
                                
                                # Scroll pozisyonunu yalnız seçim görünür deyilsə dəyişdir
                                # Bu, kullanıcı manuel scroll yaptığında pozisyonu korur
                                try:
                                    # Seçimin görünür olub olmadığını yoxla
                                    first_visible = self.employee_listbox.index("@0,0")
                                    last_visible = self.employee_listbox.index("@0,{}".format(self.employee_listbox.winfo_height()))
                                    listbox_height = self.employee_listbox.winfo_height()
                                    total_items = self.employee_listbox.size()
                                    
                                    print(f"🔍 [DEBUG] [UI THREAD] Scroll kontrolü (final): restored_idx={restored_idx}, first_visible={first_visible}, last_visible={last_visible}, listbox_height={listbox_height}, total_items={total_items}, scroll_pos_to_preserve={scroll_pos_to_preserve}")
                                    
                                    # Seçim görünür deyilsə, scroll et
                                    if restored_idx < first_visible or restored_idx > last_visible:
                                        print(f"🔍 [DEBUG] [UI THREAD] ⚠️ Seçim görünür deyil, scroll ediləcək: restored_idx={restored_idx}, first_visible={first_visible}, last_visible={last_visible}")
                                        sel_start2 = time.time()
                                        self.employee_listbox.see(restored_idx)
                                        sel_time3 = time.time() - sel_start2
                                        
                                        # Scroll sonrası pozisyonu yoxla
                                        try:
                                            first_visible_after = self.employee_listbox.index("@0,0")
                                            last_visible_after = self.employee_listbox.index("@0,{}".format(self.employee_listbox.winfo_height()))
                                            print(f"🔵 [DEBUG] [UI THREAD] ⏱️ see bitdi (scroll edildi): {sel_time3:.3f}s, restored_idx={restored_idx}, scroll sonrası: first_visible={first_visible_after}, last_visible={last_visible_after}")
                                        except:
                                            print(f"🔵 [DEBUG] [UI THREAD] ⏱️ see bitdi (scroll edildi): {sel_time3:.3f}s, restored_idx={restored_idx}")
                                    else:
                                        print(f"🔵 [DEBUG] [UI THREAD] ✅ Seçim artıq görünür, scroll edilmədi: restored_idx={restored_idx}, first_visible={first_visible}, last_visible={last_visible}")
                                        
                                        # Əgər scroll pozisyonu dəyişibsə və seçim görünürsə, scroll pozisyonunu geri qaytar
                                        if scroll_pos_to_preserve is not None and first_visible != scroll_pos_to_preserve:
                                            print(f"🔍 [DEBUG] [UI THREAD] ⚠️ Scroll pozisyonu dəyişib! Əvvəl: {scroll_pos_to_preserve}, indi: {first_visible}, geri qaytarılır...")
                                            try:
                                                self.employee_listbox.see(scroll_pos_to_preserve)
                                                restored_first_visible = self.employee_listbox.index("@0,0")
                                                print(f"🔍 [DEBUG] [UI THREAD] ✅ Scroll pozisyonu geri qaytarıldı: {restored_first_visible}")
                                            except Exception as e:
                                                print(f"🔍 [DEBUG] [UI THREAD] Scroll pozisyonu geri qaytarma xətası: {e}")
                                except Exception as e:
                                    # Xəta halında scroll etmə (otomatik gezinməyə səbəb olmasın)
                                    import traceback
                                    print(f"🔍 [DEBUG] Scroll kontrolü xətası: {e}, scroll edilmədi")
                                    print(f"🔍 [DEBUG] Scroll kontrolü xəta traceback:\n{traceback.format_exc()}")
                                    
                            except Exception as e:
                                print(f"❌ [DEBUG] Event binding xətası: {e}")
                                import traceback
                                print(f"❌ [DEBUG] Event binding xəta traceback:\n{traceback.format_exc()}")
                                # Xəta halında sadəcə selection_set et
                                self.employee_listbox.selection_set(restored_idx)
                                sel_time1 = time.time() - sel_start
                                print(f"🔵 [DEBUG] [UI THREAD] ⏱️ selection_set bitdi (xəta halında): {sel_time1:.3f}s")
                        else:
                            print(f"🔍 [DEBUG] Seçim bərpa edilmədi: selection_to_keep={self._refresh_selection_to_keep}, restored_idx={restored_idx}")
                            # Seçim yoxdursa, heç bir şey seçmə (otomatik gezinməyə səbəb olmasın)
                            try:
                                # Event'i geçici olaraq kaldır və seçimi təmizlə
                                self.employee_listbox.unbind("<<ListboxSelect>>")
                                self.employee_listbox.selection_clear(0, tb.END)
                                self.employee_listbox.bind("<<ListboxSelect>>", self.on_employee_select)
                                print(f"🔍 [DEBUG] Seçim təmizləndi (selection_to_keep=None)")
                            except Exception as e:
                                print(f"❌ [DEBUG] Seçim təmizləmə xətası: {e}")
                            
                            # activate() çağrısını kaldırdıq - otomatik gezinməyə səbəb olur
                            # selection_set() kifayətdir və otomatik gezinməyə səbəb olmur
                    
                    restore_time = time.time() - restore_start
                    print(f"🔵 [DEBUG] [UI THREAD] ⏱️ Seçim bərpa tamamlandı: {restore_time:.3f}s")
                    
                    total_time = time.time() - self._refresh_start_time
                    print(f"🔵 [DEBUG] [UI THREAD] ⏱️ refresh_employee_list TAM BİTDİ: {total_time:.3f}s (delete: {self._refresh_delete_time:.3f}s, filter: {self._refresh_filter_time:.3f}s, group: {self._refresh_group_time:.3f}s, display: {display_time:.3f}s)")
                    return
                
                # DEBUG: Batch-i işlə - DETALLI LOGLAR
                print(f"🔵 [DEBUG] [UI THREAD] ⏱️ Batch işləməyə başladı: {start_idx}-{end_idx-1}/{len(self._refresh_items)}")
                insert_start = time.time()
                
                for idx in range(start_idx, end_idx):
                    item_start = time.time()
                    item_text, fg_color, bg_color, is_dept, name = self._refresh_items[idx]
                    
                    size_start = time.time()
                    item_index = self.employee_listbox.size()
                    size_time = time.time() - size_start
                    if size_time > 0.01:
                        print(f"⚠️ [DEBUG] [UI THREAD] ⏱️ listbox.size() çox uzun: {size_time:.3f}s")
                    
                    insert_item_start = time.time()
                    self.employee_listbox.insert(tb.END, item_text)
                    insert_item_time = time.time() - insert_item_start
                    if insert_item_time > 0.01:
                        print(f"⚠️ [DEBUG] [UI THREAD] ⏱️ listbox.insert() çox uzun: {insert_item_time:.3f}s, item: {item_text[:50]}")
                    
                    config_start = time.time()
                    self.employee_listbox.itemconfig(item_index, {'fg': fg_color, 'bg': bg_color})
                    config_time = time.time() - config_start
                    if config_time > 0.01:
                        print(f"⚠️ [DEBUG] [UI THREAD] ⏱️ itemconfig() çox uzun: {config_time:.3f}s, item: {item_text[:50]}")
                    
                    item_time = time.time() - item_start
                    if item_time > 0.05:  # 50ms-dən çox çəkərsə
                        print(f"⚠️ [DEBUG] [UI THREAD] ⏱️ Item işləməsi çox uzun: {item_time:.3f}s, item: {item_text[:50]}")
                
                insert_time = time.time() - insert_start
                batch_time = time.time() - batch_start
                self._refresh_batch_count += 1
                
                print(f"🔵 [DEBUG] [UI THREAD] ⏱️ Batch bitdi: batch={self._refresh_batch_count}, batch_time={batch_time:.3f}s, insert_time={insert_time:.3f}s, items={end_idx - start_idx}")
                
                # Növbəti batch-i planla
                self._refresh_batch_index = end_idx
                
                # DEBUG: update_idletasks() çağırışı
                if self._refresh_batch_count % 3 == 0:
                    idletasks_start = time.time()
                    print(f"🔵 [DEBUG] [UI THREAD] ⏱️ update_idletasks() çağırılır (batch={self._refresh_batch_count})...")
                    self.update_idletasks()
                    idletasks_time = time.time() - idletasks_start
                    print(f"🔵 [DEBUG] [UI THREAD] ⏱️ update_idletasks() bitdi: {idletasks_time:.3f}s")
                    if idletasks_time > 0.1:
                        print(f"⚠️ [DEBUG] [UI THREAD] ⚠️ update_idletasks() ÇOX UZUN: {idletasks_time:.3f}s - UI BLOKLANIR!")
                
                # DEBUG: after() çağırışı
                after_start = time.time()
                print(f"🔵 [DEBUG] [UI THREAD] ⏱️ after(1, process_batch) çağırılır...")
                self.after(1, process_batch)
                after_time = time.time() - after_start
                print(f"🔵 [DEBUG] [UI THREAD] ⏱️ after() bitdi: {after_time:.3f}s")
                if after_time > 0.01:
                    print(f"⚠️ [DEBUG] [UI THREAD] ⚠️ after() çox uzun: {after_time:.3f}s")
                
            except Exception as e:
                print(f"❌ [DEBUG] [UI THREAD] Batch processing xətası: {e}")
                import traceback
                print(f"❌ [DEBUG] [UI THREAD] Batch processing xəta traceback:\n{traceback.format_exc()}")
                self._refresh_in_progress = False
        
        # İlk batch-i başlat - 0ms gecikmə ilə dərhal başlat
        print(f"🔵 [DEBUG] [UI THREAD] İlk batch planlanır, items: {len(all_items)}")
        self.after(0, process_batch)

    def get_selected_employee_name(self):
        if not hasattr(self, 'employee_listbox') or not self.employee_listbox.curselection(): return None, None
        full_text = self.employee_listbox.get(self.employee_listbox.curselection()[0])
        
        # Şöbə başlığı seçilibsə, None qaytar (▶ və ya ▼ ilə başlayan)
        if full_text.strip().startswith("▶") or full_text.strip().startswith("▼"):
            return None, None
        
        clean_name = full_text.replace("● ", "").replace("○ ", "").split(" [")[0].split(" (")[0].strip()
        
        # Təhlükəsizlik yoxlaması: Adi istifadəçi yalnız öz şöbəsinin işçilərini seçə bilər
        if self.current_user['role'].strip() != 'admin':
            current_user_name = self.current_user.get('name', '')
            current_user_data = self.data.get(current_user_name, {})
            current_user_department = current_user_data.get('department', '') if isinstance(current_user_data, dict) else ''
            
            selected_emp_data = self.data.get(clean_name, {})
            selected_emp_department = selected_emp_data.get('department', '') if isinstance(selected_emp_data, dict) else ''
            
            if selected_emp_department != current_user_department:
                # Adi istifadəçi başqa şöbənin işçisini seçməyə çalışırsa, öz məlumatını qaytarırıq
                return f"● {current_user_name}", current_user_name
        
        return full_text, clean_name
    
    def _on_department_header_click(self, event):
        """Şöbə başlığına klik edildikdə çağırılır"""
        # Klik edilən item-in index-ini tap
        widget = event.widget
        index = widget.nearest(event.y)
        item_text = widget.get(index)
        
        # Şöbə başlığı olub-olmadığını yoxla
        if "━━━" in item_text:
            # Şöbə adını çıxar
            dept_name = item_text.replace("━━━", "").strip()
            dept_name = dept_name.strip()
            
            # Şöbə görünürlüyünü dəyişdir
            if dept_name in self.department_visibility:
                self.department_visibility[dept_name] = not self.department_visibility[dept_name]
            else:
                self.department_visibility[dept_name] = False
            
            # List-i yenilə
            self.refresh_employee_list()
            # Event-i burada dayandır ki, normal seçim işləməsin
            return "break"
    
    def _toggle_search(self):
        """Axtarış panelini açır/bağlayır"""
        # Yalnız admin üçün
        if not self.is_admin or self.search_button is None:
            return
        
        if self.search_panel is None or not self.search_panel.winfo_exists():
            # Panel yoxdursa yarad - employee_frame-də, listbox-dan əvvəl
            # İşçilər bölməsini tap
            employee_frame = None
            for widget in self.left_frame.winfo_children():
                if isinstance(widget, tk.Frame):
                    # employee_wrapper içində employee_frame-i tap
                    for child in widget.winfo_children():
                        if isinstance(child, tb.LabelFrame) and child.cget('text') == 'İşçilər':
                            employee_frame = child
                            break
                    if employee_frame:
                        break
            
            if employee_frame is None:
                return
            
            # Listbox frame-i tap
            listbox_frame = None
            for widget in employee_frame.winfo_children():
                if hasattr(widget, 'winfo_children') and self.employee_listbox in widget.winfo_children():
                    listbox_frame = widget
                    break
            
            self.search_panel = tk.Frame(employee_frame, bg=self.employee_frame_bg)
            # Listbox frame-dən əvvəl yerləşdir - listbox-u aşağıya sıxacaq
            if listbox_frame:
                self.search_panel.pack(fill='x', pady=(2, 3), padx=3, before=listbox_frame)  # Listbox-dan əvvəl
            else:
                self.search_panel.pack(fill='x', pady=(2, 3), padx=3)  # Fallback
            
            # Axtarış input
            search_label = tk.Label(self.search_panel, text="Axtarış:", font=(self.main_font, 9), bg=self.search_panel.cget('bg'))
            search_label.pack(side='left', padx=(0, 5))
            
            self.search_var = tk.StringVar()
            self.search_var.trace('w', lambda *args: self._on_search_change())
            search_entry = tk.Entry(self.search_panel, textvariable=self.search_var, font=(self.main_font, 10))
            search_entry.pack(side='left', fill='x', expand=True, padx=(0, 5))
            search_entry.focus()
            
            # Bağla düyməsi
            close_btn = tk.Button(self.search_panel, text="✕", command=self._close_search, 
                                bg=self.search_panel.cget('bg'), relief='flat', font=(self.main_font, 10), width=2)
            close_btn.pack(side='right')
            
            self.search_text = ""
        else:
            # Panel varsa bağla
            self._close_search()
    
    def _close_search(self):
        """Axtarış panelini bağlayır"""
        if self.search_panel and self.search_panel.winfo_exists():
            self.search_panel.destroy()
            self.search_panel = None
            self.search_text = ""
            if hasattr(self, 'search_var'):
                self.search_var.set("")
            self.refresh_employee_list()
    
    def _on_search_change(self):
        """Axtarış mətnində dəyişiklik olduqda çağırılır"""
        if hasattr(self, 'search_var'):
            self.search_text = self.search_var.get()
            self.refresh_employee_list()
    
    def _toggle_filter(self):
        """Filtr panelini açır/bağlayır"""
        # Yalnız admin üçün
        if not self.is_admin or self.filter_button is None:
            return
        
        if self.filter_panel is None or not self.filter_panel.winfo_exists():
            # Panel yoxdursa yarad - employee_frame-də, listbox-dan əvvəl
            # İşçilər bölməsini tap
            employee_frame = None
            for widget in self.left_frame.winfo_children():
                if isinstance(widget, tk.Frame):
                    # employee_wrapper içində employee_frame-i tap
                    for child in widget.winfo_children():
                        if isinstance(child, tb.LabelFrame) and child.cget('text') == 'İşçilər':
                            employee_frame = child
                            break
                    if employee_frame:
                        break
            
            if employee_frame is None:
                return
            
            # Listbox frame-i tap
            listbox_frame = None
            for widget in employee_frame.winfo_children():
                if hasattr(widget, 'winfo_children') and self.employee_listbox in widget.winfo_children():
                    listbox_frame = widget
                    break
            
            self.filter_panel = tk.Frame(employee_frame, bg=self.employee_frame_bg)
            # Listbox frame-dən əvvəl yerləşdir - axtarış panelindən sonra
            # Əgər axtarış paneli varsa, ondan sonra yerləşdir
            if listbox_frame:
                # Axtarış paneli varsa, ondan sonra yerləşdir
                if self.search_panel and self.search_panel.winfo_exists():
                    self.filter_panel.pack(fill='x', pady=(2, 3), padx=3, after=self.search_panel)  # Axtarışdan sonra
                else:
                    self.filter_panel.pack(fill='x', pady=(2, 3), padx=3, before=listbox_frame)  # Listbox-dan əvvəl
            else:
                self.filter_panel.pack(fill='x', pady=(2, 3), padx=3)  # Fallback
            
            # Filtr label
            filter_label = tk.Label(self.filter_panel, text="Şöbə:", font=(self.main_font, 9), bg=self.filter_panel.cget('bg'))
            filter_label.pack(side='left', padx=(0, 5))
            
            # Şöbələr combo
            self.department_filter_var = tk.StringVar()
            self.department_filter_var.trace('w', lambda *args: self._on_filter_change())
            
            # Şöbələri yüklə
            try:
                from database.departments_positions_queries import get_departments_for_combo
                departments = get_departments_for_combo()
                dept_options = ["Bütün şöbələr"] + [dept[1] for dept in departments]
            except:
                # Fallback: employees cədvəlindən unikalları götür
                try:
                    dept_options = ["Bütün şöbələr"]
                    if hasattr(self, 'data') and self.data:
                        unique_depts = set()
                        for emp_data in self.data.values():
                            if isinstance(emp_data, dict) and emp_data.get('department'):
                                unique_depts.add(emp_data.get('department'))
                        dept_options.extend(sorted(unique_depts))
                except:
                    dept_options = ["Bütün şöbələr"]
            
            department_combo = ttk.Combobox(self.filter_panel, textvariable=self.department_filter_var, 
                                          values=dept_options, state='readonly', width=20)
            department_combo.pack(side='left', padx=(0, 5))
            department_combo.set("Bütün şöbələr")
            
            # Bağla düyməsi
            close_btn = tk.Button(self.filter_panel, text="✕", command=self._close_filter, 
                                bg=self.filter_panel.cget('bg'), relief='flat', font=(self.main_font, 10), width=2)
            close_btn.pack(side='right')
            
            self.selected_department_filter = None
        else:
            # Panel varsa bağla
            self._close_filter()
    
    def _close_filter(self):
        """Filtr panelini bağlayır"""
        if self.filter_panel and self.filter_panel.winfo_exists():
            self.filter_panel.destroy()
            self.filter_panel = None
            self.selected_department_filter = None
            if hasattr(self, 'department_filter_var'):
                self.department_filter_var.set("Bütün şöbələr")
            self.refresh_employee_list()
    
    def _on_filter_change(self):
        """Filtr dəyişdikdə çağırılır"""
        if hasattr(self, 'department_filter_var'):
            selected = self.department_filter_var.get()
            if selected == "Bütün şöbələr":
                self.selected_department_filter = None
                # Bütün şöbələr seçildikdə, bütün şöbələri bağlı saxla
                if hasattr(self, 'department_visibility'):
                    for dept in self.department_visibility.keys():
                        self.department_visibility[dept] = False
            else:
                self.selected_department_filter = selected
                # Seçilmiş şöbəni aç, digərlərini bağla
                if hasattr(self, 'department_visibility'):
                    for dept in self.department_visibility.keys():
                        if dept == selected:
                            self.department_visibility[dept] = True  # Seçilmiş şöbəni aç
                        else:
                            self.department_visibility[dept] = False  # Digərlərini bağla
            self.refresh_employee_list()
    
    def edit_selected_employee(self):
        """Seçilmiş işçini redaktə etmək üçün forma pəncərəsini açır"""
        if self.current_user['role'].strip() != 'admin':
            messagebox.showwarning("Xəbərdarlıq", "Yalnız admin işçi redaktə edə bilər!")
            return
            
        full_text, selected_name = self.get_selected_employee_name()
        if not selected_name:
            messagebox.showwarning("Xəbərdarlıq", "Redaktə ediləcək işçi seçilməyib!")
            return
        
        # İşçi məlumatlarını al
        employee_info = self.data.get(selected_name, {})
        if not employee_info or isinstance(employee_info, (str, bool)):
            messagebox.showerror("Xəta", "İşçi məlumatları tapılmadı!")
            return
        
        # Employee form pəncərəsini aç
        try:
            from .employee_form_window import EmployeeFormWindow
            
            # Digər pəncərələri gizlət
            for widget in self.winfo_children():
                if hasattr(widget, 'pack_info'):
                    widget.pack_forget()
            
            # İşçi ID-ni əlavə et
            if 'db_id' in employee_info:
                employee_info['id'] = employee_info['db_id']
            employee_info['name'] = selected_name
            
            # Form pəncərəsini aç
            self.employee_form_page = EmployeeFormWindow(
                self,
                self.load_and_refresh_data,
                employee_info,
                main_app_ref=self
            )
            # Pəncərəni göstər
            self.employee_form_page.pack(fill="both", expand=True)
        except Exception as e:
            messagebox.showerror("Xəta", f"İşçi redaktə forması açıla bilmədi: {e}")
            logging.error(f"İşçi redaktə forması xətası: {e}")
    
    def add_new_employee(self):
        """Yeni işçi əlavə etmək üçün forma pəncərəsini açır"""
        if self.current_user['role'].strip() != 'admin':
            messagebox.showwarning("Xəbərdarlıq", "Yalnız admin yeni işçi əlavə edə bilər!")
            return
        
        # Employee form pəncərəsini aç (boş məlumatla)
        try:
            from .employee_form_window import EmployeeFormWindow
            
            # Digər pəncərələri gizlət
            for widget in self.winfo_children():
                if hasattr(widget, 'pack_info'):
                    widget.pack_forget()
            
            self.employee_form_page = EmployeeFormWindow(
                self,
                self.load_and_refresh_data,
                None,  # Yeni işçi üçün None
                main_app_ref=self
            )
            # Pəncərəni göstər
            self.employee_form_page.pack(fill="both", expand=True)
        except Exception as e:
            messagebox.showerror("Xəta", f"İşçi əlavə forması açıla bilmədi: {e}")
            logging.error(f"İşçi əlavə forması xətası: {e}")
        
    def delete_employee(self):
        """Seçilmiş işçini gizlədir (hide=true) - admin parolu tələb edir"""
        # Təhlükəsizlik yoxlaması: Yalnız admin işçi silə bilər
        if self.current_user['role'].strip() != 'admin':
            messagebox.showwarning("Xəbərdarlıq", "Yalnız admin işçiləri silə bilər!")
            return
            
        full_text, selected_name = self.get_selected_employee_name()
        if not selected_name:
            messagebox.showwarning("Xəbərdarlıq", "Gizlədiləcək işçi seçilməyib!")
            return
            
        # İşçi ID-sini tapırıq
        employee_id = None
        if hasattr(self, 'data') and self.data:
            for name, info in self.data.items():
                if name == selected_name and isinstance(info, dict):
                    employee_id = info.get('db_id')
                    break
        
        if not employee_id:
            messagebox.showerror("Xəta", f"'{selected_name}' işçisinin ID-si tapılmadı!")
            return
        
        # Admin parolunu soruşur
        from tkinter import simpledialog
        admin_password = simpledialog.askstring("Admin Parolu", 
                                              f"'{selected_name}' adlı işçini gizləmək üçün admin parolunu daxil edin:",
                                              show='*')
        
        if not admin_password:
            return
            
        if messagebox.askyesno("Təsdiq", f"'{selected_name}' adlı işçini gizləmək istədiyinizə əminsiniz?\n\nBu işçi artıq siyahıda görünməyəcək, amma məlumatları veritabanında saxlanılacaq."):
            if database.hide_employee(employee_id, admin_password, self.current_user.get('id')):
                messagebox.showinfo("Uğurlu", f"'{selected_name}' adlı işçi uğurla gizlədildi!")
                
                # Real-time notification göndər
                self.send_realtime_signal('employee_hidden', {
                    'employee_name': selected_name,
                    'employee_id': employee_id,
                    'hidden_by': self.current_user.get('name')
                })
                
                self.load_and_refresh_data()
            else:
                messagebox.showerror("Xəta", "İşçi gizlədilə bilmədi!")

    def permanently_delete_employee(self):
        """Seçilmiş işçini həqiqətən silir - admin parolu tələb edir"""
        # Təhlükəsizlik yoxlaması: Yalnız admin işçi silə bilər
        if self.current_user['role'].strip() != 'admin':
            messagebox.showwarning("Xəbərdarlıq", "Yalnız admin işçiləri silə bilər!")
            return
            
        full_text, selected_name = self.get_selected_employee_name()
        if not selected_name:
            messagebox.showwarning("Xəbərdarlıq", "Silinəcək işçi seçilməyib!")
            return
            
        # İşçi ID-sini tapırıq
        employee_id = None
        if hasattr(self, 'data') and self.data:
            for name, info in self.data.items():
                if name == selected_name and isinstance(info, dict):
                    employee_id = info.get('db_id')
                    break
        
        if not employee_id:
            messagebox.showerror("Xəta", f"'{selected_name}' işçisinin ID-si tapılmadı!")
            return
        
        # Admin parolunu soruşur
        from tkinter import simpledialog
        admin_password = simpledialog.askstring("Admin Parolu", 
                                              f"'{selected_name}' adlı işçini həqiqətən silmək üçün admin parolunu daxil edin:\n\nDİQQƏT: Bu əməliyyat geri alına bilməz!",
                                              show='*')
        
        if not admin_password:
            return
            
        if messagebox.askyesno("Təsdiq", f"'{selected_name}' adlı işçini həqiqətən silmək istədiyinizə əminsiniz?\n\nDİQQƏT: Bu əməliyyat geri alına bilməz və bütün məlumatlar itiriləcək!"):
            if database.permanently_delete_employee(employee_id, admin_password, self.current_user.get('id')):
                messagebox.showinfo("Uğurlu", f"'{selected_name}' adlı işçi həqiqətən silindi!")
                
                # Real-time notification göndər
                self.send_realtime_signal('employee_permanently_deleted', {
                    'employee_name': selected_name,
                    'employee_id': employee_id,
                    'deleted_by': self.current_user.get('name')
                })
                
                self.load_and_refresh_data()
            else:
                messagebox.showerror("Xəta", "İşçi silinə bilmədi!")

    def show_hidden_employees(self):
        """Gizlənmiş işçiləri göstərir"""
        # Təhlükəsizlik yoxlaması: Yalnız admin gizlənmiş işçiləri görə bilər
        if self.current_user['role'].strip() != 'admin':
            messagebox.showwarning("Xəbərdarlıq", "Yalnız admin gizlənmiş işçiləri görə bilər!")
            return
            
        hidden_employees = database.get_hidden_employees()
        if not hidden_employees:
            messagebox.showinfo("Məlumat", "Gizlənmiş işçi yoxdur!")
            return
        
        # Gizlənmiş işçilər pəncərəsi yaradırıq
        hidden_window = tk.Toplevel(self)
        hidden_window.title("Gizlənmiş İşçilər")
        hidden_window.geometry("600x400")
        hidden_window.resizable(True, True)
        
        # Pəncərəni mərkəzləşdiririk
        self._center_toplevel(hidden_window)
        
        # Başlıq
        title_label = tk.Label(hidden_window, text="Gizlənmiş İşçilər", font=("Segoe UI", 16, "bold"))
        title_label.pack(pady=10)
        
        # İşçilər siyahısı
        listbox_frame = tk.Frame(hidden_window)
        listbox_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        listbox = tk.Listbox(listbox_frame, font=("Segoe UI", 10))
        listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        scrollbar = tk.Scrollbar(listbox_frame, orient=tk.VERTICAL, command=listbox.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        listbox.config(yscrollcommand=scrollbar.set)
        
        # İşçiləri siyahıya əlavə edirik
        employee_data = {}
        for emp_id, name, total_days, is_active, max_sessions in hidden_employees:
            display_name = f"{name} (ID: {emp_id})"
            listbox.insert(tk.END, display_name)
            employee_data[display_name] = {
                'id': emp_id,
                'name': name,
                'total_days': total_days,
                'is_active': is_active,
                'max_sessions': max_sessions
            }
        
        # Düymələr
        button_frame = tk.Frame(hidden_window)
        button_frame.pack(fill=tk.X, padx=10, pady=10)
        
        def restore_employee():
            selection = listbox.curselection()
            if not selection:
                messagebox.showwarning("Xəbərdarlıq", "Bərpa ediləcək işçi seçilməyib!")
                return
            
            selected_display = listbox.get(selection[0])
            employee_info = employee_data[selected_display]
            
            if messagebox.askyesno("Təsdiq", f"'{employee_info['name']}' adlı işçini bərpa etmək istədiyinizə əminsiniz?"):
                if database.unhide_employee(employee_info['id']):
                    messagebox.showinfo("Uğurlu", f"'{employee_info['name']}' adlı işçi bərpa edildi!")
                    hidden_window.destroy()
                    self.load_and_refresh_data()
                else:
                    messagebox.showerror("Xəta", "İşçi bərpa edilə bilmədi!")
        
        def permanently_delete_selected():
            selection = listbox.curselection()
            if not selection:
                messagebox.showwarning("Xəbərdarlıq", "Silinəcək işçi seçilməyib!")
                return
            
            selected_display = listbox.get(selection[0])
            employee_info = employee_data[selected_display]
            
            # Admin parolunu soruşur
            from tkinter import simpledialog
            admin_password = simpledialog.askstring("Admin Parolu", 
                                                  f"'{employee_info['name']}' adlı işçini həqiqətən silmək üçün admin parolunu daxil edin:\n\nDİQQƏT: Bu əməliyyat geri alına bilməz!",
                                                  show='*')
            
            if not admin_password:
                return
                
            if messagebox.askyesno("Təsdiq", f"'{employee_info['name']}' adlı işçini həqiqətən silmək istədiyinizə əminsiniz?\n\nDİQQƏT: Bu əməliyyat geri alına bilməz və bütün məlumatlar itiriləcək!"):
                if database.permanently_delete_employee(employee_info['id'], admin_password, self.current_user['id']):
                    messagebox.showinfo("Uğurlu", f"'{employee_info['name']}' adlı işçi həqiqətən silindi!")
                    hidden_window.destroy()
                    self.load_and_refresh_data()
                else:
                    messagebox.showerror("Xəta", "İşçi silinə bilmədi!")
        
        restore_btn = tk.Button(button_frame, text="Seçilmiş İşçini Bərpa Et", command=restore_employee, bg="#4CAF50", fg="white", font=("Segoe UI", 10, "bold"))
        restore_btn.pack(side=tk.LEFT, padx=5)
        
        delete_btn = tk.Button(button_frame, text="Seçilmiş İşçini Həqiqətən Sil", command=permanently_delete_selected, bg="#f44336", fg="white", font=("Segoe UI", 10, "bold"))
        delete_btn.pack(side=tk.LEFT, padx=5)
        
        close_btn = tk.Button(button_frame, text="Bağla", command=hidden_window.destroy, bg="#2196F3", fg="white", font=("Segoe UI", 10, "bold"))
        close_btn.pack(side=tk.RIGHT, padx=5)

    def toggle_user_activity(self, user_id, new_status):
        # Təhlükəsizlik yoxlaması: Yalnız admin işçi statusunu dəyişə bilər
        if self.current_user['role'].strip() != 'admin':
            messagebox.showwarning("Xəbərdarlıq", "Yalnız admin işçi statusunu dəyişə bilər!")
            return
            
        _, selected_name = self.get_selected_employee_name()
        if selected_name:
            # İşçi ID-sini tapırıq
            employee_id = None
            if hasattr(self, 'data') and self.data:
                for name, info in self.data.items():
                    if name == selected_name and isinstance(info, dict):
                        employee_id = info.get('db_id')
                        break
            
            if not employee_id:
                messagebox.showerror("Xəta", f"'{selected_name}' işçisinin ID-si tapılmadı!")
                return
            
            database.set_user_activity(employee_id, new_status)
            if new_status is False:
                command_queries.issue_immediate_logout_command([employee_id])
                session_queries.force_remove_sessions_by_user_id([employee_id])
            
            # Real-time notification göndər
            self.send_realtime_signal('employee_status_changed', {
                'employee_name': selected_name,
                'employee_id': employee_id,
                'new_status': new_status,
                'changed_by': self.current_user.get('name')
            })
            
            self.load_and_refresh_data(selection_to_keep=selected_name)
    
    def show_summary_panel(self, parent_frame, info):
        """İşçinin məzuniyyət xülasəsini göstərir"""
        import logging
        # Debug mesajlarını azaldıq - yalnız xəta halında log yazırıq
        # logging.debug("=" * 50)
        # logging.debug("SHOW_SUMMARY_PANEL ÇAĞIRILDI")
        # logging.debug(f"İşçi adı: {info.get('name', 'Naməlum')}")
        # logging.debug(f"İşçi ID: {info.get('db_id', 'Naməlum')}")
        
        umumi_gun = info.get("umumi_gun", 0)
        # logging.debug(f"Umumi gün: {umumi_gun}")
        
        # DÜZƏLİŞ: İstifadə olunmuş günləri düzgün hesablayırıq
        istifade_olunmus_gun_cemi = 0
        for v in info.get("goturulen_icazeler", []):
            if v.get('status') == 'approved' and not v.get('aktiv_deyil', False):
                muddet = mezuniyyet_muddetini_hesabla(v['baslama'], v['bitme'])
                istifade_olunmus_gun_cemi += muddet
                logging.debug(f"Məzuniyyət - {v['baslama']} - {v['bitme']}: {muddet} gün")
        
        logging.debug(f"İstifadə olunmuş günlər cəmi: {istifade_olunmus_gun_cemi}")
        
        qaliq_gun = max(0, umumi_gun - istifade_olunmus_gun_cemi)
        logging.debug(f"Qalıq gün: {qaliq_gun}")
        logging.debug("=" * 50)
        
        # Köhnə xülasə panellərini təmizləyirik
        for widget in parent_frame.winfo_children():
            if isinstance(widget, ttk.Separator) or (hasattr(widget, 'is_summary_container') and widget.is_summary_container):
                widget.destroy()

        separator1 = ttk.Separator(parent_frame)
        separator1.pack(fill='x', pady=5)
        
        summary_container = ttk.Frame(parent_frame, style="Card.TFrame")
        summary_container.pack(fill='x')
        summary_container.is_summary_container = True
        
        self._create_summary_labels(summary_container, umumi_gun, istifade_olunmus_gun_cemi, qaliq_gun)
        
        separator2 = ttk.Separator(parent_frame)
        separator2.pack(fill='x', pady=5)

    def _create_summary_labels(self, parent, total, used, remaining):
        frame_total = ttk.Frame(parent, style="Card.TFrame"); frame_total.pack(side='left', padx=10)
        ttk.Label(frame_total, text="İllik Hüquq:", style="Summary.TLabel").pack(); ttk.Label(frame_total, text=f"{total} gün", style="SummaryValue.TLabel").pack()
        frame_used = ttk.Frame(parent, style="Card.TFrame"); frame_used.pack(side='left', padx=10)
        ttk.Label(frame_used, text="İstifadə:", style="Summary.TLabel").pack(); ttk.Label(frame_used, text=f"{used} gün", style="SummaryValue.TLabel").pack()
        frame_rem = ttk.Frame(parent, style="Card.TFrame"); frame_rem.pack(side='left', padx=10)
        ttk.Label(frame_rem, text="Qalıq:", style="Summary.TLabel").pack(); ttk.Label(frame_rem, text=f"{remaining} gün", style="SummaryValue.TLabel", foreground="green" if remaining >= 0 else "red").pack()

    def _center_toplevel(self, toplevel_window):
        """Pəncərəni ana pəncərənin mərkəzində yerləşdirir və kənardan çıxmasını qarşısını alır."""
        toplevel_window.update_idletasks()
        main_app = self.winfo_toplevel()
        
        # Ana pəncərənin koordinatları və ölçüləri
        main_x = main_app.winfo_x()
        main_y = main_app.winfo_y()
        main_width = main_app.winfo_width()
        main_height = main_app.winfo_height()
        
        # Pəncərənin ölçüləri
        window_width = toplevel_window.winfo_width()
        window_height = toplevel_window.winfo_height()
        
        # Mərkəz koordinatları
        center_x = main_x + (main_width - window_width) // 2
        center_y = main_y + (main_height - window_height) // 2
        
        # Pəncərənin kənardan çıxmamasını təmin edirik
        # Sol kənar
        if center_x < main_x:
            center_x = main_x + 10  # 10 piksel məsafə
        
        # Sağ kənar
        if center_x + window_width > main_x + main_width:
            center_x = main_x + main_width - window_width - 10
        
        # Yuxarı kənar
        if center_y < main_y:
            center_y = main_y + 10
        
        # Aşağı kənar
        if center_y + window_height > main_y + main_height:
            center_y = main_y + main_height - window_height - 10
        
        # Pəncərənin ölçüsünü məhdudlaşdırırıq
        max_width = min(window_width, main_width - 100)  # Ana pəncərədən 100 piksel kiçik
        max_height = min(window_height, main_height - 100)  # Ana pəncərədən 100 piksel kiçik
        
        # Əgər pəncərə çox böyükdürsə, ölçüsünü dəyişdiririk
        if window_width > max_width or window_height > max_height:
            toplevel_window.geometry(f"{max_width}x{max_height}")
            toplevel_window.update_idletasks()
            # Yeni ölçülərlə koordinatları yenidən hesablayırıq
            window_width = toplevel_window.winfo_width()
            window_height = toplevel_window.winfo_height()
            center_x = main_x + (main_width - window_width) // 2
            center_y = main_y + (main_height - window_height) // 2
        
        # Pəncərəni yerləşdiririk
        toplevel_window.geometry(f"+{center_x}+{center_y}")
        toplevel_window.lift()
        
        # Pəncərənin ana pəncərəyə bağlı olduğunu təmin edirik
        toplevel_window.transient(main_app)
        toplevel_window.grab_set()
        
        # Pəncərənin yenidən ölçüləndirilməsini məhdudlaşdırırıq
        toplevel_window.resizable(True, True)
        toplevel_window.maxsize(main_width - 50, main_height - 50)  # Ana pəncərədən 50 piksel kiçik

    def open_user_management(self):
        # Təhlükəsizlik yoxlaması: Yalnız admin istifadəçi idarəetməsi səhifəsini aça bilər
        if self.current_user['role'].strip() != 'admin':
            messagebox.showwarning("Xəbərdarlıq", "Yalnız admin istifadəçi idarəetməsi səhifəsini aça bilər!")
            return
        
        # Mövcud səhifələri gizlət
        self.hide_all_views()
        
        # İstifadəçi idarəetməsi səhifəsini yarat və göstər
        if not hasattr(self, 'user_management_page'):
            self.user_management_page = UserManagementPage(self.right_frame, 
                                                          main_app_ref=self, 
                                                          on_back=self.show_main_view)
        
        self.user_management_page.place(in_=self.right_frame, x=0, y=0, relwidth=1, relheight=1)
        self.current_view = 'user_management'

    def open_tools_window(self):
        # Təhlükəsizlik yoxlaması: Yalnız admin alətlər pəncərəsini aça bilər
        if self.current_user['role'].strip() != 'admin':
            messagebox.showwarning("Xəbərdarlıq", "Yalnız admin alətlər pəncərəsini aça bilər!")
            return
            
        try:
            # Mövcud səhifələri gizlət
            self.hide_all_views()
            
            # Alətlər səhifəsini yarat və göstər
            if not hasattr(self, 'tools_page'):
                from .tools_window import ToolsPage
                self.tools_page = ToolsPage(self.right_frame, on_back=self.show_main_view)
            
            self.tools_page.place(in_=self.right_frame, x=0, y=0, relwidth=1, relheight=1)
            self.current_view = 'tools'
            
        except Exception as e:
            messagebox.showerror("Pəncərə Xətası", f"Alətlər pəncərəsini açmaq mümkün olmadı:\n{e}")

    def open_error_viewer(self):
        # Təhlükəsizlik yoxlaması: Yalnız admin xəta jurnalı səhifəsini aça bilər
        if self.current_user['role'].strip() != 'admin':
            messagebox.showwarning("Xəbərdarlıq", "Yalnız admin xəta jurnalı səhifəsini aça bilər!")
            return
            
        try:
            # Mövcud səhifələri gizlət
            self.hide_all_views()
            
            # Xəta jurnalı səhifəsini yarat və göstər
            if not hasattr(self, 'error_viewer_page'):
                self.error_viewer_page = ErrorViewerPage(self.right_frame, 
                                                        main_app_ref=self, 
                                                        on_back=self.show_main_view)
            
            self.error_viewer_page.place(in_=self.right_frame, x=0, y=0, relwidth=1, relheight=1)
            self.current_view = 'error_viewer'
        except Exception as e:
            messagebox.showerror("Səhifə Xətası", f"Xəta jurnalı səhifəsini açmaq mümkün olmadı:\n{e}")
            
    def open_notifications_window(self):
        # Təhlükəsizlik yoxlaması: Hər istifadəçi öz bildirişlərini görə bilər
        # Bu yoxlama notifications_window.py-də də edilməlidir
        if self.notif_window and self.notif_window.winfo_exists():
            self.notif_window.lift()
            return
        self.notif_window = NotificationsWindow(parent=self, user_id=self.current_user['id'], on_notif_click_callback=self._on_notification_click, main_app_ref=self)
        self.opened_windows.append(self.notif_window)
        self.notif_window.protocol("WM_DELETE_WINDOW", lambda: (self.load_and_refresh_data(), self.notif_window.destroy(), self.opened_windows.remove(self.notif_window)))
        self._center_toplevel(self.notif_window)
    
    def open_archive_view_window(self):
        # Təhlükəsizlik yoxlaması: Yalnız admin arxiv pəncərəsini aça bilər
        if self.current_user['role'].strip() != 'admin':
            messagebox.showwarning("Xəbərdarlıq", "Yalnız admin arxiv pəncərəsini aça bilər!")
            return
            
        win = ArchiveWindow(self, self.data, self.current_user)
        self.opened_windows.append(win)
        self._center_toplevel(win)

    def open_employee_form_window(self, is_new=False):
        try:
            # Təhlükəsizlik yoxlaması: Yalnız admin işçi əlavə edə və ya düzəldə bilər
            if self.current_user['role'].strip() != 'admin':
                messagebox.showwarning("Xəbərdarlıq", "Yalnız admin işçi əlavə edə və ya düzəldə bilər!")
                return
                
            employee_to_edit = None
            if not is_new:
                _, selected_name = self.get_selected_employee_name()
                if not selected_name: 
                    messagebox.showwarning("Xəbərdarlıq", "Düzəliş ediləcək işçi seçilməyib!")
                    return
                
                # İşçinin tam məlumatlarını veritabanından al
                if selected_name in self.data:
                    employee_to_edit = self.data[selected_name].copy()  # Kopya yarat
                    employee_to_edit['name'] = selected_name
                    
                    # İşçinin ID-sini əlavə et
                    if 'db_id' in self.data[selected_name]:
                        employee_to_edit['id'] = self.data[selected_name]['db_id']
                    
                    logging.info(f"İşçi məlumatları yükləndi: {selected_name} - {employee_to_edit}")
                else:
                    messagebox.showerror("Xəta", f"'{selected_name}' işçisinin məlumatları tapılmadı!")
                    return
            
            # Mövcud view-ləri təmizlə
            for widget in self.winfo_children():
                if hasattr(widget, 'pack_info'):
                    widget.pack_forget()
            
            # Employee form window-u yarat və göstər
            from .employee_form_window import EmployeeFormWindow
            self.employee_form_page = EmployeeFormWindow(self, self.load_and_refresh_data, employee_to_edit, main_app_ref=self)
            self.employee_form_page.pack(fill="both", expand=True)
            
            # Frame-in arxa fonunu təyin et
            self.employee_form_page.configure(bg='white')
            
        except Exception as e:
            logging.error(f"İşçi düzəliş pəncərəsi açılarkən xəta: {e}")
            messagebox.showerror("Xəta", f"İşçi düzəliş pəncərəsi açıla bilmədi: {e}")

    def _confirm_and_start_new_year(self):
        # Təhlükəsizlik yoxlaması: Yalnız admin yeni məzuniyyət ili başlada bilər
        if self.current_user['role'].strip() != 'admin':
            messagebox.showwarning("Xəbərdarlıq", "Yalnız admin yeni məzuniyyət ili başlada bilər!")
            return
            
        employees_to_archive = database.get_employees_with_archivable_vacations()
        win = Toplevel(self); win.title("Yeni Məzuniyyət İli - Arxivləmə Təsdiqi"); win.geometry("500x600"); win.transient(self); win.grab_set()
        checkbox_vars = {}

        def do_archive():
            selected_ids = [emp_id for emp_id, var in checkbox_vars.items() if var.get()]
            if not selected_ids: messagebox.showwarning("Seçim Yoxdur", "Arxivləmək üçün heç bir işçi seçilməyib.", parent=win); return
            if messagebox.askyesno("Son Təsdiq", f"{len(selected_ids)} işçi üçün yeni məzuniyyət ili başlasın?", parent=win):
                if database.start_new_vacation_year(selected_ids):
                    win.destroy()
                    self.load_and_refresh_data()

        top_frame = ttk.Frame(win, padding=10); top_frame.pack(fill='x')
        select_all_var = tb.BooleanVar()
        
        employees_by_id = {}
        for emp_id, name, count in employees_to_archive:
            employees_by_id[emp_id] = {'can_be_archived': count > 0}

        def toggle_all():
            for emp_id, var in checkbox_vars.items():
                if employees_by_id[emp_id]['can_be_archived']:
                    var.set(select_all_var.get())
        
        ttk.Checkbutton(top_frame, text="Hamısını Seç (Arxivlənə bilənləri)", variable=select_all_var, command=toggle_all).pack(side='left')
        ttk.Button(top_frame, text="Seçilənləri Arxivlə", command=do_archive).pack(side='right')

        canvas = tb.Canvas(win); scrollbar = ttk.Scrollbar(win, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas); scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw"); canvas.configure(yscrollcommand=scrollbar.set)
        
        for emp_id, name, count in employees_to_archive:
            var = tb.BooleanVar()
            checkbox_vars[emp_id] = var
            
            label_color = "black" if employees_by_id[emp_id]['can_be_archived'] else "gray"
            cb_state = "normal" if employees_by_id[emp_id]['can_be_archived'] else "disabled"
            row_frame = ttk.Frame(scrollable_frame, padding=(5,2))
            cb = ttk.Checkbutton(row_frame, variable=var, state=cb_state); cb.pack(side='left')
            ttk.Label(row_frame, text=f"{name} ({count} məzuniyyət)", foreground=label_color).pack(side='left')
            row_frame.pack(fill='x', padx=10)

        canvas.pack(side="left", fill="both", expand=True); scrollbar.pack(side="right", fill="y")
        self._center_toplevel(win)

    def _on_notification_click(self, notif_id, employee_id, vacation_id):
        # Təhlükəsizlik yoxlaması: Adi istifadəçi yalnız öz bildirişlərini görə bilər
        if self.current_user['role'].strip() != 'admin':
            # Adi istifadəçi üçün yalnız öz bildirişlərini oxuya bilər
            # Bu yoxlama notifications_window.py-də də edilməlidir
            pass
            
        database.mark_notifications_as_read([notif_id])
        if employee_id:
            self.show_employee_by_id(employee_id)
            if 'employee_details' in self.views and hasattr(self.views['employee_details'], 'highlight_vacation'):
                self.after(100, lambda: self.views['employee_details'].highlight_vacation(vacation_id))
        else:
            self.load_and_refresh_data()
            
    def _update_notification_button(self):
        """Bildiriş düyməsini yeniləyir - qırmızı badge və animasiya ilə - asinxron"""
        if not hasattr(self, 'notifications_button'):
            return
        
        # Database sorğusunu asinxron et - UI bloklanmasın
        import threading
        def update_badge_async():
            try:
                print(f"🔵 [DEBUG] _update_notification_button: Database sorğusu başladı...")
                unread_count = database.get_unread_notifications_for_user(self.current_user['id'])
                print(f"🔵 [DEBUG] _update_notification_button: Database sorğusu bitdi, unread_count={unread_count}")
                
                # UI thread-də badge-i yenilə
                def update_ui():
                    try:
                        # Badge-i tap
                        badge = None
                        if hasattr(self.notifications_button, 'badge'):
                            badge = self.notifications_button.badge
                        elif hasattr(self.notifications_button, 'winfo_children'):
                            # Container-dan badge-i tap
                            for child in self.notifications_button.winfo_children():
                                if hasattr(child, 'badge'):
                                    badge = child.badge
                                    break
                        
                        if badge:
                            if unread_count > 0:
                                # Badge-i göstər və sayını yenilə
                                badge.config(text=str(unread_count) if unread_count < 100 else '99+')
                                # Badge-i iconun sağ yuxarı küncünə yerləşdir - yarısı icondan çıxacaq
                                badge.place(relx=1.0, rely=0.0, anchor='ne', x=2, y=-2)
                                
                                # Animasiya başlat (əgər işləmirsə)
                                if not hasattr(self.notifications_button, 'animation_running'):
                                    self.notifications_button.animation_running = False
                                if not self.notifications_button.animation_running:
                                    self._start_notification_badge_animation(badge)
                            else:
                                # Badge-i gizlət və animasiyanı dayandır
                                badge.place_forget()
                                self._stop_notification_badge_animation()
                    except Exception as e:
                        logging.warning(f"Bildiriş düyməsi UI yenilənərkən xəta: {e}")
                
                # UI thread-də yenilə
                self.after(0, update_ui)
            except Exception as e:
                logging.warning(f"Bildiriş düyməsi yenilənərkən xəta: {e}")
                print(f"❌ [DEBUG] _update_notification_button xətası: {e}")
        
        # Asinxron thread-də işlə
        thread = threading.Thread(target=update_badge_async, daemon=True, name="NotificationUpdate")
        thread.start()
    
    def _start_notification_badge_animation(self, badge):
        """Bildiriş badge animasiyasını başlat - yanıb-sönmə"""
        if not badge or not badge.winfo_exists():
            return
        
        if not hasattr(self.notifications_button, 'animation_running'):
            self.notifications_button.animation_running = False
        
        # Əgər animasiya artıq işləyirsə, yenidən başlatma
        if self.notifications_button.animation_running:
            return
        
        self.notifications_button.animation_running = True
        
        def animate(visible=True):
            if not hasattr(self, 'notifications_button') or not self.notifications_button.animation_running:
                return
            
            if not badge or not badge.winfo_exists():
                self.notifications_button.animation_running = False
                return
            
            try:
                if visible:
                    # Badge-i iconun sağ yuxarı küncünə yerləşdir
                    badge.place(relx=1.0, rely=0.0, anchor='ne', x=2, y=-2)
                    # Daha parlaq qırmızı
                    badge.config(bg='#ff0000')
                else:
                    # Daha tünd qırmızı
                    badge.config(bg='#dc3545')
                
                # Növbəti animasiya addımını planlaşdır
                if self.notifications_button.animation_running:
                    self.notifications_button.animation_job = self.after(500, lambda: animate(not visible))
            except Exception:
                self.notifications_button.animation_running = False
        
        # Animasiyanı başlat
        animate(True)
    
    def _stop_notification_badge_animation(self):
        """Bildiriş badge animasiyasını dayandır"""
        if hasattr(self, 'notifications_button') and hasattr(self.notifications_button, 'animation_running'):
            self.notifications_button.animation_running = False
            if hasattr(self.notifications_button, 'animation_job') and self.notifications_button.animation_job:
                try:
                    self.after_cancel(self.notifications_button.animation_job)
                except Exception:
                    pass
    
    def _auto_refresh_data(self):
        if not self.vacation_panel_active:
            # Avtomatik yeniləmə zamanı yalnız bildirişləri yeniləyirik
            self._update_notification_button()
            # Məlumatları yalnız hər 2 dəqiqədə bir yeniləyirik (daha tez refresh)
            if not hasattr(self, '_last_data_refresh'):
                self._last_data_refresh = 0
            
            import time
            current_time = time.time()
            if current_time - self._last_data_refresh > 120:  # 2 dəqiqə - daha tez refresh
                logging.info("Avtomatik yeniləmə - məlumatlar yenilənir...")
                self.data = database.load_data_for_user(self.current_user, force_refresh=False)
                self._last_data_refresh = current_time
                self.refresh_employee_list()
                
                # Status mesajı göstər
                self.update_status_label.config(text="🔄 Avtomatik yeniləmə tamamlandı")
        self.auto_refresh_timer = self.after(60000, self._auto_refresh_data)  # 1 dəqiqə - daha tez refresh
    
    def _check_for_update(self):
        """Versiya yoxlamasını edir"""
        logging.info("_check_for_update çağırıldı")
        try:
            # UnifiedApplication-dən versiya yoxlaması funksiyasını çağırırıq
            if hasattr(self.master, 'check_for_update'):
                logging.info("master.check_for_update çağırılır")
                self.master.check_for_update()
            else:
                logging.warning("master.check_for_update mövcud deyil")
        except Exception as e:
            logging.error(f"Versiya yoxlaması zamanı xəta: {e}")

    def _check_for_commands(self):
        command = command_queries.get_pending_commands(self.current_user['id'])
        if command:
            self._handle_system_command(command)
        self.command_check_timer = self.after(5000, self._check_for_commands)  # 5 saniyədə bir

    def _handle_system_command(self, command):
        command_queries.mark_command_as_executed(command['id'])

        if command['type'] == 'IMMEDIATE_LOGOUT':
            # Admin özünə göndərilən əmri ignore et - sadə həll
            if hasattr(self, 'current_user') and self.current_user.get('role') == 'admin':
                logging.info("Admin özünə göndərilən çıxış əmri ignore edildi")
                return
            self.after(0, self.logout_callback, "Administrator tərəfindən sistemdən çıxış edildiniz.")
        elif command['type'] == 'TIMED_LOGOUT':
            # Admin özünə göndərilən əmri ignore et - sadə həll
            if hasattr(self, 'current_user') and self.current_user.get('role') == 'admin':
                logging.info("Admin özünə göndərilən vaxtlı çıxış əmri ignore edildi")
                return
            if self.master_logout_timer_id: self.after_cancel(self.master_logout_timer_id)
            try:
                logout_time = datetime.fromisoformat(command['value'])
                self._start_master_logout_timer(logout_time)
                self._show_visual_timer_window(logout_time)
            except (ValueError, TypeError): pass

    def _start_master_logout_timer(self, logout_time):
        now = datetime.now()
        remaining_ms = max(0, (logout_time - now).total_seconds() * 1000)
        if remaining_ms > 0:
            self.master_logout_timer_id = self.after(int(remaining_ms), self._execute_final_logout)

    def _execute_final_logout(self):
        self.master_logout_timer_id = None
        self.after(0, self.logout_callback, "Ayrılmış vaxt bitdiyi üçün sistemdən çıxış edilir.")

    def _show_visual_timer_window(self, logout_time):
        timer_window = Toplevel(self)
        timer_window.title("Sistem Mesajı")
        timer_window.transient(self)
        self.update_idletasks()
        x = self.winfo_rootx() + self.winfo_width() - 420
        y = self.winfo_rooty() + self.winfo_height() - 200
        timer_window.geometry(f"400x150+{x}+{y}")
        timer_window.resizable(False, False)
        
        main_frame = ttk.Frame(timer_window, padding=20)
        main_frame.pack(expand=True, fill='both')
        
        ttk.Label(main_frame, text="Administrator tərəfindən çıxış tələbi!", font=(self.main_font, 12, "bold"), foreground="red").pack(pady=(0, 5))
        ttk.Label(main_frame, text="Proqram göstərilən vaxtda bağlanacaq.").pack(pady=(0, 10))
        
        timer_label = ttk.Label(main_frame, text="", font=(self.main_font, 18, "bold"))
        timer_label.pack(pady=5)

        def update_visual_timer():
            if not timer_window.winfo_exists(): return
            now = datetime.now()
            remaining = logout_time - now
            if remaining.total_seconds() < 1:
                timer_window.destroy()
            else:
                minutes, seconds = divmod(int(remaining.total_seconds()), 60)
                timer_label.config(text=f"{minutes:02d}:{seconds:02d}")
                timer_window.after(1000, update_visual_timer)
        update_visual_timer()
        
    def _create_vacation_panel(self):
        logging.info("=== _create_vacation_panel başladı ===")
        print("🔄 DEBUG: _create_vacation_panel başladı")
        
        try:
            # Callback funksiyalarını təyin et
            def on_save():
                try:
                    logging.info("on_save callback çağırıldı")
                    print("💾 DEBUG: on_save callback çağırıldı")
                    print(f"💾 DEBUG: on_save - self tipi: {type(self)}")
                    print(f"💾 DEBUG: on_save - _save_vacation_from_panel mövcuddur: {hasattr(self, '_save_vacation_from_panel')}")
                    self._safe_flush_stdout()
                    
                    # EXE-də işləmək üçün async şəkildə çağır
                    try:
                        root = self.winfo_toplevel()
                        if root and root.winfo_exists():
                            root.after(0, self._save_vacation_from_panel)
                            print("💾 DEBUG: on_save - root.after(0) ilə çağırıldı")
                        else:
                            self.after(0, self._save_vacation_from_panel)
                            print("💾 DEBUG: on_save - self.after(0) ilə çağırıldı")
                    except Exception as after_error:
                        print(f"⚠️ DEBUG: on_save - after() xətası: {after_error}, birbaşa çağırılır...")
                        # Son çarə - birbaşa çağır
                        self._save_vacation_from_panel()
                except Exception as e:
                    logging.error(f"on_save callback xətası: {e}")
                    print(f"❌ DEBUG: on_save callback xətası: {e}")
                    import traceback
                    traceback.print_exc()
                    messagebox.showerror("Xəta", f"Sorğu göndərilərkən xəta: {e}", parent=self)
                
            def on_close():
                logging.info("on_close callback çağırıldı")
                print("❌ DEBUG: on_close callback çağırıldı")
                self.toggle_vacation_panel(show=False)
            
            # Parent widget-ı yoxla - cari employee_details view-dan istifadə et
            parent_widget = self.views.get('employee_details')
            print(f"🔍 DEBUG: Parent widget: {parent_widget}")
            print(f"🔍 DEBUG: Parent widget tipi: {type(parent_widget)}")
            
            if parent_widget:
                print(f"🔍 DEBUG: Parent widget winfo_exists: {parent_widget.winfo_exists()}")
                print(f"🔍 DEBUG: Parent widget winfo_viewable: {parent_widget.winfo_viewable()}")
                print(f"🔍 DEBUG: Parent widget path: {parent_widget}")
            
            # VacationPanel yarat
            print("🏗️ DEBUG: VacationPanel yaradılır...")
            try:
                self.vacation_form_panel = VacationPanel(parent_widget, self.main_font, on_save, on_close, employee_name=None)
                print(f"✅ DEBUG: VacationPanel yaradıldı: {self.vacation_form_panel}")
                
                # Panel widget-lərinin mövcudluğunu yoxla
                if self.vacation_form_panel:
                    print(f"🔍 DEBUG: Panel winfo_exists: {self.vacation_form_panel.winfo_exists()}")
                    print(f"🔍 DEBUG: Panel winfo_viewable: {self.vacation_form_panel.winfo_viewable()}")
                    print(f"🔍 DEBUG: Panel path: {self.vacation_form_panel}")
                else:
                    print("❌ DEBUG: VacationPanel yaradıla bilmədi")
            except Exception as e:
                print(f"❌ DEBUG: VacationPanel yaradılarkən xəta: {e}")
                self.vacation_form_panel = None
            
            logging.info("=== _create_vacation_panel tamamlandı ===")
            print("✅ DEBUG: _create_vacation_panel tamamlandı")
            
        except Exception as e:
            logging.error(f"_create_vacation_panel xətası: {e}")
            print(f"❌ DEBUG: _create_vacation_panel xətası: {e}")
            import traceback
            error_traceback = traceback.format_exc()
            logging.error(f"Traceback: {error_traceback}")
            print(f"📋 DEBUG: Traceback: {error_traceback}")
            raise

    def _close_vacation_windows(self):
        """Açıq məzuniyyət sorğusu pəncərələrini bağlayır"""
        try:
            print("🔍 DEBUG: Məzuniyyət pəncərəsi bağlanır...")
            
            # Məzuniyyət pəncərəsini bağla
            if hasattr(self, 'current_vacation_window') and self.current_vacation_window:
                try:
                    print(f"🗑️ DEBUG: Məzuniyyət pəncərəsi bağlanır: {self.current_vacation_window}")
                    if self.current_vacation_window.winfo_exists():
                        self.current_vacation_window.place_forget()
                        self.current_vacation_window.destroy()
                    self.current_vacation_window = None
                    print("✅ DEBUG: Məzuniyyət pəncərəsi bağlandı")
                except Exception as e:
                    print(f"❌ DEBUG: Məzuniyyət pəncərəsi bağlanarkən xəta: {e}")
            
            # Vacation form panel-i də bağla
            if hasattr(self, 'vacation_form_panel') and self.vacation_form_panel:
                try:
                    print(f"🗑️ DEBUG: Vacation form panel bağlanır")
                    if self.vacation_form_panel.winfo_exists():
                        self.vacation_form_panel.place_forget()
                        self.vacation_form_panel.destroy()
                    self.vacation_form_panel = None
                    print("✅ DEBUG: Vacation form panel bağlandı")
                except Exception as e:
                    print(f"❌ DEBUG: Vacation form panel bağlanarkən xəta: {e}")
                    
        except Exception as e:
            print(f"❌ DEBUG: Məzuniyyət pəncərələrini bağlarkən xəta: {e}")
            logging.warning(f"Açıq məzuniyyət pəncərələrini bağlarkən xəta: {e}")

    def _has_open_vacation_windows(self):
        """Açıq məzuniyyət sorğusu pəncərələri var mı yoxlayır"""
        try:
            print("🔍 DEBUG: Məzuniyyət pəncərəsi yoxlanılır...")
            
            # Məzuniyyət pəncərəsini yoxla
            if (hasattr(self, 'current_vacation_window') and 
                self.current_vacation_window is not None and 
                hasattr(self.current_vacation_window, 'winfo_exists')):
                try:
                    if self.current_vacation_window.winfo_exists():
                        print("✅ DEBUG: Məzuniyyət pəncərəsi açıqdır")
                        return True
                except:
                    pass
            
            # Vacation form panel-i yoxla
            if (hasattr(self, 'vacation_form_panel') and 
                self.vacation_form_panel is not None and 
                hasattr(self.vacation_form_panel, 'winfo_exists')):
                try:
                    if self.vacation_form_panel.winfo_exists():
                        print("✅ DEBUG: Vacation form panel açıqdır")
                        return True
                except:
                    pass
            
            print("❌ DEBUG: Məzuniyyət pəncərəsi tapılmadı")
            return False
        except Exception as e:
            print(f"❌ DEBUG: Məzuniyyət pəncərəsini yoxlarkən xəta: {e}")
            logging.warning(f"Açıq pəncərələri yoxlarkən xəta: {e}")
            return False

    def toggle_vacation_panel(self, show, employee_name=None, vacation=None):
        logging.info(f"=== toggle_vacation_panel başladı: show={show}, employee_name={employee_name}, vacation={vacation} ===")
        print(f"🔄 DEBUG: toggle_vacation_panel başladı - show={show}, employee={employee_name}")
        
        # Açıq məzuniyyət sorğusu pəncərələrini bağla
        self._close_vacation_windows()
        
        # Təhlükəsizlik yoxlaması: Adi istifadəçi yalnız öz məzuniyyətlərini idarə edə bilər
        if self.current_user['role'].strip() != 'admin' and employee_name:
            current_user_name = self.current_user.get('name', '')
            logging.info(f"Təhlükəsizlik yoxlaması: current_user_name={current_user_name}, employee_name={employee_name}")
            print(f"🔒 DEBUG: Təhlükəsizlik yoxlaması - current_user={current_user_name}, employee={employee_name}")
            if employee_name != current_user_name:
                logging.warning(f"Adi istifadəçi başqa işçinin məzuniyyətini idarə etməyə çalışır")
                print(f"⚠️ DEBUG: Adi istifadəçi başqa işçinin məzuniyyətini idarə etməyə çalışır")
                messagebox.showwarning("Xəbərdarlıq", "Yalnız öz məzuniyyətlərinizi idarə edə bilərsiniz!")
                return
                
        if show:
            try:
                logging.info("Vacation panel açılır...")
                print("📋 DEBUG: Vacation panel açılır...")
                
                is_edit_mode = vacation is not None
                self.current_panel_employee = employee_name
                self.current_panel_vacation = vacation
                logging.info(f"Panel parametrləri: is_edit_mode={is_edit_mode}, employee={employee_name}")
                print(f"⚙️ DEBUG: Panel parametrləri - is_edit_mode={is_edit_mode}, employee={employee_name}")
                
                # Panel yerləşdirmə - daha təhlükəsiz yöntəm
                logging.info("Panel yerləşdirmə yoxlanılır...")
                print("📍 DEBUG: Panel yerləşdirmə yoxlanılır...")
                
                if hasattr(self, 'views') and 'employee_details' in self.views:
                    logging.info("employee_details view tapıldı, panel yerləşdirilir...")
                    print("✅ DEBUG: employee_details view tapıldı, panel yerləşdirilir...")
                    
                    # Panel yerləşdirmədən əvvəl cari statusu yoxla
                    old_panel_active = getattr(self, 'vacation_panel_active', False)
                    print(f"📊 DEBUG: Köhnə panel statusu: {old_panel_active}")
                    
                    # Köhnə paneli təmizlə
                    if hasattr(self, 'vacation_form_panel') and self.vacation_form_panel:
                        try:
                            print("🧹 DEBUG: Köhnə panel təmizlənir...")
                            self.vacation_form_panel.place_forget()
                            self.vacation_form_panel.destroy()
                        except Exception as e:
                            print(f"⚠️ DEBUG: Köhnə panel təmizlənərkən xəta: {e}")
                    
                    # Yeni panel yarat (yalnız lazım olduqda)
                    if not hasattr(self, 'vacation_form_panel') or self.vacation_form_panel is None:
                        print("🏗️ DEBUG: Yeni panel yaradılır...")
                        self._create_vacation_panel()
                    else:
                        print("♻️ DEBUG: Mövcud panel istifadə edilir...")
                    
                    # Məzuniyyət pəncərəsini izlə
                    if hasattr(self, 'vacation_form_panel') and self.vacation_form_panel:
                        self.current_vacation_window = self.vacation_form_panel
                        print("✅ DEBUG: Məzuniyyət pəncərəsi izləməyə alındı")
                    
                    # Panel parametrlərini təyin et
                    logging.info("Vacation form panel set_mode çağırılır...")
                    print("🔧 DEBUG: Vacation form panel set_mode çağırılır...")
                    self.vacation_form_panel.set_mode(is_edit_mode, vacation, employee_name)
                    
                    # İşçi məlumatlarını panel-ə təyin et (çap üçün)
                    if employee_name and hasattr(self, 'data') and employee_name in self.data:
                        employee_data = self.data[employee_name]
                        self.vacation_form_panel.set_employee_data(employee_data)
                        print(f"🔧 DEBUG: İşçi məlumatları panel-ə təyin edildi: {employee_name}")
                    else:
                        print(f"⚠️ DEBUG: İşçi məlumatları tapılmadı: {employee_name}")
                    
                    # Panel və parent widget-lərin detallarını yoxla
                    print(f"🔍 DEBUG: Panel widget: {self.vacation_form_panel}")
                    print(f"🔍 DEBUG: Parent widget: {self.views['employee_details']}")
                    print(f"🔍 DEBUG: Panel winfo_exists: {self.vacation_form_panel.winfo_exists()}")
                    print(f"🔍 DEBUG: Parent winfo_exists: {self.views['employee_details'].winfo_exists()}")
                    
                    # Panel yerləşdirmədən əvvəl parent-in görünürlüyünü yoxla
                    try:
                        parent_visible = self.views['employee_details'].winfo_viewable()
                        print(f"👁️ DEBUG: Parent görünür: {parent_visible}")
                    except Exception as e:
                        print(f"⚠️ DEBUG: Parent görünürlüyü yoxlanıla bilmədi: {e}")
                    
                    # Panel yerləşdir
                    print("📍 DEBUG: Panel place() çağırılır...")
                    try:
                        self.vacation_form_panel.place(in_=self.views['employee_details'], relx=0.65, rely=0, relwidth=0.35, relheight=0.9)
                        print("✅ DEBUG: Panel place() uğurla tamamlandı")
                        self.vacation_panel_active = True
                        
                        # Panel-in düzgün yerləşdirildiyini yoxla və göstər
                        self.after(100, self._check_panel_visibility)
                        self.after(200, self._force_panel_visibility)
                    except Exception as e:
                        print(f"❌ DEBUG: Panel place() xətası: {e}")
                        self.vacation_panel_active = False
                    
                    # Yeni statusu yoxla
                    new_panel_active = getattr(self, 'vacation_panel_active', False)
                    print(f"📊 DEBUG: Yeni panel statusu: {new_panel_active}")
                    
                    logging.info(f"Vacation panel uğurla açıldı: {employee_name}")
                    print(f"✅ DEBUG: Vacation panel uğurla açıldı: {employee_name}")
                    
                    # Panel görünürlüyünü yoxla
                    try:
                        panel_visible = self.vacation_form_panel.winfo_viewable()
                        print(f"👁️ DEBUG: Panel görünür: {panel_visible}")
                    except Exception as e:
                        print(f"⚠️ DEBUG: Panel görünürlüyü yoxlanıla bilmədi: {e}")
                    
                else:
                    logging.error("employee_details view tapılmadı")
                    logging.error(f"Mövcud views: {list(self.views.keys()) if hasattr(self, 'views') else 'views yoxdur'}")
                    print(f"❌ DEBUG: employee_details view tapılmadı")
                    print(f"📋 DEBUG: Mövcud views: {list(self.views.keys()) if hasattr(self, 'views') else 'views yoxdur'}")
                    messagebox.showerror("Xəta", "Məzuniyyət pəncərəsi açıla bilmədi!")
            except Exception as e:
                logging.error(f"Vacation panel açılarkən xəta: {e}")
                print(f"❌ DEBUG: Vacation panel açılarkən xəta: {e}")
                import traceback
                logging.error(f"Traceback: {traceback.format_exc()}")
                print(f"📋 DEBUG: Traceback: {traceback.format_exc()}")
                messagebox.showerror("Xəta", f"Məzuniyyət pəncərəsi açıla bilmədi: {e}")
        else:
            # Panel bağlanır
            try:
                logging.info("Vacation panel bağlanır...")
                print("❌ DEBUG: Vacation panel bağlanır...")
                
                # Panel aktiv statusunu sıfırla
                self.vacation_panel_active = False
                
                # Panel-i gizlət və təmizlə
                if hasattr(self, 'vacation_form_panel') and self.vacation_form_panel:
                    try:
                        print("🧹 DEBUG: Panel gizlədirilir və təmizlənir...")
                        
                        # Panel-i gizlət
                        self.vacation_form_panel.place_forget()
                        
                        # Panel-i destroy et
                        self.vacation_form_panel.destroy()
                        
                        # Panel referansını təmizlə
                        self.vacation_form_panel = None
                        
                        print("✅ DEBUG: Panel uğurla bağlandı və təmizləndi")
                        
                    except Exception as e:
                        print(f"⚠️ DEBUG: Panel bağlanarkən xəta: {e}")
                        # Xəta halında da referansı təmizlə
                        self.vacation_form_panel = None
                
                # Cari pəncərə referansını təmizlə
                if hasattr(self, 'current_vacation_window'):
                    self.current_vacation_window = None
                
                # Panel parametrlərini təmizlə
                self.current_panel_employee = None
                self.current_panel_vacation = None
                
                # UI-nı yenilə ki layout düzəlsin
                self.update()
                self.update_idletasks()
                
                logging.info("Vacation panel uğurla bağlandı")
                print("✅ DEBUG: Vacation panel uğurla bağlandı")
                
            except Exception as e:
                logging.error(f"Vacation panel bağlanarkən xəta: {e}")
                print(f"❌ DEBUG: Vacation panel bağlanarkən xəta: {e}")
                import traceback
                logging.error(f"Traceback: {traceback.format_exc()}")
                print(f"📋 DEBUG: Traceback: {traceback.format_exc()}")
    
    def _check_panel_visibility(self):
        """Panel görünürlüyünü yoxlayır"""
        try:
            if hasattr(self, 'vacation_form_panel') and self.vacation_form_panel:
                panel_visible = self.vacation_form_panel.winfo_viewable()
                print(f"🔍 DEBUG: Panel görünürlük yoxlaması: {panel_visible}")
                
                if not panel_visible:
                    print("⚠️ DEBUG: Panel görünmür, yenidən yerləşdirilir...")
                    # Panel-i yenidən yerləşdir
                    if hasattr(self, 'views') and 'employee_details' in self.views:
                        self.vacation_form_panel.place(in_=self.views['employee_details'], relx=0.65, rely=0, relwidth=0.35, relheight=0.9)
                        print("✅ DEBUG: Panel yenidən yerləşdirildi")
        except Exception as e:
            print(f"⚠️ DEBUG: Panel görünürlük yoxlaması xətası: {e}")
    
    def _force_panel_visibility(self):
        """Panel görünürlüyünü məcburi edir"""
        try:
            if hasattr(self, 'vacation_form_panel') and self.vacation_form_panel:
                # Panel-i məcburi göstər
                self.vacation_form_panel.lift()
                self.vacation_form_panel.update()
                print("🔧 DEBUG: Panel görünürlüyü məcburi edildi")
        except Exception as e:
            print(f"⚠️ DEBUG: Panel görünürlük məcburi etmə xətası: {e}")
        
        logging.info("=== toggle_vacation_panel bitdi ===")
        print("🏁 DEBUG: toggle_vacation_panel bitdi")

    def _animate_panel(self):
        # Artıq animasiya və relx istifadə etmirik, paneli sadəcə pack edirik
        if self.vacation_panel_active:
            self.vacation_form_panel.pack(expand=True, fill='both', padx=20, pady=20)
        else:
            self.vacation_form_panel.pack_forget()

    def _save_vacation_from_panel(self):
        """Sorğu göndərmə funksiyası - EXE-də işləmək üçün optimizasiya edilmiş"""
        try:
            print(f"💾 DEBUG: _save_vacation_from_panel çağırıldı")
            print(f"💾 DEBUG: vacation_form_panel mövcuddur: {hasattr(self, 'vacation_form_panel')}")
            self._safe_flush_stdout()
            
            if not hasattr(self, 'vacation_form_panel') or self.vacation_form_panel is None:
                print(f"❌ DEBUG: vacation_form_panel mövcud deyil!")
                messagebox.showerror("Xəta", "Məzuniyyət paneli tapılmadı.", parent=self)
                return
            
            print(f"💾 DEBUG: Form məlumatları alınır...")
            form_data = self.vacation_form_panel.get_form_data()
            print(f"💾 DEBUG: Form data keys: {list(form_data.keys()) if form_data else 'None'}")
            self._safe_flush_stdout()
            
            start_date_obj = form_data.get('start_date')
            end_date_obj = form_data.get('end_date')
            note = form_data.get('note', '')
            
            if not start_date_obj or not end_date_obj:
                messagebox.showerror("Xəta", "Tarixlər seçilməlidir.", parent=self)
                return
            if end_date_obj < start_date_obj:
                messagebox.showerror("Xəta", "Bitmə tarixi başlanğıcdan əvvəl ola bilməz.", parent=self)
                return
            
            is_edit_mode = self.current_panel_vacation is not None
            creation_date = date.today().isoformat()
            if is_edit_mode:
                creation_date = self.current_panel_vacation.get('yaradilma_tarixi', date.today().isoformat())
            
            new_data = {
                "baslama": start_date_obj.isoformat(), 
                "bitme": end_date_obj.isoformat(), 
                "qeyd": note, 
                "yaradilma_tarixi": creation_date
            }
            
            print(f"💾 DEBUG: new_data hazırlandı: {new_data}")
            print(f"💾 DEBUG: is_edit_mode: {is_edit_mode}")
            print(f"💾 DEBUG: current_panel_employee: {self.current_panel_employee}")
            self._safe_flush_stdout()
            
            if is_edit_mode:
                print(f"💾 DEBUG: _update_vacation çağırılır...")
                self._update_vacation(new_data)
            else:
                print(f"💾 DEBUG: _create_vacation çağırılır...")
                self._create_vacation(new_data)
        except Exception as e:
            logging.error(f"_save_vacation_from_panel xətası: {e}")
            print(f"❌ DEBUG: _save_vacation_from_panel xətası: {e}")
            import traceback
            traceback.print_exc()
            self._safe_flush_stdout()
            try:
                messagebox.showerror("Xəta", f"Sorğu göndərilərkən xəta: {e}", parent=self)
            except Exception:
                pass

    def _create_vacation(self, new_data):
        """Məzuniyyət yaratma funksiyası - EXE-də işləmək üçün optimizasiya edilmiş"""
        try:
            print(f"🔵 DEBUG: _create_vacation çağırıldı")
            print(f"🔵 DEBUG: new_data: {new_data}")
            print(f"🔵 DEBUG: current_panel_employee: {self.current_panel_employee}")
            print(f"🔵 DEBUG: current_user: {self.current_user.get('name', 'N/A')}")
            self._safe_flush_stdout()
            
            # Təhlükəsizlik yoxlaması: Adi istifadəçi yalnız öz məzuniyyətini yarada bilər
            if self.current_user['role'].strip() != 'admin':
                current_user_name = self.current_user.get('name', '')
                if self.current_panel_employee != current_user_name:
                    messagebox.showerror("Xəta", "Yalnız öz məzuniyyətinizi yarada bilərsiniz!")
                    return
            
            # Employee ID-ni yoxla
            if not hasattr(self, 'data') or not self.data:
                print(f"❌ DEBUG: self.data mövcud deyil!")
                messagebox.showerror("Xəta", "Məlumatlar yüklənməyib.", parent=self)
                return
            
            if self.current_panel_employee not in self.data:
                print(f"❌ DEBUG: current_panel_employee '{self.current_panel_employee}' data-də tapılmadı!")
                messagebox.showerror("Xəta", f"İşçi '{self.current_panel_employee}' tapılmadı.", parent=self)
                return
            
            emp_id = self.data[self.current_panel_employee].get('db_id')
            if not emp_id:
                print(f"❌ DEBUG: emp_id tapılmadı!")
                messagebox.showerror("Xəta", "İşçi ID-si tapılmadı.", parent=self)
                return
            
            print(f"🔵 DEBUG: emp_id: {emp_id}")
            print(f"🔵 DEBUG: Thread yaradılır...")
            self._safe_flush_stdout()
            
            # Database işlemini background thread'de çalıştır
            thread = threading.Thread(
                target=self._create_vacation_threaded,
                args=(emp_id, new_data),
                daemon=True
            )
            print(f"✅ DEBUG: Thread yaradıldı, start() çağırılır...")
            self._safe_flush_stdout()
            thread.start()
            print(f"✅ DEBUG: Thread.start() tamamlandı")
            self._safe_flush_stdout()
            
            # Bu nöqtədən sonra kod davam etməz, thread callback ilə davam edir
            return
        except Exception as e:
            logging.error(f"_create_vacation xətası: {e}")
            print(f"❌ DEBUG: _create_vacation xətası: {e}")
            import traceback
            traceback.print_exc()
            self._safe_flush_stdout()
            try:
                messagebox.showerror("Xəta", f"Məzuniyyət yaradılarkən xəta: {e}", parent=self)
            except Exception:
                pass
        
        # Aşağıdaki kod artıq istifadə edilmir (şərhə alındı)
        try:
            pass  # database.add_vacation - thread'de çalışır
            # database.add_vacation(emp_id, self.current_panel_employee, new_data, self.current_user['role'])
            
            # Real-time notification göndər
            try:
                self.send_realtime_signal('vacation_created', {
                    'employee_name': self.current_panel_employee,
                    'employee_id': emp_id,
                    'vacation_data': new_data,
                    'created_by': self.current_user.get('name')
                })
            except Exception as signal_error:
                logging.warning(f"Real-time signal göndərilmədi: {signal_error}")
            
            # Animasiyanın biraz daha uzun görünməsi üçün qısa gecikmə (after() istifadə edirik ki animasiya hərəkətli qalsın)
            print("⏳ DEBUG main_frame: Animasiya göstərilir, qısa gecikmə...")
            self.update()
            # after() istifadə edirik ki animasiya davam etsin, event loop bloke olmasın
            self.after(500, self._show_success_message, new_data)
            
        except Exception as e:
            logging.error(f"Məzuniyyət yaradılarkən xəta: {e}")
            
            # Animasiyanın biraz daha uzun görünməsi üçün qısa gecikmə (after() istifadə edirik ki animasiya hərəkətli qalsın)
            print("⏳ DEBUG main_frame: Xəta animasiyası göstərilir, qısa gecikmə...")
            self.update()
            # after() istifadə edirik ki animasiya davam etsin, event loop bloke olmasın
            self.after(500, self._show_error_message, str(e))

    def _create_vacation_threaded(self, emp_id, new_data):
        """Database işlemini background thread'de çalıştırır"""
        import threading
        import sys
        import traceback
        from utils.debug_manager import debug_log
        
        debug_log('thread', '========== THREAD STARTED ==========', '🔵')
        print(f"🔵 DEBUG _create_vacation_threaded: ========== THREAD STARTED ==========")
        print(f"🔵 DEBUG: emp_id={emp_id}, employee_name={self.current_panel_employee}")
        print(f"🔵 DEBUG: new_data={new_data}")
        print(f"🔵 DEBUG: role={self.current_user.get('role', 'N/A')}")
        self._safe_flush_stdout()
        debug_log('thread', f'Thread name: {threading.current_thread().name}', '🔵')
        
        try:
            import time as time_module
            
            # Database modulunu yoxla - EXE-də işləmək üçün bir neçə yolu sınayırıq
            print(f"🔵 DEBUG: database modulu yoxlanılır...")
            db_module = None
            import_err = None
            
            # Birinci cəhd: database (normal Python mühitində)
            try:
                import database
                db_module = database
                print(f"✅ DEBUG: database modulu import edildi (birinci cəhd): {database}")
            except ImportError as e1:
                import_err = e1
                print(f"⚠️ DEBUG: database modulu import edilə bilmədi (birinci cəhd): {e1}")
                
                # İkinci cəhd: src.database (EXE mühitində)
                try:
                    from src import database as db_module
                    print(f"✅ DEBUG: database modulu import edildi (ikinci cəhd): {db_module}")
                except ImportError as e2:
                    print(f"⚠️ DEBUG: src.database modulu import edilə bilmədi (ikinci cəhd): {e2}")
                    
                    # Üçüncü cəhd: src.database.database
                    try:
                        from src.database import database as db_module
                        print(f"✅ DEBUG: database modulu import edildi (üçüncü cəhd): {db_module}")
                    except ImportError as e3:
                        print(f"❌ DEBUG: src.database.database modulu import edilə bilmədi (üçüncü cəhd): {e3}")
                        raise Exception(f"Database modulu tapılmadı. Cəhdlər: {e1}, {e2}, {e3}")
            
            if db_module is None:
                raise Exception(f"Database modulu None qayıtdı: {import_err}")
            
            database = db_module
            
            # add_vacation funksiyasını yoxla
            if not hasattr(database, 'add_vacation'):
                print(f"❌ DEBUG: database.add_vacation funksiyası tapılmadı!")
                raise Exception("database.add_vacation funksiyası mövcud deyil")
            
            print(f"🔵 DEBUG: add_vacation() çağırılır...")
            print(f"🔵 DEBUG: Parametrlər - emp_id={emp_id}, name={self.current_panel_employee}, data={new_data}, role={self.current_user['role']}")
            debug_log('thread', 'add_vacation() çağırılır...', '🔵')
            self._safe_flush_stdout()
            
            start_time = time_module.time()
            try:
                database.add_vacation(emp_id, self.current_panel_employee, new_data, self.current_user['role'])
                elapsed = time_module.time() - start_time
                print(f"✅ DEBUG: add_vacation() uğurla tamamlandı, vaxt: {elapsed:.2f}s")
                debug_log('thread', f'add_vacation() tamamlandı - {elapsed:.2f}s', '✅')
                self._safe_flush_stdout()
            except Exception as db_error:
                print(f"❌ DEBUG: database.add_vacation() xətası: {db_error}")
                print(f"❌ DEBUG: Xəta tipi: {type(db_error)}")
                traceback.print_exc()
                self._safe_flush_stdout()
                raise  # Xətanı yuxarı fırlat
            
            # Success callback-i UI thread-də çağır - EXE-də işləmək üçün bir neçə yolu sınayırıq
            print(f"🔵 DEBUG: Success callback çağırılır...")
            debug_log('thread', 'Success callback çağırılır...', '🔵')
            self._safe_flush_stdout()
            
            # Callback funksiyasını lambda ilə yarad ki closure problemi olmasın
            def success_callback():
                try:
                    print(f"✅ DEBUG: Success callback icra edilir...")
                    self._show_success_message(new_data, emp_id)
                except Exception as cb_error:
                    print(f"❌ DEBUG: Success callback icra xətası: {cb_error}")
                    traceback.print_exc()
            
            # Birinci cəhd: root window-dan after(0)
            callback_called = False
            try:
                root = self.winfo_toplevel()
                print(f"🔵 DEBUG: root window: {root}")
                if root and root.winfo_exists():
                    print(f"🔵 DEBUG: root.winfo_exists() = True, after(0) çağırılır...")
                    result = root.after(0, success_callback)
                    print(f"✅ DEBUG: Success callback root.after(0) ilə çağırıldı, after_id={result}")
                    callback_called = True
                    self._safe_flush_stdout()
            except Exception as e1:
                print(f"⚠️ DEBUG: root.after(0) xətası: {e1}")
                traceback.print_exc()
                self._safe_flush_stdout()
            
            # İkinci cəhd: self.after(0) - yalnız birinci uğursuz olsa
            if not callback_called:
                try:
                    print(f"🔵 DEBUG: self.after(0) sınanır...")
                    result = self.after(0, success_callback)
                    print(f"✅ DEBUG: Success callback self.after(0) ilə çağırıldı, after_id={result}")
                    callback_called = True
                    self._safe_flush_stdout()
                except Exception as e2:
                    print(f"⚠️ DEBUG: self.after(0) xətası: {e2}")
                    traceback.print_exc()
                    self._safe_flush_stdout()
            
            # Üçüncü cəhd: tk._default_root - yalnız əvvəlkilər uğursuz olsa
            if not callback_called:
                try:
                    if tk._default_root and tk._default_root.winfo_exists():
                        print(f"🔵 DEBUG: tk._default_root.after(0) sınanır...")
                        result = tk._default_root.after(0, success_callback)
                        print(f"✅ DEBUG: Success callback tk._default_root.after(0) ilə çağırıldı, after_id={result}")
                        callback_called = True
                        self._safe_flush_stdout()
                except Exception as e3:
                    print(f"⚠️ DEBUG: tk._default_root.after(0) xətası: {e3}")
                    traceback.print_exc()
                    self._safe_flush_stdout()
            
            # Son çarə: birbaşa çağır (riskli, amma bəzən işləyir)
            if not callback_called:
                print(f"⚠️ DEBUG: Bütün after() cəhdləri uğursuz, birbaşa çağırılır...")
                try:
                    success_callback()
                except Exception as direct_error:
                    print(f"❌ DEBUG: Birbaşa çağırış xətası: {direct_error}")
                    traceback.print_exc()
                    self._safe_flush_stdout()
            
        except Exception as e:
            logging.error(f"Məzuniyyət yaradılarkən xəta: {e}")
            print(f"❌ DEBUG: Thread xətası: {e}")
            print(f"❌ DEBUG: Xəta tipi: {type(e)}")
            traceback.print_exc()
            self._safe_flush_stdout()
            
            # Error callback funksiyası
            def error_callback():
                try:
                    print(f"❌ DEBUG: Error callback icra edilir...")
                    self._show_error_message(str(e))
                except Exception as cb_error:
                    print(f"❌ DEBUG: Error callback icra xətası: {cb_error}")
                    traceback.print_exc()
            
            # Error callback-i UI thread-də çağır
            error_callback_called = False
            try:
                root = self.winfo_toplevel()
                if root and root.winfo_exists():
                    root.after(0, error_callback)
                    error_callback_called = True
                    print(f"✅ DEBUG: Error callback root.after(0) ilə çağırıldı")
            except Exception as callback_error:
                print(f"⚠️ DEBUG: Error callback root.after(0) xətası: {callback_error}")
            
            if not error_callback_called:
                try:
                    self.after(0, error_callback)
                    print(f"✅ DEBUG: Error callback self.after(0) ilə çağırıldı")
                except Exception as callback_error2:
                    print(f"❌ DEBUG: Error callback self.after(0) xətası: {callback_error2}")
                    # Son çarə - birbaşa çağır
                    try:
                        error_callback()
                    except Exception as direct_error:
                        print(f"❌ DEBUG: Birbaşa error çağırış xətası: {direct_error}")

    def _show_success_message(self, new_data, emp_id):
        """Success mesajını göstərir"""
        import time
        import sys
        
        timestamp = time.time()
        print(f"🔴 DEBUG main_frame: Success mesajı göstərilir... Timestamp: {timestamp}")
        self._safe_flush_stdout()
        
        # UI-ni yenilə
        try:
            self.update_idletasks()
            self.update()
        except Exception:
            pass
        
        # Mesajı dərhal göstər
        self._show_success_message_after_delay(new_data, emp_id)

    def _show_success_message_after_delay(self, new_data, emp_id):
        import tkinter.messagebox as messagebox
        
        try:
            self.update_idletasks()
            self.update()
        except Exception:
            pass
        
        messagebox.showinfo("Uğurlu", f"Məzuniyyət sorğusu uğurla göndərildi!\nİşçi: {self.current_panel_employee}\nBaşlanğıc: {new_data['baslama']}\nBitmə: {new_data['bitme']}")
        
        # Pəncərəni bağla
        self.toggle_vacation_panel(show=False)
        
        # Məlumatları yenilə (async)
        self.after(100, lambda: self.load_and_refresh_data(selection_to_keep=self.current_panel_employee))
        
        # Real-time signal-i background thread-də göndərək (bloksuz-mailto:)
        def send_signal_in_thread():
            try:
                print(f"🔵 DEBUG: Real-time signal göndərilir (background thread)...")
                self.send_realtime_signal('vacation_created', {
                    'employee_name': self.current_panel_employee,
                    'employee_id': emp_id,
                    'vacation_data': new_data,
                    'created_by': self.current_user.get('name')
                })
                print(f"✅ DEBUG: Real-time signal göndərildi")
            except Exception as signal_error:
                logging.warning(f"Real-time signal göndərilmədi: {signal_error}")
                print(f"⚠️ DEBUG: Real-time signal xətası: {signal_error}")
        
        # Background thread-də göndər
        import threading
        threading.Thread(target=send_signal_in_thread, daemon=True).start()

    def _show_error_message(self, error_msg):
        """Error mesajını göstərir"""
        import tkinter.messagebox as messagebox
        
        print("🔴 DEBUG main_frame: Error mesajı göstərilir...")
        
        # Xəta mesajı göstər
        messagebox.showerror("Xəta", f"Məzuniyyət sorğusu göndərilmədi: {error_msg}")
        
        # Pəncərəni bağla və yenilə
        self.toggle_vacation_panel(show=False)
        self.load_and_refresh_data(selection_to_keep=self.current_panel_employee)

    def _update_vacation(self, new_data):
        # Təhlükəsizlik yoxlaması: Adi istifadəçi yalnız öz məzuniyyətini yeniləyə bilər
        if self.current_user['role'].strip() != 'admin':
            current_user_name = self.current_user.get('name', '')
            if self.current_panel_employee != current_user_name:
                messagebox.showerror("Xəta", "Yalnız öz məzuniyyətinizi yeniləyə bilərsiniz!")
                return
                
        try:
            database.update_vacation(self.current_panel_vacation['db_id'], new_data, self.current_user['name'])
            
            # Real-time notification göndər
            try:
                self.send_realtime_signal('vacation_updated', {
                    'employee_name': self.current_panel_employee,
                    'vacation_id': self.current_panel_vacation['db_id'],
                    'vacation_data': new_data,
                    'updated_by': self.current_user.get('name')
                })
            except Exception as signal_error:
                logging.warning(f"Real-time signal göndərilmədi: {signal_error}")
            
            # Uğurlu mesaj göstər
            messagebox.showinfo("Uğurlu", f"Məzuniyyət sorğusu uğurla yeniləndi!\nİşçi: {self.current_panel_employee}\nBaşlanğıc: {new_data['baslama']}\nBitmə: {new_data['bitme']}")
            
        except Exception as e:
            logging.error(f"Məzuniyyət yenilənərkən xəta: {e}")
            messagebox.showerror("Xəta", f"Məzuniyyət sorğusu yenilənmədi: {e}")
        finally:
            # Həmişə pəncərəni bağla
            self.toggle_vacation_panel(show=False)
            self.load_and_refresh_data(selection_to_keep=self.current_panel_employee)

    # Tema sistemi silindi

    def open_debug_window(self):
        """Debug pəncərəsini açır - async şəkildə (UI-ni bloklamamaq üçün)"""
        def _async_open():
            try:
                show_debug_window(self.winfo_toplevel())
            except Exception as e:
                logging.error(f"Debug pəncərəsi açılarkən xəta: {e}")
                messagebox.showerror("Xəta", f"Debug pəncərəsi açıla bilmədi: {e}")
        
        # Async şəkildə aç ki, UI bloklanmasın
        try:
            root = self.winfo_toplevel()
            if root and root.winfo_exists():
                root.after(0, _async_open)
            else:
                self.after(0, _async_open)
        except Exception:
            # Son çarə - birbaşa aç
            _async_open()
    
    def open_profile_window(self):
        """Profil səhifəsini açır"""
        try:
            # Mövcud view-ləri gizlət
            for widget in self.winfo_children():
                if hasattr(widget, 'pack_info'):
                    widget.pack_forget()
            
            # Profil səhifəsini yarat və göstər
            from .profile_window import ProfilePage
            self.profile_page = ProfilePage(self, self.current_user, on_back=self.show_main_view)
            self.profile_page.pack(fill="both", expand=True)
            
        except Exception as e:
            logging.error(f"Profil səhifəsi açılarkən xəta: {e}")
            messagebox.showerror("Xəta", f"Profil səhifəsi açıla bilmədi: {e}")
    
    def hide_all_views(self):
        """Bütün səhifələri gizlədir"""
        # Mövcud view-ləri gizlət
        for view_name, view_frame in self.views.items():
            view_frame.place_forget()
        
        # Profil səhifəsini gizlət
        if hasattr(self, 'profile_page'):
            self.profile_page.place_forget()
        
        # Alətlər səhifəsini gizlət
        if hasattr(self, 'tools_page'):
            self.tools_page.place_forget()
        
        # İstifadəçi idarəetməsi səhifəsini gizlət
        if hasattr(self, 'user_management_page'):
            self.user_management_page.place_forget()
        
        # Xəta jurnalı səhifəsini gizlət
        if hasattr(self, 'error_viewer_page'):
            self.error_viewer_page.place_forget()

    def show_main_view(self, needs_refresh=False):
        """Əsas görünüşə qayıtmaq"""
        try:
            print("🔄 DEBUG: show_main_view başladı")
            logging.info("=== show_main_view başladı ===")
            logging.info(f"needs_refresh parametri: {needs_refresh}")
            print(f"👤 DEBUG: Current user: {self.current_user}")
            logging.info(f"Current user: {self.current_user}")
            
            # Profil səhifəsini gizlət
            if hasattr(self, 'profile_page'):
                print("🧹 DEBUG: Profil səhifəsi gizlənir...")
                logging.info("Profil səhifəsi gizlənir...")
                try:
                    self.profile_page.pack_forget()
                    delattr(self, 'profile_page')
                    print("✅ DEBUG: Profil səhifəsi uğurla gizləndi")
                    logging.info("Profil səhifəsi uğurla gizləndi")
                except Exception as e:
                    print(f"❌ DEBUG: Profil səhifəsi gizlənərkən xəta: {e}")
                    logging.error(f"Profil səhifəsi gizlənərkən xəta: {e}")
            
            # Alətlər səhifəsini gizlət
            if hasattr(self, 'tools_page'):
                print("🧹 DEBUG: Alətlər səhifəsi gizlənir...")
                logging.info("Alətlər səhifəsi gizlənir...")
                try:
                    self.tools_page.pack_forget()
                    delattr(self, 'tools_page')
                    print("✅ DEBUG: Alətlər səhifəsi uğurla gizləndi")
                    logging.info("Alətlər səhifəsi uğurla gizləndi")
                except Exception as e:
                    print(f"❌ DEBUG: Alətlər səhifəsi gizlənərkən xəta: {e}")
                    logging.error(f"Alətlər səhifəsi gizlənərkən xəta: {e}")
            
            # İstifadəçi idarəetməsi səhifəsini gizlət
            if hasattr(self, 'user_management_page'):
                print("🧹 DEBUG: İstifadəçi idarəetməsi səhifəsi gizlənir...")
                logging.info("İstifadəçi idarəetməsi səhifəsi gizlənir...")
                try:
                    self.user_management_page.pack_forget()
                    delattr(self, 'user_management_page')
                    print("✅ DEBUG: İstifadəçi idarəetməsi səhifəsi uğurla gizləndi")
                    logging.info("İstifadəçi idarəetməsi səhifəsi uğurla gizləndi")
                except Exception as e:
                    print(f"❌ DEBUG: İstifadəçi idarəetməsi səhifəsi gizlənərkən xəta: {e}")
                    logging.error(f"İstifadəçi idarəetməsi səhifəsi gizlənərkən xəta: {e}")
            
            # Xəta jurnalı səhifəsini gizlət
            if hasattr(self, 'error_viewer_page'):
                print("🧹 DEBUG: Xəta jurnalı səhifəsi gizlənir...")
                logging.info("Xəta jurnalı səhifəsi gizlənir...")
                try:
                    self.error_viewer_page.pack_forget()
                    delattr(self, 'error_viewer_page')
                    print("✅ DEBUG: Alətlər səhifəsi uğurla gizləndi")
                    logging.info("Alətlər səhifəsi uğurla gizləndi")
                except Exception as e:
                    print(f"❌ DEBUG: Alətlər səhifəsi gizlənərkən xəta: {e}")
                    logging.error(f"Alətlər səhifəsi gizlənərkən xəta: {e}")
            
            # İşçi düzəliş səhifəsini gizlət
            if hasattr(self, 'employee_form_page'):
                print("🧹 DEBUG: İşçi düzəliş səhifəsi gizlənir...")
                logging.info("İşçi düzəliş səhifəsi gizlənir...")
                try:
                    self.employee_form_page.pack_forget()
                    delattr(self, 'employee_form_page')
                    print("✅ DEBUG: İşçi düzəliş səhifəsi uğurla gizləndi")
                    logging.info("İşçi düzəliş səhifəsi uğurla gizləndi")
                except Exception as e:
                    print(f"❌ DEBUG: İşçi düzəliş səhifəsi gizlənərkən xəta: {e}")
                    logging.error(f"İşçi düzəliş səhifəsi gizlənərkən xəta: {e}")
            
            # İşçi detal səhifəsini gizlət
            if hasattr(self, 'employee_detail_frame'):
                print("🧹 DEBUG: İşçi detal səhifəsi gizlənir...")
                logging.info("İşçi detal səhifəsi gizlənir...")
                try:
                    self.employee_detail_frame.pack_forget()
                    delattr(self, 'employee_detail_frame')
                    print("✅ DEBUG: İşçi detal səhifəsi uğurla gizləndi")
                    logging.info("İşçi detal səhifəsi uğurla gizləndi")
                except Exception as e:
                    print(f"❌ DEBUG: İşçi detal səhifəsi gizlənərkən xəta: {e}")
                    logging.error(f"İşçi detal səhifəsi gizlənərkən xəta: {e}")
            
            # Mövcud widget-ləri təmizlə
            print("🧹 DEBUG: Mövcud widget-lər təmizlənir...")
            logging.info("Mövcud widget-lər təmizlənir...")
            try:
                for widget in self.winfo_children():
                    if hasattr(widget, 'pack_info'):
                        print(f"🔍 DEBUG: Widget gizlənir: {type(widget).__name__}")
                        logging.debug(f"Widget gizlənir: {type(widget).__name__}")
                        widget.pack_forget()
                print("✅ DEBUG: Widget-lər uğurla təmizləndi")
                logging.info("Widget-lər uğurla təmizləndi")
            except Exception as e:
                print(f"❌ DEBUG: Widget-lər təmizlənərkən xəta: {e}")
                logging.error(f"Widget-lər təmizlənərkən xəta: {e}")
            
            # Əsas layout-u yenidən yarat
            print("🏗️ DEBUG: Əsas layout yenidən yaradılır...")
            logging.info("Əsas layout yenidən yaradılır...")
            try:
                self.create_main_layout()
                # Views-ləri yenidən yarat (çünki create_main_layout-də çağırılmır)
                # Həmişə views-ləri yenidən yarat, çünki widget-lər təmizlənib
                self.create_views()
                print("✅ DEBUG: Əsas layout uğurla yaradıldı")
                logging.info("Əsas layout uğurla yaradıldı")
            except Exception as e:
                print(f"❌ DEBUG: Əsas layout yaradılarkən xəta: {e}")
                logging.error(f"Əsas layout yaradılarkən xəta: {e}")
                raise
            
            # Sadəcə dashboard görünüşünü göstər
            print("📊 DEBUG: Dashboard görünüşü göstərilir...")
            logging.info("Dashboard görünüşü göstərilir...")
            try:
                self.show_view('dashboard')
                print("✅ DEBUG: Dashboard görünüşü uğurla göstərildi")
                logging.info("Dashboard görünüşü uğurla göstərildi")
            except Exception as e:
                print(f"❌ DEBUG: Dashboard görünüşü göstərilərkən xəta: {e}")
                logging.error(f"Dashboard görünüşü göstərilərkən xəta: {e}")
                raise
            
            # Cari view-u yenilə
            self.current_view = 'dashboard'
            print(f"📋 DEBUG: Current view yeniləndi: {self.current_view}")
            
            # Frame-in arxa fonunu təyin et - Tkinter xətasını həll edirik
            print("🎨 DEBUG: Frame arxa fonu təyin edilir...")
            logging.info("Frame arxa fonu təyin edilir...")
            try:
                # ttk.Frame üçün background parametri dəstəklənmir, yalnız style istifadə edirik
                print("🎨 DEBUG: Frame arxa fonu style ilə təyin edilir")
                logging.info("Frame arxa fonu style ilə təyin edilir")
                # Background parametrini silirik, çünki ttk.Frame üçün dəstəklənmir
            except Exception as e:
                print(f"❌ DEBUG: Frame arxa fonu təyin edilərkən xəta: {e}")
                logging.error(f"Frame arxa fonu təyin edilərkən xəta: {e}")
            
            # İşçi seçimini təmizlə
            if hasattr(self, 'employee_listbox'):
                try:
                    self.employee_listbox.selection_clear(0, tk.END)
                    print("🧹 DEBUG: İşçi seçimi təmizləndi")
                    logging.info("İşçi seçimi təmizləndi")
                except Exception as e:
                    print(f"❌ DEBUG: İşçi seçimi təmizlənərkən xəta: {e}")
                    logging.error(f"İşçi seçimi təmizlənərkən xəta: {e}")
            
            # Admin düymələrini deaktiv et - yalnız admin üçün
            # NOTE: Label widget-lər state dəstəkləmir, ona görə də görünürlük həmişə aktivdir
            # İstifadəçi işçi seçməzsə xəbərdarlıq göstəriləcək
            if self.current_user['role'].strip() == 'admin' and hasattr(self, 'edit_employee_button'):
                # Label-lərin cursor-unu dəyişdirək (aktiv görünməsi üçün)
                # State-i dəstəkləmədikləri üçün heç bir şey etmirik
                print("ℹ️ Label icon düymələri həmişə görünürdür (state dəstəkləmir)")
                logging.info("Label icon düymələri həmişə görünürdür")
            
            # Profil düyməsinin mətnini yenilə
            try:
                self.update_profile_button()
                print("👤 DEBUG: Profil düyməsi yeniləndi")
                logging.info("Profil düyməsi yeniləndi")
            except Exception as e:
                print(f"❌ DEBUG: Profil düyməsi yenilənərkən xəta: {e}")
                logging.error(f"Profil düyməsi yenilənərkən xəta: {e}")
            
            # İşçilər siyahısını yenidən doldur
            try:
                self.refresh_employee_list()
                print("📋 DEBUG: İşçilər siyahısı yeniləndi")
                logging.info("İşçilər siyahısı yeniləndi")
            except Exception as e:
                print(f"❌ DEBUG: İşçilər siyahısı yenilənərkən xəta: {e}")
                logging.error(f"İşçilər siyahısı yenilənərkən xəta: {e}")
            
            # Yalnız dəyişiklik olduqda məlumatları yenilə
            if needs_refresh:
                print("🔄 DEBUG: Dəyişikliklər olduğu üçün məlumatlar yenilənir...")
                logging.info("Dəyişikliklər olduğu üçün məlumatlar yenilənir...")
                try:
                    # Dashboard görünüşü üçün lazy loading - yalnız lazım olan məlumatları yüklə
                    self.load_and_refresh_data(load_full_data=False)
                    print("✅ DEBUG: Məlumatlar uğurla yeniləndi")
                    logging.info("Məlumatlar uğurla yeniləndi")
                except Exception as e:
                    print(f"❌ DEBUG: Məlumatlar yenilənərkən xəta: {e}")
                    logging.error(f"Məlumatlar yenilənərkən xəta: {e}")
            
            # UI-ni yenilə (update_idletasks)
            self.update_idletasks()
            
            print("✅ DEBUG: show_main_view tamamlandı")
            logging.info("=== show_main_view tamamlandı ===")
            
        except Exception as e:
            print(f"❌ DEBUG: show_main_view xətası: {e}")
            logging.error(f"Əsas görünüşə qayıtmaqda xəta: {e}")
            logging.error(f"Xəta detalları: {type(e).__name__}")
            import traceback
            print(f"📋 DEBUG: Traceback: {traceback.format_exc()}")
            logging.error(f"Traceback: {traceback.format_exc()}")
            messagebox.showerror("Xəta", f"Əsas görünüşə qayıtmaqda xəta: {e}")

    def _init_real_time_notifications(self):
        """Real-time notification sistemini başladır"""
        try:
            # Tenant ID-ni al
            tenant_id = self.get_tenant_id() if hasattr(self, 'get_tenant_id') else None
            if not tenant_id:
                logging.warning("Tenant ID tapılmadı - real-time notification sistemi başladılmadı")
                self._start_fallback_refresh()
                return
            
            # Real-time notifier-i başlad
            from core.real_time_notifier import init_notifier
            notifier = init_notifier(tenant_id, self._refresh_on_change)
            
            if notifier:
                logging.info("Real-time notification sistemi uğurla başladıldı")
                self.update_realtime_status()
                
                # Notifier statusunu yoxla
                status = notifier.get_status()
                logging.info(f"Notifier status: {status}")
                
                # Əgər notifier işləmirsə, fallback refresh sistemi işə sal
                if not status.get('is_running', False):
                    logging.warning("Notifier işləmir - fallback refresh sistemi işə salınır")
                    self._start_fallback_refresh()
            else:
                logging.warning("Real-time notification sistemi başladıla bilmədi")
                self._start_fallback_refresh()
                
        except Exception as e:
            logging.error(f"Real-time notification sistemi başladılarkən xəta: {e}")
            # Xəta olduqda da lokal refresh sistemi işləyir
            self._start_fallback_refresh()
            self.after(10000, self._init_real_time_notifications)  # 10 saniyə sonra yenidən cəhd et
    
    def _start_fallback_refresh(self):
        """Fallback refresh sistemi - real-time işləmədikdə"""
        try:
            logging.info("Fallback refresh sistemi başladıldı")
            
            # İşçilər bölməsini dərhal yenilə
            self.after(1000, self._force_refresh_employee_list)
            
            # Hər 30 saniyədə bir refresh et
            self.fallback_timer = self.after(30000, self._fallback_refresh_cycle)
            
        except Exception as e:
            logging.error(f"Fallback refresh sistemi başladılarkən xəta: {e}")
    
    def _fallback_refresh_cycle(self):
        """Fallback refresh döngüsü"""
        try:
            if not self.vacation_panel_active:
                logging.info("Fallback refresh - məlumatlar yenilənir...")
                
                # Məlumatları yenilə
                self.data = database.load_data_for_user(self.current_user, force_refresh=False)
                
                # İşçi siyahısını yenilə
                self.refresh_employee_list()
                
                # Bildirişləri yenilə
                self._update_notification_button()
                
                # Status mesajı göstər
                self.update_status_label.config(text="🔄 Fallback refresh tamamlandı")
                
            # Növbəti refresh-i planla
            self.fallback_timer = self.after(30000, self._fallback_refresh_cycle)
            
        except Exception as e:
            logging.error(f"Fallback refresh döngüsündə xəta: {e}")
            # Xəta olduqda da növbəti refresh-i planla
            self.fallback_timer = self.after(60000, self._fallback_refresh_cycle)
    
    def _force_refresh_employee_list(self):
        """İşçilər siyahısını məcburi yeniləyir"""
        try:
            logging.info("İşçilər siyahısı məcburi yenilənir...")
            
            # Məlumatları force refresh ilə yüklə
            self.data = database.load_data_for_user(self.current_user, force_refresh=True)
            logging.info(f"Məlumatlar yükləndi: {len(self.data) if self.data else 0} işçi")
            
            # İşçi siyahısını yenilə
            if hasattr(self, 'employee_listbox'):
                self.refresh_employee_list()
                logging.info("İşçilər siyahısı yeniləndi")
                
                # Əgər heç bir işçi yoxdursa, xəta mesajı göstər
                if not self.data or len(self.data) == 0:
                    logging.warning("Heç bir işçi məlumatı tapılmadı!")
                    # İşçi siyahısına xəta mesajı əlavə et
                    self.employee_listbox.delete(0, tb.END)
                    self.employee_listbox.insert(tb.END, "❌ Məlumatlar yüklənmədi")
                    self.employee_listbox.insert(tb.END, "🔄 Yenidən cəhd edilir...")
                else:
                    logging.info(f"✅ {len(self.data)} işçi uğurla yükləndi")
            else:
                logging.error("employee_listbox tapılmadı!")
                
        except Exception as e:
            logging.error(f"İşçilər siyahısı yenilənərkən xəta: {e}")
            # Xəta baş verdikdə 3 saniyə sonra yenidən cəhd et
            self.after(3000, self._force_refresh_employee_list)

    def _on_database_change(self, change_type, details=None):
        """Veritabanında dəyişiklik olduqda çağırılır"""
        logging.info(f"Veritabanında dəyişiklik: {change_type} - {details}")
        
        # UI thread-də məlumatları yenilə
        self.after(0, self._refresh_on_change, change_type, details)

    def _refresh_on_change(self, change_type, details=None):
        """Dəyişiklik olduqda refresh edir"""
        start_time = time.time()
        
        try:
            # DEBUG: Signal alındı
            log_signal_received(change_type, details, "main_frame")
            logging.info(f"🔄 Real-time dəyişiklik alındı: {change_type}")
            
            # Dəyişiklik növünə görə fərqli refresh strategiyaları
            if change_type in ['vacation_created', 'vacation_updated', 'vacation_deleted', 'vacation_status_changed']:
                # Məzuniyyət dəyişiklikləri - dərhal refresh
                self.after(0, self._immediate_vacation_refresh, change_type, details)
                
            elif change_type in ['employee_created', 'employee_updated', 'employee_deleted', 'employee_hidden']:
                # İşçi dəyişiklikləri - dərhal refresh
                self.after(0, self._immediate_employee_refresh, change_type, details)
                
            elif change_type in ['notifications_deleted', 'error_resolved', 'error_deleted']:
                # Bildiriş dəyişiklikləri - dərhal refresh
                self.after(0, self._immediate_notification_refresh, change_type, details)
                
            elif change_type in ['maintenance_mode_enabled', 'maintenance_mode_disabled', 'users_force_logout', 'users_timed_logout']:
                # Sistem dəyişiklikləri - dərhal refresh
                self.after(0, self._immediate_system_refresh, change_type, details)
                
            else:
                # Ümumi dəyişikliklər - normal refresh
                self.after(100, self._immediate_local_refresh, change_type, details)
            
            # DEBUG: Refresh planlaşdırıldı
            log_performance("refresh_plan", time.time() - start_time, {"change_type": change_type}, "main_frame")
                
        except Exception as e:
            logging.error(f"Real-time refresh xətası: {e}")
            log_performance("refresh_plan", time.time() - start_time, {"error": str(e)}, "main_frame")
            # Xəta olduqda da refresh et
            self.after(200, self._immediate_local_refresh, change_type, details)
    
    def _immediate_vacation_refresh(self, change_type, details=None):
        """Məzuniyyət dəyişiklikləri üçün dərhal refresh"""
        try:
            logging.info(f"🔄 Məzuniyyət refresh: {change_type}")
            
            # Cache-i etibarsız et
            from utils import cache
            cache.invalidate_cache()
            
            # Məlumatları force refresh ilə yenilə
            self.data = database.load_data_for_user(self.current_user, force_refresh=True)
            
            # İşçi siyahısını yenilə
            self.refresh_employee_list()
            
            # Cari işçi seçilmişsə, onun məlumatlarını da yenilə
            if hasattr(self, 'employee_listbox') and self.employee_listbox.curselection():
                try:
                    self.on_employee_select(None)
                except Exception as e:
                    logging.error(f"İşçi seçimi yenilənərkən xəta: {e}")
            
            # Məzuniyyət paneli açıqdırsa, onu da yenilə
            if hasattr(self, 'vacation_panel_active') and self.vacation_panel_active:
                try:
                    self.toggle_vacation_panel(show=False)
                    self.toggle_vacation_panel(show=True, employee_name=self.current_panel_employee)
                except Exception as e:
                    logging.error(f"Məzuniyyət paneli yenilənərkən xəta: {e}")
            
            # Bildirişləri yenilə
            self._update_notification_button()
            
            logging.info(f"✅ Məzuniyyət refresh tamamlandı: {change_type}")
            
        except Exception as e:
            logging.error(f"Məzuniyyət refresh xətası: {e}")
    
    def _immediate_employee_refresh(self, change_type, details=None):
        """İşçi dəyişiklikləri üçün dərhal refresh"""
        try:
            logging.info(f"🔄 İşçi refresh: {change_type}")
            
            # Cache-i etibarsız et
            from utils import cache
            cache.invalidate_cache()
            
            # Məlumatları force refresh ilə yenilə
            self.data = database.load_data_for_user(self.current_user, force_refresh=True)
            
            # İşçi siyahısını yenilə
            self.refresh_employee_list()
            
            # Bildirişləri yenilə
            self._update_notification_button()
            
            logging.info(f"✅ İşçi refresh tamamlandı: {change_type}")
            
        except Exception as e:
            logging.error(f"İşçi refresh xətası: {e}")
    
    def _immediate_notification_refresh(self, change_type, details=None):
        """Bildiriş dəyişiklikləri üçün dərhal refresh"""
        try:
            logging.info(f"🔄 Bildiriş refresh: {change_type}")
            
            # Bildirişləri yenilə
            self._update_notification_button()
            
            logging.info(f"✅ Bildiriş refresh tamamlandı: {change_type}")
            
        except Exception as e:
            logging.error(f"Bildiriş refresh xətası: {e}")
    
    def _immediate_system_refresh(self, change_type, details=None):
        """Sistem dəyişiklikləri üçün dərhal refresh"""
        try:
            logging.info(f"🔄 Sistem refresh: {change_type}")
            
            # Cache-i etibarsız et
            from utils import cache
            cache.invalidate_cache()
            
            # Məlumatları force refresh ilə yenilə
            self.data = database.load_data_for_user(self.current_user, force_refresh=True)
            
            # İşçi siyahısını yenilə
            self.refresh_employee_list()
            
            # Bildirişləri yenilə
            self._update_notification_button()
            
            # Sistem dəyişiklikləri üçün xüsusi emal
            if change_type == 'maintenance_mode_enabled':
                messagebox.showwarning("Sistem Xəbərdarlığı", "Sistem texniki xidmət rejimindədir!")
            elif change_type == 'maintenance_mode_disabled':
                messagebox.showinfo("Sistem Məlumatı", "Sistem normal rejimə qayıtdı!")
            elif change_type in ['users_force_logout', 'users_timed_logout']:
                messagebox.showwarning("Sistem Xəbərdarlığı", "Sistemdən çıxış tələb olunur!")
                # Logout callback-i çağır
                if hasattr(self, 'logout_callback'):
                    self.logout_callback()
            
            logging.info(f"✅ Sistem refresh tamamlandı: {change_type}")
            
        except Exception as e:
            logging.error(f"Sistem refresh xətası: {e}")
    
    def _immediate_local_refresh(self, change_type, details=None):
        """Lokal refresh - real-time signal alındıqda"""
        # Log silmə siqnallarını yoxla
        if change_type in ['log_deleted', 'user_logs_deleted']:
            try:
                try:
                    from utils.log_helper import check_and_process_deletion_signals
                except ImportError:
                    from src.utils.log_helper import check_and_process_deletion_signals
                
                user_id = self.current_user.get('id') if self.current_user else None
                if user_id:
                    # Asinxron şəkildə silmə siqnallarını yoxla
                    import threading
                    def check_signals():
                        try:
                            check_and_process_deletion_signals(user_id)
                        except Exception:
                            pass
                    
                    thread = threading.Thread(target=check_signals, daemon=True)
                    thread.start()
            except Exception:
                pass
        try:
            # DEBUG: Signal məlumatlarını log et
            current_user_id = self.current_user.get('id')
            logging.info(f"🔍 DEBUG: Signal alındı: {change_type}")
            logging.info(f"🔍 DEBUG: Signal details: {details}")
            logging.info(f"🔍 DEBUG: Cari istifadəçi ID: {current_user_id}")
            
            # YENİ: Əgər signal admin özünü çıxarmaq üçün göndərilibsə, admin özünə təsir etməsin
            if details and details.get('exclude_current_user') and details.get('executed_by') == 'admin':
                affected_users = details.get('affected_users', [])
                admin_id = details.get('admin_id')
                
                logging.info(f"🔍 DEBUG: exclude_current_user: {details.get('exclude_current_user')}")
                logging.info(f"🔍 DEBUG: executed_by: {details.get('executed_by')}")
                logging.info(f"🔍 DEBUG: affected_users: {affected_users}")
                logging.info(f"🔍 DEBUG: admin_id: {admin_id}")
                logging.info(f"🔍 DEBUG: current_user_id: {current_user_id}")
                logging.info(f"🔍 DEBUG: current_user_id affected_users-də: {current_user_id in affected_users}")
                
                if current_user_id in affected_users:
                    logging.info(f"🔍 DEBUG: Admin özünə göndərilən signal ignore edildi: {change_type}")
                    return
                else:
                    logging.info(f"🔍 DEBUG: Signal admin üçün deyil, davam edilir")
            
            logging.info(f"Lokal refresh başladıldı: {change_type}")
            
            # Cache-i etibarsız et
            from utils import cache
            cache.invalidate_cache()
            
            # Məlumatları yenilə
            self.data = database.load_data_for_user(self.current_user, force_refresh=True)
            
            # İşçi siyahısını yenilə
            self.refresh_employee_list()
            
            # Bildirişləri yenilə
            self._update_notification_button()
            
            # Profil düyməsinin mətnini yenilə
            self.update_profile_button()
            
            # Cari işçi seçilmişsə, onun məlumatlarını da yenilə
            if hasattr(self, 'employee_listbox') and self.employee_listbox.curselection():
                self.on_employee_select(None)
            
            logging.info(f"Lokal refresh tamamlandı: {change_type}")
            
        except Exception as e:
            logging.error(f"Lokal refresh xətası: {e}")
    
    def send_realtime_signal(self, change_type, details=None):
        """Realtime signal göndərir - avtomatik background thread-də işləyir"""
        import threading
        
        def send_in_background():
            """Background thread-də signal göndərir"""
            start_time = time.time()
            
            try:
                # DEBUG: Signal göndərilməyə başladı
                current_user_id = self.current_user.get('id')
                logging.info(f"🔍 DEBUG: Signal göndərilməyə başladı (background): {change_type}")
                logging.info(f"🔍 DEBUG: Signal göndərən istifadəçi ID: {current_user_id}")
                logging.info(f"🔍 DEBUG: Signal details: {details}")
                
                # YENİ: Əgər admin özü signal göndərir və exclude_current_user True-dursa, özünə göndərmə
                if details and details.get('exclude_current_user') and details.get('executed_by') == 'admin':
                    admin_id = details.get('admin_id')
                    if admin_id == current_user_id:
                        logging.info(f"🔍 DEBUG: Admin özünə signal göndərməyi dayandırdı: {change_type}")
                        # Yalnız lokal refresh et, signal göndərmə
                        self.after(0, self._immediate_local_refresh, change_type, details)
                        return
                
                log_signal_sent(change_type, details, "main_frame")
                
                notifier = get_notifier()
                if notifier:
                    notifier.send_change_notification(change_type, details)
                    logging.info(f"🟢 Realtime signal göndərildi: {change_type}")
                
                    # DEBUG: Signal göndərilmə uğurlu
                    log_performance("signal_send", time.time() - start_time, {"change_type": change_type}, "main_frame")
                    
                    # Dərhal lokal refresh et
                    self.after(0, self._immediate_local_refresh, change_type, details)
                else:
                    logging.warning("Notifier tapılmadı - signal göndərilə bilmədi")
                    log_performance("signal_send", time.time() - start_time, {"error": "notifier_not_found"}, "main_frame")
                    # Notifier yoxdursa da lokal refresh et
                    self.after(0, self._immediate_local_refresh, change_type, details)
            except Exception as e:
                logging.error(f"Realtime signal göndərilərkən xəta: {e}")
                log_performance("signal_send", time.time() - start_time, {"error": str(e)}, "main_frame")
                # Xəta olduqda da lokal refresh et
                self.after(0, self._immediate_local_refresh, change_type, details)
        
        # Background thread-də göndər
        thread = threading.Thread(target=send_in_background, daemon=True)
        thread.start()
    
    def manual_refresh_data(self):
        """Manual olaraq məlumatları yeniləyir"""
        try:
            logging.info("Manual refresh başladıldı")
            
            # Cache-i etibarsız et
            from utils import cache
            cache.invalidate_cache()
            
            # Məlumatları force refresh ilə yenilə
            self.data = database.load_data_for_user(self.current_user, force_refresh=True)
            
            # İşçi siyahısını yenilə
            self.refresh_employee_list()
            
            # Bildirişləri yenilə
            self._update_notification_button()
            
            # Profil düyməsinin mətnini yenilə
            self.update_profile_button()
            
            # Açıq pəncərələri yenilə
            self._refresh_all_windows()
            
            # Status mesajı göstər
            self.update_status_label.config(text="✅ Məlumatlar manual olaraq yeniləndi")
            
            # Real-time signal göndər
            self.send_realtime_signal("manual_refresh", {"source": "manual_button"})
            
            logging.info("Manual refresh tamamlandı")
            
            # Cari işçi seçilmişsə, onun məlumatlarını da yenilə
            if hasattr(self, 'employee_listbox') and self.employee_listbox.curselection():
                self.on_employee_select(None)
                
        except Exception as e:
            logging.error(f"Manual refresh xətası: {e}")
            if hasattr(self, 'update_status_label'):
                self.update_status_label.config(text="❌ Manual refresh xətası")
    
    def _force_refresh_data(self):
        """Məcburi refresh - cache-i tamamilə təmizləyir"""
        try:
            logging.info("Force refresh başladıldı")
            
            # Bütün cache-i təmizlə
            from utils import cache
            cache.clear_all_cache()
            
            # Məlumatları force refresh ilə yenilə
            self.data = database.load_data_for_user(self.current_user, force_refresh=True)
            
            # İşçi siyahısını yenilə
            self.refresh_employee_list()
            
            # Bildirişləri yenilə
            self._update_notification_button()
            
            # Profil düyməsinin mətnini yenilə
            self.update_profile_button()
            
            # Açıq pəncərələri yenilə
            self._refresh_all_windows()
            
            # Status mesajı göstər
            self.update_status_label.config(text="🔄 Force refresh tamamlandı")
            
            # Real-time signal göndər
            self.send_realtime_signal("force_refresh", {"source": "force_refresh_button"})
            
            logging.info("Force refresh tamamlandı")
            
        except Exception as e:
            logging.error(f"Force refresh xətası: {e}")
            if hasattr(self, 'update_status_label'):
                self.update_status_label.config(text="❌ Force refresh xətası")

    def update_realtime_status(self):
        """Real-time status göstəricisini yeniləyir"""
        is_notifier_active = get_notifier() is not None
        self.realtime_status_label.config(text="🟢 Realtime aktiv" if is_notifier_active else "🔴 Realtime aktiv yoxdur")
        self.after(500, self.update_realtime_status) # 0.5 saniyədən bir yenilə
    
    def update_profile_button(self):
        """Profil düyməsinin mətnini yeniləyir"""
        try:
            if hasattr(self, 'profile_button'):
                # profile_button Label-dir, text parametri yoxdur (yalnız image var)
                # Tooltip-i yenilə
                new_tooltip = f"👤 {self.current_user['name']} ({self.current_user['role']})"
                # Tooltip-i yeniləmək üçün widget-ə bağlı tooltip-i tap və yenilə
                # Amma tooltip sadəcə hover zamanı göstərilir, dəyişdirməyə ehtiyac yoxdur
                pass  # Label-də text yoxdur, yalnız image var
        except Exception as e:
            logging.error(f"Profil düyməsi yeniləmə xətası: {e}")

    def open_realtime_status_window(self):
        """Realtime status pəncərəsini açır"""
        # Təhlükəsizlik yoxlaması: Yalnız admin realtime status pəncərəsini aça bilər
        if self.current_user['role'].strip() != 'admin':
            messagebox.showwarning("Xəbərdarlıq", "Yalnız admin realtime status pəncərəsini aça bilər!")
            return
            
        try:
            from .realtime_status_window import RealtimeStatusWindow
            win = RealtimeStatusWindow(self, self.current_user)
            self.opened_windows.append(win)
            self._center_toplevel(win)
        except Exception as e:
            messagebox.showerror("Xəta", f"Realtime status pəncərəsi açıla bilmədi: {e}")
    
    def open_debug_viewer_window(self):
        """Debug viewer pəncərəsini açır"""
        # Təhlükəsizlik yoxlaması: Yalnız admin debug viewer pəncərəsini aça bilər
        if self.current_user['role'].strip() != 'admin':
            messagebox.showwarning("Xəbərdarlıq", "Yalnız admin debug viewer pəncərəsini aça bilər!")
            return
            
        try:
            from .debug_viewer_window import DebugViewerWindow
            win = DebugViewerWindow(self)
            self.opened_windows.append(win)
            self._center_toplevel(win)
        except Exception as e:
            messagebox.showerror("Xəta", f"Debug viewer pəncərəsi açıla bilmədi: {e}")

    def open_my_queries_window(self):
        """Adi istifadəçilər üçün öz məzuniyyət sorğularını görə bilmə pəncərəsi"""
        logging.info("=== open_my_queries_window başladı ===")
        print("🔍 DEBUG: open_my_queries_window başladı")
        
        # Təhlükəsizlik yoxlaması: Yalnız adi istifadəçilər bu pəncərəni aça bilər
        if self.is_admin:
            logging.warning("Admin istifadəçi Sorgularım pəncərəsini açmağa çalışır")
            print("⚠️ DEBUG: Admin istifadəçi Sorgularım pəncərəsini açmağa çalışır")
            messagebox.showwarning("Xəbərdarlıq", "Admin istifadəçilər üçün bu funksiya mövcud deyil!")
            return
            
        try:
            # Cari istifadəçinin məlumatlarını al
            current_user_name = self.current_user.get('name', '')
            logging.info(f"Cari istifadəçi adı: {current_user_name}")
            print(f"👤 DEBUG: Cari istifadəçi adı: {current_user_name}")
            
            if not current_user_name:
                logging.error("İstifadəçi adı tapılmadı")
                print("❌ DEBUG: İstifadəçi adı tapılmadı")
                messagebox.showerror("Xəta", "İstifadəçi məlumatları tapılmadı!")
                return
                
            # İstifadəçinin məlumatlarını data-dan tap
            logging.info(f"Data-dan istifadəçi məlumatları axtarılır: {current_user_name}")
            print(f"🔍 DEBUG: Data-dan istifadəçi məlumatları axtarılır: {current_user_name}")
            user_info = self.data.get(current_user_name)
            logging.info(f"Tapılan user_info: {user_info}")
            print(f"📋 DEBUG: Tapılan user_info keys: {list(user_info.keys()) if user_info else 'None'}")
            
            if not user_info:
                logging.error("İstifadəçi məlumatları data-dan tapılmadı")
                print("❌ DEBUG: İstifadəçi məlumatları data-dan tapılmadı")
                messagebox.showerror("Xəta", "İstifadəçi məlumatları yüklənə bilmədi!")
                return
                
            # İstifadəçinin db_id-ni al
            db_id = user_info.get('db_id')
            logging.info(f"İstifadəçinin db_id: {db_id}")
            print(f"🆔 DEBUG: İstifadəçinin db_id: {db_id}")
            
            if not db_id:
                logging.error("İstifadəçinin db_id tapılmadı")
                print("❌ DEBUG: İstifadəçinin db_id tapılmadı")
                messagebox.showerror("Xəta", "İstifadəçi ID-si tapılmadı!")
                return
                
            # Əvvəlcə employee_details görünüşünü göstər
            logging.info("employee_details görünüşü göstərilir...")
            print("🔄 DEBUG: employee_details görünüşü göstərilir...")
            self.show_view('employee_details')
            
            # Qısa gecikmə əlavə et
            print("⏳ DEBUG: 100ms gecikmə...")
            self.after(100, lambda: self._continue_my_queries_setup(current_user_name, db_id))
            
            logging.info(f"İstifadəçi {current_user_name} öz məzuniyyət sorğularını açdı")
            print(f"✅ DEBUG: İstifadəçi {current_user_name} öz məzuniyyət sorğularını açdı")
            
        except Exception as e:
            logging.error(f"Sorgularım pəncərəsi açılarkən xəta: {e}")
            print(f"❌ DEBUG: Sorgularım pəncərəsi açılarkən xəta: {e}")
            import traceback
            logging.error(f"Traceback: {traceback.format_exc()}")
            print(f"📋 DEBUG: Traceback: {traceback.format_exc()}")
            messagebox.showerror("Xəta", f"Sorgularım pəncərəsi açıla bilmədi: {e}")
        
        logging.info("=== open_my_queries_window bitdi ===")
        print("🏁 DEBUG: open_my_queries_window bitdi")

    def _continue_my_queries_setup(self, current_user_name, db_id):
        """Sorgularım pəncərəsinin qurulmasını davam etdirir"""
        logging.info("=== _continue_my_queries_setup başladı ===")
        print(f"🔄 DEBUG: _continue_my_queries_setup başladı - {current_user_name}, {db_id}")
        
        try:
            # İstifadəçinin öz məzuniyyət sorğularını göstər
            logging.info(f"show_employee_by_id çağırılır: {db_id}")
            print(f"👤 DEBUG: show_employee_by_id çağırılır: {db_id}")
            self.show_employee_by_id(db_id)
            
            # Daha uzun gecikmədən sonra məzuniyyət sorğusu pəncərəsini aç
            logging.info("Vacation panel açılması planlaşdırılır...")
            print("⏳ DEBUG: Vacation panel açılması planlaşdırılır... (500ms gecikmə)")
            self.after(500, lambda: self._open_vacation_panel(current_user_name))
            
        except Exception as e:
            logging.error(f"_continue_my_queries_setup xətası: {e}")
            print(f"❌ DEBUG: _continue_my_queries_setup xətası: {e}")
            import traceback
            logging.error(f"Traceback: {traceback.format_exc()}")
            print(f"📋 DEBUG: Traceback: {traceback.format_exc()}")
        
        logging.info("=== _continue_my_queries_setup bitdi ===")
        print("🏁 DEBUG: _continue_my_queries_setup bitdi")

    def _open_vacation_panel(self, current_user_name):
        """Vacation panel açır"""
        logging.info("=== _open_vacation_panel başladı ===")
        print(f"🔄 DEBUG: _open_vacation_panel başladı - {current_user_name}")
        
        try:
            # Vacation panel açılmasından əvvəl cari görünüşü yoxla
            current_view = None
            for view_name, view_frame in self.views.items():
                try:
                    if hasattr(view_frame, 'winfo_viewable') and view_frame.winfo_viewable():
                        current_view = view_name
                        break
                except:
                    continue
            
            logging.info(f"Cari aktiv görünüş: {current_view}")
            print(f"👁️ DEBUG: Cari aktiv görünüş: {current_view}")
            
            # Vacation panel aç
            logging.info(f"toggle_vacation_panel çağırılır: {current_user_name}")
            print(f"📋 DEBUG: toggle_vacation_panel çağırılır: {current_user_name}")
            self.toggle_vacation_panel(show=True, employee_name=current_user_name)
            
            # Panel açıldıqdan sonra yoxla
            self.after(100, lambda: self._check_vacation_panel_status(current_user_name))
            
        except Exception as e:
            logging.error(f"_open_vacation_panel xətası: {e}")
            print(f"❌ DEBUG: _open_vacation_panel xətası: {e}")
            import traceback
            logging.error(f"Traceback: {traceback.format_exc()}")
            print(f"📋 DEBUG: Traceback: {traceback.format_exc()}")
        
        logging.info("=== _open_vacation_panel bitdi ===")
        print("🏁 DEBUG: _open_vacation_panel bitdi")

    def _check_vacation_panel_status(self, current_user_name):
        """Vacation panel statusunu yoxlayır"""
        logging.info("=== _check_vacation_panel_status başladı ===")
        print(f"🔍 DEBUG: _check_vacation_panel_status başladı - {current_user_name}")
        
        try:
            # Panel statusunu yoxla
            panel_active = getattr(self, 'vacation_panel_active', False)
            logging.info(f"Vacation panel aktiv: {panel_active}")
            print(f"📋 DEBUG: Vacation panel aktiv: {panel_active}")
            
            # Panel görünürlüyünü yoxla
            if hasattr(self, 'vacation_form_panel'):
                try:
                    panel_visible = self.vacation_form_panel.winfo_viewable()
                    logging.info(f"Vacation panel görünür: {panel_visible}")
                    print(f"👁️ DEBUG: Vacation panel görünür: {panel_visible}")
                except Exception as e:
                    logging.warning(f"Panel görünürlüyü yoxlanıla bilmədi: {e}")
                    print(f"⚠️ DEBUG: Panel görünürlüyü yoxlanıla bilmədi: {e}")
            
            # Məlumat mesajı göstər
            if panel_active:
                print(f"✅ DEBUG: {current_user_name} üçün Sorgularım pəncərəsi uğurla açıldı!")
                logging.info(f"{current_user_name} üçün Sorgularım pəncərəsi uğurla açıldı")
            else:
                print(f"❌ DEBUG: {current_user_name} üçün Sorgularım pəncərəsi açıla bilmədi!")
                logging.error(f"{current_user_name} üçün Sorgularım pəncərəsi açıla bilmədi")
                
        except Exception as e:
            logging.error(f"_check_vacation_panel_status xətası: {e}")
            print(f"❌ DEBUG: _check_vacation_panel_status xətası: {e}")
        
        logging.info("=== _check_vacation_panel_status bitdi ===")
        print("🏁 DEBUG: _check_vacation_panel_status bitdi")




    def _on_click_outside(self, event):
        """Click outside handler"""
        pass
