# create_setup.bat - Yalnız Installer

## 📋 Təsvir
**Yalnız installer yaradıcısı** - EXE faylı artıq hazırdırsa, yalnız setup installer yaradır.

## ✅ Nə edir?
- **Yalnız setup installer yaradır** - EXE yaratmır
- Inno Setup ilə professional installer hazırlayır
- EXE faylının artıq mövcud olduğunu fərz edir

## 🎯 Nə vaxt istifadə edilir?
- ✅ EXE faylı artıq hazırdırsa
- ✅ Yalnız installer lazımdırsa
- ✅ EXE-ni yenidən yaratmadan installer yaratmaq lazımdırsa
- ✅ Installer versiyasını yeniləmək lazımdırsa

## ⚠️ Tələb
- **EXE faylı artıq mövcud olmalıdır:** `../dist/MezuniyyetSistemi.exe`
- Inno Setup 6 quraşdırılmış olmalıdır

## 📁 Nəticə faylı
- **Installer:** `../dist/MezuniyyetSistemi_Setup_v7.1_NoAdmin.exe`

## 🚀 İstifadə
```cmd
cd "setup etmek\yalniz installer"
create_setup.bat
```

## ❌ Xəta halında
Əgər xəta alırsınızsa:
1. EXE faylının mövcud olduğunu yoxlayın: `../dist/MezuniyyetSistemi.exe`
2. Inno Setup quraşdırılıb yoxla: `C:\Program Files (x86)\Inno Setup 6\ISCC.exe`
3. `setup.iss` faylının düzgün olduğunu yoxlayın

## 💡 Qeyd
EXE yaratmaq üçün `ilk defe etmek ucun` və ya `adi build` qovluqlarındakı skriptləri istifadə edin.

