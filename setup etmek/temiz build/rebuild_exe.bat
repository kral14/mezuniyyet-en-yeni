@echo off
chcp 65001 >nul
echo ========================================
echo Məzuniyyət Sistemi EXE Yenidən Yaradıcısı
echo ========================================
echo.

REM temiz build qovluğundan yuxarı səviyyəyə çıx
cd ..

echo 🔄 Köhnə fayllar silinir...
if exist "dist" rmdir /s /q "dist"
if exist "build" rmdir /s /q "build"
echo ✅ Köhnə fayllar silindi
echo.

echo 🔨 EXE faylı yaradılır...
python build_exe.py

if %errorlevel% neq 0 (
    echo ❌ EXE yaratma uğursuz oldu!
    pause
    exit /b 1
)

echo.
echo ✅ EXE faylı uğurla yaradıldı!
echo 📁 EXE faylı: dist\MezuniyyetSistemi.exe
echo.

echo 📦 Setup installer yaradılır...
"C:\Program Files (x86)\Inno Setup 6\ISCC.exe" "setup.iss"

if %errorlevel% equ 0 (
    echo.
    echo ✅ Setup installer uğurla yaradıldı!
    echo 📁 Setup faylı: dist\MezuniyyetSistemi_Setup_v7.1_NoAdmin.exe
    echo.
) else (
    echo.
    echo ⚠️ Setup yaratma uğursuz oldu!
    echo Amma EXE faylı hazırdır: dist\MezuniyyetSistemi.exe
    echo.
)

echo 🎉 Proses tamamlandı!
echo.
pause
