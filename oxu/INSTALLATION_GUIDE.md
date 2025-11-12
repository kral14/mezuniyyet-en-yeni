# Məzuniyyət Sistemi v6.7 - Quraşdırma Təlimatı

## 📋 Tələblər

- Windows 10/11 (64-bit)
- Administrator səlahiyyətləri
- Minimum 50 MB boş yer

## 🚀 Quraşdırma

### 1. EXE Faylını Yaratmaq

Əgər mənbə kodundan EXE faylı yaratmaq istəyirsinizsə:

```bash
# PyInstaller quraşdırın
pip install pyinstaller

# EXE faylını yaradın
python build_exe.py
```

### 2. Quraşdırma

#### Seçim 1: Professional Quraşdırıcı (Tövsiyə olunur)

1. `setup_installer.bat` faylını **Administrator kimi işə salın**
2. Quraşdırıcı avtomatik olaraq:
   - Proqramı `C:\Program Files\MezuniyyetSistemi\` qovluğuna quraşdırar
   - Desktop-da shortcut yaradar
   - Start Menu-də shortcut yaradar
   - Registry-də uninstall məlumatı əlavə edər

#### Seçim 2: Sadə Quraşdırma

1. `setup.bat` faylını **Administrator kimi işə salın**
2. Proqram avtomatik quraşdırılacaq

#### Seçim 3: Manual Quraşdırma

1. `dist\MezuniyyetSistemi.exe` faylını istədiyiniz qovluğa kopyalayın
2. EXE faylını işə salın

## 🎯 Xüsusiyyətlər

### ✅ Professional Quraşdırıcı
- **Təmiz quraşdırma**: Əlavə fayllar açılmır
- **Professional shortcut-lar**: PowerShell ilə yaradılan .lnk faylları
- **Registry inteqrasiyası**: Windows Control Panel-də görünür
- **Uninstall dəstəyi**: Tam silmə funksiyası
- **Administrator yoxlaması**: Təhlükəsizlik
- **Xəta idarəetməsi**: Detallı xəta mesajları

### 🔧 Sistem Tələbləri
- **Windows**: 10/11 (64-bit)
- **RAM**: Minimum 2 GB
- **Disk**: 50 MB boş yer
- **Səlahiyyət**: Administrator

## 📁 Quraşdırma Strukturu

```
C:\Program Files\MezuniyyetSistemi\
├── MezuniyyetSistemi.exe    # Əsas proqram
└── uninstall.exe            # Silmə skripti

Desktop\
└── Məzuniyyət Sistemi.lnk  # Desktop shortcut

Start Menu\
└── Mezuniyyət Sistemi\
    └── Məzuniyyət Sistemi.lnk  # Start Menu shortcut
```

## 🗑️ Proqramı Silmək

### Seçim 1: Uninstall Skripti
1. `C:\Program Files\MezuniyyetSistemi\uninstall.exe` faylını işə salın
2. "Y" yazaraq təsdiqləyin

### Seçim 2: Control Panel
1. Control Panel → Programs and Features
2. "Məzuniyyət Sistemi v6.7" tapın
3. "Uninstall" düyməsinə basın

### Seçim 3: Manual Silmə
1. `C:\Program Files\MezuniyyetSistemi\` qovluğunu silin
2. Desktop və Start Menu shortcut-larını silin
3. Registry-dən məlumatları silin

## 🔍 Problemlərin Həlli

### Xəta: "Administrator səlahiyyətləri tələb edir"
**Həll**: Quraşdırıcı faylını "Administrator kimi işə sal" seçimi ilə açın

### Xəta: "EXE faylı tapılmadı"
**Həll**: `dist\MezuniyyetSistemi.exe` faylının mövcudluğunu yoxlayın

### Xəta: "Quraşdırma qovluğu yaradıla bilmədi"
**Həll**: Administrator səlahiyyətlərinizi yoxlayın

### Proqram açılmır
**Həll**: 
1. Antivirus proqramını müvəqqəti deaktiv edin
2. Windows Defender-də istisna əlavə edin
3. Proqramı yenidən quraşdırın

## 📞 Dəstək

Əgər problem yaşayırsınızsa:
1. Log fayllarını yoxlayın
2. Sistem tələblərini yoxlayın
3. Proqramı yenidən quraşdırın

## 📝 Versiya Məlumatları

- **Versiya**: 6.7
- **Tarix**: 2024
- **Platform**: Windows 10/11 (64-bit)
- **Dil**: Azərbaycan dili
- **Lisenziya**: Özəl

---

**Qeyd**: Bu proqram professional məzuniyyət idarəetmə sistemi olub, şirkətlər üçün hazırlanıb. 