# unified_app.py (Tamamilə tkinter əsaslı birləşdirilmiş versiya)

import tkinter as tk
from tkinter import ttk, messagebox
import logging
import os
import sys
import json
import traceback
import bcrypt
import psycopg2
import uuid
import math
import threading

# PyInstaller EXE rejimində paket yollarını əlavə et
try:
    if getattr(sys, 'frozen', False):
        base_path = getattr(sys, '_MEIPASS', os.path.abspath(os.path.dirname(__file__)))
        src_path_mei = os.path.join(base_path, 'src')
        if src_path_mei not in sys.path:
            sys.path.insert(0, src_path_mei)
        if base_path not in sys.path:
            sys.path.insert(0, base_path)
    else:
        # Normal rejim üçün kök və src yollarını təhlükəsiz əlavə et
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
        src_path_fs = os.path.join(project_root, 'src')
        for p in (project_root, src_path_fs):
            if p not in sys.path:
                sys.path.insert(0, p)
except Exception:
    pass

# Importları həm normal, həm də PyInstaller EXE rejimində işləyəcək şəkildə qururuq
try:
    from database import database
    from utils import cache
    from ui.auth import LoginFrame, RegisterFrame
    from ui.main_frame import MainAppFrame
    from ui.loading_animation import LoadingAnimation
    from ui.password_reset_window import PasswordResetFrame  # Şifrə sıfırlama frame-i
    from core.tenant_manager import SettingsManager, LocalApiLogic
    from utils.updater import UpdaterService
except ImportError:
    # Kaynak kod strukturu 'src' kökü ilə istifadə olunursa
    from src.database import database
    from src.utils import cache
    from src.ui.auth import LoginFrame, RegisterFrame
    from src.ui.main_frame import MainAppFrame
    from src.ui.loading_animation import LoadingAnimation
    from src.ui.password_reset_window import PasswordResetFrame  # Şifrə sıfırlama frame-i
    from src.core.tenant_manager import SettingsManager, LocalApiLogic
    from src.utils.updater import UpdaterService  # <-- YENİ ƏLAVƏ

# cache modulunu cache_manager kimi istifadə edirik
cache_manager = cache

APP_VERSION = "7.1"

# Global dəyişənlər
_current_conn_string = None

def get_log_file_path():
    """Log faylının yolunu qaytarır - artıq debug_logs qovluğunda"""
    try:
        # Log helper istifadə et
        try:
            from utils.log_helper import get_log_file_path as get_log_path, archive_existing_log
        except ImportError:
            from src.utils.log_helper import get_log_file_path as get_log_path, archive_existing_log
        
        # Mövcud log faylını arxiv et
        archive_existing_log('unified_app_debug.log')
        
        # Yeni log faylının yolunu al (timestamp ilə)
        return get_log_path('unified_app_debug.log', with_timestamp=True)
    except Exception:
        # Fallback - köhnə yol
        app_data_dir = os.path.join(os.getenv('APPDATA'), 'MezuniyyetSistemi')
        os.makedirs(app_data_dir, exist_ok=True)
        return os.path.join(app_data_dir, 'unified_app_debug.log')

def setup_logging():
    """Logging konfiqurasiyası - DEBUG səviyyəsi"""
    log_file = get_log_file_path()
    
    # File handler
    file_handler = logging.FileHandler(log_file, encoding='utf-8', mode='w')
    file_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(file_formatter)
    
    # Stream handler
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(file_formatter)
    
    # Database handler - verilənlər bazasına yazmaq üçün
    class DatabaseLogHandler(logging.Handler):
        def emit(self, record):
            try:
                try:
                    from utils.log_helper import log_to_database_async
                except ImportError:
                    from src.utils.log_helper import log_to_database_async
                
                log_message = self.format(record)
                log_file_name = os.path.basename(log_file) if log_file else None
                log_to_database_async('unified_app_debug', log_message, log_file_name)
            except Exception:
                pass
    
    db_handler = DatabaseLogHandler()
    db_handler.setFormatter(file_formatter)
    
    logging.basicConfig(
        level=logging.DEBUG,  # DEBUG səviyyəsi
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            file_handler,
            stream_handler,
            db_handler
        ]
    )

def setup_database_connection():
    """
    Lokal saxlanmış tenant_id-ni oxuyur, mərkəzi bazadan həqiqi qoşulma
    sətrini alır və proqram üçün konfiqurasiya edir.
    Xəta baş verdikdə konfiqurasiyanı təmizləyir.
    """
    global _current_conn_string
    settings = SettingsManager()
    try:
        tenant_id = settings.get_tenant_id()
        company_name = settings.get_company_name()

        if not tenant_id:
            # Xəta mesajını göstərmirik, sadəcə False qaytarırıq
            logging.warning("Aktiv şirkət konfiqurasiyası tapılmadı.")
            return False, None

        # Mərkəzi serverə müraciət etmədən əvvəl serverin işləyib-işləmədiyini yoxlayırıq
        try:
            import requests
            response = requests.get("https://mezuniyyet-serverim.onrender.com/health", timeout=5)
            if response.status_code != 200:
                logging.warning("Mərkəzi server işləmir")
                return False, None
        except ImportError:
            logging.warning("requests modulu tapılmadı - offline rejim")
            return False, None
        except Exception as e:
            logging.warning(f"Mərkəzi serverə qoşulmaq mümkün olmadı: {e}")
            return False, None

        api_logic = LocalApiLogic()
        details, error = api_logic.get_tenant_details(tenant_id)

        if error:
            # Xəta mesajını göstərmirik, sadəcə False qaytarırıq
            logging.warning(f"Şirkət məlumatları alına bilmədi: {error}")
            return False, None
        
        conn_string = details.get("connection_string")
        if not conn_string:
             logging.warning(f"Boş database konfiqurasiyası. Tenant ID: {tenant_id}")
             return False, None

        # Təhlükəsizlik: Connection string log-larda göstərilmir
        # Yalnız tenant_id log-lanır
        logging.info(f"Database konfiqurasiyası server-dən alındı (tenant_id: {tenant_id})")
        
        # Connection string-i düzəlt - əgər postgresql:// ilə başlamırsa, əlavə et
        if not conn_string.startswith('postgresql://'):
            if conn_string.startswith('postgres://'):
                conn_string = conn_string.replace('postgres://', 'postgresql://', 1)
            else:
                # Əgər heç biri ilə başlamırsa, postgresql:// əlavə et
                conn_string = f"postgresql://{conn_string}"
        
        # Təhlükəsizlik: Connection string log-larda göstərilmir
        logging.info(f"Database konfiqurasiyası təyin edildi (tenant_id: {tenant_id})")

        from database.connection import set_connection_params
        set_connection_params(conn_string)
        
        # database.py moduluna da göndər
        try:
            from database import database
            database.set_connection_params(conn_string)
            logging.info(f"Database konfiqurasiyası modullara təyin edildi (tenant_id: {tenant_id})")
        except Exception as e:
            logging.warning(f"database.py moduluna database konfiqurasiyası göndərilmədi: {e}")
        
        # Təhlükəsizlik: conn_string-i global variable-da saxlamırıq
        # Connection string yalnız runtime-da istifadə olunur, saxlanılmır
        global _current_conn_string
        _current_conn_string = None  # Təhlükəsizlik üçün None
        return True, company_name

    except Exception as e:
        logging.error(f"setup_database_connection xətası: {e}", exc_info=True)
        return False, None

# ==============================================================================
# UPDATE PROGRESS DIALOG
# ==============================================================================
class UpdateProgressDialog(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.title("Yeniləmə Prosesi")
        self.geometry("450x200")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()
        
        # İkon təyin edirik
        try:
            import os, sys
            if getattr(sys, 'frozen', False):
                # EXE rejimində
                base_path = sys._MEIPASS
                icon_path = os.path.join(base_path, 'icons', 'icon.ico')
            else:
                # Normal Python rejimində
                # src/icons-dan icon yüklə
                icon_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'icons', 'icon.ico')
            
            if os.path.exists(icon_path):
                self.iconbitmap(icon_path)
        except Exception as e:
            import logging
            logging.warning(f"Update dialog ikonu yüklənə bilmədi: {e}")
        
        # Pəncərəni mərkəzləşdir
        self.center_window()
        
        # UI elementləri
        self.create_widgets()
        
    def center_window(self):
        """Pəncərəni ekranın mərkəzinə yerləşdirir."""
        self.update_idletasks()
        width = self.winfo_reqwidth()
        height = self.winfo_reqheight()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f"{width}x{height}+{x}+{y}")
        
    def create_widgets(self):
        """UI elementlərini yaradır."""
        # Əsas frame
        main_frame = ttk.Frame(self, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Başlıq
        title_label = ttk.Label(main_frame, text="Yeniləmə Prosesi", font=("Segoe UI", 12, "bold"))
        title_label.pack(pady=(0, 15))
        
        # Status label
        self.status_label = ttk.Label(main_frame, text="Yeniləmə hazırlanır...", font=("Segoe UI", 10))
        self.status_label.pack(pady=(0, 15))
        
        # Progress bar
        self.progress_bar = ttk.Progressbar(main_frame, mode='determinate', length=350)
        self.progress_bar.pack(pady=(0, 10))
        
        # Progress label
        self.progress_label = ttk.Label(main_frame, text="0%", font=("Segoe UI", 9))
        self.progress_label.pack(pady=(0, 15))
        
        # Məlumat mətn
        info_label = ttk.Label(main_frame, text="Zəhmət olmasa gözləyin, yeniləmə endirilir...", 
                              font=("Segoe UI", 8), foreground="gray")
        info_label.pack()
        
    def update_status(self, text):
        """Status mətnini yeniləyir."""
        try:
            self.status_label.config(text=text)
            self.update()
        except Exception as e:
            print(f"Status yeniləmə xətası: {e}")
        
    def update_progress(self, percent):
        """Progress bar və faiz mətnini yeniləyir."""
        try:
            self.progress_bar['value'] = percent
            self.progress_label.config(text=f"{percent:.1f}%")
            self.update()
        except Exception as e:
            print(f"Progress yeniləmə xətası: {e}")
        
    def close_dialog(self):
        """Pəncərəni bağlayır."""
        self.destroy()

# ==============================================================================
# LAUNCHER PƏNCƏRƏLƏRİ
# ==============================================================================
class BaseDialog(tk.Toplevel):
    def __init__(self, parent, title):
        super().__init__(parent)
        self.title(title)
        self.parent = parent
        self.result = None
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()
        
        # İkon təyin edirik
        try:
            import os, sys
            if getattr(sys, 'frozen', False):
                # EXE rejimində - icons are in root icons folder
                base_path = sys._MEIPASS
                icon_path = os.path.join(base_path, 'icons', 'icon.ico')
            else:
                # Normal Python rejimində - src/icons-dan icon yüklə
                icon_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'icons', 'icon.ico')
            
            if os.path.exists(icon_path):
                self.iconbitmap(icon_path)
        except Exception as e:
            import logging
            logging.warning(f"Dialog ikonu yüklənə bilmədi: {e}")

        self.api_logic = LocalApiLogic()
        self.settings = SettingsManager()

        self.main_frame = ttk.Frame(self, padding=20)
        self.main_frame.pack(expand=True, fill="both")

        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self.bind("<Escape>", self._on_close)

    def _on_close(self, event=None):
        self.result = None
        self.destroy()

    def _center_window(self):
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f'{width}x{height}+{x}+{y}')

class ChoiceDialog(BaseDialog):
    def __init__(self, parent, has_tenant):
        super().__init__(parent, "Əməliyyat Seçimi")
        self.choice = None
        self.back_requested = False

        # Başlıq
        title_label = ttk.Label(self.main_frame, text="Zəhmət olmasa, bir əməliyyat seçin:", font=("Segoe UI", 12, "bold"))
        title_label.pack(pady=(0, 15))
        
        # Əməliyyat seçimləri
        self.v = tk.StringVar(value="user")
        
        # Radio düymələr üçün frame
        radio_frame = ttk.Frame(self.main_frame)
        radio_frame.pack(fill="x", pady=(0, 15))
        
        ttk.Radiobutton(radio_frame, text="Admin (Yeni Şirkət Yaradacağam)", variable=self.v, value="admin").pack(anchor="w", pady=3)
        ttk.Radiobutton(radio_frame, text="İstifadəçi (Mənə Verilən Linklə Qoşulacağam)", variable=self.v, value="user").pack(anchor="w", pady=3)
        ttk.Radiobutton(radio_frame, text="Admin (Unudulmuş Linki Tapacağam)", variable=self.v, value="relink").pack(anchor="w", pady=3)
        
        # Düymələr üçün frame
        btn_frame = ttk.Frame(self.main_frame)
        btn_frame.pack(fill="x", pady=(15, 0))

        # Sol tərəf - Geri dönmə düyməsi
        left_frame = ttk.Frame(btn_frame)
        left_frame.pack(side="left")
        
        if has_tenant:
            back_btn = ttk.Button(left_frame, text="← Girişə Geri Dön", command=self._on_back, style="Secondary.TButton")
            back_btn.pack(side="left")
        
        # Sağ tərəf - Əsas düymələr
        right_frame = ttk.Frame(btn_frame)
        right_frame.pack(side="right")
        
        ttk.Button(right_frame, text="Çıxış", command=self._on_close).pack(side="right")
        ttk.Button(right_frame, text="Davam Et →", command=self._on_ok, style="Accent.TButton").pack(side="right", padx=5)
        
        self._center_window()
        
    def _on_ok(self):
        self.choice = self.v.get()
        self.destroy()

    def _on_back(self):
        self.back_requested = True
        self.destroy()

class ConnectWithLinkWindow(BaseDialog):
    def __init__(self, parent):
        super().__init__(parent, "Link ilə Qoşulma")
        ttk.Label(self.main_frame, text="Şirkət Linkini (ID) daxil edin:").pack(pady=5)
        self.link_var = tk.StringVar()
        ttk.Entry(self.main_frame, textvariable=self.link_var, width=50).pack(pady=5, ipady=3)
        ttk.Button(self.main_frame, text="Qoşul", command=self._connect, style="Accent.TButton").pack(pady=10)
        self._center_window()

    def _connect(self):
        tenant_id_str = self.link_var.get().strip()
        if not tenant_id_str:
            messagebox.showwarning("Xəta", "Link boş ola bilməz!", parent=self)
            return
        try:
            tenant_id = uuid.UUID(tenant_id_str)
        except ValueError:
            messagebox.showerror("Xəta", "Link düzgün formatda deyil (UUID).", parent=self)
            return
        details, error = self.api_logic.get_tenant_details(tenant_id_str)
        if error:
            messagebox.showerror("Xəta", f"Bu link ilə şirkət tapılmadı: {error}", parent=self)
        else:
            self.settings.set_active_tenant(tenant_id, details.get("name"))
            messagebox.showinfo("Uğurlu", f"'{details.get('name')}' şirkətinə uğurla qoşuldunuz!", parent=self)
            self.result = True
            self.destroy()

class RelinkWindow(BaseDialog):
    def __init__(self, parent):
        super().__init__(parent, "Link İdarəetmə Mərkəzi")
        
        # Notebook (tab sistemi) yaradırıq
        self.notebook = ttk.Notebook(self.main_frame)
        self.notebook.pack(fill="both", expand=True, pady=10)
        
        # Tab 1: Connection string ilə axtarış
        self.tab1 = ttk.Frame(self.notebook)
        self.notebook.add(self.tab1, text="Connection String")
        
        ttk.Label(self.tab1, text="Qeydiyyatdan keçirdiyiniz şirkətin baza qoşulma sətrini daxil edin:").pack(pady=5)
        self.conn_str_var = tk.StringVar()
        ttk.Entry(self.tab1, textvariable=self.conn_str_var, width=60).pack(pady=5, ipady=3)
        ttk.Button(self.tab1, text="Linki Tap", command=self._relink_by_connection, style="Accent.TButton").pack(pady=10)
        
        # Tab 2: Şirkət adına görə axtarış
        self.tab2 = ttk.Frame(self.notebook)
        self.notebook.add(self.tab2, text="Şirkət Adı")
        
        ttk.Label(self.tab2, text="Şirkət adını daxil edin:").pack(pady=5)
        self.company_name_var = tk.StringVar()
        ttk.Entry(self.tab2, textvariable=self.company_name_var, width=40).pack(pady=5, ipady=3)
        ttk.Button(self.tab2, text="Axtar", command=self._search_by_name, style="Accent.TButton").pack(pady=10)
        
        # Tab 3: Bütün linklərim
        self.tab3 = ttk.Frame(self.notebook)
        self.notebook.add(self.tab3, text="Bütün Linklərim")
        
        ttk.Button(self.tab3, text="Linkləri Yüklə", command=self._load_all_links, style="Accent.TButton").pack(pady=10)
        
        # Nəticə sahəsi
        self.result_frame = ttk.Frame(self.main_frame)
        self.result_frame.pack(fill="both", expand=True, pady=10)
        
        self.result_text = tk.Text(self.result_frame, height=10, width=70)
        self.result_text.pack(fill="both", expand=True)
        
        self._center_window()
        
    def _relink_by_connection(self):
        conn_str = self.conn_str_var.get().strip()
        if not conn_str:
            messagebox.showwarning("Xəta", "Qoşulma sətri daxil edilməlidir!", parent=self)
            return
        
        self.result_text.delete(1.0, tk.END)
        self.result_text.insert(tk.END, "Axtarılır...\n")
        self.update()
        
        result, error = self.api_logic.relink_to_tenant(conn_str)
        if error:
            self.result_text.delete(1.0, tk.END)
            self.result_text.insert(tk.END, f"Xəta: {error}")
        else:
            self.result_text.delete(1.0, tk.END)
            self.result_text.insert(tk.END, f"✅ Link Tapıldı!\n\n")
            self.result_text.insert(tk.END, f"Şirkət: {result.get('name')}\n")
            self.result_text.insert(tk.END, f"Link ID: {result.get('tenant_id')}\n")
            self.result_text.insert(tk.END, f"Giriş sayı: {result.get('access_count', '0')}\n")
            self.result_text.insert(tk.END, f"\nUniversal Link:\n{result.get('universal_link')}\n")
            
            # Mübadilə buferinə kopyala
            self.clipboard_clear()
            self.clipboard_append(result.get('tenant_id'))
    
    def _search_by_name(self):
        company_name = self.company_name_var.get().strip()
        if not company_name:
            messagebox.showwarning("Xəta", "Şirkət adı daxil edilməlidir!", parent=self)
            return
        
        self.result_text.delete(1.0, tk.END)
        self.result_text.insert(tk.END, "Axtarılır...\n")
        self.update()
        
        results, error = self.api_logic.search_company_by_name(company_name)
        if error:
            self.result_text.delete(1.0, tk.END)
            self.result_text.insert(tk.END, f"Xəta: {error}")
        else:
            self.result_text.delete(1.0, tk.END)
            if results:
                self.result_text.insert(tk.END, f"✅ {len(results)} şirkət tapıldı:\n\n")
                for i, company in enumerate(results, 1):
                    if isinstance(company, dict):
                        self.result_text.insert(tk.END, f"{i}. {company.get('name', 'Naməlum')}\n")
                        self.result_text.insert(tk.END, f"   Link ID: {company.get('id', 'Naməlum')}\n")
                        self.result_text.insert(tk.END, f"   Yaradılma: {company.get('created_at', 'Naməlum')}\n")
                        self.result_text.insert(tk.END, f"   Son giriş: {company.get('last_accessed', 'Naməlum')}\n")
                        self.result_text.insert(tk.END, f"   Giriş sayı: {company.get('access_count', 'Naməlum')}\n\n")
                    else:
                        self.result_text.insert(tk.END, f"{i}. {company}\n")
            else:
                self.result_text.insert(tk.END, "❌ Heç bir şirkət tapılmadı.")
    
    def _load_all_links(self):
        self.result_text.delete(1.0, tk.END)
        self.result_text.insert(tk.END, "Linklər yüklənir...\n")
        self.update()
        
        links, error = self.api_logic.get_my_all_links()
        if error:
            self.result_text.delete(1.0, tk.END)
            self.result_text.insert(tk.END, f"Xəta: {error}")
        else:
            self.result_text.delete(1.0, tk.END)
            if links:
                self.result_text.insert(tk.END, f"📋 Bütün Linkləriniz ({len(links)} ədəd):\n\n")
                for i, link in enumerate(links, 1):
                    self.result_text.insert(tk.END, f"{i}. {link['name']}\n")
                    self.result_text.insert(tk.END, f"   Link ID: {link['id']}\n")
                    self.result_text.insert(tk.END, f"   Universal Link: {link['universal_link']}\n")
                    self.result_text.insert(tk.END, f"   Yaradılma: {link['created_at']}\n")
                    self.result_text.insert(tk.END, f"   Son giriş: {link['last_accessed']}\n")
                    self.result_text.insert(tk.END, f"   Giriş sayı: {link['access_count']}\n\n")
            else:
                self.result_text.insert(tk.END, "❌ Heç bir link tapılmadı.")

class CreateTenantWindow(BaseDialog):
    def __init__(self, parent):
        super().__init__(parent, "Yeni Şirkət Qurulumu")
        
        form_frame = ttk.Frame(self.main_frame)
        form_frame.pack(pady=5)
        
        ttk.Label(form_frame, text="Şirkətin Adı:").grid(row=0, column=0, sticky="w", pady=2)
        self.company_name_var = tk.StringVar()
        ttk.Entry(form_frame, textvariable=self.company_name_var, width=50).grid(row=0, column=1, pady=2)
        
        ttk.Label(form_frame, text="Baza Qoşulma Sətri:").grid(row=1, column=0, sticky="w", pady=2)
        self.conn_str_var = tk.StringVar()
        ttk.Entry(form_frame, textvariable=self.conn_str_var, width=50).grid(row=1, column=1, pady=2)
        
        ttk.Button(self.main_frame, text="Yarat və Linki Al", command=self._create, style="Accent.TButton").pack(pady=10)
        self._center_window()

    def _create(self):
        company = self.company_name_var.get().strip()
        conn_str = self.conn_str_var.get().strip()
        if not company or not conn_str:
            messagebox.showwarning("Xəta", "Bütün məlumatlar doldurulmalıdır!", parent=self)
            return

        result, error = self.api_logic.create_tenant(company, conn_str)
        if error:
            messagebox.showerror("Xəta", error, parent=self)
        else:
            tenant_id = result.get("tenant_id")
            self.settings.set_active_tenant(tenant_id, company)
            messagebox.showinfo("Uğurlu", f"'{company}' adlı şirkət uğurla yaradıldı!\n\nLink: {tenant_id}\n\nLink mübadilə buferinə kopyalandı.", parent=self)
            self.clipboard_clear()
            self.clipboard_append(tenant_id)
            self.result = True
            self.destroy()

# ==============================================================================
# ƏSAS TƏTBİQ SINİFİ (Tamamilə tkinter əsaslı)
# ==============================================================================
class UnifiedApplication(tk.Tk):
    def __init__(self):
        super().__init__()
        
        # Açılış vaxtını ölçmək üçün timer başlat
        import time
        self.startup_start_time = time.time()
        print(f"⏱️ [STARTUP] Proqram başladı: {self.startup_start_time:.3f}")
        
        # Pəncərəni əvvəlcə gizlədirik ki, ghost window görünməsin
        self.withdraw()
        
        # Pəncərə debug logging
        self._setup_window_debug()
        
        # Azərbaycan dili üçün əlavə təyinləmələr
        self._setup_azerbaijani_support()
        
        # Offline database-i başlat
        try:
            from database.offline_db import init_offline_db
            init_offline_db()
            print("Offline database initialized successfully")
        except Exception as e:
            print(f"Failed to initialize offline database: {e}")
        
        # Debug sistemi başlat
        try:
            from utils.realtime_debug import init_debugger
            init_debugger()
            print("DEBUG: Debug system started")
        except Exception as e:
            print(f"DEBUG: Could not start debug system: {e}")
        
        self.session_id = None
        self.login_history_id = None
        self.current_user = None
        self.version_info = {"current": APP_VERSION, "latest": ""}
        self.company_name = None
        
        # Azərbaycan dili üçün font təyin et
        font_name = self._get_azerbaijani_font()
        self.main_font = font_name  # String olaraq saxla, tuple formatında istifadə et
        
        self.remember_session = False
        self.current_mode = "launcher"  # "launcher" və ya "main_app"
        self.update_progress_dialog = None  # Update progress dialog üçün
        self.connection_retry_count = 0  # Server qoşulma cəhd sayı
        # self.debug_mode = tk.BooleanVar(value=False)  # Debug rejimi üçün dəyişən (SİLİNDİ)

        self.title(f"Məzuniyyət İdarəetmə Sistemi v{self.version_info['current']}")
        self.resizable(True, True)  # Pəncərə ölçüsünü dəyişməyə icazə ver
        # self.state('zoomed')        # Açılan kimi tam ekran olsun - SİLİNDİ

        # Minimize → taskbar → geri bərpa sabitliyi üçün event-lər
        try:
            self.bind('<Unmap>', lambda e: self._on_window_minimized())
            # Map event-ini sadəcə debug üçün istifadə edirik, restore event-ini ayrı bind edirik
            self.bind('<Map>', self._on_window_map)
        except Exception:
            pass
        
        # İkon təyin edirik
        try:
            import os, sys
            if getattr(sys, 'frozen', False):
                # EXE rejimində - icons are in root icons folder
                base_path = sys._MEIPASS
                icon_path = os.path.join(base_path, 'icons', 'icon.ico')
            else:
                # Normal Python rejimində - src/icons-dan icon yüklə
                icon_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'icons', 'icon.ico')
            
            if os.path.exists(icon_path):
                self.iconbitmap(icon_path)
        except Exception as e:
            import logging
            logging.warning(f"İkon yüklənə bilmədi: {e}")
        
        self.configure_styles()
        self.container = ttk.Frame(self)
        self.container.pack(fill="both", expand=True)
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.frames = {}
        
        # Tema sistemi silindi
        
        # Lokal bazanı başlatmaq lazım deyil - bütün məlumatlar Neon bazasındadır
        
        # İlk rejimi müəyyən edirik
        self.determine_initial_mode()

        # Debug checkbox və logging səviyyəsi ilə bağlı kodlar SİLİNDİ

        # EXE-də log faylının yeri artıq göstərilmir (istifadəçi tələbi ilə)
        # Log faylı: %APPDATA%\MezuniyyetSistemi\debug_console.log

        # Proqram açılarkən Debug pəncərəsini də yanaşı göstər
        # DEAKTİV EDİLDİ - Debug pəncərəsi artıq avtomatik açılmır
        # Yalnız development mühitində (PyInstaller deyil) açılır
        # def is_pyinstaller():
        #     """PyInstaller EXE mühitində olub-olmadığımızı yoxlayır"""
        #     return getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS')

        # if not is_pyinstaller():
        #     # Yalnız development mühitində debug pəncərəsini aç
        #     try:
        #         from utils.debug_manager import show_debug_window
        #         # Tk tam hazır olduqdan sonra açmaq üçün qısa gecikmə ilə planlaşdır
        #         self.after(200, lambda: show_debug_window(self))
        #     except Exception:
        #         pass

    def _setup_window_debug(self):
        """Pəncərə debug logging təyinləməsi"""
        self.window_debug_enabled = False  # Debug logging söndürüldü
        self.last_geometry = None
        self.last_position = None
        
        # Pəncərə event-lərini izlə (yalnız kritik xətalar üçün)
        # self.bind('<Configure>', self._on_window_configure)  # Çox debug mesajı yaradır
        # self.bind('<Map>', self._on_window_map)  # Çox debug mesajı yaradır
        # self.bind('<Unmap>', self._on_window_unmap)  # Çox debug mesajı yaradır
        # self.bind('<FocusIn>', self._on_window_focus_in)  # Çox debug mesajı yaradır
        # self.bind('<FocusOut>', self._on_window_focus_out)  # Çox debug mesajı yaradır
        
        print("DEBUG: Window debug logging disabled")

    def _on_window_configure(self, event):
        """Pəncərə konfiqurasiyası dəyişəndə"""
        if not self.window_debug_enabled:
            return
            
        current_geometry = self.geometry()
        current_position = (event.x, event.y)
        
        if current_geometry != self.last_geometry:
            print(f"DEBUG: Window size changed: {current_geometry}")
            self.last_geometry = current_geometry
            
        if current_position != self.last_position:
            print(f"DEBUG: Window position changed: {current_position}")
            self.last_position = current_position

    def _on_window_map(self, event):
        """Pəncərə göstərildikdə"""
        if self.window_debug_enabled:
            print(f"DEBUG: Window shown: {self.geometry()}")
        
        # Pəncərə göstərildikdə ölçüsünü dəyişdirməyək
        # Bu funksiya sadəcə debug məqsədi ilə istifadə olunur

    def _on_window_unmap(self, event):
        """Pəncərə gizlədildikdə"""
        if self.window_debug_enabled:
            print(f"DEBUG: Window hidden")

    def _on_window_focus_in(self, event):
        """Pəncərə fokus aldıqda"""
        if self.window_debug_enabled:
            print(f"DEBUG: Window focus gained")

    def _on_window_focus_out(self, event):
        """Pəncərə fokusu itirdikdə"""
        if self.window_debug_enabled:
            print(f"DEBUG: Window focus lost")

    def _setup_azerbaijani_support(self):
        """Azərbaycan dili üçün əlavə təyinləmələr"""
        try:
            # Tkinter encoding təyinləməsi
            import tkinter as tk
            
            # Font təyinləməsi - Azərbaycan dili üçün ən yaxşı fontu istifadə et
            best_font = self._get_azerbaijani_font()
            self.option_add('*Font', f'{best_font} 10')
            
            # Encoding təyinləməsi
            if hasattr(self, 'tk'):
                self.tk.eval('encoding system utf-8')
            
            print("Azerbaijani language support enabled")
            
        except Exception as e:
            print(f"Error: Could not enable Azerbaijani language support: {e}")

    def _get_azerbaijani_font(self):
        """Azərbaycan dili üçün ən yaxşı fontu tapır"""
        import tkinter.font as tkFont
        
        # Azərbaycan hərflərini dəstəkləyən fontların siyahısı (prioritet sırası ilə)
        # Qeyd: Boşluq olan font adları Tkinter-də problem yaradır, ona görə Tahoma prioritetdir
        azerbaijani_fonts = [
            "Tahoma",
            "Verdana",
            "Arial",
            "Helvetica",
            "Calibri",
            "Cambria",
            "Georgia",
            "Arial Unicode MS",
            "Microsoft YaHei",
            "Trebuchet MS",
            "Lucida Sans Unicode",
            "Times New Roman",
            "Comic Sans MS",
            "SimSun"
        ]
        
        # Mövcud fontları yoxla
        available_fonts = list(tkFont.families())
        
        # Azərbaycan hərflərini dəstəkləyən fontu tap
        for font_name in azerbaijani_fonts:
            if font_name in available_fonts:
                print(f"Selected font for Azerbaijani: {font_name}")
                return font_name
        
        # Əgər heç biri tapılmadısa, default font istifadə et
        print("No suitable font found for Azerbaijani, using default font")
        return "TkDefaultFont"

    def configure_styles(self):
        s = ttk.Style()
        s.theme_use('vista')
        
        # Sadə stil təyinləmələri - font parametrlərini çıxartdıq
        s.configure('TCheckbutton', background='white')
        s.configure('TLabel')
        s.configure('TButton')
        s.configure('TEntry')
        s.configure('TCombobox')
        s.configure('Treeview')
        s.configure('Treeview.Heading')
        
        # Əlavə stillər
        s.configure("Accent.TButton")
        s.configure("Secondary.TButton")
        s.configure("Azerbaijani.TLabel")
        s.configure("Azerbaijani.TButton")
        s.configure("Azerbaijani.TEntry")

    def determine_initial_mode(self):
        """İlk rejimi müəyyən edir"""
        print(f"DEBUG: Program started - determining initial mode")
        print(f"DEBUG: Current window size: {self.geometry()}")
        print(f"DEBUG: Window state: {self.state()}")
        
        settings = SettingsManager()
        current_tenant_id = settings.get_tenant_id()
        
        if current_tenant_id:
            # Aktiv şirkət varsa, birbaşa giriş pəncərəsinə keçirik
            print(f"DEBUG: Active company found: {current_tenant_id}")
            print(f"DEBUG: Switching to login mode")
            self.switch_to_login_mode()
        else:
            # Aktiv şirkət yoxdursa, launcher rejimində qalırıq
            print(f"DEBUG: No active company found")
            print(f"DEBUG: Switching to launcher mode")
            self.show_launcher_mode()
        
        # Pəncərəni konfiqurasiya edildikdən sonra göstəririk
        print(f"DEBUG: Showing window after configuration")
        self.deiconify()
        self.lift()
        self.focus_force()
        self.update_idletasks()  # Pəncərəni dərhal yenilə
        print(f"DEBUG: Window shown - final size: {self.geometry()}")


    def show_launcher_mode(self):
        """Launcher rejimini göstərir"""
        print(f"DEBUG: Showing launcher mode")
        print(f"DEBUG: Current window size: {self.geometry()}")
        
        self.current_mode = "launcher"
        self.title(f"Məzuniyyət İdarəetmə Sistemi v{self.version_info['current']} - Şirkət Seçimi")
        
        # Pəncərəni mərkəzə yerləşdir və ölçüsünü təyin et (yalnız normal rejimdə)
        current_state = self.state()
        if current_state != 'zoomed' and current_state != 'maximized':
            self.center_window(600, 400)
            self.resizable(False, False)  # Ölçü dəyişməyə icazə verilmir
            self.state('normal')          # Maximize olmur
        else:
            print(f"DEBUG: Pencere artiq tam ekrandadir ({current_state}), olcusu deyisdirilmir")
        
        print(f"DEBUG: Launcher mode set")
        # Mövcud widgetləri təmizləyirik
        for widget in self.container.winfo_children():
            widget.destroy()
        # Launcher interfeysini yaradırıq
        self.create_launcher_interface()

    def create_launcher_interface(self):
        """Launcher interfeysini yaradır"""
        # Başlıq
        title_label = ttk.Label(self.container, text="Məzuniyyət İdarəetmə Sistemi", 
                               font=(self.main_font, 16, 'bold'))
        title_label.pack(pady=(20, 10))
        
        subtitle_label = ttk.Label(self.container, text="Şirkət Seçimi və Qoşulma", 
                                  font=(self.main_font, 12))
        subtitle_label.pack(pady=(0, 30))
        
        # Seçim çərçivəsi
        choice_frame = ttk.LabelFrame(self.container, text="Əməliyyat Seçimi", padding=20)
        choice_frame.pack(padx=50, pady=20, fill="x")
        
        self.choice_var = tk.StringVar(value="user")
        
        ttk.Radiobutton(choice_frame, text="Admin (Yeni Şirkət Yaradacağam)", 
                       variable=self.choice_var, value="admin").pack(anchor="w", pady=5)
        ttk.Radiobutton(choice_frame, text="İstifadəçi (Mənə Verilən Linklə Qoşulacağam)", 
                       variable=self.choice_var, value="user").pack(anchor="w", pady=5)
        ttk.Radiobutton(choice_frame, text="Admin (Unudulmuş Linki Tapacağam)", 
                       variable=self.choice_var, value="relink").pack(anchor="w", pady=5)
        
        # Düymələr çərçivəsi
        button_frame = ttk.Frame(self.container)
        button_frame.pack(pady=20)
        
        # Sol tərəf - Geri dönmə düyməsi
        left_frame = ttk.Frame(button_frame)
        left_frame.pack(side="left")
        
        # Mövcud tenant var mı yoxlayırıq
        settings = SettingsManager()
        has_tenant = settings.get_tenant_id() is not None
        
        if has_tenant:
            back_btn = ttk.Button(left_frame, text="← Girişə Geri Dön", 
                                 command=self.switch_to_main_app_mode, 
                                 style="Secondary.TButton", width=15)
            back_btn.pack(side="left", padx=5)
        
        # Sağ tərəf - Əsas düymələr
        right_frame = ttk.Frame(button_frame)
        right_frame.pack(side="right")
        
        ttk.Button(right_frame, text="Çıxış", command=self.quit, width=15).pack(side="right", padx=5)
        ttk.Button(right_frame, text="Davam Et →", command=self.handle_launcher_choice, 
                  style="Accent.TButton", width=15).pack(side="right", padx=5)

    def handle_launcher_choice(self):
        """Launcher seçimini emal edir"""
        choice = self.choice_var.get()
        
        if choice == "admin":
            self.show_create_tenant_dialog()
        elif choice == "user":
            self.show_connect_dialog()
        elif choice == "relink":
            self.show_relink_dialog()

    def show_create_tenant_dialog(self):
        """Yeni şirkət yaratma dialoqu"""
        dialog = CreateTenantWindow(self)
        self.wait_window(dialog)
        if dialog.result:
            self.switch_to_main_app_mode()

    def show_connect_dialog(self):
        """Qoşulma dialoqu"""
        dialog = ConnectWithLinkWindow(self)
        self.wait_window(dialog)
        if dialog.result:
            self.switch_to_main_app_mode()

    def show_relink_dialog(self):
        """Link tapma dialoqu"""
        dialog = RelinkWindow(self)
        self.wait_window(dialog)

    def switch_to_login_mode(self):
        """Giriş rejiminə keçir və arxa fonda serverə qoşulma cəhdi edir"""
        try:
            print(f"DEBUG: switch_to_login_mode basladi")
            print(f"DEBUG: Cari pencere olcusu: {self.geometry()}")
            print(f"DEBUG: Cari pencere state: {self.state()}")
        except UnicodeEncodeError:
            logging.info("DEBUG: switch_to_login_mode started")
        
        settings = SettingsManager()
        company_name = settings.get_company_name()
        
        # Şirkət adını təyin edirik
        self.company_name = company_name or "Naməlum Şirkət"
        self.current_mode = "login"
        self.title(f"Məzuniyyət İdarəetmə Sistemi v{self.version_info['current']} - {self.company_name}")
        print(f"DEBUG: Şirkət adı təyin edildi: {self.company_name}")
        
        # Pəncərə ölçüsünü təyin edirik
        current_state = self.state()
        print(f"DEBUG: Pəncərə state yoxlanılır: {current_state}")
        
        # Əgər pəncərə tam ekrandadırsa, əvvəlcə normal rejimə gətir
        if current_state == 'zoomed' or current_state == 'maximized':
            print(f"DEBUG: Pəncərə tam ekrandadır, normal rejimə gətirilir")
            self.state('normal')
            self.update_idletasks()  # State dəyişikliyini emal et
        
        # Pəncərəni resizable et (əvvəlcə)
        self.resizable(True, True)
        
        # Pəncərə ölçüsünü təyin et
        print(f"DEBUG: Pəncərə ölçüsü təyin edilir: 400x550")
        self.center_window(400, 550)
        
        # Resizable-ı false et
        self.resizable(False, False)
        
        print(f"DEBUG: Pəncərə ölçüsü təyin edildi: {self.geometry()}, state: {self.state()}")
        
        # Mövcud widgetləri təmizləyirik
        print(f"DEBUG: Mövcud widgetlər təmizlənir")
        for widget in self.container.winfo_children():
            widget.destroy()
        print(f"DEBUG: Widgetlər təmizləndi")
        
        # Login frame-i birbaşa əsas thread-də yaradırıq
        print(f"DEBUG: show_frame('Login') çağırılır")
        self.show_frame('Login')
        print(f"DEBUG: show_frame('Login') tamamlandı")
        
        # Pəncərəni yenidən göstəririk (əgər gizlədilibsə)
        print(f"DEBUG: Pəncərə yenidən göstərilir")
        self.deiconify()
        self.lift()
        self.focus_force()
        self.update_idletasks()  # Pəncərəni dərhal yenilə
        print(f"DEBUG: Pəncərə göstərildi - final ölçü: {self.geometry()}")
        
        # Avtomatik giriş yoxlaması (daha gec - yumuşaq açılma üçün)
        print(f"DEBUG: Avtomatik giriş yoxlaması təyin edilir")
        self.after(500, self.check_auto_login)  # 50ms-dən 500ms-ə artırdıq
        
        # Arxa fonda serverə qoşulma cəhdi edirik (daha gec)
        print(f"DEBUG: Server qoşulma cəhdi təyin edilir")
        self.after(1000, self.attempt_server_connection_async)  # 150ms-dən 1000ms-ə artırdıq
        print(f"DEBUG: switch_to_login_mode tamamlandı")
    
    def attempt_server_connection_async(self):
        """Arxa fonda serverə qoşulma cəhdi edir (async)"""
        def connection_worker():
            try:
                # Yalnız tenant ID ilə qoşulma
                is_connected, company_name = setup_database_connection()
                # UI yeniləməsini əsas thread-də edirik
                self.after(0, self.update_connection_status, is_connected, company_name)
            except Exception as e:
                logging.error(f"Server qoşulma cəhdi xətası: {e}")
                self.after(0, self.update_connection_status, False, None)
        
        import threading
        threading.Thread(target=connection_worker, daemon=True).start()
    
    def update_connection_status(self, is_connected, company_name):
        """Server qoşulma statusunu yeniləyir"""
        if is_connected:
            self.company_name = company_name
            self.title(f"Məzuniyyət İdarəetmə Sistemi v{self.version_info['current']} - {self.company_name}")
            # Şirkət adını yaşıl rəngdə göstəririk
            self.update_company_status(True)
            self.server_connected = True
        else:
            # Şirkət adını boz rəngdə göstəririk
            self.update_company_status(False)
            self.server_connected = False
    
    def check_server_connection_quick(self):
        """Server qoşulmasını tez yoxlayır (5 saniyə)"""
        self.server_connected = False
        self.connection_check_count = 0
        self.max_connection_attempts = 5  # 5 saniyə
        self.connection_retry_count = 0
        
        def check_connection():
            if self.connection_check_count >= self.max_connection_attempts:
                logging.warning("Server qoşulması 5 saniyə sonra da baş vermədi")
                return
            
            self.connection_check_count += 1
            logging.info(f"Server qoşulması yoxlanılır... (Cəhd {self.connection_check_count}/{self.max_connection_attempts})")
            
            try:
                is_connected, company_name = setup_database_connection()
                if is_connected:
                    logging.info("Server qoşulması uğurlu oldu")
                    self.server_connected = True
                    self.company_name = company_name
                    self.title(f"Məzuniyyət İdarəetmə Sistemi v{self.version_info['current']} - {self.company_name}")
                    self.update_company_status(True)
                    return
                else:
                    logging.warning(f"Server qoşulması uğursuz (Cəhd {self.connection_check_count})")
                    self.connection_retry_count += 1
            except Exception as e:
                logging.error(f"Server qoşulma cəhdi xətası: {e}")
                self.connection_retry_count += 1
            
            # 1 saniyə sonra yenidən yoxla
            self.after(1000, check_connection)
        
        check_connection()

    def check_server_connection_with_timeout(self):
        """Server qoşulmasını 30 saniyə gözləyərək yoxlayır"""
        self.server_connected = False
        self.connection_check_count = 0
        self.max_connection_attempts = 30  # 30 saniyə
        self.connection_retry_count = 0
        self.max_retry_attempts = 5  # Maksimum 5 dəfə cəhd
        
        def check_connection():
            if self.connection_check_count >= self.max_connection_attempts:
                # 30 saniyə keçdi, qoşulma baş vermədi
                logging.warning("Server qoşulması 30 saniyə sonra da baş vermədi")
                self.show_connection_retry_message()
                return
            
            try:
                is_connected, company_name = setup_database_connection()
                if is_connected:
                    logging.info("Server qoşulması uğurlu oldu")
                    self.server_connected = True
                    self.company_name = company_name
                    self.title(f"Məzuniyyət İdarəetmə Sistemi v{self.version_info['current']} - {self.company_name}")
                    self.update_company_status(True)
                    return
                else:
                    self.connection_check_count += 1
                    # 1 saniyə sonra yenidən cəhd edirik
                    self.after(1000, check_connection)
            except Exception as e:
                logging.error(f"Server qoşulma cəhdi xətası: {e}")
                self.connection_check_count += 1
                # 1 saniyə sonra yenidən cəhd edirik
                self.after(1000, check_connection)
        
        # İlk cəhdi başladırıq
        check_connection()
    
    def show_connection_retry_message(self):
        """Qoşulma uğursuz olduqda mesaj göstərir və yenidən cəhd edir"""
        if self.connection_retry_count >= self.max_retry_attempts:
            logging.warning("Maksimum cəhd sayına çatıldı, qoşulma dayandırıldı")
            return
        
        self.connection_retry_count += 1
        logging.info(f"Qoşulma uğursuz oldu, {self.connection_retry_count}. cəhd başladılır")
        
        # Mesaj pəncərəsi yaradırıq
        retry_window = tk.Toplevel(self)
        retry_window.title("Server Qoşulması")
        retry_window.geometry("400x150")
        retry_window.resizable(False, False)
        retry_window.transient(self)
        retry_window.grab_set()
        
        # Pəncərəni mərkəzə yerləşdiririk
        retry_window.update_idletasks()
        x = (retry_window.winfo_screenwidth() // 2) - (400 // 2)
        y = (retry_window.winfo_screenheight() // 2) - (150 // 2)
        retry_window.geometry(f"400x150+{x}+{y}")
        
        # Mesaj məzmunu
        frame = tk.Frame(retry_window, bg='white')
        frame.pack(fill='both', expand=True, padx=20, pady=20)
        
        # Xəta ikonu
        error_icon = tk.Label(frame, text="⚠️", font=('Segoe UI', 24), bg='white', fg='orange')
        error_icon.pack(pady=(0, 10))
        
        # Mesaj mətni
        message_text = f"Qoşulma uğursuz oldu, yenidən cəhd edilir...\n3 saniyə gözləyin..."
        message_label = tk.Label(frame, text=message_text, font=('Arial', 10), 
                               bg='white', fg='black', justify='center')
        message_label.pack(pady=(0, 10))
        
        # Proqress bar
        progress_frame = tk.Frame(frame, bg='white')
        progress_frame.pack(fill='x', pady=(0, 10))
        
        progress_bar = tk.Frame(progress_frame, bg='#e0e0e0', height=4)
        progress_bar.pack(fill='x')
        
        progress_fill = tk.Frame(progress_bar, bg='#4CAF50', height=4, width=0)
        progress_fill.pack(side='left', fill='y')
        
        # Geri sayım
        countdown_label = tk.Label(frame, text="3", font=('Segoe UI', 12, 'bold'), 
                                 bg='white', fg='red')
        countdown_label.pack()
        
        # Animasiya funksiyası
        def animate_progress(seconds_left):
            if seconds_left <= 0:
                retry_window.destroy()
                # 30 saniyə sonra yenidən cəhd et
                self.after(30000, self.check_server_connection_with_timeout)
                return
            
            # Proqress bar animasiyası
            progress_width = int((5 - seconds_left) / 5 * 400)  # 400px genişlik
            progress_fill.configure(width=progress_width)
            
            # Geri sayım
            countdown_label.configure(text=str(seconds_left))
            
            # 1 saniyə sonra yenidən çağır
            self.after(1000, lambda: animate_progress(seconds_left - 1))
        
        # Animasiyanı başlat
        animate_progress(5)
    
    
    def update_company_status(self, is_connected):
        """Şirkət statusunu yeniləyir"""
        try:
            # LoginFrame-də şirkət adı label-ini tapırıq və rəngini dəyişirik
            for widget in self.container.winfo_children():
                if hasattr(widget, 'company_label'):
                    if is_connected:
                        widget.company_label.configure(foreground='green')
                    else:
                        widget.company_label.configure(foreground='gray')
                    break
        except Exception as e:
            logging.error(f"Şirkət statusu yeniləmə xətası: {e}")
    
    

    def switch_to_main_app_mode(self):
        """Ana tətbiq rejiminə keçir"""
        # Server əlaqəsini yoxlayırıq - daha qısa timeout ilə
        print("DEBUG: Server elaqesi yoxlanilir (switch_to_main_app_mode)...")
        
        # Server yoxlamasını 5 saniyə ilə məhdudlaşdırıq
        self.server_connection_timeout = 5
        self.check_server_connection_quick()
        
        # Əgər hələ də qoşulmayıbsa, animasiyada mesaj göstəririk
        if not hasattr(self, 'server_connected') or not self.server_connected:
            logging.info("Server qoşulması uğursuz, animasiyada mesaj göstərilir")
            print("🔴 DEBUG: Server qoşulması uğursuz (switch_to_main_app_mode)")
            # Animasiyada xəta mesajı göstər
            self.update_login_animation_status(False)
            return
            
        # Uğurlu qoşulma
        settings = SettingsManager()
        company_name = settings.get_company_name()
        self.company_name = company_name or "Naməlum Şirkət"
        self.current_mode = "main_app"
        self.title(f"Məzuniyyət İdarəetmə Sistemi v{self.version_info['current']} - {self.company_name}")
        
        # Update yoxlamasını dərhal başladırıq
        logging.info("Ana tətbiqə keçid - Update yoxlaması başladılır")
        self.after(1000, self.check_for_update)  # 1 saniyə sonra update yoxlaması
        
        # Ana tətbiqi yaradırıq
        self.check_auto_login()

    def check_auto_login(self):
        """Avtomatik giriş yoxlaması"""
        def auto_login_worker():
            try:
                logging.info("=== check_auto_login başladı ===")
                
                # Cache fayllarının mövcudluğunu yoxlayırıq
                import os
                cache_file = os.path.join(os.getenv('APPDATA'), 'MezuniyyetSistemi', 'user_cache.json')
                user_data_file = os.path.join(os.getenv('APPDATA'), 'MezuniyyetSistemi', 'user_data.json')
                
                logging.info(f"Cache file exists: {os.path.exists(cache_file)}")
                logging.info(f"User data file exists: {os.path.exists(user_data_file)}")
                
                # Cache fayllarının məzmununu yoxlayırıq
                if os.path.exists(cache_file):
                    try:
                        with open(cache_file, 'r', encoding='utf-8') as f:
                            cache_content = f.read()
                            logging.info(f"Cache file content length: {len(cache_content)}")
                    except Exception as e:
                        logging.warning(f"Cache file oxuna bilmədi: {e}")
                
                if os.path.exists(user_data_file):
                    try:
                        with open(user_data_file, 'r', encoding='utf-8') as f:
                            user_data_content = f.read()
                            logging.info(f"User data file content length: {len(user_data_content)}")
                    except Exception as e:
                        logging.warning(f"User data file oxuna bilmədi: {e}")
                
                # Yeni cache sistemi ilə saxlanmış məlumatları yoxlayırıq
                try:
                    from src.utils import cache_manager
                    if cache_manager.has_saved_credentials():
                        logging.info("has_saved_credentials() True qaytardı")
                        credentials = cache_manager.get_user_credentials()
                        logging.info(f"Retrieved credentials keys: {list(credentials.keys()) if credentials else 'None'}")
                        
                        username = credentials.get('username', '')
                        password = credentials.get('password', '')
                        remember_me = credentials.get('remember_me', False)
                        
                        logging.info(f"Username: '{username}', Password length: {len(password) if password else 0}, Remember: {remember_me}")
                        
                        if username and password and remember_me:
                            logging.info(f"Avtomatik giriş cəhdi: {username}")
                            print(f"✅ DEBUG: Avtomatik giriş başladı - Username: {username}, Remember: {remember_me}")
                            # UI yeniləməsini əsas thread-də edirik
                            # Kiçik gecikmə əlavə edirik ki, UI hazır olsun
                            # Closure problemi üçün lambda-da default parametrlərdən istifadə edirik
                            self.after(100, lambda u=username, p=password, r=remember_me: self.attempt_login(u, p, r, True))
                            return
                        else:
                            logging.info("Məlumatlar tam deyil - avtomatik giriş edilmir")
                            logging.info(f"Username empty: {not username}, Password empty: {not password}, Remember: {remember_me}")
                            print(f"⚠️ DEBUG: Avtomatik giriş edilmir - Username: {bool(username)}, Password: {bool(password)}, Remember: {remember_me}")
                    else:
                        logging.info("has_saved_credentials() False qaytardı")
                except ImportError:
                    logging.warning("cache_manager import edilə bilmədi")
                    logging.info("Cache manager mövcud deyil - avtomatik giriş edilmir")
                    
                    # Fallback: Cache fayllarını birbaşa yoxlayırıq
                    try:
                        import json
                        try:
                            from src.utils import cache_manager
                            fallback_credentials = None
                        except ImportError:
                            logging.warning("cache_manager import edilə bilmədi")
                            fallback_credentials = None
                        
                        # Yeni şifrələnmiş cache sistemi ilə məlumatları alırıq
                        fallback_credentials = cache_manager.get_user_credentials()
                        if fallback_credentials and fallback_credentials.get('username') and fallback_credentials.get('remember_me', False):
                            logging.info("Fallback: Şifrələnmiş cache-dən məlumat tapıldı")
                        
                        if fallback_credentials:
                            username = fallback_credentials.get('username', '')
                            password = fallback_credentials.get('password', '')
                            remember_me = fallback_credentials.get('remember_me', False)
                            
                            if username and password and remember_me:
                                logging.info(f"Fallback avtomatik giriş cəhdi: {username}")
                                print(f"✅ DEBUG: Fallback avtomatik giriş başladı - Username: {username}, Remember: {remember_me}")
                                # Closure problemi üçün lambda-da default parametrlərdən istifadə edirik
                                self.after(100, lambda u=username, p=password, r=remember_me: self.attempt_login(u, p, r, True))
                                return
                    except Exception as e:
                        logging.warning(f"Fallback cache yoxlaması xətası: {e}")
                
                # Saxlanmış məlumat yoxdursa və ya avtomatik giriş uğursuz oldusa, normal login frame göstəririk
                logging.info("Normal login frame göstərilir")
                self.after(0, self._show_login_frame_if_needed)
                logging.info("=== check_auto_login bitdi ===")
            except Exception as e:
                logging.error(f"check_auto_login xətası: {e}", exc_info=True)
                print(f"DEBUG: check_auto_login xətası: {e}")
                # Xəta baş verdikdə normal login frame göstəririk
                # Amma yalnız əgər Login frame mövcud deyilsə
                self.after(0, self._show_login_frame_if_needed)
        
        # Avtomatik giriş yoxlamasını arxa fonda edirik
        import threading
        threading.Thread(target=auto_login_worker, daemon=True).start()
    
    def _show_login_frame_if_needed(self):
        """Login frame-i göstərir (əgər lazımdırsa)"""
        print(f"DEBUG: _show_login_frame_if_needed çağırıldı")
        print(f"DEBUG: Mövcud frames: {list(self.frames.keys()) if hasattr(self, 'frames') else 'frames yoxdur'}")
        
        # Əgər Login frame artıq mövcuddursa, yenidən yaratmayaq
        if hasattr(self, 'frames') and 'Login' in self.frames:
            print(f"DEBUG: Login frame artıq mövcuddur, yenidən yaradılmır")
            return
        
        # Əgər container-də Login frame varsa, yenidən yaratmayaq
        if hasattr(self, 'container') and self.container.winfo_children():
            print(f"DEBUG: Container-də widgetlər mövcuddur, yenidən yaradılmır")
            return
        
        print(f"DEBUG: Login frame yaradılır")
        # show_frame əvəzinə birbaşa _create_login_frame çağırırıq
        self._create_login_frame()

    def on_closing(self):
        """Pəncərə 'X' ilə bağlanarkən həmişə sessiyanı silir."""
        if self.current_user and self.session_id:
            try:
                database.remove_user_session(self.session_id, self.login_history_id)
            except Exception as e:
                logging.warning(f"Sessiya bağlanarkən xəta: {e}")

        # Cache-də "Məni xatırla" seçilibsə, cache-i saxlayırıq
        # Yalnız seçilməyibsə təmizləyirik
        try:
            # user_data faylından remember_me dəyərini yoxlayırıq
            user_data = cache_manager.load_user_data()
            if not user_data.get("remember_me", False):
                cache_manager.clear_cache()  # Bu halda bütün cache təmizlənir
                logging.info("Remember me seçilmədiyi üçün cache təmizləndi.")
            else:
                logging.info("Remember me seçildiyi üçün cache saxlanıldı.")
        except Exception as e:
            logging.warning(f"Cache yoxlaması zamanı xəta: {e}")
            # Xəta baş verərsə, cache-i saxlayırıq
            logging.info("Xəta səbəbindən cache saxlanıldı.")
        
        self.destroy()

    def show_frame(self, frame_name):
        try:
            logging.info(f"=== show_frame başladı: {frame_name} ===")
            print(f"DEBUG: Frame changing: {frame_name}")
            print(f"DEBUG: Current window size: {self.geometry()}")
            
            # Mövcud widgetləri təmizləyirik
            for widget in self.container.winfo_children():
                widget.destroy()

            if frame_name == 'Login':
                logging.info("Login frame yaradılır")
                print(f"DEBUG: show_frame('Login') başladı")
                print(f"DEBUG: Cari pəncərə ölçüsü: {self.geometry()}")
                print(f"DEBUG: Cari pəncərə state: {self.state()}")
                
                # Pəncərəni əvvəlcə normal rejimə gətir (tam ekrandadırsa)
                current_state = self.state()
                if current_state == 'zoomed' or current_state == 'maximized':
                    print(f"DEBUG: Pəncərə tam ekrandadır, normal rejimə gətirilir")
                    self.state('normal')
                    self.update_idletasks()
                
                # Pəncərə ölçüsünü Login üçün yenilə (yalnız bir dəfə)
                self.resizable(True, True)
                self.center_window(400, 550)
                self.resizable(False, False)
                print(f"DEBUG: Login frame üçün pəncərə ölçüsü yeniləndi: 400x550")
                
                # Yumuşaq açılma üçün kiçik gecikmə
                print(f"DEBUG: LoginFrame yaradılır...")
                self.after(50, lambda: self._create_login_frame())
                print(f"DEBUG: show_frame('Login') tamamlandı")
            
            elif frame_name == 'Register':
                logging.info("Register frame yaradılır")
                print(f"DEBUG: show_frame('Register') başladı")
                print(f"DEBUG: Cari pəncərə ölçüsü: {self.geometry()}")
                print(f"DEBUG: Cari pəncərə state: {self.state()}")
                
                # Pəncərə ölçüsünü Register üçün təyin et
                self.resizable(True, True)
                self.center_window(500, 700)
                
                # Yumuşaq açılma üçün kiçik gecikmə
                print(f"DEBUG: RegisterFrame yaradılır...")
                self.after(50, lambda: self._create_register_frame())
                print(f"DEBUG: show_frame('Register') tamamlandı")
            
            elif frame_name == 'PasswordReset':
                logging.info("PasswordReset frame yaradılır")
                print(f"DEBUG: show_frame('PasswordReset') başladı")
                print(f"DEBUG: Cari pəncərə ölçüsü: {self.geometry()}")
                print(f"DEBUG: Cari pəncərə state: {self.state()}")
                
                # Pəncərə ölçüsünü PasswordReset üçün təyin et (Register ilə eyni)
                self.resizable(True, True)
                self.center_window(500, 700)
                
                # Yumuşaq açılma üçün kiçik gecikmə
                print(f"DEBUG: PasswordResetFrame yaradılır...")
                self.after(50, lambda: self._create_password_reset_frame())
                print(f"DEBUG: show_frame('PasswordReset') tamamlandı")
        
        except Exception as e:
            logging.error(f"show_frame xətası ({frame_name}): {e}", exc_info=True)
            self.show_error_message("Xəta", f"Pəncərə yaradılarkən xəta: {e}")

    def _create_login_frame(self):
        """Login frame-i yaradır (yumuşaq açılma üçün)"""
        try:
            print(f"DEBUG: _create_login_frame başladı")
            frame = LoginFrame(self.container, self.attempt_login, self.show_register_frame, self.restart_app, self.company_name)
            logging.info("LoginFrame yaradıldı")
            print(f"DEBUG: LoginFrame yaradıldı")
            
            # Şifrə sıfırlama callback-ini əlavə et
            print(f"DEBUG: Şifrə sıfırlama callback əlavə edilir")
            frame.set_forgot_password_callback(self.show_password_reset_frame)
            
            # Frame-i düzgün pack et
            print(f"DEBUG: Frame pack edilir")
            frame.pack(expand=True, fill="both")
            
            # Frame-i frames dictionary-ə əlavə et
            if not hasattr(self, 'frames'):
                self.frames = {}
            self.frames['Login'] = frame
            print(f"DEBUG: Frame frames dictionary-ə əlavə edildi")
            
            # Pəncərəni yenilə
            self.update_idletasks()
            print(f"DEBUG: Pəncərə yeniləndi")
            
            print(f"DEBUG: Login frame yaradılması tamamlandı")
        except Exception as e:
            print(f"DEBUG: Login frame yaradılarkən xəta: {e}")
            logging.error(f"Login frame yaradılarkən xəta: {e}")

    def show_register_frame(self):
        self.show_frame('Register')
    
    def _create_register_frame(self):
        """Register frame-i yaradır (yumuşaq açılma üçün)"""
        try:
            print(f"DEBUG: _create_register_frame başladı")
            frame = RegisterFrame(self.container, self.attempt_register, lambda: self.show_frame('Login'))
            logging.info("RegisterFrame yaradıldı")
            print(f"DEBUG: RegisterFrame yaradıldı")
            
            # Frame-i düzgün pack et
            print(f"DEBUG: Frame pack edilir")
            frame.pack(expand=True, fill="both")
            
            # Frame-i frames dictionary-ə əlavə et
            if not hasattr(self, 'frames'):
                self.frames = {}
            self.frames['Register'] = frame
            print(f"DEBUG: Frame frames dictionary-ə əlavə edildi")
            
            # Pəncərəni yenilə və göstər
            self.update_idletasks()
            self.update()
            print(f"DEBUG: Pəncərə yeniləndi və göstərildi")
            
            # Pəncərəni fokusla
            self.focus_set()
            print(f"DEBUG: Pəncərə fokuslandı")
            
            print(f"DEBUG: Register frame yaradılması tamamlandı")
        except Exception as e:
            print(f"DEBUG: Register frame yaradılarkən xəta: {e}")
            logging.error(f"Register frame yaradılarkən xəta: {e}")
            import traceback
            print(f"DEBUG: Traceback: {traceback.format_exc()}")
            self.show_error_message("Xəta", f"Qeydiyyat pəncərəsi açıla bilmədi: {e}")
        
    def center_window(self, width, height):
        print(f"DEBUG: center_window çağırıldı: {width}x{height}")
        print(f"DEBUG: Cari pəncərə ölçüsü: {self.geometry()}")
        print(f"DEBUG: Cari pəncərə state: {self.state()}")
        
        # Əgər pəncərə tam ekrandadırsa, əvvəlcə normal rejimə gətir
        current_state = self.state()
        if current_state == 'zoomed' or current_state == 'maximized':
            print(f"DEBUG: Pencere tam ekrandadir ({current_state}), normal rejimə gətirilir")
            self.state('normal')
            self.update_idletasks()  # State dəyişikliyini emal et
        
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x = (screen_width // 2) - (width // 2)
        y = (screen_height // 2) - (height // 2)
        
        # Debug logging
        print(f"DEBUG: Ekran ölçüsü: {screen_width}x{screen_height}")
        print(f"DEBUG: Pəncərə ölçüsü: {width}x{height}")
        print(f"DEBUG: Hesablanmış mövqe: ({x}, {y})")
        
        # Pəncərəni bir dəfədə düzgün yerləşdir
        new_geometry = f"{width}x{height}+{x}+{y}"
        print(f"DEBUG: Yeni geometry təyin edilir: {new_geometry}")
        self.geometry(new_geometry)
        self.update_idletasks()  # Pəncərəni dərhal yenilə
        print(f"DEBUG: Geometry təyin edildikdən sonra: {self.geometry()}")
        logging.info(f'center_window: {width}x{height} at ({x},{y})')
        
        # Pəncərə tətbiq edildikdən sonra yoxla
        print(f"DEBUG: Pəncərə yoxlaması təyin edilir")
        self.after(100, self._check_window_after_center)
        print(f"DEBUG: center_window tamamlandı")

    def _check_window_after_center(self):
        """Pəncərə mərkəzləndikdən sonra yoxla"""
        if self.window_debug_enabled:
            current_geometry = self.geometry()
            print(f"DEBUG: Window after centering: {current_geometry}")

    def show_error_message(self, title, message):
        """Xəta mesajını göstərir və bu zaman proqramı gizlədir."""
        # Proqramı gizlədirik
        self.withdraw()
        
        # Xəta mesajını göstəririk
        messagebox.showerror(title, message, parent=self)
        
        # Proqramı yenidən göstəririk
        self.deiconify()
        self.lift()
        self.focus_force()

    def _on_window_minimized(self):
        """Pəncərə minimize ediləndə çağrılır."""
        try:
            self._was_minimized = True
            # Aktiv grab varsa (modal pəncərə), bərpa zamanı blok yaratmasın deyə buraxırıq
            try:
                self.grab_release()
            except Exception:
                pass
        except Exception:
            pass

    def _on_window_restored(self):
        """Taskbar-dan bərpa ediləndə pəncərəni etibarlı şəkildə önə gətirir."""
        try:
            if getattr(self, '_was_minimized', False):
                self._was_minimized = False
                self.deiconify()
                # Pəncərə state-ini məcburi olaraq dəyişdirmirik - istifadəçinin seçimini saxlayırıq
                # self.state('normal')  # Bu sətri silirik ki, pəncərə ölçüsü saxlanılsın
                self.lift()
                self.focus_force()
                # Bir anlıq topmost edib geri alırıq ki, həmişə önə gəlsin
                self.attributes('-topmost', True)
                self.after(200, lambda: self.attributes('-topmost', False))
        except Exception:
            pass

    def show_loading_animation(self):
        """Loading animasiyasını göstərir."""
        import time
        loading_start_time = time.time()
        if hasattr(self, 'startup_start_time'):
            elapsed = loading_start_time - self.startup_start_time
            print(f"⏱️ [STARTUP] Loading animasiyası göstərilir: {elapsed:.3f} saniyə sonra")
        
        self.loading_animation = LoadingAnimation(self.container)
        self.loading_animation.show()
        
        loading_end_time = time.time()
        if hasattr(self, 'startup_start_time'):
            elapsed = loading_end_time - self.startup_start_time
            loading_duration = loading_end_time - loading_start_time
            print(f"⏱️ [STARTUP] Loading animasiyası göstərildi: {elapsed:.3f} saniyə sonra (yaradılma vaxtı: {loading_duration:.3f} saniyə)")

    def hide_loading_and_show_frame(self, frame):
        """Loading animasiyasını gizlədir və frame-i göstərir."""
        import time
        
        # Loading animasiyasını dayandırırıq
        if hasattr(self, 'loading_animation'):
            self.loading_animation.hide()
        
        # Frame-i göstəririk
        self.container.pack(fill="both", expand=True)
        frame.pack(expand=True, fill="both")
        
        # Pəncərəni yeniləyirik - yalnız bir dəfə
        self.update_idletasks()
        
        # Açılış vaxtını ölç və göstər
        if hasattr(self, 'startup_start_time'):
            startup_end_time = time.time()
            startup_duration = startup_end_time - self.startup_start_time
            print(f"⏱️ [STARTUP] Ana pəncərə göstərildi: {startup_end_time:.3f}")
            print(f"⏱️ [STARTUP] ÜMUMİ AÇILIŞ VAXTI: {startup_duration:.3f} saniyə ({startup_duration*1000:.0f} ms)")
            logging.info(f"⏱️ [STARTUP] ÜMUMİ AÇILIŞ VAXTI: {startup_duration:.3f} saniyə ({startup_duration*1000:.0f} ms)")

    def restart_app(self):
        """ Proqramı bağlayır və launcher-in davam etməsinə imkan verir. """
        logging.info("Şirkət dəyişdirilir... Launcher-ə qayıdılır.")
        
        # Aktiv şirkət konfiqurasiyasını saxlayırıq (təmizləmirik)
        # settings = SettingsManager()
        # settings.clear_active_tenant()
        # logging.info(f"Aktiv şirkət konfiqurasiyası təmizləndi.")
        
        # Launcher rejiminə qayıdırıq
        self.show_launcher_mode()

    def attempt_login(self, username, password, remember_me, is_auto_login=False):
        logging.info(f"Giriş cəhdi başladı. İstifadəçi: {username}, Avtomatik: {is_auto_login}")
        print(f"DEBUG: attempt_login basladi - Username: {username}, Auto: {is_auto_login}")
        print(f"DEBUG: Cari pencere olcusu: {self.geometry()}")
        print(f"DEBUG: Cari pencere state: {self.state()}")
        
        # Server əlaqəsini yoxlayırıq - daha qısa timeout ilə
        print("DEBUG: Server elaqesi yoxlanilir...")
        
        # Server yoxlamasını 5 saniyə ilə məhdudlaşdırıq
        self.server_connection_timeout = 5
        self.check_server_connection_quick()
        
        # Əgər hələ də qoşulmayıbsa, offline rejimə keçirik
        if not hasattr(self, 'server_connected') or not self.server_connected:
            logging.info("Server qoşulması uğursuz - offline rejimə keçirik")
            print("DEBUG: Server qosulmasi ugursuz - offline rejimə keçirik")
            self.attempt_offline_login(username, password, remember_me, is_auto_login)
            return
        
        try:
            # Connection string-i yenidən təyin edirik
            if _current_conn_string:
                database.set_connection_params(_current_conn_string)
                logging.info(f"Database konfiqurasiyası yenidən təyin edildi (tenant_id: {self.tenant_id})")
            
            logging.info("İstifadəçi məlumatları alınır...")
            user_data = database.get_user_for_login(username)
            if user_data and bcrypt.checkpw(password.encode('utf-8'), user_data[2].encode('utf-8')):
                user_id = user_data[0]
                max_sessions = user_data[5] if len(user_data) > 5 else 1  # max_sessions sütunundan alırıq (indeks 5)
                logging.info(f"İstifadəçi tapıldı. ID: {user_id}, Maksimum sessiya: {max_sessions}")
                
                # Aktiv sessiya sayını yoxlayırıq
                logging.info("Aktiv sessiya sayı yoxlanır...")
                conn = database.db_connect()
                if conn:
                    try:
                        with conn.cursor() as cur:
                            cur.execute("SELECT COUNT(*) FROM active_sessions WHERE user_id = %s", (user_id,))
                            current_user_sessions = cur.fetchone()[0]
                            logging.info(f"Cari aktiv sessiya sayı: {current_user_sessions}")
                    except Exception as e:
                        logging.error(f"Sessiya sayı yoxlanarkən xəta: {e}", exc_info=True)
                        current_user_sessions = 0
                    finally:
                        conn.close()
                else:
                    logging.warning("Veritabanı qoşulması uğursuz oldu")
                    current_user_sessions = 0
                
                if current_user_sessions >= max_sessions:
                    logging.warning(f"Sessiya limiti aşıldı: {current_user_sessions}/{max_sessions}")
                    messagebox.showwarning("Giriş Məhdudiyyəti", f"Maksimum ({max_sessions}) sessiya limitinə çatmısınız.")
                    if is_auto_login: self.show_frame('Login')
                    return

                logging.info("Sessiya yaradılır...")
                if remember_me:
                    # Yeni cache sistemi ilə istifadəçi məlumatlarını saxlayırıq
                    cache_manager.save_user_credentials(username, password, remember_me)
                    logging.info("İstifadəçi məlumatları həmişə saxlanıldı")
                else:
                    # Remember me seçilməyibsə, məlumatları silirik
                    cache_manager.save_user_credentials(username, password, False)
                    logging.info("İstifadəçi məlumatları silindi")

                ip_address = "127.0.0.1"
                self.session_id, self.login_history_id = database.add_user_session(user_id, ip_address)
                self.current_user = {'id': user_id, 'name': user_data[1], 'role': user_data[3].strip()}
                
                # Log helper-ə cari istifadəçi ID-ni təyin et
                try:
                    try:
                        from utils.log_helper import set_current_user_id, sync_existing_logs_to_database
                    except ImportError:
                        from src.utils.log_helper import set_current_user_id, sync_existing_logs_to_database
                    set_current_user_id(user_id)
                    
                    # Mövcud log fayllarını verilənlər bazasına sinxronlaşdır
                    # Asinxron şəkildə işlədirik ki, login prosesini yavaşlatmasın
                    import threading
                    def sync_logs():
                        try:
                            sync_existing_logs_to_database(user_id)
                        except Exception:
                            pass
                    
                    sync_thread = threading.Thread(target=sync_logs, daemon=True)
                    sync_thread.start()
                except Exception:
                    pass
                
                logging.info(f"Giriş uğurlu. Sessiya ID: {self.session_id}")
                
                # Təhlükəsizlik: Connection string offline mode-da saxlanılmır
                # Yalnız tenant_id və company_name saxlanılır
                try:
                    from database.offline_db import save_connection_info
                    from core.tenant_manager import SettingsManager
                    settings = SettingsManager()
                    tenant_id = settings.get_tenant_id()
                    company_name = settings.get_company_name()
                    if tenant_id:
                        # Connection string saxlanılmır - təhlükəsizlik üçün
                        save_connection_info(tenant_id, company_name, None)
                        logging.info("Connection info saved (connection_string saxlanılmadı - təhlükəsizlik üçün)")
                except Exception as e:
                    logging.warning(f"Failed to save connection info: {e}")
                print(f"DEBUG: Giris ugurlu! User: {user_data[1]}, Role: {user_data[3].strip()}")
                print(f"DEBUG: Pencere olcusu deyisdirilmezden evvel: {self.geometry()}")
                
                # Pəncərəni əvvəlcə gizlədirik ki, ghost window görünməsin
                print("DEBUG: Pencere gizledilir")
                self.withdraw()
                
                # Pəncərə ölçüsünü dəyişdiririk (yalnız normal rejimdə)
                current_state = self.state()
                if current_state != 'zoomed' and current_state != 'maximized':
                    print("DEBUG: Pencere olcusu deyisdirilir: 1200x700")
                    self.resizable(True, True)
                    self.center_window(1200, 700)
                else:
                    print(f"DEBUG: Pencere artiq tam ekrandadir ({current_state}), olcusu deyisdirilmir")
                
                # Container-i tam yeniləyirik
                print("DEBUG: Container tam yenilenir")
                self.container.update_idletasks()
                self.container.update()
                self.update_idletasks()
                self.update()
                
                # Kiçik gecikmə əlavə edirik ki, container tam yenilənsin
                print("🔵 DEBUG: Container yenilənməsi üçün gecikmə")
                self.after(100, self._show_loading_after_resize)
            else:
                logging.warning("İstifadəçi adı və ya şifrə yanlışdır")
                if is_auto_login:
                    cache_manager.clear_database_cache_only()
                    self.show_frame('Login')
                else:
                    self.show_error_message("Xəta", "İstifadəçi adı və ya şifrə yanlışdır.")
        except Exception as e:
            logging.error(f"Giriş cəhdi zamanı xəta: {e}", exc_info=True)
            if is_auto_login:
                cache_manager.clear_database_cache_only()
                self.show_frame('Login')
            else:
                self.show_error_message("Giriş Xətası", f"Giriş zamanı xəta baş verdi: {e}")
    
    def attempt_offline_login(self, username, password, remember_me, is_auto_login=False):
        """Offline rejimdə giriş cəhdi"""
        logging.info(f"Offline giriş cəhdi başladı. İstifadəçi: {username}")
        print(f"DEBUG: attempt_offline_login başladı - Username: {username}")
        
        try:
            # Offline database-dən istifadəçini yoxlayırıq
            from database.offline_db import authenticate_offline, init_offline_db
            
            # Initialize offline database
            init_offline_db()
            
            # Authenticate using offline database
            offline_user = authenticate_offline(username, password)
            
            if offline_user:
                logging.info(f"Offline authentication successful for {username}")
                print(f"DEBUG: Offline authentication ugurlu: {offline_user['name']}")
                
                # Təhlükəsizlik: Offline mode-da connection string istifadə edilmir
                # Server-ə qoşulmaq lazımdır ki, connection string alınsın
                from database.offline_db import get_connection_info
                conn_info = get_connection_info()
                
                if conn_info:
                    # Offline mode-da connection string yoxdur
                    # Server-ə qoşulmaq lazımdır ki, connection string alınsın
                    logging.warning("Offline mode: Database konfiqurasiyası offline bazada yoxdur. Server-ə qoşulmaq lazımdır.")
                    # Offline mode-da işləmək üçün server-ə qoşulmaq lazımdır
                    global _current_conn_string
                    _current_conn_string = None  # Təhlükəsizlik üçün None
                
                # İstifadəçi məlumatlarını saxlayırıq
                self.current_user = {
                    'id': offline_user.get('id', 0),
                    'name': offline_user.get('name', username),
                    'role': offline_user.get('role', 'user'),
                    'offline_mode': True  # Offline mode marker
                }
                
                # Offline mode notification
                messagebox.showinfo(
                    "Offline Rejim", 
                    f"Salam, {offline_user['name']}!\n\n"
                    f"Serverdən qoşulma uğursuz oldu.\n"
                    f"Proqram OFFLINE rejimdə işləyir.\n\n"
                    f"Server bərpa olunan kimi avtomatik bağlantı yaradılacaq."
                )
                
                # Connection monitoring start
                self.start_connection_monitoring()
                
                # Pəncərəni yeniləy spezīalne resize et
                print("DEBUG: Offline mode - pencere resize edilir")
                self.withdraw()
                
                current_state = self.state()
                if current_state != 'zoomed' and current_state != 'maximized':
                    print("DEBUG: Pencere olcusu deyisdirilir: 1200x700 (offline)")
                    self.resizable(True, True)
                    self.center_window(1200, 700)
                else:
                    print(f"DEBUG: Pencere artiq tam ekrandadir ({current_state}), olcusu deyisdirilmir")
                
                self.container.update_idletasks()
                self.container.update()
                self.update_idletasks()
                self.update()
                
                print("🔵 DEBUG: Offline mode - Loading animasiyası")
                self.after(100, self._show_loading_after_resize)
                
            else:
                logging.warning(f"Offline authentication failed for {username}")
                print(f"DEBUG: Offline authentication ugursuz")
                
                # Offline authentication failed - show error
                if is_auto_login:
                    cache_manager.clear_database_cache_only()
                    self.show_frame('Login')
                else:
                    self.show_error_message(
                        "Xəta", 
                        "İstifadəçi adı və ya şifrə yanlışdır.\n\n"
                        "Offline rejimdə yalnız əvvəl bağlı olduğunuz hesab ilə daxil ola bilərsiniz.\n"
                        "Zəhmət olmasa server bərpa olunanadək gözləyin."
                    )
                
        except Exception as e:
            logging.error(f"Offline login attempt error: {e}", exc_info=True)
            print(f"DEBUG: Offline login xətası: {e}")
            
            if is_auto_login:
                cache_manager.clear_database_cache_only()
                self.show_frame('Login')
            else:
                self.show_error_message("Giriş Xətası", f"Offline giriş zamanı xəta baş verdi: {e}")
                
    def start_connection_monitoring(self):
        """Server bağlantısının avtomatik izlənilməsinə başlayır"""
        def check_server_reconnection():
            try:
                # Server bağlantısını yoxlayırıq
                is_connected, company_name = setup_database_connection()
                
                if is_connected:
                    logging.info("Server bərpa olundu!")
                    print("DEBUG: Server bərpa olundu!")
                    
                    # UI update əsas thread-də
                    self.after(0, self.handle_server_reconnection, company_name)
                else:
                    # Hələ server bərpa olunmayıb - 10 saniyə sonra yenidən yoxla
                    if hasattr(self, 'current_user') and self.current_user and self.current_user.get('offline_mode'):
                        self.after(10000, check_server_reconnection)
                        
            except Exception as e:
                logging.error(f"Server reconnection monitoring error: {e}")
                if hasattr(self, 'current_user') and self.current_user and self.current_user.get('offline_mode'):
                    self.after(10000, check_server_reconnection)
        
        # İlk yoxlamanı 5 saniyə sonra edirik
        self.after(5000, check_server_reconnection)
    
    def handle_server_reconnection(self, company_name):
        """Server bərpa olunduqda çağırılır - proqramı yenidən başladır"""
        try:
            logging.info("Server bərpa olundu - proqram yenidən başladılır")
            print("DEBUG: Server bərpa olundu - proqram yenidən başladılır")
            
            # Uğur mesajı göstəririk
            messagebox.showinfo(
                "Server Bərpa Olundu ✓",
                f"Serverdən bərpa edildi!\n\n"
                f"Şirkət: {company_name}\n\n"
                f"Proqram yenidən başladılacaq və online rejimə keçəcək."
            )
            
            # Proqramı yenidən başlat
            self.restart_application()
            
        except Exception as e:
            logging.error(f"Server reconnection handling error: {e}", exc_info=True)
            print(f"DEBUG: Server reconnection handling xətası: {e}")
    
    def restart_application(self):
        """Proqramı yenidən başladır"""
        try:
            import os
            import subprocess
            
            logging.info("Proqram yenidən başladılır...")
            print("DEBUG: Proqram yenidən başladılır...")
            
            # Cari proqramın yolunu al
            if getattr(sys, 'frozen', False):
                # EXE rejimində - sadəcə EXE faylını işə sal
                executable = sys.executable
                # Windows-da CREATE_NO_WINDOW flag istifadə et
                creation_flags = subprocess.CREATE_NO_WINDOW if sys.platform.startswith('win') else 0
                subprocess.Popen([executable], cwd=os.getcwd(), creationflags=creation_flags)
            else:
                # Python rejimində - main.py ilə başlat
                executable = sys.executable
                script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                main_script = os.path.join(script_dir, 'main.py')
                if os.path.exists(main_script):
                    subprocess.Popen([executable, main_script], cwd=os.getcwd())
                else:
                    # Fallback - sadəcə Python interpreter
                    subprocess.Popen([executable], cwd=os.getcwd())
            
            # Cari proqramı bağla - qısa gecikmə ilə
            self.after(500, lambda: self.destroy())
            self.after(1000, lambda: sys.exit(0))
            
        except Exception as e:
            logging.error(f"Proqram yenidən başlatma xətası: {e}", exc_info=True)
            print(f"DEBUG: Proqram yenidən başlatma xətası: {e}")
            # Xəta olsa belə, ən azı proqramı bağla
            try:
                self.after(500, lambda: self.destroy())
                self.after(1000, lambda: sys.exit(0))
            except Exception:
                pass
                
    def _show_loading_after_resize(self):
        """Pəncərə ölçüsü dəyişdirildikdən sonra loading göstərir"""
        print(f"🔵 DEBUG: Container yeniləndikdən sonra ölçü: {self.container.winfo_width()}x{self.container.winfo_height()}")
        print(f"🔵 DEBUG: Pəncərə yeniləndikdən sonra: {self.geometry()}")
        
        # Pəncərəni yenidən göstəririk
        print("🔵 DEBUG: Pəncərə yenidən göstərilir")
        self.deiconify()
        self.lift()
        self.focus_force()
        
        # Loading animasiyasını göstəririk
        print("🔵 DEBUG: Loading animasiyası göstərilir")
        self.show_loading_animation()
        print(f"🔵 DEBUG: Loading animasiyası göstərildikdən sonra pəncərə: {self.geometry()}")
        
        # Main frame thread-ini başladırıq
        self._start_main_frame_thread()
    
    def _start_main_frame_thread(self):
        """Main frame thread-ini başladır"""
        import time
        
        # Main frame yaradılmasının başlanğıc vaxtı
        main_frame_start_time = time.time()
        if hasattr(self, 'startup_start_time'):
            elapsed = main_frame_start_time - self.startup_start_time
            print(f"⏱️ [STARTUP] Main frame thread başladı: {elapsed:.3f} saniyə sonra")
        
        # Frame-i ayrı thread-də yaradırıq ki, UI donmasın
        def create_main_frame():
            import time
            frame_create_start = time.time()
            if hasattr(self, 'startup_start_time'):
                elapsed = frame_create_start - self.startup_start_time
                print(f"⏱️ [STARTUP] MainAppFrame yaradılması başladı: {elapsed:.3f} saniyə sonra")
            
            # MainAppFrame yaradılır (məlumatlar yüklənmədən əvvəl)
            frame = MainAppFrame(self.container, self.current_user, self.version_info, self.logout)
            
            frame_create_end = time.time()
            if hasattr(self, 'startup_start_time'):
                elapsed = frame_create_end - self.startup_start_time
                frame_duration = frame_create_end - frame_create_start
                print(f"⏱️ [STARTUP] MainAppFrame yaradıldı: {elapsed:.3f} saniyə sonra (yaradılma vaxtı: {frame_duration:.3f} saniyə)")
            
            # Loading animasiyasını dayandırırıq və frame-i göstəririk
            # Kiçik gecikmə - frame tam yaradılsın
            self.after(50, self.hide_loading_and_show_frame, frame)
            
            # Update yoxlamasını 3 saniyə sonra başladırıq
            self.after(3000, self.check_for_update)
        
        import threading
        threading.Thread(target=create_main_frame, daemon=True).start()

    def attempt_register(self, name, username, email, password, confirm_password, total_days_str, first_name=None, last_name=None, father_name=None, phone_number=None, birth_date=None, fin_code=None, department_id=None, position_id=None, hire_date=None, salary=None, address=None, emergency_contact=None):
        import logging
        logging.info(f"📝 [REGISTER] Qeydiyyat prosesi başladı: Username={username}, Email={email}")
        print(f"📝 [REGISTER] Qeydiyyat prosesi başladı: Username={username}, Email={email}")
        
        if not all([name, username, email, password, confirm_password, total_days_str]):
            logging.warning(f"⚠️ [REGISTER] Məcburi xanalar doldurulmayıb: Name={bool(name)}, Username={bool(username)}, Email={bool(email)}, Password={bool(password)}, Confirm={bool(confirm_password)}, Days={bool(total_days_str)}")
            print(f"⚠️ [REGISTER] Məcburi xanalar doldurulmayıb")
            self.show_error_message("Xəta", "Bütün məcburi xanalar doldurulmalıdır.")
            return
        
        # Email formatını yoxla
        if "@" not in email or "." not in email:
            logging.warning(f"⚠️ [REGISTER] Email formatı düzgün deyil: {email}")
            print(f"⚠️ [REGISTER] Email formatı düzgün deyil: {email}")
            self.show_error_message("Xəta", "Düzgün email ünvanı daxil edin.")
            return
            
        if password != confirm_password:
            logging.warning(f"⚠️ [REGISTER] Şifrələr eyni deyil")
            print(f"⚠️ [REGISTER] Şifrələr eyni deyil")
            self.show_error_message("Xəta", "Şifrələr eyni deyil.")
            return
        try:
            total_days = int(total_days_str)
            if total_days < 0: raise ValueError
        except (ValueError, TypeError):
            self.show_error_message("Xəta", "Məzuniyyət günü düzgün rəqəm formatında olmalıdır.")
            return
        
        # Maaş rəqəm formatında olmalıdır
        salary_value = None
        if salary:
            try:
                salary_value = float(salary)
                if salary_value < 0: raise ValueError
            except (ValueError, TypeError):
                self.show_error_message("Xəta", "Maaş düzgün rəqəm formatında olmalıdır.")
                return
        
        # Tarix validasiyası
        birth_date_value = "1990-01-01"  # Default tarix
        if birth_date and birth_date.strip():
            try:
                from datetime import datetime
                # Tarix formatını yoxlayırıq
                datetime.strptime(birth_date.strip(), '%Y-%m-%d')
                birth_date_value = birth_date.strip()
            except ValueError:
                self.show_error_message("Xəta", "Doğum tarixi 'YYYY-MM-DD' formatında olmalıdır (məsələn: 1990-01-01).")
                return
        
        hire_date_value = None
        if hire_date and hire_date.strip() and hire_date.strip() != "YYYY-MM-DD":
            try:
                from datetime import datetime
                # Tarix formatını yoxlayırıq
                datetime.strptime(hire_date.strip(), '%Y-%m-%d')
                hire_date_value = hire_date.strip()
            except ValueError:
                self.show_error_message("Xəta", "İşə qəbul tarixi 'YYYY-MM-DD' formatında olmalıdır (məsələn: 2020-01-01).")
                return
        
        try:
            logging.info(f"💾 [REGISTER] Database-də istifadəçi yaradılır: Username={username}, Email={email}")
            print(f"💾 [REGISTER] Database-də istifadəçi yaradılır: Username={username}, Email={email}")
            
            result = database.create_new_user(
                name=name, 
                username=username, 
                password=password, 
                email=email, 
                total_days=total_days,
                first_name=first_name,
                last_name=last_name,
                father_name=father_name,
                phone_number=phone_number,
                birth_date=birth_date_value,
                fin_code=fin_code,
                department_id=department_id,
                position_id=position_id,
                hire_date=hire_date_value,
                salary=salary_value,
                address=address,
                emergency_contact=emergency_contact
            )
            
            logging.info(f"📊 [REGISTER] create_new_user nəticəsi: {result}")
            print(f"📊 [REGISTER] create_new_user nəticəsi: {result}")
            
            if result:
                logging.info(f"✅ [REGISTER] Qeydiyyat uğurlu: Username={username}, Email={email}")
                print(f"✅ [REGISTER] Qeydiyyat uğurlu: Username={username}, Email={email}")
                messagebox.showinfo("Uğurlu", "Qeydiyyat uğurla tamamlandı.")
                self.show_frame('Login')
            else:
                logging.warning(f"⚠️ [REGISTER] Qeydiyyat uğursuz oldu: Username={username}, Email={email}")
                print(f"⚠️ [REGISTER] Qeydiyyat uğursuz oldu: Username={username}, Email={email}")
                self.show_error_message("Xəta", "Qeydiyyat uğursuz oldu. Zəhmət olmasa yenidən cəhd edin.")
        except psycopg2.errors.UniqueViolation as e:
            logging.error(f"❌ [REGISTER] UniqueViolation: {e}, Username={username}")
            print(f"❌ [REGISTER] UniqueViolation: {e}, Username={username}")
            self.show_error_message("Xəta", f"'{username}' adlı istifadəçi artıq mövcuddur.")
        except Exception as e:
            logging.error(f"❌ [REGISTER] Gözlənilməz xəta: {e}, Username={username}, Email={email}")
            print(f"❌ [REGISTER] Gözlənilməz xəta: {e}, Username={username}, Email={email}")
            import traceback
            logging.error(f"❌ [REGISTER] Traceback: {traceback.format_exc()}")
            print(f"❌ [REGISTER] Traceback: {traceback.format_exc()}")
            self.show_error_message("Qeydiyyat Xətası", f"Qeydiyyat zamanı xəta: {e}")

    def logout(self, event=None):
        """Sistemdən çıxış edir, amma cache-i saxlayır."""
        try:
            current_frame = self.container.winfo_children()[0]
            if isinstance(current_frame, MainAppFrame):
                current_frame.stop_background_tasks()
        except IndexError:
            pass

        # Session məlumatlarını saxla ki, background thread-də istifadə edək
        session_id = self.session_id
        login_history_id = self.login_history_id
        current_user = self.current_user
        
        # Session məlumatlarını dərhal təmizlə (UI-ni bloklamamaq üçün)
        self.session_id, self.login_history_id, self.current_user = None, None, None
        
        # Cache-i təmizləmirik! Yalnız sessiya məlumatlarını sıfırlayırıq
        # Əgər "Məni xatırla" seçilibsə, məlumatlar saxlanılır
        logging.info("Sistemdən çıxış edildi, cache saxlanıldı.")
        
        # Database əməliyyatını background thread-də icra et (UI-ni bloklamamaq üçün)
        if current_user and session_id and login_history_id:
            def remove_session_async():
                try:
                    database.remove_user_session(session_id, login_history_id)
                except Exception as e:
                    logging.warning(f"Session silinərkən xəta: {e}")
            
            import threading
            threading.Thread(target=remove_session_async, daemon=True).start()
        
        # Giriş pəncərəsini göstəririk - async şəkildə (UI-ni bloklamamaq üçün)
        def show_login_async():
            try:
                # Pəncərəni əvvəlcə normal rejimə gətir (tam ekrandadırsa)
                current_state = self.state()
                print(f"DEBUG: Logout zamanı pəncərə state: {current_state}")
                
                if current_state == 'zoomed' or current_state == 'maximized':
                    print(f"DEBUG: Pəncərə tam ekrandadır, normal rejimə gətirilir")
                    self.state('normal')
                    # Kiçik gecikmə - pəncərə state dəyişikliyini emal etsin
                    self.update_idletasks()
                
                # Login frame-i göstər - o özü pəncərə ölçüsünü təyin edəcək
                # Burada iki dəfə refresh olmasın deyə, yalnız frame-i göstəririk
                self.show_frame('Login')
            except Exception as e:
                logging.error(f"Logout sonrası Login frame göstərilərkən xəta: {e}")
                import traceback
                print(f"DEBUG: Logout xətası: {traceback.format_exc()}")
        
        # Async şəkildə göstər
        self.after(0, show_login_async)

    def show_update_status(self, text):
        """Update status mətnini göstərir."""
        print(text)  # Console-a da yazdır
        try:
            if self.update_progress_dialog:
                self.update_progress_dialog.update_status(text)
        except Exception as e:
            print(f"Status yeniləmə xətası: {e}")

    def show_update_progress(self, percent):
        """Update progress faizini göstərir."""
        print(f"Yüklənir: {percent:.1f}%")  # Console-a da yazdır
        try:
            if self.update_progress_dialog:
                self.update_progress_dialog.update_progress(percent)
        except Exception as e:
            print(f"Progress yeniləmə xətası: {e}")

    def on_update_error(self):
        """Update xətası zamanı çağırılır."""
        print("Yeniləmə zamanı xəta baş verdi.")
        if self.update_progress_dialog:
            self.update_progress_dialog.close_dialog()
            self.update_progress_dialog = None
            
    def on_update_success(self):
        """Update uğurlu olduqda çağırılır."""
        print("Yeniləmə uğurla tamamlandı.")
        if self.update_progress_dialog:
            self.update_progress_dialog.close_dialog()
            self.update_progress_dialog = None

    def check_for_update(self):
        """Verilənlər bazasından versiya məlumatını yoxlayır və lazım olduqda update mesajı göstərir."""
        logging.info("=== UPDATE YOXLAMASI BAŞLADI ===")
        logging.info(f"Cari versiya: {APP_VERSION}")
        
        # Versiya yoxlamasını 60 saniyə gözləyərək edirik
        self.update_check_count = 0
        self.max_update_check_attempts = 60  # 60 saniyə
        logging.info(f"Maksimum yoxlama cəhdi: {self.max_update_check_attempts} saniyə")
        
        def check_version_with_timeout():
            global _current_conn_string
            logging.debug(f"check_version_with_timeout çağırıldı (cəhd {self.update_check_count + 1})")
            
            if self.update_check_count >= self.max_update_check_attempts:
                # 60 saniyə keçdi, versiya yoxlaması baş vermədi
                logging.warning("Versiya yoxlaması 60 saniyə sonra da baş vermədi")
                return
            
            try:
                logging.debug("Verilənlər bazasından ən son versiyanı alınır...")
                # Verilənlər bazasından ən son versiyanı al
                latest_version = None
                
                # Əvvəlcə PostgreSQL sistem sorğularından yoxla
                try:
                    logging.debug("PostgreSQL system_queries-dən versiya yoxlanılır...")
                    from database.system_queries import get_latest_version
                    # Veritabanı qoşulma parametrlərini təyin et
                    from database.connection import set_connection_params
                    if '_current_conn_string' in globals() and _current_conn_string:
                        set_connection_params(_current_conn_string)
                    latest_version = get_latest_version()
                    logging.info(f"PostgreSQL-dən alınan versiya: {latest_version}")
                    return latest_version
                except Exception as e:
                    logging.warning(f"PostgreSQL system_queries xətası: {e}")
                    try:
                        logging.debug("PostgreSQL user_queries-dən versiya yoxlanılır...")
                        from database.user_queries import get_latest_version
                        # Veritabanı qoşulma parametrlərini təyin et
                        from database.connection import set_connection_params
                        if '_current_conn_string' in globals() and _current_conn_string:
                            set_connection_params(_current_conn_string)
                        latest_version = get_latest_version()
                        logging.info(f"PostgreSQL user_queries-dən alınan versiya: {latest_version}")
                        return latest_version
                    except Exception as e2:
                        logging.warning(f"PostgreSQL user_queries xətası: {e2}")
                        logging.error(f"Bütün versiya yoxlama cəhdləri uğursuz oldu: {e2}")
                        return None
                
                if latest_version:
                    logging.info(f"Ən son versiya tapıldı: {latest_version}")
                    # Versiya müqayisəsi
                    current_version = APP_VERSION
                    
                    # Versiya formatını təhlil et (məsələn: "6.6-final-unified-tkinter")
                    def parse_version(version_str):
                        try:
                            logging.debug(f"Versiya parse edilir: {version_str}")
                            # Versiya sətrini hissələrə böl
                            parts = version_str.split('-')
                            if parts:
                                # İlk hissəni versiya nömrəsi kimi götür
                                version_num = parts[0]
                                # Nöqtə ilə ayrılmış hissələri al
                                version_parts = version_num.split('.')
                                if len(version_parts) >= 2:
                                    major = int(version_parts[0])
                                    minor = int(version_parts[1])
                                    result = (major, minor)
                                    logging.debug(f"Parse edilən versiya: {result}")
                                    return result
                        except Exception as e:
                            logging.warning(f"Versiya parse xətası: {e}")
                            pass
                        return (0, 0)
                    
                    current_parsed = parse_version(current_version)
                    latest_parsed = parse_version(latest_version)
                    
                    logging.info(f"Cari versiya (parse): {current_parsed}")
                    logging.info(f"Ən son versiya (parse): {latest_parsed}")
                    
                    # Versiya müqayisəsi
                    if latest_parsed > current_parsed:
                        # Yeni versiya mövcuddur
                        logging.info("YENİ VERSİYA MÖVCUDDUR!")
                        self.version_info["latest"] = latest_version
                        self.show_update_notification(latest_version)
                    else:
                        # Cari versiya güncəldir
                        logging.info("Cari versiya güncəldir")
                        self.version_info["latest"] = current_version
                    return
                else:
                    logging.debug(f"Versiya tapılmadı, cəhd {self.update_check_count + 1}/{self.max_update_check_attempts}")
                    self.update_check_count += 1
                    # 1 saniyə sonra yenidən cəhd edirik
                    self.after(1000, check_version_with_timeout)
            except Exception as e:
                logging.error(f"Versiya yoxlaması zamanı xəta: {e}", exc_info=True)
                self.update_check_count += 1
                logging.debug(f"Xəta sonrası cəhd {self.update_check_count}/{self.max_update_check_attempts}")
                # 1 saniyə sonra yenidən cəhd edirik
                self.after(1000, check_version_with_timeout)
        
        # İlk cəhdi başladırıq
        check_version_with_timeout()
    
    def show_update_notification(self, latest_version):
        """Update bildirişi göstərir."""
        try:
            logging.info(f"UPDATE BİLDİRİŞİ GÖSTƏRİLİR: {latest_version}")
            from tkinter import messagebox
            result = messagebox.askyesno(
                "Yeni Versiya Mövcuddur", 
                f"Yeni versiya mövcuddur: v{latest_version}\n\n"
                f"Cari versiya: v{APP_VERSION}\n\n"
                "Yeni versiyanı yükləmək istəyirsinizmi?"
            )
            
            if result:
                logging.info("İstifadəçi update-ə razılaşdı")
                # Update prosesini başladırıq
                self.start_update_process(latest_version)
            else:
                logging.info("İstifadəçi update-i ləğv etdi")
                
        except Exception as e:
            logging.error(f"Update bildirişi göstərilərkən xəta: {e}")
    
    def start_update_process(self, latest_version):
        """Update prosesini başladır."""
        try:
            # Progress dialog yaradır və göstərir
            self.update_progress_dialog = UpdateProgressDialog(self)
            
            # UpdaterService istifadə edərək həqiqi update prosesini başladır
            updater = UpdaterService(
                ui_callbacks={
                    'update_status': self.show_update_status,
                    'update_progress': self.show_update_progress,
                    'on_error': self.on_update_error,
                    'on_success': self.on_update_success
                },
                current_version=APP_VERSION
            )
            
            # Update prosesini başladır və latest_version parametrini ötür
            updater.start_update_in_thread(latest_version)
            
        except Exception as e:
            logging.error(f"Update prosesi başladılarkən xəta: {e}")
            messagebox.showerror("Update Xətası", f"Update prosesi başladıla bilmədi: {e}")
            if self.update_progress_dialog:
                self.update_progress_dialog.close_dialog()
                self.update_progress_dialog = None

    # def toggle_debug(self):
    #     if self.debug_mode.get():
    #         logging.getLogger().setLevel(logging.DEBUG)
    #         print("DEBUG rejimi aktivdir")
    #     else:
    #         logging.getLogger().setLevel(logging.INFO)
    #         print("DEBUG rejimi PASSIVdir")

    def show_password_reset_frame(self):
        """Şifrə sıfırlama frame-ini göstərir"""
        self.show_frame('PasswordReset')
    
    def _create_password_reset_frame(self):
        """PasswordReset frame-i yaradır (yumuşaq açılma üçün)"""
        try:
            print(f"DEBUG: _create_password_reset_frame başladı")
            from ui.password_reset_window import PasswordResetFrame
            frame = PasswordResetFrame(self.container, lambda: self.show_frame('Login'))
            logging.info("PasswordResetFrame yaradıldı")
            print(f"DEBUG: PasswordResetFrame yaradıldı")
            
            # Frame-i düzgün pack et
            print(f"DEBUG: Frame pack edilir")
            frame.pack(expand=True, fill="both")
            
            # Frame-i frames dictionary-ə əlavə et
            if not hasattr(self, 'frames'):
                self.frames = {}
            self.frames['PasswordReset'] = frame
            print(f"DEBUG: Frame frames dictionary-ə əlavə edildi")
            
            # Pəncərəni yenilə və göstər
            self.update_idletasks()
            self.update()
            print(f"DEBUG: Pəncərə yeniləndi və göstərildi")
            
            # Pəncərəni fokusla
            self.focus_set()
            print(f"DEBUG: Pəncərə fokuslandı")
            
            print(f"DEBUG: PasswordReset frame yaradılması tamamlandı")
        except Exception as e:
            print(f"DEBUG: PasswordReset frame yaradılarkən xəta: {e}")
            logging.error(f"PasswordReset frame yaradılarkən xəta: {e}")
            import traceback
            print(f"DEBUG: Traceback: {traceback.format_exc()}")
            self.show_error_message("Xəta", f"Şifrə sıfırlama pəncərəsi açıla bilmədi: {e}")

def main():
    """Proqramın əsas giriş nöqtəsi."""
    # Logging konfiqurasiyası yalnız bir dəfə edilir
    setup_logging()
    
    try:
        app = UnifiedApplication()
        app.mainloop()
    except Exception as e:
        logging.critical(f"GÖZLƏNİLMƏYƏN KRİTİK XƏTA: {e}", exc_info=True)
        # Kritik xəta zamanı proqramı gizlətmirik, çünki proqram çöküb
        messagebox.showerror("Kritik Xəta", f"Proqram çökdü. Detallar üçün log faylına baxın.")

if __name__ == "__main__":
    # Install global icon hook before app creates any Toplevels
    try:
        try:
            from utils.icon_helper import install_global_toplevel_icon, apply_window_icon
        except ImportError:
            from src.utils.icon_helper import install_global_toplevel_icon, apply_window_icon
        install_global_toplevel_icon()
    except Exception:
        pass
    main()