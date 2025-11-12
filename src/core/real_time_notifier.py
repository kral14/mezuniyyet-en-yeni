# real_time_notifier.py - Real-time notification sistemi

import threading
import time
import logging
import requests
from datetime import datetime
import json
import websocket
import ssl
import sys
import os

# Debug sistemi əlavə et
current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, current_dir)
# Realtime debug sistemi - şərti import
try:
    try:
        from utils.realtime_debug import log_signal_sent, log_signal_received, log_network_operation, log_performance
    except ImportError:
        from src.utils.realtime_debug import log_signal_sent, log_signal_received, log_network_operation, log_performance
except ImportError:
    # Əgər debug modulu tapılmazsa, boş funksiyalar yaradırıq
    def log_signal_sent(*args, **kwargs): pass
    def log_signal_received(*args, **kwargs): pass
    def log_network_operation(*args, **kwargs): pass
    def log_performance(*args, **kwargs): pass

class RealTimeNotifier:
    def __init__(self, tenant_id, server_url="https://mezuniyyet-serverim.onrender.com"):
        self.tenant_id = tenant_id
        self.server_url = server_url.rstrip('/')
        self.is_running = False
        self.thread = None
        self.callback = None
        self.last_check = None
        self.check_interval = 1.0  # 1 saniyədə bir yoxla (daha az tez)
        self.last_change_time = None
        self.change_count = 0
        self.force_refresh = False  # Məcburi refresh üçün
        
        # WebSocket dəstəyi
        self.websocket = None
        self.use_websocket = False
        self.ws_thread = None
        
        # Real-time status
        self.connection_status = "disconnected"
        self.last_successful_check = None
        self.error_count = 0
        self.max_errors = 10
        
    def start(self, callback=None):
        """Real-time notification sistemini başladır"""
        if self.is_running:
            return
            
        self.callback = callback
        self.is_running = True
        self.connection_status = "connecting"
        
        # WebSocket cəhd et
        if self._try_websocket():
            self.use_websocket = True
            self.connection_status = "websocket_connected"
            logging.info("🟢 WebSocket realtime sistemi başladıldı")
        else:
            # Fallback polling - çox tez yoxlama
            self.thread = threading.Thread(target=self._monitor_loop, daemon=True)
            self.thread.start()
            self.connection_status = "polling_active"
            logging.info("🟡 Polling realtime sistemi başladıldı (çox tez yoxlama)")
        
    def _try_websocket(self):
        """WebSocket qoşulmasını cəhd edir"""
        try:
            # WebSocket URL-ni hazırla
            ws_url = self.server_url.replace('https://', 'wss://').replace('http://', 'ws://')
            ws_url = f"{ws_url}/ws/tenants/{self.tenant_id}"
            
            # WebSocket qoşulması
            self.websocket = websocket.WebSocketApp(
                ws_url,
                on_message=self._on_websocket_message,
                on_error=self._on_websocket_error,
                on_close=self._on_websocket_close,
                on_open=self._on_websocket_open
            )
            
            # WebSocket thread-i başlad
            self.ws_thread = threading.Thread(target=self.websocket.run_forever, 
                                            kwargs={'sslopt': {"cert_reqs": ssl.CERT_NONE}}, 
                                            daemon=True)
            self.ws_thread.start()
            
            # Qoşulma üçün 1 saniyə gözlə (daha qısa)
            time.sleep(1)
            
            # WebSocket statusunu yoxla
            if self.websocket.sock and self.websocket.sock.connected:
                logging.info("🟢 WebSocket qoşulması uğurlu oldu")
                return True
            else:
                logging.warning("🔴 WebSocket qoşulması uğursuz oldu, polling-ə keçilir")
                return False
            
        except Exception as e:
            logging.error(f"🔴 WebSocket xətası: {e} -+-+- {getattr(e, 'headers', None)} -+-+- {getattr(e, 'body', None)}")
            return False
    
    def _on_websocket_message(self, ws, message):
        """WebSocket mesajı alındıqda"""
        try:
            data = json.loads(message)
            change_type = data.get('change_type', 'general')
            details = data.get('details', {})
            
            self.change_count += 1
            self.last_successful_check = datetime.now()
            self.error_count = 0  # Uğurlu əməliyyatda xəta sayını sıfırla
            
            logging.info(f"🟢 WebSocket dəyişiklik alındı (#{self.change_count}): {change_type}")
            self._trigger_refresh(change_type, details)
            
        except Exception as e:
            logging.error(f"WebSocket mesaj işləmə xətası: {e}")
    
    def _on_websocket_error(self, ws, error):
        """WebSocket xətası"""
        logging.error(f"🔴 WebSocket xətası: {error}")
        self.use_websocket = False
        self.connection_status = "websocket_error"
        self.error_count += 1
        
        # Fallback polling-ə keç
        self._start_polling_fallback()
    
    def _on_websocket_close(self, ws, close_status_code, close_msg):
        """WebSocket bağlandı"""
        logging.info("🟡 WebSocket bağlandı")
        self.use_websocket = False
        self.connection_status = "websocket_closed"
        
        # Fallback polling-ə keç
        self._start_polling_fallback()
    
    def _on_websocket_open(self, ws):
        """WebSocket açıldı"""
        logging.info("🟢 WebSocket qoşuldu")
        self.connection_status = "websocket_connected"
        self.error_count = 0
        
        # Qoşulma mesajı göndər
        try:
            ws.send(json.dumps({
                'type': 'subscribe',
                'tenant_id': self.tenant_id
            }))
        except Exception as e:
            logging.error(f"WebSocket qoşulma mesajı xətası: {e}")
    
    def _start_polling_fallback(self):
        """Polling fallback başladır"""
        if not self.thread or not self.thread.is_alive():
            self.thread = threading.Thread(target=self._monitor_loop, daemon=True)
            self.thread.start()
            self.connection_status = "polling_active"
            logging.info("🟡 Polling fallback başladıldı")
        
    def stop(self):
        """Real-time notification sistemini dayandırır"""
        self.is_running = False
        self.connection_status = "stopped"
        
        # WebSocket bağla
        if self.websocket:
            try:
                self.websocket.close()
            except:
                pass
        
        # Thread-ləri dayandır
        if self.thread:
            self.thread.join(timeout=1)
        if self.ws_thread:
            self.ws_thread.join(timeout=1)
            
        logging.info("🔴 Real-time notification sistemi dayandırıldı")
        
    def _monitor_loop(self):
        """Monitor döngüsü - dəyişiklikləri izləyir (polling fallback)"""
        while self.is_running and not self.use_websocket:
            try:
                self._check_for_changes()
                time.sleep(self.check_interval)
            except Exception as e:
                logging.error(f"Real-time monitor xətası: {e}")
                self.error_count += 1
                time.sleep(0.5)  # Xəta olduqda 0.5 saniyə gözlə
                
    def _check_for_changes(self):
        """Dəyişiklikləri yoxlayır (polling fallback)"""
        try:
            # Məcburi refresh varsa dərhal işlə
            if self.force_refresh:
                self._trigger_refresh('force_refresh', {'reason': 'manual_force'})
                self.force_refresh = False
                return
            
            # Son yoxlama vaxtını al
            current_time = datetime.now().isoformat()
            
            # Serverdən dəyişiklikləri sorğula (daha qısa timeout)
            response = requests.get(
                f"{self.server_url}/api/tenants/{self.tenant_id}/changes",
                params={
                    'since': self.last_check or current_time,
                    'timeout': 0.5  # 0.5 saniyə timeout
                },
                timeout=2  # 2 saniyə timeout - artırıldı
            )
            
            if response.status_code == 200:
                changes = response.json()
                if changes.get('has_changes', False):
                    self.change_count += 1
                    self.last_successful_check = datetime.now()
                    self.error_count = 0  # Uğurlu əməliyyatda xəta sayını sıfırla
                    
                    logging.info(f"🟢 Yeni dəyişiklik tapıldı (#{self.change_count}) - refresh tələb olunur")
                    self._trigger_refresh(changes.get('change_type', 'general'), changes.get('details', {}))
                    
                self.last_check = current_time
                
            elif response.status_code == 422:
                # 422 xətası - normal polling rejimi, amma az tezliklə
                self.error_count += 1
                # 422 xətaları çox olduqda interval-i artır
                if self.error_count > 10:
                    logging.info(f"422 xətaları çox - polling interval artırılacaq")
                
        except requests.exceptions.Timeout:
            # Timeout normaldır - server long polling istifadə edir
            pass
        except requests.exceptions.ConnectionError:
            # Bağlantı xətası - server əlçatan deyil
            logging.warning("Server əlçatan deyil - lokal refresh edilir")
            self._trigger_refresh('connection_error', {'reason': 'server_unavailable'})
        except Exception as e:
            logging.error(f"Dəyişiklik yoxlanarkən xəta: {e}")
            self.error_count += 1
            
    def _trigger_refresh(self, change_type, details=None):
        """Refresh tələb edir"""
        start_time = time.time()
        
        # DEBUG: Refresh başladı
        log_signal_received(change_type, details, "realtime_notifier")
        
        # Cache-i dərhal etibarsız et
        try:
            try:
                from utils import cache
            except ImportError:
                from src.utils import cache
            cache.invalidate_cache()
            logging.info(f"🔄 Cache etibarsız edildi - dəyişiklik: {change_type}")
        except Exception as e:
            logging.error(f"Cache etibarsız etmə xətası: {e}")
        
        # Callback-i çağır
        if self.callback:
            try:
                self.callback(change_type, details)
                self.last_change_time = datetime.now()
                logging.info(f"🔄 Refresh tələb edildi: {change_type}")
                
                # DEBUG: Refresh tamamlandı
                log_performance("refresh_trigger", time.time() - start_time, {"change_type": change_type}, "realtime_notifier")
            except Exception as e:
                logging.error(f"Refresh callback xətası: {e}")
                log_performance("refresh_trigger", time.time() - start_time, {"error": str(e)}, "realtime_notifier")
                
    def send_change_notification(self, change_type, details=None):
        """Dəyişiklik bildirişi göndərir (digər proqramlar üçün)"""
        start_time = time.time()
        
        try:
            # DEBUG: Signal göndərilməyə başladı
            log_signal_sent(change_type, details, "realtime_notifier")
            
            # Dəyişiklik məlumatlarını hazırla
            notification_data = {
                'change_type': change_type,
                'details': details or {},
                'timestamp': datetime.now().isoformat(),
                'tenant_id': self.tenant_id,
                'source': 'client'
            }
            
            # Dərhal lokal refresh tələb et
            self._trigger_refresh(change_type, details)
            
            # WebSocket varsa, oradan göndər
            if self.use_websocket and self.websocket and self.websocket.sock and self.websocket.sock.connected:
                try:
                    self.websocket.send(json.dumps(notification_data))
                    logging.info(f"🟢 WebSocket ilə bildiriş göndərildi: {change_type}")
                    
                    # DEBUG: WebSocket ilə göndərilmə uğurlu
                    log_network_operation("websocket_send", f"ws://{self.server_url}", "success", time.time() - start_time, "realtime_notifier")
                    return
                except Exception as e:
                    logging.warning(f"WebSocket göndərmə xətası: {e}")
                    log_network_operation("websocket_send", f"ws://{self.server_url}", "error", time.time() - start_time, "realtime_notifier")
            
            # Serverə bildiriş göndər (background thread-də)
            def send_to_server():
                server_start_time = time.time()
                try:
                    url = f"{self.server_url}/api/tenants/{self.tenant_id}/notify"
                    response = requests.post(url, json=notification_data, timeout=3)
                    
                    response_time = time.time() - server_start_time
                    
                    if response.status_code == 200:
                        logging.info(f"🟢 Dəyişiklik bildirişi göndərildi: {change_type}")
                        log_network_operation("server_notify", url, "success", response_time, "realtime_notifier")
                    else:
                        logging.warning(f"🔴 Dəyişiklik bildirişi göndərilmədi: {response.status_code}")
                        log_network_operation("server_notify", url, f"error_{response.status_code}", response_time, "realtime_notifier")
                        
                except Exception as e:
                    response_time = time.time() - server_start_time
                    logging.error(f"Server bildirişi xətası: {e}")
                    log_network_operation("server_notify", url, "exception", response_time, "realtime_notifier")
            
            # Background thread-də göndər
            threading.Thread(target=send_to_server, daemon=True).start()
            
            # DEBUG: Signal göndərilmə tamamlandı
            log_performance("signal_send", time.time() - start_time, {"change_type": change_type}, "realtime_notifier")
                
        except Exception as e:
            logging.error(f"Dəyişiklik bildirişi göndərilərkən xəta: {e}")
            log_performance("signal_send", time.time() - start_time, {"error": str(e)}, "realtime_notifier")
            # Xəta olduqda da lokal refresh et
            self._trigger_refresh(change_type, details)
    
    def send_immediate_refresh(self, change_type="manual_refresh", details=None):
        """Dərhal refresh tələb edir (manual əmrlər üçün)"""
        logging.info(f"🔄 Dərhal refresh tələb edilir: {change_type}")
        self._trigger_refresh(change_type, details or {})
        
    def force_immediate_refresh(self):
        """Məcburi dərhal refresh tələb edir"""
        self.force_refresh = True
        logging.info("🔄 Məcburi refresh tələb edildi")
        
    def get_status(self):
        """Notifier statusunu qaytarır"""
        return {
            'is_running': self.is_running,
            'connection_status': self.connection_status,
            'last_check': self.last_check,
            'last_change_time': self.last_change_time,
            'last_successful_check': self.last_successful_check,
            'change_count': self.change_count,
            'error_count': self.error_count,
            'check_interval': self.check_interval,
            'force_refresh_pending': self.force_refresh,
            'use_websocket': self.use_websocket,
            'websocket_connected': self.websocket and self.websocket.sock and self.websocket.sock.connected if self.websocket else False
        }

# Global instance
notifier = None

def init_notifier(tenant_id, callback=None):
    """Global notifier instance-ini başladır"""
    global notifier
    if notifier:
        notifier.stop()
    
    notifier = RealTimeNotifier(tenant_id)
    notifier.start(callback)
    return notifier

def get_notifier():
    """Global notifier instance-ini qaytarır"""
    return notifier

def stop_notifier():
    """Global notifier instance-ini dayandırır"""
    global notifier
    if notifier:
        notifier.stop()
        notifier = None

def send_manual_refresh(change_type="manual_refresh", details=None):
    """Manual refresh tələb edir"""
    global notifier
    if notifier:
        notifier.send_immediate_refresh(change_type, details)
    else:
        logging.warning("Notifier başladılmayıb - manual refresh göndərilə bilmədi")

def force_immediate_refresh():
    """Məcburi dərhal refresh tələb edir"""
    global notifier
    if notifier:
        notifier.force_immediate_refresh()
    else:
        logging.warning("Notifier başladılmayıb - məcburi refresh göndərilə bilmədi")