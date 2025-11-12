import tkinter as tk
from tkinter import ttk, Toplevel

# Proyekt importları
from database import database
from .components import mezuniyyet_muddetini_hesabla
from .vacation_tree import VacationTreeView
from datetime import date

class ArchiveWindow(Toplevel):
    def __init__(self, parent, all_employee_data, current_user):
        super().__init__(parent)
        self.title("Arxiv Məlumatları")
        self.geometry("850x500")
        self.transient(parent)
        self.grab_set()

        self.all_employee_data = all_employee_data
        self.current_user = current_user

        self.create_widgets()

    # Tema sistemi silindi

    def create_widgets(self):
        main_frame = ttk.Frame(self, padding=10)
        main_frame.pack(fill="both", expand=True)

        top_frame = ttk.Frame(main_frame)
        top_frame.pack(fill='x', pady=(0, 10))

        ttk.Label(top_frame, text="İşçi seçin:").pack(side='left', padx=(0, 5))
        employee_names = sorted(self.all_employee_data.keys())
        self.emp_combo = ttk.Combobox(top_frame, values=employee_names, state="readonly", width=30)
        self.emp_combo.pack(side='left', padx=5)

        ttk.Label(top_frame, text="İli seçin:").pack(side='left', padx=(10, 5))
        years = list(range(date.today().year - 1, 2020, -1)) # Cari il xaric, keçmiş illər
        self.year_combo = ttk.Combobox(top_frame, values=years, state="readonly")
        self.year_combo.pack(side='left', padx=5)
        
        ttk.Button(top_frame, text="Göstər", command=self.show_archive_data).pack(side='left', padx=10)

        self.summary_frame = ttk.Frame(main_frame, padding=5)
        self.summary_frame.pack(fill='x')
        
        self.results_frame = ttk.Frame(main_frame)
        self.results_frame.pack(fill='both', expand=True)
        
        ttk.Label(self.results_frame, text="Zəhmət olmasa, yuxarıdan işçi və il seçib 'Göstər' düyməsinə basın.", justify="center").pack(pady=50)

    def show_archive_data(self):
        # Köhnə nəticələri təmizlə
        for widget in self.results_frame.winfo_children():
            widget.destroy()
        for widget in self.summary_frame.winfo_children():
            widget.destroy()

        selected_name = self.emp_combo.get()
        selected_year_str = self.year_combo.get()

        if not selected_name or not selected_year_str:
            ttk.Label(self.results_frame, text="Zəhmət olmasa, işçi və il seçin.").pack(pady=20)
            return

        selected_year = int(selected_year_str)
        employee_info = self.all_employee_data.get(selected_name)
        if not employee_info:
            return

        archived_vacations = database.load_archived_vacations_for_year(employee_info['db_id'], selected_year)

        # Arxivdəki il üçün ümumi və istifadə edilmiş günləri hesabla
        # Qeyd: Bu, sadəcə təxmini bir hesabatdır, çünki illik məzuniyyət günləri dəyişmiş ola bilər.
        # Dəqiq hesabat üçün hər ilin sonunda məlumatları saxlamaq lazımdır.
        umumi_gun = 30 # Standart olaraq
        istifade_olunmus = sum(mezuniyyet_muddetini_hesabla(v['baslama'], v['bitme']) for v in archived_vacations if v.get('status') == 'approved' and not v.get('aktiv_deyil', False))
        qaliq_gun = umumi_gun - istifade_olunmus

        self._create_summary_labels(self.summary_frame, umumi_gun, istifade_olunmus, qaliq_gun)

        if not archived_vacations:
            ttk.Label(self.results_frame, text=f"{selected_year}-ci il üçün arxiv məlumatı tapılmadı.").pack(pady=20)
            return

        # VacationTreeView-ə göndərmək üçün məlumat strukturunu hazırla
        info_archive = {
            "name": selected_name,
            "goturulen_icazeler": archived_vacations
        }
        
        tree_frame = VacationTreeView(self.results_frame, self, info_archive, self.current_user, self.show_archive_data)
        tree_frame.pack(expand=True, fill='both')
    
    def _create_summary_labels(self, parent, total, used, remaining):
        """Hesabat üçün labelləri yaradan köməkçi funksiya."""
        style = ttk.Style()
        style.configure("Summary.TLabel", font=("Helvetica", 9))
        style.configure("SummaryValue.TLabel", font=("Helvetica", 10, "bold"))
        
        frame_total = ttk.Frame(parent)
        frame_total.pack(side='left', padx=10)
        ttk.Label(frame_total, text="İllik Hüquq (Təxmini):", style="Summary.TLabel").pack()
        ttk.Label(frame_total, text=f"{total} gün", style="SummaryValue.TLabel").pack()

        frame_used = ttk.Frame(parent)
        frame_used.pack(side='left', padx=10)
        ttk.Label(frame_used, text="İstifadə:", style="Summary.TLabel").pack()
        ttk.Label(frame_used, text=f"{used} gün", style="SummaryValue.TLabel").pack()

        frame_rem = ttk.Frame(parent)
        frame_rem.pack(side='left', padx=10)
        ttk.Label(frame_rem, text="Qalıq (Təxmini):", style="Summary.TLabel").pack()
        ttk.Label(frame_rem, text=f"{remaining} gün", style="SummaryValue.TLabel", foreground="green" if remaining >= 0 else "red").pack()
        
        ttk.Separator(parent, orient='vertical').pack(side='left', fill='y', padx=10, expand=True)