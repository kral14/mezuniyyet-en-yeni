# Məzuniyyət Sistemi - Setup Faylları

Bu qovluqda Məzuniyyət Sistemi üçün bütün setup faylları yerləşir.

## 📁 Qovluq Strukturu

```
setup etmek/
├── build_exe.py          # EXE yaratma skripti
├── MezuniyyetSistemi.spec # PyInstaller spec faylı
├── run_build.bat         # Avtomatik build skripti
├── setup.iss            # Inno Setup konfiqurasiyası
└── setup files/         # Build nəticələri
    ├── dist/            # EXE faylı
    ├── build/           # Build faylları
    ├── setup.bat        # Quraşdırma skripti
    └── version_info.txt # Versiya məlumatı
```

## 🚀 İstifadə

### 1. EXE Faylı Yaratmaq

**Avtomatik (Tövsiyə edilir):**
```cmd
run_build.bat
```

**Əl ilə:**
```cmd
python build_exe.py
```

### 2. Setup Installer Yaratmaq

**Inno Setup ilə:**
1. Inno Setup 6 quraşdırın: https://jrsoftware.org/isdl.php
2. `setup.iss` faylını açın
3. "Compile" düyməsinə basın
4. Setup faylı `dist/` qovluğunda yaradılacaq

**Sadə Batch Script ilə:**
```cmd
setup files\setup.bat
```

## 📋 Faylların Təsviri

### `build_exe.py`
- EXE faylı yaratmaq üçün əsas skript
- Versiya məlumatlarını avtomatik yeniləyir
- PyInstaller ilə EXE yaradır
- İkon və versiya məlumatlarını əlavə edir

### `MezuniyyetSistemi.spec`
- PyInstaller konfiqurasiya faylı
- Bütün modulları düzgün import edir
- İkon və versiya məlumatlarını təyin edir
- Lazımsız modulları istisna edir

### `run_build.bat`
- Avtomatik build skripti
- Python və PyInstaller yoxlayır
- EXE faylı yaradır
- Inno Setup ilə installer yaradır

### `setup.iss`
- Inno Setup konfiqurasiyası
- Professional installer yaradır
- Admin icazəsi tələb etmir
- Desktop və Start Menu shortcut yaradır

## 🎯 Nəticələr

### EXE Faylı:
- **Yol:** `setup files/dist/MezuniyyetSistemi.exe`
- **Ölçü:** ~30-50 MB
- **İkon:** Daxil edilib
- **Versiya:** 7.1

### Setup Installer:
- **Yol:** `dist/MezuniyyetSistemi_Setup_v7.1_NoAdmin.exe`
- **Ölçü:** ~35-55 MB
- **Admin icazəsi:** Lazım deyil
- **Versiya:** 7.1

## 🔧 Xətaların Həlli

### PyInstaller tapılmadı:
```cmd
pip install pyinstaller
```

### İkon tapılmadı:
İkon faylının yolunu yoxlayın: `../src/icons/icon.ico`

### Inno Setup tapılmadı:
https://jrsoftware.org/isdl.php saytından yükləyin və quraşdırın

### Encoding xətaları:
Batch fayllarını UTF-8 encoding ilə saxlayın

## 📝 Versiya Yeniləmə

Yeni versiya yaratmaq üçün:

1. `build_exe.py` faylında versiya nömrəsini dəyişdirin
2. `setup.iss` faylında versiya nömrəsini dəyişdirin
3. `run_build.bat` faylını işə salın
4. Inno Setup ilə yeni installer yaradın

## 🎉 Uğurlu Build

Build uğurlu olduqdan sonra:

1. **EXE faylı:** `setup files/dist/MezuniyyetSistemi.exe`
2. **Setup installer:** `dist/MezuniyyetSistemi_Setup_v7.1_NoAdmin.exe`
3. **Quraşdırma skripti:** `setup files/setup.bat`

---

**Versiya:** 7.1  
**Tarix:** 2024  
**Müəllif:** Məzuniyyət Sistemi
