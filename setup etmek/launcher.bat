@echo off
chcp 65001 >nul
echo Məzuniyyət Sistemi v7.1 Başladılır...
echo.

REM Cari qovluğu al
set CURRENT_DIR=%~dp0

REM EXE faylının yolunu təyin et
set EXE_PATH=%CURRENT_DIR%dist\MezuniyyetSistemi.exe

REM EXE faylının mövcudluğunu yoxla
if not exist "%EXE_PATH%" (
    echo ❌ Xəta: MezuniyyetSistemi.exe faylı tapılmadı!
    echo 📁 Axtarılan yer: %EXE_PATH%
    echo.
    echo 🔧 Həll yolları:
    echo   1. build_exe.py faylını işə salın
    echo   2. EXE faylının düzgün yaradıldığını yoxlayın
    echo.
    pause
    exit /b 1
)

REM Fayl icazələrini yoxla və təmir et
echo 🔍 Fayl icazələri yoxlanılır...
attrib -R "%EXE_PATH%" >nul 2>&1
if %errorlevel% neq 0 (
    echo ⚠️ Fayl icazələri təmir edilə bilmədi, lakin davam edilir...
)

REM Windows Defender və antivirus yoxlaması
echo 🛡️ Windows Defender yoxlaması...
powershell -Command "Get-MpPreference | Select-Object -ExpandProperty ExclusionPath" | findstr /i "%CURRENT_DIR%" >nul
if %errorlevel% neq 0 (
    echo ℹ️ Qovluq Windows Defender istisnalarında deyil
    echo 💡 Əgər problem davam edərsə, qovluğu Windows Defender istisnalarına əlavə edin
)

REM EXE faylını işə sal
echo 🚀 Proqram başladılır...
echo 📁 İşlədilən fayl: %EXE_PATH%
echo.

REM EXE faylını işə sal
"%EXE_PATH%"

REM Əgər proqram səhv ilə başa çatdısa
if %errorlevel% neq 0 (
    echo.
    echo ❌ Proqram səhv ilə başa çatdı (Kod: %errorlevel%)
    echo.
    echo 🔧 Həll yolları:
    echo   1. Windows Defender istisnalarına qovluğu əlavə edin
    echo   2. Antivirus proqramını yoxlayın
    echo   3. Fayl icazələrini yoxlayın
    echo   4. Administrator kimi işə salın
    echo.
    echo 📋 Ətraflı məlumat üçün debug_logs qovluğuna baxın
    echo.
    pause
)


