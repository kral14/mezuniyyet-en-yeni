@echo off
chcp 65001 >nul
echo ========================================
echo Məzuniyyət Sistemi EXE Yaradıcısı
echo ========================================
echo.

REM Cari qovluğu göstər
echo 📁 Cari qovluq: %CD%
echo.

REM Python yoxla
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Python tapılmadı! Python quraşdırın.
    pause
    exit /b 1
)

REM PyInstaller yoxla
python -c "import PyInstaller" >nul 2>&1
if %errorlevel% neq 0 (
    echo ⚙️ PyInstaller quraşdırılır...
    pip install pyinstaller
)

REM EXE yaradılır
echo.
echo 🔨 EXE faylı yaradılır...
echo.

REM adi build qovluğundan yuxarı səviyyəyə çıx
cd ..

python build_exe.py

if %errorlevel% neq 0 (
    echo ❌ EXE yaratma uğursuz oldu!
    pause
    exit /b 1
)

echo.
echo ✅ EXE faylı uğurla yaradıldı!
echo.
echo 📁 EXE faylı: setup files\dist\MezuniyyetSistemi.exe
echo.

REM İndi Inno Setup ilə installer yaradılacaq
echo.
echo 📦 Setup installer yaradılır...
echo.

REM Inno Setup quraşdırılıb yoxla
if exist "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" (
    echo ✅ Inno Setup tapıldı
    "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" "setup.iss"
    
    if %errorlevel% equ 0 (
        echo.
        echo ✅ Setup installer uğurla yaradıldı!
        echo 📁 Setup faylı: dist\
        echo.
    ) else (
        echo ❌ Setup yaratma uğursuz oldu!
    )
) else (
    echo ⚠️ Inno Setup tapılmadı!
    echo.
    echo Inno Setup quraşdırmaq üçün:
    echo 1. https://jrsoftware.org/isdl.php saytından Inno Setup yükləyin
    echo 2. Quraşdırın
    echo 3. Bu skripti yenidən işə salın
    echo.
    echo Hələlik sadə setup.bat faylı istifadə edə bilərsiniz.
)

echo.
echo 🎉 Proses tamamlandı!
echo.
pause

