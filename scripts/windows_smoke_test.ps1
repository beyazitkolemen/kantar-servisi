param(
    [Parameter(Mandatory = $true)]
    [string]$Executable,
    [int]$Port = 18080,
    [string]$DataDirectory = ""
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

$Executable = (Resolve-Path $Executable).Path
if (-not $DataDirectory) {
    $tempRoot = $env:RUNNER_TEMP
    if (-not $tempRoot) {
        $tempRoot = $env:TEMP
    }
    $DataDirectory = Join-Path $tempRoot ("kantar-servisi-smoke-" + [Guid]::NewGuid().ToString("N"))
}
New-Item -ItemType Directory -Force -Path $DataDirectory | Out-Null

$oncekiVeriDizini = $env:KANTAR_VERI_DIZINI
$oncekiPort = $env:KANTAR_SERVIS_PORT
$env:KANTAR_VERI_DIZINI = $DataDirectory
$env:KANTAR_SERVIS_PORT = [string]$Port
$baseUrl = "http://127.0.0.1:$Port"
$process = $null

try {
    $process = Start-Process -FilePath $Executable -ArgumentList "--server" -PassThru -WindowStyle Hidden
    $hazir = $false
    for ($deneme = 0; $deneme -lt 120; $deneme++) {
        Start-Sleep -Milliseconds 250
        if ($process.HasExited) {
            throw "Paketlenmis servis erken sonlandi. Cikis kodu: $($process.ExitCode)"
        }
        try {
            $saglik = Invoke-RestMethod "$baseUrl/saglik" -TimeoutSec 2
            if (
                $saglik.ok -eq $true -and
                $saglik.uygulama -eq "Kantar Servisi" -and
                $saglik.durum -eq "hazir"
            ) {
                $hazir = $true
                break
            }
        } catch {
        }
    }
    Assert-True $hazir "Paketlenmis Kantar Servisi saglik kontrolunu gecemedi."

    $saglikCevabi = Invoke-WebRequest "$baseUrl/saglik" -TimeoutSec 5
    Assert-True ($saglikCevabi.StatusCode -eq 200) "Saglik endpointi HTTP 200 donmedi."
    Assert-True ($saglikCevabi.Headers["X-Frame-Options"] -eq "DENY") "X-Frame-Options basligi eksik."
    Assert-True ($saglikCevabi.Headers["X-Content-Type-Options"] -eq "nosniff") "X-Content-Type-Options basligi eksik."
    Assert-True ($saglikCevabi.Headers["Content-Security-Policy"] -match "script-src 'self'") "CSP basligi gecersiz."

    $panel = Invoke-WebRequest "$baseUrl/ayarlar" -TimeoutSec 5
    Assert-True ($panel.StatusCode -eq 200) "Ayarlar paneli acilamadi."
    Assert-True ($panel.Content -match "Kantar Servisi") "Ayarlar paneli beklenen icerigi icermiyor."
    Assert-True ($panel.Content -match "_csrf_token") "Ayarlar panelinde CSRF token bulunamadi."

    $serialScript = Invoke-WebRequest "$baseUrl/static/serial.js" -TimeoutSec 5
    Assert-True ($serialScript.StatusCode -eq 200) "Serial JavaScript dosyasi sunulamadi."
    Assert-True ($serialScript.Content.Length -gt 1000) "Serial JavaScript dosyasi eksik gorunuyor."

    $corsBasliklari = @{
        "Origin" = "https://demo.lisdep.com"
        "Sec-Fetch-Site" = "cross-site"
        "Access-Control-Request-Private-Network" = "true"
    }
    $cors = Invoke-WebRequest "$baseUrl/api/v1/agirlik" -Method Options -Headers $corsBasliklari -SkipHttpErrorCheck -TimeoutSec 5
    Assert-True ($cors.StatusCode -eq 204) "CORS on kontrolu HTTP 204 donmedi."
    Assert-True ($cors.Headers["Access-Control-Allow-Origin"] -eq "https://demo.lisdep.com") "LISDEP CORS izni eksik."
    Assert-True ($cors.Headers["Access-Control-Allow-Private-Network"] -eq "true") "Private Network Access izni eksik."

    $yasakli = Invoke-WebRequest "$baseUrl/loglar/veri" -Headers $corsBasliklari -SkipHttpErrorCheck -TimeoutSec 5
    Assert-True ($yasakli.StatusCode -eq 403) "LISDEP origin yonetim endpointine erisebildi."

    $sahteOrigin = @{
        "Origin" = "https://example.test"
        "Sec-Fetch-Site" = "cross-site"
    }
    $reddedilen = Invoke-WebRequest "$baseUrl/saglik" -Headers $sahteOrigin -SkipHttpErrorCheck -TimeoutSec 5
    Assert-True ($reddedilen.StatusCode -eq 403) "Izinsiz web origini reddedilmedi."

    $saglikSureci = Start-Process -FilePath $Executable -ArgumentList "--health-check" -PassThru -Wait -WindowStyle Hidden
    Assert-True ($saglikSureci.ExitCode -eq 0) "--health-check basarili cikis kodu donmedi."

    Write-Host "Windows paket smoke testi basarili: $Executable"
} finally {
    if ($process -and -not $process.HasExited) {
        Stop-Process -Id $process.Id -Force -ErrorAction SilentlyContinue
        $process.WaitForExit(5000) | Out-Null
    }
    $env:KANTAR_VERI_DIZINI = $oncekiVeriDizini
    $env:KANTAR_SERVIS_PORT = $oncekiPort
}
