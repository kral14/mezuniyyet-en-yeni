#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Email xidməti - Şifrə sıfırlama üçün
Gmail SMTP istifadə edir
Modern təhlükəsizlik standartları ilə
"""

import smtplib
import random
import string
import hashlib
import secrets
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
import json
import os
import logging

class EmailService:
    def __init__(self):
        self.smtp_server = "smtp.gmail.com"
        self.smtp_port = 587
        self.sender_email = "vacationseasonplans@gmail.com"  # Gmail hesabı
        
        # Təhlükəsizlik: App password artıq client-də oxunmur
        # Yalnız server-dən email göndərilir
        self.app_password = None
        
        # Şifrə sıfırlama kodları üçün cache (təhlükəsizlik üçün)
        self.reset_codes = {}
        
        # Rate limiting üçün
        self.rate_limit = {}
        self.max_attempts = 3  # 15 dəqiqədə maksimum 3 cəhd
        self.rate_limit_window = 900  # 15 dəqiqə (saniyə)
        
        # Server client (email göndərmə üçün)
        try:
            try:
                from core.tenant_manager import CentralServerClient
            except ImportError:
                from src.core.tenant_manager import CentralServerClient
            self.server_client = CentralServerClient()
            self.use_server = True
        except Exception:
            self.server_client = None
            self.use_server = False
        
        # Logging konfiqurasiyası
        self.logger = self._setup_logging()
    
    def _setup_logging(self):
        """Logging konfiqurasiyasını quraşdırır"""
        logger = logging.getLogger('email_service')
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            try:
                # Log helper istifadə et
                try:
                    from utils.log_helper import get_log_file_path, archive_existing_log
                except ImportError:
                    from src.utils.log_helper import get_log_file_path, archive_existing_log
                
                # Mövcud log faylını arxiv et
                archive_existing_log('email_service.log')
                
                # Yeni log faylının yolunu al (timestamp ilə)
                log_file_path = get_log_file_path('email_service.log', with_timestamp=True)
                
                handler = logging.FileHandler(log_file_path, encoding='utf-8', mode='w')
                formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
                handler.setFormatter(formatter)
                logger.addHandler(handler)
                
                # Log handler-ə verilənlər bazasına yazma funksiyası əlavə et
                class DatabaseLogHandler(logging.Handler):
                    def emit(self, record):
                        try:
                            try:
                                from utils.log_helper import log_to_database_async
                            except ImportError:
                                from src.utils.log_helper import log_to_database_async
                            
                            log_message = self.format(record)
                            log_file_name = os.path.basename(log_file_path) if log_file_path else None
                            log_to_database_async('email_service', log_message, log_file_name)
                        except Exception:
                            pass
                
                db_handler = DatabaseLogHandler()
                db_handler.setFormatter(formatter)
                logger.addHandler(db_handler)
            except Exception as e:
                # Əgər fayl yaradıla bilməzsə, console handler istifadə et
                handler = logging.StreamHandler()
                formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
                handler.setFormatter(formatter)
                logger.addHandler(handler)
        
        return logger
    
    def _load_app_password(self):
        """Təhlükəsizlik: Artıq istifadə olunmur - yalnız server-dən email göndərilir"""
        # Bu funksiya artıq lazım deyil, amma köhnə kod uyğunluğu üçün saxlanılır
        return None
    
    def _create_sample_config(self, config_file):
        """Təhlükəsizlik: Artıq istifadə olunmur - yalnız server-dən email göndərilir"""
        # Bu funksiya artıq lazım deyil
        pass
        
    def _check_rate_limit(self, email):
        """Rate limiting yoxlayır"""
        current_time = datetime.now().timestamp()
        
        if email in self.rate_limit:
            attempts = self.rate_limit[email]
            # Köhnə cəhdləri sil
            attempts = [attempt_time for attempt_time in attempts 
                       if current_time - attempt_time < self.rate_limit_window]
            
            if len(attempts) >= self.max_attempts:
                return False, f"Çox cəhd edildi. Zəhmət olmasa {self.rate_limit_window // 60} dəqiqə gözləyin."
            
            attempts.append(current_time)
            self.rate_limit[email] = attempts
        else:
            self.rate_limit[email] = [current_time]
        
        return True, "OK"
    
    def generate_reset_code(self):
        """6 rəqəmli təsdiq kodu yaradır (təhlükəsizlik üçün secrets istifadə edir)"""
        return ''.join(secrets.choice(string.digits) for _ in range(6))
    
    def _generate_secure_token(self):
        """Təhlükəsiz token yaradır"""
        return secrets.token_urlsafe(32)
    
    def send_reset_email(self, to_email, employee_name, tenant_id=None):
        """Şifrə sıfırlama emaili göndərir (server-ə prioritet verir)"""
        self.logger.info(f"📧 [EMAIL_SERVICE] Email göndərmə prosesi başladı: Email={to_email}, Ad={employee_name}, TenantID={tenant_id}")
        
        # Rate limiting yoxla
        self.logger.debug(f"🔍 [EMAIL_SERVICE] Rate limiting yoxlanılır: {to_email}")
        rate_ok, rate_message = self._check_rate_limit(to_email)
        if not rate_ok:
            self.logger.warning(f"⚠️ [EMAIL_SERVICE] Rate limit exceeded: {to_email}, Message: {rate_message}")
            return False, rate_message
        self.logger.debug(f"✅ [EMAIL_SERVICE] Rate limiting OK: {to_email}")
        
        # Server-ə qoşulmadan əvvəl network connectivity yoxla
        if self.use_server and self.server_client:
            self.logger.info(f"🌐 [EMAIL_SERVICE] Server client mövcuddur: {to_email}")
            # Server-ə qoşulma yoxlaması (health check)
            self.logger.info(f"🏥 [EMAIL_SERVICE] Server health check başladı: {self.server_client.server_url}")
            try:
                import requests
                health_response = requests.get(
                    f"{self.server_client.server_url}/health",
                    timeout=5
                )
                if health_response.status_code != 200:
                    self.logger.warning(f"⚠️ [EMAIL_SERVICE] Server health check failed: Status={health_response.status_code}")
                    return False, "Server əlçatan deyil. Zəhmət olmasa internet bağlantınızı yoxlayın və ya admin ilə əlaqə saxlayın."
                self.logger.info(f"✅ [EMAIL_SERVICE] Server health check uğurlu: {self.server_client.server_url}")
            except requests.exceptions.ConnectionError as e:
                error_msg = str(e)
                self.logger.error(f"❌ [EMAIL_SERVICE] Server-ə qoşula bilmədi: {error_msg}, URL: {self.server_client.server_url}")
                if "Network is unreachable" in error_msg or "101" in error_msg:
                    return False, "İnternet bağlantısı yoxdur və ya server əlçatan deyil. Zəhmət olmasa internet bağlantınızı yoxlayın."
                else:
                    return False, f"Server-ə qoşula bilmədi: {error_msg}. Zəhmət olmasa internet bağlantınızı yoxlayın."
            except requests.exceptions.Timeout:
                self.logger.warning(f"⏱️ [EMAIL_SERVICE] Server health check timeout: {self.server_client.server_url}")
                return False, "Server cavab vermədi (timeout). Zəhmət olmasa yenidən cəhd edin."
            except Exception as e:
                self.logger.warning(f"⚠️ [EMAIL_SERVICE] Server health check xətası: {e}, URL: {self.server_client.server_url}")
                # Health check xətası olsa belə, email göndərməyə cəhd edək
        
        # Əvvəlcə server-ə cəhd et
        if self.use_server and self.server_client:
            try:
                self.logger.info(f"📤 [EMAIL_SERVICE] Email göndərmə sorğusu server-ə göndərilir: Email={to_email}, Ad={employee_name}, TenantID={tenant_id}")
                result = self.server_client.send_reset_email(to_email, employee_name, tenant_id)
                self.logger.info(f"📥 [EMAIL_SERVICE] Server cavabı alındı: {result}, Email={to_email}")
                
                if "error" not in result:
                    # Server uğurlu cavab verdi
                    if result.get("success", False):
                        # Reset kodu server-dən gəldi, lokal cache-ə də əlavə et
                        reset_code = result.get("reset_code")
                        if reset_code:
                            secure_token = self._generate_secure_token()
                            expiry_time = datetime.now() + timedelta(minutes=15)
                            code_hash = hashlib.sha256(reset_code.encode()).hexdigest()
                            self.reset_codes[to_email] = {
                                'code_hash': code_hash,
                                'expiry': expiry_time,
                                'employee_name': employee_name,
                                'token': secure_token,
                                'attempts': 0
                            }
                        self.logger.info(f"Email server tərəfindən uğurla göndərildi: {to_email}")
                        return True, result.get("message", "Email uğurla göndərildi!")
                    else:
                        error_msg = result.get('message', 'Unknown error')
                        error_type = result.get('error', 'UNKNOWN')
                        self.logger.error(f"Server email göndərə bilmədi: {error_msg} (Error: {error_type})")
                        # Daha ətraflı xəta mesajı qaytar
                        if error_type == "EMAIL_CONFIG_MISSING":
                            return False, f"Server-də email konfiqurasiyası yoxdur. Render.com-da APP_PASSWORD environment variable-ı təyin edilməlidir."
                        elif error_type == "SMTP_AUTH_FAILED":
                            return False, f"Gmail App Password səhvdir. Render.com-da APP_PASSWORD yenilənməlidir."
                        else:
                            return False, error_msg
                else:
                    error_msg = result.get('error', 'Unknown error')
                    error_type = result.get('error_type', 'UNKNOWN')
                    self.logger.error(f"Server xətası: {error_msg} (Type: {error_type})")
                    return False, f"Server xətası: {error_msg}"
            except Exception as e:
                error_msg = str(e)
                self.logger.error(f"Server çağırışı xətası: {error_msg}")
                # Daha yaxşı error mesajları
                if "Network is unreachable" in error_msg or "101" in error_msg:
                    return False, "İnternet bağlantısı yoxdur və ya server əlçatan deyil. Zəhmət olmasa internet bağlantınızı yoxlayın."
                elif "timeout" in error_msg.lower():
                    return False, "Server cavab vermədi (timeout). Zəhmət olmasa yenidən cəhd edin."
                else:
                    return False, f"Server-ə qoşula bilmədi: {error_msg}. Zəhmət olmasa internet bağlantınızı yoxlayın."
        
        # Təhlükəsizlik: Fallback lokal SMTP silindi
        # Yalnız server-dən email göndərilir
        self.logger.error("Email service: Server işləmir və fallback lokal SMTP təhlükəsizlik səbəbindən deaktiv edilib")
        return False, "Email xidməti hazırda mövcud deyil. Zəhmət olmasa server-ə qoşulun və ya admin ilə əlaqə saxlayın."
    
    def verify_reset_code(self, email, code, tenant_id=None):
        """Təsdiq kodunu yoxlayır (server-ə prioritet verir)"""
        # Əvvəlcə server-ə cəhd et
        if self.use_server and self.server_client:
            try:
                self.logger.info(f"Reset kodu server-də yoxlanılır: {email}")
                result = self.server_client.verify_reset_code(email, code, tenant_id)
                
                if "error" not in result:
                    # Server uğurlu cavab verdi
                    if result.get("success", False):
                        # Server-də kod düzgündür, lokal cache-dən də sil
                        if email in self.reset_codes:
                            del self.reset_codes[email]
                        self.logger.info(f"Reset kodu server tərəfindən təsdiqləndi: {email}")
                        return True, result.get("message", "Kod düzgündür")
                    else:
                        self.logger.warning(f"Server kod yoxlaması uğursuz: {result.get('message', 'Unknown error')}")
                else:
                    self.logger.warning(f"Server xətası: {result['error']}")
            except Exception as e:
                self.logger.warning(f"Server çağırışı xətası: {e}")
        
        # Təhlükəsizlik: Fallback lokal cache silindi
        # Yalnız server-dən kod yoxlanılır
        self.logger.error("Email service: Server işləmir və fallback lokal cache təhlükəsizlik səbəbindən deaktiv edilib")
        return False, "Kod yoxlanıla bilmədi. Zəhmət olmasa server-ə qoşulun və ya admin ilə əlaqə saxlayın."
    
    def get_employee_name(self, email):
        """Email üçün işçi adını qaytarır"""
        if email in self.reset_codes:
            return self.reset_codes[email]['employee_name']
        return None

# Global email service instance
email_service = EmailService()

def test_email_service():
    """Email xidmətini test edir"""
    print("Email xidməti test edilir...")
    
    # Təhlükəsizlik: Artıq lokal konfiqurasiya yoxlanılmır
    if email_service.use_server and email_service.server_client:
        print("✅ Email xidməti server-dən istifadə edir (təhlükəsiz)")
        print("MƏLUMAT: Email xidməti hazırdır!")
        return True
    else:
        print("⚠️ Email xidməti server-ə qoşula bilmədi")
        print("MƏLUMAT: Server-ə qoşulun və ya admin ilə əlaqə saxlayın")
        return False

if __name__ == "__main__":
    test_email_service()