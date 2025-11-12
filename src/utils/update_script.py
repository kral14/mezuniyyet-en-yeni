
import os
import sys
import shutil
import urllib.request
import zipfile
import subprocess

def download_and_install_update():
    try:
        # Yeni versiyanı yüklə
        print("Yeni versiya yüklənir...")
        url = "https://github.com/your-repo/mezuniyyet-sistemi/releases/latest/download/mezuniyyet-sistemi-6.7.zip"
        
        # Yükləmə prosesi
        urllib.request.urlretrieve(url, "update.zip")
        
        # Zip faylını aç
        with zipfile.ZipFile("update.zip", 'r') as zip_ref:
            zip_ref.extractall("temp_update")
        
        # Köhnə faylları yedəklə
        if os.path.exists("backup"):
            shutil.rmtree("backup")
        shutil.copytree(".", "backup", ignore=shutil.ignore_patterns("backup", "temp_update", "update.zip"))
        
        # Yeni faylları kopyala
        for item in os.listdir("temp_update"):
            s = os.path.join("temp_update", item)
            d = os.path.join(".", item)
            if os.path.isdir(s):
                shutil.copytree(s, d, dirs_exist_ok=True)
            else:
                shutil.copy2(s, d)
        
        # Təmizlik
        shutil.rmtree("temp_update")
        os.remove("update.zip")
        
        print("Update tamamlandı! Proqram yenidən başladılacaq...")
        
        # Proqramı yenidən başlat
        subprocess.Popen([sys.executable, "unified_app.py"])
        sys.exit(0)
        
    except Exception as e:
        print(f"Update xətası: {e}")
        messagebox.showerror("Update Xətası", f"Update zamanı xəta baş verdi: {e}")

if __name__ == "__main__":
    download_and_install_update()
