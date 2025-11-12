import ttkbootstrap as tb
from ttkbootstrap.constants import *
import tkinter as tk
from tkinter import ttk, messagebox
import logging
from datetime import datetime
from core.real_time_notifier import get_notifier, send_manual_refresh

class RealtimeStatusWindow(tb.Toplevel):
    def __init__(self, parent, current_user):
        super().__init__(parent)
        self.parent = parent
        self.current_user = current_user
        self.title("🔄 Real-Time Status Monitor")
        self.geometry("700x600")
        self.resizable(True, True)
        
        # Pəncərəni mərkəzləşdir
        self.center_window()
        
        # Pəncərəni modal et
        self.transient(parent)
        self.grab_set()
        
        self.create_widgets()
        self.update_status()
        
        # Status yeniləmə timer-i
        self.status_timer = None
        self.start_status_update()
        
    def center_window(self):
        """Pəncərəni mərkəzləşdirir"""
        self.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - (700 // 2)
        y = (self.winfo_screenheight() // 2) - (600 // 2)
        self.geometry(f"700x600+{x}+{y}")
        
    def create_widgets(self):
        """Widget-ləri yaradır"""
        # Başlıq
        header_frame = tb.Frame(self)
        header_frame.pack(fill='x', padx=10, pady=10)
        
        tb.Label(header_frame, text="🔄 Real-Time Status Monitor", font=('Helvetica', 16, 'bold')).pack(side='left')
        
        # Status göstəricisi
        status_frame = tb.LabelFrame(self, text="📊 Status Məlumatları", bootstyle="secondary")
        status_frame.pack(fill='x', padx=10, pady=5)
        
        # Connection status
        self.connection_status_label = tb.Label(status_frame, text="🔴 Bağlantı yoxdur", font=('Helvetica', 12, 'bold'))
        self.connection_status_label.pack(anchor='w', padx=10, pady=5)
        
        # Notifier statusu
        self.notifier_status_label = tb.Label(status_frame, text="Yoxlanılır...", font=('Helvetica', 10))
        self.notifier_status_label.pack(anchor='w', padx=10, pady=2)
        
        # Son yoxlama vaxtı
        self.last_check_label = tb.Label(status_frame, text="Son yoxlama: -", font=('Helvetica', 9))
        self.last_check_label.pack(anchor='w', padx=10, pady=2)
        
        # Son uğurlu yoxlama
        self.last_successful_label = tb.Label(status_frame, text="Son uğurlu yoxlama: -", font=('Helvetica', 9))
        self.last_successful_label.pack(anchor='w', padx=10, pady=2)
        
        # Son dəyişiklik vaxtı
        self.last_change_label = tb.Label(status_frame, text="Son dəyişiklik: -", font=('Helvetica', 9))
        self.last_change_label.pack(anchor='w', padx=10, pady=2)
        
        # Dəyişiklik sayı
        self.change_count_label = tb.Label(status_frame, text="Dəyişiklik sayı: 0", font=('Helvetica', 9))
        self.change_count_label.pack(anchor='w', padx=10, pady=2)
        
        # Xəta sayı
        self.error_count_label = tb.Label(status_frame, text="Xəta sayı: 0", font=('Helvetica', 9))
        self.error_count_label.pack(anchor='w', padx=10, pady=2)
        
        # Yoxlama intervalı
        self.check_interval_label = tb.Label(status_frame, text="Yoxlama intervalı: -", font=('Helvetica', 9))
        self.check_interval_label.pack(anchor='w', padx=10, pady=2)
        
        # WebSocket status
        self.websocket_label = tb.Label(status_frame, text="WebSocket: -", font=('Helvetica', 9))
        self.websocket_label.pack(anchor='w', padx=10, pady=2)
        
        # Test əmrləri
        manual_frame = tb.LabelFrame(self, text="🧪 Test Əmrləri", bootstyle="secondary")
        manual_frame.pack(fill='x', padx=10, pady=5)
        
        # Test signal düyməsi
        test_signal_btn = tb.Button(
            manual_frame, 
            text="📡 Test Signal Göndər", 
            command=self.send_test_signal,
            bootstyle="info"
        )
        test_signal_btn.pack(fill='x', padx=10, pady=5)
        
        # Force refresh düyməsi
        force_refresh_btn = tb.Button(
            manual_frame, 
            text="🔄 Force Refresh", 
            command=self.force_refresh,
            bootstyle="warning"
        )
        force_refresh_btn.pack(fill='x', padx=10, pady=5)
        
        # Real-time log
        log_frame = tb.LabelFrame(self, text="📝 Real-Time Log", bootstyle="secondary")
        log_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        # Log text widget
        self.log_text = tk.Text(
            log_frame,
            font=('Consolas', 9),
            wrap='word',
            height=15
        )
        self.log_text.pack(side='left', fill='both', expand=True, padx=5, pady=5)
        
        # Scrollbar
        log_scrollbar = ttk.Scrollbar(log_frame, orient='vertical', command=self.log_text.yview)
        log_scrollbar.pack(side='right', fill='y')
        self.log_text.config(yscrollcommand=log_scrollbar.set)
        
        # Alt düymələr
        bottom_frame = tb.Frame(self)
        bottom_frame.pack(fill='x', padx=10, pady=10)
        
        # Log təmizlə
        clear_log_btn = tb.Button(bottom_frame, text="🗑️ Log Təmizlə", command=self.clear_log, bootstyle="secondary")
        clear_log_btn.pack(side='left')
        
        tb.Button(bottom_frame, text="❌ Bağla", command=self.destroy, bootstyle="danger").pack(side='right')
        
    def update_status(self):
        """Status məlumatlarını yeniləyir"""
        try:
            notifier = get_notifier()
            if notifier:
                status = notifier.get_status()
                
                # Connection status
                connection_status = status.get('connection_status', 'unknown')
                if connection_status == 'websocket_connected':
                    self.connection_status_label.config(text="🟢 WebSocket Bağlı", foreground='green')
                elif connection_status == 'polling_active':
                    self.connection_status_label.config(text="🟡 Polling Aktiv", foreground='orange')
                elif connection_status == 'websocket_error':
                    self.connection_status_label.config(text="🔴 WebSocket Xətası", foreground='red')
                elif connection_status == 'websocket_closed':
                    self.connection_status_label.config(text="🟡 WebSocket Bağlandı", foreground='orange')
                elif connection_status == 'stopped':
                    self.connection_status_label.config(text="🔴 Dayanıb", foreground='red')
                else:
                    self.connection_status_label.config(text="🔴 Bağlantı yoxdur", foreground='red')
                
                # Notifier statusu
                status_text = "🟢 Aktiv" if status['is_running'] else "🔴 Dayanıb"
                self.notifier_status_label.config(text=f"Notifier Status: {status_text}")
                
                # Son yoxlama vaxtı
                if status['last_check']:
                    try:
                        last_check = datetime.fromisoformat(status['last_check'].replace('Z', '+00:00'))
                        self.last_check_label.config(text=f"Son yoxlama: {last_check.strftime('%H:%M:%S')}")
                    except:
                        self.last_check_label.config(text=f"Son yoxlama: {status['last_check']}")
                
                # Son uğurlu yoxlama
                if status.get('last_successful_check'):
                    try:
                        last_successful = status['last_successful_check']
                        self.last_successful_label.config(text=f"Son uğurlu yoxlama: {last_successful.strftime('%H:%M:%S')}")
                    except:
                        self.last_successful_label.config(text="Son uğurlu yoxlama: -")
                
                # Son dəyişiklik vaxtı
                if status['last_change_time']:
                    last_change = status['last_change_time']
                    self.last_change_label.config(text=f"Son dəyişiklik: {last_change.strftime('%H:%M:%S')}")
                
                # Dəyişiklik sayı
                self.change_count_label.config(text=f"Dəyişiklik sayı: {status['change_count']}")
                
                # Xəta sayı
                error_count = status.get('error_count', 0)
                self.error_count_label.config(text=f"Xəta sayı: {error_count}")
                
                # Yoxlama intervalı
                self.check_interval_label.config(text=f"Yoxlama intervalı: {status['check_interval']} saniyə")
                
                # WebSocket status
                websocket_connected = status.get('websocket_connected', False)
                websocket_text = "🟢 Bağlı" if websocket_connected else "🔴 Bağlı deyil"
                self.websocket_label.config(text=f"WebSocket: {websocket_text}")
                
            else:
                self.connection_status_label.config(text="🔴 Notifier tapılmadı", foreground='red')
                self.notifier_status_label.config(text="🔴 Notifier tapılmadı")
                self.last_check_label.config(text="Son yoxlama: -")
                self.last_successful_label.config(text="Son uğurlu yoxlama: -")
                self.last_change_label.config(text="Son dəyişiklik: -")
                self.change_count_label.config(text="Dəyişiklik sayı: -")
                self.error_count_label.config(text="Xəta sayı: -")
                self.check_interval_label.config(text="Yoxlama intervalı: -")
                self.websocket_label.config(text="WebSocket: -")
                
        except Exception as e:
            logging.error(f"Status yenilənərkən xəta: {e}")
            self.connection_status_label.config(text="❌ Xəta baş verdi", foreground='red')
            
    def start_status_update(self):
        """Status yeniləmə timer-ini başladır"""
        self.update_status()
        self.status_timer = self.after(500, self.start_status_update)  # 0.5 saniyədə bir yenilə
        
    def stop_status_update(self):
        """Status yeniləmə timer-ini dayandırır"""
        if self.status_timer:
            self.after_cancel(self.status_timer)
            self.status_timer = None
            
    def send_test_signal(self):
        """Test signal göndərir"""
        try:
            send_manual_refresh('test_signal', {
                'user': self.current_user.get('name'),
                'timestamp': datetime.now().isoformat(),
                'source': 'status_window',
                'message': 'Bu test signalidir'
            })
            
            # Log-a əlavə et
            self.add_log_entry("🧪 Test signal göndərildi")
            
            messagebox.showinfo("Uğurlu", "Test signal göndərildi!")
            
        except Exception as e:
            logging.error(f"Test signal xətası: {e}")
            self.add_log_entry(f"❌ Test signal xətası: {e}")
            messagebox.showerror("Xəta", f"Test signal xətası: {e}")
            
    def force_refresh(self):
        """Force refresh tələb edir"""
        try:
            from core.real_time_notifier import force_immediate_refresh
            force_immediate_refresh()
            
            # Log-a əlavə et
            self.add_log_entry("🔄 Force refresh tələb edildi")
            
            messagebox.showinfo("Uğurlu", "Force refresh tələb edildi!")
            
        except Exception as e:
            logging.error(f"Force refresh xətası: {e}")
            self.add_log_entry(f"❌ Force refresh xətası: {e}")
            messagebox.showerror("Xəta", f"Force refresh xətası: {e}")
            
    def add_log_entry(self, message):
        """Log-a yeni giriş əlavə edir"""
        timestamp = datetime.now().strftime('%H:%M:%S')
        full_message = f"[{timestamp}] {message}\n"
        
        self.log_text.insert(tk.END, full_message)
        self.log_text.see(tk.END)  # Avtomatik scroll
        
        # Maksimum 1000 sətri saxla
        lines = self.log_text.get('1.0', tk.END).split('\n')
        if len(lines) > 1000:
            self.log_text.delete('1.0', f'{len(lines)-1000}.0')
            
    def clear_log(self):
        """Log-u təmizləyir"""
        self.log_text.delete('1.0', tk.END)
        self.add_log_entry("🗑️ Log təmizləndi")
            
    def destroy(self):
        """Pəncərəni bağlayır"""
        self.stop_status_update()
        super().destroy()