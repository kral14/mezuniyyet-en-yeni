#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Şifrə sıfırlama pəncərəsi
İşçilər üçün şifrə sıfırlama funksionallığı
Modern UI standartları ilə
"""

import tkinter as tk
from tkinter import ttk, messagebox
import re
import threading

# Import database with proper path handling
try:
    from core.email_service import email_service
    from database import database
except ImportError:
    # PyInstaller EXE rejimində alternativ import
    from src.core.email_service import email_service
    from src.database import database

class PasswordResetFrame(tk.Frame):
    def __init__(self, parent, back_callback=None):
        super().__init__(parent)
        self.parent = parent
        self.back_callback = back_callback
        
        # Modern stil
        self.configure(bg='#f0f0f0')
        
        # Dəyişənlər
        self.current_step = 1
        self.reset_email = ""
        self.reset_code = ""
        self.is_loading = False
        
        # UI yarat
        self.create_widgets()
        
        # Email regex pattern
        self.email_pattern = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
    
    def create_widgets(self):
        """UI elementlərini yaradır"""
        # Ana frame
        main_frame = tk.Frame(self, bg='#f0f0f0')
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Başlıq frame
        header_frame = tk.Frame(main_frame, bg='#f0f0f0')
        header_frame.pack(fill="x", pady=(0, 20))
        
        # Başlıq
        title_label = tk.Label(header_frame, text="🔐 Şifrə Sıfırlama", 
                              font=("Arial", 18, "bold"), 
                              bg='#f0f0f0', fg='#2c3e50')
        title_label.pack()
        
        # Alt başlıq
        subtitle_label = tk.Label(header_frame, text="Təhlükəsiz şifrə sıfırlama prosesi", 
                                 font=("Arial", 10), 
                                 bg='#f0f0f0', fg='#7f8c8d')
        subtitle_label.pack(pady=(5, 0))
        
        # Məzmun frame
        self.content_frame = tk.Frame(main_frame, bg='#f0f0f0')
        self.content_frame.pack(fill="both", expand=True)
        
        # İlk addımı göstər
        self.show_step_1()
    
    def show_step_1(self):
        """1-ci addım: Email daxil etmə"""
        # Mövcud məzmunu təmizlə
        for widget in self.content_frame.winfo_children():
            widget.destroy()
        
        # Addım göstəricisi
        step_frame = tk.Frame(self.content_frame, bg='#f0f0f0')
        step_frame.pack(fill="x", pady=(0, 20))
        
        step_label = tk.Label(step_frame, text="Addım 1/3", 
                             font=("Arial", 10, "bold"), 
                             bg='#f0f0f0', fg='#3498db')
        step_label.pack()
        
        # Təlimat
        instruction = tk.Label(self.content_frame, 
                              text="Şifrənizi sıfırlamaq üçün email ünvanınızı daxil edin:",
                              font=("Arial", 11), 
                              bg='#f0f0f0', fg='#2c3e50',
                              wraplength=400, justify="center")
        instruction.pack(pady=(0, 20))
        
        # Email frame
        email_frame = tk.Frame(self.content_frame, bg='#f0f0f0')
        email_frame.pack(fill="x", pady=10)
        
        email_label = tk.Label(email_frame, text="Email ünvanı:", 
                              font=("Arial", 10, "bold"), 
                              bg='#f0f0f0', fg='#2c3e50')
        email_label.pack(anchor="w", pady=(0, 5))
        
        self.email_entry = tk.Entry(email_frame, font=("Arial", 11), 
                                   width=50, relief="solid", bd=1)
        self.email_entry.pack(fill="x", pady=(0, 5))
        self.email_entry.bind('<KeyRelease>', self.check_email)
        self.email_entry.bind('<Return>', lambda e: self.send_reset_code() if self.send_button['state'] == 'normal' else None)
        
        # Status label
        self.status_label = tk.Label(self.content_frame, text="", 
                                    font=("Arial", 9), 
                                    bg='#f0f0f0')
        self.status_label.pack(pady=(10, 0))
        
        # Düymələr
        button_frame = tk.Frame(self.content_frame, bg='#f0f0f0')
        button_frame.pack(fill="x", pady=(30, 0))
        
        # Geri düyməsi
        back_btn = tk.Button(button_frame, text="⬅️ Geri", 
                            command=self.go_back,
                            font=("Arial", 10), 
                            bg='#95a5a6', fg='white',
                            relief="flat", bd=0, padx=20, pady=8)
        back_btn.pack(side="left", padx=(0, 10))
        
        # Göndər düyməsi
        self.send_button = tk.Button(button_frame, text="📧 Kod Göndər", 
                                    command=self.send_reset_code, 
                                    state="disabled",
                                    font=("Arial", 10, "bold"), 
                                    bg='#3498db', fg='white',
                                    relief="flat", bd=0, padx=20, pady=8)
        self.send_button.pack(side="right")
    
    def check_email(self, event=None):
        """Email yoxlanır və düymə aktiv/deaktiv edilir"""
        email = self.email_entry.get().strip()
        
        if not email:
            self.status_label.config(text="", fg="red")
            self.send_button.config(state="disabled", bg='#bdc3c7')
            return
        
        # Email formatını regex ilə yoxla
        if not self.email_pattern.match(email):
            self.status_label.config(text="❌ Düzgün email ünvanı daxil edin!", fg="#e74c3c")
            self.send_button.config(state="disabled", bg='#bdc3c7')
            return
        
        # Bazada istifadəçi varmı yoxla
        try:
            employee = database.get_employee_by_email(email)
            if employee:
                self.status_label.config(text=f"✅ İstifadəçi tapıldı: {employee['name']}", fg="#27ae60")
                self.send_button.config(state="normal", bg='#27ae60')
            else:
                # Database qoşulması işləmirsə, test üçün sadə həll
                self.status_label.config(text="⚠️ Database qoşulması yoxdur - test rejimi", fg="#f39c12")
                self.send_button.config(state="normal", bg='#f39c12')
        except Exception as e:
            print(f"DEBUG: check_email database xətası: {e}")
            # Database qoşulması işləmirsə, test üçün sadə həll
            self.status_label.config(text="⚠️ Database qoşulması yoxdur - test rejimi", fg="#f39c12")
            self.send_button.config(state="normal", bg='#f39c12')
    
    def show_step_2(self):
        """2-ci addım: Kod daxil etmə"""
        # Mövcud məzmunu təmizlə
        for widget in self.content_frame.winfo_children():
            widget.destroy()
        
        # Addım göstəricisi
        step_frame = tk.Frame(self.content_frame, bg='#f0f0f0')
        step_frame.pack(fill="x", pady=(0, 20))
        
        step_label = tk.Label(step_frame, text="Addım 2/3", 
                             font=("Arial", 10, "bold"), 
                             bg='#f0f0f0', fg='#3498db')
        step_label.pack()
        
        # İstifadəçi məlumatları
        try:
            employee = database.get_employee_by_email(self.reset_email)
            employee_name = employee['name'] if employee else "Naməlum"
        except:
            employee_name = "Naməlum"
        
        # Təlimat
        instruction = tk.Label(self.content_frame, 
                              text=f"'{self.reset_email}' ünvanına göndərilən 6 rəqəmli kodu daxil edin:",
                              font=("Arial", 11), 
                              bg='#f0f0f0', fg='#2c3e50',
                              wraplength=400, justify="center")
        instruction.pack(pady=(0, 15))
        
        # İstifadəçi adı
        user_info = tk.Label(self.content_frame, 
                            text=f"👤 İstifadəçi: {employee_name}",
                            font=("Arial", 12, "bold"),
                            bg='#f0f0f0', fg='#3498db')
        user_info.pack(pady=(0, 20))
        
        # Kod frame
        code_frame = tk.Frame(self.content_frame, bg='#f0f0f0')
        code_frame.pack(fill="x", pady=10)
        
        code_label = tk.Label(code_frame, text="Təsdiq Kodu:", 
                             font=("Arial", 10, "bold"), 
                             bg='#f0f0f0', fg='#2c3e50')
        code_label.pack(anchor="w", pady=(0, 5))
        
        self.code_entry = tk.Entry(code_frame, font=("Arial", 16, "bold"), 
                                  width=20, relief="solid", bd=1,
                                  justify="center")
        self.code_entry.pack(fill="x", pady=(0, 5))
        self.code_entry.focus()
        self.code_entry.bind('<KeyRelease>', self.check_code)
        self.code_entry.bind('<Return>', lambda e: self.verify_code() if self.verify_button['state'] == 'normal' else None)
        
        # Status label
        self.code_status_label = tk.Label(self.content_frame, text="", 
                                         font=("Arial", 9), 
                                         bg='#f0f0f0')
        self.code_status_label.pack(pady=(10, 0))
        
        # Yenidən göndər linki
        resend_frame = tk.Frame(self.content_frame, bg='#f0f0f0')
        resend_frame.pack(fill="x", pady=10)
        
        resend_label = tk.Label(resend_frame, text="Kod gəlmədi?", 
                               font=("Arial", 9), 
                               bg='#f0f0f0', fg='#7f8c8d')
        resend_label.pack(side="left")
        
        resend_link = tk.Label(resend_frame, text="🔄 Yenidən göndər", 
                              font=("Arial", 9, "bold"), 
                              bg='#f0f0f0', fg='#3498db', cursor="hand2")
        resend_link.pack(side="left", padx=(5, 0))
        resend_link.bind("<Button-1>", lambda e: self.send_reset_code())
        
        # Düymələr
        button_frame = tk.Frame(self.content_frame, bg='#f0f0f0')
        button_frame.pack(fill="x", pady=(30, 0))
        
        back_btn = tk.Button(button_frame, text="⬅️ Geri", 
                            command=self.show_step_1,
                            font=("Arial", 10), 
                            bg='#95a5a6', fg='white',
                            relief="flat", bd=0, padx=20, pady=8)
        back_btn.pack(side="left", padx=(0, 10))
        
        self.verify_button = tk.Button(button_frame, text="✅ Təsdiq Et", 
                                      command=self.verify_code, 
                                      state="disabled",
                                      font=("Arial", 10, "bold"), 
                                      bg='#bdc3c7', fg='white',
                                      relief="flat", bd=0, padx=20, pady=8)
        self.verify_button.pack(side="right")
    
    def check_code(self, event=None):
        """Kod yoxlanır və düymə aktiv/deaktiv edilir"""
        code = self.code_entry.get().strip()
        
        if not code:
            self.code_status_label.config(text="", fg="red")
            self.verify_button.config(state="disabled", bg='#bdc3c7')
            return
        
        if len(code) != 6 or not code.isdigit():
            self.code_status_label.config(text="❌ 6 rəqəmli kod daxil edin!", fg="#e74c3c")
            self.verify_button.config(state="disabled", bg='#bdc3c7')
            return
        
        # Yalnız format yoxlanır, real kod yoxlaması verify_code funksiyasında olacaq
        self.code_status_label.config(text="✅ Kod formatı düzgündür", fg="#27ae60")
        self.verify_button.config(state="normal", bg='#27ae60')
    
    def show_step_3(self):
        """3-cü addım: Yeni şifrə daxil etmə"""
        # Mövcud məzmunu təmizlə
        for widget in self.content_frame.winfo_children():
            widget.destroy()
        
        # Addım göstəricisi
        step_frame = tk.Frame(self.content_frame, bg='#f0f0f0')
        step_frame.pack(fill="x", pady=(0, 20))
        
        step_label = tk.Label(step_frame, text="Addım 3/3", 
                             font=("Arial", 10, "bold"), 
                             bg='#f0f0f0', fg='#3498db')
        step_label.pack()
        
        # İstifadəçi məlumatları
        try:
            employee = database.get_employee_by_email(self.reset_email)
            employee_name = employee['name'] if employee else "Naməlum"
        except:
            employee_name = "Naməlum"
        
        # Təlimat
        instruction = tk.Label(self.content_frame, 
                              text="Yeni şifrənizi daxil edin:",
                              font=("Arial", 11), 
                              bg='#f0f0f0', fg='#2c3e50',
                              wraplength=400, justify="center")
        instruction.pack(pady=(0, 15))
        
        # İstifadəçi adı
        user_info = tk.Label(self.content_frame, 
                            text=f"👤 İstifadəçi: {employee_name}",
                            font=("Arial", 12, "bold"),
                            bg='#f0f0f0', fg='#3498db')
        user_info.pack(pady=(0, 20))
        
        # Şifrə frame
        password_frame = tk.Frame(self.content_frame, bg='#f0f0f0')
        password_frame.pack(fill="x", pady=10)
        
        # Yeni şifrə
        password_label = tk.Label(password_frame, text="Yeni Şifrə:", 
                                 font=("Arial", 10, "bold"), 
                                 bg='#f0f0f0', fg='#2c3e50')
        password_label.pack(anchor="w", pady=(0, 5))
        
        self.password_entry = tk.Entry(password_frame, font=("Arial", 11), 
                                      width=50, show="*", relief="solid", bd=1)
        self.password_entry.pack(fill="x", pady=(0, 15))
        self.password_entry.bind('<KeyRelease>', self.check_password)
        
        # Şifrə təsdiqi
        confirm_label = tk.Label(password_frame, text="Şifrəni Təsdiq Et:", 
                                font=("Arial", 10, "bold"), 
                                bg='#f0f0f0', fg='#2c3e50')
        confirm_label.pack(anchor="w", pady=(0, 5))
        
        self.confirm_password_entry = tk.Entry(password_frame, font=("Arial", 11), 
                                              width=50, show="*", relief="solid", bd=1)
        self.confirm_password_entry.pack(fill="x", pady=(0, 5))
        self.confirm_password_entry.bind('<KeyRelease>', self.check_password)
        self.confirm_password_entry.bind('<Return>', lambda e: self.change_password() if self.change_button['state'] == 'normal' else None)
        
        # Şifrə tələbləri
        requirements_label = tk.Label(password_frame, 
                                     text="Şifrə tələbləri: ən azı 6 simvol",
                                     font=("Arial", 8), 
                                     bg='#f0f0f0', fg='#7f8c8d')
        requirements_label.pack(anchor="w", pady=(5, 0))
        
        # Status label
        self.password_status_label = tk.Label(self.content_frame, text="", 
                                             font=("Arial", 9), 
                                             bg='#f0f0f0')
        self.password_status_label.pack(pady=(10, 0))
        
        # Düymələr
        button_frame = tk.Frame(self.content_frame, bg='#f0f0f0')
        button_frame.pack(fill="x", pady=(30, 0))
        
        back_btn = tk.Button(button_frame, text="⬅️ Geri", 
                            command=self.show_step_2,
                            font=("Arial", 10), 
                            bg='#95a5a6', fg='white',
                            relief="flat", bd=0, padx=20, pady=8)
        back_btn.pack(side="left", padx=(0, 10))
        
        self.change_button = tk.Button(button_frame, text="🔐 Şifrəni Dəyiş", 
                                      command=self.change_password, 
                                      state="disabled",
                                      font=("Arial", 10, "bold"), 
                                      bg='#bdc3c7', fg='white',
                                      relief="flat", bd=0, padx=20, pady=8)
        self.change_button.pack(side="right")
    
    def check_password(self, event=None):
        """Şifrə yoxlanır və düymə aktiv/deaktiv edilir"""
        password = self.password_entry.get()
        confirm_password = self.confirm_password_entry.get()
        
        if not password:
            self.password_status_label.config(text="Yeni şifrəni daxil edin", fg="#e74c3c")
            self.change_button.config(state="disabled", bg='#bdc3c7')
            return
        
        if len(password) < 6:
            self.password_status_label.config(text="❌ Şifrə ən azı 6 simvol olmalıdır!", fg="#e74c3c")
            self.change_button.config(state="disabled", bg='#bdc3c7')
            return
        
        if not confirm_password:
            self.password_status_label.config(text="Şifrəni təsdiq edin!", fg="#e74c3c")
            self.change_button.config(state="disabled", bg='#bdc3c7')
            return
        
        if password != confirm_password:
            self.password_status_label.config(text="❌ Şifrələr uyğun gəlmir!", fg="#e74c3c")
            self.change_button.config(state="disabled", bg='#bdc3c7')
            return
        
        self.password_status_label.config(text="✅ Şifrələr uyğundur! Düyməyə basaraq şifrəni dəyişə bilərsiniz.", fg="#27ae60")
        self.change_button.config(state="normal", bg='#27ae60')
    
    def send_reset_code(self):
        """Şifrə sıfırlama kodunu göndərir"""
        if self.is_loading:
            return
            
        email = self.email_entry.get().strip()
        
        if not email:
            messagebox.showerror("Xəta", "Email ünvanını daxil edin!")
            return
        
        # Email formatını yoxla
        if not self.email_pattern.match(email):
            messagebox.showerror("Xəta", "Düzgün email ünvanı daxil edin!")
            return
        
        # Loading state
        self.is_loading = True
        self.send_button.config(text="⏳ Göndərilir...", state="disabled", bg='#bdc3c7')
        self.status_label.config(text="⏳ Email göndərilir, zəhmət olmasa gözləyin...", fg="#3498db")
        
        # Threading ilə email göndər
        thread = threading.Thread(target=self._send_email_thread, args=(email,))
        thread.daemon = True
        thread.start()
    
    def _send_email_thread(self, email):
        """Email göndərmə thread-i"""
        import logging
        logging.info(f"📧 [EMAIL_SEND] Email göndərmə prosesi başladı: {email}")
        
        try:
            # Progress: Veritabanında email yoxlanılır
            self.after(0, lambda: self.status_label.config(
                text="⏳ İstifadəçi məlumatları yoxlanılır...", fg="#3498db"
            ))
            
            logging.info(f"🔍 [EMAIL_SEND] Veritabanında email yoxlanılır: {email}")
            
            # Veritabanında bu email-i yoxla
            employee = None
            try:
                employee = database.get_employee_by_email(email)
                if employee:
                    logging.info(f"✅ [EMAIL_SEND] İstifadəçi tapıldı: ID={employee.get('id')}, Ad={employee.get('name')}, Email={email}")
                else:
                    logging.warning(f"⚠️ [EMAIL_SEND] İstifadəçi tapılmadı: {email}")
                    # Database qoşulması işləmirsə, test üçün sadə həll
                    employee = {'name': 'Test İstifadəçi', 'id': 1}
                    logging.warning(f"⚠️ [EMAIL_SEND] Test istifadəçi istifadə edilir: {email}")
            except Exception as e:
                logging.error(f"❌ [EMAIL_SEND] Database xətası: {e}, Email: {email}")
                print(f"DEBUG: Database xətası: {e}")
                # Database qoşulması işləmirsə, test üçün sadə həll
                employee = {'name': 'Test İstifadəçi', 'id': 1}
                logging.warning(f"⚠️ [EMAIL_SEND] Test istifadəçi istifadə edilir (xəta səbəbindən): {email}")
            
            # Progress: Server-ə sorğu göndərilir
            self.after(0, lambda: self.status_label.config(
                text="⏳ Server-ə sorğu göndərilir...", fg="#3498db"
            ))
            
            # Tenant ID-ni al (əgər mövcuddursa)
            tenant_id = None
            try:
                from core.tenant_manager import SettingsManager
                settings = SettingsManager()
                tenant_id = settings.get_tenant_id()
                logging.info(f"📋 [EMAIL_SEND] Tenant ID alındı: {tenant_id}, Email: {email}")
            except Exception as e:
                logging.warning(f"⚠️ [EMAIL_SEND] Tenant ID alına bilmədi: {e}, Email: {email}")
                pass
            
            # Progress: Email göndərilir
            self.after(0, lambda: self.status_label.config(
                text="⏳ Email göndərilir (5-15 saniyə çəkə bilər)...", fg="#3498db"
            ))
            
            logging.info(f"📧 [EMAIL_SEND] Email göndərmə funksiyası çağırılır: Email={email}, Ad={employee.get('name')}, TenantID={tenant_id}")
            
            # Email göndər
            success, message = email_service.send_reset_email(email, employee['name'], tenant_id)
            
            logging.info(f"📧 [EMAIL_SEND] Email göndərmə nəticəsi: Success={success}, Message={message}, Email={email}")
            
            # UI-ni yenilə
            self.after(0, self._handle_email_result, success, message, email, employee['name'])
            
        except Exception as e:
            logging.error(f"❌ [EMAIL_SEND] Gözlənilməz xəta: {e}, Email: {email}")
            self.after(0, self._handle_email_error, str(e))
    
    def _handle_email_result(self, success, message, email, employee_name):
        """Email nəticəsini emal edir"""
        self.is_loading = False
        
        if success:
            self.reset_email = email
            messagebox.showinfo("✅ Uğurlu", "Email uğurla göndərildi! Zəhmət olmasa email qutunuzu yoxlayın.")
            self.show_step_2()
        else:
            # Təhlükəsizlik: Email göndərilməyəndə kod yaradılmır
            # Yalnız server-dən email göndəriləndə kod mövcuddur
            self.send_button.config(text="📧 Kod Göndər", state="normal", bg='#3498db')
            self.status_label.config(text="❌ Email göndərilmədi", fg="#e74c3c")
            messagebox.showerror(
                "❌ Email Göndərilmədi", 
                f"{message}\n\n"
                f"Zəhmət olmasa:\n"
                f"• Server-ə qoşulduğunuzdan əmin olun\n"
                f"• İnternet bağlantınızı yoxlayın\n"
                f"• Admin ilə əlaqə saxlayın"
            )
    
    def _handle_email_error(self, error_message):
        """Email xətasını emal edir"""
        self.is_loading = False
        self.send_button.config(text="📧 Kod Göndər", state="normal", bg='#3498db')
        self.status_label.config(text="❌ Xəta baş verdi", fg="#e74c3c")
        messagebox.showerror("Xəta", f"Email göndərilmədi: {error_message}")
    
    def verify_code(self):
        """Təsdiq kodunu yoxlayır"""
        code = self.code_entry.get().strip()
        
        if not code:
            messagebox.showerror("❌ Xəta", "Təsdiq kodunu daxil edin!")
            return
        
        if len(code) != 6 or not code.isdigit():
            messagebox.showerror("❌ Xəta", "6 rəqəmli kod daxil edin!")
            return
        
        # Loading state
        self.verify_button.config(text="⏳ Yoxlanılır...", state="disabled", bg='#bdc3c7')
        self.code_status_label.config(text="⏳ Kod yoxlanılır...", fg="#3498db")
        
        # Kodu yoxla
        # Tenant ID-ni al (əgər mövcuddursa)
        tenant_id = None
        try:
            from core.tenant_manager import SettingsManager
            settings = SettingsManager()
            tenant_id = settings.get_tenant_id()
        except Exception:
            pass
        
        success, message = email_service.verify_reset_code(self.reset_email, code, tenant_id)
        
        if success:
            self.reset_code = code
            self.current_step = 3
            self.show_step_3()
            messagebox.showinfo("✅ Uğurlu", "Kod təsdiq edildi! İndi yeni şifrənizi təyin edə bilərsiniz.")
        else:
            self.verify_button.config(text="✅ Təsdiq Et", state="normal", bg='#27ae60')
            self.code_status_label.config(text="❌ " + message, fg="#e74c3c")
            messagebox.showerror("❌ Xəta", message)
    
    def change_password(self):
        """Yeni şifrəni tətbiq edir"""
        password = self.password_entry.get()
        confirm_password = self.confirm_password_entry.get()
        
        if not password:
            messagebox.showerror("❌ Xəta", "Yeni şifrəni daxil edin!")
            return
        
        if password != confirm_password:
            messagebox.showerror("❌ Xəta", "Şifrələr uyğun gəlmir!")
            return
        
        # Loading state
        self.change_button.config(text="⏳ Dəyişdirilir...", state="disabled", bg='#bdc3c7')
        self.password_status_label.config(text="⏳ Şifrə dəyişdirilir...", fg="#3498db")
        
        # Threading ilə şifrə dəyişdir
        thread = threading.Thread(target=self._change_password_thread, args=(password,))
        thread.daemon = True
        thread.start()
    
    def _change_password_thread(self, password):
        """Şifrə dəyişdirmə thread-i"""
        try:
            # İşçini tap və şifrəni dəyiş
            employee = database.get_employee_by_email(self.reset_email)
            if not employee:
                self.after(0, self._handle_password_error, "İşçi məlumatı tapılmadı!")
                return
            
            # Şifrəni yenilə
            if database.update_user_password(employee['id'], password):
                self.after(0, self._handle_password_success)
            else:
                self.after(0, self._handle_password_error, "Şifrə dəyişdirilərkən xəta baş verdi!")
                
        except Exception as e:
            self.after(0, self._handle_password_error, f"Gözlənilməz xəta: {str(e)}")
    
    def _handle_password_success(self):
        """Şifrə dəyişdirmə uğurlu"""
        self.change_button.config(text="🔐 Şifrəni Dəyiş", state="normal", bg='#27ae60')
        self.password_status_label.config(text="✅ Şifrə uğurla dəyişdirildi!", fg="#27ae60")
        messagebox.showinfo("✅ Uğurlu", "Şifrəniz uğurla dəyişdirildi!\n\nİndi yeni şifrənizlə giriş edə bilərsiniz.")
        self.go_back()
    
    def _handle_password_error(self, error_message):
        """Şifrə dəyişdirmə xətası"""
        self.change_button.config(text="🔐 Şifrəni Dəyiş", state="normal", bg='#27ae60')
        self.password_status_label.config(text="❌ " + error_message, fg="#e74c3c")
        messagebox.showerror("❌ Xəta", error_message)
    
    def go_back(self):
        """Login frame-ə qayıdır"""
        if self.back_callback:
            self.back_callback()