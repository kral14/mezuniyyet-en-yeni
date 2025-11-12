# setup_windows.py

import tkinter as tk
from tkinter import ttk, messagebox

class TenantLinkWindow(tk.Toplevel):
    def __init__(self, parent, check_link_callback):
        super().__init__(parent)
        self.title("Şirkətə Qoşulma")
        self.geometry("400x150")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        self.check_link_callback = check_link_callback
        self.result = None

        main_frame = ttk.Frame(self, padding=20)
        main_frame.pack(expand=True, fill='both')

        ttk.Label(main_frame, text="Zəhmət olmasa, şirkətinizin qoşulma linkini daxil edin:").pack(pady=(0, 5))
        
        self.link_var = tk.StringVar()
        self.link_entry = ttk.Entry(main_frame, textvariable=self.link_var, width=50)
        self.link_entry.pack(pady=5, ipady=4)
        self.link_entry.focus()
        
        connect_button = ttk.Button(main_frame, text="Yoxla və Qoşul", command=self.connect)
        connect_button.pack(pady=10)
        
        self.link_entry.bind('<Return>', lambda event: self.connect())
        self.protocol("WM_DELETE_WINDOW", self.on_close)

    def connect(self):
        link = self.link_var.get().strip()
        if not link:
            messagebox.showwarning("Xəta", "Link xanası boş ola bilməz.", parent=self)
            return
        
        is_successful, message = self.check_link_callback(link)
        
        if is_successful:
            self.result = link
            self.destroy()
        else:
            messagebox.showerror("Xəta", message, parent=self)
            self.link_entry.focus()
            self.link_entry.selection_range(0, 'end')

    def on_close(self):
        self.result = None
        self.destroy()