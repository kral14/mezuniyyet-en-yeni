# rebuild_exe.bat

## 📋 Təsvir
**Təmiz yenidən build skripti** - Köhnə build fayllarını silib sıfırdan yaradır.

## ✅ Nə edir?
1. **Köhnə faylları silir** - `dist/` və `build/` qovluqlarını tamamilə silir
2. **EXE faylı yaradır** - Sıfırdan təmiz build edir
3. **Setup installer yaradır** - Inno Setup ilə installer hazırlayır (əgər quraşdırılıbsa)

## 🎯 Nə vaxt istifadə edilir?
- ✅ Köhnə build faylları problem yaradırsa
- ✅ Tam təmiz build lazımdırsa
- ✅ Kod dəyişikliklərindən sonra
- ✅ Build xətaları baş verərsə
- ✅ Cache problemləri varsa

## 📁 Nəticə faylları
- **EXE:** `dist/MezuniyyetSistemi.exe`
- **Installer:** `dist/MezuniyyetSistemi_Setup_v7.1_NoAdmin.exe`

## 🚀 İstifadə
```cmd
cd setup etmek\scripts
rebuild_exe.bat
```

## ⚠️ Diqqət
Bu skript köhnə build fayllarını **tamamilə silir**. Əgər köhnə build lazımdırsa, əvvəlcə backup edin.

## 💡 Qeyd
Normal build üçün `run_build.bat` istifadə edin. Bu skript yalnız problem olduqda lazımdır.

