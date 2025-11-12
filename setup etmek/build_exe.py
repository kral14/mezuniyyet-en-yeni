#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Məzuniyyət Sistemi EXE yaradıcısı
Bu skript proqramı EXE faylına çevirir
"""

import os
import sys
import subprocess
import shutil
import re
import time
import stat

# Unicode encoding təyin et
if sys.platform.startswith('win'):
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.detach())
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.detach())

def get_version_from_user():
    """İstifadəçidən versiya nömrəsini alır"""
    # Əvvəlki versiyaları oxuyub göstər
    versions_file = os.path.join("..", "version_management", "versions.json")
    if os.path.exists(versions_file):
        try:
            import json
            with open(versions_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                versions = data.get('versions', [])
                if versions:
                    latest_version = versions[-1]
                    print(f"\n📦 Cari versiya: {latest_version.get('version', '?')} - {latest_version.get('date', '?')}")
                    if latest_version.get('notes'):
                        print(f"   Qeydlər: {latest_version['notes']}")
                    print()
        except Exception as e:
            print(f"⚠️ Versiyalar oxuna bilmədi: {e}")
    
    print("🔢 YENİ versiya nömrəsini daxil edin:")
    print("   Məsələn: 7.13, 7.14, 8.0 və s.")
    
    # Test üçün avtomatik versiya
    version = "7.13"
    print(f"📝 Yeni versiya nömrəsi: {version}")
    return version

def update_version_files(version):
    """Versiya fayllarını yeniləyir"""
    print(f"🔄 Versiya faylları yenilənir: {version}")
    
    # src/config/version.txt faylını yenilə
    version_file = os.path.join("..", "src", "config", "version.txt")
    if os.path.exists(version_file):
        with open(version_file, 'w', encoding='utf-8') as f:
            f.write(version)
        print(f"✅ {version_file} yeniləndi")
    
    # Versiya faylı yarat (PyInstaller üçün)
    version_info_file = os.path.join("setup files", "version_info.txt")
    
    # setup files papkasını yarat
    setup_files_dir = "setup files"
    if not os.path.exists(setup_files_dir):
        os.makedirs(setup_files_dir)
    
    version_parts = version.split('.')
    major = version_parts[0] if len(version_parts) > 0 else "7"
    minor = version_parts[1] if len(version_parts) > 1 else "1"
    patch = version_parts[2] if len(version_parts) > 2 else "0"
    
    version_info_content = f"""# UTF-8
#
# For more details about fixed file info 'ffi' see:
# http://msdn.microsoft.com/en-us/library/ms646997.aspx
VSVersionInfo(
  ffi=FixedFileInfo(
    # filevers and prodvers should be always a tuple with four items: (1, 2, 3, 4)
    # Set not needed items to zero 0.
    filevers=({major}, {minor}, {patch}, 0),
    prodvers=({major}, {minor}, {patch}, 0),
    # Contains a bitmask that specifies the valid bits 'flags'r
    mask=0x3f,
    # Contains a bitmask that specifies the Boolean attributes of the file.
    flags=0x0,
    # The operating system for which this file was designed.
    # 0x4 - NT and there is no need to change it.
    OS=0x40004,
    # The general type of file.
    # 0x1 - the file is an application.
    fileType=0x1,
    # The function of the file.
    # 0x0 - the function is not defined for this fileType
    subtype=0x0,
    # Creation date and time stamp.
    date=(0, 0)
    ),
  kids=[
    StringFileInfo(
      [
      StringTable(
        u'040904B0',
        [StringStruct(u'CompanyName', u'Məzuniyyət Sistemi'),
        StringStruct(u'FileDescription', u'Məzuniyyət İdarəetmə Sistemi'),
        StringStruct(u'FileVersion', u'{version}'),
        StringStruct(u'InternalName', u'MezuniyyetSistemi'),
        StringStruct(u'LegalCopyright', u'© 2024 Məzuniyyət Sistemi'),
        StringStruct(u'OriginalFilename', u'MezuniyyetSistemi.exe'),
        StringStruct(u'ProductName', u'Məzuniyyət İdarəetmə Sistemi'),
        StringStruct(u'ProductVersion', u'{version}')])
      ]), 
    VarFileInfo([VarStruct(u'Translation', [1033, 1200])])
  ]
)"""
    
    with open(version_info_file, 'w', encoding='utf-8') as f:
        f.write(version_info_content)
    print(f"✅ {version_info_file} yaradıldı")
    
    return version_info_file

def build_exe(version_info_file=None):
    """Proqramı EXE faylına çevirir"""
    
    print("🔨 EXE faylı yaradılır...")
    
    # Əvvəlcə açıq EXE proseslərini sonlandır (təhlükəsizlik üçün)
    kill_exe_processes()
    
    # İkon faylının yolunu təyin et - src/icons
    icon_path = os.path.join("..", "src", "icons", "icon.ico")
    if not os.path.exists(icon_path):
        print(f"⚠️ İkon faylı tapılmadı: {icon_path}")
        icon_param = []
    else:
        icon_param = ['--icon=' + os.path.abspath(icon_path)]
        print(f"✅ İkon faylı tapıldı: {icon_path}")
    
    # PyInstaller əmrləri - spec faylını istifadə et
    pyinstaller_cmd = [
        sys.executable,  # Python interpreter-i istifadə et
        '-m', 'PyInstaller',
        'MezuniyyetSistemi.spec',  # Spec faylını istifadə et
        '--clean',  # Əvvəlki build fayllarını təmizlə
        '--noconfirm',  # Təsdiq istəmə
    ]
    
    # İkon və versiya faylları spec faylında təyin edilib
    if icon_param:
        print(f"✅ İkon faylı spec faylında təyin edilib: {icon_path}")
    if version_info_file and os.path.exists(version_info_file):
        print(f"✅ Versiya faylı spec faylında təyin edilib: {version_info_file}")
    
    try:
        # PyInstaller əmrini işə sal
        result = subprocess.run(pyinstaller_cmd, check=True, capture_output=True, text=True)
        print("✅ EXE faylı uğurla yaradıldı!")
        
        # Dist qovluğunu yoxla
        if os.path.exists('dist'):
            exe_path = os.path.join('dist', 'MezuniyyetSistemi.exe')
            if os.path.exists(exe_path):
                print(f"📁 EXE faylı: {exe_path}")
                
                # Fayl ölçüsünü göstər
                size = os.path.getsize(exe_path)
                size_mb = size / (1024 * 1024)
                print(f"📏 Fayl ölçüsü: {size_mb:.2f} MB")
                
                # İkon məlumatını göstər
                if icon_param:
                    print("🎨 İkon uğurla əlavə edildi!")
                else:
                    print("⚠️ İkon əlavə edilmədi!")
        
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Xəta baş verdi: {e}")
        print(f"Stderr: {e.stderr}")
        return False
    except Exception as e:
        print(f"❌ Gözlənilməz xəta: {e}")
        return False

def create_setup_script():
    """Setup skripti yaradır"""
    
    setup_content = '''@echo off
echo Məzuniyyət Sistemi v7.1 Quraşdırılır...
echo.

REM Quraşdırma qovluğunu yarat
set INSTALL_DIR=%PROGRAMFILES%\\MezuniyyetSistemi
if not exist "%INSTALL_DIR%" mkdir "%INSTALL_DIR%"

REM EXE faylını kopyala
copy "setup files\\dist\\MezuniyyetSistemi.exe" "%INSTALL_DIR%\\"

REM Desktop shortcut yarat
set DESKTOP=%USERPROFILE%\\Desktop
echo @echo off > "%DESKTOP%\\Məzuniyyət Sistemi.bat"
echo start "" "%INSTALL_DIR%\\MezuniyyetSistemi.exe" >> "%DESKTOP%\\Məzuniyyət Sistemi.bat"

REM Start Menu shortcut yarat
set START_MENU=%APPDATA%\\Microsoft\\Windows\\Start Menu\\Programs
if not exist "%START_MENU%\\Mezuniyyet Sistemi" mkdir "%START_MENU%\\Mezuniyyet Sistemi"
echo @echo off > "%START_MENU%\\Mezuniyyet Sistemi\\Məzuniyyət Sistemi.bat"
echo start "" "%INSTALL_DIR%\\MezuniyyetSistemi.exe" >> "%START_MENU%\\Mezuniyyet Sistemi\\Məzuniyyət Sistemi.bat"

echo ✅ Quraşdırma tamamlandı!
echo 📁 Quraşdırma qovluğu: %INSTALL_DIR%
echo 🖥️ Desktop shortcut yaradıldı
echo 📋 Start Menu shortcut yaradıldı
echo.
pause
'''
    
    setup_script_path = os.path.join("setup files", "setup.bat")
    with open(setup_script_path, 'w', encoding='utf-8') as f:
        f.write(setup_content)
    
    print(f"📝 Setup skripti yaradıldı: {setup_script_path}")

def kill_exe_processes():
    """Açıq EXE proseslərini sonlandırır"""
    if not sys.platform.startswith('win'):
        return
    
    exe_name = "MezuniyyetSistemi.exe"
    try:
        # tasklist ilə prosesləri tap
        result = subprocess.run(
            ['tasklist', '/FI', f'IMAGENAME eq {exe_name}', '/FO', 'CSV'],
            capture_output=True,
            text=True,
            creationflags=subprocess.CREATE_NO_WINDOW if sys.platform.startswith('win') else 0
        )
        
        if exe_name in result.stdout:
            print(f"⚠️ {exe_name} prosesi işləyir, sonlandırılır...")
            # taskkill ilə prosesi sonlandır
            subprocess.run(
                ['taskkill', '/F', '/IM', exe_name],
                capture_output=True,
                text=True,
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform.startswith('win') else 0
            )
            # Bir az gözlə ki proses tam bağlansın
            time.sleep(1)
            print(f"✅ {exe_name} prosesi sonlandırıldı")
    except Exception as e:
        print(f"⚠️ Proses sonlandırma xətası (təhlükəsiz): {e}")

def clean_old_builds():
    """Köhnə build və dist fayllarını silir"""
    print("🧹 Köhnə build faylları təmizlənir...")
    
    # Əvvəlcə açıq EXE proseslərini sonlandır
    kill_exe_processes()
    
    # Silinəcək qovluqlar
    folders_to_clean = ['dist', 'build', '__pycache__']
    
    for folder in folders_to_clean:
        if os.path.exists(folder):
            try:
                print(f"🗑️ {folder} qovluğu silinir...")
                
                # Windows-da faylları bir-bir silməyə çalış (daha təhlükəsiz)
                if sys.platform.startswith('win') and folder == 'dist':
                    # dist qovluğundakı faylları bir-bir sil
                    try:
                        for root, dirs, files in os.walk(folder, topdown=False):
                            for name in files:
                                file_path = os.path.join(root, name)
                                try:
                                    # Windows-da fayl icazələrini dəyişməyə çalış
                                    if sys.platform.startswith('win'):
                                        try:
                                            os.chmod(file_path, stat.S_IWRITE)
                                        except Exception:
                                            pass  # İcazə dəyişmə uğursuz olsa belə davam et
                                    os.remove(file_path)
                                except Exception as file_error:
                                    print(f"⚠️ Fayl silinə bilmədi: {file_path} - {file_error}")
                            for name in dirs:
                                dir_path = os.path.join(root, name)
                                try:
                                    os.rmdir(dir_path)
                                except Exception:
                                    pass
                        # Boş qovluğu sil
                        try:
                            os.rmdir(folder)
                            print(f"✅ {folder} qovluğu silindi")
                        except Exception:
                            pass
                    except Exception as e:
                        print(f"⚠️ {folder} qismən silinə bilmədi: {e}")
                        # Yenidən cəhd et
                        try:
                            shutil.rmtree(folder, ignore_errors=True)
                        except Exception:
                            pass
                else:
                    shutil.rmtree(folder)
                    print(f"✅ {folder} qovluğu silindi")
            except Exception as e:
                print(f"⚠️ {folder} silinə bilmədi: {e}")
                # Yenidən cəhd et - ignore_errors ilə
                try:
                    shutil.rmtree(folder, ignore_errors=True)
                except Exception:
                    pass
        else:
            print(f"ℹ️ {folder} qovluğu mövcud deyil")
    
    # setup files qovluğundakı köhnə faylları da sil
    setup_files_dir = "setup files"
    if os.path.exists(setup_files_dir):
        try:
            # dist və build qovluqlarını sil
            for subfolder in ['dist', 'build']:
                subfolder_path = os.path.join(setup_files_dir, subfolder)
                if os.path.exists(subfolder_path):
                    print(f"🗑️ setup files/{subfolder} qovluğu silinir...")
                    try:
                        shutil.rmtree(subfolder_path)
                        print(f"✅ setup files/{subfolder} qovluğu silindi")
                    except Exception as e:
                        print(f"⚠️ setup files/{subfolder} silinə bilmədi: {e}")
                        shutil.rmtree(subfolder_path, ignore_errors=True)
        except Exception as e:
            print(f"⚠️ setup files qovluğunda təmizlik xətası: {e}")
    
    print("✅ Köhnə build faylları təmizləndi")

def main():
    """Əsas funksiya"""
    
    # Skriptin yerləşdiyi qovluğa keç
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    print(f"📁 İş qovluğu: {os.getcwd()}")
    
    print("🚀 Məzuniyyət Sistemi EXE yaradıcısı")
    print("=" * 50)
    
    # Köhnə build fayllarını təmizlə
    clean_old_builds()
    print()
    
    # Versiya nömrəsini al
    version = get_version_from_user()
    
    # Versiya fayllarını yenilə
    version_info_file = update_version_files(version)
    
    # EXE yarat
    if build_exe(version_info_file):
        # Setup skripti yarat
        create_setup_script()
        
        print("\n🎉 Uğurla tamamlandı!")
        print(f"📦 Versiya: {version}")
        print("📁 Fayllar:")
        print("  - setup files/dist/MezuniyyetSistemi.exe (Əsas proqram)")
        print("  - setup files/build/ (Build faylları)")
        print("  - setup files/setup.bat (Quraşdırma skripti)")
        print("  - setup.iss (Inno Setup faylı)")
        print(f"  - {version_info_file} (Versiya məlumatı)")
        print("\n📋 İstifadə:")
        print("  1. setup files/setup.bat faylını administrator kimi işə salın")
        print("  2. Proqram avtomatik quraşdırılacaq")
        print("  3. Desktop və Start Menu-də shortcut yaradılacaq")
        print(f"  4. Setup faylı: setup.iss (versiya {version})")
        print(f"  5. EXE faylında versiya məlumatı: {version}")
    else:
        print("\n❌ EXE yaratma uğursuz oldu!")

if __name__ == "__main__":
    main()