import sys
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from kantar_servis import __version__

BUILD_DIR = ROOT / ".build-assets"


def version_tuple():
    parcalar = [int(parca) for parca in __version__.split(".")]
    while len(parcalar) < 4:
        parcalar.append(0)
    return tuple(parcalar[:4])


def generate_icon():
    BUILD_DIR.mkdir(parents=True, exist_ok=True)
    image = Image.new("RGBA", (256, 256), (15, 23, 42, 0))
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle((14, 14, 242, 242), radius=50, fill=(37, 99, 235, 255))
    draw.rounded_rectangle((52, 55, 204, 109), radius=17, fill=(239, 246, 255, 255))
    draw.rectangle((71, 130, 185, 194), fill=(255, 255, 255, 255))
    draw.rectangle((90, 146, 105, 180), fill=(37, 99, 235, 255))
    draw.rectangle((121, 136, 136, 180), fill=(37, 99, 235, 255))
    draw.rectangle((152, 154, 167, 180), fill=(37, 99, 235, 255))
    image.save(
        BUILD_DIR / "app.ico",
        sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)],
    )


def generate_installer_images():
    BUILD_DIR.mkdir(parents=True, exist_ok=True)
    buyuk = Image.new("RGB", (164, 314), (15, 23, 42))
    draw = ImageDraw.Draw(buyuk)
    draw.rounded_rectangle((18, 26, 146, 154), radius=28, fill=(37, 99, 235))
    draw.rounded_rectangle((45, 55, 119, 82), radius=8, fill=(239, 246, 255))
    draw.rectangle((54, 98, 110, 132), fill=(255, 255, 255))
    draw.rectangle((65, 106, 72, 124), fill=(37, 99, 235))
    draw.rectangle((78, 102, 85, 124), fill=(37, 99, 235))
    draw.rectangle((91, 111, 98, 124), fill=(37, 99, 235))
    draw.rectangle((18, 176, 146, 179), fill=(30, 41, 59))
    draw.text((22, 198), "KANTAR", fill=(255, 255, 255))
    draw.text((22, 218), "SERVISI", fill=(147, 197, 253))
    draw.text((22, 274), "LISDEP", fill=(148, 163, 184))
    buyuk.save(BUILD_DIR / "wizard-large.bmp")

    kucuk = Image.new("RGB", (55, 55), (37, 99, 235))
    draw = ImageDraw.Draw(kucuk)
    draw.rounded_rectangle((6, 7, 49, 23), radius=5, fill=(239, 246, 255))
    draw.rectangle((12, 29, 43, 47), fill=(255, 255, 255))
    draw.rectangle((18, 34, 22, 43), fill=(37, 99, 235))
    draw.rectangle((26, 31, 30, 43), fill=(37, 99, 235))
    draw.rectangle((34, 36, 38, 43), fill=(37, 99, 235))
    kucuk.save(BUILD_DIR / "wizard-small.bmp")


def generate_version_info():
    surum = version_tuple()
    metin = """VSVersionInfo(
  ffi=FixedFileInfo(
    filevers={surum},
    prodvers={surum},
    mask=0x3f,
    flags=0x0,
    OS=0x40004,
    fileType=0x1,
    subtype=0x0,
    date=(0, 0)
  ),
  kids=[
    StringFileInfo([
      StringTable(
        '041F04E6',
        [
          StringStruct('CompanyName', 'LISDEP'),
          StringStruct('FileDescription', 'Kantar Servisi'),
          StringStruct('FileVersion', '{surum_metni}'),
          StringStruct('InternalName', 'KantarServisi'),
          StringStruct('LegalCopyright', 'Copyright (c) 2026'),
          StringStruct('OriginalFilename', 'KantarServisi.exe'),
          StringStruct('ProductName', 'Kantar Servisi'),
          StringStruct('ProductVersion', '{surum_metni}')
        ]
      )
    ]),
    VarFileInfo([VarStruct('Translation', [1055, 1254])])
  ]
)
""".format(surum=surum, surum_metni=__version__)
    (BUILD_DIR / "version_info.txt").write_text(metin, encoding="utf-8")


if __name__ == "__main__":
    generate_icon()
    generate_installer_images()
    generate_version_info()
    print("Windows build varliklari olusturuldu: %s" % BUILD_DIR)
