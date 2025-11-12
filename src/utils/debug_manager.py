#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Debug Manager - Debug mesajlarını kategorilərə bölünmüş şəkildə göstərir və idarə edir
"""

import tkinter as tk
from tkinter import ttk, scrolledtext
import threading
from datetime import datetime
from collections import deque

class DebugManager:
    """Debug mesajlarını kategorilərə görə yönətmək"""
    
    def __init__(self):
        self.enabled_categories = {
            'takvim': True,  # Varsayılan olaraq açık
            'animasiya': True,
            'database': True,
            'ui': True,
            'vacation': True,
            'employee': True,
            'signal': True,
            'performance': True,
            'umumi': True  # Hepsi açık
        }
        
        self.window = None
        self.text_widget = None
        self.checkboxes = {}
        self.message_queue = deque(maxlen=1000)  # Son 1000 mesaj (azaldıldı)
        self.lock = threading.Lock()
        self.auto_scroll = True
        self.is_logging = False  # Sonsuz loop'u önlemek üçün flag
        self.last_update_time = 0  # Son yeniləmə zamanı
        self.update_throttle_ms = 500  # Minimum 500ms interval (artırıldı)
        self.pending_messages = []  # Gözləyən mesajlar
        self.update_scheduled = False  # Yeniləmə planlaşdırılıb
        self.console_output_enabled = False  # Konsola print default: OFF
        self.settings_file_path = self._default_settings_path()
        self._after_job_id = None  # Tk after job id to throttle UI updates
        self._render_index = 0  # Last rendered message index in queue snapshot
        self._load_settings_safely()

    def _default_settings_path(self):
        try:
            import os
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            return os.path.join(base_dir, 'debug_settings.json')
        except Exception:
            return 'debug_settings.json'

    def _load_settings_safely(self):
        try:
            import json, os
            if os.path.exists(self.settings_file_path):
                with open(self.settings_file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                if isinstance(data.get('console_output_enabled'), bool):
                    self.console_output_enabled = data['console_output_enabled']
                categories = data.get('enabled_categories')
                if isinstance(categories, dict):
                    for k, v in categories.items():
                        if k in self.enabled_categories and isinstance(v, bool):
                            self.enabled_categories[k] = v
        except Exception:
            pass
        
        # Logging handler əlavə et
        self._setup_logging_handler()

    def _save_settings_safely(self):
        try:
            import json
            payload = {
                'console_output_enabled': self.console_output_enabled,
                'enabled_categories': self.enabled_categories,
            }
            with open(self.settings_file_path, 'w', encoding='utf-8') as f:
                json.dump(payload, f, ensure_ascii=False, indent=2)
        except Exception:
            pass
    
    def _save_settings(self):
        """Yadda Saxla düyməsi üçün"""
        self._save_settings_safely()
        if self.text_widget:
            # Mesaj göstər
            self.text_widget.insert("end", "✅ Debug ayarları yadda saxlanıldı\n")
            self.text_widget.see("end")
    
    def _setup_logging_handler(self):
        """Logging handler əlavə et - log faylına yazmaq üçün"""
        try:
            import os
            import sys
            import logging
            
            # Log helper istifadə et
            try:
                from utils.log_helper import get_log_file_path, archive_existing_log
            except ImportError:
                from src.utils.log_helper import get_log_file_path, archive_existing_log
            
            # Mövcud log faylını arxiv et
            archive_existing_log('debug_console.log')
            
            # Yeni log faylının yolunu al (timestamp ilə)
            self.log_file_path = get_log_file_path('debug_console.log', with_timestamp=True)
            
            # File handler yarad
            self.log_file_handler = logging.FileHandler(self.log_file_path, encoding='utf-8', mode='w')
            self.log_file_handler.setLevel(logging.DEBUG)
            formatter = logging.Formatter('%(asctime)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
            self.log_file_handler.setFormatter(formatter)
            
            # Logger-ə əlavə et
            logger = logging.getLogger('debug_console')
            logger.setLevel(logging.DEBUG)
            logger.addHandler(self.log_file_handler)
            self.logger = logger
            
            # İlk mesajı yaz
            logger.info("=" * 80)
            logger.info("DEBUG LOG FAYLI BAŞLADI")
            logger.info(f"Log faylı yolu: {self.log_file_path}")
            logger.info("=" * 80)
        except Exception as e:
            # Xəta olsa belə davam et
            self.log_file_path = None
            self.logger = None
            pass
        try:
            import logging
            
            class DebugLoggingHandler(logging.Handler):
                def __init__(self, debug_manager):
                    super().__init__()
                    self.debug_manager = debug_manager
                
                def emit(self, record):
                    try:
                        if getattr(self.debug_manager, 'is_logging', False):
                            return  # Sonsuz loopdan qaç
                        
                        msg = self.format(record)
                        level = record.levelname
                        name = record.name.lower()
                        
                        # Kateqoriya təyini
                        if 'database' in msg.lower() or 'connection' in msg.lower() or 'offline database' in msg.lower():
                            cat, emoji = 'database', '🗄️'
                        elif 'ui' in msg.lower() or 'frame' in msg.lower() or 'widget' in msg.lower() or 'login' in msg.lower():
                            cat, emoji = 'ui', '🖥️'
                        elif 'vacation' in msg.lower() or 'məzuniyyət' in msg.lower():
                            cat, emoji = 'vacation', '🏖️'
                        elif 'employee' in msg.lower() or 'işçi' in msg.lower():
                            cat, emoji = 'employee', '👤'
                        elif 'performance' in msg.lower() or 'yavaş' in msg.lower():
                            cat, emoji = 'performance', '⚡'
                        elif 'signal' in msg.lower() or 'notification' in msg.lower():
                            cat, emoji = 'signal', '📡'
                        elif 'animation' in msg.lower() or 'gif' in msg.lower() or 'loading' in msg.lower():
                            cat, emoji = 'animasiya', '🎬'
                        elif 'calendar' in msg.lower() or 'takvim' in msg.lower():
                            cat, emoji = 'takvim', '📅'
                        else:
                            cat, emoji = 'umumi', '📝'
                        
                        # Emoji level-ə görə
                        if level == 'DEBUG':
                            emoji = '🔍'
                        elif level == 'INFO':
                            emoji = 'ℹ️'
                        elif level == 'WARNING':
                            emoji = '⚠️'
                        elif level == 'ERROR':
                            emoji = '❌'
                        
                        # Debug manager-a göndər
                        self.debug_manager.is_logging = True
                        try:
                            self.debug_manager.log(cat, msg, emoji)
                        finally:
                            self.debug_manager.is_logging = False
                            
                    except Exception:
                        pass
            
            # Root logger-a handler əlavə et
            root_logger = logging.getLogger()
            
            # Mövcud handler-ləri sil (konsol çıxışını dayandır)
            for handler in list(root_logger.handlers):
                root_logger.removeHandler(handler)
            
            # Debug handler əlavə et
            debug_handler = DebugLoggingHandler(self)
            debug_handler.setFormatter(logging.Formatter('%(levelname)s:%(name)s:%(message)s'))
            root_logger.addHandler(debug_handler)
            root_logger.setLevel(logging.DEBUG)
            
            # Üçüncü tərəf logger-ları sakitləşdir
            logging.getLogger('urllib3').setLevel(logging.WARNING)
            logging.getLogger('PIL').setLevel(logging.WARNING)
            
        except Exception:
            pass

    def set_console_output(self, enabled: bool):
        self.console_output_enabled = bool(enabled)
        self._save_settings_safely()

    def enable_category(self, category: str):
        if category in self.enabled_categories:
            self.enabled_categories[category] = True
            self._save_settings_safely()
            self._refresh_display()

    def disable_category(self, category: str):
        if category in self.enabled_categories:
            self.enabled_categories[category] = False
            self._save_settings_safely()
            self._refresh_display()

    def set_enabled_categories(self, categories_on=None, categories_off=None):
        changed = False
        if isinstance(categories_on, (list, tuple, set)):
            for c in categories_on:
                if c in self.enabled_categories and not self.enabled_categories[c]:
                    self.enabled_categories[c] = True
                    changed = True
        if isinstance(categories_off, (list, tuple, set)):
            for c in categories_off:
                if c in self.enabled_categories and self.enabled_categories[c]:
                    self.enabled_categories[c] = False
                    changed = True
        if changed:
            self._save_settings_safely()
            self._refresh_display()
        
    def create_debug_window(self, master=None):
        """Debug pəncərəsi yaradır - UI-ni bloklamamaq üçün optimizasiya edilmiş"""
        # İlk açılışta bir mesaj logla
        self.log('umumi', 'Debug yöneticisi başlatıldı', '🚀')
        
        if self.window is not None:
            try:
                self.window.destroy()
            except:
                pass
        
        self.window = tk.Toplevel(master)
        self.window.title("🔍 Debug Yönəticisi")
        self.window.geometry("800x600")
        self.window.protocol("WM_DELETE_WINDOW", self._hide_window)
        
        # Üst panel - Kategori kontrolü
        control_frame = ttk.Frame(self.window, padding="10")
        control_frame.pack(fill="x", padx=5, pady=5)
        
        ttk.Label(control_frame, text="Debug Kateqoriyaları:", font=("Arial", 10, "bold")).pack(side="left", padx=5)
        
        # Checkbox'lar
        checkbox_frame = ttk.Frame(control_frame)
        checkbox_frame.pack(side="left", fill="x", expand=True)
        
        self.checkboxes = {}
        row, col = 0, 0
        for category in sorted(self.enabled_categories.keys()):
            var = tk.BooleanVar(value=self.enabled_categories[category])
            cb = ttk.Checkbutton(
                checkbox_frame, 
                text=category.upper(), 
                variable=var,
                command=lambda c=category, v=var: self._toggle_category(c, v.get())
            )
            cb.grid(row=row, column=col, sticky="w", padx=5)
            self.checkboxes[category] = var
            
            col += 1
            if col > 4:
                col = 0
                row += 1
        
        # Təmizlə və Yadda Saxla butonları
        button_frame = ttk.Frame(control_frame)
        button_frame.pack(side="right", padx=5)
        
        ttk.Button(button_frame, text="Təmizlə", command=self._clear_logs).pack(side="left", padx=2)
        ttk.Button(button_frame, text="Yadda Saxla", command=self._save_settings).pack(side="left", padx=2)
        
        # Auto-scroll checkbox
        auto_scroll_var = tk.BooleanVar(value=self.auto_scroll)
        ttk.Checkbutton(
            control_frame,
            text="Avtomatik Scroll",
            variable=auto_scroll_var,
            command=lambda: setattr(self, 'auto_scroll', auto_scroll_var.get())
        ).pack(side="right", padx=5)
        
        # Debug mesajları texxt sahəsi
        text_frame = ttk.Frame(self.window)
        text_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        self.text_widget = scrolledtext.ScrolledText(
            text_frame,
            wrap="word",
            font=("Consolas", 9),
            bg="#1e1e1e",
            fg="#d4d4d4",
            insertbackground="#d4d4d4"
        )
        self.text_widget.pack(fill="both", expand=True)
        
        # Başlıq - sadəcə minimal məlumat
        self.text_widget.insert("end", "🔍 DEBUG YÖNƏTİCİSİ\n")
        self.text_widget.insert("end", "=" * 80 + "\n\n")
        self.text_widget.insert("end", "Debug penceresi açıldı. Mesajlar yüklənir...\n\n")
        self._apply_tags()
        
        # UI-ni bloklamamaq üçün - köhnə mesajları async şəkildə yüklə
        # Pəncərə tam açılsın və render olsun, sonra mesajları yüklə
        if self.window:
            # İlk öncə pəncərəni göstər, sonra mesajları yüklə
            self.window.update_idletasks()  # Pəncərəni render et
            self.window.after(200, self._refresh_display)  # 200ms sonra mesajları yüklə
        
    def _toggle_category(self, category, enabled):
        """Kategori açar/bağlar"""
        with self.lock:
            self.enabled_categories[category] = enabled
            # Ayarları avtomatik yadda saxla
            self._save_settings_safely()
            # Köhnə mesajları güncelle - async şəkildə (UI-ni bloklamamaq üçün)
            if self.text_widget and self.text_widget.winfo_exists():
                self.text_widget.after(0, self._refresh_display)
    
    def _clear_logs(self):
        """Log'ları təmizlə"""
        if self.text_widget:
            self.text_widget.delete("1.0", "end")
            self.text_widget.insert("end", "🔍 DEBUG YÖNƏTİCİSİ\n")
            self.text_widget.insert("end", "=" * 80 + "\n\n")
    
    def _hide_window(self):
        """Pəncərəni gizlət (lütfen destroy etme)"""
        if self.window:
            self.window.withdraw()
    
    def show_window(self, master=None):
        """Pəncərəni göstər - async şəkildə (UI-ni bloklamamaq üçün)"""
        def _async_show():
            try:
                if self.window:
                    self.window.deiconify()
                    self.window.lift()
                    self.window.focus_force()
                else:
                    self.create_debug_window(master)
            except Exception as e:
                # Xətaları udur ki, proqram dayanmasın
                pass
        
        # Async şəkildə göstər
        if master:
            try:
                master.after(0, _async_show)
            except Exception:
                _async_show()
        else:
            _async_show()
    
    def log(self, category, message, emoji="📝"):
        """
        Debug mesajı əlavə et - Non-blocking versiya və log faylına yaz
        """
        try:
            # Mesajı sadəcə queue-ya əlavə et, UI yeniləməni gecikdir
            timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
            log_entry = {
                'timestamp': timestamp,
                'category': category,
                'emoji': emoji,
                'message': message
            }
            
            with self.lock:
                self.message_queue.append(log_entry)
            
            # Log faylına yaz (EXE-də görmək üçün)
            if hasattr(self, 'logger') and self.logger:
                try:
                    full_timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    log_message = f"[{full_timestamp}] [{category.upper()}] {emoji} {message}"
                    self.logger.debug(log_message)
                    
                    # Verilənlər bazasına da yaz
                    try:
                        try:
                            from utils.log_helper import log_to_database_async
                        except ImportError:
                            from src.utils.log_helper import log_to_database_async
                        
                        log_file_name = getattr(self, 'log_file_path', None)
                        if log_file_name:
                            log_file_name = os.path.basename(log_file_name)
                        log_to_database_async('debug_console', log_message, log_file_name)
                    except Exception:
                        pass
                except Exception:
                    pass
            
            # UI yeniləməni gecikdir (non-blocking)
            if self.text_widget and self.enabled_categories.get(category, False):
                self._schedule_update()
                
        except Exception:
            # Xətaları udur ki, proqram dayanmasın
            pass
    
    def _schedule_update(self):
        """Schedule a throttled UI update on Tk main thread using after()."""
        if not self.text_widget or not self.text_widget.winfo_exists():
            return
        # If an after job is already scheduled, do nothing (throttle)
        if self._after_job_id is not None:
            return
        # Schedule a single-shot flush soon
        delay_ms = 100  # small delay to coalesce bursts
        def _cb():
            self._after_job_id = None
            try:
                self._batch_update_mainthread()
            except Exception:
                pass
        try:
            self._after_job_id = self.text_widget.after(delay_ms, _cb)
        except Exception:
            self._after_job_id = None
    
    def _batch_update_mainthread(self):
        """Append only new messages to the text widget. Must run on Tk thread."""
        if not self.text_widget or not self.text_widget.winfo_exists():
            return
        try:
            # Take a snapshot of the queue
            with self.lock:
                snapshot = list(self.message_queue)
            total = len(snapshot)
            # If messages were dropped due to maxlen, clamp render index
            if self._render_index > total:
                self._render_index = total
            start = max(0, self._render_index)
            # Limit how many we render per batch to avoid UI stalls
            batch = snapshot[start:][:200]
            if not batch:
                return
            for entry in batch:
                if self.enabled_categories.get(entry['category'], False):
                    self._add_simple_message(entry)
            self._render_index = start + len(batch)
            if self.auto_scroll:
                self.text_widget.see("end")
        except Exception:
            pass
    
    def _add_simple_message(self, entry):
        """Sadə mesaj əlavə et"""
        try:
            # Sadə format
            message_text = f"[{entry['timestamp']}] {entry['emoji']} {entry['message']}\n"
            self.text_widget.insert("end", message_text)
        except Exception:
            pass
    
    def _refresh_display(self):
        """Tüm mesajları yenidən göster (sadece enabled kategoriler) - Non-blocking versiya"""
        if not self.text_widget:
            return
        
        # UI-ni bloklamamaq üçün async şəkildə yenilə
        def _async_refresh():
            try:
                if not self.text_widget or not self.text_widget.winfo_exists():
                    return
                
                # Təmizlə
                self.text_widget.delete("1.0", "end")
                self.text_widget.insert("end", "🔍 DEBUG YÖNƏTİCİSİ\n")
                self.text_widget.insert("end", "=" * 80 + "\n\n")
                
                # Enabled kategorilerin mesajlarını göster - batch şəkildə
                with self.lock:
                    snapshot = list(self.message_queue)
                
                # Mesajları batch-lərə böl və tədricən göstər - UI-ni bloklamamaq üçün
                batch_size = 30  # Batch ölçüsünü daha da azaltdım (50-dən 30-a)
                total = len(snapshot)
                
                # Çox mesaj varsa, yalnız son mesajları göstər (ilk 300 mesajı atla - daha az yüklə)
                max_messages_to_show = 300  # 500-dən 300-ə azaldıldı
                start_from = max(0, total - max_messages_to_show) if total > max_messages_to_show else 0
                snapshot = snapshot[start_from:]
                total = len(snapshot)
                
                # Əgər çox mesaj varsa, istifadəçiyə bildir
                if start_from > 0:
                    self.text_widget.insert("end", f"⚠️ {start_from} köhnə mesaj göstərilmir (yalnız son {max_messages_to_show} mesaj göstərilir)\n\n")
                
                def _render_batch(start_idx):
                    if not self.text_widget or not self.text_widget.winfo_exists():
                        return
                    
                    try:
                        end_idx = min(start_idx + batch_size, total)
                        # Batch mesajlarını topla
                        batch_messages = []
                        for i in range(start_idx, end_idx):
                            entry = snapshot[i]
                            if self.enabled_categories.get(entry['category'], False):
                                message_text = f"[{entry['timestamp']}] {entry['emoji']} {entry['message']}\n"
                                batch_messages.append(message_text)
                        
                        # Bütün batch mesajlarını bir dəfədə insert et (daha sürətli)
                        if batch_messages:
                            self.text_widget.insert("end", "".join(batch_messages))
                        
                        # Növbəti batch-i planlaşdır - closure problemi üçün end_idx-i capture et
                        if end_idx < total:
                            if self.text_widget and self.text_widget.winfo_exists():
                                # Closure problemi üçün end_idx-i lambda parametri kimi ötür
                                # Delay-i artırdım (50ms-dən 100ms-yə) ki, UI daha responsive olsun
                                self.text_widget.after(100, lambda idx=end_idx: _render_batch(idx))
                        else:
                            # Bütün mesajlar render edildi
                            if self.auto_scroll:
                                self.text_widget.see("end")
                    except Exception as e:
                        # Xətaları udur ki, proqram dayanmasın
                        pass
                
                # İlk batch-i başlat - async şəkildə
                if total > 0:
                    if self.text_widget and self.text_widget.winfo_exists():
                        self.text_widget.after(0, lambda: _render_batch(0))
                else:
                    if self.auto_scroll:
                        self.text_widget.see("end")
            except Exception as e:
                # Xətaları udur ki, proqram dayanmasın
                pass
        
        # Async refresh-i planlaşdır
        if self.text_widget and self.text_widget.winfo_exists():
            self.text_widget.after(0, _async_refresh)
    
    def _apply_tags(self):
        """Tag'ları tətbiq et"""
        self.text_widget.tag_config("timestamp", foreground="#808080")
    
    def is_enabled(self, category):
        """Kategori enabled mi?"""
        return self.enabled_categories.get(category, False)

# Global instance
_debug_manager = None

def get_debug_manager():
    """Global debug manager instance"""
    global _debug_manager
    if _debug_manager is None:
        _debug_manager = DebugManager()
    return _debug_manager

def debug_log(category, message, emoji="📝"):
    """Debug mesajı logla"""
    get_debug_manager().log(category, message, emoji)

def show_debug_window(master=None):
    """Debug pəncərəsini göstər"""
    get_debug_manager().show_window(master)

def is_category_enabled(category):
    """Kategori enabled mi?"""
    return get_debug_manager().is_enabled(category)

def setup_debug_print_intercept():
    """Print funksiyasını intercept et və debug manager-a göndər"""
    import builtins
    if hasattr(builtins, '_original_print_'):
        return builtins._original_print_  # Zaten intercept edilmiş
    
    original_print = builtins.print
    builtins._original_print_ = original_print
    
    def debug_print(*args, **kwargs):
        # Konsola çıxışı idarə et
        manager = get_debug_manager()
        if manager is None or manager.console_output_enabled:
            try:
                original_print(*args, **kwargs)
            except UnicodeEncodeError:
                pass
        
        # Log faylına da yaz (EXE-də görmək üçün)
        if manager and hasattr(manager, 'logger') and manager.logger:
            try:
                message = ' '.join(str(arg) for arg in args)
                timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                manager.logger.debug(f"[{timestamp}] {message}")
            except Exception:
                pass
        
        # Debug manager var mı ve aktif mi kontrol et
        manager = _debug_manager if manager is None else manager
        if manager is None or manager.is_logging:
            return  # Sonsuz loop'u önle
        
        # Mesajı hızlıca oluştur
        try:
            message = ' '.join(str(arg) for arg in args)
        except:
            return  # Hata durumunda devam etme
        
        # Debug test mesajı əlavə et
        if not hasattr(debug_print, '_test_sent'):
            debug_print._test_sent = True
            try:
                debug_log('umumi', 'Print intercept aktivləşdirildi', '🔧')
            except:
                pass
        
        # Kategori təyin et (basit ve hızlı)
        category = None
        emoji = '📝'
        
        # Hızlı kategori tespiti - sadece birkaç karakter kontrol et
        msg_lower = message.lower()
        
        if '🟢' in message or '🎬' in message or 'loading' in msg_lower or 'gif' in msg_lower:
            category = 'animasiya'
            emoji = '🎬'
        elif 'məzuniyyət' in message or 'kvadrat' in message or '🎯' in message or 'takvim' in msg_lower:
            category = 'takvim'
            emoji = '📅'
        elif 'veritabanı' in msg_lower or 'connection' in msg_lower or 'database' in msg_lower or 'offline database' in msg_lower:
            category = 'database'
            emoji = '🗄️'
        elif any(word in message for word in ['Panel', 'Widget', 'Frame', 'UI', 'Login', 'window', 'pəncərə']):
            category = 'ui'
            emoji = '🖥️'
        elif 'məzuniyyət' in message or 'vacation' in msg_lower:
            category = 'vacation'
            emoji = '🏖️'
        elif 'işçi' in message or 'employee' in msg_lower:
            category = 'employee'
            emoji = '👤'
        elif 'debug' in msg_lower or 'DEBUG' in message:
            category = 'umumi'
            emoji = '🔍'
        elif 'warning' in msg_lower or 'WARNING' in message:
            category = 'umumi'
            emoji = '⚠️'
        elif 'info' in msg_lower or 'INFO' in message:
            category = 'umumi'
            emoji = 'ℹ️'
        else:
            category = 'umumi'
            emoji = '📝'
        
        # HER ZAMAN logla (gösterilmesi kategoriye bağlı)
        manager.is_logging = True
        try:
            manager.log(category, message, emoji)
        finally:
            manager.is_logging = False
    
    # Print'i değiştir
    builtins.print = debug_print
    return original_print

def configure_debug(categories_on=None, categories_off=None, console_output=None):
    """Runtime konfiqurasiya: kateqoriyalar və konsol çıxışı."""
    mgr = get_debug_manager()
    if console_output is not None:
        mgr.set_console_output(bool(console_output))
    mgr.set_enabled_categories(categories_on, categories_off)

