# run_build.bat - Adi Build

## 📋 Təsvir
**Normal build skripti** - Adi build üçün istifadə edilir.

## ✅ Nə edir?
1. **Python və PyInstaller yoxlayır** - Yoxdursa avtomatik quraşdırır
2. **EXE faylı yaradır** - `build_exe.py` skriptini işə salır
3. **Setup installer yaradır** - Inno Setup ilə professional installer hazırlayır (əgər quraşdırılıbsa)

## 🎯 Nə vaxt istifadə edilir?
- ✅ Normal build lazımdır
- ✅ Kod dəyişikliklərindən sonra
- ✅ Adi build prosesi

## 📁 Nəticə faylları
- **EXE:** `../setup files/dist/MezuniyyetSistemi.exe`
- **Installer:** `../dist/MezuniyyetSistemi_Setup_v7.1_NoAdmin.exe`

## 🚀 İstifadə
```cmd
cd "setup etmek\adi build"
run_build.bat
```

## ⚙️ Tələb olunan proqramlar
- Python 3.x (avtomatik yoxlanılır)
- PyInstaller (avtomatik quraşdırılır)
- Inno Setup 6 (opsional, installer üçün)

