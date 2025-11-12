#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import os
import shutil
from datetime import datetime, date
import logging

# Universal kalendar import (nisbi yol ilə)
from .universal_calendar import DateEntry

class ProfilePage(tk.Frame):
    """Test profil səhifəsi - sadə və təmiz"""
    
    def __init__(self, parent, user_data, on_back=None):
        logger = logging.getLogger(__name__)
        logger.info("ProfilePage __init__ başlayır")
        
        super().__init__(parent)
        self.parent = parent
        self.user_data = user_data
        self.on_back = on_back
        
        # Veritabanından tam məlumatları yüklə
        self.load_full_user_data()
        
        # Dəyişiklik izləmə sistemi
        self.has_changes = False
        self.original_data = {}
        
        # Sadə rəng sxemi
        self.colors = {
            'primary': 'blue',         # Mavi
            'secondary': 'green',      # Yaşıl
            'danger': 'red',           # Qırmızı
            'success': 'green',        # Yaşıl
            'warning': 'orange',       # Narıncı
            'light': 'lightgray',      # Açıq boz
            'white': 'white',          # Ağ
            'dark': 'darkgray',        # Tünd mavi-boz
            'text_primary': 'black',   # Əsas mətn
            'text_secondary': 'gray',  # İkinci dərəcəli mətn
            'border': 'gray',          # Sərhəd rəngi
            'background': 'white'      # Açıq arxa fon
        }
        
        # Frame konfiqurasiyası
        self.configure(background=self.colors['background'])
        
        # Profil şəkilləri artıq lokal papkada deyil, veritabanında saxlanılır
        self.profile_images_dir = None
        self.profile_image_path = None
        
        # Widget-ləri yarat
        self.create_widgets()
        
        # Profil məlumatlarını yüklə
        self.load_profile_data()
        
        # Orijinal məlumatları saxla
        self._save_original_data()
        
        logger.info("ProfilePage tamamlandı")
    
    def load_full_user_data(self):
        """Veritabanından istifadəçinin tam məlumatlarını yükləyir"""
        try:
            import database
            full_user_data = database.get_user_by_id(self.user_data['id'])
            if full_user_data:
                # Mövcud məlumatları yenilə
                self.user_data.update(full_user_data)
                logging.info(f"İstifadəçi məlumatları yükləndi: {self.user_data['name']}")
            else:
                logging.warning(f"İstifadəçi ID {self.user_data['id']} üçün məlumat tapılmadı")
        except Exception as e:
            logging.error(f"İstifadəçi məlumatları yüklənərkən xəta: {e}")
    
    def _save_original_data(self):
        """Orijinal məlumatları saxlayır"""
        try:
            # Bütün dəyişən sahələri izlə
            self.original_data = {
                'first_name': getattr(self, 'first_name_var', None),
                'last_name': getattr(self, 'last_name_var', None),
                'email': getattr(self, 'email_var', None),
                'phone': getattr(self, 'phone_var', None),
                'birth_date': getattr(self, 'birth_date_var', None),
                'address': getattr(self, 'address_var', None),
                'position': getattr(self, 'position_var', None),
                'department': getattr(self, 'department_var', None),
                'hire_date': getattr(self, 'hire_date_var', None),
                'salary': getattr(self, 'salary_var', None),
                'profile_image': self.profile_image_path
            }
        except Exception as e:
            logging.error(f"Orijinal məlumatları saxlayarkən xəta: {e}")
    
    def _check_for_changes(self):
        """Dəyişiklikləri yoxlayır"""
        try:
            current_data = {
                'first_name': getattr(self, 'first_name_var', None),
                'last_name': getattr(self, 'last_name_var', None),
                'email': getattr(self, 'email_var', None),
                'phone': getattr(self, 'phone_var', None),
                'birth_date': getattr(self, 'birth_date_var', None),
                'address': getattr(self, 'address_var', None),
                'position': getattr(self, 'position_var', None),
                'department': getattr(self, 'department_var', None),
                'hire_date': getattr(self, 'hire_date_var', None),
                'salary': getattr(self, 'salary_var', None),
                'profile_image': self.profile_image_path
            }
            
            # Dəyişiklikləri yoxla
            for key in current_data:
                if key in self.original_data:
                    current_value = current_data[key].get() if hasattr(current_data[key], 'get') else current_data[key]
                    original_value = self.original_data[key].get() if hasattr(self.original_data[key], 'get') else self.original_data[key]
                    
                    if current_value != original_value:
                        self.has_changes = True
                        logging.info(f"Dəyişiklik tapıldı: {key} - {original_value} -> {current_value}")
                        return True
            
            self.has_changes = False
            return False
            
        except Exception as e:
            logging.error(f"Dəyişiklikləri yoxlayarkən xəta: {e}")
            return False
    
    def _mark_as_changed(self):
        """Dəyişiklik olduğunu qeyd edir"""
        self.has_changes = True
        logging.info("Profil məlumatlarında dəyişiklik qeyd edildi") 
    
    def create_widgets(self):
        """Ana widget-ləri yaradır"""
        logger = logging.getLogger(__name__)
        logger.info("create_widgets başlayır")
        
        # Ana container
        main_frame = tk.Frame(self, bg=self.colors['background'])
        main_frame.pack(fill="both", expand=True, padx=15, pady=15)
        
        # Başlıq
        self.create_header(main_frame)
        
        # Məzmun bölməsi
        content_frame = tk.Frame(main_frame, bg=self.colors['white'], relief="raised", bd=2)
        content_frame.pack(fill="both", expand=True, pady=(15, 0))
        
        # Sol və sağ panel
        left_panel = tk.Frame(content_frame, bg=self.colors['white'], width=300)
        left_panel.pack(side="left", fill="y", padx=15, pady=15)
        left_panel.pack_propagate(False)
        
        right_panel = tk.Frame(content_frame, bg=self.colors['white'])
        right_panel.pack(side="right", fill="both", expand=True, padx=15, pady=15)
        
        # Sol panel məzmunu
        self.create_left_panel(left_panel)
        
        # Sağ panel məzmunu
        self.create_right_panel(right_panel)
        
        logger.info("create_widgets tamamlandı")
    
    def create_header(self, parent):
        """Başlıq bölməsini yaradır"""
        header_frame = tk.Frame(parent, bg=self.colors['primary'], height=60)
        header_frame.pack(fill="x")
        header_frame.pack_propagate(False)
        
        # Geri qayıtma düyməsi (sol tərəf)
        if self.on_back:
            back_btn = tk.Button(header_frame, text="← Geri", 
                                command=self.on_escape,
                                bg='#2980b9', fg=self.colors['white'], 
                                font=('Segoe UI', 11, 'bold'),
                                relief="flat", padx=12, pady=4, cursor="hand2")
            back_btn.pack(side="left", padx=15, pady=18)
        
        # Başlıq mətn (mərkəz) - istifadəçinin adı ilə
        user_name = self.user_data.get('name', 'İstifadəçi')
        title_text = f"👤 {user_name.upper()} PROFİL SƏHİFƏSİ"
        title_label = tk.Label(header_frame, 
                              text=title_text, 
                              bg=self.colors['primary'], fg=self.colors['white'],
                              font=('Segoe UI', 16, 'bold'))
        title_label.pack(expand=True)
        
        # Alt xətt
        separator = tk.Frame(header_frame, bg='#2980b9', height=3)
        separator.pack(fill="x", side="bottom")
    
    def create_left_panel(self, parent):
        """Sol panel məzmununu yaradır"""
        # Profil şəkli
        self.create_profile_image_section(parent)
        
        # İstifadəçi məlumatları
        self.create_user_info_section(parent)
    
    def create_profile_image_section(self, parent):
        """Profil şəkli bölməsini yaradır"""
        image_frame = tk.Frame(parent, bg=self.colors['white'])
        image_frame.pack(fill="x", pady=(0, 20))
        
        # Şəkil çərçivəsi
        image_container = tk.Frame(image_frame, bg=self.colors['border'], width=180, height=180, 
                                  relief="solid", bd=3)
        image_container.pack()
        image_container.pack_propagate(False)
        
        self.image_label = tk.Label(image_container, text="📷\nŞəkil yoxdur", 
                                   bg=self.colors['border'], fg=self.colors['text_secondary'], 
                                   font=('Segoe UI', 12), justify="center")
        self.image_label.pack(expand=True, fill="both")
        
        # Şəkil düymələri
        btn_frame = tk.Frame(image_frame, bg=self.colors['white'])
        btn_frame.pack(pady=10)
        
        tk.Button(btn_frame, text="📁 Şəkil Seç", command=self.select_image,
                 bg=self.colors['primary'], fg=self.colors['white'], font=('Segoe UI', 9, 'bold'),
                 relief="flat", padx=10, pady=3, cursor="hand2").pack(side="left", padx=2)
        
        tk.Button(btn_frame, text="🗑️ Sil", command=self.remove_image,
                 bg=self.colors['danger'], fg=self.colors['white'], font=('Segoe UI', 9, 'bold'),
                 relief="flat", padx=10, pady=3, cursor="hand2").pack(side="left", padx=2)
    
    def create_user_info_section(self, parent):
        """İstifadəçi məlumatları bölməsini yaradır"""
        info_frame = tk.Frame(parent, bg=self.colors['white'])
        info_frame.pack(fill="x")
        
        # İstifadəçi adı
        tk.Label(info_frame, text="👤 İstifadəçi Adı:", 
                bg=self.colors['white'], fg=self.colors['text_primary'], 
                font=('Segoe UI', 11, 'bold')).pack(anchor="w", pady=(0, 5))
        
        self.username_var = tk.StringVar(value=self.user_data.get('username', ''))
        username_entry = tk.Entry(info_frame, textvariable=self.username_var, 
                                 font=('Segoe UI', 11), state="readonly", 
                                 bg=self.colors['light'], fg=self.colors['text_primary'], 
                                 relief="solid", bd=1)
        username_entry.pack(fill="x", pady=(0, 15))
        
        # Rol
        tk.Label(info_frame, text="🔑 Rol:", 
                bg=self.colors['white'], fg=self.colors['text_primary'], 
                font=('Segoe UI', 11, 'bold')).pack(anchor="w", pady=(0, 5))
        
        self.role_var = tk.StringVar(value=self.user_data.get('role', 'user'))
        role_entry = tk.Entry(info_frame, textvariable=self.role_var, 
                             font=('Segoe UI', 11), state="readonly",
                             bg=self.colors['light'], fg=self.colors['text_primary'], 
                             relief="solid", bd=1)
        role_entry.pack(fill="x", pady=(0, 15))
        
        # Email
        tk.Label(info_frame, text="📧 Email:", 
                bg=self.colors['white'], fg=self.colors['text_primary'], 
                font=('Segoe UI', 11, 'bold')).pack(anchor="w", pady=(0, 5))
        
        self.email_var = tk.StringVar(value=self.user_data.get('email', ''))
        email_entry = tk.Entry(info_frame, textvariable=self.email_var, 
                              font=('Segoe UI', 11),
                              bg=self.colors['white'], fg=self.colors['text_primary'], 
                              relief="solid", bd=1)
        email_entry.pack(fill="x", pady=(0, 15))
        
        # Dəyişiklik izləmə üçün event listener əlavə et
        def on_change(*args):
            self._mark_as_changed()
        
        self.email_var.trace_add("write", on_change)
    
    def select_image(self):
        """Şəkil seçmə dialoqu - şəkil base64 kimi saxlanılır"""
        file_path = filedialog.askopenfilename(
            title="Profil şəkli seç",
            filetypes=[("Şəkil faylları", "*.jpg *.jpeg *.png *.gif *.bmp")]
        )
        
        if file_path:
            try:
                # Şəkli base64 formatına çevir
                import base64
                with open(file_path, 'rb') as img_file:
                    img_data = base64.b64encode(img_file.read()).decode('utf-8')
                
                # Base64 məlumatları saxla (lokal fayl yoxdur)
                self.profile_image_path = img_data
                self.load_profile_image(img_data, is_base64=True)
                self._mark_as_changed()  # Dəyişiklik qeyd et
                
                messagebox.showinfo("Uğurlu", "Şəkil uğurla yükləndi!")
                
            except Exception as e:
                logging.error(f"Şəkil yükləmə xətası: {e}")
                messagebox.showerror("Xəta", f"Şəkil yüklənərkən xəta: {e}")
    
    def load_profile_image(self, image_path, is_base64=False):
        """Profil şəkli yükləyir - base64 formatında"""
        try:
            if image_path:
                if is_base64 or len(image_path) > 100:  # Base64 string uzundur
                    self.image_label.configure(text="📷\nŞəkil yükləndi\n(veritabanında)")
                    logging.info("Şəkil base64 formatında yükləndi")
                elif os.path.exists(image_path):
                    # Köhnə lokal fayllar üçün
                    self.image_label.configure(text="📷\nŞəkil yükləndi")
                    logging.info(f"Şəkil yükləndi: {image_path}")
                else:
                    self.image_label.configure(text="📷\nŞəkil yoxdur")
            else:
                self.image_label.configure(text="📷\nŞəkil yoxdur")
        except Exception as e:
            logging.error(f"Şəkil yükləmə xətası: {e}")
            self.image_label.configure(text="Şəkil yüklənə bilmədi")
    
    def remove_image(self):
        """Profil şəkli silir"""
        self.image_label.configure(text="📷\nŞəkil yoxdur")
        self.profile_image_path = None
        self._mark_as_changed()  # Dəyişiklik qeyd et
        messagebox.showinfo("Uğurlu", "Şəkil silindi!")
    
    def load_profile_data(self):
        """Profil məlumatlarını yükləyir"""
        # Mövcud şəkli yüklə
        if 'profile_image' in self.user_data and self.user_data['profile_image']:
            self.profile_image_path = self.user_data['profile_image']
            self.load_profile_image(self.user_data['profile_image'])
    
    def change_password(self):
        """İşçilər öz şifrələrini dəyişir (cari şifrə tələb olunur)"""
        current_password = self.current_password_var.get()
        new_password = self.new_password_var.get()
        confirm_password = self.confirm_password_var.get()
        
        if not all([current_password, new_password, confirm_password]):
            messagebox.showerror("Xəta", "Bütün şifrə sahələri doldurulmalıdır.")
            return
            
        if new_password != confirm_password:
            messagebox.showerror("Xəta", "Yeni şifrələr eyni deyil.")
            return
            
        # Minimum şifrə uzunluğu məhdudiyyətini aradan qaldırırıq
        if len(new_password) < 1:
            messagebox.showerror("Xəta", "Şifrə boş ola bilməz.")
            return
        
        # İşçilər öz şifrələrini dəyişəndə cari şifrə tələb olunur
        try:
            import database
            success = database.change_user_password(self.user_data['id'], current_password, new_password)
            if success:
                messagebox.showinfo("Uğurlu", "Şifrə uğurla dəyişdirildi!")
            else:
                messagebox.showerror("Xəta", "Cari şifrə yanlışdır və ya şifrə dəyişdirilərkən xəta baş verdi!")
        except Exception as e:
            messagebox.showerror("Xəta", f"Şifrə dəyişdirilərkən xəta: {str(e)}")
        
        # Şifrə sahələrini təmizlə
        self.current_password_var.set("")
        self.new_password_var.set("")
        self.confirm_password_var.set("")
    
    def save_changes(self):
        """Dəyişiklikləri saxlayır"""
        try:
            # Tarix validasiyası
            if self.birth_date_var.get() and self.birth_date_var.get().strip():
                try:
                    datetime.strptime(self.birth_date_var.get().strip(), '%Y-%m-%d')
                except ValueError:
                    messagebox.showerror("Xəta", "Doğum tarixi 'YYYY-MM-DD' formatında olmalıdır.")
                    return
            
            if self.hire_date_var.get() and self.hire_date_var.get().strip():
                try:
                    datetime.strptime(self.hire_date_var.get().strip(), '%Y-%m-%d')
                except ValueError:
                    messagebox.showerror("Xəta", "İşə qəbul tarixi 'YYYY-MM-DD' formatında olmalıdır.")
                    return
            
            # Maaş rəqəm formatında olmalıdır
            if self.salary_var.get():
                try:
                    salary_value = float(self.salary_var.get())
                    if salary_value < 0: raise ValueError
                except (ValueError, TypeError):
                    messagebox.showerror("Xəta", "Maaş düzgün rəqəm formatında olmalıdır.")
                    return
            
            # Məlumatları topla
            user_data = {
                'first_name': self.first_name_var.get().strip(),
                'last_name': self.last_name_var.get().strip(),
                'father_name': self.father_name_var.get().strip(),
                'email': self.email_var.get().strip(),
                'phone_number': self.phone_var.get().strip(),
                'birth_date': self.birth_date_var.get().strip(),
                'address': self.address_var.get().strip(),
                'position': self.position_var.get().strip(),
                'department': self.department_var.get().strip(),
                'hire_date': self.hire_date_var.get().strip(),
                'salary': self.salary_var.get().strip(),
                'profile_image': self.profile_image_path
            }
            
            # Veritabanına yaz
            import database
            success = database.update_user_profile(self.user_data['id'], user_data)
            if success:
                # Mövcud məlumatları yenilə
                self.user_data.update(user_data)
                
                # Dəyişiklikləri qeyd et
                self.has_changes = False
                self._save_original_data()  # Yeni orijinal məlumatları saxla
                        
                messagebox.showinfo("Uğurlu", "Məlumatlar uğurla yeniləndi!")
                logging.info("Profil məlumatları uğurla saxlanıldı")
            else:
                messagebox.showerror("Xəta", "Məlumatlar yenilənərkən xəta baş verdi!")
            
        except Exception as e:
            logging.error(f"Məlumatlar yenilənərkən xəta: {e}")
            messagebox.showerror("Xəta", f"Məlumatlar yenilənərkən xəta: {e}")
    
    def on_escape(self):
        """Geri qayıtma funksiyası"""
        try:
            # Dəyişiklikləri yoxla
            has_changes = self._check_for_changes()
            
            if has_changes:
                # Dəyişiklik varsa, istifadəçidən təsdiq al
                result = messagebox.askyesnocancel(
                    "Dəyişikliklər",
                    "Profil məlumatlarında dəyişikliklər var. Dəyişiklikləri saxlamaq istəyirsinizmi?",
                    icon='question'
                )
                
                if result is True:  # Bəli - saxlamaq istəyir
                    self.save_changes()
                    logging.info("Dəyişikliklər saxlanıldı və əsas səhifəyə qayıtmaq lazımdır")
                    if self.on_back:
                        self.on_back(needs_refresh=True)
                        
                elif result is False:  # Xeyr - saxlamaq istəmir
                    logging.info("Dəyişikliklər saxlanılmadı, əsas səhifəyə qayıtmaq lazımdır")
                    if self.on_back:
                        self.on_back(needs_refresh=False)
                        
                else:  # Cancel - burada qal
                    logging.info("İstifadəçi geri qayıtmaqdan imtina etdi")
                    return
                    
            else:
                # Dəyişiklik yoxdursa, sadəcə geri qayıt
                logging.info("Dəyişiklik yoxdur, əsas səhifəyə qayıtmaq lazımdır")
                if self.on_back:
                    self.on_back(needs_refresh=False)
                    
        except Exception as e:
            logging.error(f"Geri qayıtma zamanı xəta: {e}")
            if self.on_back:
                self.on_back(needs_refresh=False)
    
    def create_right_panel(self, parent):
        """Sağ panel məzmununu yaradır"""
        # Notebook (tab sistemi)
        notebook = ttk.Notebook(parent)
        notebook.pack(fill="both", expand=True)
        
        # Şəxsi məlumatlar tab
        personal_tab = tk.Frame(notebook, bg=self.colors['white'])
        notebook.add(personal_tab, text="👤 Şəxsi Məlumatlar")
        self.create_personal_info_tab(personal_tab)
        
        # İş məlumatları tab
        work_tab = tk.Frame(notebook, bg=self.colors['white'])
        notebook.add(work_tab, text="💼 İş Məlumatları")
        self.create_work_info_tab(work_tab)
        
        # Şifrə dəyişdirmə tab
        password_tab = tk.Frame(notebook, bg=self.colors['white'])
        notebook.add(password_tab, text="🔒 Şifrə Dəyişdirmə")
        self.create_password_tab(password_tab)
    
    def create_personal_info_tab(self, parent):
        """Şəxsi məlumatlar tab-ını yaradır"""
        # Scrollable frame
        canvas = tk.Canvas(parent, bg=self.colors['white'], highlightthickness=0)
        scrollbar = tk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg=self.colors['white'])
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Məlumat sahələri
        fields_frame = tk.Frame(scrollable_frame, bg=self.colors['white'])
        fields_frame.pack(fill="x", padx=15, pady=15)
        
        # Ad
        self.first_name_var = tk.StringVar(value=self.user_data.get('first_name', ''))
        self.create_field_row(fields_frame, "Ad:", self.first_name_var)
        
        # Soyad
        self.last_name_var = tk.StringVar(value=self.user_data.get('last_name', ''))
        self.create_field_row(fields_frame, "Soyad:", self.last_name_var)
        
        # Ata adı
        self.father_name_var = tk.StringVar(value=self.user_data.get('father_name', ''))
        self.create_field_row(fields_frame, "Ata adı:", self.father_name_var)
        
        # Doğum tarixi
        self.birth_date_var = tk.StringVar(value=self.user_data.get('birth_date', '1990-01-01'))
        self.create_date_field_row(fields_frame, "Doğum tarixi:", self.birth_date_var)
        
        # Telefon
        self.phone_var = tk.StringVar(value=self.user_data.get('phone_number', ''))
        self.create_field_row(fields_frame, "📞 Telefon:", self.phone_var)
        
        # Ünvan
        self.address_var = tk.StringVar(value=self.user_data.get('address', ''))
        self.create_field_row(fields_frame, "🏠 Ünvan:", self.address_var)
        
        # Düymələr
        button_frame = tk.Frame(scrollable_frame, bg=self.colors['white'])
        button_frame.pack(pady=20)
        
        tk.Button(button_frame, text="💾 Yadda Saxla", command=self.save_changes,
                 bg=self.colors['success'], fg=self.colors['white'], font=('Segoe UI', 11, 'bold'),
                 relief="flat", padx=25, pady=8, cursor="hand2").pack(side="left", padx=5)
        
        # Scrollbar və canvas
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y") 
    
    def create_work_info_tab(self, parent):
        """İş məlumatları tab-ını yaradır"""
        # Scrollable frame
        canvas = tk.Canvas(parent, bg=self.colors['white'], highlightthickness=0)
        scrollbar = tk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg=self.colors['white'])
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Məlumat sahələri
        fields_frame = tk.Frame(scrollable_frame, bg=self.colors['white'])
        fields_frame.pack(fill="x", padx=15, pady=15)
        
        # Vəzifə
        self.position_var = tk.StringVar(value=self.user_data.get('position', ''))
        self.create_field_row(fields_frame, "Vəzifə:", self.position_var)
        
        # Şöbə
        self.department_var = tk.StringVar(value=self.user_data.get('department', ''))
        self.create_field_row(fields_frame, "Şöbə:", self.department_var)
        
        # İşə qəbul tarixi
        self.hire_date_var = tk.StringVar(value=self.user_data.get('hire_date', '2020-01-01'))
        self.create_date_field_row(fields_frame, "İşə qəbul:", self.hire_date_var)
        
        # Maaş
        salary_value = self.user_data.get('salary', '')
        if salary_value:
            salary_value = str(salary_value)
        self.salary_var = tk.StringVar(value=salary_value)
        self.create_field_row(fields_frame, "💰 Maaş:", self.salary_var)
        
        # Düymələr
        button_frame = tk.Frame(scrollable_frame, bg=self.colors['white'])
        button_frame.pack(pady=20)
        
        tk.Button(button_frame, text="💾 Yadda Saxla", command=self.save_changes,
                 bg=self.colors['success'], fg=self.colors['white'], font=('Segoe UI', 11, 'bold'),
                 relief="flat", padx=25, pady=8, cursor="hand2").pack(side="left", padx=5)
        
        # Scrollbar və canvas
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
    
    def create_password_tab(self, parent):
        """Şifrə dəyişdirmə tab-ını yaradır"""
        # Mərkəz çərçivəsi
        center_frame = tk.Frame(parent, bg=self.colors['white'])
        center_frame.pack(expand=True, fill="both")
        
        # Şifrə dəyişdirmə çərçivəsi
        password_frame = tk.Frame(center_frame, bg=self.colors['light'], relief="raised", bd=3)
        password_frame.pack(expand=True, padx=50, pady=50)
        
        # Başlıq
        tk.Label(password_frame, text="🔒 Şifrə Dəyişdirmə", 
                bg=self.colors['light'], fg=self.colors['text_primary'], 
                font=('Segoe UI', 14, 'bold')).pack(pady=(20, 15))
        
        # İstifadəçi məlumatı
        tk.Label(password_frame, text="ℹ️ Öz şifrənizi dəyişmək üçün cari şifrənizi daxil edin", 
                bg=self.colors['light'], fg=self.colors['text_secondary'], 
                font=('Segoe UI', 10)).pack(anchor="w", padx=20, pady=(0, 15))
        
        # Cari şifrə
        tk.Label(password_frame, text="Cari şifrə:", 
                bg=self.colors['light'], fg=self.colors['text_primary'], 
                font=('Segoe UI', 11, 'bold')).pack(anchor="w", padx=20)
        
        self.current_password_var = tk.StringVar()
        tk.Entry(password_frame, textvariable=self.current_password_var, show="*", 
                font=('Segoe UI', 11), width=25, relief="solid", bd=1).pack(pady=(5, 10), padx=20)
        
        # Yeni şifrə
        tk.Label(password_frame, text="Yeni şifrə:", 
                bg=self.colors['light'], fg=self.colors['text_primary'], 
                font=('Segoe UI', 11, 'bold')).pack(anchor="w", padx=20)
        
        self.new_password_var = tk.StringVar()
        tk.Entry(password_frame, textvariable=self.new_password_var, show="*", 
                font=('Segoe UI', 11), width=25, relief="solid", bd=1).pack(pady=(5, 10), padx=20)
        
        # Şifrə təsdiq
        tk.Label(password_frame, text="Şifrə təsdiq:", 
                bg=self.colors['light'], fg=self.colors['text_primary'], 
                font=('Segoe UI', 11, 'bold')).pack(anchor="w", padx=20)
        
        self.confirm_password_var = tk.StringVar()
        tk.Entry(password_frame, textvariable=self.confirm_password_var, show="*", 
                font=('Segoe UI', 11), width=25, relief="solid", bd=1).pack(pady=(5, 20), padx=20)
        
        # Düymə
        tk.Button(password_frame, text="🔐 Şifrəni Dəyiş", command=self.change_password,
                 bg=self.colors['danger'], fg=self.colors['white'], font=('Segoe UI', 11, 'bold'),
                 relief="flat", padx=25, pady=8, cursor="hand2").pack(pady=(0, 20)) 
    
    def create_field_row(self, parent, label_text, variable, help_text=None):
        """Məlumat sahəsi sətrini yaradır"""
        row_frame = tk.Frame(parent, bg=self.colors['white'])
        row_frame.pack(fill="x", pady=8)
        
        # Label
        tk.Label(row_frame, text=label_text, 
                bg=self.colors['white'], fg=self.colors['text_primary'], 
                font=('Segoe UI', 11, 'bold')).pack(anchor="w", pady=(0, 3))
        
        # Entry və help text
        entry_frame = tk.Frame(row_frame, bg=self.colors['white'])
        entry_frame.pack(fill="x")
        
        # Normal entry
        entry = tk.Entry(entry_frame, textvariable=variable, 
                font=('Segoe UI', 11), relief="solid", bd=1)
        entry.pack(side="left", fill="x", expand=True)
        
        # Dəyişiklik izləmə üçün event listener əlavə et
        def on_change(*args):
            self._mark_as_changed()
        
        variable.trace_add("write", on_change)
        
        if help_text:
            tk.Label(entry_frame, text=help_text, 
                    bg=self.colors['white'], fg=self.colors['text_secondary'], 
                    font=('Segoe UI', 8)).pack(side="right", padx=(10, 0))
    
    def create_date_field_row(self, parent, label_text, variable):
        """Tarix sahəsi sətrini yaradır (universal kalendar ilə)"""
        row_frame = tk.Frame(parent, bg=self.colors['white'])
        row_frame.pack(fill="x", pady=8)
        
        # Label
        tk.Label(row_frame, text=label_text, 
                bg=self.colors['white'], fg=self.colors['text_primary'], 
                font=('Segoe UI', 11, 'bold')).pack(anchor="w", pady=(0, 3))
        
        # Tarix sahəsi çərçivəsi
        date_frame = tk.Frame(row_frame, bg=self.colors['white'])
        date_frame.pack(fill="x")
        
        # Universal kalendar widget-i
        date_entry = DateEntry(date_frame, variable)
        date_entry.pack(side="left", fill="x", expand=True)
        
        # Dəyişiklik izləmə üçün event listener əlavə et
        def on_change(*args):
            self._mark_as_changed()
        
        variable.trace_add("write", on_change) 