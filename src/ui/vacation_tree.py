# vacation_tree_view.py

import tkinter as tk
from tkinter import ttk, messagebox
import tkinter.font as tkFont
from datetime import datetime, date
from database import database
from database.bulk_operations import bulk_delete_vacations_threaded, bulk_update_vacation_status_threaded
from .components import Tooltip, get_vacation_status_and_color, mezuniyyet_muddetini_hesabla
from .progress_indicator import ProgressIndicator, BulkOperationDialog

def safe_date_format(date_value, format_str='%d.%m.%Y'):
    """Tarix dəyərini təhlükəsiz şəkildə format edir"""
    if isinstance(date_value, str):
        try:
            return datetime.strptime(date_value, '%Y-%m-%d').strftime(format_str)
        except ValueError:
            return str(date_value)
    elif hasattr(date_value, 'strftime'):
        return date_value.strftime(format_str)
    else:
        return str(date_value)

class VacationTreeView(ttk.Frame):
    def __init__(self, parent, main_app, employee_info, current_user, refresh_callback):
        super().__init__(parent)
        self.main_app_ref = main_app 
        self.employee_info = employee_info
        self.current_user = current_user
        self.is_admin = self.current_user['role'].strip() == 'admin'
        self.refresh_callback = refresh_callback

        default_font_info = tkFont.nametofont("TkDefaultFont").actual()
        self.strikethrough_font = tkFont.Font(family=default_font_info['family'], size=default_font_info['size'], overstrike=True)

        columns = ('#', 'start_date', 'end_date', 'duration', 'status', 'note', 'countdown', 'created_at')
        self.tree = ttk.Treeview(self, columns=columns, show='headings')
        self.setup_tree_columns()
        self.tree.pack(expand=True, fill='both')

        self.populate_tree()
        self.create_context_menu()
        self.tree.bind("<Button-3>", self.show_context_menu)
        self.tree.bind("<Double-1>", self.on_double_click)
        
        # Çoxlu seçim funksionallığı
        self.setup_multi_selection()

    # --- YENİ FUNKSİYA BURADADIR ---
    def highlight_vacation(self, vacation_id):
        """Verilmiş ID-yə malik məzuniyyət sətirini cədvəldə tapıb işarələyir."""
        if not vacation_id:
            return
        
        # Treeview-də item ID-ləri string formatında olur
        item_id_str = str(vacation_id)
        
        if self.tree.exists(item_id_str):
            # Bütün seçimləri təmizlə
            for i in self.tree.selection():
                self.tree.selection_remove(i)
            
            # Lazım olan sətri seç, fokusla və görünən et
            self.tree.selection_set(item_id_str)
            self.tree.focus(item_id_str)
            self.tree.see(item_id_str)
    
    def setup_multi_selection(self):
        """Çoxlu seçim funksionallığını quraşdırır"""
        # Ctrl+A ilə hamısını seç
        self.tree.bind("<Control-a>", self.select_all_items)
        
        # Delete düyməsi ilə seçilmişləri sil
        self.tree.bind("<Delete>", self.delete_selected_items)
        self.tree.bind("<BackSpace>", self.delete_selected_items)
        
        # Ctrl+Click ilə çoxlu seçim
        self.tree.bind("<Control-Button-1>", self.on_ctrl_click)
        
        # Focus alanda keyboard shortcut-ları aktiv et
        self.tree.bind("<FocusIn>", self.on_focus_in)
        
        print("✅ DEBUG: Çoxlu seçim funksionallığı quraşdırıldı")
    
    def select_all_items(self, event):
        """Ctrl+A ilə bütün elementləri seçir"""
        try:
            all_items = self.tree.get_children()
            if all_items:
                self.tree.selection_set(all_items)
                print(f"✅ DEBUG: {len(all_items)} element seçildi")
            return "break"  # Event-i dayandır
        except Exception as e:
            print(f"⚠️ DEBUG: select_all_items xətası: {e}")
            return "break"
    
    def on_ctrl_click(self, event):
        """Ctrl+Click ilə çoxlu seçim"""
        try:
            item = self.tree.identify_row(event.y)
            if item:
                if item in self.tree.selection():
                    # Artıq seçilibsə, seçimdən çıxar
                    self.tree.selection_remove(item)
                else:
                    # Seçilməyibsə, seçimə əlavə et
                    self.tree.selection_add(item)
                print(f"✅ DEBUG: Ctrl+Click - {item} toggle edildi")
            return "break"
        except Exception as e:
            print(f"⚠️ DEBUG: on_ctrl_click xətası: {e}")
            return "break"
    
    def delete_selected_items(self, event):
        """Delete düyməsi ilə seçilmiş elementləri silir"""
        try:
            selected_items = self.tree.selection()
            if not selected_items:
                print("⚠️ DEBUG: Silinəcək element seçilməyib")
                return "break"
            
            # Təsdiq mesajı göstər
            count = len(selected_items)
            if count == 1:
                message = "Seçilmiş məzuniyyət sorğusunu silmək istədiyinizə əminsiniz?"
            else:
                message = f"{count} məzuniyyət sorğusunu silmək istədiyinizə əminsiniz?"
            
            import tkinter.messagebox as messagebox
            if messagebox.askyesno("Təsdiq", message):
                self._delete_items(selected_items)
            
            return "break"
        except Exception as e:
            print(f"⚠️ DEBUG: delete_selected_items xətası: {e}")
            return "break"
    
    def _delete_items(self, item_ids):
        """Seçilmiş elementləri silir - Toplu əməliyyat versiyası"""
        try:
            if not item_ids:
                return
            
            # Əgər çox element varsa, toplu silmə dialoqu göstər
            if len(item_ids) > 1:
                self.show_bulk_delete_dialog(item_ids)
            else:
                # Tək element silmə
                vacation_id = int(item_ids[0])
                vacation = self._get_vacation_by_id(str(vacation_id))
                if vacation:
                    self.delete_vacation(vacation)
                
        except Exception as e:
            print(f"⚠️ DEBUG: _delete_items xətası: {e}")
            import tkinter.messagebox as messagebox
            messagebox.showerror("Xəta", f"Elementlər silinərkən xəta: {e}")
    
    def show_bulk_delete_dialog(self, item_ids):
        """Toplu silmə dialoqu göstərir"""
        try:
            # Seçilmiş məzuniyyətlərin məlumatlarını al
            vacation_data = []
            for item_id in item_ids:
                vacation = self._get_vacation_by_id(str(item_id))
                if vacation:
                    vacation_data.append({
                        'db_id': vacation['db_id'],
                        'employee_name': self.employee_info.get('name', ''),
                        'baslama': vacation.get('baslama', ''),
                        'bitme': vacation.get('bitme', ''),
                        'status': vacation.get('status', '')
                    })
            
            if not vacation_data:
                import tkinter.messagebox as messagebox
                messagebox.showwarning("Xəbərdarlıq", "Seçilmiş məzuniyyətlər tapılmadı!")
                return
            
            # Toplu silmə dialoqu göstər
            dialog = BulkOperationDialog(self, "sil")
            dialog.show(vacation_data, self.execute_bulk_delete)
            
        except Exception as e:
            print(f"⚠️ DEBUG: show_bulk_delete_dialog xətası: {e}")
            import tkinter.messagebox as messagebox
            messagebox.showerror("Xəta", f"Toplu silmə dialoqu göstərilərkən xəta: {e}")
    
    def execute_bulk_delete(self, vacation_ids):
        """Toplu silmə əməliyyatını icra edir"""
        try:
            if not vacation_ids:
                return
            
            # Progress indicator göstər
            progress = ProgressIndicator(self.winfo_toplevel(), "Məzuniyyətlər silinir...")
            progress.show(len(vacation_ids))
            
            # Success callback
            def on_success(result):
                try:
                    progress.hide()
                    import tkinter.messagebox as messagebox
                    messagebox.showinfo("Uğurlu", f"{result['deleted_count']} məzuniyyət uğurla silindi!")
                    
                    # UI-ni yenilə
                    self.after(0, self.refresh_callback)
                    
                    # Real-time signal göndər
                    if hasattr(self.main_app_ref, 'send_realtime_signal'):
                        self.main_app_ref.send_realtime_signal('bulk_vacation_deleted', {
                            'deleted_count': result['deleted_count'],
                            'deleted_by': self.current_user.get('name'),
                            'employee_name': self.employee_info.get('name')
                        })
                        
                except Exception as e:
                    print(f"⚠️ DEBUG: on_success callback xətası: {e}")
            
            # Error callback
            def on_error(result):
                try:
                    progress.hide()
                    import tkinter.messagebox as messagebox
                    error_msg = "\n".join(result.get('errors', ['Naməlum xəta']))
                    messagebox.showerror("Xəta", f"Toplu silmə əməliyyatı uğursuz oldu:\n{error_msg}")
                except Exception as e:
                    print(f"⚠️ DEBUG: on_error callback xətası: {e}")
            
            # Progress callback
            def on_progress(current, total, status):
                try:
                    progress.update(current, total, status)
                except Exception as e:
                    print(f"⚠️ DEBUG: on_progress callback xətası: {e}")
            
            # Background thread-də toplu silmə icra et
            bulk_delete_vacations_threaded(
                vacation_ids, 
                self.current_user['name'],
                success_callback=on_success,
                error_callback=on_error,
                progress_callback=on_progress
            )
            
        except Exception as e:
            print(f"⚠️ DEBUG: execute_bulk_delete xətası: {e}")
            import tkinter.messagebox as messagebox
            messagebox.showerror("Xəta", f"Toplu silmə əməliyyatı başladılarkən xəta: {e}")
    
    def show_bulk_status_dialog(self, item_ids, new_status):
        """Toplu status yeniləmə dialoqu göstərir"""
        try:
            # Seçilmiş məzuniyyətlərin məlumatlarını al
            vacation_data = []
            for item_id in item_ids:
                vacation = self._get_vacation_by_id(str(item_id))
                if vacation:
                    vacation_data.append({
                        'db_id': vacation['db_id'],
                        'employee_name': self.employee_info.get('name', ''),
                        'baslama': vacation.get('baslama', ''),
                        'bitme': vacation.get('bitme', ''),
                        'status': vacation.get('status', '')
                    })
            
            if not vacation_data:
                import tkinter.messagebox as messagebox
                messagebox.showwarning("Xəbərdarlıq", "Seçilmiş məzuniyyətlər tapılmadı!")
                return
            
            # Status mətnini hazırla
            status_text = "təsdiqlə" if new_status == 'approved' else "rədd et"
            
            # Toplu status dialoqu göstər
            dialog = BulkOperationDialog(self, status_text)
            dialog.show(vacation_data, lambda ids: self.execute_bulk_status_update(ids, new_status))
            
        except Exception as e:
            print(f"⚠️ DEBUG: show_bulk_status_dialog xətası: {e}")
            import tkinter.messagebox as messagebox
            messagebox.showerror("Xəta", f"Toplu status dialoqu göstərilərkən xəta: {e}")
    
    def execute_bulk_status_update(self, vacation_ids, new_status):
        """Toplu status yeniləmə əməliyyatını icra edir"""
        try:
            if not vacation_ids:
                return
            
            # Progress indicator göstər
            status_text = "təsdiqlənir" if new_status == 'approved' else "rədd edilir"
            progress = ProgressIndicator(self.winfo_toplevel(), f"Məzuniyyətlər {status_text}...")
            progress.show(len(vacation_ids))
            
            # Success callback
            def on_success(result):
                try:
                    progress.hide()
                    import tkinter.messagebox as messagebox
                    messagebox.showinfo("Uğurlu", f"{result['updated_count']} məzuniyyət uğurla yeniləndi!")
                    
                    # UI-ni yenilə
                    self.after(0, self.refresh_callback)
                    
                    # Real-time signal göndər
                    if hasattr(self.main_app_ref, 'send_realtime_signal'):
                        self.main_app_ref.send_realtime_signal('bulk_vacation_status_changed', {
                            'updated_count': result['updated_count'],
                            'new_status': new_status,
                            'changed_by': self.current_user.get('name'),
                            'employee_name': self.employee_info.get('name')
                        })
                        
                except Exception as e:
                    print(f"⚠️ DEBUG: on_success callback xətası: {e}")
            
            # Error callback
            def on_error(result):
                try:
                    progress.hide()
                    import tkinter.messagebox as messagebox
                    error_msg = "\n".join(result.get('errors', ['Naməlum xəta']))
                    messagebox.showerror("Xəta", f"Toplu status yeniləmə əməliyyatı uğursuz oldu:\n{error_msg}")
                except Exception as e:
                    print(f"⚠️ DEBUG: on_error callback xətası: {e}")
            
            # Progress callback
            def on_progress(current, total, status):
                try:
                    progress.update(current, total, status)
                except Exception as e:
                    print(f"⚠️ DEBUG: on_progress callback xətası: {e}")
            
            # Background thread-də toplu status yeniləmə icra et
            bulk_update_vacation_status_threaded(
                vacation_ids, 
                new_status,
                self.current_user['name'],
                success_callback=on_success,
                error_callback=on_error,
                progress_callback=on_progress
            )
            
        except Exception as e:
            print(f"⚠️ DEBUG: execute_bulk_status_update xətası: {e}")
            import tkinter.messagebox as messagebox
            messagebox.showerror("Xəta", f"Toplu status yeniləmə əməliyyatı başladılarkən xəta: {e}")
    
    def _delete_multiple_items(self, item_ids):
        """Kontekst menyusundan çoxlu elementləri silir"""
        try:
            count = len(item_ids)
            message = f"{count} məzuniyyət sorğusunu silmək istədiyinizə əminsiniz?"
            
            import tkinter.messagebox as messagebox
            if messagebox.askyesno("Təsdiq", message):
                self._delete_items(item_ids)
            
        except Exception as e:
            print(f"❌ DEBUG: _delete_multiple_items xətası: {e}")
            import tkinter.messagebox as messagebox
            messagebox.showerror("Xəta", f"Məzuniyyət sorğuları silinərkən xəta: {e}")
    
    def on_focus_in(self, event):
        """Focus alanda keyboard shortcut-ları aktiv et"""
        # Treeview focus alanda keyboard event-ləri işləsin
        self.tree.focus_set()
    
    def sort_by_column(self, col, reverse):
        """Məlumatları verilən sütuna görə çeşidləyir."""
        data = []
        for item_id in self.tree.get_children(''):
            values = self.tree.item(item_id, 'values')
            tags = self.tree.item(item_id, 'tags')
            data.append((item_id, values, tags))

        def sort_key(item):
            values = item[1]
            col_index = self.tree["columns"].index(col)
            val = values[col_index]
            
            if col in ['start_date', 'end_date', 'created_at']:
                try: return datetime.strptime(val, '%d.%m.%Y')
                except (ValueError, TypeError): return datetime.min
            if col in ['duration', 'countdown']:
                try: return int(val.split()[0])
                except (ValueError, IndexError): return 0
            if col == '#':
                try: return int(val)
                except (ValueError, IndexError): return 0
            return str(val)

        data.sort(key=sort_key, reverse=reverse)

        for col_name in self.tree['columns']:
            current_text = self.tree.heading(col_name, 'text').replace(' ▼', '').replace(' ▲', '')
            self.tree.heading(col_name, text=current_text)
        
        arrow = ' ▼' if reverse else ' ▲'
        new_heading = self.tree.heading(col, 'text') + arrow
        self.tree.heading(col, text=new_heading)
        
        for item in self.tree.get_children(): self.tree.delete(item)
        
        for item_id, values, tags in data:
            self.tree.insert('', 'end', iid=item_id, values=values, tags=tags)

        self.tree.heading(col, command=lambda _col=col: self.sort_by_column(_col, not reverse))

    def setup_tree_columns(self):
        columns_config = {
            '#': {'text': '№', 'width': 40, 'minwidth': 30, 'anchor': 'center', 'sortable': True},
            'start_date': {'text': 'Başlanğıc', 'width': 100, 'minwidth': 90, 'anchor': 'center', 'sortable': True},
            'end_date': {'text': 'Bitmə', 'width': 100, 'minwidth': 90, 'anchor': 'center', 'sortable': True},
            'duration': {'text': 'Müddət', 'width': 80, 'minwidth': 60, 'anchor': 'center', 'sortable': True},
            'status': {'text': 'Status', 'width': 110, 'minwidth': 90, 'anchor': 'w', 'sortable': True},
            'note': {'text': 'Qeyd', 'width': 150, 'minwidth': 100, 'anchor': 'w', 'sortable': True},
            'countdown': {'text': 'Bitməsinə', 'width': 100, 'minwidth': 80, 'anchor': 'center', 'sortable': True},
            'created_at': {'text': 'Yaradılma Tarixi', 'width': 120, 'minwidth': 100, 'anchor': 'center', 'sortable': True}
        }
        
        for col, config in columns_config.items():
            self.tree.heading(col, text=config['text'])
            self.tree.column(col, width=config['width'], minwidth=config['minwidth'], anchor=config['anchor'])
            if config['sortable']:
                self.tree.heading(col, command=lambda _col=col: self.sort_by_column(_col, False))

        self.tree.tag_configure('approved_ongoing', foreground='green'); self.tree.tag_configure('approved_finished', foreground='red')
        self.tree.tag_configure('approved_planned', foreground='#007bff'); self.tree.tag_configure('pending', foreground='#E49B0F')
        self.tree.tag_configure('rejected', foreground='gray'); self.tree.tag_configure('inactive', font=self.strikethrough_font, foreground='gray')

    def populate_tree(self):
        for item in self.tree.get_children(): self.tree.delete(item)
        today = date.today()
        vacations_list = self.employee_info.get("goturulen_icazeler", [])
        
        for i, vacation in enumerate(vacations_list, start=1):
            try:
                # DÜZƏLİŞ: Təhlükəsiz tarix formatı istifadə edirik
                start_date_formatted = safe_date_format(vacation['baslama'])
                end_date_formatted = safe_date_format(vacation['bitme'])
                created_at_formatted = safe_date_format(vacation.get('yaradilma_tarixi', '1970-01-01'))
            except (ValueError, KeyError):
                start_date_formatted = str(vacation.get('baslama', ''))
                end_date_formatted = str(vacation.get('bitme', ''))
                created_at_formatted = str(vacation.get('yaradilma_tarixi', ''))

            is_inactive = vacation.get('aktiv_deyil', False)
            _, status_text = get_vacation_status_and_color(vacation)
            
            # DÜZƏLİŞ: Müddəti düzgün hesablayırıq
            muddet = mezuniyyet_muddetini_hesabla(vacation['baslama'], vacation['bitme'])
            
            qalan_gun_str = ""
            if status_text == "[Davam edən]":
                try:
                    # DÜZƏLİŞ: Tarix emalı təhlükəsiz şəkildə
                    if isinstance(vacation['bitme'], str):
                        end_dt = datetime.strptime(vacation['bitme'], '%Y-%m-%d').date()
                    else:
                        end_dt = vacation['bitme']
                    qalan_gun = (end_dt - today).days + 1
                    if qalan_gun > 0: 
                        qalan_gun_str = f"{qalan_gun} gün"
                    elif qalan_gun == 0:
                        qalan_gun_str = "Bu gün bitir"
                    else:
                        qalan_gun_str = "Bitmiş"
                except Exception as e:
                    print(f"Qalan gün hesablanarkən xəta: {e}")
                    qalan_gun_str = ""
            
            tag_name = vacation.get('status', 'approved')
            if tag_name == 'approved':
                if status_text == "[Davam edən]": tag_name = "approved_ongoing"
                elif status_text == "[Bitmiş]": tag_name = "approved_finished"
                else: tag_name = "approved_planned"
            if is_inactive: tag_name = 'inactive'
            
            # Qeyd məlumatını al və qısalt
            note = vacation.get('qeyd', '')
            if len(note) > 30:  # Qeyd çox uzundursa qısalt
                note = note[:27] + "..."
            
            values = (i, start_date_formatted, end_date_formatted, f"{muddet} gün", status_text.strip("[]"), note, qalan_gun_str, created_at_formatted)
            self.tree.insert('', 'end', iid=vacation['db_id'], values=values, tags=(tag_name,))
        
        self.sort_by_column('start_date', False)

    def create_context_menu(self):
        self.context_menu = tk.Menu(self, tearoff=0)

    def show_context_menu(self, event):
        self.context_menu.delete(0, 'end')
        item_id = self.tree.identify_row(event.y)
        if not item_id: return
        
        # Əgər Ctrl basılı deyilsə, yalnız klik edilən elementi seç
        if not event.state & 0x4:  # Ctrl basılı deyil
            self.tree.selection_set(item_id)
        
        # Adi istifadəçilər üçün yoxlama - yalnız öz məzuniyyətlərini idarə edə bilərlər
        if not self.is_admin and self.current_user['name'] != self.employee_info['name']:
            return
            
        vacation = self._get_vacation_by_id(item_id)
        if not vacation: return
        
        # İşçi adını vacation obyektinə əlavə et
        vacation['employee_name'] = self.employee_info.get('name', 'Naməlum')
        
        vac_status = vacation['status']; is_inactive = vacation.get('aktiv_deyil', False)
        
        # Çoxlu seçim funksiyaları
        selected_items = self.tree.selection()
        if len(selected_items) > 1:
            # Çoxlu seçim zamanı - Toplu əməliyyatlar
            self.context_menu.add_command(label=f"Seçilmiş {len(selected_items)} sorğunu sil", 
                                         command=lambda: self._delete_multiple_items(selected_items))
            
            # Admin üçün toplu status əməliyyatları
            if self.is_admin:
                self.context_menu.add_separator()
                self.context_menu.add_command(label=f"Seçilmiş {len(selected_items)} sorğunu təsdiqlə", 
                                             command=lambda: self.show_bulk_status_dialog(selected_items, 'approved'))
                self.context_menu.add_command(label=f"Seçilmiş {len(selected_items)} sorğunu rədd et", 
                                             command=lambda: self.show_bulk_status_dialog(selected_items, 'rejected'))
            
            self.context_menu.add_separator()
        
        # Admin funksiyaları
        if self.is_admin:
            if vac_status == 'pending':
                self.context_menu.add_command(label="Təsdiqlə", command=lambda: self._handle_request_action(item_id, 'approved'))
                self.context_menu.add_command(label="Rədd Et", command=lambda: self._handle_request_action(item_id, 'rejected'))
            if vac_status == 'approved':
                self.context_menu.add_separator()
                toggle_label = "Deaktiv Et" if not is_inactive else "Aktiv Et"
                self.context_menu.add_command(label=toggle_label, command=lambda: self.toggle_vacation_activity(vacation))
            self.context_menu.add_separator()
            self.context_menu.add_command(label="Sorğunu Sil", command=lambda: self.delete_vacation(vacation))
        
        # Düzəliş etmə funksiyası - status əsasında icazə
        can_edit = self.is_admin or (vac_status == 'pending')
        if can_edit:
            self.context_menu.add_command(label="Düzəliş Et", command=lambda: self.main_app_ref.toggle_vacation_panel(show=True, employee_name=self.employee_info['name'], vacation=vacation))
        else:
            # Düzəliş edilə bilməyən statuslar üçün xəbərdarlıq
            if not self.is_admin:
                self.context_menu.add_command(label="Düzəliş Et (İcazə yoxdur)", command=lambda: self._show_edit_warning(vac_status))
        
        # Kalendara bax funksiyası - yalnız kalendarda görünən statuslar üçün
        calendar_visible_statuses = ['approved', 'ongoing', 'completed', 'scheduled']
        if vac_status in calendar_visible_statuses:
            self.context_menu.add_separator()
            self.context_menu.add_command(label="📅 Kalendara Bax", command=lambda: self._show_in_calendar(vacation))
        else:
            # Gözləyən və ya rədd edilmiş sorğular üçün xəbərdarlıq
            self.context_menu.add_separator()
            self.context_menu.add_command(label="📅 Kalendara Bax (Mövcud deyil)", command=lambda: self._show_calendar_warning(vac_status))
        
        self.context_menu.post(event.x_root, event.y_root)

    def on_double_click(self, event):
        # Adi istifadəçilər üçün yoxlama - yalnız öz məzuniyyətlərini düzəliş edə bilərlər
        if not self.is_admin and self.current_user['name'] != self.employee_info['name']:
            return
            
        item_id = self.tree.identify_row(event.y)
        if not item_id: return
        vacation = self._get_vacation_by_id(item_id)
        if not vacation: return
        
        # İşçi adını vacation obyektinə əlavə et
        vacation['employee_name'] = self.employee_info.get('name', 'Naməlum')
        
        # Status əsasında düzəliş icazəsi
        vac_status = vacation['status']
        can_edit = self.is_admin or (vac_status == 'pending')
        
        if can_edit:
            self.main_app_ref.toggle_vacation_panel(show=True, employee_name=self.employee_info['name'], vacation=vacation)
        else:
            # Düzəliş edilə bilməyən statuslar üçün xəbərdarlıq
            if not self.is_admin:
                self._show_edit_warning(vac_status)

    def _get_vacation_by_id(self, item_id):
        return next((v for v in self.employee_info.get("goturulen_icazeler", []) if str(v['db_id']) == str(item_id)), None)

    def _handle_request_action(self, vac_id, new_status):
        database.update_vacation_status(vac_id, new_status, self.current_user['name'])
        
        # Real-time notification göndər
        if hasattr(self.main_app_ref, 'send_realtime_signal'):
            self.main_app_ref.send_realtime_signal('vacation_status_changed', {
                'vacation_id': vac_id,
                'new_status': new_status,
                'changed_by': self.current_user.get('name'),
                'employee_name': self.employee_info.get('name')
            })
        
        # Tree-də statusu dərhal yenilə
        try:
            item = self.tree.item(vac_id)
            if item:
                values = list(item['values'])
                if new_status == 'approved':
                    values[4] = 'Təsdiqlənmiş'  # Status sütunu
                elif new_status == 'rejected':
                    values[4] = 'Rədd edilmiş'  # Status sütunu
                self.tree.item(vac_id, values=values)
                print(f"Status dərhal yeniləndi: {vac_id} -> {new_status}")
        except Exception as e:
            print(f"Status yenilənərkən xəta: {e}")
        
        # Dərhal lokal refresh et (UI thread-də)
        try:
            self.after(0, self.refresh_callback)
        except Exception as e:
            print(f"Refresh callback xətası: {e}")

    def toggle_vacation_activity(self, vacation):
        new_activity_status = not vacation.get('aktiv_deyil', False)
        database.toggle_vacation_activity(vacation['db_id'], new_activity_status, self.current_user['name'])
        
        # Real-time notification göndər
        if hasattr(self.main_app_ref, 'send_realtime_signal'):
            self.main_app_ref.send_realtime_signal('vacation_activity_toggled', {
                'vacation_id': vacation['db_id'],
                'new_activity_status': new_activity_status,
                'changed_by': self.current_user.get('name'),
                'employee_name': self.employee_info.get('name')
            })
        
        # Tree-də aktivlik statusunu dərhal yenilə
        try:
            item = self.tree.item(vacation['db_id'])
            if item:
                status_text = "Deaktiv" if new_activity_status else "Aktiv"
                print(f"Aktivlik statusu dərhal yeniləndi: {vacation['db_id']} -> {status_text}")
        except Exception as e:
            print(f"Aktivlik statusu yenilənərkən xəta: {e}")
        
        # Dərhal lokal refresh et (UI thread-də)
        try:
            self.after(0, self.refresh_callback)
        except Exception as e:
            print(f"Refresh callback xətası: {e}")

    def delete_vacation(self, vacation):
        if messagebox.askyesno("Təsdiq", f"Məzuniyyət sorğusunu silmək istədiyinizə əminsiniz?", parent=self):
            database.delete_vacation(vacation['db_id'], self.current_user['name'])
            
            # Real-time notification göndər
            if hasattr(self.main_app_ref, 'send_realtime_signal'):
                self.main_app_ref.send_realtime_signal('vacation_deleted', {
                    'vacation_id': vacation['db_id'],
                    'deleted_by': self.current_user.get('name'),
                    'employee_name': self.employee_info.get('name'),
                    'vacation_data': {
                        'baslama': vacation.get('baslama'),
                        'bitme': vacation.get('bitme'),
                        'status': vacation.get('status')
                    }
                })
            
            # Tree-dən elementi dərhal sil
            try:
                self.tree.delete(vacation['db_id'])
                print(f"Sorğu dərhal silindi: {vacation['db_id']}")
            except Exception as e:
                print(f"Tree-dən silinərkən xəta: {e}")
            
            # Dərhal lokal refresh et (UI thread-də)
            try:
                self.after(0, self.refresh_callback)
            except Exception as e:
                print(f"Refresh callback xətası: {e}")

    def _show_edit_warning(self, status):
        """Düzəliş edilə bilməyən statuslar üçün xəbərdarlıq göstərir"""
        status_text = {
            'approved': 'Təsdiqlənmiş',
            'rejected': 'Rədd edilmiş',
            'completed': 'Bitmiş',
            'ongoing': 'Davam edən',
            'scheduled': 'Planlaşdırılmış',
            'pending': 'Gözləyən'
        }.get(status, status)
        
        messagebox.showwarning(
            "Düzəliş İcazəsi Yoxdur",
            f"Bu sorğu '{status_text}' statusunda olduğu üçün düzəliş edilə bilməz.\n\n"
            "Yalnız 'Gözləyən' statusunda olan sorğular düzəliş edilə bilər.\n"
            "Admin istifadəçilər istənilən sorğunu düzəliş edə bilər."
        )

    def _show_calendar_warning(self, status):
        """Kalendarda görünməyən sorğular üçün xəbərdarlıq göstərir"""
        status_text = {
            'approved': 'Təsdiqlənmiş',
            'rejected': 'Rədd edilmiş',
            'completed': 'Bitmiş',
            'ongoing': 'Davam edən',
            'scheduled': 'Planlaşdırılmış',
            'pending': 'Gözləyən'
        }.get(status, status)
        
        messagebox.showinfo(
            "Kalendarda Görünmür",
            f"Bu sorğu '{status_text}' statusunda olduğu üçün kalendarda görünmür.\n\n"
            "Kalendarda yalnız aşağıdakı statuslarda olan sorğular görünür:\n"
            "• Təsdiqlənmiş\n"
            "• Davam edən\n"
            "• Bitmiş\n"
            "• Planlaşdırılmış\n\n"
            "'Gözləyən' və 'Rədd edilmiş' sorğular kalendarda görünmür."
        )

    def _show_in_calendar(self, vacation):
        """Məzuniyyəti kalendarda göstərir"""
        try:
            import logging
            print(f"🔍 DEBUG: _show_in_calendar başladı - vacation: {vacation}")
            logging.info(f"_show_in_calendar çağırıldı: {vacation}")
            
            # Status yoxlaması - yalnız kalendarda görünən sorğular üçün
            calendar_visible_statuses = ['approved', 'ongoing', 'completed', 'scheduled']
            vacation_status = vacation.get('status')
            print(f"🔍 DEBUG: Vacation status: {vacation_status}")
            
            if vacation_status not in calendar_visible_statuses:
                status_text = {
                    'approved': 'Təsdiqlənmiş',
                    'rejected': 'Rədd edilmiş',
                    'completed': 'Bitmiş',
                    'ongoing': 'Davam edən',
                    'scheduled': 'Planlaşdırılmış',
                    'pending': 'Gözləyən'
                }.get(vacation_status, vacation_status)
                
                print(f"⚠️ DEBUG: Status kalendarda görünmür: {status_text}")
                messagebox.showinfo(
                    "Kalendarda Görünmür",
                    f"Bu sorğu '{status_text}' statusunda olduğu üçün kalendarda görünmür.\n\n"
                    "Kalendarda yalnız aşağıdakı statuslarda olan sorğular görünür:\n"
                    "• Təsdiqlənmiş\n"
                    "• Davam edən\n"
                    "• Bitmiş\n"
                    "• Planlaşdırılmış"
                )
                return
            
            print(f"✅ DEBUG: Status kalendarda görünür: {vacation_status}")
            
            # Dashboard view-a keç və kalendarda məzuniyyəti işarələ
            print("🔄 DEBUG: Dashboard view-a keçilir...")
            logging.info("Dashboard view-a keçilir...")
            
            # Dashboard view-a keçmədən əvvəl cari view-u yoxla
            current_view = getattr(self.main_app_ref, 'current_view', 'unknown')
            print(f"🔍 DEBUG: Cari view: {current_view}")
            
            self.main_app_ref.show_view('dashboard')
            
            # Ana səhifəyə keçdikdən sonra view-u yoxla
            new_view = getattr(self.main_app_ref, 'current_view', 'unknown')
            print(f"🔍 DEBUG: Yeni view: {new_view}")
            
            # Kalendar tab-ını aktivləşdir
            print("📅 DEBUG: Kalendar tab-ı aktivləşdirilir...")
            self.after(300, lambda: self._activate_calendar_tab())
            
            # Kalendar yükləndikdən sonra məzuniyyəti işarələ
            print("⏳ DEBUG: Kalendarda məzuniyyət işarələnir... (800ms gecikmə)")
            logging.info("Kalendarda məzuniyyət işarələnir...")
            self.after(800, lambda: self._highlight_vacation_in_calendar(vacation))
            
        except Exception as e:
            print(f"❌ DEBUG: _show_in_calendar xətası: {e}")
            logging.error(f"_show_in_calendar xətası: {e}")
            messagebox.showerror("Xəta", f"Kalendarda göstərilərkən xəta baş verdi: {e}")

    def _activate_calendar_tab(self):
        """Kalendar tab-ını aktivləşdirir"""
        try:
            import logging
            print(f"📅 DEBUG: _activate_calendar_tab başladı")
            logging.info(f"_activate_calendar_tab çağırıldı")
            
            # Dashboard view-u tap
            print("🔍 DEBUG: Dashboard view axtarılır...")
            dashboard_view = self.main_app_ref.views.get('dashboard')
            print(f"🔍 DEBUG: Dashboard view tapıldı: {dashboard_view}")
            
            if dashboard_view:
                print(f"🔍 DEBUG: Dashboard view tipi: {type(dashboard_view)}")
                
                # Dashboard view-də notebook-u tap - daha dəqiq axtarış
                print("🔍 DEBUG: Dashboard view children axtarılır...")
                children = dashboard_view.winfo_children()
                print(f"🔍 DEBUG: Children sayı: {len(children)}")
                
                notebook = None
                for i, child in enumerate(children):
                    print(f"🔍 DEBUG: Child {i}: {type(child)} - {child}")
                    # ttk.Notebook tipini yoxla
                    if hasattr(child, 'tabs') and callable(getattr(child, 'tabs', None)):
                        notebook = child
                        print(f"✅ DEBUG: Notebook tapıldı: {notebook}")
                        break
                
                if notebook:
                    print(f"🔍 DEBUG: Notebook tipi: {type(notebook)}")
                    
                    # Notebook-un tabs metodunu tap
                    if hasattr(notebook, 'tabs'):
                        tabs = notebook.tabs()
                        print(f"🔍 DEBUG: Notebook tabs sayı: {len(tabs)}")
                        
                        # Kalendar tab-ını tap və aktivləşdir
                        print("🔍 DEBUG: Kalendar tab-ı axtarılır...")
                        for i, tab_id in enumerate(tabs):
                            try:
                                tab_text = notebook.tab(tab_id, "text")
                                print(f"🔍 DEBUG: Tab {i}: '{tab_text}'")
                                
                                # Kalendar tab-ını tap - daha dəqiq axtarış
                                if ("🗓️" in tab_text or 
                                    "təqvim" in tab_text.lower() or
                                    "kalendar" in tab_text.lower() or
                                    "calendar" in tab_text.lower()):
                                    print(f"✅ DEBUG: Kalendar tab tapıldı: '{tab_text}'")
                                    notebook.select(tab_id)
                                    print(f"✅ DEBUG: Kalendar tab aktivləşdirildi: '{tab_text}'")
                                    logging.info(f"Kalendar tab aktivləşdirildi: '{tab_text}'")
                                    return
                            except Exception as tab_error:
                                print(f"❌ DEBUG: Tab {i} xətası: {tab_error}")
                                continue
                        
                        print("❌ DEBUG: Kalendar tab tapılmadı, bütün tab-lar:")
                        for i, tab_id in enumerate(tabs):
                            try:
                                tab_text = notebook.tab(tab_id, "text")
                                print(f"  - Tab {i}: '{tab_text}'")
                            except:
                                print(f"  - Tab {i}: xəta")
                        logging.warning("Kalendar tab tapılmadı")
                    else:
                        print("❌ DEBUG: Notebook tabs metodu tapılmadı")
                        logging.warning("Notebook tabs metodu tapılmadı")
                else:
                    print("❌ DEBUG: Notebook tapılmadı")
                    print(f"🔍 DEBUG: Dashboard view atributları: {dir(dashboard_view)}")
                    logging.warning("Dashboard view-də notebook tapılmadı")
            else:
                print("❌ DEBUG: Dashboard view tapılmadı")
                logging.warning("Dashboard view tapılmadı")
                
        except Exception as e:
            print(f"❌ DEBUG: _activate_calendar_tab xətası: {e}")
            logging.error(f"_activate_calendar_tab xətası: {e}")
            import traceback
            print(f"📋 DEBUG: Traceback: {traceback.format_exc()}")
            logging.error(f"Traceback: {traceback.format_exc()}")

    def _highlight_vacation_in_calendar(self, vacation):
        """Kalendarda məzuniyyəti işarələyir"""
        try:
            import logging
            print(f"🔍 DEBUG: _highlight_vacation_in_calendar başladı - vacation: {vacation}")
            logging.info(f"_highlight_vacation_in_calendar çağırıldı: {vacation}")
            
            # Dashboard view-u tap
            print("🔍 DEBUG: Dashboard view axtarılır...")
            dashboard_view = self.main_app_ref.views.get('dashboard')
            print(f"🔍 DEBUG: Dashboard view tapıldı: {dashboard_view}")
            
            if dashboard_view:
                print(f"🔍 DEBUG: Dashboard view tipi: {type(dashboard_view)}")
                print(f"🔍 DEBUG: highlight_vacation metodu var: {hasattr(dashboard_view, 'highlight_vacation')}")
                
                if hasattr(dashboard_view, 'highlight_vacation'):
                    print("✅ DEBUG: Dashboard view tapıldı, highlight_vacation çağırılır...")
                    logging.info("Dashboard view tapıldı, highlight_vacation çağırılır...")
                    dashboard_view.highlight_vacation(vacation)
                    
                    # İşçi adını göstər
                    employee_name = vacation.get('employee_name') or vacation.get('employee', 'Naməlum')
                    start_date = safe_date_format(vacation['baslama'])
                    end_date = safe_date_format(vacation['bitme'])
                    
                    print(f"✅ DEBUG: Məzuniyyət işarələndi: {employee_name} - {start_date} - {end_date}")
                    logging.info(f"Məzuniyyət işarələndi: {employee_name} - {start_date} - {end_date}")
                    
                    # İkinci mesaj pəncərəsi açılmasın - sadəcə bir dəfə açılsın
                    # messagebox.showinfo(
                    #     "Kalendarda Göstərildi",
                    #     f"'{employee_name}' məzuniyyəti kalendarda işarələndi:\n"
                    #     f"Başlama: {start_date}\n"
                    #     f"Bitmə: {end_date}\n\n"
                    #     "Qırmızı border ilə işarələnmiş günlərə baxın."
                    # )
                else:
                    print("❌ DEBUG: highlight_vacation metodu tapılmadı")
                    logging.warning("highlight_vacation funksiyası tapılmadı")
                    messagebox.showwarning("Xəbərdarlıq", "Kalendar funksiyası tapılmadı!")
            else:
                print("❌ DEBUG: Dashboard view tapılmadı")
                logging.warning("Dashboard view tapılmadı")
                messagebox.showwarning("Xəbərdarlıq", "Kalendar funksiyası tapılmadı!")
                
        except Exception as e:
            print(f"❌ DEBUG: _highlight_vacation_in_calendar xətası: {e}")
            logging.error(f"_highlight_vacation_in_calendar xətası: {e}")
            messagebox.showerror("Xəta", f"Kalendarda işarələmə xətası: {e}")
    
    def get_selected_vacation(self):
        """Seçilmiş məzuniyyəti qaytarır"""
        try:
            selection = self.tree.selection()
            if not selection:
                return None
            
            selected_item = selection[0]
            
            # Seçilmiş item-in məlumatlarını al
            item_values = self.tree.item(selected_item, 'values')
            if not item_values:
                return None
            
            # Məzuniyyət məlumatlarını employee_info-dan tap
            vacations = self.employee_info.get('goturulen_icazeler', [])
            
            # Item-in sıra nömrəsini al (1-ci sütun)
            try:
                row_number = int(item_values[0]) - 1  # 1-dən başladığı üçün 1 çıxırıq
                if 0 <= row_number < len(vacations):
                    return vacations[row_number]
            except (ValueError, IndexError):
                pass
            
            # Əgər sıra nömrəsi ilə tapmadıqsa, tarixlərə görə axtaraq
            start_date_str = item_values[1]  # Başlanğıc tarixi
            end_date_str = item_values[2]    # Bitmə tarixi
            
            for vacation in vacations:
                vacation_start = vacation.get('baslama', vacation.get('baslangic', ''))
                vacation_end = vacation.get('bitme', '')
                
                # Tarixləri format et və müqayisə et
                if vacation_start and vacation_end:
                    formatted_start = safe_date_format(vacation_start)
                    formatted_end = safe_date_format(vacation_end)
                    
                    if formatted_start == start_date_str and formatted_end == end_date_str:
                        return vacation
            
            return None
            
        except Exception as e:
            print(f"Seçilmiş məzuniyyət alınarkən xəta: {e}")
            return None