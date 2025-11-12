@echo off
chcp 65001 >nul
echo 🔧 Məzuniyyət Sistemi İcazə Problemləri Həll Edilir...
echo.

REM Cari qovluğu al
set CURRENT_DIR=%~dp0

REM EXE faylının yolunu təyin et
set EXE_PATH=%CURRENT_DIR%setup etmek\dist\MezuniyyetSistemi.exe

echo 📍 Cari qovluq: %CURRENT_DIR%
echo 📁 EXE faylı: %EXE_PATH%
echo.

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

echo ✅ EXE faylı tapıldı!

REM Fayl icazələrini təmir et
echo 🔧 Fayl icazələri təmir edilir...
attrib -R "%EXE_PATH%" >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ Fayl icazələri təmir edildi
) else (
    echo ⚠️ Fayl icazələri təmir edilə bilmədi
)

REM Windows Defender istisnası əlavə et
echo 🛡️ Windows Defender istisnası əlavə edilir...
powershell -Command "Add-MpPreference -ExclusionPath '%CURRENT_DIR%'" >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ Windows Defender istisnası əlavə edildi
) else (
    echo ⚠️ Windows Defender istisnası əlavə edilə bilmədi (admin icazəsi lazımdır)
)

REM Launcher faylını yarat
echo 🚀 Launcher faylı yaradılır...
set LAUNCHER_PATH=%CURRENT_DIR%setup etmek\dist\launcher.bat

if not exist "%LAUNCHER_PATH%" (
    echo @echo off > "%LAUNCHER_PATH%"
    echo chcp 65001 ^>nul >> "%LAUNCHER_PATH%"
    echo echo Məzuniyyət Sistemi v7.1 Başladılır... >> "%LAUNCHER_PATH%"
    echo echo. >> "%LAUNCHER_PATH%"
    echo. >> "%LAUNCHER_PATH%"
    echo REM Cari qovluğu al >> "%LAUNCHER_PATH%"
    echo set CURRENT_DIR=%%~dp0 >> "%LAUNCHER_PATH%"
    echo. >> "%LAUNCHER_PATH%"
    echo REM EXE faylının yolunu təyin et >> "%LAUNCHER_PATH%"
    echo set EXE_PATH=%%CURRENT_DIR%%MezuniyyetSistemi.exe >> "%LAUNCHER_PATH%"
    echo. >> "%LAUNCHER_PATH%"
    echo REM EXE faylını işə sal >> "%LAUNCHER_PATH%"
    echo "%%EXE_PATH%%" >> "%LAUNCHER_PATH%"
    echo. >> "%LAUNCHER_PATH%"
    echo if %%errorlevel%% neq 0 ( >> "%LAUNCHER_PATH%"
    echo     echo. >> "%LAUNCHER_PATH%"
    echo     echo ❌ Proqram səhv ilə başa çatdı ^(Kod: %%errorlevel%%^) >> "%LAUNCHER_PATH%"
    echo     echo. >> "%LAUNCHER_PATH%"
    echo     echo 🔧 Həll yolları: >> "%LAUNCHER_PATH%"
    echo     echo   1. Windows Defender istisnalarına qovluğu əlavə edin >> "%LAUNCHER_PATH%"
    echo     echo   2. Antivirus proqramını yoxlayın >> "%LAUNCHER_PATH%"
    echo     echo   3. Fayl icazələrini yoxlayın >> "%LAUNCHER_PATH%"
    echo     echo   4. Administrator kimi işə salın >> "%LAUNCHER_PATH%"
    echo     echo. >> "%LAUNCHER_PATH%"
    echo     pause >> "%LAUNCHER_PATH%"
    echo ^) >> "%LAUNCHER_PATH%"
    
    echo ✅ Launcher faylı yaradıldı: %LAUNCHER_PATH%
) else (
    echo ✅ Launcher faylı artıq mövcuddur
)

REM Desktop shortcut yarat
echo 🖥️ Desktop shortcut yaradılır...
set DESKTOP=%USERPROFILE%\Desktop
set SHORTCUT_PATH=%DESKTOP%\Məzuniyyət Sistemi.bat

echo @echo off > "%SHORTCUT_PATH%"
echo chcp 65001 ^>nul >> "%SHORTCUT_PATH%"
echo cd /d "%CURRENT_DIR%setup etmek\dist" >> "%SHORTCUT_PATH%"
echo launcher.bat >> "%SHORTCUT_PATH%"

echo ✅ Desktop shortcut yaradıldı: %SHORTCUT_PATH%

echo.
echo 🎉 Həll tamamlandı!
echo.
echo 📋 İstifadə:
echo   1. Desktop-dan "Məzuniyyət Sistemi" shortcut-una basın
echo   2. Və ya %LAUNCHER_PATH% faylını işə salın
echo   3. Və ya %EXE_PATH% faylını birbaşa işə salın
echo.
echo 💡 Əgər problem davam edərsə:
echo   - Windows Defender istisnalarına qovluğu əlavə edin
echo   - Antivirus proqramını yoxlayın
echo   - Administrator kimi işə salın
echo.
pause


