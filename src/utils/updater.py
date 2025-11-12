# updater_service.py (Düzgün versiya)

import tkinter as tk
from tkinter import messagebox
import requests
import os
import sys
import subprocess
import threading
from pathlib import Path
import time  # <-- ƏSAS DÜZƏLİŞ BURADADIR / EN ÖNEMLİ DÜZELTME BURADA
import logging

# --- YENİLƏMƏ ÜÇÜN KONFİQURASİYA ---
GITHUB_API_URL = "https://api.github.com/repos/kral14/mezuniyyet/releases/latest"

class UpdaterService:
    def __init__(self, ui_callbacks, current_version=None):
        self.ui_callbacks = ui_callbacks
        self.current_version = current_version

    def check_and_prompt_update(self):
        """Son versiyanı yoxlayır və popup göstərir. İstifadəçi razılaşsa, yeniləməyə başlayır."""
        def _check():
            try:
                logging.info("=== UPDATER SERVICE: Versiya yoxlaması başladı ===")
                self.ui_callbacks.get('update_status', lambda x: None)("Yeni versiya yoxlanılır...")
                
                # Verilənlər bazasından ən son versiyanı al
                latest_version = None
                
                logging.debug("UpdaterService: Verilənlər bazasından versiya yoxlanılır...")
                
                # Əvvəlcə PostgreSQL sistem sorğularından yoxla
                try:
                    logging.debug("UpdaterService: PostgreSQL system_queries yoxlanılır...")
                    from database.system_queries import get_latest_version
                    latest_version = get_latest_version()
                    logging.info(f"UpdaterService: PostgreSQL-dən versiya: {latest_version}")
                except Exception as e:
                    logging.warning(f"UpdaterService: PostgreSQL system_queries xətası: {e}")
                    pass
                
                # Əgər PostgreSQL-dən alınmadısa, user_queries-dən yoxla
                if not latest_version:
                    try:
                        logging.debug("UpdaterService: PostgreSQL user_queries yoxlanılır...")
                        from database.user_queries import get_latest_version
                        latest_version = get_latest_version()
                        logging.info(f"UpdaterService: PostgreSQL user_queries-dən versiya: {latest_version}")
                    except Exception as e:
                        logging.warning(f"UpdaterService: PostgreSQL user_queries xətası: {e}")
                        pass
                
                # SQLite yoxlaması silindi
                
                if latest_version and latest_version != self.current_version:
                    logging.info(f"UpdaterService: Yeni versiya tapıldı! Cari: {self.current_version}, Yeni: {latest_version}")
                    answer = messagebox.askyesno(
                        "Yeniləmə mövcuddur",
                        f"Yeni versiya mövcuddur: {latest_version}\nYeniləmək istəyirsiniz?"
                    )
                    if answer:
                        logging.info("UpdaterService: İstifadəçi yeniləməyə razılaşdı")
                        self.start_update_in_thread(latest_version)
                else:
                    logging.info("UpdaterService: Cari versiya güncəldir")
                    messagebox.showinfo("Yeniləmə", "Siz ən son versiyadan istifadə edirsiniz.")
            except Exception as e:
                messagebox.showerror("Yeniləmə Xətası", f"Yeniləmə yoxlanılarkən xəta baş verdi:\n{e}")
                if 'on_error' in self.ui_callbacks:
                    self.ui_callbacks['on_error']()
        threading.Thread(target=_check, daemon=True).start()

    def start_update_in_thread(self, latest_version=None):
        """Yeniləmə prosesini arxa fonda (background thread) başladır."""
        logging.info(f"UpdaterService: Update thread başladılır (versiya: {latest_version})")
        threading.Thread(target=self._run_update_task, args=(latest_version,), daemon=True).start()

    def _run_update_task(self, latest_version=None):
        """Yeni versiyanı endirir və istifadəçiyə məlumat verir."""
        try:
            logging.info("=== UPDATER SERVICE: Update prosesi başladı ===")
            self.ui_callbacks.get('update_status', lambda x: None)("Yeni versiya endirilir...")
            
            # Əgər latest_version verilməyibsə, GitHub-dan al
            if not latest_version:
                logging.debug("UpdaterService: GitHub-dan versiya məlumatı alınır...")
                response = requests.get(GITHUB_API_URL, timeout=10)
                response.raise_for_status()
                latest_data = response.json()
                latest_version = latest_data['tag_name']
                logging.info(f"UpdaterService: GitHub-dan alınan versiya: {latest_version}")
                asset = next((a for a in latest_data['assets'] if 'setup' in a['name'].lower() and a['name'].endswith('.exe')), None)
                if not asset:
                    raise Exception("GitHub Releases-də 'setup.exe' faylı tapılmadı.")
                asset_url = asset['browser_download_url']
                setup_filename = asset['name']
                logging.info(f"UpdaterService: Setup faylı: {setup_filename}")
            else:
                # Verilənlər bazasından alınan versiya üçün GitHub-dan uyğun asset tap
                logging.debug("UpdaterService: Verilənlər bazasından alınan versiya üçün GitHub asset axtarılır...")
                response = requests.get(GITHUB_API_URL, timeout=10)
                response.raise_for_status()
                latest_data = response.json()
                asset = next((a for a in latest_data['assets'] if 'setup' in a['name'].lower() and a['name'].endswith('.exe')), None)
                if not asset:
                    raise Exception("GitHub Releases-də 'setup.exe' faylı tapılmadı.")
                asset_url = asset['browser_download_url']
                setup_filename = asset['name']
                logging.info(f"UpdaterService: Setup faylı: {setup_filename}")
            
            self.ui_callbacks.get('update_status', lambda x: None)(f"{setup_filename} endirilir...")
            downloads_path = str(Path.home() / "Downloads")
            save_path = os.path.join(downloads_path, setup_filename)
            logging.info(f"UpdaterService: Fayl endiriləcək: {save_path}")
            
            response = requests.get(asset_url, stream=True, timeout=180)
            response.raise_for_status()
            total_size = int(response.headers.get('content-length', 0))
            logging.info(f"UpdaterService: Fayl ölçüsü: {total_size} byte")
            
            with open(save_path, 'wb') as f:
                downloaded_size = 0
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
                    downloaded_size += len(chunk)
                    if total_size > 0:
                        progress = (downloaded_size / total_size) * 100
                        self.ui_callbacks.get('update_progress', lambda x: None)(progress)
                        logging.debug(f"UpdaterService: Endirilən: {downloaded_size}/{total_size} ({progress:.1f}%)")
            self.ui_callbacks.get('update_status', lambda x: None)("Quraşdırma başladılır...")
            time.sleep(1) # Endirmənin bitməsinə əmin olmaq üçün qısa fasilə
            
            logging.info("UpdaterService: Fayl endirildi, quraşdırma başladılır...")
            
            # Progress dialog-u bağla (əgər varsa)
            if 'update_status' in self.ui_callbacks:
                self.ui_callbacks['update_status']("Quraşdırma başladılır...")
                time.sleep(0.5)  # İstifadəçiyə son status mesajını göstərmək üçün
            
            # Uğurlu update callback-i çağır
            if 'on_success' in self.ui_callbacks:
                logging.info("UpdaterService: Update uğurlu oldu, success callback çağırılır")
                self.ui_callbacks['on_success']()
            
            logging.info(f"UpdaterService: Setup faylı işə salınır: {save_path}")
            subprocess.Popen([save_path])
            logging.info("UpdaterService: Proqram bağlanır...")
            sys.exit()
        except Exception as e:
            logging.error(f"UpdaterService: Update xətası: {e}", exc_info=True)
            messagebox.showerror("Yeniləmə Xətası", f"Yeniləmə zamanı xəta baş verdi:\n{e}")
            if 'on_error' in self.ui_callbacks:
                logging.info("UpdaterService: Error callback çağırılır")
                self.ui_callbacks['on_error']()