@echo off
chcp 1254 >nul
setlocal EnableExtensions EnableDelayedExpansion

REM LISDEP - Kantar Servisi hizli kurulum - gerekirse BASE_URL degerini guncelleyin.
set "BASE_URL=https://demo.lisdep.com"
set "KANTAR_KLASOR=C:\kantar"
set "GECICI=%TEMP%\lisdep-kantar-kurulum"
set "MESAUSTU=%PUBLIC%\Desktop"
set "HATA=0"
set "PYTHON_KOMUT="
set "PYTHON_DOSYA=%KANTAR_KLASOR%\kantar-cihazi-python3.py"
set "REQUIREMENTS_DOSYA=%KANTAR_KLASOR%\kantar-requirements.txt"
set "MODUL_KLASOR=%KANTAR_KLASOR%\kantar_servis"
set "TEMPLATE_KLASOR=%KANTAR_KLASOR%\templates"
set "TEMPLATE_DOSYA=%TEMPLATE_KLASOR%\kantar-ayarlar.html"
set "PARTIAL_KLASOR=%TEMPLATE_KLASOR%\partials"
set "KANTAR_AYAR_DB=%KANTAR_KLASOR%\kantar-ayarlar.sqlite"
set "PYTHON_INSTALLER=%GECICI%\python3-installer.exe"
set "PYTHON_INSTALLER_URL=https://www.python.org/ftp/python/3.12.3/python-3.12.3-amd64.exe"

call :yonetici_kontrol
if errorlevel 2 exit /b 0
if errorlevel 1 goto :son_hata

call :hazirlik
if errorlevel 1 goto :son_hata

call :baslik "LÝSDEP - Kantar Servisi Hýzlý Kurulum"
echo Program      : LÝSDEP - Kantar Servisi
echo Hedef klasor : %KANTAR_KLASOR%
echo Public adres : %BASE_URL%/programlar
echo Python surum : Python 3
echo Ayar DB      : %KANTAR_AYAR_DB%
echo Calisma      : Tek Python 3 dosyasi + tek port + profil parametresi
echo.

call :python3_kontrol
if errorlevel 1 (
    call :python3_kur
    if errorlevel 1 set "HATA=1"
    call :python3_kontrol
)

if defined PYTHON_KOMUT (
    call :requirements_dosyasi_indir
    if errorlevel 1 set "HATA=1"
    call :pip_kur
    if errorlevel 1 set "HATA=1"
) else (
    echo UYARI: Python 3 komutu bulunamadi. Python paket kurulumu atlandi.
    set "HATA=1"
)

call :kantar_dosyalarini_indir
if errorlevel 1 set "HATA=1"

call :masaustu_baslat_olustur
if errorlevel 1 set "HATA=1"

goto :son_ozet

:yonetici_kontrol
net session >nul 2>&1
if not errorlevel 1 exit /b 0
echo LÝSDEP - Kantar Servisi kurulumu C:\kantar ve Python kurulumu icin yonetici izni ister.
echo Windows izin ekraninda Evet secin.
powershell -NoProfile -ExecutionPolicy Bypass -Command "Start-Process -FilePath 'cmd.exe' -ArgumentList '/c ""%~f0""' -Verb RunAs"
if errorlevel 1 (
    echo Yonetici olarak yeniden baslatma basarisiz oldu.
    pause
    exit /b 1
)
exit /b 2

:hazirlik
where powershell >nul 2>&1
if errorlevel 1 (
    echo PowerShell bulunamadi. Windows 7 veya daha yeni bir surum kullanin.
    exit /b 1
)
if not exist "%KANTAR_KLASOR%" mkdir "%KANTAR_KLASOR%"
if errorlevel 1 (
    echo Kantar klasoru olusturulamadi: %KANTAR_KLASOR%
    exit /b 1
)
if not exist "%GECICI%" mkdir "%GECICI%"
if errorlevel 1 (
    echo Gecici klasor olusturulamadi: %GECICI%
    exit /b 1
)
if not exist "%MODUL_KLASOR%" mkdir "%MODUL_KLASOR%"
if errorlevel 1 (
    echo Python modul klasoru olusturulamadi: %MODUL_KLASOR%
    exit /b 1
)
if not exist "%TEMPLATE_KLASOR%" mkdir "%TEMPLATE_KLASOR%"
if errorlevel 1 (
    echo Template klasoru olusturulamadi: %TEMPLATE_KLASOR%
    exit /b 1
)
if not exist "%PARTIAL_KLASOR%" mkdir "%PARTIAL_KLASOR%"
if errorlevel 1 (
    echo Partial template klasoru olusturulamadi: %PARTIAL_KLASOR%
    exit /b 1
)
if not exist "%MESAUSTU%" set "MESAUSTU=%USERPROFILE%\Desktop"
exit /b 0

:baslik
echo.
echo ========================================
echo %~1
echo ========================================
exit /b 0

:dosya_indir
set "INDIR_URL=%~1"
set "INDIR_HEDEF=%~2"
echo Indiriliyor: %INDIR_URL%
powershell -NoProfile -ExecutionPolicy Bypass -Command "$ErrorActionPreference='Stop'; [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; Invoke-WebRequest -Uri $env:INDIR_URL -OutFile $env:INDIR_HEDEF -UseBasicParsing"
if errorlevel 1 (
    echo UYARI: Indirme basarisiz: %INDIR_URL%
    exit /b 1
)
if not exist "%INDIR_HEDEF%" (
    echo UYARI: Indirilen dosya bulunamadi: %INDIR_HEDEF%
    exit /b 1
)
exit /b 0

:python3_kontrol
py -3 -V >nul 2>&1
if not errorlevel 1 (
    set "PYTHON_KOMUT=py -3"
    exit /b 0
)
python -V 2>&1 | findstr /R "3\." >nul
if not errorlevel 1 (
    set "PYTHON_KOMUT=python"
    exit /b 0
)
set "PYTHON_KOMUT="
exit /b 1

:python3_kur
call :baslik "Python 3 kurulumu"
echo Python 3 bulunamadi. Resmi kurulum dosyasi indiriliyor...
call :dosya_indir "%PYTHON_INSTALLER_URL%" "%PYTHON_INSTALLER%"
if errorlevel 1 (
    echo Python 3 kurulum dosyasi indirilemedi.
    echo Elle kurulum adresi: https://www.python.org/downloads/windows/
    exit /b 1
)
echo Python 3 sessiz kurulum baslatiliyor...
"%PYTHON_INSTALLER%" /quiet InstallAllUsers=1 PrependPath=1 Include_pip=1 Include_launcher=1
if errorlevel 1 (
    echo Python 3 kurulum komutu hata verdi.
    exit /b 1
)
timeout /t 8 /nobreak >nul
exit /b 0

:requirements_dosyasi_indir
call :baslik "Python requirements indiriliyor"
call :dosya_indir "%BASE_URL%/programlar/kantar-requirements.txt" "%REQUIREMENTS_DOSYA%"
if errorlevel 1 (
    echo UYARI: Requirements dosyasi indirilemedi, paketler varsayilan isimlerle kurulacak.
    exit /b 1
)
exit /b 0

:pip_kur
call :baslik "Python paket kurulumu"
echo Kullanilan Python komutu: %PYTHON_KOMUT%
%PYTHON_KOMUT% -m pip --version >nul 2>&1
if errorlevel 1 (
    echo pip bulunamadi. ensurepip deneniyor...
    %PYTHON_KOMUT% -m ensurepip >nul 2>&1
)
%PYTHON_KOMUT% -m pip install --upgrade pip
if errorlevel 1 (
    echo pip guncellenemedi, paket kurulumu mevcut pip ile denenecek.
)
if exist "%REQUIREMENTS_DOSYA%" (
    %PYTHON_KOMUT% -m pip install -r "%REQUIREMENTS_DOSYA%"
) else (
    %PYTHON_KOMUT% -m pip install flask pyserial
)
if errorlevel 1 (
    echo Python paketleri kurulamadi. Requirements dosyasini veya internet baglantisini kontrol edin.
    exit /b 1
)
exit /b 0

:kantar_dosyalarini_indir
call :baslik "LÝSDEP - Kantar Servisi dosyalari indiriliyor"
set "INDIRME_HATASI=0"
call :dosya_indir "%BASE_URL%/programlar/kantar-cihazi-python3.py" "%PYTHON_DOSYA%"
if errorlevel 1 set "INDIRME_HATASI=1"
call :dosya_indir "%BASE_URL%/programlar/kantar_servis/__init__.py" "%MODUL_KLASOR%\__init__.py"
if errorlevel 1 set "INDIRME_HATASI=1"
call :dosya_indir "%BASE_URL%/programlar/kantar_servis/__main__.py" "%MODUL_KLASOR%\__main__.py"
if errorlevel 1 set "INDIRME_HATASI=1"
call :dosya_indir "%BASE_URL%/programlar/kantar_servis/config.py" "%MODUL_KLASOR%\config.py"
if errorlevel 1 set "INDIRME_HATASI=1"
call :dosya_indir "%BASE_URL%/programlar/kantar_servis/errors.py" "%MODUL_KLASOR%\errors.py"
if errorlevel 1 set "INDIRME_HATASI=1"
call :dosya_indir "%BASE_URL%/programlar/kantar_servis/logging_utils.py" "%MODUL_KLASOR%\logging_utils.py"
if errorlevel 1 set "INDIRME_HATASI=1"
call :dosya_indir "%BASE_URL%/programlar/kantar_servis/storage.py" "%MODUL_KLASOR%\storage.py"
if errorlevel 1 set "INDIRME_HATASI=1"
call :dosya_indir "%BASE_URL%/programlar/kantar_servis/serial_bridge.py" "%MODUL_KLASOR%\serial_bridge.py"
if errorlevel 1 set "INDIRME_HATASI=1"
call :dosya_indir "%BASE_URL%/programlar/kantar_servis/web.py" "%MODUL_KLASOR%\web.py"
if errorlevel 1 set "INDIRME_HATASI=1"
call :dosya_indir "%BASE_URL%/programlar/templates/base.html" "%TEMPLATE_KLASOR%\base.html"
if errorlevel 1 set "INDIRME_HATASI=1"
call :dosya_indir "%BASE_URL%/programlar/templates/kantar-ayarlar.html" "%TEMPLATE_DOSYA%"
if errorlevel 1 set "INDIRME_HATASI=1"
call :dosya_indir "%BASE_URL%/programlar/templates/serial.html" "%TEMPLATE_KLASOR%\serial.html"
if errorlevel 1 set "INDIRME_HATASI=1"
call :dosya_indir "%BASE_URL%/programlar/templates/loglar.html" "%TEMPLATE_KLASOR%\loglar.html"
if errorlevel 1 set "INDIRME_HATASI=1"
call :dosya_indir "%BASE_URL%/programlar/templates/partials/_header.html" "%PARTIAL_KLASOR%\_header.html"
if errorlevel 1 set "INDIRME_HATASI=1"
call :dosya_indir "%BASE_URL%/programlar/templates/partials/_nav.html" "%PARTIAL_KLASOR%\_nav.html"
if errorlevel 1 set "INDIRME_HATASI=1"
call :dosya_indir "%BASE_URL%/programlar/templates/partials/_alerts.html" "%PARTIAL_KLASOR%\_alerts.html"
if errorlevel 1 set "INDIRME_HATASI=1"
call :dosya_indir "%BASE_URL%/programlar/templates/partials/_profile_select.html" "%PARTIAL_KLASOR%\_profile_select.html"
if errorlevel 1 set "INDIRME_HATASI=1"
call :dosya_indir "%BASE_URL%/programlar/templates/partials/_settings_form.html" "%PARTIAL_KLASOR%\_settings_form.html"
if errorlevel 1 set "INDIRME_HATASI=1"
call :dosya_indir "%BASE_URL%/programlar/templates/partials/_usage_addresses.html" "%PARTIAL_KLASOR%\_usage_addresses.html"
if errorlevel 1 set "INDIRME_HATASI=1"
call :dosya_indir "%BASE_URL%/programlar/templates/partials/_com_ports.html" "%PARTIAL_KLASOR%\_com_ports.html"
if errorlevel 1 set "INDIRME_HATASI=1"
call :dosya_indir "%BASE_URL%/programlar/templates/partials/_sqlite_info.html" "%PARTIAL_KLASOR%\_sqlite_info.html"
if errorlevel 1 set "INDIRME_HATASI=1"
call :dosya_indir "%BASE_URL%/programlar/templates/partials/_troubleshooting.html" "%PARTIAL_KLASOR%\_troubleshooting.html"
if errorlevel 1 set "INDIRME_HATASI=1"
call :dosya_indir "%BASE_URL%/programlar/calistir.bat" "%KANTAR_KLASOR%\calistir.bat"
if errorlevel 1 set "INDIRME_HATASI=1"
exit /b %INDIRME_HATASI%

:masaustu_baslat_olustur
call :baslik "Masaustu baslaticisi"
(
    echo @echo off
    echo chcp 1254 ^>nul
    echo call "%KANTAR_KLASOR%\calistir.bat"
) > "%MESAUSTU%\LISDEP - Kantar Servisi Baslat.bat"
if errorlevel 1 exit /b 1
echo Olusturuldu: %MESAUSTU%\LISDEP - Kantar Servisi Baslat.bat
exit /b 0

:son_ozet
call :baslik "Kurulum ozeti"
echo Program       : LÝSDEP - Kantar Servisi
echo Baslatici     : Masaustundeki LISDEP - Kantar Servisi Baslat.bat
echo Ayar sayfasi  : http://127.0.0.1/ayarlar
echo Kantar klasoru: %KANTAR_KLASOR%
echo Ayar DB       : %KANTAR_AYAR_DB%
echo Tekli adres   : http://127.0.0.1
echo Kantar 1 adres: http://127.0.0.1/?profil=kantar1
echo Kantar 2 adres: http://127.0.0.1/?profil=kantar2
echo.
if "%HATA%"=="0" (
    echo Kurulum tamamlandi.
    echo Tek servis acilir; Kantar 1 ve Kantar 2 profil parametresiyle okunur.
) else (
    echo Kurulum bitti fakat bazi adimlarda uyari var.
    echo Eksik dosyalari https://demo.lisdep.com/programlar yolundan veya Kantar Kurulumu sayfasindan elle kontrol edin.
)
echo.
pause
if "%HATA%"=="0" exit /b 0
exit /b 1

:son_hata
echo.
echo Kurulum tamamlanamadi. Yukaridaki hata mesajini kontrol edin.
pause
exit /b 1
