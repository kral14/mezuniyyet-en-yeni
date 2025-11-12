# ui/login_history_window.py

import tkinter as tk
from tkinter import ttk, Toplevel
import database

class LoginHistoryWindow(Toplevel):
    def __init__(self, parent, user_id, username):
        super().__init__(parent)
        self.title(f"'{username}' - Giriş Tarixçəsi")
        self.geometry("550x450")
        self.transient(parent)
        self.grab_set()

        tree_frame = ttk.Frame(self, padding=10)
        tree_frame.pack(expand=True, fill='both')

        columns = ('login', 'logout')
        tree = ttk.Treeview(tree_frame, columns=columns, show='headings')
        
        vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=tree.yview)
        hsb = ttk.Scrollbar(tree_frame, orient="horizontal", command=tree.xview)
        tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        tree.heading('login', text='Daxil Olma Vaxtı')
        tree.heading('logout', text='Çıxış Vaxtı')

        tree.column('login', width=220, anchor='center')
        tree.column('logout', width=220, anchor='center')
        
        vsb.pack(side='right', fill='y')
        hsb.pack(side='bottom', fill='x')
        tree.pack(side='left', expand=True, fill='both')

        login_data = database.get_login_history(user_id)

        if not login_data:
            tree.destroy()
            vsb.destroy()
            hsb.destroy()
            ttk.Label(tree_frame, text="Bu istifadəçi üçün giriş tarixçəsi tapılmadı.", font=("Helvetica", 12)).pack(pady=20)
        else:
            for login_time, logout_time in login_data:
                login_str = login_time.strftime('%d.%m.%Y %H:%M:%S') if login_time else "Məlumat yoxdur"
                logout_str = logout_time.strftime('%d.%m.%Y %H:%M:%S') if logout_time else "Sessiya aktivdir / Düzgün bağlanmayıb"
                tree.insert('', 'end', values=(login_str, logout_str))