import hashlib
import json
from pathlib import Path

from PIL import Image

from kantar_servis import desktop
from scripts import build_windows_local, generate_build_assets


ROOT = Path(__file__).resolve().parent.parent


def test_installer_windows_uygulama_sozlesmesini_korur():
    icerik = (ROOT / "packaging" / "windows" / "installer.nsi").read_text(encoding="utf-8")

    assert desktop.MUTEX_ADI == "Local\\KantarServisi"
    assert "RequestExecutionLevel user" in icerik
    assert "MUI2.nsh" in icerik
    assert '"--open-panel"' in icerik
    assert '"--open-logs"' in icerik
    assert '"--diagnostics"' in icerik
    assert "Software\\Microsoft\\Windows\\CurrentVersion\\App Paths" in icerik
    assert "WriteUninstaller" in icerik
    assert "DeleteRegKey" in icerik


def test_gomme_windows_baslaticisi_penceresiz_ve_guvenli():
    icerik = (ROOT / "packaging" / "windows" / "launcher.c").read_text(encoding="utf-8")
    dockerfile = (ROOT / "packaging" / "windows" / "Dockerfile.local").read_text(encoding="utf-8")

    assert "wWinMain" in icerik
    assert "LoadLibraryW(python_dll_path)" in icerik
    assert '"kantar_servis.windows_bootstrap"' in icerik
    assert "gcc-mingw-w64-x86-64" in dockerfile
    assert "nsis" in dockerfile

    manifest = (ROOT / "packaging" / "windows" / "app.manifest").read_text(encoding="utf-8")
    assert 'requestedExecutionLevel level="asInvoker"' in manifest
    assert "PerMonitorV2" in manifest
    assert "longPathAware" in manifest


def test_windows_build_gorselleri_beklenen_formatta_uretilir(monkeypatch, tmp_path):
    monkeypatch.setattr(generate_build_assets, "BUILD_DIR", tmp_path)

    generate_build_assets.generate_icon()
    generate_build_assets.generate_installer_images()
    generate_build_assets.generate_version_info()

    with Image.open(tmp_path / "app.ico") as ikon:
        assert ikon.format == "ICO"
    with Image.open(tmp_path / "wizard-large.bmp") as buyuk:
        assert buyuk.size == (164, 314)
        assert buyuk.format == "BMP"
    with Image.open(tmp_path / "wizard-small.bmp") as kucuk:
        assert kucuk.size == (55, 55)
        assert kucuk.format == "BMP"
    surum_bilgisi = (tmp_path / "version_info.txt").read_text(encoding="utf-8")
    assert "KantarServisi.exe" in surum_bilgisi
    assert "ProductVersion" in surum_bilgisi


def test_windows_manifest_surumu_build_surumunden_uretilir(monkeypatch, tmp_path):
    monkeypatch.setattr(build_windows_local, "BUILD_DIR", tmp_path)

    manifest = build_windows_local.write_app_manifest("1.2.3")

    assert 'version="1.2.3.0"' in manifest.read_text(encoding="utf-8")


def test_github_actions_kullanilmaz_ve_build_yerelde_yapilir():
    workflow_klasoru = ROOT / ".github" / "workflows"
    build_script = (ROOT / "scripts" / "build_windows_local.py").read_text(encoding="utf-8")

    assert not workflow_klasoru.exists() or list(workflow_klasoru.iterdir()) == []
    assert "docker" in build_script
    assert "makensis" in build_script
    assert "win_amd64" in build_script
    assert "PYTHON_EMBED_SHA256" in build_script
    assert "Kantar-Servisi-Setup.exe" in build_script
    lock = (ROOT / "packaging" / "windows" / "requirements.lock").read_text(encoding="utf-8")
    assert "Flask==" in lock
    assert "Pillow==" in lock


def test_repoda_hazir_windows_kurulumu_ve_dogrulanabilir_manifest_var():
    installer = ROOT / "downloads" / "Kantar-Servisi-Setup.exe"
    manifest_path = ROOT / "downloads" / "latest.json"

    assert installer.is_file()
    assert installer.read_bytes()[:2] == b"MZ"
    assert installer.stat().st_size < 100 * 1024 * 1024
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["installer"] == installer.name
    assert manifest["sha256"] == hashlib.sha256(installer.read_bytes()).hexdigest()


def test_depo_bat_ve_cmd_dosyasi_icermez():
    adaylar = [
        yol
        for yol in ROOT.rglob("*")
        if yol.is_file()
        and yol.suffix.lower() in (".bat", ".cmd")
        and ".venv" not in yol.parts
        and "node_modules" not in yol.parts
    ]

    assert adaylar == []
