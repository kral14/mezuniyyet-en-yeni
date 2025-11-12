# ui/notifications_window.py

import tkinter as tk
from tkinter import ttk, messagebox, Toplevel
import database

class NotificationsWindow(Toplevel):
    def __init__(self, parent, user_id, on_notif_click_callback, main_app_ref=None):
        super().__init__(parent)
        self.title("Bildirişlər")
        self.geometry("650x500")
        self.transient(parent)
        self.grab_set()
        
        # Pəncərənin arxa fonunu təmizlə (sarı fondan qurtarmaq)
        self.configure(bg='#ffffff')
        
        self.user_id = user_id
        self.on_notif_click_callback = on_notif_click_callback
        self.main_app_ref = main_app_ref
        self.notif_checkbox_vars = {}

        self.create_widgets()
        self.load_notifications()

    # Tema sistemi silindi

    def create_widgets(self):
        top_frame = ttk.Frame(self, padding=(10, 5))
        top_frame.pack(fill='x')
        main_frame = ttk.Frame(self)
        main_frame.pack(fill="both", expand=True)
        
        canvas = tk.Canvas(main_frame, background="white")
        scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=canvas.yview)
        self.scrollable_frame = ttk.Frame(canvas, style="Card.TFrame")
        self.scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        
        canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        self.select_all_var = tk.BooleanVar()
        select_all_cb = ttk.Checkbutton(top_frame, text="Hamısını Seç", variable=self.select_all_var, command=self._toggle_select_all)
        select_all_cb.pack(side='left')
        
        delete_button = ttk.Button(top_frame, text="Seçilənləri Sil", command=self._delete_selected, style="Accent.TButton")
        delete_button.pack(side='right', padx=5)

    def load_notifications(self):
        notifications = database.get_all_notifications_for_user(self.user_id)
        
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()

        if not notifications:
            ttk.Label(self.scrollable_frame, text="Heç bir bildiriş yoxdur.", padding=20, style="Card.TLabel").pack()
            return

        self.checkbox_list = []
        for notif_id, message, created_at, vac_id, emp_id, is_read in notifications:
            var = tk.BooleanVar()
            self.notif_checkbox_vars[notif_id] = var
            self.checkbox_list.append(var)
            
            frame_style = "Read.TFrame" if is_read else "Notification.TFrame"
            label_style = "Read.TLabel" if is_read else "Card.TLabel"
            cb_style = "Read.TCheckbutton" if is_read else "Notification.TCheckbutton"
            
            frame = ttk.Frame(self.scrollable_frame, padding=(10, 5), relief="solid", borderwidth=1, style=frame_style)
            frame.pack(fill='x', padx=10, pady=5)
            
            cb = ttk.Checkbutton(frame, variable=var, style=cb_style)
            cb.pack(side='left', padx=(0, 10))
            
            text_frame = ttk.Frame(frame, style=frame_style, cursor="hand2")
            text_frame.pack(fill='x', expand=True)
            
            label_msg = ttk.Label(text_frame, text=message, wraplength=500, justify="left", style=label_style)
            label_msg.pack(anchor='w')
            
            label_date = ttk.Label(text_frame, text=created_at.strftime('%d.%m.%Y %H:%M'), font=("Helvetica", 8, "italic"), style=label_style)
            label_date.pack(anchor='e')

            if not is_read:
                click_command = lambda e, n_id=notif_id, emp_id=emp_id, vac_id=vac_id: self._handle_click(n_id, emp_id, vac_id)
                text_frame.bind("<Button-1>", click_command)
                label_msg.bind("<Button-1>", click_command)
                label_date.bind("<Button-1>", click_command)
    
    def _handle_click(self, notif_id, emp_id, vac_id):
        self.on_notif_click_callback(notif_id, emp_id, vac_id)
        self.destroy()

    def _toggle_select_all(self):
        is_selected = self.select_all_var.get()
        for cb_var in self.checkbox_list:
            cb_var.set(is_selected)

    def _delete_selected(self):
        ids_to_delete = [notif_id for notif_id, var in self.notif_checkbox_vars.items() if var.get()]
        if not ids_to_delete:
            messagebox.showwarning("Seçim Yoxdur", "Silmək üçün heç bir bildiriş seçilməyib.", parent=self)
            return
        if messagebox.askyesno("Təsdiq", f"{len(ids_to_delete)} bildirişi silmək istədiyinizə əminsiniz?", parent=self):
            database.delete_notifications(ids_to_delete)
            
            # Real-time notification göndər (əgər main_app_ref varsa)
            if hasattr(self, 'main_app_ref') and hasattr(self.main_app_ref, 'send_realtime_signal'):
                self.main_app_ref.send_realtime_signal('notifications_deleted', {
                    'deleted_count': len(ids_to_delete),
                    'deleted_by': 'user',
                    'user_id': self.user_id
                })
            
            self.load_notifications()