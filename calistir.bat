@echo off
chcp 1254 >nul
setlocal EnableExtensions

set "KANTAR_KLASOR=C:\kantar"
set "KANTAR_AYAR_PROFILI=tekli"
set "KANTAR_AYAR_DB=%KANTAR_KLASOR%\kantar-ayarlar.sqlite"
set "PYTHON_DOSYA=%KANTAR_KLASOR%\kantar-cihazi-python3.py"
set "CALISMA_BASARILI=0"

call :yonetici_kontrol
if errorlevel 2 exit /b 0
if errorlevel 1 goto :hata

cd /d "%KANTAR_KLASOR%" 2>nul
if errorlevel 1 (
    echo Kantar klasoru bulunamadi: %KANTAR_KLASOR%
    echo Hizli kurulumu tekrar calistirin veya dosyalari C:\kantar klasorune kopyalayin.
    goto :hata
)

echo.
echo LÝSDEP - Kantar Servisi baslatiliyor...
echo Varsayilan profil : %KANTAR_AYAR_PROFILI%
echo Ayar DB           : %KANTAR_AYAR_DB%
echo Tekli adres       : http://127.0.0.1
echo Kantar 1 adres    : http://127.0.0.1/?profil=kantar1
echo Kantar 2 adres    : http://127.0.0.1/?profil=kantar2
echo Ayar sayfasi      : http://127.0.0.1/ayarlar
echo.

if not exist "%PYTHON_DOSYA%" (
    echo Python 3 kantar dosyasi bulunamadi: %PYTHON_DOSYA%
    goto :hata
)

py -3 "%PYTHON_DOSYA%"
if not errorlevel 1 set "CALISMA_BASARILI=1"

if "%CALISMA_BASARILI%"=="0" (
    python -V 2>&1 | findstr /R "3\." >nul
    if not errorlevel 1 (
        python "%PYTHON_DOSYA%"
        if not errorlevel 1 set "CALISMA_BASARILI=1"
    )
)

if "%CALISMA_BASARILI%"=="1" goto :son

echo LÝSDEP - Kantar Servisi Python 3 ile baslatilamadi.
echo Python 3 kurulumunu ve pyserial/flask paketlerini kontrol edin.
goto :hata

:yonetici_kontrol
net session >nul 2>&1
if not errorlevel 1 exit /b 0
echo LÝSDEP - Kantar Servisi port acmak icin yonetici izni isteyebilir.
echo Windows izin ekraninda Evet secin.
powershell -NoProfile -ExecutionPolicy Bypass -Command "Start-Process -FilePath 'cmd.exe' -ArgumentList '/c ""%~f0""' -Verb RunAs"
if errorlevel 1 exit /b 1
exit /b 2

:son
endlocal
exit /b 0

:hata
pause
endlocal
exit /b 1
