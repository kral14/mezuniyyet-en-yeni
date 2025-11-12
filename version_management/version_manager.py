#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Versiya İdarəetmə Proqramı
Məzuniyyət proqramının versiyalarını idarə edir
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import json
import shutil
import zipfile
from datetime import datetime
import sys

class VersionManager:
    def __init__(self, parent=None):
        self.parent = parent
        self.versions_file = os.path.join(os.path.dirname(__file__), "versions.json")
        self.settings_file = os.path.join(os.path.dirname(__file__), "version_manager_settings.json")
        self.versions_data = self.load_versions()
        self.settings = self.load_settings()
        
        # Ana pəncərə
        self.window = tk.Toplevel(parent) if parent else tk.Tk()
        self.window.title("Versiya İdarəetmə Proqramı")
        self.window.geometry("800x600")
        self.window.resizable(True, True)
        
        # Pəncərəni mərkəzə yerləşdir
        self.center_window()
        
        # UI yarad
        self.create_widgets()
        
        # Versiyaları yüklə
        self.refresh_versions()
        
        # Avtomatik versiya nömrəsi və papka yollarını təyin et
        self.set_auto_values()
    
    def center_window(self):
        """Pəncərəni ekranın mərkəzinə yerləşdirir"""
        self.window.update_idletasks()
        width = self.window.winfo_width()
        height = self.window.winfo_height()
        x = (self.window.winfo_screenwidth() // 2) - (width // 2)
        y = (self.window.winfo_screenheight() // 2) - (height // 2)
        self.window.geometry(f"{800}x{600}+{x}+{y}")
    
    def create_widgets(self):
        """UI elementlərini yaradır"""
        # Ana frame
        main_frame = ttk.Frame(self.window, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Başlıq
        title_label = ttk.Label(main_frame, text="Versiya İdarəetmə Proqramı", 
                               font=("Segoe UI", 16, "bold"))
        title_label.pack(pady=(0, 20))
        
        # Yeni versiya yaratma hissəsi
        create_frame = ttk.LabelFrame(main_frame, text="Yeni Versiya Yarat", padding="10")
        create_frame.pack(fill=tk.X, pady=(0, 20))
        
        # Versiya adı
        ttk.Label(create_frame, text="Versiya Adı:").grid(row=0, column=0, sticky=tk.W, padx=(0, 10))
        self.version_var = tk.StringVar()
        version_entry = ttk.Entry(create_frame, textvariable=self.version_var, width=30)
        version_entry.grid(row=0, column=1, sticky=tk.W, padx=(0, 10))
        
        # Qeydlər
        ttk.Label(create_frame, text="Qeydlər:").grid(row=1, column=0, sticky=tk.W, padx=(0, 10), pady=(10, 0))
        self.notes_var = tk.StringVar()
        notes_entry = ttk.Entry(create_frame, textvariable=self.notes_var, width=50)
        notes_entry.grid(row=1, column=1, sticky=tk.W, padx=(0, 10), pady=(10, 0))
        
        # Mənbə papka seçimi
        ttk.Label(create_frame, text="Mənbə Papka:").grid(row=2, column=0, sticky=tk.W, padx=(0, 10), pady=(10, 0))
        self.source_var = tk.StringVar()
        source_entry = ttk.Entry(create_frame, textvariable=self.source_var, width=40)
        source_entry.grid(row=2, column=1, sticky=tk.W, padx=(0, 10), pady=(10, 0))
        
        source_btn = ttk.Button(create_frame, text="Seç", command=self.select_source_folder)
        source_btn.grid(row=2, column=2, padx=(10, 0), pady=(10, 0))
        
        # Hədəf papka seçimi
        ttk.Label(create_frame, text="Hədəf Papka:").grid(row=3, column=0, sticky=tk.W, padx=(0, 10), pady=(10, 0))
        self.target_var = tk.StringVar()
        target_entry = ttk.Entry(create_frame, textvariable=self.target_var, width=40)
        target_entry.grid(row=3, column=1, sticky=tk.W, padx=(0, 10), pady=(10, 0))
        
        target_btn = ttk.Button(create_frame, text="Seç", command=self.select_target_folder)
        target_btn.grid(row=3, column=2, padx=(10, 0), pady=(10, 0))
        
        # Yarat düyməsi
        create_btn = ttk.Button(create_frame, text="Versiya Yarat", command=self.create_version)
        create_btn.grid(row=4, column=1, pady=(20, 0))
        
        # Mövcud versiyalar hissəsi
        versions_frame = ttk.LabelFrame(main_frame, text="Mövcud Versiyalar", padding="10")
        versions_frame.pack(fill=tk.BOTH, expand=True)
        
        # Versiyalar cədvəli
        columns = ("Versiya", "Tarix", "Qeydlər", "Fayl Sayı")
        self.tree = ttk.Treeview(versions_frame, columns=columns, show="headings", height=10)
        
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=150)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(versions_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Versiya əməliyyatları
        actions_frame = ttk.Frame(versions_frame)
        actions_frame.pack(fill=tk.X, pady=(10, 0))
        
        ttk.Button(actions_frame, text="Versiyanı Aç", command=self.open_version).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(actions_frame, text="Versiyanı Sil", command=self.delete_version).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(actions_frame, text="Versiyanı Kopyala", command=self.copy_version).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(actions_frame, text="Yenilə", command=self.refresh_versions).pack(side=tk.LEFT)
    
    def select_source_folder(self):
        """Mənbə papka seçir"""
        folder = filedialog.askdirectory(title="Mənbə papka seçin")
        if folder:
            self.source_var.set(folder)
    
    def select_target_folder(self):
        """Hədəf papka seçir"""
        folder = filedialog.askdirectory(title="Hədəf papka seçin")
        if folder:
            self.target_var.set(folder)
    
    def create_version(self):
        """Yeni versiya yaradır"""
        version = self.version_var.get().strip()
        notes = self.notes_var.get().strip()
        source = self.source_var.get().strip()
        target = self.target_var.get().strip()
        
        if not all([version, source, target]):
            messagebox.showerror("Xəta", "Bütün sahələri doldurun!")
            return
        
        if not os.path.exists(source):
            messagebox.showerror("Xəta", "Mənbə papka mövcud deyil!")
            return
        
        if not os.path.exists(target):
            messagebox.showerror("Xəta", "Hədəf papka mövcud deyil!")
            return
        
        try:
            # Yalnız zip faylı yarat (papka kopyalamırıq)
            zip_path = os.path.join(target, f"v{version}.zip")
            if os.path.exists(zip_path):
                if not messagebox.askyesno("Təsdiq", f"v{version}.zip faylı artıq mövcuddur. Üzərinə yazılsın?"):
                    return
                os.remove(zip_path)
            
            # Zip faylı yarat
            self.create_zip(source, zip_path)
            
            # Versiya məlumatlarını əlavə et
            version_data = {
                "version": version,
                "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "notes": notes,
                "source_path": source,
                "target_path": target,
                "zip_path": zip_path,
                "files_count": self.count_files(source)
            }
            
            self.versions_data["versions"].append(version_data)
            self.save_versions()
            
            # Papka yollarını saxla
            self.settings["last_source_folder"] = source
            self.settings["last_target_folder"] = target
            self.settings["last_version"] = version
            self.save_settings()
            
            messagebox.showinfo("Uğurlu", f"v{version} versiyası uğurla yaradıldı!")
            self.refresh_versions()
            
            # Sahələri təmizlə (versiya nömrəsini avtomatik artır)
            next_version = self.get_next_version()
            self.version_var.set(next_version)
            self.notes_var.set("")
            
        except Exception as e:
            messagebox.showerror("Xəta", f"Versiya yaradılarkən xəta: {e}")
    
    def create_zip(self, source, zip_path):
        """Zip faylı yaradır"""
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(source):
                # Gizli papkaları və faylları atla
                dirs[:] = [d for d in dirs if not d.startswith('.')]
                files = [f for f in files if not f.startswith('.')]
                
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, source)
                    zipf.write(file_path, arcname)
    
    def count_files(self, folder):
        """Papkadakı fayl sayını hesablayır"""
        count = 0
        for root, dirs, files in os.walk(folder):
            dirs[:] = [d for d in dirs if not d.startswith('.')]
            files = [f for f in files if not f.startswith('.')]
            count += len(files)
        return count
    
    def load_versions(self):
        """Versiya məlumatlarını yükləyir"""
        if os.path.exists(self.versions_file):
            try:
                with open(self.versions_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                pass
        
        return {"versions": []}
    
    def save_versions(self):
        """Versiya məlumatlarını saxlayır"""
        with open(self.versions_file, 'w', encoding='utf-8') as f:
            json.dump(self.versions_data, f, ensure_ascii=False, indent=2)
    
    def load_settings(self):
        """Təyinləmələri yükləyir"""
        if os.path.exists(self.settings_file):
            try:
                with open(self.settings_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                pass
        
        return {
            "last_source_folder": "",
            "last_target_folder": "",
            "last_version": "1.0"
        }
    
    def save_settings(self):
        """Təyinləmələri saxlayır"""
        with open(self.settings_file, 'w', encoding='utf-8') as f:
            json.dump(self.settings, f, ensure_ascii=False, indent=2)
    
    def get_next_version(self):
        """Növbəti versiya nömrəsini hesablayır"""
        if not self.versions_data["versions"]:
            return "1.0"
        
        # Ən son versiyanı tap
        versions = []
        for version in self.versions_data["versions"]:
            try:
                # Versiya nömrəsini parse et (məsələn: "7.2" -> [7, 2])
                parts = version["version"].split(".")
                if len(parts) == 2:
                    major, minor = int(parts[0]), int(parts[1])
                    versions.append((major, minor))
            except:
                continue
        
        if not versions:
            return "1.0"
        
        # Ən böyük versiyanı tap
        latest = max(versions)
        # Minor versiyanı artır
        return f"{latest[0]}.{latest[1] + 1}"
    
    def set_auto_values(self):
        """Avtomatik versiya nömrəsi və papka yollarını təyin edir"""
        # Avtomatik versiya nömrəsi
        next_version = self.get_next_version()
        self.version_var.set(next_version)
        
        # Son istifadə edilən papka yolları
        if self.settings.get("last_source_folder"):
            self.source_var.set(self.settings["last_source_folder"])
        
        if self.settings.get("last_target_folder"):
            self.target_var.set(self.settings["last_target_folder"])
    
    def refresh_versions(self):
        """Versiyalar cədvəlini yeniləyir"""
        # Mövcud elementləri təmizlə
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Versiyaları əlavə et
        for version in self.versions_data["versions"]:
            self.tree.insert("", tk.END, values=(
                version["version"],
                version["date"],
                version["notes"],
                version.get("files_count", 0)
            ))
    
    def open_version(self):
        """Seçilmiş versiyanı açar"""
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("Xəbərdarlıq", "Versiya seçin!")
            return
        
        item = self.tree.item(selection[0])
        version = item['values'][0]
        
        # Versiya məlumatlarını tap
        version_data = None
        for v in self.versions_data["versions"]:
            if v["version"] == version:
                version_data = v
                break
        
        if version_data and os.path.exists(version_data["target_path"]):
            os.startfile(version_data["target_path"])
        else:
            messagebox.showerror("Xəta", "Versiya papkası tapılmadı!")
    
    def delete_version(self):
        """Seçilmiş versiyanı silir"""
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("Xəbərdarlıq", "Versiya seçin!")
            return
        
        item = self.tree.item(selection[0])
        version = item['values'][0]
        
        if not messagebox.askyesno("Təsdiq", f"v{version} versiyasını silmək istəyirsiniz?"):
            return
        
        # Versiya məlumatlarını tap və sil
        for i, v in enumerate(self.versions_data["versions"]):
            if v["version"] == version:
                # Papkanı sil
                if os.path.exists(v["target_path"]):
                    shutil.rmtree(v["target_path"])
                
                # Məlumatları sil
                del self.versions_data["versions"][i]
                break
        
        self.save_versions()
        self.refresh_versions()
        messagebox.showinfo("Uğurlu", f"v{version} versiyası silindi!")
    
    def copy_version(self):
        """Seçilmiş versiyanı kopyalayır"""
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("Xəbərdarlıq", "Versiya seçin!")
            return
        
        item = self.tree.item(selection[0])
        version = item['values'][0]
        
        # Yeni versiya adı al
        new_version = tk.simpledialog.askstring("Yeni Versiya", f"v{version} üçün yeni ad:")
        if not new_version:
            return
        
        # Versiya məlumatlarını tap
        version_data = None
        for v in self.versions_data["versions"]:
            if v["version"] == version:
                version_data = v
                break
        
        if not version_data:
            messagebox.showerror("Xəta", "Versiya məlumatları tapılmadı!")
            return
        
        # Hədəf papka seç
        target = filedialog.askdirectory(title="Hədəf papka seçin")
        if not target:
            return
        
        try:
            # Yeni versiya papkası yarat
            new_version_folder = os.path.join(target, f"v{new_version}")
            if os.path.exists(new_version_folder):
                if not messagebox.askyesno("Təsdiq", f"v{new_version} papkası artıq mövcuddur. Üzərinə yazılsın?"):
                    return
                shutil.rmtree(new_version_folder)
            
            # Versiyanı kopyala
            shutil.copytree(version_data["target_path"], new_version_folder)
            
            # Yeni versiya məlumatlarını əlavə et
            new_version_data = version_data.copy()
            new_version_data["version"] = new_version
            new_version_data["date"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            new_version_data["target_path"] = new_version_folder
            new_version_data["zip_path"] = os.path.join(new_version_folder, f"v{new_version}.zip")
            
            self.versions_data["versions"].append(new_version_data)
            self.save_versions()
            
            messagebox.showinfo("Uğurlu", f"v{new_version} versiyası uğurla kopyalandı!")
            self.refresh_versions()
            
        except Exception as e:
            messagebox.showerror("Xəta", f"Versiya kopyalanarkən xəta: {e}")

def main():
    """Ana funksiya"""
    app = VersionManager()
    app.window.mainloop()

if __name__ == "__main__":
    # Ayrıca işə salmaq üçün
    import tkinter as tk
    root = tk.Tk()
    root.withdraw()  # Ana pəncərəni gizlə
    app = VersionManager(root)
    app.window.mainloop()
