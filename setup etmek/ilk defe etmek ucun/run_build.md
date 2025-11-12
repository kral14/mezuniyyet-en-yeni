# run_build.bat

## 📋 Təsvir
**Tam avtomatik build skripti** - İlk dəfə build etmək və ya normal build üçün ən yaxşı seçim.

## ✅ Nə edir?
1. **Python və PyInstaller yoxlayır** - Yoxdursa avtomatik quraşdırır
2. **EXE faylı yaradır** - `build_exe.py` skriptini işə salır
3. **Setup installer yaradır** - Inno Setup ilə professional installer hazırlayır (əgər quraşdırılıbsa)

## 🎯 Nə vaxt istifadə edilir?
- ✅ İlk dəfə build edirsiniz
- ✅ Normal build lazımdır
- ✅ Hər şeyi avtomatik etmək istəyirsiniz
- ✅ **Ən tövsiyə edilən variant**

## 📁 Nəticə faylları
- **EXE:** `setup files/dist/MezuniyyetSistemi.exe`
- **Installer:** `dist/MezuniyyetSistemi_Setup_v7.1_NoAdmin.exe`

## 🚀 İstifadə
```cmd
cd setup etmek\scripts
run_build.bat
```

## ⚙️ Tələb olunan proqramlar
- Python 3.x (avtomatik yoxlanılır)
- PyInstaller (avtomatik quraşdırılır)
- Inno Setup 6 (opsional, installer üçün)

## 💡 Qeyd
Bu skript köhnə build fayllarını silmir. Əgər problem yaşayırsınızsa, `rebuild_exe.bat` istifadə edin.

