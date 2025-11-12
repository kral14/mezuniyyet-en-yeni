# ui/employee_form_window.py

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import os
import shutil
from datetime import datetime
from PIL import Image, ImageTk
import database
import logging

# Universal kalendar import (nisbi yol ilə)
from .universal_calendar import DateEntry
from utils.text_formatter import format_name, format_full_name, format_employee_display_name, format_username

def create_azerbaijani_entry(parent, textvariable, **kwargs):
    """Azərbaycan hərfləri üçün xüsusi Entry widget yaradır"""
    entry = tk.Entry(parent, textvariable=textvariable, **kwargs)
    
    # Azərbaycan hərfləri üçün xüsusi event binding
    def on_key_press(event):
        # Debug məlumatları
        print(f"Key pressed: char='{event.char}', keysym='{event.keysym}', state={event.state}")
        
        # Klaviatura kombinasiyalarını yoxla
        if event.state & 0x4:  # Ctrl basılıdır
            if event.keysym == 'e' or event.char == 'e':
                # Ctrl+E = ə
                entry.insert(tk.INSERT, 'ə')
                return 'break'
            elif event.keysym == 'g' or event.char == 'g':
                # Ctrl+G = ğ
                entry.insert(tk.INSERT, 'ğ')
                return 'break'
            elif event.keysym == 'u' or event.char == 'u':
                # Ctrl+U = ü
                entry.insert(tk.INSERT, 'ü')
                return 'break'
            elif event.keysym == 'o' or event.char == 'o':
                # Ctrl+O = ö
                entry.insert(tk.INSERT, 'ö')
                return 'break'
            elif event.keysym == 's' or event.char == 's':
                # Ctrl+S = ş
                entry.insert(tk.INSERT, 'ş')
                return 'break'
            elif event.keysym == 'c' or event.char == 'c':
                # Ctrl+C = ç
                entry.insert(tk.INSERT, 'ç')
                return 'break'
            elif event.keysym == 'i' or event.char == 'i':
                # Ctrl+I = ı
                entry.insert(tk.INSERT, 'ı')
                return 'break'
        
        # Alt kombinasiyaları yoxla
        if event.state & 0x20000:  # Alt basılıdır
            if event.keysym == 'e' or event.char == 'e':
                # Alt+E = ə
                entry.insert(tk.INSERT, 'ə')
                return 'break'
            elif event.keysym == 'g' or event.char == 'g':
                # Alt+G = ğ
                entry.insert(tk.INSERT, 'ğ')
                return 'break'
            elif event.keysym == 'u' or event.char == 'u':
                # Alt+U = ü
                entry.insert(tk.INSERT, 'ü')
                return 'break'
            elif event.keysym == 'o' or event.char == 'o':
                # Alt+O = ö
                entry.insert(tk.INSERT, 'ö')
                return 'break'
            elif event.keysym == 's' or event.char == 's':
                # Alt+S = ş
                entry.insert(tk.INSERT, 'ş')
                return 'break'
            elif event.keysym == 'c' or event.char == 'c':
                # Alt+C = ç
                entry.insert(tk.INSERT, 'ç')
                return 'break'
            elif event.keysym == 'i' or event.char == 'i':
                # Alt+I = ı
                entry.insert(tk.INSERT, 'ı')
                return 'break'
        
        # Direkt ə hərfi yoxlaması
        if event.char == 'ə':
            entry.insert(tk.INSERT, 'ə')
            return 'break'
        
        # Sual işarəsi problemini həll et
        if event.char == '?':
            # Əgər sual işarəsi yazılırsa, ə hərfi olaraq dəyişdir
            entry.insert(tk.INSERT, 'ə')
            return 'break'
    
    entry.bind('<KeyPress>', on_key_press)
    
    # Focus olduqda xüsusi ayarlar
    def on_focus_in(event):
        # Entry focus olduqda encoding təyin et
        entry.configure(insertbackground='black')
        print("Entry focus oldu - Azərbaycan hərfləri aktiv")
    
    entry.bind('<FocusIn>', on_focus_in)
    
    return entry

class EmployeeFormWindow(tk.Frame):
    def __init__(self, parent, refresh_callback, employee_data=None, main_app_ref=None):
        super().__init__(parent)
        
        self.refresh_callback = refresh_callback
        self.employee_data = employee_data
        self.is_edit_mode = bool(employee_data)
        self.main_app_ref = main_app_ref
        self.profile_image_path = None
        self.original_image_path = None
        
        # Cari istifadəçinin rolunu yoxla
        if main_app_ref and hasattr(main_app_ref, 'current_user'):
            self.current_user = main_app_ref.current_user
            self.is_admin = self.current_user.get('role', '').strip() == 'admin'
        else:
            self.current_user = None
            self.is_admin = False

        # Dəyişiklik izləmə sistemi
        self.has_changes = False
        self.original_data = {}

        # Rəng sxemi
        self.colors = {
            'primary': '#007bff',
            'secondary': '#6c757d',
            'success': '#28a745',
            'danger': '#dc3545',
            'warning': '#ffc107',
            'info': '#17a2b8',
            'light': '#f8f9fa',
            'dark': '#343a40',
            'white': '#ffffff',
            'black': '#000000',
            'border': '#dee2e6',
            'text_primary': '#212529',
            'text_secondary': '#6c757d',
            'background': '#ffffff'
        }
        
        # Frame konfiqurasiyası
        self.configure(background=self.colors['background'])
        
        # Profil şəkilləri artıq lokal papkada deyil, veritabanında saxlanılır
        self.profile_images_dir = None
        
        # Widget-ləri yarat
        self.create_widgets()
        # İşçi məlumatlarını yüklə (widget-lər yaradıldıqdan sonra)
        self.load_employee_data()
        # Orijinal məlumatları saxla (məlumatlar yükləndikdən sonra)
        self._save_original_data()

    def _get_azerbaijani_font(self):
        """Azərbaycan dili üçün ən yaxşı fontu tapır"""
        import tkinter.font as tkFont
        
        # Azərbaycan hərflərini dəstəkləyən fontların siyahısı (prioritet sırası ilə)
        azerbaijani_fonts = [
            "Segoe UI",
            "Microsoft YaHei",
            "SimSun",
            "Arial Unicode MS",
            "Tahoma",
            "Verdana",
            "Arial",
            "Helvetica",
            "Times New Roman",
            "Calibri",
            "Cambria",
            "Georgia",
            "Trebuchet MS",
            "Lucida Sans Unicode",
            "Comic Sans MS"
        ]
        
        # Mövcud fontları yoxla
        available_fonts = list(tkFont.families())
        
        # Azərbaycan hərflərini dəstəkləyən fontu tap
        for font_name in azerbaijani_fonts:
            if font_name in available_fonts:
                return font_name
        
        # Əgər heç biri tapılmadısa, default font istifadə et
        return "TkDefaultFont"

    def _save_original_data(self):
        """Orijinal məlumatları saxlayır"""
        try:
            # Bütün dəyişən sahələri izlə
            self.original_data = {
                'first_name': getattr(self, 'first_name_var', tk.StringVar()).get() if hasattr(self, 'first_name_var') else '',
                'last_name': getattr(self, 'last_name_var', tk.StringVar()).get() if hasattr(self, 'last_name_var') else '',
                'father_name': getattr(self, 'father_name_var', tk.StringVar()).get() if hasattr(self, 'father_name_var') else '',
                'email': getattr(self, 'email_var', tk.StringVar()).get() if hasattr(self, 'email_var') else '',
                'phone': getattr(self, 'phone_var', tk.StringVar()).get() if hasattr(self, 'phone_var') else '',
                'birth_date': getattr(self, 'birth_date_var', tk.StringVar()).get() if hasattr(self, 'birth_date_var') else '',
                'address': getattr(self, 'address_var', tk.StringVar()).get() if hasattr(self, 'address_var') else '',
                'position': getattr(self, 'position_var', tk.StringVar()).get() if hasattr(self, 'position_var') else '',
                'department': getattr(self, 'department_var', tk.StringVar()).get() if hasattr(self, 'department_var') else '',
                'hire_date': getattr(self, 'hire_date_var', tk.StringVar()).get() if hasattr(self, 'hire_date_var') else '',
                'salary': getattr(self, 'salary_var', tk.StringVar()).get() if hasattr(self, 'salary_var') else '',
                'profile_image': self.profile_image_path,
                # Sistem tənzimləmələri
                'role': getattr(self, 'role_var', tk.StringVar()).get() if hasattr(self, 'role_var') else 'user',
                'vacation_days': getattr(self, 'vacation_days_var', tk.StringVar()).get() if hasattr(self, 'vacation_days_var') else '30',
                'max_sessions': getattr(self, 'max_sessions_var', tk.StringVar()).get() if hasattr(self, 'max_sessions_var') else '1',
                'username': getattr(self, 'username_var', tk.StringVar()).get() if hasattr(self, 'username_var') else ''
            }
            logging.info(f"Orijinal məlumatlar saxlandı: {self.original_data}")
        except Exception as e:
            logging.error(f"Orijinal məlumatları saxlayarkən xəta: {e}")
    
    def _check_for_changes(self):
        """Dəyişiklikləri yoxlayır"""
        try:
            current_data = {
                'first_name': getattr(self, 'first_name_var', tk.StringVar()).get() if hasattr(self, 'first_name_var') else '',
                'last_name': getattr(self, 'last_name_var', tk.StringVar()).get() if hasattr(self, 'last_name_var') else '',
                'father_name': getattr(self, 'father_name_var', tk.StringVar()).get() if hasattr(self, 'father_name_var') else '',
                'email': getattr(self, 'email_var', tk.StringVar()).get() if hasattr(self, 'email_var') else '',
                'phone': getattr(self, 'phone_var', tk.StringVar()).get() if hasattr(self, 'phone_var') else '',
                'birth_date': getattr(self, 'birth_date_var', tk.StringVar()).get() if hasattr(self, 'birth_date_var') else '',
                'address': getattr(self, 'address_var', tk.StringVar()).get() if hasattr(self, 'address_var') else '',
                'position': getattr(self, 'position_var', tk.StringVar()).get() if hasattr(self, 'position_var') else '',
                'department': getattr(self, 'department_var', tk.StringVar()).get() if hasattr(self, 'department_var') else '',
                'hire_date': getattr(self, 'hire_date_var', tk.StringVar()).get() if hasattr(self, 'hire_date_var') else '',
                'salary': getattr(self, 'salary_var', tk.StringVar()).get() if hasattr(self, 'salary_var') else '',
                'profile_image': self.profile_image_path,
                # Sistem tənzimləmələri
                'role': getattr(self, 'role_var', tk.StringVar()).get() if hasattr(self, 'role_var') else 'user',
                'vacation_days': getattr(self, 'vacation_days_var', tk.StringVar()).get() if hasattr(self, 'vacation_days_var') else '30',
                'max_sessions': getattr(self, 'max_sessions_var', tk.StringVar()).get() if hasattr(self, 'max_sessions_var') else '1',
                'username': getattr(self, 'username_var', tk.StringVar()).get() if hasattr(self, 'username_var') else ''
            }
            
            # Dəyişiklikləri yoxla
            for key in current_data:
                if key in self.original_data:
                    current_value = current_data[key]
                    original_value = self.original_data[key]
                    
                    if current_value != original_value:
                        self.has_changes = True
                        logging.info(f"Dəyişiklik tapıldı: {key} - '{original_value}' -> '{current_value}'")
                        return True
            
            self.has_changes = False
            return False
            
        except Exception as e:
            logging.error(f"Dəyişiklikləri yoxlayarkən xəta: {e}")
            return False
    
    def _mark_as_changed(self):
        """Dəyişiklik olduğunu qeyd edir"""
        self.has_changes = True
        logging.info("İşçi məlumatlarında dəyişiklik qeyd edildi")

    def create_widgets(self):
        """Ana widget-ləri yaradır"""
        # Ana container
        main_container = tk.Frame(self, background=self.colors['background'])
        main_container.pack(expand=True, fill="both", padx=20, pady=20)
        
        # Frame-in öz arxa fonunu da təyin et
        self.configure(background=self.colors['background'])
        
        # Başlıq
        self.create_header(main_container)
        
        # Məzmun bölməsi
        content_frame = tk.Frame(main_container, bg=self.colors['white'], relief="raised", bd=2)
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
    
    def create_header(self, parent):
        """Başlıq bölməsini yaradır"""
        header_frame = tk.Frame(parent, bg=self.colors['primary'], height=60)
        header_frame.pack(fill="x")
        header_frame.pack_propagate(False)
        
        # Geri qayıtma düyməsi (sol tərəf)
        azerbaijani_font = self._get_azerbaijani_font()
        back_btn = tk.Button(header_frame, text="← Geri", 
                            command=self.on_escape,
                            bg='#2980b9', fg=self.colors['white'], 
                            font=(azerbaijani_font, 11, 'bold'),
                            relief="flat", padx=12, pady=4, cursor="hand2")
        back_btn.pack(side="left", padx=15, pady=18)
        
        # Başlıq mətn (mərkəz) - seçilən işçinin adı ilə
        if self.is_edit_mode and self.employee_data:
            # Əvvəlcə name sahəsindən yoxla (tam ad)
            employee_name = self.employee_data.get('name', '')
            
            # Əgər name sahəsi yoxdursa, first_name və last_name-dən yarat
            if not employee_name:
                first_name = self.employee_data.get('first_name', '')
                last_name = self.employee_data.get('last_name', '')
                employee_name = format_full_name(first_name, last_name)
            
            # Əgər hələ də boşdursa, "Naməlum İşçi" yaz
            if not employee_name:
                employee_name = "Naməlum İşçi"
                
            title_text = f"👤 İŞÇİ DÜZƏLT: {employee_name}"
        else:
            title_text = "👤 YENİ İŞÇİ ƏLAVƏ ET"
            
        self.title_label = tk.Label(header_frame, 
                              text=title_text, 
                              bg=self.colors['primary'], fg=self.colors['white'],
                              font=(azerbaijani_font, 16, 'bold'))
        self.title_label.pack(expand=True)
        
        # Alt xətt
        separator = tk.Frame(header_frame, bg='#2980b9', height=3)
        separator.pack(fill="x", side="bottom")
    
    def on_escape(self):
        """Geri qayıtma funksiyası"""
        try:
            # Dəyişiklikləri yoxla
            has_changes = self._check_for_changes()
            
            if has_changes:
                # Dəyişiklik varsa, istifadəçidən təsdiq al
                result = messagebox.askyesnocancel(
                    "Dəyişikliklər",
                    "İşçi məlumatlarında dəyişikliklər var. Dəyişiklikləri saxlamaq istəyirsinizmi?",
                    icon='question'
                )
                
                if result is True:  # Bəli - saxlamaq istəyir
                    self.save()
                    logging.info("Dəyişikliklər saxlanıldı və əsas səhifəyə qayıtmaq lazımdır")
                    self.show_main_view(needs_refresh=True)
                        
                elif result is False:  # Xeyr - saxlamaq istəmir
                    logging.info("Dəyişikliklər saxlanılmadı, əsas səhifəyə qayıtmaq lazımdır")
                    self.show_main_view(needs_refresh=False)
                        
                else:  # Cancel - burada qal
                    logging.info("İstifadəçi geri qayıtmaqdan imtina etdi")
                    return
                    
            else:
                # Dəyişiklik yoxdursa, sadəcə geri qayıt
                logging.info("Dəyişiklik yoxdur, əsas səhifəyə qayıtmaq lazımdır")
                self.show_main_view(needs_refresh=False)
                
        except Exception as e:
            logging.error(f"Geri qayıtma zamanı xəta: {e}")
            self.show_main_view(needs_refresh=False)
    
    def show_main_view(self, needs_refresh=False):
        """Əsas səhifəyə qayıtmaq"""
        try:
            # Öz frame-ini gizlət
            self.pack_forget()
            
            # Əsas tətbiqə qayıt
            if self.main_app_ref and hasattr(self.main_app_ref, 'show_main_view'):
                self.main_app_ref.show_main_view(needs_refresh=needs_refresh)
            else:
                logging.error("main_app_ref tapılmadı və ya show_main_view metodu yoxdur")
                
        except Exception as e:
            logging.error(f"show_main_view zamanı xəta: {e}")
            # Xəta baş verdikdə də frame-i gizlət
            try:
                self.pack_forget()
            except:
                pass
    
    def create_left_panel(self, parent):
        """Sol panel məzmununu yaradır"""
        # Profil şəkli
        self.create_profile_image_section(parent)
        
        # İşçi məlumatları - profil pəncərəsi ilə eyni format
        self.create_employee_info_section(parent)
    
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
    
    def create_employee_info_section(self, parent):
        """İşçi məlumatları bölməsini yaradır - profil pəncərəsi ilə eyni format"""
        info_frame = tk.Frame(parent, bg=self.colors['white'])
        info_frame.pack(fill="x")
        
        # İşçi adı - profil pəncərəsindəki kimi
        tk.Label(info_frame, text="👤 İşçi Adı:", 
                bg=self.colors['white'], fg=self.colors['text_primary'], 
                font=('Tahoma', 11, 'bold')).pack(anchor="w", pady=(0, 5))
        
        # İşçi adı - profil pəncərəsindəki kimi
        employee_name = format_employee_display_name(self.employee_data) if self.employee_data else ''
        self.employee_name_var = tk.StringVar(value=employee_name)
        employee_name_entry = tk.Entry(info_frame, textvariable=self.employee_name_var, 
                                    font=('Tahoma', 11), state="readonly", 
                                    bg=self.colors['light'], fg=self.colors['text_primary'], 
                                    relief="solid", bd=1)
        employee_name_entry.pack(fill="x", pady=(0, 15))
        
        # Vəzifə - profil pəncərəsindəki "Rol" kimi
        tk.Label(info_frame, text="🔑 Vəzifə:", 
                bg=self.colors['white'], fg=self.colors['text_primary'], 
                font=('Tahoma', 11, 'bold')).pack(anchor="w", pady=(0, 5))
        
        self.position_display_var = tk.StringVar(value=self.employee_data.get('position', 'İşçi') if self.employee_data else 'İşçi')
        position_entry = tk.Entry(info_frame, textvariable=self.position_display_var, 
                                font=('Tahoma', 11), state="readonly",
                                bg=self.colors['light'], fg=self.colors['text_primary'], 
                                relief="solid", bd=1)
        position_entry.pack(fill="x", pady=(0, 15))
        
        # Email
        tk.Label(info_frame, text="📧 Email:", 
                bg=self.colors['white'], fg=self.colors['text_primary'], 
                font=('Tahoma', 11, 'bold')).pack(anchor="w", pady=(0, 5))
        
        self.email_var = tk.StringVar(value=self.employee_data.get('email', '') if self.employee_data else '')
        email_entry = tk.Entry(info_frame, textvariable=self.email_var, 
                            font=('Tahoma', 11),
                            bg=self.colors['white'], fg=self.colors['text_primary'], 
                            relief="solid", bd=1)
        email_entry.pack(fill="x", pady=(0, 15))
        
        # Dəyişiklik izləmə üçün event listener əlavə et
        def on_change(*args):
            self._mark_as_changed()
        
        self.email_var.trace_add("write", on_change)
    
    def create_right_panel(self, parent):
        """Sağ panel məzmununu yaradır - profil pəncərəsi ilə eyni format"""
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
        
        # Sistem tənzimləmələri tab - yeni əlavə edildi
        system_tab = tk.Frame(notebook, bg=self.colors['white'])
        notebook.add(system_tab, text="🔧 Sistem Tənzimləmələri")
        self.create_system_settings_tab(system_tab)
        
        # Şifrə dəyişdirmə tab - profil pəncərəsindəki kimi
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
        self.first_name_var = tk.StringVar(value=self.employee_data.get('first_name', '') if self.employee_data else '')
        self.create_field_row(fields_frame, "Ad:", self.first_name_var)
        
        # Soyad
        self.last_name_var = tk.StringVar(value=self.employee_data.get('last_name', '') if self.employee_data else '')
        self.create_field_row(fields_frame, "Soyad:", self.last_name_var)
        
        # Ata adı - profil pəncərəsindəki kimi
        self.father_name_var = tk.StringVar(value=self.employee_data.get('father_name', '') if self.employee_data else '')
        self.create_field_row(fields_frame, "Ata adı:", self.father_name_var)
        
        # Doğum tarixi
        birth_date_value = self.employee_data.get('birth_date', '1990-01-01') if self.employee_data else '1990-01-01'
        self.birth_date_var = tk.StringVar(value=birth_date_value)
        self.create_date_field_row(fields_frame, "Doğum tarixi:", self.birth_date_var)
        
        # Telefon
        self.phone_var = tk.StringVar(value=self.employee_data.get('phone', '') if self.employee_data else '')
        self.create_field_row(fields_frame, "Telefon:", self.phone_var)
        
        # Ünvan - profil pəncərəsindəki kimi
        self.address_var = tk.StringVar(value=self.employee_data.get('address', '') if self.employee_data else '')
        self.create_field_row(fields_frame, "🏠 Ünvan:", self.address_var)
        
        # Düymələr
        button_frame = tk.Frame(scrollable_frame, bg=self.colors['white'])
        button_frame.pack(pady=20)
        
        tk.Button(button_frame, text="💾 Yadda Saxla", command=self.save,
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
        
        # FIN kodu (YENİ)
        fin_code_value = self.employee_data.get('fin_code', '') if self.employee_data else ''
        self.fin_code_var = tk.StringVar(value=fin_code_value)
        self.create_field_row(fields_frame, "🆔 FIN Kodu:", self.fin_code_var, "Şəxsiyyət vəsqiqəsindəki FIN kodu")
        
        # Şöbə seçimi (YENİ - combobox)
        tk.Label(fields_frame, text="🏢 Şöbə:", 
                bg=self.colors['white'], fg=self.colors['text_primary'], 
                font=('Tahoma', 11, 'bold')).pack(anchor="w", pady=(15, 5))
        
        self.department_var = tk.StringVar(value=self.employee_data.get('department', '') if self.employee_data else '')
        # Adi istifadəçilər üçün passiv vəziyyət
        combo_state = "readonly" if self.is_admin else "disabled"
        self.department_combo = ttk.Combobox(fields_frame, textvariable=self.department_var, 
                                           font=('Tahoma', 11), state=combo_state, width=40)
        self.department_combo.pack(fill="x", pady=(0, 15))
        
        # Vəzifə seçimi (YENİ - combobox)
        tk.Label(fields_frame, text="👔 Vəzifə:", 
                bg=self.colors['white'], fg=self.colors['text_primary'], 
                font=('Tahoma', 11, 'bold')).pack(anchor="w", pady=(15, 5))
        
        self.position_var = tk.StringVar(value=self.employee_data.get('position', '') if self.employee_data else '')
        # Adi istifadəçilər üçün passiv vəziyyət
        self.position_combo = ttk.Combobox(fields_frame, textvariable=self.position_var, 
                                         font=('Tahoma', 11), state=combo_state, width=40)
        self.position_combo.pack(fill="x", pady=(0, 15))
        
        # İşə qəbul tarixi
        hire_date_value = self.employee_data.get('hire_date', '2020-01-01') if self.employee_data else '2020-01-01'
        self.hire_date_var = tk.StringVar(value=hire_date_value)
        self.create_date_field_row(fields_frame, "İşə qəbul:", self.hire_date_var)
        
        # Maaş - profil pəncərəsindəki kimi
        salary_value = self.employee_data.get('salary', '') if self.employee_data else ''
        if salary_value:
            salary_value = str(salary_value)
        self.salary_var = tk.StringVar(value=salary_value)
        self.create_field_row(fields_frame, "💰 Maaş:", self.salary_var)
        
        # Düymələr
        button_frame = tk.Frame(scrollable_frame, bg=self.colors['white'])
        button_frame.pack(pady=20)
        
        tk.Button(button_frame, text="💾 Yadda Saxla", command=self.save,
                bg=self.colors['success'], fg=self.colors['white'], font=('Segoe UI', 11, 'bold'),
                relief="flat", padx=25, pady=8, cursor="hand2").pack(side="left", padx=5)
        
        # Scrollbar və canvas
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Şöbə və vəzifə məlumatlarını yüklə
        self.load_department_and_position_data()
    
    def load_department_and_position_data(self):
        """Şöbə və vəzifə məlumatlarını yükləyir"""
        try:
            # Əvvəlcə veritabanından məlumatları almağa çalış
            departments = []
            positions = []
            
            try:
                from database.departments_positions_queries import get_departments_for_combo, get_positions_for_combo
                departments = get_departments_for_combo()
                positions = get_positions_for_combo()
                print(f"DEBUG: Veritabanından şöbələr: {departments}")
                print(f"DEBUG: Veritabanından vəzifələr: {positions}")
            except Exception as db_error:
                print(f"DEBUG: Veritabanından məlumat alınmadı: {db_error}")
                departments = []
                positions = []
            
            # Əgər veritabanı boşdursa, default məlumatlar əlavə et
            if not departments:
                departments = [
                    (1, "İnsan Resursları"),
                    (2, "Maliyyə"),
                    (3, "Texniki"),
                    (4, "Marketinq"),
                    (5, "Satış")
                ]
                print("DEBUG: Default şöbələr əlavə edildi")
            
            if not positions:
                positions = [
                    (1, "Müdür"),
                    (2, "Mütəxəssis"),
                    (3, "Operator"),
                    (4, "Məsləhətçi"),
                    (5, "Analitik")
                ]
                print("DEBUG: Default vəzifələr əlavə edildi")
            
            # Şöbə seçimləri - sadəcə adları
            dept_options = [dept[1] for dept in departments]
            if not dept_options:
                dept_options = ["— Məlumat yoxdur —"]
            
            # Vəzifə seçimləri - sadəcə adları
            pos_options = [pos[1] for pos in positions]
            if not pos_options:
                pos_options = ["— Məlumat yoxdur —"]
            
            # Combo box-lara dəyərləri təyin et
            self.department_combo['values'] = dept_options
            self.position_combo['values'] = pos_options
            
            print(f"DEBUG: Combo box dəyərləri - Şöbələr: {dept_options}, Vəzifələr: {pos_options}")
            
            # Mövcud seçimləri təyin et
            if self.employee_data:
                print(f"DEBUG: İşçi məlumatları: {self.employee_data}")
                
                # Şöbə seçimi - əvvəlcə department_id ilə yoxla
                if 'department_id' in self.employee_data and self.employee_data['department_id']:
                    print(f"DEBUG: department_id ilə axtarış: {self.employee_data['department_id']}")
                    # department_id ilə şöbə adını tap
                    for dept in departments:
                        if dept[0] == self.employee_data['department_id']:
                            self.department_var.set(dept[1])
                            print(f"DEBUG: Şöbə tapıldı: {dept[1]}")
                            break
                elif 'department' in self.employee_data and self.employee_data['department']:
                    current_dept = self.employee_data['department']
                    print(f"DEBUG: department adı ilə axtarış: {current_dept}")
                    if current_dept in dept_options:
                        self.department_var.set(current_dept)
                        print(f"DEBUG: Şöbə tapıldı: {current_dept}")
                    else:
                        # Əgər mövcud deyilsə, əlavə et
                        dept_options.append(current_dept)
                        self.department_combo['values'] = dept_options
                        self.department_var.set(current_dept)
                        print(f"DEBUG: Yeni şöbə əlavə edildi: {current_dept}")
                
                # Vəzifə seçimi - əvvəlcə position_id ilə yoxla
                if 'position_id' in self.employee_data and self.employee_data['position_id']:
                    print(f"DEBUG: position_id ilə axtarış: {self.employee_data['position_id']}")
                    # position_id ilə vəzifə adını tap
                    for pos in positions:
                        if pos[0] == self.employee_data['position_id']:
                            self.position_var.set(pos[1])
                            print(f"DEBUG: Vəzifə tapıldı: {pos[1]}")
                            break
                elif 'position' in self.employee_data and self.employee_data['position']:
                    current_pos = self.employee_data['position']
                    print(f"DEBUG: position adı ilə axtarış: {current_pos}")
                    if current_pos in pos_options:
                        self.position_var.set(current_pos)
                        print(f"DEBUG: Vəzifə tapıldı: {current_pos}")
                    else:
                        # Əgər mövcud deyilsə, əlavə et
                        pos_options.append(current_pos)
                        self.position_combo['values'] = pos_options
                        self.position_var.set(current_pos)
                        print(f"DEBUG: Yeni vəzifə əlavə edildi: {current_pos}")
                
                print(f"DEBUG: Final seçimlər - Şöbə: {self.department_var.get()}, Vəzifə: {self.position_var.get()}")
            
        except Exception as e:
            print(f"Şöbə və vəzifə məlumatları yüklənərkən xəta: {e}")
            # Fallback - ən azı boş seçimlər təyin et
            self.department_combo['values'] = ["— Məlumat yoxdur —"]
            self.position_combo['values'] = ["— Məlumat yoxdur —"]
    
    def create_system_settings_tab(self, parent):
        """Sistem tənzimləmələri tab-ını yaradır"""
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
        
        # Başlıq
        tk.Label(fields_frame, text="🔧 Sistem Tənzimləmələri", 
                bg=self.colors['white'], fg=self.colors['text_primary'], 
                font=('Segoe UI', 14, 'bold')).pack(pady=(0, 20))
        
        # İstifadəçi rolunu dəyişdirmə
        tk.Label(fields_frame, text="👑 İstifadəçi Rolunu Dəyişdirmə", 
                bg=self.colors['white'], fg=self.colors['text_primary'], 
                font=('Segoe UI', 12, 'bold')).pack(anchor="w", pady=(10, 5))
        
        # Rol seçimi
        self.role_var = tk.StringVar(value=self.employee_data.get('role', 'user') if self.employee_data else 'user')
        role_frame = tk.Frame(fields_frame, bg=self.colors['white'])
        role_frame.pack(fill="x", pady=(0, 15))
        
        tk.Radiobutton(role_frame, text="👤 Adi İstifadəçi", variable=self.role_var, value="user",
                      bg=self.colors['white'], fg=self.colors['text_primary'], 
                      font=('Segoe UI', 10), selectcolor=self.colors['light']).pack(anchor="w")
        
        tk.Radiobutton(role_frame, text="👑 Admin", variable=self.role_var, value="admin",
                      bg=self.colors['white'], fg=self.colors['text_primary'], 
                      font=('Segoe UI', 10), selectcolor=self.colors['light']).pack(anchor="w")
        
        # Məzuniyyət günlərini dəyişdirmə
        tk.Label(fields_frame, text="📅 Məzuniyyət Günlərini Dəyişdirmə", 
                bg=self.colors['white'], fg=self.colors['text_primary'], 
                font=('Segoe UI', 12, 'bold')).pack(anchor="w", pady=(10, 5))
        
        # Məzuniyyət günləri
        vacation_days_value = self.employee_data.get('total_days', 30) if self.employee_data else 30
        self.vacation_days_var = tk.StringVar(value=str(vacation_days_value))
        self.create_field_row(fields_frame, "Məzuniyyət günləri:", self.vacation_days_var, 
                             "İl ərzində istifadə edə biləcəyi məzuniyyət günlərinin sayı")
        
        # Sessiya sayını dəyişdirmə
        tk.Label(fields_frame, text="🖥️ Sessiya Sayını Dəyişdirmə", 
                bg=self.colors['white'], fg=self.colors['text_primary'], 
                font=('Segoe UI', 12, 'bold')).pack(anchor="w", pady=(10, 5))
        
        # Maksimum sessiya sayı
        max_sessions_value = self.employee_data.get('max_sessions', 1) if self.employee_data else 1
        self.max_sessions_var = tk.StringVar(value=str(max_sessions_value))
        self.create_field_row(fields_frame, "Maksimum sessiya sayı:", self.max_sessions_var,
                             "Eyni anda açıq saxlaya biləcəyi sessiya sayı")
        
        # İstifadəçi adını dəyişdirmə
        tk.Label(fields_frame, text="👤 İstifadəçi Adını Dəyişdirmə", 
                bg=self.colors['white'], fg=self.colors['text_primary'], 
                font=('Segoe UI', 12, 'bold')).pack(anchor="w", pady=(10, 5))
        
        # İstifadəçi adı
        username_value = self.employee_data.get('username', '') if self.employee_data else ''
        self.username_var = tk.StringVar(value=username_value)
        self.create_field_row(fields_frame, "İstifadəçi adı:", self.username_var,
                             "Sistemə daxil olmaq üçün istifadə etdiyi ad")
        
        # Təsdiq düyməsi
        button_frame = tk.Frame(scrollable_frame, bg=self.colors['white'])
        button_frame.pack(pady=20)
        
        tk.Button(button_frame, text="💾 Sistem Tənzimləmələrini Saxla", command=self.save_system_settings,
                bg=self.colors['success'], fg=self.colors['white'], font=('Segoe UI', 11, 'bold'),
                relief="flat", padx=25, pady=8, cursor="hand2").pack(side="left", padx=5)
        
        # Scrollbar və canvas
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
    
    def create_password_tab(self, parent):
        """Şifrə dəyişdirmə tab-ını yaradır - profil pəncərəsindəki kimi"""
        # Mərkəz çərçivəsi
        center_frame = tk.Frame(parent, bg=self.colors['white'])
        center_frame.pack(expand=True, fill="both")
        
        # Şifrə dəyişdirmə çərçivəsi
        password_frame = tk.Frame(center_frame, bg=self.colors['light'], relief="raised", bd=3)
        password_frame.pack(expand=True, padx=50, pady=50)
        
        # Başlıq
        tk.Label(password_frame, text="🔒 Admin Şifrə Dəyişdirmə", 
                bg=self.colors['light'], fg=self.colors['text_primary'], 
                font=('Segoe UI', 14, 'bold')).pack(pady=(20, 15))
        
        # Admin məlumatı
        tk.Label(password_frame, text="ℹ️ Admin olaraq istənilən işçinin şifrəsini dəyişə bilərsiniz", 
                bg=self.colors['light'], fg=self.colors['text_secondary'], 
                font=('Segoe UI', 10)).pack(anchor="w", padx=20, pady=(0, 15))
        
        # Admin üçün cari şifrə sahəsi gizlədilir
        # tk.Label(password_frame, text="Cari şifrə:", 
        #         bg=self.colors['light'], fg=self.colors['text_primary'], 
        #         font=('Segoe UI', 11, 'bold')).pack(anchor="w", padx=20)
        
        self.current_password_var = tk.StringVar()
        # tk.Entry(password_frame, textvariable=self.current_password_var, show="*", 
        #         font=('Segoe UI', 11), width=25, relief="solid", bd=1).pack(pady=(5, 10), padx=20)
        
        # Yeni şifrə
        tk.Label(password_frame, text="Yeni şifrə:", 
                bg=self.colors['light'], fg=self.colors['text_primary'], 
                font=('Tahoma', 11, 'bold')).pack(anchor="w", padx=20)
        
        self.new_password_var = tk.StringVar()
        tk.Entry(password_frame, textvariable=self.new_password_var, show="*", 
                font=('Tahoma', 11), width=25, relief="solid", bd=1).pack(pady=(5, 10), padx=20)
        
        # Şifrə təsdiq
        tk.Label(password_frame, text="Şifrə təsdiq:", 
                bg=self.colors['light'], fg=self.colors['text_primary'], 
                font=('Tahoma', 11, 'bold')).pack(anchor="w", padx=20)
        
        self.confirm_password_var = tk.StringVar()
        tk.Entry(password_frame, textvariable=self.confirm_password_var, show="*", 
                font=('Tahoma', 11), width=25, relief="solid", bd=1).pack(pady=(5, 20), padx=20)
        
        # Düymə
        tk.Button(password_frame, text="🔐 Şifrəni Dəyiş", command=self.change_password,
                 bg=self.colors['danger'], fg=self.colors['white'], font=('Segoe UI', 11, 'bold'),
                 relief="flat", padx=25, pady=8, cursor="hand2").pack(pady=(0, 20))
    
    def save_system_settings(self):
        """Sistem tənzimləmələrini saxlayır"""
        try:
            # Məlumatları al
            new_role = self.role_var.get()
            new_vacation_days = self.vacation_days_var.get().strip()
            new_max_sessions = self.max_sessions_var.get().strip()
            new_username = self.username_var.get().strip()
            
            # Validasiya
            if not new_vacation_days or not new_max_sessions or not new_username:
                messagebox.showerror("Xəta", "Bütün sahələri doldurun!")
                return
            
            try:
                vacation_days = int(new_vacation_days)
                max_sessions = int(new_max_sessions)
            except ValueError:
                messagebox.showerror("Xəta", "Məzuniyyət günləri və sessiya sayı rəqəm olmalıdır!")
                return
            
            if vacation_days < 0 or vacation_days > 365:
                messagebox.showerror("Xəta", "Məzuniyyət günləri 0-365 arasında olmalıdır!")
                return
            
            if max_sessions < 1 or max_sessions > 100:
                messagebox.showerror("Xəta", "Sessiya sayı 1-100 arasında olmalıdır!")
                return
            
            # İstifadəçi adının unikallığını yoxla (əgər dəyişdirilibsə)
            if new_username != self.employee_data.get('username', ''):
                if database.check_if_username_exists(new_username):
                    messagebox.showerror("Xəta", "Bu istifadəçi adı artıq mövcuddur!")
                    return
            
            # Sistem tənzimləmələrini yenilə
            success = database.update_employee_system_settings(
                self.employee_data['id'],
                new_role,
                vacation_days,
                max_sessions,
                new_username
            )
            
            if success:
                messagebox.showinfo("Uğurlu", "Sistem tənzimləmələri uğurla yeniləndi!")
                # İşçi məlumatlarını yenilə
                self.employee_data.update({
                    'role': new_role,
                    'total_days': vacation_days,
                    'umumi_gun': vacation_days,  # umumi_gun sahəsini də yenilə
                    'max_sessions': max_sessions,
                    'username': new_username
                })
                # Orijinal məlumatları yenilə
                self._save_original_data()
            else:
                messagebox.showerror("Xəta", "Sistem tənzimləmələri yenilənərkən xəta baş verdi!")
                
        except Exception as e:
            messagebox.showerror("Xəta", f"Sistem tənzimləmələri saxlanarkən xəta baş verdi: {str(e)}")
    
    def change_password(self):
        """Admin işçilərin şifrəsini cari şifrə bilmədən dəyişir"""
        current_password = self.current_password_var.get()
        new_password = self.new_password_var.get()
        confirm_password = self.confirm_password_var.get()
        
        # Admin işçilərin şifrəsini dəyişəndə cari şifrə tələb olunmur
        if not new_password or not confirm_password:
            messagebox.showerror("Xəta", "Yeni şifrə və təsdiq sahələri doldurulmalıdır.")
            return
            
        if new_password != confirm_password:
            messagebox.showerror("Xəta", "Yeni şifrələr eyni deyil.")
            return
            
        # Minimum şifrə uzunluğu məhdudiyyətini aradan qaldırırıq
        if len(new_password) < 1:
            messagebox.showerror("Xəta", "Şifrə boş ola bilməz.")
            return
        
        # Admin işçilərin şifrəsini cari şifrə yoxlamadan dəyişir
        try:
            import database
            
            # ID-ni tapmaq üçün müxtəlif variantları yoxlayırıq
            employee_id = None
            if 'id' in self.employee_data:
                employee_id = self.employee_data['id']
            elif 'db_id' in self.employee_data:
                employee_id = self.employee_data['db_id']
            elif 'employee_id' in self.employee_data:
                employee_id = self.employee_data['employee_id']
            
            if not employee_id:
                messagebox.showerror("Xəta", "İşçi ID-si tapılmadı!")
                return
                
            success = database.change_employee_password_admin(employee_id, new_password)
            if success:
                messagebox.showinfo("Uğurlu", "İşçi şifrəsi uğurla dəyişdirildi!")
            else:
                messagebox.showerror("Xəta", "Şifrə dəyişdirilərkən xəta baş verdi!")
        except Exception as e:
            messagebox.showerror("Xəta", f"Şifrə dəyişdirilərkən xəta: {str(e)}")
        
        # Şifrə sahələrini təmizlə
        self.current_password_var.set("")
        self.new_password_var.set("")
        self.confirm_password_var.set("")
    
    def create_field_row(self, parent, label_text, variable, help_text=None):
        """Məlumat sahəsi sətrini yaradır"""
        row_frame = tk.Frame(parent, bg=self.colors['white'])
        row_frame.pack(fill="x", pady=8)
        
        # Label
        tk.Label(row_frame, text=label_text, 
                bg=self.colors['white'], fg=self.colors['text_primary'], 
                font=('Tahoma', 11, 'bold')).pack(anchor="w", pady=(0, 3))
        
        # Entry və help text
        entry_frame = tk.Frame(row_frame, bg=self.colors['white'])
        entry_frame.pack(fill="x")
        
        # Azərbaycan hərfləri üçün xüsusi Entry widget
        entry = create_azerbaijani_entry(entry_frame, variable, 
                font=('Tahoma', 11), relief="solid", bd=1,
                insertbackground='black', selectbackground='#007bff', selectforeground='white')
        entry.pack(side="left", fill="x", expand=True)
        
        # Dəyişiklik izləmə üçün event listener əlavə et
        def on_change(*args):
            self._mark_as_changed()
        
        variable.trace_add("write", on_change)
        
        if help_text:
            tk.Label(entry_frame, text=help_text, 
                    bg=self.colors['white'], fg=self.colors['text_secondary'], 
                    font=('Tahoma', 8)).pack(side="right", padx=(10, 0))
    
    def create_date_field_row(self, parent, label_text, variable):
        """Tarix sahəsi sətrini yaradır (universal kalendar ilə)"""
        row_frame = tk.Frame(parent, bg=self.colors['white'])
        row_frame.pack(fill="x", pady=8)
        
        # Label
        tk.Label(row_frame, text=label_text, 
                bg=self.colors['white'], fg=self.colors['text_primary'], 
                font=('Tahoma', 11, 'bold')).pack(anchor="w", pady=(0, 3))
        
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
    
    def select_image(self):
        """Şəkil seçmə dialoqu"""
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
                
            except Exception as e:
                messagebox.showerror("Xəta", f"Şəkil yüklənərkən xəta: {e}")
                
    def load_profile_image(self, image_path, is_base64=False):
        """Profil şəkli yükləyir - base64 formatında"""
        try:
            if image_path:
                if is_base64 or len(image_path) > 100:  # Base64 string uzundur
                    # Base64-dan şəkli decode et
                    import base64
                    from io import BytesIO
                    img_data = base64.b64decode(image_path)
                    image = Image.open(BytesIO(img_data))
                    image = image.resize((150, 150), Image.Resampling.LANCZOS)
                    photo = ImageTk.PhotoImage(image)
                    
                    self.image_label.configure(image=photo, text="")
                    self.image_label.image = photo
                    self.original_image_path = image_path  # Base64 string saxlanır
                    logging.info("Şəkil base64 formatında yükləndi")
                elif os.path.exists(image_path):
                    # Köhnə lokal fayllar üçün
                    image = Image.open(image_path)
                    image = image.resize((150, 150), Image.Resampling.LANCZOS)
                    photo = ImageTk.PhotoImage(image)
                    
                    self.image_label.configure(image=photo, text="")
                    self.image_label.image = photo
                    self.original_image_path = image_path
                else:
                    self.image_label.configure(image="", text="📷\nŞəkil yoxdur")
                    self.original_image_path = None
            else:
                self.image_label.configure(image="", text="📷\nŞəkil yoxdur")
                self.original_image_path = None
        except Exception as e:
            self.image_label.configure(image="", text="📷\nŞəkil yüklənə bilmədi")
            logging.error(f"Şəkil yükləmə xətası: {e}")
                
    def remove_image(self):
        """Profil şəkli silir"""
        self.image_label.configure(image="", text="📷\nŞəkil yoxdur")
        self.profile_image_path = None
        self.original_image_path = None
        self._mark_as_changed()  # Dəyişiklik qeyd et
    
    def load_employee_data(self):
        """İşçi məlumatlarını yükləyir"""
        if self.employee_data:
            logging.info(f"İşçi məlumatları yüklənir: {self.employee_data}")
            print(f"DEBUG: İşçi məlumatları yüklənir: {self.employee_data}")
            
            # Başlığı yenilə (məlumatlar yüklənməzdən əvvəl)
            self.update_header_title()
            
            # Mövcud şəkli yüklə
            if 'profile_image' in self.employee_data and self.employee_data['profile_image']:
                self.load_profile_image(self.employee_data['profile_image'])
            
            # Bütün sahələrə işçi məlumatlarını yüklə
            try:
                # Şəxsi məlumatlar
                if hasattr(self, 'first_name_var'):
                    self.first_name_var.set(self.employee_data.get('first_name', ''))
                if hasattr(self, 'last_name_var'):
                    self.last_name_var.set(self.employee_data.get('last_name', ''))
                if hasattr(self, 'father_name_var'):
                    self.father_name_var.set(self.employee_data.get('father_name', ''))
                if hasattr(self, 'email_var'):
                    self.email_var.set(self.employee_data.get('email', ''))
                if hasattr(self, 'phone_var'):
                    self.phone_var.set(self.employee_data.get('phone_number', ''))
                if hasattr(self, 'birth_date_var'):
                    birth_date = self.employee_data.get('birth_date', '')
                    if birth_date and birth_date != 'None':
                        self.birth_date_var.set(birth_date)
                if hasattr(self, 'address_var'):
                    self.address_var.set(self.employee_data.get('address', ''))
                
                # İş məlumatları
                if hasattr(self, 'fin_code_var'):
                    self.fin_code_var.set(self.employee_data.get('fin_code', ''))
                if hasattr(self, 'hire_date_var'):
                    hire_date = self.employee_data.get('hire_date', '')
                    if hire_date and hire_date != 'None':
                        self.hire_date_var.set(hire_date)
                if hasattr(self, 'salary_var'):
                    self.salary_var.set(self.employee_data.get('salary', ''))
                
                # Şöbə və vəzifə məlumatlarını yüklə (combobox-lar yaradıldıqdan sonra)
                if hasattr(self, 'load_department_and_position_data'):
                    self.load_department_and_position_data()
                
                # Sistem tənzimləmələri sahələrini yüklə
                if hasattr(self, 'role_var'):
                    self.role_var.set(self.employee_data.get('role', 'user'))
                if hasattr(self, 'vacation_days_var'):
                    # Əvvəlcə umumi_gun sahəsini yoxla, sonra total_days
                    vacation_days = self.employee_data.get('umumi_gun', self.employee_data.get('total_days', 30))
                    self.vacation_days_var.set(str(vacation_days))
                if hasattr(self, 'max_sessions_var'):
                    max_sessions = self.employee_data.get('max_sessions', 1)
                    self.max_sessions_var.set(str(max_sessions))
                if hasattr(self, 'username_var'):
                    self.username_var.set(self.employee_data.get('username', ''))
                
                logging.info(f"İşçi məlumatları sahələrə yükləndi: {self.employee_data.get('first_name', '')} {self.employee_data.get('last_name', '')}")
                logging.info(f"Sistem tənzimləmələri yükləndi: role={self.employee_data.get('role', 'user')}, vacation_days={self.employee_data.get('umumi_gun', self.employee_data.get('total_days', 30))}, max_sessions={self.employee_data.get('max_sessions', 1)}")
                
                # Başlığı yenidən yenilə (məlumatlar yükləndikdən sonra)
                self.update_header_title()
                
            except Exception as e:
                logging.error(f"İşçi məlumatları sahələrə yüklənərkən xəta: {e}")
                messagebox.showerror("Xəta", f"İşçi məlumatları yüklənərkən xəta: {e}")
            
            logging.info(f"İşçi məlumatları yükləndi: {self.employee_data.get('first_name', '')} {self.employee_data.get('last_name', '')}")
    
    def _load_employee_data(self):
        """İşçi məlumatlarını yenidən yükləyir (daxili funksiya)"""
        self.load_employee_data()
    
    def update_header_title(self):
        """Başlığı yeniləyir"""
        if hasattr(self, 'title_label') and self.employee_data:
            # Əvvəlcə name sahəsindən yoxla (tam ad)
            employee_name = self.employee_data.get('name', '')
            
            # Əgər name sahəsi yoxdursa, first_name və last_name-dən yarat
            if not employee_name:
                first_name = self.employee_data.get('first_name', '')
                last_name = self.employee_data.get('last_name', '')
                employee_name = format_full_name(first_name, last_name)
            
            # Əgər hələ də boşdursa, "Naməlum İşçi" yaz
            if not employee_name:
                employee_name = "Naməlum İşçi"
            
            title_text = f"👤 İŞÇİ DÜZƏLT: {employee_name}"
            self.title_label.config(text=title_text)
            logging.info(f"Başlıq yeniləndi: {title_text}")
            logging.info(f"İşçi adı: '{employee_name}'")
    
    def _extract_id_from_combobox(self, combo_value):
        """Combobox dəyərindən ID-ni çıxarır"""
        if not combo_value or not combo_value.strip():
            return None
        
        # Əgər "— Məlumat yoxdur —" seçilibsə, None qaytar
        if combo_value.strip() == "— Məlumat yoxdur —":
            return None
            
        try:
            # Əvvəlcə "ID - Name" formatını yoxla
            parts = combo_value.strip().split(" - ", 1)
            if len(parts) == 2:
                return int(parts[0])
            
            # Əgər sadəcə ad varsa, veritabanından real ID-ləri al
            name = combo_value.strip()
            
            try:
                from database.departments_positions_queries import get_departments_for_combo, get_positions_for_combo
                
                # Şöbələrdən ID tap
                departments = get_departments_for_combo()
                for dept_id, dept_name in departments:
                    if dept_name == name:
                        print(f"DEBUG: Şöbə tapıldı: {name} -> ID: {dept_id}")
                        return dept_id
                
                # Vəzifələrdən ID tap
                positions = get_positions_for_combo()
                for pos_id, pos_name in positions:
                    if pos_name == name:
                        print(f"DEBUG: Vəzifə tapıldı: {name} -> ID: {pos_id}")
                        return pos_id
                
                print(f"DEBUG: '{name}' adı veritabanında tapılmadı")
                return None
                
            except Exception as db_error:
                print(f"DEBUG: Veritabanından ID alınmadı: {db_error}")
                return None
            
        except (ValueError, IndexError):
            return None

    def save(self):
        """Məlumatları saxlayır"""
        try:
            # Validasiya
            if not self.first_name_var.get().strip():
                messagebox.showerror("Xəta", "Ad sahəsi məcburidir.")
                return
            
            if not self.last_name_var.get().strip():
                messagebox.showerror("Xəta", "Soyad sahəsi məcburidir.")
                return
            
            # Combobox-lardan ID-ləri çıxar
            department_id = self._extract_id_from_combobox(self.department_var.get())
            position_id = self._extract_id_from_combobox(self.position_var.get())
            
            print(f"DEBUG: Combo box dəyərləri - Şöbə: '{self.department_var.get()}', Vəzifə: '{self.position_var.get()}'")
            print(f"DEBUG: Çıxarılan ID-lər - department_id: {department_id}, position_id: {position_id}")
            
            # Məlumatları topla
            employee_data = {
                'first_name': self.first_name_var.get().strip(),
                'last_name': self.last_name_var.get().strip(),
                'father_name': self.father_name_var.get().strip(),
                'email': self.email_var.get().strip(),
                'phone_number': self.phone_var.get().strip(),
                'birth_date': self.birth_date_var.get().strip() if self.birth_date_var.get().strip() else None,
                'address': self.address_var.get().strip(),
                'fin_code': self.fin_code_var.get().strip(),
                'department_id': department_id,
                'position_id': position_id,
                'hire_date': self.hire_date_var.get().strip() if self.hire_date_var.get().strip() else None,
                'salary': self.salary_var.get().strip(),
                'profile_image': self.profile_image_path
            }
            
            print(f"DEBUG: Saxlanılacaq məlumatlar: {employee_data}")
            print(f"DEBUG: department_id: {department_id}")
            print(f"DEBUG: position_id: {position_id}")
            print(f"DEBUG: fin_code: {self.fin_code_var.get().strip()}")
            
            # Veritabanına yaz
            if self.is_edit_mode:
                # Mövcud işçini yenilə
                print(f"DEBUG: update_employee_full çağırıldı - emp_id: {self.employee_data['id']}, employee_data: {employee_data}")
                success = database.update_employee_full(self.employee_data['id'], employee_data)
                if success:
                    # Yenilənmiş məlumatları veritabanından yüklə
                    updated_employee = database.get_user_by_id(self.employee_data['id'])
                    if updated_employee:
                        self.employee_data = updated_employee
                        self._load_employee_data()  # Formu yenilənmiş məlumatlarla yenidən yüklə
                    messagebox.showinfo("Uğurlu", "İşçi məlumatları uğurla yeniləndi!")
                else:
                    messagebox.showerror("Xəta", "İşçi məlumatları yenilənərkən xəta baş verdi!")
                    return
            else:
                # Yeni işçi yarat
                success = database.create_new_user(
                    name=format_full_name(employee_data['first_name'], employee_data['last_name']),
                    username=format_username(employee_data['first_name'], employee_data['last_name']),
                    password="123456",  # Default şifrə
                    role='user',
                    total_days=30,
                    max_sessions=1,
                    email=employee_data.get('email', ''),
                    first_name=employee_data.get('first_name', ''),
                    last_name=employee_data.get('last_name', ''),
                    father_name=employee_data.get('father_name', ''),
                    phone_number=employee_data.get('phone_number', ''),
                    birth_date=employee_data.get('birth_date') if employee_data.get('birth_date', '').strip() else None,
                    fin_code=employee_data.get('fin_code') if employee_data.get('fin_code', '').strip() else None,
                    department_id=int(employee_data.get('department_id')) if employee_data.get('department_id') else None,
                    position_id=int(employee_data.get('position_id')) if employee_data.get('position_id') else None,
                    hire_date=employee_data.get('hire_date') if employee_data.get('hire_date', '').strip() else None,
                    salary=float(employee_data.get('salary', 0)) if employee_data.get('salary', '').strip() else None,
                    address=employee_data.get('address', '')
                )
                if success:
                    messagebox.showinfo("Uğurlu", "Yeni işçi uğurla yaradıldı!")
                else:
                    messagebox.showerror("Xəta", "İşçi yaradılarkən xəta baş verdi!")
                    return
            
            # Dəyişiklikləri qeyd et
            self.has_changes = False
            self._save_original_data()  # Yeni orijinal məlumatları saxla
            
            # Əsas səhifəyə qayıt
            full_name = format_full_name(employee_data['first_name'], employee_data['last_name'])
            self.refresh_callback(selection_to_keep=full_name)
            self.show_main_view(needs_refresh=True)
            
        except Exception as e:
            logging.error(f"Məlumatlar saxlanarkən xəta: {e}")
            messagebox.showerror("Xəta", f"Məlumatlar saxlanarkən xəta: {e}")