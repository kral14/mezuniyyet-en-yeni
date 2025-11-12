# Setup Üçün Lazım Olan Fayllar

## ✅ Əsas Setup Faylları (Mütləq Lazımdır)

### 1. **EXE Yaradılması Üçün:**
- ✅ `build_exe.py` - EXE yaratma skripti (əsas)
- ✅ `MezuniyyetSistemi.spec` - PyInstaller konfiqurasiya faylı
- ✅ `app.manifest` - Windows manifest faylı
- ✅ `setup files/version_info.txt` - Versiya məlumatı (avtomatik yaradılır)

### 2. **Installer Yaradılması Üçün:**
- ✅ `setup.iss` - Inno Setup konfiqurasiya faylı
- ✅ `create_setup.bat` - Setup installer yaratma skripti

### 3. **Avtomatik Build Üçün:**
- ✅ `run_build.bat` - Tam avtomatik build skripti (tövsiyə edilir)
- ✅ `rebuild_exe.bat` - EXE-ni yenidən yaratmaq üçün

### 4. **Launcher:**
- ✅ `launcher.bat` - Proqramı işə salmaq üçün launcher script

## 📋 İstifadə Sırası

### Variant 1: Avtomatik (Tövsiyə edilir)
```cmd
run_build.bat
```
Bu skript:
1. Python və PyInstaller yoxlayır
2. EXE faylı yaradır
3. Inno Setup ilə installer yaradır

### Variant 2: Manual
```cmd
# 1. EXE yarat
python build_exe.py

# 2. Installer yarat (Inno Setup lazımdır)
create_setup.bat
```

## ❌ Lazımsız Fayllar (Silinə bilər)

Bu fayllar setup üçün lazım deyil, yalnız fix/development üçündür:
- ❌ `fix_email_check.bat` - Fix script
- ❌ `fix_imports.py` - Fix script  
- ❌ `fix_password_reset.bat` - Fix script
- ❌ `copy_exe.bat` - Köçürmə script

## 📦 Nəticə Faylları

Build tamamlandıqdan sonra yaradılan fayllar:

### EXE Faylı:
- **Yol:** `setup files/dist/MezuniyyetSistemi.exe`
- **Ölçü:** ~30-50 MB

### Setup Installer:
- **Yol:** `dist/MezuniyyetSistemi_Setup_v7.1_NoAdmin.exe`
- **Ölçü:** ~35-55 MB

## 🔧 Tələb Olunan Proqramlar

1. **Python 3.x** - Proqramın özü üçün
2. **PyInstaller** - EXE yaratmaq üçün
   ```cmd
   pip install pyinstaller
   ```
3. **Inno Setup 6** (opsional) - Professional installer üçün
   - Yüklə: https://jrsoftware.org/isdl.php

## 📝 Qeydlər

- `setup files/version_info.txt` avtomatik yaradılır, əllə dəyişdirməyə ehtiyac yoxdur
- `build/` və `dist/` qovluqları avtomatik yaradılır və silinə bilər
- Versiya nömrəsi `build_exe.py` faylında təyin edilir

