# ui/employee_detail_frame.py

import tkinter as tk
from tkinter import ttk
import logging
from .components import mezuniyyet_muddetini_hesabla
from .vacation_tree import VacationTreeView
# Database import - şərti import
try:
    from ..database import database
except ImportError:
    try:
        from database import database
    except ImportError:
        from src.database import database
import tkinter.messagebox as messagebox

class EmployeeDetailFrame(ttk.Frame):
    def __init__(self, parent, main_app_ref):
        super().__init__(parent)
        self.main_app_ref = main_app_ref # Ana pəncərəyə referans
        # Bu çərçivənin daxili, update_data ilə dinamik dolacaq
        self.header_container = ttk.Frame(self, style="Card.TFrame")
        self.header_container.pack(fill='x', padx=6)  # Optimizasiya: boşluq azaldıldı
        
        self.tree_area_frame = ttk.Frame(self)
        self.tree_area_frame.pack(expand=True, fill='both', padx=6, pady=(0, 6))  # Optimizasiya: boşluq azaldıldı
        
        # Seçilmiş məzuniyyət üçün
        self.selected_vacation = None
        
        # Açıq pəncərələri izləmək üçün
        self.open_vacation_windows = []
        
    # Tema sistemi silindi
        
    def update_data(self, info, current_user):
        """Bu görünüşü seçilmiş işçinin məlumatları ilə yeniləyir."""
        try:
            # Məlumatları yoxla
            if not info or not isinstance(info, dict):
                logging.error(f"Yanlış info məlumatı: {info}")
                error_label = ttk.Label(self, text="Məlumatlar yüklənə bilmədi", foreground="red")
                error_label.pack(expand=True, fill='both')
                return
            
            if 'name' not in info:
                logging.error(f"Info obyektində 'name' sahəsi yoxdur: {info}")
                error_label = ttk.Label(self, text="İşçi adı tapılmadı", foreground="red")
                error_label.pack(expand=True, fill='both')
                return
            
            # Açıq məzuniyyət sorğusu pəncərələrini bağla
            self._close_open_vacation_windows()
            
            # Köhnə məlumatları təmizlə
            for widget in self.header_container.winfo_children(): widget.destroy()
            for widget in self.tree_area_frame.winfo_children(): widget.destroy()

            is_admin = current_user['role'].strip() == 'admin'
            
            # Başlıq hissəsi
            title_bar = ttk.Frame(self.header_container, style="Card.TFrame")
            title_bar.pack(fill='x', pady=(3,0))  # Optimizasiya: boşluq azaldıldı
            
            # Geri dönmə oxu
            back_button = ttk.Button(
                title_bar, 
                text="← Geri", 
                command=lambda: self.main_app_ref.show_main_view(),
                style="Card.TButton",
                width=8
            )
            back_button.pack(side='left', padx=(0, 10))  # Optimizasiya: boşluq azaldıldı
            
            # İşçi adı
            ttk.Label(title_bar, text=info['name'], font=("Helvetica", 18, "bold"), style="Card.TLabel").pack(side='left', anchor='w')
            if is_admin:
                admin_buttons_frame = ttk.Frame(title_bar, style="Card.TFrame")
                admin_buttons_frame.pack(side='right', anchor='e')
                user_id = info['db_id']
                is_user_active = info.get("is_active", True)
                toggle_text = "Deaktiv Et" if is_user_active else "Aktiv Et"
                ttk.Button(admin_buttons_frame, text=toggle_text, command=lambda: self.main_app_ref.toggle_user_activity(user_id, not is_user_active)).pack(side='left')

            # Xülasə paneli (İllik hüquq, istifadə, qalıq)
            self.main_app_ref.show_summary_panel(self.header_container, info)
            
            # Yeni məzuniyyət düyməsi - adi istifadəçilər üçün də aktiv
            # Adi istifadəçilər yalnız öz məzuniyyətlərini əlavə edə bilər
            can_add_vacation = is_admin or (current_user['name'] == info['name'])
            
            if can_add_vacation:
                # Düymələr çərçivəsi
                buttons_frame = ttk.Frame(self.header_container, style="Card.TFrame")
                buttons_frame.pack(pady=6)  # Optimizasiya: boşluq azaldıldı
                
                ttk.Button(
                    buttons_frame, 
                    text=f"✚ Yeni Məzuniyyət Əlavə Et", 
                    command=lambda: self.main_app_ref.toggle_vacation_panel(show=True, employee_name=info['name'])
                ).pack(side='left', padx=(0, 10))
                
                # Çap düyməsi
                ttk.Button(
                    buttons_frame,
                    text="🖨️ Çap Et",
                    command=lambda: self._show_print_menu(info)
                ).pack(side='left')
            
            # Məzuniyyət cədvəli
            def refresh_vacation_tree():
                """Məzuniyyət cədvəlini yeniləyir"""
                try:
                    # Məlumatları yenilə
                    self.main_app_ref.data = database.load_data_for_user(self.main_app_ref.current_user)
                    
                    # İşçi siyahısını yenilə
                    self.main_app_ref.refresh_employee_list()
                    
                    # Cari işçinin məlumatlarını yenilə
                    if 'name' in info and info['name']:
                        updated_info = self.main_app_ref.data.get(info['name'], {})
                        if updated_info and isinstance(updated_info, dict) and 'name' in updated_info:
                            # UI thread-də yenilə
                            self.after(0, lambda: self.update_data(updated_info, current_user))
                        else:
                            logging.warning(f"Yenilənmiş məlumatlar tapılmadı: {info['name']}")
                    else:
                        logging.warning("İşçi adı yoxdur")
                    
                    logging.info("Məzuniyyət cədvəli yeniləndi")
                except Exception as e:
                    logging.error(f"Məzuniyyət cədvəli yenilənərkən xəta: {e}")
            
            tree_view = VacationTreeView(self.tree_area_frame, self.main_app_ref, info, current_user, refresh_vacation_tree)
            tree_view.pack(expand=True, fill='both')
            
            logging.info(f"İşçi məlumatları yeniləndi: {info.get('name', 'Unknown')}")
            
        except Exception as e:
            logging.error(f"İşçi məlumatları yenilənərkən xəta: {e}")
            # Xəta olduqda sadə mesaj göstər
            error_label = ttk.Label(self, text=f"Xəta: {e}", foreground="red")
            error_label.pack(expand=True, fill='both')
    
    def _show_print_menu(self, employee_info):
        """Çap menyusunu göstərir"""
        try:
            # Popup menyu yaradırıq
            menu_window = tk.Toplevel(self)
            menu_window.title("Çap və İxrac Seçimləri")
            menu_window.geometry("400x450")
            menu_window.resizable(False, False)
            menu_window.transient(self)
            menu_window.grab_set()
            
            # Pəncərəni mərkəzləşdir
            menu_window.update_idletasks()
            x = (menu_window.winfo_screenwidth() // 2) - (400 // 2)
            y = (menu_window.winfo_screenheight() // 2) - (450 // 2)
            menu_window.geometry(f"400x450+{x}+{y}")
            
            # Başlıq
            title_label = ttk.Label(menu_window, text="Çap Seçimləri", font=("Helvetica", 14, "bold"))
            title_label.pack(pady=20)
            
            # Düymələr çərçivəsi
            buttons_frame = ttk.Frame(menu_window)
            buttons_frame.pack(expand=True, fill='both', padx=20, pady=10)
            
            # Bütün məzuniyyətləri yığcam çap et
            all_vacations_compact_btn = ttk.Button(
                buttons_frame,
                text="📋 Bütün Məzuniyyətləri Yığcam Çap Et",
                command=lambda: self._print_all_vacations_compact(employee_info, menu_window)
            )
            all_vacations_compact_btn.pack(fill='x', pady=(0, 5))
            
            
            # Ləğv et
            cancel_btn = ttk.Button(
                buttons_frame,
                text="❌ Ləğv Et",
                command=menu_window.destroy
            )
            cancel_btn.pack(fill='x', pady=(10, 0))
            
        except Exception as e:
            messagebox.showerror("Xəta", f"Çap menyusu açılarkən xəta: {e}")
            logging.error(f"Çap menyusu xətası: {e}")
    
    
    
    def _get_selected_vacation(self):
        """Seçilmiş məzuniyyəti qaytarır"""
        try:
            # VacationTreeView-dan seçilmiş məzuniyyəti al
            for widget in self.tree_area_frame.winfo_children():
                if isinstance(widget, VacationTreeView):
                    return widget.get_selected_vacation()
            return None
        except Exception as e:
            logging.error(f"Seçilmiş məzuniyyət alınarkən xəta: {e}")
            return None
    
    
    
    def _print_selected_vacation_compact(self, employee_info, menu_window):
        """Seçilmiş məzuniyyəti yığcam formatda çap edir"""
        try:
            # Seçilmiş məzuniyyəti tap
            selected_vacation = self._get_selected_vacation()
            
            if not selected_vacation:
                messagebox.showwarning("Xəbərdarlıq", "Zəhmət olmasa çap etmək istədiyiniz məzuniyyəti seçin!")
                return
            
            try:
                from utils.print_service import generate_compact_vacation_html
            except ImportError:
                from src.utils.print_service import generate_compact_vacation_html
            import tempfile
            import webbrowser
            
            menu_window.destroy()
            
            # Məzuniyyət məlumatlarını format et
            vacation_data = {
                'start_date': selected_vacation.get('baslama', selected_vacation.get('baslangic', '')),
                'end_date': selected_vacation.get('bitme', ''),
                'note': selected_vacation.get('qeyd', '')
            }
            
            # Yığcam HTML yaradırıq
            html_content = generate_compact_vacation_html(employee_info, vacation_data)
            
            # Temp fayl yaradırıq
            with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False, encoding='utf-8') as temp_file:
                temp_file.write(html_content)
                temp_file_path = temp_file.name
            
            # Brauzer-də açırıq (çap üçün)
            webbrowser.open(f'file://{temp_file_path}')
            
            messagebox.showinfo("Uğur", "Seçilmiş məzuniyyət yığcam formatda çap üçün hazırlandı!")
                
        except Exception as e:
            messagebox.showerror("Xəta", f"Yığcam çap xətası: {e}")
            logging.error(f"Seçilmiş məzuniyyət yığcam çap xətası: {e}")
    
    def _print_all_vacations_compact(self, employee_info, menu_window):
        """Bütün məzuniyyətləri yığcam formatda çap edir"""
        try:
            try:
                from utils.print_service import generate_compact_all_vacations_html
            except ImportError:
                from src.utils.print_service import generate_compact_all_vacations_html
            import tempfile
            import webbrowser
            
            menu_window.destroy()
            
            # Yığcam HTML yaradırıq
            html_content = generate_compact_all_vacations_html(employee_info)
            
            # Temp fayl yaradırıq
            with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False, encoding='utf-8') as temp_file:
                temp_file.write(html_content)
                temp_file_path = temp_file.name
            
            # Brauzer-də açırıq (çap üçün)
            webbrowser.open(f'file://{temp_file_path}')
            
            messagebox.showinfo("Uğur", f"{employee_info.get('name')} üçün bütün məzuniyyətlər yığcam formatda çap üçün hazırlandı!")
                
        except Exception as e:
            messagebox.showerror("Xəta", f"Yığcam bütün məzuniyyətlər çap xətası: {e}")
            logging.error(f"Bütün məzuniyyətlər yığcam çap xətası: {e}")
    
    def _close_open_vacation_windows(self):
        """Açıq məzuniyyət sorğusu pəncərələrini bağlayır"""
        try:
            # Açıq pəncərələri bağla
            for window in self.open_vacation_windows[:]:
                try:
                    if window.winfo_exists():
                        window.destroy()
                    self.open_vacation_windows.remove(window)
                except:
                    pass
            
            # Ana pəncərədə də açıq pəncərələri yoxla
            if hasattr(self.main_app_ref, 'opened_windows'):
                vacation_windows = []
                for window in self.main_app_ref.opened_windows[:]:
                    try:
                        if hasattr(window, 'title') and 'məzuniyyət' in window.title().lower():
                            vacation_windows.append(window)
                    except:
                        pass
                
                # Məzuniyyət pəncərələrini bağla
                for window in vacation_windows:
                    try:
                        if window.winfo_exists():
                            window.destroy()
                        if window in self.main_app_ref.opened_windows:
                            self.main_app_ref.opened_windows.remove(window)
                    except:
                        pass
                        
        except Exception as e:
            logging.warning(f"Açıq pəncərələri bağlarkən xəta: {e}")
    
    
    
    def _get_selected_vacation(self):
        """Seçilmiş məzuniyyəti qaytarır"""
        try:
            # Treeview-dən seçilmiş elementi al
            if hasattr(self, 'vacation_tree') and self.vacation_tree:
                selection = self.vacation_tree.selection()
                if selection:
                    item = self.vacation_tree.item(selection[0])
                    return item.get('values', {})
            
            # Əgər treeview yoxdursa, sadə dict qaytar
            return {
                'start_date': '',
                'end_date': '',
                'note': '',
                'status': 'Bitmiş'
            }
            
        except Exception as e:
            logging.error(f"Seçilmiş məzuniyyət alınarkən xəta: {e}")
            return None