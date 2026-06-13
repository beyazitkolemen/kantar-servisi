param(
    [Parameter(Mandatory = $true)]
    [string]$Installer,
    [int]$Port = 18081
)

$ErrorActionPreference = "Stop"

function Assert-True {
    param(
        [bool]$Condition,
        [string]$Message
    )
    if (-not $Condition) {
        throw $Message
    }
}

$Installer = (Resolve-Path $Installer).Path
$tempRoot = $env:RUNNER_TEMP
if (-not $tempRoot) {
    $tempRoot = $env:TEMP
}
$installDirectory = Join-Path $tempRoot ("KantarServisiInstall-" + [Guid]::NewGuid().ToString("N"))
$installLog = Join-Path $tempRoot "kantar-servisi-install.log"
$setupArgs = @(
    "/VERYSILENT",
    "/SUPPRESSMSGBOXES",
    "/NORESTART",
    "/SP-",
    "/DIR=`"$installDirectory`"",
    "/MERGETASKS=`"!startup,!desktopicon`"",
    "/LOG=`"$installLog`""
)

$kurulum = Start-Process -FilePath $Installer -ArgumentList $setupArgs -PassThru -Wait
Assert-True ($kurulum.ExitCode -eq 0) "Windows kurulumu basarisiz. Cikis kodu: $($kurulum.ExitCode)"

$executable = Join-Path $installDirectory "KantarServisi.exe"
$uninstaller = Join-Path $installDirectory "unins000.exe"
Assert-True (Test-Path $executable) "Kurulu KantarServisi.exe bulunamadi."
Assert-True (Test-Path $uninstaller) "Windows kaldirma programi bulunamadi."

$appPath = "HKCU:\Software\Microsoft\Windows\CurrentVersion\App Paths\KantarServisi.exe"
Assert-True (Test-Path $appPath) "Windows App Paths kaydi olusturulmadi."
$kayitliExe = (Get-Item $appPath).GetValue("")
Assert-True ($kayitliExe -eq $executable) "Windows App Paths kaydi kurulu EXE ile eslesmiyor."

& "$PSScriptRoot\windows_smoke_test.ps1" -Executable $executable -Port $Port

$kaldirma = Start-Process -FilePath $uninstaller -ArgumentList @(
    "/VERYSILENT",
    "/SUPPRESSMSGBOXES",
    "/NORESTART"
) -PassThru -Wait
Assert-True ($kaldirma.ExitCode -eq 0) "Windows kaldirma islemi basarisiz. Cikis kodu: $($kaldirma.ExitCode)"
Assert-True (-not (Test-Path $executable)) "Kaldirma sonrasinda uygulama EXE dosyasi kaldi."
Assert-True (-not (Test-Path $appPath)) "Kaldirma sonrasinda App Paths kaydi kaldi."

Write-Host "Windows installer smoke testi basarili: $Installer"
