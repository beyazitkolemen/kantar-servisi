#!/usr/bin/env python3
import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import urllib.request
import zipfile
from datetime import date
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
BUILD_DIR = ROOT / ".windows-build"
RUNTIME_DIR = BUILD_DIR / "runtime"
DOWNLOADS_DIR = ROOT / "downloads"
ASSETS_DIR = ROOT / ".build-assets"
PYTHON_VERSION = "3.12.10"
PYTHON_TAG = "312"
PYTHON_EMBED_URL = (
    "https://www.python.org/ftp/python/%s/python-%s-embed-amd64.zip"
    % (PYTHON_VERSION, PYTHON_VERSION)
)
PYTHON_EMBED_SHA256 = "4acbed6dd1c744b0376e3b1cf57ce906f9dc9e95e68824584c8099a63025a3c3"
DOCKER_IMAGE = "kantar-servisi-windows-builder:local"
MAX_GITHUB_FILE_SIZE = 100 * 1024 * 1024


def run(command, **kwargs):
    print("+", " ".join(str(part) for part in command), flush=True)
    subprocess.run(command, check=True, **kwargs)


def read_version():
    namespace = {}
    exec((ROOT / "kantar_servis" / "__init__.py").read_text(encoding="utf-8"), namespace)
    return namespace["__version__"]


def version4(version):
    parts = [int(part) for part in version.split(".")]
    while len(parts) < 4:
        parts.append(0)
    return ".".join(str(part) for part in parts[:4])


def download(url, destination, expected_sha256):
    if not destination.exists():
        destination.parent.mkdir(parents=True, exist_ok=True)
        print("Indiriliyor:", url, flush=True)
        with urllib.request.urlopen(url, timeout=120) as response:
            with destination.open("wb") as output:
                shutil.copyfileobj(response, output)
    digest = hashlib.sha256(destination.read_bytes()).hexdigest()
    if digest != expected_sha256:
        destination.unlink(missing_ok=True)
        raise RuntimeError("Indirilen Windows calisma zamani SHA256 dogrulamasindan gecemedi.")


def copy_application():
    target = RUNTIME_DIR / "kantar_servis"
    shutil.copytree(
        ROOT / "kantar_servis",
        target,
        ignore=shutil.ignore_patterns("__pycache__", "*.pyc", "*.pyo"),
    )


def install_windows_dependencies():
    site_packages = RUNTIME_DIR / "Lib" / "site-packages"
    site_packages.mkdir(parents=True, exist_ok=True)
    run(
        [
            sys.executable,
            "-m",
            "pip",
            "install",
            "--disable-pip-version-check",
            "--no-compile",
            "--only-binary=:all:",
            "--platform=win_amd64",
            "--implementation=cp",
            "--python-version=3.12",
            "--abi=cp312",
            "--no-deps",
            "--target",
            str(site_packages),
            "-r",
            str(ROOT / "packaging" / "windows" / "requirements.lock"),
        ]
    )
    shutil.rmtree(site_packages / "bin", ignore_errors=True)


def write_python_path():
    path_file = RUNTIME_DIR / ("python%s._pth" % PYTHON_TAG)
    path_file.write_text(
        "python%s.zip\n.\nLib\\site-packages\nimport site\n" % PYTHON_TAG,
        encoding="ascii",
    )


def write_app_manifest(version):
    source = ROOT / "packaging" / "windows" / "app.manifest"
    target = BUILD_DIR / "app.manifest"
    content = source.read_text(encoding="utf-8")
    content = re.sub(
        r'version="[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+"',
        'version="%s"' % version4(version),
        content,
        count=1,
    )
    target.write_text(content, encoding="utf-8")
    return target


def write_launcher_resource(version):
    resource = BUILD_DIR / "launcher.rc"
    icon = (ASSETS_DIR / "app.ico").as_posix()
    manifest = write_app_manifest(version).as_posix()
    numeric_version = ",".join(version4(version).split("."))
    resource.write_text(
        """#include <windows.h>
1 ICON "{icon}"
1 RT_MANIFEST "{manifest}"
VS_VERSION_INFO VERSIONINFO
 FILEVERSION {numeric_version}
 PRODUCTVERSION {numeric_version}
 FILEFLAGSMASK 0x3fL
 FILEFLAGS 0x0L
 FILEOS 0x40004L
 FILETYPE 0x1L
 FILESUBTYPE 0x0L
BEGIN
  BLOCK "StringFileInfo"
  BEGIN
    BLOCK "041F04E6"
    BEGIN
      VALUE "CompanyName", "LISDEP\\0"
      VALUE "FileDescription", "Kantar Servisi\\0"
      VALUE "FileVersion", "{version}\\0"
      VALUE "InternalName", "KantarServisi\\0"
      VALUE "LegalCopyright", "Copyright (c) 2026 LISDEP\\0"
      VALUE "OriginalFilename", "KantarServisi.exe\\0"
      VALUE "ProductName", "Kantar Servisi\\0"
      VALUE "ProductVersion", "{version}\\0"
    END
  END
  BLOCK "VarFileInfo"
  BEGIN
    VALUE "Translation", 0x041f, 1254
  END
END
""".format(
            icon=icon,
            manifest=manifest,
            numeric_version=numeric_version,
            version=version,
        ),
        encoding="utf-8",
    )
    return resource


def build_launcher(version):
    resource = write_launcher_resource(version)
    resource_object = BUILD_DIR / "launcher-resource.o"
    executable = RUNTIME_DIR / "KantarServisi.exe"
    run(
        [
            "x86_64-w64-mingw32-windres",
            "--codepage=65001",
            str(resource),
            str(resource_object),
        ]
    )
    run(
        [
            "x86_64-w64-mingw32-gcc",
            "-O2",
            "-s",
            "-municode",
            "-mwindows",
            str(ROOT / "packaging" / "windows" / "launcher.c"),
            str(resource_object),
            "-o",
            str(executable),
            "-lshell32",
            "-luser32",
        ]
    )
    return executable


def verify_runtime(executable):
    file_output = subprocess.check_output(["file", str(executable)], text=True)
    if "PE32+ executable" not in file_output or "x86-64" not in file_output:
        raise RuntimeError("KantarServisi.exe gecerli bir Windows x64 PE dosyasi degil.")
    exports = subprocess.check_output(
        ["x86_64-w64-mingw32-objdump", "-p", str(RUNTIME_DIR / "python312.dll")],
        text=True,
        errors="replace",
    )
    if "Py_Main" not in exports:
        raise RuntimeError("Gomme Python calisma zamani Py_Main girisini sunmuyor.")


def build_installer(version):
    DOWNLOADS_DIR.mkdir(parents=True, exist_ok=True)
    installer = DOWNLOADS_DIR / "Kantar-Servisi-Setup.exe"
    installer.unlink(missing_ok=True)
    run(
        [
            "makensis",
            "-V3",
            "-DAPP_VERSION=%s" % version,
            "-DAPP_VERSION4=%s" % version4(version),
            "-DSOURCE_DIR=%s" % RUNTIME_DIR,
            "-DOUTPUT_DIR=%s" % DOWNLOADS_DIR,
            str(ROOT / "packaging" / "windows" / "installer.nsi"),
        ],
        cwd=str(ROOT / "packaging" / "windows"),
    )
    if not installer.exists():
        raise RuntimeError("NSIS kurulum dosyasi olusturulmadi.")
    file_output = subprocess.check_output(["file", str(installer)], text=True)
    if "PE32 executable" not in file_output:
        raise RuntimeError("Kurulum dosyasi gecerli bir Windows PE dosyasi degil.")
    if installer.stat().st_size >= MAX_GITHUB_FILE_SIZE:
        raise RuntimeError("Kurulum dosyasi GitHub 100 MiB tek dosya sinirini asiyor.")
    return installer


def write_distribution_metadata(version, installer):
    digest = hashlib.sha256(installer.read_bytes()).hexdigest()
    manifest = {
        "version": version,
        "published_at": date.today().isoformat(),
        "installer": installer.name,
        "sha256": digest,
    }
    (DOWNLOADS_DIR / "latest.json").write_text(
        json.dumps(manifest, ensure_ascii=True, indent=2) + "\n",
        encoding="utf-8",
    )
    (DOWNLOADS_DIR / "SHA256SUMS.txt").write_text(
        "%s  %s\n" % (digest, installer.name),
        encoding="ascii",
    )
    print("Windows kurulumu hazir: %s" % installer)
    print("SHA256: %s" % digest)


def inside_container():
    version = read_version()
    if BUILD_DIR.exists():
        shutil.rmtree(BUILD_DIR)
    BUILD_DIR.mkdir(parents=True)
    archive = BUILD_DIR / ("python-%s-embed-amd64.zip" % PYTHON_VERSION)
    download(PYTHON_EMBED_URL, archive, PYTHON_EMBED_SHA256)
    RUNTIME_DIR.mkdir(parents=True)
    with zipfile.ZipFile(archive) as bundle:
        bundle.extractall(RUNTIME_DIR)
    for executable_name in ("python.exe", "pythonw.exe"):
        (RUNTIME_DIR / executable_name).unlink(missing_ok=True)
    write_python_path()
    install_windows_dependencies()
    copy_application()
    executable = build_launcher(version)
    verify_runtime(executable)
    installer = build_installer(version)
    write_distribution_metadata(version, installer)


def host_build():
    run(["npm", "run", "build:css"], cwd=str(ROOT))
    run([sys.executable, str(ROOT / "scripts" / "generate_build_assets.py")], cwd=str(ROOT))
    run(
        [
            "docker",
            "build",
            "-f",
            str(ROOT / "packaging" / "windows" / "Dockerfile.local"),
            "-t",
            DOCKER_IMAGE,
            str(ROOT),
        ],
        cwd=str(ROOT),
    )
    run(
        [
            "docker",
            "run",
            "--rm",
            "-v",
            "%s:/workspace" % ROOT,
            "-w",
            "/workspace",
            DOCKER_IMAGE,
        ],
        cwd=str(ROOT),
    )


def main():
    parser = argparse.ArgumentParser(description="Yerel Windows kurulum paketi uretir.")
    parser.add_argument("--inside-container", action="store_true", help=argparse.SUPPRESS)
    args = parser.parse_args()
    if args.inside_container:
        inside_container()
    else:
        host_build()


if __name__ == "__main__":
    main()
