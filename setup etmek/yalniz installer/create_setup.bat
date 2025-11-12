@echo off
chcp 65001 >nul
echo ========================================
echo Setup Installer Yaradıcısı
echo ========================================
echo.

echo 📦 Setup installer yaradılır...
echo.

REM yalniz installer qovluğundan yuxarı səviyyəyə çıx
cd ..

REM Inno Setup ilə installer yarat
"C:\Program Files (x86)\Inno Setup 6\ISCC.exe" "setup.iss"

if %errorlevel% equ 0 (
    echo.
    echo ✅ Setup installer uğurla yaradıldı!
    echo 📁 Setup faylı: dist\MezuniyyetSistemi_Setup_v7.1_NoAdmin.exe
    echo.
    echo 🎉 Proses tamamlandı!
) else (
    echo.
    echo ❌ Setup yaratma uğursuz oldu!
    echo.
    echo Xəta həlli üçün:
    echo 1. EXE faylı mövcuddur? (dist\MezuniyyetSistemi.exe)
    echo 2. Inno Setup quraşdırılıb?
    echo 3. setup.iss faylı düzgündür?
)

echo.
pause

